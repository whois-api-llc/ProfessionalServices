#!/usr/bin/env python3
"""
WHOIS API benchmark: 4-way comparison.

Modes:
  1. Sequential (HTTP/1.1, single keep-alive session)
  2. Threaded   (HTTP/1.1, N worker threads, one session per thread)
  3. HTTP/2 single-connection (async, one client, many in-flight via multiplexing)
  4. HTTP/2 multi-connection  (async, pool of clients, many in-flight per connection)

Reads a list of domain names from a file (one per line) and queries the
WhoisXML WHOIS service for each. Prints per-mode latency stats and
optionally writes a self-contained HTML report with embedded charts.

The HTTP/2 modes require httpx with the h2 extra:
    pip install 'httpx[http2]'
If httpx is not installed, those modes are skipped with a clear message.

Usage:
    python whois_benchmark.py domains.txt --apiKey at_yourkey
    python whois_benchmark.py domains.txt --apiKey at_yourkey -t 10 --concurrency 20
    python whois_benchmark.py domains.txt --apiKey at_yourkey --html-report report.html
    python whois_benchmark.py domains.txt --apiKey at_yourkey --only sequential threaded
"""

import argparse
import asyncio
import datetime as dt
import html
import json
import os
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


WHOIS_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

ALL_MODES = ["sequential", "threaded", "http2_single", "http2_pool"]
MODE_LABELS = {
    "sequential":   "Sequential (HTTP/1.1 keep-alive)",
    "threaded":     "Threaded (HTTP/1.1)",
    "http2_single": "HTTP/2 single-connection (async)",
    "http2_pool":   "HTTP/2 multi-connection (async pool)",
}
MODE_SHORT = {
    "sequential":   "Sequential",
    "threaded":     "Threaded",
    "http2_single": "HTTP/2 (1 conn)",
    "http2_pool":   "HTTP/2 (pool)",
}


# ---------------------------------------------------------------------------
# Sync request (modes 1 & 2)
# ---------------------------------------------------------------------------

def fetch_sync(session: requests.Session, domain: str, api_key: str, run_start: float, thread_id: int):
    params = {"domainName": domain, "apiKey": api_key, "outputFormat": "JSON", "da": 1}
    started = time.perf_counter()
    try:
        resp = session.get(WHOIS_URL, params=params, timeout=30)
        elapsed = time.perf_counter() - started
        if resp.status_code != 200:
            return _result(domain, elapsed, False, f"HTTP {resp.status_code}", started - run_start, thread_id)
        data = resp.json()
        created = data.get("WhoisRecord", {}).get("createdDate", "")
        if "T" in created:
            created = created[: created.index("T")]
        return _result(domain, elapsed, True, created or "(no createdDate)", started - run_start, thread_id)
    except Exception as e:
        elapsed = time.perf_counter() - started
        return _result(domain, elapsed, False, f"{type(e).__name__}: {e}", started - run_start, thread_id)


def _result(domain, elapsed, ok, info, started_rel, thread_id):
    return {
        "domain": domain,
        "elapsed": elapsed,
        "ok": ok,
        "info": info,
        "started_rel": started_rel,
        "thread": thread_id,
    }


# ---------------------------------------------------------------------------
# Mode 1: Sequential
# ---------------------------------------------------------------------------

def run_sequential(domains, api_key):
    session = requests.Session()
    results = []
    wall_start = time.perf_counter()
    for d in domains:
        results.append(fetch_sync(session, d, api_key, wall_start, 0))
    wall = time.perf_counter() - wall_start
    return {"results": results, "wall": wall, "info": {}}


# ---------------------------------------------------------------------------
# Mode 2: Threaded
# ---------------------------------------------------------------------------

def run_threaded(domains, api_key, n_threads):
    tls = threading.local()
    thread_ids = {}
    lock = threading.Lock()

    def get_session():
        if not hasattr(tls, "session"):
            tls.session = requests.Session()
        return tls.session

    def get_tid():
        tid = threading.get_ident()
        with lock:
            if tid not in thread_ids:
                thread_ids[tid] = len(thread_ids)
            return thread_ids[tid]

    wall_start = time.perf_counter()

    def worker(domain):
        return fetch_sync(get_session(), domain, api_key, wall_start, get_tid())

    results = []
    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futures = [pool.submit(worker, d) for d in domains]
        for fut in as_completed(futures):
            results.append(fut.result())
    wall = time.perf_counter() - wall_start
    return {"results": results, "wall": wall, "info": {"workers": n_threads}}


# ---------------------------------------------------------------------------
# Async request (modes 3 & 4)
# ---------------------------------------------------------------------------

async def fetch_async(client, domain, api_key, run_start, conn_id, info_capture):
    params = {"domainName": domain, "apiKey": api_key, "outputFormat": "JSON", "da": 1}
    started = time.perf_counter()
    try:
        resp = await client.get(WHOIS_URL, params=params, timeout=30)
        elapsed = time.perf_counter() - started
        # Capture negotiated protocol once
        if "http_version" not in info_capture:
            try:
                info_capture["http_version"] = resp.http_version
            except Exception:
                info_capture["http_version"] = "?"
        if resp.status_code != 200:
            return _result(domain, elapsed, False, f"HTTP {resp.status_code}", started - run_start, conn_id)
        data = resp.json()
        created = data.get("WhoisRecord", {}).get("createdDate", "")
        if "T" in created:
            created = created[: created.index("T")]
        return _result(domain, elapsed, True, created or "(no createdDate)", started - run_start, conn_id)
    except Exception as e:
        elapsed = time.perf_counter() - started
        return _result(domain, elapsed, False, f"{type(e).__name__}: {e}", started - run_start, conn_id)


# ---------------------------------------------------------------------------
# Mode 3: HTTP/2 single connection
# ---------------------------------------------------------------------------

async def _run_http2_single(domains, api_key, concurrency):
    info = {}
    # max_keepalive_connections=1 + max_connections=1 forces a single connection.
    # All concurrent requests get multiplexed over it via HTTP/2.
    limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)
    async with httpx.AsyncClient(http2=True, http1=False, limits=limits) as client:
        sem = asyncio.Semaphore(concurrency)

        async def bounded(d):
            async with sem:
                return await fetch_async(client, d, api_key, wall_start, 0, info)

        wall_start = time.perf_counter()
        tasks = [asyncio.create_task(bounded(d)) for d in domains]
        results = []
        for fut in asyncio.as_completed(tasks):
            results.append(await fut)
        wall = time.perf_counter() - wall_start
    return {"results": results, "wall": wall, "info": info}


def run_http2_single(domains, api_key, concurrency):
    return asyncio.run(_run_http2_single(domains, api_key, concurrency))


# ---------------------------------------------------------------------------
# Mode 4: HTTP/2 multi-connection pool
# ---------------------------------------------------------------------------

async def _run_http2_pool(domains, api_key, concurrency, pool_size):
    info = {}
    # Allow multiple connections; httpx will open up to pool_size and
    # multiplex multiple requests per connection.
    limits = httpx.Limits(max_connections=pool_size, max_keepalive_connections=pool_size)
    # Track which connection each request lands on (by local port). httpx
    # does not expose this directly per-request, so we approximate by
    # tagging by connection-id captured via an event hook.
    conn_id_for_url = {}
    next_conn_id = [0]
    conn_lock = asyncio.Lock()

    async def log_response(resp):
        # Use the underlying network stream's id as a proxy for connection identity.
        try:
            ext = resp.extensions
            net_stream = ext.get("network_stream")
            key = id(net_stream) if net_stream is not None else 0
        except Exception:
            key = 0
        async with conn_lock:
            if key not in conn_id_for_url:
                conn_id_for_url[key] = next_conn_id[0]
                next_conn_id[0] += 1
        # stash the conn_id on the response for the caller to read
        resp._conn_id = conn_id_for_url[key]

    async with httpx.AsyncClient(
        http2=True,
        http1=False,
        limits=limits,
        event_hooks={"response": [log_response]},
    ) as client:
        sem = asyncio.Semaphore(concurrency)

        async def bounded(d):
            async with sem:
                params = {"domainName": d, "apiKey": api_key, "outputFormat": "JSON", "da": 1}
                started = time.perf_counter()
                try:
                    resp = await client.get(WHOIS_URL, params=params, timeout=30)
                    elapsed = time.perf_counter() - started
                    if "http_version" not in info:
                        info["http_version"] = resp.http_version
                    cid = getattr(resp, "_conn_id", 0)
                    if resp.status_code != 200:
                        return _result(d, elapsed, False, f"HTTP {resp.status_code}", started - wall_start, cid)
                    data = resp.json()
                    created = data.get("WhoisRecord", {}).get("createdDate", "")
                    if "T" in created:
                        created = created[: created.index("T")]
                    return _result(d, elapsed, True, created or "(no createdDate)", started - wall_start, cid)
                except Exception as e:
                    elapsed = time.perf_counter() - started
                    return _result(d, elapsed, False, f"{type(e).__name__}: {e}", started - wall_start, 0)

        wall_start = time.perf_counter()
        tasks = [asyncio.create_task(bounded(d)) for d in domains]
        results = []
        for fut in asyncio.as_completed(tasks):
            results.append(await fut)
        wall = time.perf_counter() - wall_start
    info["connections_used"] = len(conn_id_for_url)
    return {"results": results, "wall": wall, "info": info}


def run_http2_pool(domains, api_key, concurrency, pool_size):
    return asyncio.run(_run_http2_pool(domains, api_key, concurrency, pool_size))


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def percentile(sorted_values, pct):
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def compute_stats(results, wall):
    latencies = [r["elapsed"] for r in results]
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    sorted_lat = sorted(latencies)
    return {
        "requests": len(results),
        "ok": ok_count,
        "failed": fail_count,
        "wall": wall,
        "throughput": (len(results) / wall) if wall > 0 else 0,
        "min": min(latencies) if latencies else 0,
        "avg": statistics.mean(latencies) if latencies else 0,
        "median": statistics.median(latencies) if latencies else 0,
        "p95": percentile(sorted_lat, 95) if latencies else 0,
        "p99": percentile(sorted_lat, 99) if latencies else 0,
        "max": max(latencies) if latencies else 0,
        "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
    }


def print_summary(label, run_data):
    s = compute_stats(run_data["results"], run_data["wall"])
    print(f"\n=== {label} ===")
    print(f"  requests       : {s['requests']}  (ok={s['ok']}, failed={s['failed']})")
    print(f"  wall time      : {s['wall']:.3f} s")
    print(f"  throughput     : {s['throughput']:.2f} req/s")
    print(f"  latency min    : {s['min']:.3f} s")
    print(f"  latency avg    : {s['avg']:.3f} s")
    print(f"  latency median : {s['median']:.3f} s")
    print(f"  latency p95    : {s['p95']:.3f} s")
    print(f"  latency p99    : {s['p99']:.3f} s")
    print(f"  latency max    : {s['max']:.3f} s")
    info = run_data.get("info", {})
    if "http_version" in info:
        print(f"  protocol       : {info['http_version']}")
    if "connections_used" in info:
        print(f"  connections    : {info['connections_used']}")
    if "workers" in info:
        print(f"  workers        : {info['workers']}")
    if s["failed"]:
        print("  failures:")
        for r in run_data["results"]:
            if not r["ok"]:
                print(f"    {r['domain']}: {r['info']}")
    return s


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WHOIS API Benchmark Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0e0d0b;
    --bg-card: #16140f;
    --bg-elev: #1d1a14;
    --ink: #f4ede0;
    --ink-dim: #a59c89;
    --ink-faint: #6b6356;
    --rule: #2a261d;
    --accent: #d4a04a;
    --c0: #d4a04a;  /* sequential   - gold */
    --c1: #6ab7a1;  /* threaded     - teal */
    --c2: #c66b9b;  /* http2 single - rose */
    --c3: #7b8ed4;  /* http2 pool   - periwinkle */
    --bad: #e85d3a;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--ink);
    font-family: 'Fraunces', Georgia, serif;
    line-height: 1.5;
    min-height: 100vh;
    background-image:
      radial-gradient(circle at 12% 0%, rgba(212,160,74,0.08), transparent 40%),
      radial-gradient(circle at 88% 100%, rgba(123,142,212,0.06), transparent 50%);
  }
  .wrap { max-width: 1240px; margin: 0 auto; padding: 64px 40px 96px; }

  header { border-bottom: 1px solid var(--rule); padding-bottom: 32px; margin-bottom: 48px; }
  .eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: 0.25em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 16px;
  }
  h1 {
    font-family: 'Fraunces', serif; font-weight: 800;
    font-size: clamp(36px, 5vw, 64px); line-height: 1.05; letter-spacing: -0.02em;
    margin: 0 0 12px;
  }
  h1 em { font-style: italic; color: var(--accent); font-weight: 400; }
  .meta {
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    color: var(--ink-dim); margin-top: 16px;
  }
  .meta span { margin-right: 24px; }
  .meta strong { color: var(--ink); font-weight: 500; }

  h2 {
    font-family: 'Fraunces', serif; font-weight: 600;
    font-size: 28px; letter-spacing: -0.01em;
    margin: 56px 0 24px;
    display: flex; align-items: baseline; gap: 16px;
  }
  h2 .num {
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    color: var(--accent); font-weight: 400;
  }

  /* Headline grid - one card per mode */
  .headline {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1px; background: var(--rule);
    border: 1px solid var(--rule); margin-bottom: 24px;
  }
  .headline > div { background: var(--bg-card); padding: 28px; }
  .headline .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-dim); margin-bottom: 12px;
  }
  .headline .big {
    font-family: 'Fraunces', serif; font-weight: 800;
    font-size: 44px; line-height: 1; letter-spacing: -0.03em;
  }
  .headline .unit {
    font-family: 'JetBrains Mono', monospace; font-size: 13px;
    color: var(--ink-faint); margin-left: 4px; font-weight: 400;
  }
  .headline .sub {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--ink-dim); margin-top: 12px;
  }
  .headline .badge {
    display: inline-block;
    margin-top: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.1em;
    padding: 2px 8px; border-radius: 2px;
    background: rgba(212,160,74,0.12); color: var(--accent);
  }
  .headline .badge.winner { background: rgba(106,183,161,0.15); color: var(--c1); }

  .verdict {
    background: var(--bg-elev);
    border-left: 3px solid var(--accent);
    padding: 24px 32px; margin-bottom: 48px;
    font-size: 18px; font-style: italic; color: var(--ink);
  }
  .verdict strong { color: var(--accent); font-style: normal; font-weight: 600; }

  .stats {
    width: 100%; border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace; font-size: 12.5px;
    background: var(--bg-card); border: 1px solid var(--rule);
  }
  .stats th, .stats td {
    padding: 13px 16px; text-align: right;
    border-bottom: 1px solid var(--rule);
  }
  .stats th {
    background: var(--bg-elev); color: var(--ink-dim);
    font-weight: 500; font-size: 10.5px;
    letter-spacing: 0.15em; text-transform: uppercase;
  }
  .stats th:first-child, .stats td:first-child {
    text-align: left; color: var(--ink);
  }
  .stats tr:last-child td { border-bottom: none; }
  .stats tr:hover td { background: var(--bg-elev); }

  .chart-card {
    background: var(--bg-card); border: 1px solid var(--rule);
    padding: 32px; margin-bottom: 24px;
  }
  .chart-card h3 {
    font-family: 'Fraunces', serif; font-weight: 600;
    font-size: 20px; margin: 0 0 4px; letter-spacing: -0.01em;
  }
  .chart-card .desc {
    font-size: 13px; color: var(--ink-dim);
    margin-bottom: 24px; font-style: italic;
  }
  .chart-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
  .chart-host { position: relative; height: 340px; }
  .chart-host.tall { height: 480px; }

  .timeline-stack { display: flex; flex-direction: column; gap: 24px; }

  details.requests {
    background: var(--bg-card); border: 1px solid var(--rule);
    padding: 24px 32px; margin-top: 16px;
  }
  details.requests summary {
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: var(--ink-dim); user-select: none;
  }
  details.requests summary:hover { color: var(--accent); }
  details.requests[open] summary { color: var(--accent); margin-bottom: 20px; }
  table.req {
    width: 100%; border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace; font-size: 11.5px;
  }
  table.req th, table.req td {
    padding: 7px 12px; text-align: right;
    border-bottom: 1px solid var(--rule);
  }
  table.req th {
    color: var(--ink-faint); font-weight: 500; font-size: 10px;
    letter-spacing: 0.15em; text-transform: uppercase;
  }
  table.req th:first-child, table.req td:first-child { text-align: left; }
  .pill {
    display: inline-block; padding: 2px 8px; border-radius: 2px;
    font-size: 10px; letter-spacing: 0.1em;
  }
  .pill.ok  { background: rgba(106,183,161,0.15); color: var(--c1); }
  .pill.bad { background: rgba(232,93,58,0.15);   color: var(--bad); }

  footer {
    margin-top: 80px; padding-top: 32px;
    border-top: 1px solid var(--rule);
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--ink-faint); letter-spacing: 0.05em;
  }

  @media (max-width: 800px) {
    .wrap { padding: 32px 20px; }
    .chart-grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="eyebrow">Benchmark Report · WhoisXML API</div>
  <h1>Four ways to <em>fetch faster</em></h1>
  <div class="meta">
    <span><strong>Generated</strong> __TIMESTAMP__</span>
    <span><strong>Domains</strong> __DOMAIN_COUNT__</span>
    <span><strong>Threads</strong> __THREAD_COUNT__</span>
    <span><strong>Concurrency</strong> __CONCURRENCY__</span>
    <span><strong>Pool size</strong> __POOL_SIZE__</span>
  </div>
</header>

__HEADLINE__

__VERDICT__

<h2><span class="num">01</span> Latency Statistics</h2>
<table class="stats">
  <thead><tr>__HEADER_COLS__</tr></thead>
  <tbody>__STATS_ROWS__</tbody>
</table>

<h2><span class="num">02</span> Wall time &amp; throughput</h2>
<div class="chart-card">
  <h3>Total time and requests per second</h3>
  <div class="desc">Lower wall time and higher throughput are better. The gap between modes is the actual win.</div>
  <div class="chart-host"><canvas id="throughputChart"></canvas></div>
</div>

<h2><span class="num">03</span> Latency distribution</h2>
<div class="chart-grid">
  <div class="chart-card">
    <h3>Per-request latency</h3>
    <div class="desc">Each request plotted in completion order, per mode.</div>
    <div class="chart-host"><canvas id="lineChart"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Latency histogram</h3>
    <div class="desc">How request times cluster across modes. Tighter = more predictable.</div>
    <div class="chart-host"><canvas id="histChart"></canvas></div>
  </div>
</div>

<h2><span class="num">04</span> Percentiles</h2>
<div class="chart-card">
  <h3>min · median · p95 · p99 · max</h3>
  <div class="desc">The tail tells the real story. A mode that wins on average but loses on p99 is risky in production.</div>
  <div class="chart-host"><canvas id="percentileChart"></canvas></div>
</div>

<h2><span class="num">05</span> Execution timelines</h2>
<div class="timeline-stack">__TIMELINES__</div>

<h2><span class="num">06</span> Per-request detail</h2>
__REQUEST_DETAILS__

<footer>
  WHOIS Benchmark · powered by WhoisXML API · Chart.js 4 · httpx
</footer>

</div>

<script>
const DATA = __DATA_JSON__;
const COLORS = { sequential: '#d4a04a', threaded: '#6ab7a1', http2_single: '#c66b9b', http2_pool: '#7b8ed4' };
const RULE = '#2a261d';
const INK_DIM = '#a59c89';
const INK_FAINT = '#6b6356';

Chart.defaults.color = INK_DIM;
Chart.defaults.borderColor = RULE;
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 11;

function gridOpts() {
  return { grid: { color: RULE, drawBorder: false }, ticks: { color: INK_FAINT } };
}
function modesPresent() {
  return Object.keys(DATA).filter(k => DATA[k]);
}

// Throughput / wall time
(function() {
  const modes = modesPresent();
  const labels = modes.map(m => DATA[m].short_label);
  const colors = modes.map(m => COLORS[m]);
  const wallData = modes.map(m => DATA[m].stats.wall);
  const tputData = modes.map(m => DATA[m].stats.throughput);
  new Chart(document.getElementById('throughputChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Wall time (s)',      data: wallData, backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 1, yAxisID: 'y' },
        { label: 'Throughput (req/s)', data: tputData, backgroundColor: colors.map(c => c + '55'), borderColor: colors, borderWidth: 1, yAxisID: 'y1' },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: INK_DIM } } },
      scales: {
        x: { ...gridOpts() },
        y:  { ...gridOpts(), position: 'left',  title: { display: true, text: 'Wall time (s)',      color: INK_FAINT }, beginAtZero: true },
        y1: { ...gridOpts(), position: 'right', title: { display: true, text: 'Throughput (req/s)', color: INK_FAINT }, beginAtZero: true, grid: { drawOnChartArea: false } },
      }
    }
  });
})();

// Per-request line chart
(function() {
  const datasets = modesPresent().map(m => ({
    label: DATA[m].short_label,
    data: DATA[m].results.map((r, i) => ({ x: i + 1, y: r.elapsed * 1000 })),
    borderColor: COLORS[m], backgroundColor: COLORS[m] + '33',
    borderWidth: 2, pointRadius: 2, pointHoverRadius: 5, tension: 0.2,
  }));
  new Chart(document.getElementById('lineChart'), {
    type: 'line', data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: INK_DIM } },
        tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)} ms` } }
      },
      scales: {
        x: { ...gridOpts(), title: { display: true, text: 'Request # (completion order)', color: INK_FAINT } },
        y: { ...gridOpts(), title: { display: true, text: 'Latency (ms)', color: INK_FAINT }, beginAtZero: true }
      }
    }
  });
})();

// Histogram (shared bins)
(function() {
  const N_BINS = 14;
  const all = [];
  modesPresent().forEach(m => DATA[m].results.forEach(r => all.push(r.elapsed * 1000)));
  if (!all.length) return;
  const minV = Math.min(...all), maxV = Math.max(...all);
  const width = ((maxV - minV) || 1) / N_BINS;
  const labels = [];
  for (let i = 0; i < N_BINS; i++) {
    const lo = minV + i * width, hi = lo + width;
    labels.push(`${lo.toFixed(0)}–${hi.toFixed(0)}`);
  }
  function bin(values) {
    const counts = new Array(N_BINS).fill(0);
    for (const v of values) {
      let idx = Math.floor((v - minV) / width);
      if (idx >= N_BINS) idx = N_BINS - 1;
      if (idx < 0) idx = 0;
      counts[idx]++;
    }
    return counts;
  }
  const datasets = modesPresent().map(m => ({
    label: DATA[m].short_label,
    data: bin(DATA[m].results.map(r => r.elapsed * 1000)),
    backgroundColor: COLORS[m] + 'aa', borderColor: COLORS[m], borderWidth: 1,
  }));
  new Chart(document.getElementById('histChart'), {
    type: 'bar', data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: INK_DIM } } },
      scales: {
        x: { ...gridOpts(), title: { display: true, text: 'Latency bucket (ms)', color: INK_FAINT } },
        y: { ...gridOpts(), title: { display: true, text: 'Request count', color: INK_FAINT }, beginAtZero: true }
      }
    }
  });
})();

// Percentile radar
(function() {
  const labels = ['min', 'median', 'p95', 'p99', 'max'];
  const datasets = modesPresent().map(m => {
    const s = DATA[m].stats;
    return {
      label: DATA[m].short_label,
      data: [s.min, s.median, s.p95, s.p99, s.max].map(v => v * 1000),
      backgroundColor: COLORS[m] + '22', borderColor: COLORS[m],
      borderWidth: 2, pointBackgroundColor: COLORS[m],
    };
  });
  new Chart(document.getElementById('percentileChart'), {
    type: 'radar', data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: INK_DIM } },
        tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.r.toFixed(1)} ms` } }
      },
      scales: {
        r: {
          angleLines: { color: RULE }, grid: { color: RULE },
          pointLabels: { color: INK_DIM, font: { size: 12 } },
          ticks: { color: INK_FAINT, backdropColor: 'transparent', callback: (v) => v + ' ms' },
          beginAtZero: true,
        }
      }
    }
  });
})();

// Per-mode timelines
modesPresent().forEach(m => {
  const canvas = document.getElementById('timeline_' + m);
  if (!canvas) return;
  const results = DATA[m].results.slice().sort((a, b) => a.started_rel - b.started_rel);
  const dataset = {
    label: 'Request',
    data: results.map((r) => ({
      x: [r.started_rel, r.started_rel + r.elapsed],
      y: r.thread, domain: r.domain, ms: r.elapsed * 1000, ok: r.ok,
    })),
    backgroundColor: results.map(r => r.ok ? COLORS[m] + 'cc' : '#e85d3acc'),
    borderColor: results.map(r => r.ok ? COLORS[m] : '#e85d3a'),
    borderWidth: 1, borderSkipped: false, barPercentage: 0.7,
  };
  new Chart(canvas, {
    type: 'bar', data: { datasets: [dataset] },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => items[0].raw.domain,
            label: (ctx) => `lane ${ctx.raw.y} · ${ctx.raw.ms.toFixed(1)} ms`
          }
        }
      },
      scales: {
        x: { ...gridOpts(), title: { display: true, text: 'Time since run start (s)', color: INK_FAINT }, beginAtZero: true },
        y: { ...gridOpts(), title: { display: true, text: 'Lane (thread or connection)', color: INK_FAINT }, ticks: { stepSize: 1, callback: (v) => '#' + v } }
      }
    }
  });
});
</script>
</body>
</html>"""


def render_html_report(runs, domain_count, thread_count, concurrency, pool_size, out_path):
    """runs: dict[mode_key] -> {"results", "stats", "wall", "info", "short_label"}"""
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Headline cards
    fastest_mode = None
    fastest_wall = float("inf")
    for mode, run in runs.items():
        if run["stats"]["wall"] < fastest_wall:
            fastest_wall = run["stats"]["wall"]
            fastest_mode = mode

    headline_parts = []
    for mode in ALL_MODES:
        if mode not in runs:
            continue
        run = runs[mode]
        s = run["stats"]
        info = run.get("info", {})
        sub_extras = []
        if "http_version" in info:
            sub_extras.append(info["http_version"])
        if "connections_used" in info:
            sub_extras.append(f"{info['connections_used']} conn")
        if "workers" in info:
            sub_extras.append(f"{info['workers']} workers")
        sub_extra = " · ".join(sub_extras)
        sub_extra = " · " + sub_extra if sub_extra else ""

        winner_badge = '<div class="badge winner">FASTEST</div>' if mode == fastest_mode else ''
        headline_parts.append(
            f'<div>'
            f'<div class="label">{html.escape(MODE_LABELS[mode])}</div>'
            f'<div class="big" style="color: var(--c{ALL_MODES.index(mode)})">{s["wall"]:.2f}<span class="unit">s</span></div>'
            f'<div class="sub">{s["throughput"]:.2f} req/s · avg {s["avg"]*1000:.0f} ms{sub_extra}</div>'
            f'{winner_badge}'
            f'</div>'
        )
    headline_html = '<div class="headline">' + "".join(headline_parts) + "</div>"

    # Verdict
    if len(runs) >= 2 and fastest_mode:
        slowest_wall = max(r["stats"]["wall"] for r in runs.values())
        slowest_mode = max(runs, key=lambda m: runs[m]["stats"]["wall"])
        speedup = slowest_wall / fastest_wall if fastest_wall > 0 else 0
        if speedup >= 1.05:
            verdict = (f"<strong>{MODE_SHORT[fastest_mode]}</strong> finished "
                       f"<strong>{speedup:.2f}× faster</strong> than "
                       f"<strong>{MODE_SHORT[slowest_mode]}</strong> "
                       f"on this workload of {domain_count} domains.")
        else:
            verdict = "All modes performed within 5% of each other — the network or server is the bottleneck, not the client strategy."
        verdict_html = f'<div class="verdict">{verdict}</div>'
    else:
        verdict_html = ""

    # Stats table
    metrics = [
        ("Requests",            lambda s: f"{s['requests']}"),
        ("Successful",          lambda s: f"{s['ok']}"),
        ("Failed",              lambda s: f"{s['failed']}"),
        ("Wall time (s)",       lambda s: f"{s['wall']:.3f}"),
        ("Throughput (req/s)",  lambda s: f"{s['throughput']:.2f}"),
        ("Min latency (ms)",    lambda s: f"{s['min']*1000:.1f}"),
        ("Avg latency (ms)",    lambda s: f"{s['avg']*1000:.1f}"),
        ("Median latency (ms)", lambda s: f"{s['median']*1000:.1f}"),
        ("p95 latency (ms)",    lambda s: f"{s['p95']*1000:.1f}"),
        ("p99 latency (ms)",    lambda s: f"{s['p99']*1000:.1f}"),
        ("Max latency (ms)",    lambda s: f"{s['max']*1000:.1f}"),
        ("Std dev (ms)",        lambda s: f"{s['stdev']*1000:.1f}"),
    ]
    present = [m for m in ALL_MODES if m in runs]
    header_cols = "<th>Metric</th>" + "".join(f"<th>{html.escape(MODE_SHORT[m])}</th>" for m in present)
    rows = []
    for name, fn in metrics:
        cells = [f"<td>{name}</td>"]
        for m in present:
            cells.append(f'<td style="color: var(--c{ALL_MODES.index(m)})">{fn(runs[m]["stats"])}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    stats_rows = "\n    ".join(rows)

    # Timelines per mode
    timeline_parts = []
    for m in present:
        timeline_parts.append(
            f'<div class="chart-card">'
            f'<h3>{html.escape(MODE_LABELS[m])}</h3>'
            f'<div class="desc">Each bar is one request, positioned by start time and sized by duration. '
            f'Lanes are threads (sync modes) or connections (HTTP/2 modes).</div>'
            f'<div class="chart-host tall"><canvas id="timeline_{m}"></canvas></div>'
            f'</div>'
        )
    timelines_html = "\n".join(timeline_parts)

    # Per-request collapsibles
    def render_req_table(label, run):
        rrows = []
        for r in run["results"]:
            pill_cls = "ok" if r["ok"] else "bad"
            pill_text = "OK" if r["ok"] else "ERR"
            rrows.append(
                f"<tr><td>{html.escape(r['domain'])}</td>"
                f"<td>{r['elapsed']*1000:.1f}</td>"
                f"<td>{r['started_rel']:.3f}</td>"
                f"<td>{r['thread']}</td>"
                f"<td><span class='pill {pill_cls}'>{pill_text}</span></td>"
                f"<td>{html.escape(str(r['info']))}</td></tr>"
            )
        return (f'<details class="requests">'
                f'<summary>{html.escape(label)} — {len(run["results"])} requests</summary>'
                f'<table class="req">'
                f'<thead><tr><th>Domain</th><th>Latency (ms)</th><th>Started (s)</th>'
                f'<th>Lane</th><th>Status</th><th>Info</th></tr></thead>'
                f'<tbody>{"".join(rrows)}</tbody></table></details>')
    request_details_html = "\n".join(render_req_table(MODE_LABELS[m], runs[m]) for m in present)

    # Embed JSON
    payload = {}
    for m in ALL_MODES:
        if m in runs:
            r = runs[m]
            payload[m] = {
                "results": r["results"],
                "stats": r["stats"],
                "info": r.get("info", {}),
                "short_label": MODE_SHORT[m],
                "long_label": MODE_LABELS[m],
            }
        else:
            payload[m] = None
    data_json = json.dumps(payload)

    out = (HTML_TEMPLATE
           .replace("__TIMESTAMP__", html.escape(timestamp))
           .replace("__DOMAIN_COUNT__", str(domain_count))
           .replace("__THREAD_COUNT__", str(thread_count) if "threaded" in runs else "—")
           .replace("__CONCURRENCY__", str(concurrency) if any(m in runs for m in ("http2_single", "http2_pool")) else "—")
           .replace("__POOL_SIZE__", str(pool_size) if "http2_pool" in runs else "—")
           .replace("__HEADLINE__", headline_html)
           .replace("__VERDICT__", verdict_html)
           .replace("__HEADER_COLS__", header_cols)
           .replace("__STATS_ROWS__", stats_rows)
           .replace("__TIMELINES__", timelines_html)
           .replace("__REQUEST_DETAILS__", request_details_html)
           .replace("__DATA_JSON__", data_json))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_domains(path):
    with open(path, "r", encoding="utf-8") as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not domains:
        sys.exit(f"No domains found in {path}")
    return domains


def main():
    ap = argparse.ArgumentParser(
        description="WHOIS API benchmark across 4 strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="HTTP/2 modes require: pip install 'httpx[http2]'",
    )
    ap.add_argument("domains_file", help="Path to file with one domain per line")
    ap.add_argument("--apiKey", "--apikey", dest="api_key", default=None,
                    help="WhoisXML API key (falls back to WXAAPI env var)")
    ap.add_argument("-t", "--threads", type=int, default=10,
                    help="Number of worker threads for the threaded run (default: 10)")
    ap.add_argument("-c", "--concurrency", type=int, default=20,
                    help="Max in-flight requests for HTTP/2 modes (default: 20)")
    ap.add_argument("--pool-size", type=int, default=10,
                    help="Max connections in the HTTP/2 pool mode (default: 10)")
    ap.add_argument("--only", nargs="+", choices=ALL_MODES, default=None,
                    help="Run only the specified modes")
    ap.add_argument("--skip", nargs="+", choices=ALL_MODES, default=[],
                    help="Skip the specified modes")
    ap.add_argument("--show-results", action="store_true",
                    help="Print each domain's createdDate after the runs")
    ap.add_argument("--html-report", metavar="PATH",
                    help="Write a self-contained HTML report with embedded charts to PATH")
    args = ap.parse_args()

    api_key = args.api_key or os.getenv("WXAAPI")
    if not api_key:
        sys.exit("API key required. Pass --apiKey or set the WXAAPI environment variable.")

    domains = load_domains(args.domains_file)
    print(f"Loaded {len(domains)} domain(s) from {args.domains_file}")

    modes_to_run = args.only if args.only else list(ALL_MODES)
    modes_to_run = [m for m in modes_to_run if m not in args.skip]

    needs_httpx = any(m in modes_to_run for m in ("http2_single", "http2_pool"))
    if needs_httpx and not HAS_HTTPX:
        print("\nWARNING: httpx is not installed. HTTP/2 modes will be skipped.")
        print("         Install with: pip install 'httpx[http2]'")
        modes_to_run = [m for m in modes_to_run if m not in ("http2_single", "http2_pool")]

    print(f"Running modes: {', '.join(modes_to_run)}")
    if "threaded" in modes_to_run:
        print(f"  threaded workers   : {args.threads}")
    if any(m in modes_to_run for m in ("http2_single", "http2_pool")):
        print(f"  http/2 concurrency : {args.concurrency}")
    if "http2_pool" in modes_to_run:
        print(f"  http/2 pool size   : {args.pool_size}")

    runs = {}

    if "sequential" in modes_to_run:
        print(f"\n[1/4] Sequential...")
        run = run_sequential(domains, api_key)
        run["stats"] = print_summary(MODE_LABELS["sequential"], run)
        runs["sequential"] = run

    if "threaded" in modes_to_run:
        print(f"\n[2/4] Threaded ({args.threads} workers)...")
        run = run_threaded(domains, api_key, args.threads)
        run["stats"] = print_summary(MODE_LABELS["threaded"], run)
        runs["threaded"] = run

    if "http2_single" in modes_to_run:
        print(f"\n[3/4] HTTP/2 single connection (concurrency={args.concurrency})...")
        run = run_http2_single(domains, api_key, args.concurrency)
        run["stats"] = print_summary(MODE_LABELS["http2_single"], run)
        if run["info"].get("http_version") and run["info"]["http_version"] != "HTTP/2":
            print(f"  NOTE: server negotiated {run['info']['http_version']} — HTTP/2 not in use")
        runs["http2_single"] = run

    if "http2_pool" in modes_to_run:
        print(f"\n[4/4] HTTP/2 connection pool (pool={args.pool_size}, concurrency={args.concurrency})...")
        run = run_http2_pool(domains, api_key, args.concurrency, args.pool_size)
        run["stats"] = print_summary(MODE_LABELS["http2_pool"], run)
        if run["info"].get("http_version") and run["info"]["http_version"] != "HTTP/2":
            print(f"  NOTE: server negotiated {run['info']['http_version']} — HTTP/2 not in use")
        runs["http2_pool"] = run

    # Comparison summary
    if len(runs) >= 2:
        print("\n=== Comparison ===")
        sorted_modes = sorted(runs.keys(), key=lambda m: runs[m]["stats"]["wall"])
        baseline = runs[sorted_modes[-1]]["stats"]["wall"]  # slowest
        for m in sorted_modes:
            w = runs[m]["stats"]["wall"]
            speedup = baseline / w if w > 0 else 0
            print(f"  {MODE_LABELS[m]:42s}  {w:6.2f} s   ({speedup:.2f}x)")

    if args.show_results:
        print("\nResults:")
        merged = {}
        for run in runs.values():
            for r in run["results"]:
                merged.setdefault(r["domain"], (r["ok"], r["info"]))
        for d, (ok, info) in merged.items():
            tag = "OK " if ok else "ERR"
            print(f"  [{tag}] {d}: {info}")

    if args.html_report:
        render_html_report(runs, len(domains), args.threads,
                           args.concurrency, args.pool_size, args.html_report)
        print(f"\nHTML report written to: {args.html_report}")


if __name__ == "__main__":
    main()
