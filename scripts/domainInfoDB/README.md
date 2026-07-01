# WhoisXML Domain Info DB Downloader

Two interchangeable command-line tools for downloading the [WhoisXML API](https://www.whoisxmlapi.com/)
**Domain Info DB** weekly files for one or more dates from the download portal
at `https://download.whoisxmlapi.com/domaininfodb/`.

- **`wxa_domaininfo_dl.py`** — Python 3 implementation (uses `requests`).
- **`wxa_domaininfo_dl.sh`** — Bash implementation (uses `curl`, no third-party
  Python packages).

Both share the same command-line interface, the same file-selection logic, and
the same exit codes. Pick whichever fits the host: the Bash version has zero
Python dependencies; the Python version is easier to extend.

---

## What it does

The download directory is a plain Apache-style autoindex containing weekly
files whose names embed a `YYYY-MM-DD` date, for example:

```
domain_info.2026-06-01.weekly.jsonl.zst    225G
domain_names.2026-06-01.weekly.csv.zst     5.0G
stats.2026-06-01.weekly.txt                89K
...
readme.txt
sample_v1.jsonl
```

Given one or more `--date YYYY-MM-DD` values, the tool:

1. Fetches and parses the directory index (over HTTP Basic auth).
2. Selects **every** file whose name contains a requested date string. For
   `--date 2026-06-01` that is the `domain_info`, `domain_names`, and `stats`
   files for that date. Undated files such as `readme.txt` and the `sample_*`
   files are never matched.
3. Streams each selected file to `--path`, showing live progress.
4. Verifies each downloaded file against the server's reported size, then
   prints the total elapsed time.

> **Heads up on size.** The `domain_info.*.weekly.jsonl.zst` files are on the
> order of **200–240 GB each** (compressed). Make sure `--path` has room, and
> expect long runs. Resume (below) exists precisely because a connection drop
> at 200 GB is otherwise painful.

---

## Requirements

### Python version (`wxa_domaininfo_dl.py`)

- Python 3.7+
- The [`requests`](https://pypi.org/project/requests/) library:
  ```bash
  pip install requests
  ```

### Bash version (`wxa_domaininfo_dl.sh`)

- `bash` (uses arrays — not POSIX `sh`)
- `curl`
- GNU coreutils: `stat`, `date` (the script uses `stat -c%s` and `date -d`)
- `awk`, `sed`, `grep`

These are standard on Ubuntu/Debian/RHEL. The GNU coreutils requirement means
the Bash version targets **Linux**; it will not run unmodified on macOS/BSD,
where `stat` and `date` take different flags.

Make the scripts executable once:

```bash
chmod +x wxa_domaininfo_dl.py wxa_domaininfo_dl.sh
```

---

## Authentication

Both tools use the same WhoisXML download credentials (HTTP Basic auth). The
password can be supplied three ways, checked in this order:

1. `--password VALUE` on the command line.
2. The `WXA_DL_PASSWORD` environment variable.
3. An interactive prompt (no echo) if neither of the above is set.

**Keeping the password out of `ps`.** A password on the command line is normally
visible to any user via `ps`/`/proc`. Both tools avoid leaking it further:

- The **Bash** version never passes `-u user:pass` to `curl`. It writes the
  credentials to a `mktemp` config file with `umask 077` (mode `0600`), passes
  it via `curl -K`, and removes it on exit. Backslashes and quotes in the
  password are escaped for curl's config syntax.
- The **Python** version passes credentials in-process via `requests`.

For unattended/cron use, prefer the environment variable so the secret never
appears on a command line at all:

```bash
export WXA_DL_PASSWORD='your-password'
```

---

## Usage

```
wxa_domaininfo_dl.(py|sh) --user USER [--password PASS] --date YYYY-MM-DD --path DIR
                          [--url URL] [--include SUBSTR] [--exclude SUBSTR]
                          [--no-resume] [--retries N] [--dry-run]
```

### Options

| Option                 | Required | Description                                                                    |
| ---------------------- | -------- | ------------------------------------------------------------------------------ |
| `--user`, `--username` | yes      | HTTP Basic auth username.                                                      |
| `--password`           | no       | Password. Falls back to `$WXA_DL_PASSWORD`, then prompt.                       |
| `--date YYYY-MM-DD`    | yes      | Date to match in file names. **Repeatable** for multiple dates.                |
| `--path DIR`           | yes      | Destination directory (created if missing).                                    |
| `--url URL`            | no       | Base autoindex URL. Default: `https://download.whoisxmlapi.com/domaininfodb/`. |
| `--include SUBSTR`     | no       | Only download files whose name contains `SUBSTR`.                              |
| `--exclude SUBSTR`     | no       | Skip files whose name contains `SUBSTR`.                                       |
| `--no-resume`          | no       | Re-download from scratch instead of resuming `.part` files.                    |
| `--retries N`          | no       | Retry attempts per file on network error / truncation. Default: `5`.           |
| `--dry-run`            | no       | List the files that would be downloaded, then exit.                            |
| `-h`, `--help`         | no       | Show help.                                                                     |

---

## Examples

Download all files for one date:

```bash
./wxa_domaininfo_dl.sh --user U --password P --date 2026-06-01 --path /data/wxa
```

Multiple dates in one run (repeat `--date`):

```bash
./wxa_domaininfo_dl.py --user U --date 2026-06-01 --date 2026-06-08 --path /data/wxa
```

Only the large JSONL domain-info file (skip the CSV and stats):

```bash
./wxa_domaininfo_dl.sh --user U --date 2026-06-01 --include domain_info --path /data/wxa
```

Everything for a date except the stats text file:

```bash
./wxa_domaininfo_dl.py --user U --date 2026-06-01 --exclude stats --path /data/wxa
```

Preview what would be downloaded without transferring anything:

```bash
./wxa_domaininfo_dl.sh --user U --date 2026-06-01 --path /data/wxa --dry-run
```

Unattended (cron), credentials via environment, no terminal prompt:

```bash
# crontab: every Tuesday at 06:00, pull the previous Monday's files
0 6 * * 2 WXA_DL_PASSWORD='...' /opt/wxa/wxa_domaininfo_dl.sh \
    --user U --date "$(date -d 'last monday' +\%F)" \
    --path /data/wxa >> /var/log/wxa_dl.log 2>&1
```

---

## Output and progress

Each file is announced with an index header, then progress is shown while it
transfers, and a per-file summary is printed on completion:

```
[1/3] domain_info.2026-06-01.weekly.jsonl.zst
  -> https://download.whoisxmlapi.com/domaininfodb/domain_info.2026-06-01.weekly.jsonl.zst
  size: 225.00 GiB
  45.20 GiB / 225.00 GiB   20.1%  118.50 MiB/s  ETA 00:25:43
  done: 225.00 GiB in 00:32:15 (avg 119.10 MiB/s)
```

The run ends with a summary and the total wall-clock time:

```
============================================================
Completed 3/3 file(s), 230.00 GiB transferred.
Total time: 00:41:07
```

- **Interactive terminal:** progress updates in place (the Python version draws
  its own bytes/percent/rate/ETA line; the Bash version uses curl's native
  progress meter, which shows received bytes, speed, and time-left).
- **Redirected / cron (not a TTY):** in-place progress is suppressed so log
  files stay clean; you still get the per-file header and completion summary.

---

## How resume works

Downloads are written to `<name>.part` and only renamed to the final `<name>`
after the byte count matches the server's `Content-Length`. On a repeat run:

- A partial `.part` is continued from where it left off via an HTTP `Range`
  request (Bash: `curl -C -`; Python: an explicit `Range: bytes=N-` header).
- A `.part` that already matches the full size is finalized without
  re-downloading.
- An already-complete final file is skipped.

Resume is on by default. Use `--no-resume` to force a clean re-download.

If a transfer is truncated mid-stream, the tool retries (up to `--retries`),
resuming rather than restarting. If the final size still doesn't match, the
`.part` is left in place and the file is reported as failed so a later run can
finish it.

---

## Exit codes

| Code | Meaning                                                                       |
| ---- | ----------------------------------------------------------------------------- |
| `0`  | All matched files downloaded (or already present) successfully.               |
| `1`  | No files matched the date(s), or some files failed to download.               |
| `2`  | Usage error, authentication failure (401), or the index could not be fetched. |

This makes the tools safe to drive from cron or a wrapper: check `$?` and alert
on non-zero.

---

## File types in the Domain Info DB

For reference, the dated files you'll typically retrieve:

| Pattern                               | Contents                                                                   | Approx. size |
| ------------------------------------- | -------------------------------------------------------------------------- | ------------ |
| `domain_info.<date>.weekly.jsonl.zst` | Full WHOIS/domain records, one JSON object per line, Zstandard-compressed. | ~200–240 GB  |
| `domain_names.<date>.weekly.csv.zst`  | Domain name list, CSV, Zstandard-compressed.                               | ~4–5 GB      |
| `stats.<date>.weekly.txt`             | Weekly summary statistics.                                                 | KB–MB        |

To decompress a `.zst` file: `zstd -d file.jsonl.zst` (install `zstd` if needed).

---

## Troubleshooting

- **`authentication failed (401)`** — Check `--user` and the password source.
  Confirm the account has Domain Info DB download access.
- **`No files match date(s): ...`** — The exact `YYYY-MM-DD` string isn't in any
  file name yet. Weekly files publish a few days after the dated period; run
  `--dry-run` to see what the index currently offers.
- **Bash: `stat: invalid option` or `date: illegal option`** — You're likely on
  macOS/BSD. Use the Python version, or run on Linux (GNU coreutils).
- **Slow or stalling transfers** — The tool retries and resumes automatically;
  interrupt and re-run to continue where it left off. Files download one at a
  time (a single 200 GB transfer usually saturates the link on its own).
- **Disk fills up** — Check free space before starting; a single weekly
  `domain_info` file can exceed 200 GB, and the `.part` uses the same space.
