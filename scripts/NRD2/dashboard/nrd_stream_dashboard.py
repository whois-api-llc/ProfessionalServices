#!/usr/bin/env python3
"""NRD (Newly Registered Domains) Stream Client with a live terminal dashboard.

Requires: pip install websocket-client rich
Usage: NRD_API_KEY=... python nrd_stream_dashboard.py output.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import signal
import sys
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Any

from websocket import ABNF, create_connection
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException

try:
    from rich import box
    from rich.align import Align
    from rich.console import Group
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError as exc:  # Friendly, intentional failure instead of a traceback.
    raise SystemExit("Missing dependency: install it with `pip install rich websocket-client`") from exc


WS_URL = "wss://nrd-stream.whoisxmlapi.com/ultimate"
REASONS = ("added", "discovered", "updated", "dropped")
LOG = logging.getLogger("nrd_stream")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    seconds = max(0, int(seconds))
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def format_age(moment: float | None) -> str:
    return "never" if moment is None else f"{format_duration(time.monotonic() - moment)} ago"


@dataclass
class Stats:
    started_at: float = field(default_factory=time.monotonic)
    transactions: int = 0
    records_total: int = 0
    counts: Counter[str] = field(default_factory=Counter)
    reconnects: int = 0
    transmission_errors: int = 0
    decode_errors: int = 0
    writer_errors: int = 0
    dropped_rows: int = 0
    keepalives_sent: int = 0
    last_message_at: float | None = None
    last_transaction_at: float | None = None
    last_keepalive_at: float | None = None
    last_error: str = "None"
    connected: bool = False
    connection_state: str = "Starting"
    output_rows: int = 0
    recent_records: deque[tuple[str, str, str]] = field(default_factory=lambda: deque(maxlen=6))
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def event_error(self, message: str, *, writer: bool = False, decode: bool = False) -> None:
        with self.lock:
            self.transmission_errors += 1
            self.writer_errors += int(writer)
            self.decode_errors += int(decode)
            self.last_error = message

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "uptime": time.monotonic() - self.started_at,
                "transactions": self.transactions, "records_total": self.records_total,
                "counts": self.counts.copy(), "reconnects": self.reconnects,
                "transmission_errors": self.transmission_errors,
                "decode_errors": self.decode_errors, "writer_errors": self.writer_errors,
                "dropped_rows": self.dropped_rows, "keepalives_sent": self.keepalives_sent,
                "last_message_at": self.last_message_at,
                "last_transaction_at": self.last_transaction_at,
                "last_keepalive_at": self.last_keepalive_at, "last_error": self.last_error,
                "connected": self.connected, "connection_state": self.connection_state,
                "output_rows": self.output_rows,
                "recent_records": list(self.recent_records),
            }


class EventLog:
    def __init__(self, limit: int = 8) -> None:
        self._items: deque[tuple[str, str]] = deque(maxlen=limit)
        self._lock = threading.Lock()

    def add(self, level: str, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self._items.append((level, f"{stamp}  {message}"))
        getattr(LOG, level.lower(), LOG.info)(message)

    def snapshot(self) -> list[tuple[str, str]]:
        with self._lock:
            return list(self._items)


class DomainWriter(threading.Thread):
    """Owns file output so the WebSocket receiver stays responsive."""

    SENTINEL = object()

    def __init__(self, path: Path, queue: Queue[tuple[str, str, str] | object], fmt: str,
                 stats: Stats, events: EventLog) -> None:
        super().__init__(name="DomainWriter", daemon=True)
        self.path, self.queue, self.fmt, self.stats = path, queue, fmt, stats
        self.events = events

    def run(self) -> None:
        try:
            with self.path.open("w", newline="", encoding="utf-8", buffering=1) as handle:
                if self.fmt == "CSV":
                    csv.writer(handle).writerow(("Timestamp", "Reason", "DomainName"))
                buffer: list[tuple[str, str, str]] = []
                while True:
                    try:
                        item = self.queue.get(timeout=1)
                    except Empty:
                        item = None
                    if item is self.SENTINEL:
                        break
                    if item is not None:
                        buffer.append(item)  # type: ignore[arg-type]
                    if buffer and (len(buffer) >= 500 or item is None):
                        self._write_buffer(handle, buffer)
                        buffer.clear()
                if buffer:
                    self._write_buffer(handle, buffer)
        except OSError as exc:
            self.stats.event_error(f"Output write failed: {exc}", writer=True)
            self.events.add("ERROR", f"Output write failed: {exc}")
        finally:
            self.events.add("INFO", "Writer stopped.")

    def _write_buffer(self, handle: Any, rows: list[tuple[str, str, str]]) -> None:
        if self.fmt == "CSV":
            csv.writer(handle).writerows(rows)
        else:
            handle.writelines(json.dumps({"timestamp": ts, "reason": reason, "domain": domain}) + "\n"
                              for ts, reason, domain in rows)
        handle.flush()
        with self.stats.lock:
            self.stats.output_rows += len(rows)

    def enqueue(self, timestamp: str, reason: str, domain: str) -> None:
        try:
            self.queue.put((timestamp, reason, domain), timeout=0.25)
        except Full:
            with self.stats.lock:
                self.stats.dropped_rows += 1
            self.stats.event_error("Writer queue full; output row dropped", writer=True)
            self.events.add("WARNING", "Writer queue is full; an output row was dropped.")

    def stop(self) -> None:
        # The receiver has stopped, so this cannot race with new producers.
        self.queue.put(self.SENTINEL)
        self.join(timeout=15)


def process_record(raw: str, stats: Stats, writer: DomainWriter, events: EventLog) -> None:
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        stats.event_error(f"Invalid JSON: {exc.msg}", decode=True)
        events.add("WARNING", f"Discarded malformed JSON: {exc.msg}")
        return
    if not isinstance(record, dict):
        stats.event_error("JSON record is not an object", decode=True)
        events.add("WARNING", "Discarded JSON record that was not an object.")
        return
    reason = str(record.get("reason", "unknown"))
    domain = str(record.get("domainName", "N/A"))
    now = time.monotonic()
    with stats.lock:
        stats.records_total += 1
        stats.counts[reason if reason in REASONS else "unknown"] += 1
        stats.last_message_at = now
        stats.recent_records.append((datetime.now().strftime("%H:%M:%S"), reason, domain))
    if reason == "added":
        writer.enqueue(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], reason, domain)


def stream_loop(args: argparse.Namespace, writer: DomainWriter, stats: Stats,
                events: EventLog, stop_event: threading.Event) -> None:
    retries = 0
    while not stop_event.is_set():
        ws = None
        try:
            with stats.lock:
                stats.connection_state = "Connecting"
            events.add("INFO", f"Connecting to {args.ws_url}")
            ws = create_connection(args.ws_url, timeout=args.connect_timeout)
            ws.settimeout(args.ws_timeout)
            ws.send(args.api_key)
            with stats.lock:
                stats.connected, stats.connection_state = True, "Streaming"
            events.add("INFO", "Authenticated; stream is active.")
            retries = 0
            last_keepalive_check = time.monotonic()
            while not stop_event.is_set():
                try:
                    opcode, payload = ws.recv_data(control_frame=True)
                except WebSocketTimeoutException:
                    now = time.monotonic()
                    if now - last_keepalive_check >= args.keepalive:
                        ws.ping("nrd-dashboard")
                        with stats.lock:
                            stats.keepalives_sent += 1
                            stats.last_keepalive_at = now
                        events.add("INFO", "Keep-alive ping sent (no stream data received).")
                        last_keepalive_check = now
                    continue
                except WebSocketConnectionClosedException:
                    raise ConnectionError("Server closed the WebSocket")
                if opcode == ABNF.OPCODE_PONG:
                    events.add("INFO", "Keep-alive pong received.")
                    continue
                if opcode == ABNF.OPCODE_CLOSE:
                    raise ConnectionError("Server sent a close frame")
                if opcode not in (ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY):
                    continue
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8", errors="replace")
                now = time.monotonic()
                with stats.lock:
                    stats.transactions += 1
                    stats.last_transaction_at = now
                # Any stream traffic proves the connection is active; only ping after idle time.
                last_keepalive_check = now
                for line in (line.strip() for line in payload.splitlines()):
                    if line:
                        process_record(line, stats, writer, events)
        except (ConnectionError, OSError, WebSocketConnectionClosedException) as exc:
            stats.event_error(str(exc))
            events.add("WARNING", f"Connection problem: {exc}")
        except Exception as exc:
            stats.event_error(f"Unexpected: {exc}")
            events.add("ERROR", f"Unexpected stream error: {exc}")
        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass
            with stats.lock:
                stats.connected = False
        if stop_event.is_set():
            break
        retries += 1
        if retries > args.max_retries:
            with stats.lock:
                stats.connection_state = "Stopped: retry limit reached"
            events.add("ERROR", f"Retry limit ({args.max_retries}) reached; stopping.")
            return
        with stats.lock:
            stats.reconnects += 1
            stats.connection_state = f"Reconnecting ({retries}/{args.max_retries})"
        events.add("WARNING", f"Reconnecting in {args.retry_delay}s ({retries}/{args.max_retries}).")
        stop_event.wait(args.retry_delay)


def render_dashboard(stats: Stats, events: EventLog, queue: Queue[Any], output_path: Path) -> Layout:
    s = stats.snapshot()
    status = "[bold green]● CONNECTED[/]" if s["connected"] else "[bold yellow]● " + s["connection_state"] + "[/]"
    head = Table.grid(expand=True)
    head.add_column(justify="left"); head.add_column(justify="right")
    head.add_row("[bold cyan]NRD STREAM MONITOR[/]", status)
    head.add_row(f"[dim]Output:[/] {output_path}", f"[dim]Runtime:[/] [bold]{format_duration(s['uptime'])}[/]")
    activity = Table.grid(expand=True, padding=(0, 2))
    for _ in range(4): activity.add_column(justify="center")
    activity.add_row("[bold]Transactions[/]", "[bold]Records[/]", "[bold]Written[/]", "[bold]Queue[/]")
    activity.add_row(str(s["transactions"]), str(s["records_total"]), str(s["output_rows"]), f"{queue.qsize():,}/{queue.maxsize:,}")
    activity.add_row("[dim]Last transaction[/]", "[dim]Last record[/]", "[dim]Keep-alives[/]", "[dim]Last ping[/]")
    activity.add_row(format_age(s["last_transaction_at"]), format_age(s["last_message_at"]), str(s["keepalives_sent"]), format_age(s["last_keepalive_at"]))
    reasons = Table(box=box.SIMPLE_HEAD, expand=True)
    for label in ("Added", "Discovered", "Updated", "Dropped", "Unknown"):
        reasons.add_column(label, justify="center")
    c = s["counts"]
    reasons.add_row(*(f"[bold]{c[key.lower()]:,}[/]" for key in ("Added", "Discovered", "Updated", "Dropped", "Unknown")))
    error_style = "green" if not s["transmission_errors"] else "red"
    health = Text.from_markup(
        f"[bold {error_style}]Transmission errors: {s['transmission_errors']}[/]  "
        f"Decode: {s['decode_errors']}  Writer: {s['writer_errors']}  "
        f"Dropped rows: {s['dropped_rows']}  Reconnects: {s['reconnects']}\n"
        f"[dim]Last error:[/] {s['last_error']}"
    )
    latest = Table.grid(expand=True, padding=(0, 1))
    latest.add_column("Time", style="dim", no_wrap=True)
    latest.add_column("Reason", no_wrap=True)
    latest.add_column("Domain")
    for timestamp, reason, domain in reversed(s["recent_records"]):
        color = {"added": "green", "discovered": "cyan", "updated": "yellow", "dropped": "red"}.get(reason, "white")
        latest.add_row(timestamp, f"[{color}]{reason}[/]", domain)
    if not s["recent_records"]:
        latest.add_row("—", "—", "Waiting for stream records…")
    event_lines = []
    colors = {"ERROR": "red", "WARNING": "yellow", "INFO": "dim"}
    for level, message in events.snapshot():
        event_lines.append(Text.from_markup(f"[{colors.get(level, 'white')}]{message}[/]"))
    bottom = Layout()
    bottom.split_row(
        Layout(Panel(latest, title="Latest stream records", border_style="bright_black"), ratio=3),
        Layout(Panel(Group(*event_lines), title="Recent events", border_style="bright_black"), ratio=2),
    )
    layout = Layout()
    layout.split_column(
        Layout(Panel(head, border_style="cyan"), size=5),
        Layout(Panel(activity, title="Activity", border_style="blue"), size=7),
        Layout(Panel(reasons, title="Record reasons", border_style="blue"), size=6),
        Layout(Panel(health, title="Connection health", border_style=error_style), size=4),
        bottom,
    )
    return layout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream newly registered domains with a terminal dashboard.")
    parser.add_argument("output_file", type=Path, help="Destination CSV or NDJSON file.")
    parser.add_argument("--output-format", "--outputFormat", choices=("CSV", "JSON"), default="CSV", dest="output_format")
    parser.add_argument("--api-key", default=os.getenv("NRD_API_KEY"), help="API key (or set NRD_API_KEY).")
    parser.add_argument("--ws-url", default=WS_URL, help=argparse.SUPPRESS)
    parser.add_argument("--ws-timeout", type=float, default=2.0, help="Seconds between receive polls (default: 2).")
    parser.add_argument("--connect-timeout", type=float, default=15.0, help="Connection timeout in seconds.")
    parser.add_argument("--keepalive", type=float, default=30.0, help="Idle seconds before sending a WebSocket ping.")
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    return parser.parse_args()


def hide_api_key_from_process_arguments() -> None:
    """Re-exec without a secret in argv so terminal titles and `ps` do not expose it."""
    redacted_args: list[str] = []
    key: str | None = None
    index = 1
    while index < len(sys.argv):
        arg = sys.argv[index]
        if arg == "--api-key" and index + 1 < len(sys.argv):
            key = sys.argv[index + 1]
            index += 2
            continue
        if arg.startswith("--api-key="):
            key = arg.split("=", 1)[1]
            index += 1
            continue
        redacted_args.append(arg)
        index += 1
    if key is not None:
        environment = os.environ.copy()
        environment["NRD_API_KEY"] = key
        os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve()), *redacted_args], environment)


def main() -> int:
    hide_api_key_from_process_arguments()
    args = parse_args()
    if not args.api_key:
        raise SystemExit("No API key. Set NRD_API_KEY or pass --api-key.")
    if args.keepalive <= args.ws_timeout:
        raise SystemExit("--keepalive must be greater than --ws-timeout.")
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    stats, events, stop_event = Stats(), EventLog(), threading.Event()
    queue: Queue[tuple[str, str, str] | object] = Queue(maxsize=10_000)
    writer = DomainWriter(args.output_file, queue, args.output_format, stats, events)
    stream = threading.Thread(target=stream_loop, args=(args, writer, stats, events, stop_event), name="NRDReceiver", daemon=True)

    def stop(_: int, __: Any) -> None:
        events.add("INFO", "Shutdown requested; finishing queued output.")
        stop_event.set()
    signal.signal(signal.SIGINT, stop); signal.signal(signal.SIGTERM, stop)
    writer.start(); stream.start()
    try:
        with Live(render_dashboard(stats, events, queue, args.output_file), refresh_per_second=4, screen=True) as live:
            while stream.is_alive() and not stop_event.is_set():
                live.update(render_dashboard(stats, events, queue, args.output_file))
                time.sleep(0.25)
    finally:
        stop_event.set()
        stream.join(timeout=args.ws_timeout + 2)
        writer.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
