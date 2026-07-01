#!/usr/bin/env bash
#
# wxa_domaininfo_dl.sh
#
# Download the WhoisXML API Domain Info DB weekly files for a given date (or
# dates) from an Apache-style autoindex behind HTTP Basic auth.
#
# For each date YYYY-MM-DD, every file in the directory whose name contains that
# date string is downloaded to --path. That picks up the matching
# domain_info.<date>.weekly.jsonl.zst, domain_names.<date>.weekly.csv.zst and
# stats.<date>.weekly.txt while ignoring readme/sample files.
#
# Features
#   * HTTP Basic auth (CLI, $WXA_DL_PASSWORD, or interactive prompt).
#   * Credentials passed via a 0600 curl config file, NOT the command line,
#     so the password never appears in `ps`.
#   * Streaming download; resume of partial files via curl -C - (default on).
#   * Per-file progress: curl's live meter (bytes, speed, ETA) on a terminal;
#     a compact one-line-per-file summary when output is redirected (cron).
#   * Final size verification against the server's Content-Length.
#   * Total wall-clock time printed at the end.
#
# Requires: bash, curl, coreutils (stat, date), awk, sed, grep.
#
# Examples
#   ./wxa_domaininfo_dl.sh --user U --password P --date 2026-06-01 --path /data
#   ./wxa_domaininfo_dl.sh --user U --date 2026-06-01 --date 2026-06-08 \
#       --include domain_info --path /data --dry-run

set -uo pipefail

DEFAULT_BASE_URL="https://download.whoisxmlapi.com/domaininfodb/"
PROG="$(basename "$0")"

# ---- defaults --------------------------------------------------------------
user=""
password=""
declare -a dates=()
path=""
base_url="$DEFAULT_BASE_URL"
include=""
exclude=""
resume=1
retries=5
dry_run=0

# ---- helpers ---------------------------------------------------------------
die() { printf '%s: %s\n' "$PROG" "$*" >&2; exit 2; }

usage() {
    cat <<EOF
Usage: $PROG --user USER [--password PASS] --date YYYY-MM-DD --path DIR
             [--url URL] [--include SUBSTR] [--exclude SUBSTR]
             [--no-resume] [--retries N] [--dry-run]

  --user, --username   HTTP Basic auth username (required)
  --password           HTTP Basic auth password. If omitted, uses
                       \$WXA_DL_PASSWORD or prompts. (CLI value avoids \`ps\`
                       exposure because it is written to a 0600 config file.)
  --date YYYY-MM-DD    Date to match in file names. Repeatable. (required)
  --path DIR           Destination directory (required)
  --url URL            Base autoindex URL (default: $DEFAULT_BASE_URL)
  --include SUBSTR     Only files whose name contains SUBSTR
  --exclude SUBSTR     Skip files whose name contains SUBSTR
  --no-resume          Re-download from scratch instead of resuming .part files
  --retries N          Retry attempts per file (default: 5)
  --dry-run            List files that would be downloaded, then exit
  -h, --help           This help
EOF
}

# Human-readable byte count.
human_bytes() {
    awk -v b="$1" 'BEGIN{
        split("B KiB MiB GiB TiB PiB", u, " "); i=1;
        while (b>=1024 && i<6){ b/=1024; i++ }
        if (i==1) printf "%d %s", b, u[i]; else printf "%.2f %s", b, u[i]
    }'
}

# Seconds -> HH:MM:SS
human_time() {
    local s=$1
    printf '%02d:%02d:%02d' $(( s/3600 )) $(( (s%3600)/60 )) $(( s%60 ))
}

# ---- argument parsing ------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --user|--username) user="${2:-}"; shift 2 ;;
        --password)        password="${2:-}"; shift 2 ;;
        --date)            dates+=("${2:-}"); shift 2 ;;
        --path)            path="${2:-}"; shift 2 ;;
        --url)             base_url="${2:-}"; shift 2 ;;
        --include)         include="${2:-}"; shift 2 ;;
        --exclude)         exclude="${2:-}"; shift 2 ;;
        --no-resume)       resume=0; shift ;;
        --retries)         retries="${2:-}"; shift 2 ;;
        --dry-run)         dry_run=1; shift ;;
        -h|--help)         usage; exit 0 ;;
        *)                 die "unknown argument: $1" ;;
    esac
done

[[ -n "$user" ]]              || die "--user is required"
[[ ${#dates[@]} -gt 0 ]]      || die "at least one --date is required"
[[ -n "$path" ]]              || die "--path is required"
[[ "$retries" =~ ^[0-9]+$ ]]  || die "--retries must be an integer"
command -v curl >/dev/null    || die "curl is required but not found"

# Validate dates: format then real calendar date (GNU date if available).
for d in "${dates[@]}"; do
    [[ "$d" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] \
        || die "date must be YYYY-MM-DD, got: '$d'"
    if date -d "$d" +%F >/dev/null 2>&1; then
        :  # GNU date validated it
    fi
done

# Normalise base URL to a trailing slash.
[[ "$base_url" == */ ]] || base_url="${base_url}/"

# ---- credentials -----------------------------------------------------------
if [[ -z "$password" ]]; then
    if [[ -n "${WXA_DL_PASSWORD:-}" ]]; then
        password="$WXA_DL_PASSWORD"
    else
        read -rsp "Password for $user: " password </dev/tty; echo
    fi
fi

# Write credentials to a private curl config file so they never hit `ps`.
umask 077
conf="$(mktemp "${TMPDIR:-/tmp}/wxadl.XXXXXX")" || die "mktemp failed"
cleanup() { rm -f "$conf"; }
trap cleanup EXIT INT TERM
# Escape backslashes and double-quotes for curl config quoting rules.
esc_user=${user//\\/\\\\}; esc_user=${esc_user//\"/\\\"}
esc_pass=${password//\\/\\\\}; esc_pass=${esc_pass//\"/\\\"}
printf 'user = "%s:%s"\n' "$esc_user" "$esc_pass" > "$conf"

# ---- index fetch + selection ----------------------------------------------
echo "Indexing ${base_url} ..."
index_body="$(mktemp "${TMPDIR:-/tmp}/wxaidx.XXXXXX")" || die "mktemp failed"
trap 'rm -f "$conf" "$index_body"' EXIT INT TERM

http_code="$(curl -sS -L -K "$conf" -o "$index_body" -w '%{http_code}' "$base_url")" \
    || die "failed to fetch index (network error)"

case "$http_code" in
    200) ;;
    401) die "authentication failed (401). Check --user / --password." ;;
    *)   die "failed to fetch index: HTTP $http_code" ;;
esac

# Parse hrefs, dropping sort links (?...), parent/absolute (/...), and dirs.
mapfile -t all_files < <(
    grep -oiE 'href="[^"?/][^"]*"' "$index_body" \
        | sed -E 's/^href="//I; s/"$//' \
        | grep -vE '/$' \
        | sort -u
)

# Filter to files matching a requested date + include/exclude.
declare -a targets=()
for f in "${all_files[@]}"; do
    matched=0
    for d in "${dates[@]}"; do
        [[ "$f" == *"$d"* ]] && { matched=1; break; }
    done
    [[ $matched -eq 1 ]] || continue
    [[ -n "$include" && "$f" != *"$include"* ]] && continue
    [[ -n "$exclude" && "$f" == *"$exclude"* ]] && continue
    targets+=("$f")
done

if [[ ${#targets[@]} -eq 0 ]]; then
    printf 'No files match date(s): %s' "${dates[*]}"
    [[ -n "$include" ]] && printf " include='%s'" "$include"
    [[ -n "$exclude" ]] && printf " exclude='%s'" "$exclude"
    printf '\n'
    exit 1
fi

printf 'Matched %d file(s):\n' "${#targets[@]}"
for f in "${targets[@]}"; do printf '  %s\n' "$f"; done

if [[ $dry_run -eq 1 ]]; then
    echo; echo "(dry run — nothing downloaded)"
    exit 0
fi

mkdir -p "$path" || die "cannot create --path: $path"

# ---- remote size (best effort via HEAD) ------------------------------------
remote_size() {
    curl -sS -L -I -K "$conf" "$1" 2>/dev/null | tr -d '\r' \
        | awk 'tolower($1)=="content-length:"{v=$2} END{ if (v!="") print v }'
}

# ---- download one file -----------------------------------------------------
GRAND_BYTES=0
OK=0
download_one() {
    local url="$1" dest="$2"
    local part="${dest}.part"
    local rsize; rsize="$(remote_size "$url")"

    # Already have a complete final file?
    if [[ -f "$dest" ]]; then
        if [[ -n "$rsize" && "$(stat -c%s "$dest")" == "$rsize" ]]; then
            echo "  exists, skipping ($(human_bytes "$rsize"))"
            GRAND_BYTES=$(( GRAND_BYTES + rsize )); OK=$(( OK + 1 )); return 0
        elif [[ -z "$rsize" ]]; then
            echo "  exists, skipping"; OK=$(( OK + 1 )); return 0
        fi
    fi

    # Already have a complete .part (from a prior run)? Just finalise.
    if [[ $resume -eq 1 && -f "$part" && -n "$rsize" \
          && "$(stat -c%s "$part")" == "$rsize" ]]; then
        mv -f "$part" "$dest"
        echo "  already complete ($(human_bytes "$rsize")); finalized."
        GRAND_BYTES=$(( GRAND_BYTES + rsize )); OK=$(( OK + 1 )); return 0
    fi

    [[ -n "$rsize" ]] && echo "  size: $(human_bytes "$rsize")"
    if [[ $resume -eq 1 && -f "$part" ]]; then
        echo "  resuming from $(human_bytes "$(stat -c%s "$part")")"
    fi

    local -a opts=( -f -L -K "$conf" -o "$part"
                    --retry "$retries" --retry-delay 5 --retry-connrefused )
    [[ $resume -eq 1 ]] && opts+=( -C - )
    if [[ -t 1 ]]; then
        :                       # interactive: curl shows its live progress meter
    else
        opts+=( -sS )           # redirected/cron: quiet but still report errors
    fi

    local t0 t1 elapsed
    t0="$(date +%s)"
    if ! curl "${opts[@]}" "$url"; then
        echo "  FAILED: curl error downloading $url" >&2
        return 1
    fi
    t1="$(date +%s)"; elapsed=$(( t1 - t0 ))

    # Verify size before finalising.
    local got; got="$(stat -c%s "$part" 2>/dev/null || echo 0)"
    if [[ -n "$rsize" && "$got" != "$rsize" ]]; then
        echo "  FAILED: size mismatch (got $got, expected $rsize); kept $part" >&2
        return 1
    fi

    mv -f "$part" "$dest"
    local avg="n/a"
    [[ $elapsed -gt 0 ]] && avg="$(human_bytes $(( got / elapsed )))/s"
    echo "  done: $(human_bytes "$got") in $(human_time "$elapsed") (avg $avg)"
    GRAND_BYTES=$(( GRAND_BYTES + got )); OK=$(( OK + 1 )); return 0
}

# ---- main loop -------------------------------------------------------------
overall_start="$(date +%s)"
i=0
for name in "${targets[@]}"; do
    i=$(( i + 1 ))
    url="${base_url}${name}"
    dest="${path%/}/${name}"
    printf '\n[%d/%d] %s\n' "$i" "${#targets[@]}" "$name"
    echo "  -> $url"
    download_one "$url" "$dest" || true    # report and continue to next file
done
overall_elapsed=$(( $(date +%s) - overall_start ))

echo
printf '%s\n' "============================================================"
printf 'Completed %d/%d file(s), %s transferred.\n' \
    "$OK" "${#targets[@]}" "$(human_bytes "$GRAND_BYTES")"
printf 'Total time: %s\n' "$(human_time "$overall_elapsed")"

[[ "$OK" -eq "${#targets[@]}" ]] && exit 0 || exit 1
