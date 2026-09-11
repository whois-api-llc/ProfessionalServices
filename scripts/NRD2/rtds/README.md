# NRD Stream Dashboard

`nrd_stream_dashboard.py` is a terminal dashboard and file writer for the WHOISXMLAPI Newly Registered Domains (NRD) WebSocket stream.

It authenticates to the NRD Ultimate WebSocket endpoint, continuously receives newline-delimited JSON records, shows live operational health in the terminal, and writes **only `added` records** to a CSV file or newline-delimited JSON (NDJSON) file.

The dashboard is designed for long-running monitoring: it keeps the receiver independent of disk I/O, tracks reconnects and malformed messages, and sends a WebSocket ping after a configurable period of stream inactivity.

## What it shows

The full-screen terminal dashboard refreshes four times per second and includes:

| Area                      | Meaning                                                                                                                                                        |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Connection status         | Whether the client is connected and authenticated, connecting, reconnecting, or stopped after exhausting retries.                                              |
| Runtime                   | Wall-clock duration since the dashboard started.                                                                                                               |
| Transactions              | Number of WebSocket text/binary payloads received. A payload can contain several records.                                                                      |
| Records                   | Total JSON records successfully parsed from payloads.                                                                                                          |
| Written                   | Number of `added` records successfully flushed to the output file.                                                                                             |
| Queue                     | Pending output rows versus the 10,000-row queue capacity.                                                                                                      |
| Last transaction / record | Time elapsed since the last payload or parsed record.                                                                                                          |
| Keep-alives               | Count and time of WebSocket pings sent after an idle period. Pongs are listed in Recent events.                                                                |
| Record reasons            | Totals for `added`, `discovered`, `updated`, `dropped`, and unrecognized reason values.                                                                        |
| Latest stream records     | The six most recent parsed records, including time, reason, and domain. These are visible for every reason type, whether or not the record is written to disk. |
| Connection health         | Transmission, JSON decoding, writer, queue-drop, and reconnection counts, plus the most recent error message.                                                  |
| Recent events             | Connection, keep-alive, retry, shutdown, and error events.                                                                                                     |

Press `Ctrl+C` to stop. The receiver is stopped first and the writer then finishes rows already queued for output.

## Requirements

- Python **3.10 or newer**
- An active NRD Ultimate stream API key from WHOISXMLAPI
- Network access to `wss://nrd-stream.whoisxmlapi.com/ultimate`
- Packages listed in `requirements.txt`:
  - `websocket-client` — WebSocket transport
  - `rich` — live terminal dashboard

## Installation

From the directory containing the script:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Quick start

Set the API key in an environment variable, then provide the output filename:

```bash
export NRD_API_KEY="your-new-api-key"
python3 nrd_stream_dashboard.py test.csv
```

The default output is CSV. To write NDJSON instead:

```bash
python3 nrd_stream_dashboard.py --output-format JSON nrd-added.ndjson
```

### API-key handling

Prefer the `NRD_API_KEY` environment variable. It keeps the secret out of shell history, process listings, and most terminal titles.

The script also accepts `--api-key VALUE` for short-lived manual testing:

```bash
python3 nrd_stream_dashboard.py --api-key "your-new-api-key" test.csv
```

When this option is used, the program immediately re-executes itself with the value removed from its command-line arguments and placed in the process environment. This prevents the running process and dashboard title from retaining the API key, but it **cannot remove a value already recorded in your shell history**. Do not paste production keys into chat, tickets, or screenshots; regenerate a key if that happens.

## Command-line options

Run `python3 nrd_stream_dashboard.py --help` for the authoritative list.

| Option                      | Default                            | Description                                                                                                                       |
| --------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `output_file`               | Required                           | Destination file. It is created or overwritten at startup.                                                                        |
| `--output-format CSV`       | `CSV`                              | Output format: `CSV` or `JSON`. `JSON` means newline-delimited JSON / NDJSON. The legacy alias `--outputFormat` is also accepted. |
| `--api-key KEY`             | `NRD_API_KEY` environment variable | NRD stream API key. The environment variable is preferred.                                                                        |
| `--ws-timeout SECONDS`      | `2.0`                              | Time to wait for a received frame before the receiver checks shutdown and keep-alive timing.                                      |
| `--connect-timeout SECONDS` | `15.0`                             | Initial WebSocket connection timeout.                                                                                             |
| `--keepalive SECONDS`       | `30.0`                             | Idle time after the last stream payload before sending a WebSocket ping. It must be greater than `--ws-timeout`.                  |
| `--max-retries N`           | `5`                                | Maximum consecutive reconnect attempts after a connection failure.                                                                |
| `--retry-delay SECONDS`     | `5.0`                              | Delay between reconnect attempts.                                                                                                 |

The endpoint option is intentionally hidden from normal help but exists for controlled testing:

```bash
python3 nrd_stream_dashboard.py --ws-url wss://example.invalid/stream test.csv
```

## WebSocket protocol and expected messages

1. The client opens a TLS WebSocket connection to:

   ```text
   wss://nrd-stream.whoisxmlapi.com/ultimate
   ```

2. Immediately after connecting, it sends the API key as a WebSocket message to authenticate.

3. The service sends text or binary WebSocket payloads. The client treats each nonempty line in a payload as a separate JSON record.

4. A normal record is expected to be a JSON object containing at least:

   ```json
   {
     "reason": "added",
     "domainName": "example.com"
   }
   ```

   The dashboard recognizes `added`, `discovered`, `updated`, and `dropped`. Any other or missing reason is counted as `unknown`. A missing domain name is displayed as `N/A`.

5. If no stream payload arrives for the configured idle period, the client sends a WebSocket `PING` control frame. If the server responds with `PONG`, that is noted in Recent events. Receiving normal stream traffic also proves the connection is active and resets the idle timer.

6. If the server closes the socket or a transport error occurs, the client closes the current socket, updates the dashboard, waits for `--retry-delay`, and reconnects. A successful connection resets the consecutive retry count. The process stops after the configured retry limit is exceeded.

## Output behavior

The dashboard always counts and displays all recognized reason types. It intentionally writes **only records with `reason == "added"`** to the output file. This matches the use case of collecting newly added registrations without persisting discovered/updated/dropped events.

### CSV output

CSV output begins with:

```csv
Timestamp,Reason,DomainName
```

Example:

```csv
2026-09-10 14:02:31.184,added,"example.com"
```

The built-in CSV writer correctly escapes domains if they contain characters that require quoting.

### JSON output

`--output-format JSON` writes one JSON object per line:

```json
{
  "timestamp": "2026-09-10 14:02:31.184",
  "reason": "added",
  "domain": "example.com"
}
```

This is NDJSON, not a single JSON array, so it can be processed incrementally with tools such as `jq`, Logstash, or a streaming parser.

### Buffering and durability

The receive loop pushes `added` rows onto a bounded queue and a dedicated writer thread owns the file. This keeps slower disk writes from blocking the WebSocket receiver. The writer flushes when it reaches 500 rows, after one second of queue inactivity, and at shutdown.

The queue holds at most 10,000 rows. If it fills, the client waits up to 250 ms for capacity. If it remains full, that output row is dropped, and the dashboard increments both `Dropped rows` and writer/transmission error counters. Treat a nonzero dropped-row count as data loss requiring investigation.

The output file is opened in write mode at startup. Running the program again with the same filename overwrites the existing file. Use a unique filename or a rotation wrapper for continuous collection.

## Error handling and operational interpretation

| Dashboard indication                             | Meaning / next check                                                                                                                                                                   |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Transmission errors` increases                  | A connection, malformed JSON, or writer-related failure occurred. Read `Last error` and Recent events.                                                                                 |
| `Decode` increases                               | A line was not valid JSON or did not decode to an object. The bad record is not counted or written. Capture an example before treating it as an upstream contract change.              |
| `Writer` increases                               | The output file could not be written, or the writer queue overflowed. Check path permissions, free disk space, filesystem health, and output throughput.                               |
| `Dropped rows` increases                         | An `added` record was not written because the queue remained full. This is an output-data-loss signal.                                                                                 |
| `Reconnects` increases                           | The client had to reconnect after a socket or transport failure. Check endpoint reachability, proxy/load-balancer idle policies, API-key status, and the service-side connection logs. |
| `Last record` grows but connection remains green | The socket is open but no valid records have been parsed recently. A keep-alive should appear after the configured idle interval.                                                      |
| `Stopped: retry limit reached`                   | The client exhausted consecutive reconnect attempts and exited the stream loop. Correct the underlying failure, then restart it.                                                       |

<img width="954" height="424" alt="image" src="https://github.com/user-attachments/assets/a7326e85-c8cc-4bbb-b563-79722d0356dd" />

## Practical examples

Write default CSV with a 60-second idle ping:

```bash
export NRD_API_KEY="your-new-api-key"
python3 nrd_stream_dashboard.py --keepalive 60 nrd-added.csv
```

Use a slower reconnect cycle during a planned endpoint outage:

```bash
python3 nrd_stream_dashboard.py \
  --retry-delay 30 \
  --max-retries 20 \
  nrd-added.csv
```

Write NDJSON for a downstream ingestion pipeline:

```bash
python3 nrd_stream_dashboard.py \
  --output-format JSON \
  nrd-added.ndjson
```

## Limitations and design choices

- The client does not rotate files, resume an existing output file, or deduplicate domains. Those are intentional responsibilities for an external supervisor or downstream pipeline.
- Timestamps use the host machine's local time. Ensure system time/NTP is correct if the output is consumed across regions.
- The dashboard needs a terminal that supports ANSI control sequences. Use a normal interactive Terminal, iTerm2, Windows Terminal, or an SSH terminal with color support.
- The process is intended for a single stream connection. Run separate processes with separate output targets if multiple independent collections are required.
- `websocket-client` performs standard TLS handling. If your environment requires a proxy, custom CA bundle, or client certificate, extend the connection configuration deliberately rather than disabling certificate verification.

## Suggested production operation

Run under a service manager such as `systemd`, `supervisord`, Docker, or a process supervisor that restarts the process if it exits. Use a protected environment file for `NRD_API_KEY`, write output to a volume with monitored capacity, and alert on nonzero `Dropped rows`, repeated reconnects, writer errors, or an unexpectedly old `Last record` value.

For a noninteractive deployment, consider redirecting standard error to a log and use the output file plus external process monitoring as the source of truth. The dashboard itself is optimized for an operator-attended terminal.
