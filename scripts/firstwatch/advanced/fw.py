#!/usr/bin/env python3
"""
FirstWatch batch domain tool (JWT Bearer auth) – FULL SCRIPT (with STIX 2.1 Bundle output)
(C)2025-2026 WHOISXMLAPI.COM

Environment (new):
  Base URL: https://chaos.yatic.io/api/firstwatch
  Login:    POST /login   (application/x-www-form-urlencoded) -> {"token": "..."}
  Quota:    GET  /user/quota
  Check:    GET  /feed/check/{domain}
  Search:   GET  /feed/search/{query}

Output formats:
- csv  : row-based, includes payload_json column
- json : JSONL (newline-delimited JSON objects)
- stix : STIX 2.1 Bundle JSON (single JSON file)

STIX behavior (from config):
- TLP marking from [stix].tlp  (clear|green|amber|red)
- Indicator classification from [stix].classification
  - If it's a known STIX indicator_types value, it becomes indicator_types.
  - Otherwise it becomes a label (and indicator_types defaults to ["unknown"]).

Usage:
  python fw.py domains.csv results.csv
  python fw.py --fuzzy domains.csv results.jsonl
  python fw.py --output-format stix domains.csv firstwatch_bundle.json
  python fw.py --fallback-fuzzy domains.csv results.csv
  python fw.py --create-config
"""

from __future__ import annotations

import argparse
import configparser
import csv
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests


DEFAULT_BASE_URL = "https://chaos.yatic.io/api/firstwatch"
DEFAULT_DELAY_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 2  # retries for 429/5xx (not auth refresh)

# STIX vocab helpers (STIX 2.1 indicator_types open vocab; these are common/expected values)
KNOWN_INDICATOR_TYPES = {
    "anomalous-activity",
    "benign",
    "compromised",
    "malicious-activity",
    "unknown",
}
KNOWN_TLP = {"clear", "green", "amber", "red"}


# ----------------------------
# Config model
# ----------------------------
@dataclass
class FWConfig:
    username: str
    password: str

    base_url: str = DEFAULT_BASE_URL
    delay: float = DEFAULT_DELAY_SECONDS
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES

    # Optional behavior
    check_quota_before_run: bool = True
    stop_if_quota_insufficient: bool = False

    # Output defaults (CLI can override)
    output_format: str = "csv"  # "csv" or "json"(JSONL) or "stix"(bundle)

    # STIX config
    stix_tlp: str = "clear"  # clear|green|amber|red
    stix_classification: str = "malicious-activity"  # indicator_types or custom label
    stix_identity_name: str = "FirstWatch"
    stix_labels: List[str] = None  # extra labels (optional)

    @property
    def login_url(self) -> str:
        return f"{self.base_url}/login"

    @property
    def quota_url(self) -> str:
        return f"{self.base_url}/user/quota"

    @property
    def feed_check_url(self) -> str:
        return f"{self.base_url}/feed/check"

    @property
    def feed_search_url(self) -> str:
        return f"{self.base_url}/feed/search"


def _parse_csv_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def load_config(config_file: str = "firstwatch.conf") -> FWConfig:
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found")

    cp = configparser.ConfigParser()
    cp.read(config_file)

    if "credentials" not in cp:
        raise ValueError("Missing [credentials] section in configuration file")

    creds = cp["credentials"]
    for key in ("username", "password"):
        if key not in creds or not creds[key].strip():
            raise ValueError(f"Missing '{key}' in [credentials] section")

    cfg = FWConfig(
        username=creds["username"].strip(),
        password=creds["password"].strip(),
        stix_labels=[],
    )

    if "api" in cp:
        api = cp["api"]
        if api.get("base_url", "").strip():
            cfg.base_url = api["base_url"].strip().rstrip("/")
        if api.get("delay", "").strip():
            cfg.delay = float(api["delay"].strip())
        if api.get("timeout", "").strip():
            cfg.timeout = int(api["timeout"].strip())
        if api.get("max_retries", "").strip():
            cfg.max_retries = int(api["max_retries"].strip())
        if api.get("check_quota_before_run", "").strip():
            cfg.check_quota_before_run = api.getboolean("check_quota_before_run")
        if api.get("stop_if_quota_insufficient", "").strip():
            cfg.stop_if_quota_insufficient = api.getboolean("stop_if_quota_insufficient")

    if "output" in cp:
        out = cp["output"]
        if out.get("output_format", "").strip():
            val = out["output_format"].strip().lower()
            if val not in ("csv", "json", "stix"):
                raise ValueError("Invalid [output].output_format. Use 'csv', 'json', or 'stix'.")
            cfg.output_format = val

    if "stix" in cp:
        st = cp["stix"]
        if st.get("tlp", "").strip():
            tlp = st["tlp"].strip().lower()
            if tlp not in KNOWN_TLP:
                raise ValueError("Invalid [stix].tlp. Use clear|green|amber|red.")
            cfg.stix_tlp = tlp

        if st.get("classification", "").strip():
            cfg.stix_classification = st["classification"].strip()

        if st.get("identity_name", "").strip():
            cfg.stix_identity_name = st["identity_name"].strip()

        if st.get("labels", "").strip():
            cfg.stix_labels = _parse_csv_list(st["labels"].strip())

    return cfg


# ----------------------------
# Input domains
# ----------------------------
def _looks_like_domain(s: str) -> bool:
    s = s.strip().lower()
    if not s or " " in s or "/" in s:
        return False
    return "." in s and all(ch.isalnum() or ch in ".-_" for ch in s)


def load_domains_from_csv(csv_file: str) -> List[str]:
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Input file '{csv_file}' not found")

    domains: List[str] = []
    with open(csv_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        first = next(reader, None)

        # Header detection: if first row doesn't look like a domain, skip it.
        if first and first[0].strip():
            if _looks_like_domain(first[0]):
                domains.append(first[0].strip())

        for row in reader:
            if not row:
                continue
            val = row[0].strip()
            if val:
                domains.append(val)

    # Normalize + de-dupe preserving order
    out: List[str] = []
    seen = set()
    for d in domains:
        d2 = d.strip().lower()
        if not d2:
            continue
        if d2 in seen:
            continue
        seen.add(d2)
        out.append(d2)
    return out


# ----------------------------
# Output (CSV / JSONL)
# ----------------------------
OUTPUT_HEADER = [
    "timestamp_utc",
    "input_query",
    "matched_domain",
    "mode",
    "status",
    "http_status",
    "error",
    "payload_json",
]


def write_results_header_csv(fh) -> None:
    csv.writer(fh).writerow(OUTPUT_HEADER)
    fh.flush()


def write_result_csv(fh, row: List[Any]) -> None:
    csv.writer(fh).writerow(row)
    fh.flush()


def write_result_jsonl(fh, obj: Dict[str, Any]) -> None:
    fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    fh.flush()


def build_record(
    *,
    input_query: str,
    matched_domain: str,
    mode: str,  # "exact" or "fuzzy"
    status: str,  # "success" or "failed"
    http_status: int,
    error: str,
    payload: Any,
) -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_query": input_query,
        "matched_domain": matched_domain,
        "mode": mode,
        "status": status,
        "http_status": http_status,
        "error": error,
        "payload": payload,
    }


def write_record(fh, output_format: str, record: Dict[str, Any]) -> None:
    if output_format == "json":
        write_result_jsonl(fh, record)
        return

    # CSV
    payload = record.get("payload", None)
    payload_json = ""
    if payload is not None:
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    row = [
        record.get("timestamp_utc", ""),
        record.get("input_query", ""),
        record.get("matched_domain", ""),
        record.get("mode", ""),
        record.get("status", ""),
        record.get("http_status", ""),
        record.get("error", ""),
        payload_json,
    ]
    write_result_csv(fh, row)


# ----------------------------
# STIX 2.1 Bundle Builder
# ----------------------------
def _utc_now_z() -> str:
    # STIX typically uses Zulu timestamps
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class StixBundleBuilder:
    """
    Builds a STIX 2.1 bundle:
      - identity (producer)
      - marking-definition (TLP)
      - domain-name (SCO)
      - indicator (SDO)
      - relationship indicator -> domain-name (based-on)
    """

    def __init__(self, *, identity_name: str, tlp: str, classification: str, labels: Optional[List[str]] = None):
        self.identity_name = identity_name
        self.tlp = tlp.lower()
        self.classification = classification.strip()
        self.labels = labels or []

        if self.tlp not in KNOWN_TLP:
            raise ValueError("TLP must be one of clear|green|amber|red")

        self.objects: List[Dict[str, Any]] = []
        self.domain_id_by_value: Dict[str, str] = {}

        now = _utc_now_z()

        self.identity_id = f"identity--{uuid.uuid4()}"
        self.marking_id = f"marking-definition--{uuid.uuid4()}"

        self.objects.append({
            "type": "identity",
            "spec_version": "2.1",
            "id": self.identity_id,
            "created": now,
            "modified": now,
            "name": self.identity_name,
            "identity_class": "organization",
        })

        # TLP marking definition
        self.objects.append({
            "type": "marking-definition",
            "spec_version": "2.1",
            "id": self.marking_id,
            "created": now,
            "definition_type": "tlp",
            "definition": {"tlp": self.tlp},
        })

        # Determine how to represent "classification"
        cls_lower = self.classification.lower()
        if cls_lower in KNOWN_INDICATOR_TYPES:
            self.indicator_types = [cls_lower]
            self.class_label = None
        else:
            # Not a known indicator type: keep it as a label; use unknown indicator_types
            self.indicator_types = ["unknown"]
            self.class_label = self.classification

    def add_hit(self, *, domain: str, source_payload: Dict[str, Any], mode: str) -> None:
        """
        Add one 'hit' for a domain (from exact or fuzzy).
        """
        domain_value = domain.strip().lower()
        if not domain_value:
            return

        now = _utc_now_z()

        # Domain SCO (de-dupe)
        domain_id = self.domain_id_by_value.get(domain_value)
        if not domain_id:
            domain_id = f"domain-name--{uuid.uuid4()}"
            self.domain_id_by_value[domain_value] = domain_id
            self.objects.append({
                "type": "domain-name",
                "spec_version": "2.1",
                "id": domain_id,
                "value": domain_value,
                "object_marking_refs": [self.marking_id],
            })

        # Indicator SDO
        ind_id = f"indicator--{uuid.uuid4()}"
        ind_labels = ["firstwatch-hit"]
        if mode:
            ind_labels.append(f"mode:{mode}")
        ind_labels.extend(self.labels)
        if self.class_label:
            ind_labels.append(self.class_label)

        indicator = {
            "type": "indicator",
            "spec_version": "2.1",
            "id": ind_id,
            "created": now,
            "modified": now,
            "name": f"FirstWatch domain indicator: {domain_value}",
            "description": "Indicator generated from FirstWatch feed results.",
            "pattern_type": "stix",
            "pattern": f"[domain-name:value = '{domain_value}']",
            "valid_from": now,
            "indicator_types": self.indicator_types,
            "labels": ind_labels,
            "created_by_ref": self.identity_id,
            "object_marking_refs": [self.marking_id],
            # Custom property for raw payload
            "x_firstwatch": source_payload,
        }
        self.objects.append(indicator)

        # Relationship: indicator based-on domain-name
        self.objects.append({
            "type": "relationship",
            "spec_version": "2.1",
            "id": f"relationship--{uuid.uuid4()}",
            "created": now,
            "modified": now,
            "relationship_type": "based-on",
            "source_ref": ind_id,
            "target_ref": domain_id,
            "created_by_ref": self.identity_id,
            "object_marking_refs": [self.marking_id],
        })

    def bundle(self) -> Dict[str, Any]:
        return {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "spec_version": "2.1",
            "objects": self.objects,
        }


# ----------------------------
# FirstWatch client
# ----------------------------
class FirstWatchClient:
    def __init__(self, cfg: FWConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.token: Optional[str] = None

    def login(self) -> str:
        resp = self.session.post(
            self.cfg.login_url,
            data={"username": self.cfg.username, "password": self.cfg.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=self.cfg.timeout,
        )
        if not (200 <= resp.status_code < 300):
            raise RuntimeError(f"Login failed (HTTP {resp.status_code}): {resp.text}")

        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"Login returned non-JSON (HTTP {resp.status_code}): {resp.text}")

        token = data.get("token")
        if not token:
            raise RuntimeError(f"Login response missing token: {data}")

        self.token = token
        return token

    def _auth_headers(self) -> Dict[str, str]:
        if not self.token:
            self.login()
        return {"Authorization": f"Bearer {self.token}"}

    def _retry_sleep(self, attempt: int) -> None:
        sleep_s = min(10.0, 0.75 * (2 ** (attempt - 1)))
        time.sleep(sleep_s)

    def get_quota(self) -> Tuple[int, Any, str]:
        url = self.cfg.quota_url
        resp = self.session.get(url, headers=self._auth_headers(), timeout=self.cfg.timeout)

        if resp.status_code == 401:
            self.login()
            resp = self.session.get(url, headers=self._auth_headers(), timeout=self.cfg.timeout)

        if not (200 <= resp.status_code < 300):
            return resp.status_code, resp.text, resp.text.strip()

        try:
            return resp.status_code, resp.json(), ""
        except json.JSONDecodeError:
            return resp.status_code, resp.text, ""

    def check_domain(self, domain: str) -> Tuple[int, Optional[Dict[str, Any]], str]:
        url = f"{self.cfg.feed_check_url}/{domain}"
        headers = self._auth_headers()

        for attempt in range(1, self.cfg.max_retries + 2):
            resp = self.session.get(url, headers=headers, timeout=self.cfg.timeout)

            if resp.status_code == 401:
                self.login()
                headers = self._auth_headers()
                resp = self.session.get(url, headers=headers, timeout=self.cfg.timeout)

            if resp.status_code in (429,) or (500 <= resp.status_code <= 599):
                if attempt <= self.cfg.max_retries:
                    self._retry_sleep(attempt)
                    continue

            if not (200 <= resp.status_code < 300):
                return resp.status_code, None, resp.text.strip()

            try:
                return resp.status_code, resp.json(), ""
            except json.JSONDecodeError:
                return resp.status_code, None, f"Non-JSON response: {resp.text.strip()}"

        return 0, None, "Unknown error"

    def fuzzy_search(self, query: str, page: int = 1, per_page: int = 10) -> Tuple[int, Optional[Dict[str, Any]], str]:
        url = f"{self.cfg.feed_search_url}/{query}"
        params = {"page": page, "per_page": per_page}
        headers = self._auth_headers()

        for attempt in range(1, self.cfg.max_retries + 2):
            resp = self.session.get(url, headers=headers, params=params, timeout=self.cfg.timeout)

            if resp.status_code == 401:
                self.login()
                headers = self._auth_headers()
                resp = self.session.get(url, headers=headers, params=params, timeout=self.cfg.timeout)

            if resp.status_code in (429,) or (500 <= resp.status_code <= 599):
                if attempt <= self.cfg.max_retries:
                    self._retry_sleep(attempt)
                    continue

            if not (200 <= resp.status_code < 300):
                return resp.status_code, None, resp.text.strip()

            try:
                return resp.status_code, resp.json(), ""
            except json.JSONDecodeError:
                return resp.status_code, None, f"Non-JSON response: {resp.text.strip()}"

        return 0, None, "Unknown error"


# ----------------------------
# Processing
# ----------------------------
def process_domains(
    domains: List[str],
    client: FirstWatchClient,
    cfg: FWConfig,
    out_fh,
    *,
    output_format: str,
    fuzzy: bool,
    per_page: int,
    max_pages: int,
    fallback_fuzzy: bool,
    stix_builder: Optional[StixBundleBuilder],
) -> Dict[str, int]:
    stats = {"inputs": len(domains), "records_written": 0, "hits": 0, "failed_inputs": 0}

    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{stats['inputs']}] Processing: {domain}")
        had_hit = False

        # -------- Exact lookup --------
        if not fuzzy:
            http_status, data, err = client.check_domain(domain)
            if data is not None and not err and 200 <= http_status < 300:
                had_hit = True
                stats["hits"] += 1

                if output_format in ("csv", "json"):
                    rec = build_record(
                        input_query=domain,
                        matched_domain=domain,
                        mode="exact",
                        status="success",
                        http_status=http_status,
                        error="",
                        payload=data,
                    )
                    write_record(out_fh, output_format, rec)
                    stats["records_written"] += 1

                if output_format == "stix" and stix_builder:
                    stix_builder.add_hit(domain=domain, source_payload=data, mode="exact")

                print("  ✓ exact match")
            else:
                print(f"  ✗ exact lookup failed (HTTP {http_status})")
                if not fallback_fuzzy:
                    if output_format in ("csv", "json"):
                        rec = build_record(
                            input_query=domain,
                            matched_domain="",
                            mode="exact",
                            status="failed",
                            http_status=http_status,
                            error=err or "Exact lookup failed",
                            payload=None,
                        )
                        write_record(out_fh, output_format, rec)
                        stats["records_written"] += 1

        # -------- Fuzzy lookup (primary or fallback) --------
        if fuzzy or (fallback_fuzzy and not had_hit):
            found_any = False
            last_http = 200
            last_err = ""

            for page in range(1, max_pages + 1):
                http_status, data, err = client.fuzzy_search(domain, page=page, per_page=per_page)
                last_http, last_err = http_status, err

                if err or data is None:
                    if output_format in ("csv", "json"):
                        rec = build_record(
                            input_query=domain,
                            matched_domain="",
                            mode="fuzzy",
                            status="failed",
                            http_status=http_status,
                            error=err or "Fuzzy search failed",
                            payload=None,
                        )
                        write_record(out_fh, output_format, rec)
                        stats["records_written"] += 1
                    break

                results = data.get("results", []) if isinstance(data, dict) else []
                if not results:
                    break

                for item in results:
                    matched = (item.get("domain_name", "") if isinstance(item, dict) else "") or ""
                    matched = matched.strip().lower()

                    found_any = True
                    had_hit = True
                    stats["hits"] += 1

                    if output_format in ("csv", "json"):
                        rec = build_record(
                            input_query=domain,
                            matched_domain=matched,
                            mode="fuzzy",
                            status="success",
                            http_status=http_status,
                            error="",
                            payload=item,
                        )
                        write_record(out_fh, output_format, rec)
                        stats["records_written"] += 1

                    if output_format == "stix" and stix_builder:
                        # Prefer the matched domain value for the STIX object
                        stix_domain = matched if matched else domain
                        stix_builder.add_hit(domain=stix_domain, source_payload=item, mode="fuzzy")

                total_pages = 1
                if isinstance(data, dict):
                    try:
                        total_pages = int(data.get("total_pages", 1))
                    except Exception:
                        total_pages = 1
                if page >= total_pages:
                    break

            if not found_any and output_format in ("csv", "json"):
                rec = build_record(
                    input_query=domain,
                    matched_domain="",
                    mode="fuzzy",
                    status="failed",
                    http_status=last_http,
                    error=last_err or "No matches",
                    payload={"results": [], "page": 1, "per_page": per_page},
                )
                write_record(out_fh, output_format, rec)
                stats["records_written"] += 1

            if found_any:
                print("  ✓ fuzzy matches written")
            else:
                print("  ✗ no fuzzy matches")

        if not had_hit and output_format == "stix":
            # For STIX output we typically only emit hits; failures/no-matches are not indicators.
            pass

        if not had_hit:
            stats["failed_inputs"] += 1

        if i < stats["inputs"] and cfg.delay > 0:
            time.sleep(cfg.delay)

    return stats


# ----------------------------
# Config sample
# ----------------------------
def create_sample_config() -> None:
    sample = f"""# FirstWatch API Configuration File
# Copy to firstwatch.conf and update [credentials].

[credentials]
username = your_username_here
password = your_password_here

[api]
base_url = {DEFAULT_BASE_URL}
delay = {DEFAULT_DELAY_SECONDS}
timeout = {DEFAULT_TIMEOUT_SECONDS}
max_retries = {DEFAULT_MAX_RETRIES}
check_quota_before_run = true
stop_if_quota_insufficient = false

[output]
# Default output format if --output-format is not provided
# Options: csv, json  (json is JSONL), stix (STIX 2.1 bundle JSON)
output_format = csv

[stix]
# TLP marking for STIX bundle objects: clear|green|amber|red
tlp = clear

# Classification for indicators:
# - If it matches a known STIX indicator_types value (e.g., malicious-activity), it will be used as indicator_types.
# - Otherwise it will be stored as a label and indicator_types will default to ["unknown"].
classification = malicious-activity

# Producer identity name used in created_by_ref
identity_name = FirstWatch

# Optional extra labels (comma-separated)
labels = firstwatch
"""
    with open("firstwatch.conf.sample", "w", encoding="utf-8") as f:
        f.write(sample)

    print("Created sample configuration: firstwatch.conf.sample")
    print("Copy to firstwatch.conf and update [credentials].")


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="FirstWatch batch domain tool (new chaos.yatic.io environment)"
    )
    parser.add_argument("csv_file", nargs="?", help="CSV file containing domain names (single column)")
    parser.add_argument("output_file", nargs="?", help="Output file path (.csv, .jsonl, or .json for STIX bundle)")
    parser.add_argument("-c", "--config", default="firstwatch.conf", help="Config file path (default: firstwatch.conf)")
    parser.add_argument("--create-config", action="store_true", help="Create a sample configuration file")

    # Search behavior
    parser.add_argument("--fuzzy", action="store_true", help="Use fuzzy search instead of exact domain lookup")
    parser.add_argument("--fallback-fuzzy", action="store_true", help="If exact lookup fails, run fuzzy search as fallback")
    parser.add_argument("--per-page", type=int, default=10, help="Fuzzy search results per page (default: 10)")
    parser.add_argument("--max-pages", type=int, default=1, help="Max pages per fuzzy search input (default: 1)")

    # Output format override
    parser.add_argument(
        "--output-format",
        choices=["csv", "json", "stix"],
        default=None,
        help="Output format override: csv | json (JSONL) | stix (bundle). If omitted, uses config [output].output_format",
    )

    args = parser.parse_args()

    if args.create_config:
        create_sample_config()
        return

    if not args.csv_file or not args.output_file:
        parser.error("csv_file and output_file are required (unless using --create-config)")

    cfg = load_config(args.config)
    output_format = (args.output_format or cfg.output_format).lower()

    print(f"Using base URL: {cfg.base_url}")
    if output_format == "json":
        print("Output format: json (JSONL)")
    else:
        print(f"Output format: {output_format}")

    domains = load_domains_from_csv(args.csv_file)
    print(f"Loaded {len(domains)} unique domains from {args.csv_file}")
    if not domains:
        raise SystemExit("No domains found. Check your input file.")

    client = FirstWatchClient(cfg)

    # Optional quota check (will login)
    if cfg.check_quota_before_run:
        print("Checking quota...")
        try:
            qs, qdata, qerr = client.get_quota()
            if qerr:
                print(f"WARNING: quota check failed (HTTP {qs}): {qdata}")
            else:
                remaining = int(qdata.get("remaining", -1))
                monthly_quota = int(qdata.get("monthly_quota", -1))
                print(f"Quota remaining: {remaining} / {monthly_quota}")
                if cfg.stop_if_quota_insufficient and remaining >= 0 and remaining < len(domains):
                    raise SystemExit(
                        f"Insufficient quota: remaining={remaining}, inputs={len(domains)}. "
                        "Set stop_if_quota_insufficient=false to override."
                    )
        except Exception as e:
            print(f"WARNING: quota check error: {e}")

    # Ensure login before doing work
    print(f"Authenticating as: {cfg.username!r}")
    client.login()
    print("Authenticated.")

    stix_builder: Optional[StixBundleBuilder] = None
    if output_format == "stix":
        stix_builder = StixBundleBuilder(
            identity_name=cfg.stix_identity_name,
            tlp=cfg.stix_tlp,
            classification=cfg.stix_classification,
            labels=cfg.stix_labels or [],
        )
        print(f"STIX: TLP={cfg.stix_tlp}, classification={cfg.stix_classification}")

    # Stream outputs for csv/json; build bundle in memory for stix
    if output_format in ("csv", "json"):
        with open(args.output_file, "w", newline="", encoding="utf-8") as out_fh:
            if output_format == "csv":
                write_results_header_csv(out_fh)

            stats = process_domains(
                domains,
                client,
                cfg,
                out_fh,
                output_format=output_format,
                fuzzy=args.fuzzy,
                per_page=max(1, args.per_page),
                max_pages=max(1, args.max_pages),
                fallback_fuzzy=args.fallback_fuzzy,
                stix_builder=None,
            )
    else:
        # STIX bundle written at end
        stats = process_domains(
            domains,
            client,
            cfg,
            out_fh=None,
            output_format="stix",
            fuzzy=args.fuzzy,
            per_page=max(1, args.per_page),
            max_pages=max(1, args.max_pages),
            fallback_fuzzy=args.fallback_fuzzy,
            stix_builder=stix_builder,
        )

        bundle = stix_builder.bundle() if stix_builder else {"type": "bundle", "id": f"bundle--{uuid.uuid4()}", "objects": []}
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)
        stats["records_written"] = len(bundle.get("objects", []))

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print(f"Inputs:          {stats['inputs']}")
    print(f"Hits:            {stats['hits']}")
    print(f"Failed inputs:   {stats['failed_inputs']}")
    print(f"Records written: {stats['records_written']}")
    print(f"Output:          {args.output_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

