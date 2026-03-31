#!/usr/bin/env python3
"""
NRD (Newly Registered Domains) Stream Client
WHOISXMLAPI.COM - Professional Services 03/31/2026.  Provided "as-is".
Connects to the WhoisXML API WebSocket stream and logs newly added domains.
  example: $ nrd2-readstream.py 
"""

import json
import sys
import signal
import logging
import threading
import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from io import TextIOWrapper
from queue import Queue, Empty
from websocket import create_connection, WebSocketTimeoutException, WebSocketConnectionClosedException

# ── Configuration ─────────────────────────────────────────────────────────────

API_KEY      = "YOUR_API_KEY_HERE" # or read from environment
WS_URL       = "wss://nrd-stream.whoisxmlapi.com/ultimate"
BUFFER_SIZE  = 500          # rows before flushing to disk
WS_TIMEOUT   = 2.0          # seconds between recv() polls
MAX_RETRIES  = 5            # reconnect attempts before giving up
RETRY_DELAY  = 5            # seconds between reconnect attempts
WRITE_QUEUE_MAX = 10_000    # max rows queued for the writer thread

REASONS = {"added", "discovered", "updated", "dropped"}

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Stats ─────────────────────────────────────────────────────────────────────

@dataclass
class Stats:
    transactions: int = 0
    records_total: int = 0
    counts: defaultdict = field(default_factory=lambda: defaultdict(int))

    def bump(self, reason: str) -> None:
        self.counts[reason] += 1

    def report(self) -> str:
        c = self.counts
        return (
            f"transactions={self.transactions}  total={self.records_total}  "
            f"added={c['added']}  discovered={c['discovered']}  "
            f"updated={c['updated']}  dropped={c['dropped']}  "
            f"unknown={c['unknown']}"
        )

# ── Writer thread ─────────────────────────────────────────────────────────────

class DomainWriter(threading.Thread):
    """Dedicated thread that owns all file I/O to avoid lock contention."""

    SENTINEL = None  # poison-pill to signal shutdown

    def __init__(self, filepath: str, queue: Queue, fmt: str = "CSV"):
        super().__init__(name="DomainWriter", daemon=True)
        self._filepath = filepath
        self._queue = queue
        self._fmt = fmt.upper()
        self._file: TextIOWrapper | None = None

    def _format_row(self, timestamp: str, reason: str, domain: str) -> str:
        if self._fmt == "JSON":
            return json.dumps({
                "timestamp": timestamp,
                "reason":    reason,
                "domain":    domain,
            }) + "\n"
        # CSV — quote domain in case it ever contains a comma
        return f'{timestamp},{reason},"{domain}"\n'

    def run(self) -> None:
        try:
            with open(self._filepath, "w", buffering=1) as f:
                if self._fmt == "CSV":
                    f.write("Timestamp,Reason,DomainName\n")

                buf: list[str] = []

                while True:
                    try:
                        item = self._queue.get(timeout=1.0)
                    except Empty:
                        # Flush partial buffer periodically even if quiet
                        if buf:
                            f.writelines(buf)
                            f.flush()
                            buf.clear()
                        continue

                    if item is self.SENTINEL:
                        break

                    buf.append(item)
                    if len(buf) >= BUFFER_SIZE:
                        f.writelines(buf)
                        f.flush()
                        buf.clear()

                # Drain remaining rows on shutdown
                if buf:
                    f.writelines(buf)
        except IOError as exc:
            log.error("Writer thread IO error: %s", exc)
        finally:
            log.info("Writer thread finished.")

    def enqueue(self, timestamp: str, reason: str, domain: str) -> None:
        self._queue.put(self._format_row(timestamp, reason, domain))

    def stop(self) -> None:
        self._queue.put(self.SENTINEL)
        self.join(timeout=10)

# ── WebSocket helpers ─────────────────────────────────────────────────────────

def connect(ws_url: str, api_key: str):
    """Create an authenticated WebSocket connection."""
    log.info("Connecting to %s ...", ws_url)
    ws = create_connection(ws_url)
    ws.settimeout(WS_TIMEOUT)
    ws.send(api_key)
    log.info("Authenticated — streaming NRD data (Ctrl+C to stop).")
    return ws


def process_record(raw: str, stats: Stats, writer: DomainWriter) -> None:
    """Parse one JSON line and dispatch it."""
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.warning("JSON decode error (record %d): %s", stats.records_total, exc)
        return

    reason    = record.get("reason", "unknown")
    domain    = record.get("domainName", "N/A")
    iana_id   = record.get("registrarIANAID", "N/A")
    registrar = record.get("registrarName", "N/A")

    stats.bump(reason if reason in REASONS else "unknown")
    stats.records_total += 1

    log.info("%-12s %s", reason, domain)

    if reason == "added":
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        writer.enqueue(ts, reason, domain)


def stream_loop(ws_url: str, api_key: str, writer: DomainWriter, stats: Stats,
                stop_event: threading.Event) -> None:
    """Main receive loop with automatic reconnection."""
    retries = 0

    while not stop_event.is_set():
        try:
            ws = connect(ws_url, api_key)
            retries = 0  # reset on successful connection

            while not stop_event.is_set():
                try:
                    payload = ws.recv()
                except WebSocketTimeoutException:
                    continue  # normal poll timeout — check stop_event
                except WebSocketConnectionClosedException:
                    log.warning("Connection closed by server.")
                    break

                stats.transactions += 1
                lines = [l.strip() for l in payload.splitlines() if l.strip()]

                for line in lines:
                    process_record(line, stats, writer)

                log.info(
                    "tx=%d  lines=%d  %s",
                    stats.transactions, len(lines), stats.report(),
                )

            ws.close()

        except ConnectionError as exc:
            log.error("Connection error: %s", exc)
        except Exception as exc:
            log.error("Unexpected error: %s", exc)

        if stop_event.is_set():
            break

        retries += 1
        if retries > MAX_RETRIES:
            log.error("Max retries (%d) reached — giving up.", MAX_RETRIES)
            break

        log.info("Reconnecting in %ds (attempt %d/%d)...", RETRY_DELAY, retries, MAX_RETRIES)
        stop_event.wait(RETRY_DELAY)

# ── Entry point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream newly registered domains from WhoisXML API.")
    parser.add_argument("output_file", help="Output file path.")
    parser.add_argument(
        "--outputFormat",
        choices=["CSV", "JSON"],
        default="CSV",
        metavar="CSV|JSON",
        help="Output format: CSV (default) or JSON (newline-delimited).",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug-level logging.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("Output format: %s", args.outputFormat)

    write_queue = Queue(maxsize=WRITE_QUEUE_MAX)
    writer      = DomainWriter(args.output_file, write_queue, fmt=args.outputFormat)
    stats       = Stats()
    stop_event  = threading.Event()

    def handle_signal(sig, frame):
        log.info("Shutdown signal received — stopping...")
        stop_event.set()

    signal.signal(signal.SIGINT,  handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    writer.start()

    try:
        stream_loop(WS_URL, API_KEY, writer, stats, stop_event)
    finally:
        writer.stop()
        log.info("Final stats: %s", stats.report())
        log.info("Output written to: %s", args.output_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
