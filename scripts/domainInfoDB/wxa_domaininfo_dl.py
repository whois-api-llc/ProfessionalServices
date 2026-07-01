#!/usr/bin/env python3
"""
wxa_domaininfo_dl.py

Download the WhoisXML API Domain Info DB weekly files for a given date (or
dates) from an Apache-style autoindex behind HTTP Basic auth.

For each date YYYY-MM-DD, every file in the directory whose name contains that
date string is selected and downloaded to --path. That naturally picks up the
matching domain_info.<date>.weekly.jsonl.zst, domain_names.<date>.weekly.csv.zst
and stats.<date>.weekly.txt while ignoring readme/sample files.

Features
  * HTTP Basic auth (username/password on the CLI, env var, or interactive).
  * Streaming download (never buffers a whole file in memory).
  * Resume of partially-downloaded files via HTTP Range (default on).
  * Per-file live progress: name, bytes so far, %, current rate, ETA.
  * TTY-aware output (in-place line on a terminal, periodic lines otherwise).
  * Final size verification against the server's Content-Length.
  * Total wall-clock time printed at the end.

Examples
  ./wxa_domaininfo_dl.py --user U --password P --date 2026-06-01 --path /data
  ./wxa_domaininfo_dl.py --user U --date 2026-06-01 --date 2026-06-08 \
      --include domain_info --path /data --dry-run
"""

import argparse
import getpass
import os
import re
import sys
import time
from collections import deque
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, unquote

import requests
from requests.auth import HTTPBasicAuth

DEFAULT_BASE_URL = "https://download.whoisxmlapi.com/domaininfodb/"
CHUNK = 8 * 1024 * 1024          # 8 MiB read chunks — big files, keep overhead low
CONNECT_READ_TIMEOUT = (30, 120)  # (connect, read) seconds


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #
def human_bytes(n):
    n = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(n) < 1024.0 or unit == "PiB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0


def human_time(seconds):
    if seconds is None or seconds != seconds or seconds == float("inf"):
        return "--:--:--"
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# --------------------------------------------------------------------------- #
# Rolling-window rate meter (for a stable rate / ETA rather than lifetime avg)
# --------------------------------------------------------------------------- #
class RateMeter:
    def __init__(self, window=5.0):
        self.window = window
        self.samples = deque()  # (timestamp, cumulative_bytes)

    def update(self, now, cumulative_bytes):
        self.samples.append((now, cumulative_bytes))
        while len(self.samples) > 1 and now - self.samples[0][0] > self.window:
            self.samples.popleft()

    def rate(self):
        if len(self.samples) < 2:
            return 0.0
        t0, b0 = self.samples[0]
        t1, b1 = self.samples[-1]
        dt = t1 - t0
        return (b1 - b0) / dt if dt > 0 else 0.0


# --------------------------------------------------------------------------- #
# Directory index parsing
# --------------------------------------------------------------------------- #
class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, val in attrs:
            if key.lower() == "href" and val:
                self.hrefs.append(val)


def fetch_index(session, base_url):
    """Return a list of file names present in the autoindex at base_url."""
    resp = session.get(base_url, timeout=CONNECT_READ_TIMEOUT)
    resp.raise_for_status()
    parser = _LinkParser()
    parser.feed(resp.text)

    names = []
    seen = set()
    for href in parser.hrefs:
        # Skip Apache sort links (?C=N;O=D), parent dir, and absolute/other URLs.
        if href.startswith("?") or href.startswith("/"):
            continue
        if "://" in href:
            continue
        if href in ("../", "..") or href.endswith("/"):
            continue
        name = unquote(href)
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def valid_date(s):
    if not _DATE_RE.match(s):
        raise argparse.ArgumentTypeError(f"date must be YYYY-MM-DD, got: {s!r}")
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a real calendar date: {s!r}")
    return s


def select_files(names, dates, include=None, exclude=None):
    """Files whose name contains any requested date, with optional substring
    include/exclude filters. Returns a de-duplicated, sorted list."""
    chosen = []
    for name in names:
        if not any(d in name for d in dates):
            continue
        if include and include not in name:
            continue
        if exclude and exclude in name:
            continue
        chosen.append(name)
    return sorted(set(chosen))


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #
def _server_total_size(session, url):
    """Best-effort total size via HEAD; None if the server won't say."""
    try:
        r = session.head(url, timeout=CONNECT_READ_TIMEOUT, allow_redirects=True)
        if r.status_code == 200:
            cl = r.headers.get("Content-Length")
            if cl is not None:
                return int(cl)
    except requests.RequestException:
        pass
    return None


def _render_progress(name, done, total, meter, is_tty):
    rate = meter.rate()
    if total:
        pct = 100.0 * done / total
        eta = (total - done) / rate if rate > 0 else float("inf")
        line = (f"  {human_bytes(done)} / {human_bytes(total)}  "
                f"{pct:5.1f}%  {human_bytes(rate)}/s  ETA {human_time(eta)}")
    else:
        line = f"  {human_bytes(done)}  {human_bytes(rate)}/s  (size unknown)"
    if is_tty:
        sys.stdout.write("\r\033[K" + line)
    else:
        sys.stdout.write(line + "\n")
    sys.stdout.flush()


def download_file(session, url, dest_path, resume=True, retries=5):
    """Download url -> dest_path with resume + retries. Returns (bytes, seconds)."""
    part = dest_path + ".part"
    name = os.path.basename(dest_path)
    is_tty = sys.stdout.isatty()

    total = _server_total_size(session, url)
    existing = os.path.getsize(part) if os.path.exists(part) else 0

    # If we already have a complete-looking .part, just finalize it.
    if resume and total is not None and existing == total and existing > 0:
        os.replace(part, dest_path)
        print(f"  already complete ({human_bytes(existing)}); finalized.")
        return existing, 0.0
    if existing and (total is not None and existing > total):
        existing = 0  # corrupt/oversized partial — start over

    print(f"  -> {url}")
    if existing and resume:
        print(f"  resuming from {human_bytes(existing)}")

    last_err = None
    for attempt in range(retries + 1):
        headers = {}
        if resume and existing:
            headers["Range"] = f"bytes={existing}-"
        try:
            with session.get(url, headers=headers, stream=True,
                             timeout=CONNECT_READ_TIMEOUT) as r:
                # Already fully downloaded: server rejects the range.
                if r.status_code == 416 and total is not None and existing == total:
                    break
                # Server ignored our Range and is sending the whole file again.
                if headers.get("Range") and r.status_code == 200:
                    existing = 0
                r.raise_for_status()

                # Learn total from this response if HEAD didn't tell us.
                if total is None:
                    if r.status_code == 206:
                        cr = r.headers.get("Content-Range", "")
                        m = re.search(r"/(\d+)\s*$", cr)
                        if m:
                            total = int(m.group(1))
                    else:
                        cl = r.headers.get("Content-Length")
                        if cl is not None:
                            total = int(cl)

                mode = "ab" if (existing and r.status_code == 206) else "wb"
                if mode == "wb":
                    existing = 0

                meter = RateMeter()
                done = existing
                start = time.monotonic()
                last_draw = 0.0
                with open(part, mode) as fh:
                    for chunk in r.iter_content(chunk_size=CHUNK):
                        if not chunk:
                            continue
                        fh.write(chunk)
                        done += len(chunk)
                        now = time.monotonic()
                        meter.update(now, done)
                        interval = 0.2 if is_tty else 30.0
                        if now - last_draw >= interval:
                            _render_progress(name, done, total, meter, is_tty)
                            last_draw = now
                _render_progress(name, done, total, meter, is_tty)
                if is_tty:
                    sys.stdout.write("\n")
                elapsed = time.monotonic() - start

            # Verify and finalize.
            final = os.path.getsize(part)
            if total is not None and final != total:
                # Truncated mid-stream — set up a resume and retry.
                existing = final
                last_err = (f"size mismatch: got {final}, expected {total}")
                if attempt < retries:
                    print(f"  {last_err}; retrying ({attempt + 1}/{retries})")
                    time.sleep(min(2 ** attempt, 30))
                    continue
                raise IOError(last_err)

            os.replace(part, dest_path)
            avg = final / elapsed if elapsed > 0 else 0.0
            print(f"  done: {human_bytes(final)} in {human_time(elapsed)} "
                  f"(avg {human_bytes(avg)}/s)")
            return final, elapsed

        except (requests.RequestException, IOError) as exc:
            last_err = exc
            existing = os.path.getsize(part) if os.path.exists(part) else 0
            if attempt < retries:
                backoff = min(2 ** attempt, 30)
                print(f"  error: {exc}; resuming in {backoff}s "
                      f"({attempt + 1}/{retries})")
                time.sleep(backoff)
                continue
            raise

    # Reached only via the 416 "already complete" break.
    if os.path.exists(part):
        os.replace(part, dest_path)
    size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
    print(f"  already complete ({human_bytes(size)}).")
    return size, 0.0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Download WhoisXML Domain Info DB files for a given date.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--user", "--username", dest="user", required=True,
                   help="HTTP Basic auth username")
    p.add_argument("--password", dest="password",
                   help="HTTP Basic auth password. If omitted, uses "
                        "$WXA_DL_PASSWORD or prompts. Note: a password given "
                        "here is visible in `ps`.")
    p.add_argument("--date", dest="dates", action="append", type=valid_date,
                   required=True, metavar="YYYY-MM-DD",
                   help="Date to match in file names. Repeatable.")
    p.add_argument("--path", required=True,
                   help="Destination directory for downloaded files")
    p.add_argument("--url", default=DEFAULT_BASE_URL,
                   help="Base autoindex URL")
    p.add_argument("--include", default=None,
                   help="Only download files whose name contains this substring")
    p.add_argument("--exclude", default=None,
                   help="Skip files whose name contains this substring")
    p.add_argument("--no-resume", dest="resume", action="store_false",
                   help="Re-download from scratch instead of resuming .part files")
    p.add_argument("--retries", type=int, default=5,
                   help="Retry attempts per file on network error / truncation")
    p.add_argument("--dry-run", action="store_true",
                   help="List the files that would be downloaded, then exit")
    return p.parse_args(argv)


def resolve_password(args):
    if args.password:
        return args.password
    env = os.environ.get("WXA_DL_PASSWORD")
    if env:
        return env
    return getpass.getpass(f"Password for {args.user}: ")


def main(argv=None):
    args = parse_args(argv)
    base_url = args.url if args.url.endswith("/") else args.url + "/"
    password = resolve_password(args)

    session = requests.Session()
    session.auth = HTTPBasicAuth(args.user, password)
    session.headers.update({"User-Agent": "wxa-domaininfo-dl/1.0"})

    print(f"Indexing {base_url} ...")
    try:
        names = fetch_index(session, base_url)
    except requests.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else "?"
        if code == 401:
            print("Authentication failed (401). Check --user / --password.",
                  file=sys.stderr)
        else:
            print(f"Failed to fetch index: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"Failed to fetch index: {exc}", file=sys.stderr)
        return 2

    targets = select_files(names, args.dates, args.include, args.exclude)
    if not targets:
        print(f"No files match date(s) {', '.join(args.dates)}"
              + (f" with include={args.include!r}" if args.include else "")
              + (f" exclude={args.exclude!r}" if args.exclude else "")
              + ".")
        return 1

    print(f"Matched {len(targets)} file(s):")
    for name in targets:
        print(f"  {name}")

    if args.dry_run:
        print("\n(dry run — nothing downloaded)")
        return 0

    os.makedirs(args.path, exist_ok=True)

    overall_start = time.monotonic()
    grand_bytes = 0
    ok = 0
    for i, name in enumerate(targets, 1):
        url = urljoin(base_url, name)
        dest = os.path.join(args.path, name)
        print(f"\n[{i}/{len(targets)}] {name}")
        if os.path.exists(dest):
            print(f"  exists, skipping: {dest}")
            ok += 1
            continue
        try:
            nbytes, _ = download_file(session, url, dest,
                                      resume=args.resume, retries=args.retries)
            grand_bytes += nbytes
            ok += 1
        except Exception as exc:  # noqa: BLE001 - report and continue to next file
            print(f"  FAILED: {exc}", file=sys.stderr)

    total_elapsed = time.monotonic() - overall_start
    print("\n" + "=" * 60)
    print(f"Completed {ok}/{len(targets)} file(s), "
          f"{human_bytes(grand_bytes)} transferred.")
    print(f"Total time: {human_time(total_elapsed)}")
    return 0 if ok == len(targets) else 1


if __name__ == "__main__":
    sys.exit(main())
