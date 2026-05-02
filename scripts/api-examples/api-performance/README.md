# WHOIS API Benchmark

> Methodology, usage, and interpretation guide for the four-mode HTTP benchmark.

A self-contained command-line tool that measures how four different HTTP client strategies perform when calling the [WhoisXML](https://www.whoisxmlapi.com/) WHOIS API. It reads a list of domain names from a file, executes the same workload under each strategy, captures per-request latency and protocol details, and produces both a console summary and an optional self-contained HTML report with embedded charts.

The goal is not to declare a single winner — the right strategy depends on the workload, the server, and operational constraints — but to make the trade-offs measurable and visible for a given environment.

---

## Table of Contents

- [Overview](#1-overview)
- [Installation and Setup](#2-installation-and-setup)
- [Usage](#3-usage)
- [Methodology](#4-methodology)
- [Interpreting the Output](#5-interpreting-the-output)
- [Reproducibility and Caveats](#6-reproducibility-and-caveats)
- [Troubleshooting](#7-troubleshooting)

---

## 1. Overview

### 1.1 What it tests

The script benchmarks four client strategies against the WhoisService endpoint:

- **Sequential** — a single keep-alive HTTP/1.1 connection, one request at a time.
- **Threaded** — N parallel HTTP/1.1 connections, one request per thread at a time.
- **HTTP/2 single-connection** — one HTTP/2 connection, many in-flight requests via stream multiplexing.
- **HTTP/2 multi-connection** — a pool of HTTP/2 connections, multiplexing requests across each.

### 1.2 What it reports

- Wall-clock time for the full workload, per mode.
- Throughput (requests per second).
- Per-request latency: min, average, median, p95, p99, max, standard deviation.
- Negotiated HTTP protocol version for HTTP/2 modes (so silent fallback to HTTP/1.1 is visible).
- Number of distinct connections actually used in the pool mode.
- A Gantt-style timeline of every request, plotted against either thread ID or connection ID.

---

## 2. Installation and Setup

### 2.1 Requirements

The script requires Python 3.8 or newer. The HTTP/1.1 modes use the `requests` library; the HTTP/2 modes use `httpx` with the `h2` extra. The HTTP/2 modes are optional — if `httpx` is not installed the script will still run the sequential and threaded modes and emit a clear warning.

### 2.2 Installing dependencies

```bash
pip install requests "httpx[http2]"
```

### 2.3 API key

A WhoisXML API key is required. The script accepts the key in two ways:

- `--apiKey` command-line argument (preferred for one-off runs and CI)
- `WXAAPI` environment variable (used as fallback if the argument is omitted)

If neither is provided, the script exits with an error before making any network calls.

---

## 3. Usage

### 3.1 Input file format

The domains file is a plain-text file with one fully-qualified domain name per line. Blank lines are ignored. Lines starting with `#` are treated as comments and skipped. Example:

```text
# Top-100 reference domains
google.com
amazon.com
microsoft.com
cisco.com
apple.com
```

### 3.2 Basic invocations

Run all four modes with default tuning:

```bash
python whois_benchmark.py domains.txt --apiKey at_yourkey
```

Generate the HTML report:

```bash
python whois_benchmark.py domains.txt --apiKey at_yourkey \
    --html-report report.html
```

Tune concurrency parameters:

```bash
python whois_benchmark.py domains.txt --apiKey at_yourkey \
    -t 20 -c 50 --pool-size 10 \
    --html-report report.html
```

Run only specific modes (useful for debugging or when comparing just two strategies):

```bash
python whois_benchmark.py domains.txt --apiKey at_yourkey \
    --only sequential threaded
```

### 3.3 Command-line options

| Option              | Default | Purpose                                           |
| ------------------- | ------- | ------------------------------------------------- |
| `--apiKey`          | —       | WhoisXML API key. Falls back to `WXAAPI` env var. |
| `-t, --threads`     | `10`    | Worker thread count for the threaded mode.        |
| `-c, --concurrency` | `20`    | Maximum in-flight requests for HTTP/2 modes.      |
| `--pool-size`       | `10`    | Maximum HTTP/2 connections in the pool mode.      |
| `--only`            | all     | Whitelist of modes to run (space-separated).      |
| `--skip`            | none    | Blacklist of modes to skip.                       |
| `--show-results`    | off     | Print each domain's `createdDate` after the runs. |
| `--html-report`     | —       | Write a self-contained HTML report to `PATH`.     |

Valid mode names for `--only` and `--skip` are: `sequential`, `threaded`, `http2_single`, `http2_pool`.

---

## 4. Methodology

Every mode performs the same logical workload: one WHOIS lookup per domain in the input file, against the same endpoint, with the same query parameters. The differences between modes are entirely in how requests are dispatched and how connections are managed. This section describes each strategy, what it controls for, and what its results actually mean.

### 4.1 Common measurement framework

All four modes share the same instrumentation:

- **Per-request timing:** measured with `time.perf_counter()` immediately before issuing the request and immediately after the response (or exception) returns. The elapsed value includes connection acquisition, request transmission, server processing, and full response read.
- **Wall time:** measured around the full workload, from before the first request is dispatched to after the last result is collected. This is the number that matters for capacity planning.
- **Start offset:** each request also records its start time relative to the run's wall-time origin. This is what enables the timeline visualization to show overlap and gaps between requests.
- **Success criteria:** a request is counted as successful if and only if it returns HTTP 200 with valid JSON and no exception. Non-200 responses, JSON parse errors, timeouts, and network exceptions are all classified as failures.

### 4.2 Mode 1: Sequential (HTTP/1.1 keep-alive)

#### What it does

Creates a single `requests.Session()` and issues each WHOIS request synchronously, waiting for the previous response before sending the next. The Session keeps the underlying TCP and TLS connection open across all requests, so the cost of a TLS handshake is paid only once per run.

#### What it controls for

This mode establishes the baseline round-trip latency for a single client-server pair. Because there is exactly one connection and exactly one request in flight at any time, the wall time is the sum of per-request latencies. There is no concurrency, no scheduling overhead, and no contention on the server side from this client.

#### What its results mean

The sequential wall time is the lower bound on how slow a naive client implementation will be — it is also the upper bound on how slow a pessimistic real-world deployment might be if all concurrency is accidentally serialized (for example, by a misconfigured proxy). Comparing other modes against sequential gives you the actual concurrency speedup you achieve.

#### Caveats

- The first request pays the TLS handshake cost; subsequent requests reuse the connection. On runs with very few domains, this front-loaded cost can distort the average. Looking at the median or p50 helps.
- Server-side keep-alive timeouts can close the connection mid-run on long workloads, which would force a reconnect. If you see a step-change in latency partway through the sequential timeline, this is the likely cause.

### 4.3 Mode 2: Threaded (HTTP/1.1 with worker pool)

#### What it does

Spawns a `ThreadPoolExecutor` with N workers (configurable via `-t`). Each worker holds its own `requests.Session` in thread-local storage, so each worker maintains its own keep-alive HTTP/1.1 connection. The N domains are distributed across workers as they become free; any single worker still issues its requests one at a time, but multiple workers are active concurrently.

#### What it controls for

This is the standard, conservative answer to "how do I make this faster" with the requests library. It establishes how much of the sequential wall time is server-side latency that can be hidden by overlap, versus client-side serialization that cannot.

#### What its results mean

In the absence of server-side rate limiting, the threaded wall time approaches `sequential_wall / min(N_threads, N_domains)`, with diminishing returns as N grows. The ratio of actual to theoretical speedup tells you how much serialization the server is imposing — either through hard rate limits, queue depth limits, or single-tenant resource constraints.

#### Caveats

- Each thread opens its own connection. With N threads, the server sees N concurrent client connections from the same source. If the API enforces a per-connection or per-IP concurrency limit, you may see HTTP 429 responses or stalled requests as N increases.
- `requests.Session` is not thread-safe; the script avoids this pitfall by giving each thread its own session via `threading.local()`. Sharing a single Session across threads in your own code would produce subtle data corruption or hangs.
- The Python GIL is released during socket I/O, so threading is genuinely effective for HTTP workloads. CPU-bound work in your response handler would not benefit from this approach.

### 4.4 Mode 3: HTTP/2 single-connection (async)

#### What it does

Uses `httpx.AsyncClient` configured with `http2=True` and connection limits forced to a single connection (`max_connections=1`). Concurrency is provided by `asyncio` tasks bounded by a semaphore (default 20). All requests are multiplexed as independent HTTP/2 streams over the single underlying TCP/TLS connection.

#### What it controls for

This mode isolates the benefit of HTTP/2 stream multiplexing from the benefit of having multiple connections. If this mode performs comparably to the threaded mode, the win comes from the protocol; if it underperforms, it suggests the server is processing the multiplexed streams serially or there is head-of-line blocking from a slow response.

#### What its results mean

A successful single-connection HTTP/2 run that approaches threaded throughput proves the server genuinely parallelizes work across streams on one connection. A run that approaches sequential throughput suggests the server is serializing internally and exposing a multiplexed interface only nominally.

#### Caveats

- **Protocol negotiation:** httpx will gracefully fall back to HTTP/1.1 if the server does not negotiate HTTP/2 via ALPN. The script captures the negotiated protocol from the first response and reports it; if "HTTP/2" is not what was negotiated, the mode is effectively async-over-HTTP/1.1 and should be interpreted as such.
- **Head-of-line blocking:** one slow response on the connection can delay the others. HTTP/2 multiplexing is at the application layer; at the TCP layer, packet loss still blocks all streams.

### 4.5 Mode 4: HTTP/2 multi-connection (async pool)

#### What it does

Identical to mode 3, but the connection pool is allowed to open multiple connections (default pool size: 10). Each connection still multiplexes streams; the difference is that the workload can spread across multiple connections, which the server may treat as independent clients with independent quotas.

#### What it controls for

This mode tests whether combining both axes of concurrency — multiple connections and multiplexing per connection — produces a meaningful win over either alone. It also reveals whether the server enforces a per-connection concurrency limit that single-connection HTTP/2 hits.

#### What its results mean

If this mode beats mode 3 by a wide margin, the server is throttling per connection and benefits from being addressed across multiple sockets. If it ties mode 3, one HTTP/2 connection was already enough capacity for this workload — typical for low-N workloads, where opening more connections just adds handshake overhead.

#### Caveats

- The script reports `connections_used`, which is the number of distinct underlying network streams the run actually touched. If this is less than `--pool-size`, httpx decided fewer connections were sufficient.
- Connection identity is approximated via `id(network_stream)` from httpx response extensions. This is reliable enough to count distinct connections but should not be used as a stable identifier across runs.

---

## 5. Interpreting the Output

### 5.1 Console output

Each mode prints a stat block immediately after it completes:

```text
=== HTTP/2 single-connection (async) ===
  requests       : 25  (ok=25, failed=0)
  wall time      : 0.847 s
  throughput     : 29.51 req/s
  latency min    : 0.182 s
  latency avg    : 0.341 s
  latency median : 0.318 s
  latency p95    : 0.492 s
  latency p99    : 0.541 s
  latency max    : 0.541 s
  protocol       : HTTP/2
```

After all modes complete, a comparison table sorts modes from fastest to slowest and shows the speedup over the slowest mode:

```text
=== Comparison ===
  HTTP/2 multi-connection (async pool)        0.71 s   (5.13x)
  HTTP/2 single-connection (async)            0.85 s   (4.30x)
  Threaded (HTTP/1.1)                         1.42 s   (2.57x)
  Sequential (HTTP/1.1 keep-alive)            3.65 s   (1.00x)
```

### 5.2 HTML report

When `--html-report` is provided, a single self-contained HTML file is written. The report has the following sections:

| Section                | Content                                                                                                                                                                             |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Headline cards         | One card per mode showing wall time, throughput, average latency, and protocol details. The fastest mode is tagged.                                                                 |
| Latency statistics     | Full numerical comparison table covering all stats from the console output.                                                                                                         |
| Wall time & throughput | Dual-axis bar chart: wall time per mode on the left axis, throughput on the right.                                                                                                  |
| Latency distribution   | Per-request latency line chart and a shared-bin histogram showing how latencies cluster across modes.                                                                               |
| Percentiles            | Radar chart of min, median, p95, p99, max — useful for spotting modes that win on average but lose on tail latency.                                                                 |
| Execution timelines    | A Gantt-style chart per mode showing each request as a bar, positioned by start time and sized by duration. Lanes correspond to threads (sync modes) or connections (HTTP/2 modes). |
| Per-request detail     | Collapsible table per mode with every domain, latency, start offset, lane, status, and result info.                                                                                 |

Chart.js is loaded from a CDN and all benchmark data is embedded inline as JSON, so the report works offline once generated and can be shared as a single file.

### 5.3 What to look for

#### Speedup ratios

The most direct comparison is the wall-time ratio between modes. A 4× speedup from sequential to threaded with 10 workers means the server is handling concurrent requests in parallel; a 1.2× speedup means the server is serializing them somewhere — likely a rate limit or a per-account queue.

#### Tail latency

A mode that wins on average but loses on p99 is risky in production. The radar chart in section 4 of the report makes this easy to spot: look for shapes where one mode has a long spike toward the "max" or "p99" axis even if its center is small.

#### Timeline patterns

In the threaded mode timeline, you should see N parallel lanes, each with bars packed tightly together. Gaps in a lane mean the worker was blocked waiting for the server. In the HTTP/2 single-connection timeline, all bars share lane 0; if they appear stacked rather than overlapping, the server is processing streams sequentially despite the multiplexed protocol.

#### Failure clusters

Failures concentrated in time (a contiguous block of red bars in the timeline) usually indicate rate limiting kicked in. Failures scattered randomly through the run usually indicate transient network or server issues.

---

## 6. Reproducibility and Caveats

### 6.1 Things outside the script's control

- **Network conditions:** RTT to the API endpoint, packet loss, and intermediate proxy buffering all affect timing. Running the benchmark from different network locations will produce different results.
- **Server-side load:** the WhoisXML API serves many customers. Latency varies with their aggregate load, not just yours. Running the same benchmark at different times of day can produce 2–3× variation.
- **Account-level rate limits:** some plans cap requests per second or per minute. Hitting that cap will silently serialize the threaded and HTTP/2 modes back toward sequential performance.
- **DNS and TLS warm-up:** the first connection in any mode pays a DNS resolution and TLS handshake cost. With small workloads (under 20 domains), this cost is a meaningful fraction of the total. Larger workloads amortize it.

### 6.2 Running a meaningful benchmark

1. Use at least 50 domains. Smaller workloads are dominated by handshake costs and produce noisy percentiles.
2. Run each configuration three times and take the median wall time. A single run can be skewed by transient network conditions.
3. Run all four modes back-to-back in the same invocation. Running them at different times conflates network/server variability with mode differences.
4. When tuning `-t` and `--concurrency`, sweep across values (e.g., 1, 5, 10, 20, 50). The sweet spot is workload- and account-specific.
5. If HTTP/2 modes report HTTP/1.1 in the output, the server did not negotiate HTTP/2. Treat those modes as "async over HTTP/1.1" and weight the conclusions accordingly.

### 6.3 Known limitations

- The script does not implement automatic retries beyond what the underlying libraries provide. Transient 5xx responses count as failures.
- Connection identity tracking in the HTTP/2 pool mode relies on httpx response extensions, which may behave differently across httpx versions.
- The HTTP/2 modes use `asyncio.run()`, which creates a new event loop per mode. Total invocation overhead is small but not zero.
- The script measures only the WHOIS service. Other WhoisXML endpoints may have different performance characteristics.

---

## 7. Troubleshooting

| Symptom                                               | Likely cause and fix                                                                                                                                                                                                                 |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `"API key required"` error.                           | No `--apiKey` passed and `WXAAPI` environment variable not set. Pass the key explicitly or export the variable before running.                                                                                                       |
| HTTP/2 modes skipped with warning.                    | `httpx` not installed. Run: `pip install "httpx[http2]"`. The `h2` extra is required; plain httpx will not negotiate HTTP/2.                                                                                                         |
| HTTP/2 modes show `"HTTP/1.1"` in the protocol field. | The server did not negotiate HTTP/2 via ALPN. Either the server does not support HTTP/2 or an intermediate proxy is downgrading the connection. The mode still runs (async over HTTP/1.1) but is not testing what its name suggests. |
| Threaded mode is slower than sequential.              | Server-side rate limiting or per-IP concurrency limit. Lower `-t` and try again. If the issue persists, check your account's rate-limit documentation.                                                                               |
| All modes have very similar wall times.               | The network is the bottleneck — most likely high RTT. Run from a host closer to the server, or accept that concurrency cannot help in this environment.                                                                              |
| Failures cluster at the start of the run.             | TLS handshake or DNS issue on first connection. Re-run; if persistent, check the network path with `curl` or `openssl s_client`.                                                                                                     |
| Failures cluster at the end of the run.               | Account quota likely exhausted. Check the account dashboard or wait for the quota window to reset.                                                                                                                                   |
| HTML report is generated but charts are blank.        | Chart.js could not be loaded from the CDN. Open the report on a machine with internet access, or download `chart.umd.min.js` and adjust the script tag to point to a local copy.                                                     |

---

## License

See repository for license information.

## Acknowledgements

Powered by the [WhoisXML API](https://www.whoisxmlapi.com/). Charts rendered with [Chart.js 4](https://www.chartjs.org/). HTTP/2 support via [httpx](https://www.python-httpx.org/) + [h2](https://python-hyper.org/projects/h2/).
