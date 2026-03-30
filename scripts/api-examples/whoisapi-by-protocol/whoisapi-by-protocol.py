#!/usr/bin/env python3
"""
whoisapi-by-protocol.py  Version 1.2  30 March 2026

Provided by WHOISXMLAPI.COM as is. 

RDAP Monitor: rdap.wxapros.com

------------------------
Checks whether a domain's TLD supports RDAP, WHOIS, Both, or None,
based on a reference CSV file.

Usage:

    # Single domain lookup (plain output):
    python check_domain_protocol.py tld_results.csv google.com

    # Batch mode — input is a CSV file of domain names (one per row):
    python check_domain_protocol.py tld_results.csv domains.csv

The reference CSV must contain at minimum these columns:
    tld, rdap_supported, whois_available

The input domains CSV must be a single-column file (with or without a header).
Output for batch mode is written to stdout in CSV format:
    domain,tld,protocol

This can be used to determine if the input value for rdap should be (0|1|2) where,
	
   0 results in retrieving data via Auto protocol.

   1 results in retrieving data via RDAP protocol.

   2 results in retrieving data via WHOIS protocol.

   Acceptable values: 0 | 1 | 2
   
   Example: python whoisapi-by-protocol.py tld_results_20260330_194558.csv amazon.com

    $ python whoisapi-by-protocol.py tld_results_20260330_194558.csv domains.csv
      domain,tld,protocol
      amazon.com,com,Both
      amazon.ai,ai,Both
      amazon.io,io,WHOIS
      amazon.pt,pt,NO_DATA
      amazon.vn,vn,NO_DATA
      amazon.zip,zip,RDAP
      amazon.xyz,xyz,Both
      amazon.eu,eu,WHOIS
      amazon.co,co,NO_DATA
      amazon.ca,ca,Both
      amazon.cn,cn,WHOIS

"""

import sys
import csv
import argparse
import pandas as pd
import tldextract

# Use tldextract's bundled Public Suffix List snapshot so the script works
# offline and doesn't emit network-timeout warnings.  Pass
# suffix_list_urls=() to skip all remote fetches; tldextract will fall back
# to its built-in snapshot (updated with each release).  If you want the
# latest PSL you can remove the `_EXTRACTOR` override below.
_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


def load_tld_map(reference_path: str) -> dict[str, str]:
    """Load the TLD reference CSV and return a dict mapping tld -> protocol."""
    df = pd.read_csv(reference_path)

    required = {"tld", "rdap_supported", "whois_available"}
    missing = required - set(df.columns.str.lower())
    if missing:
        sys.exit(f"ERROR: Reference CSV is missing required columns: {missing}")

    # Normalise column names to lowercase just in case
    df.columns = df.columns.str.lower()

    tld_map: dict[str, str] = {}
    for _, row in df.iterrows():
        tld = str(row["tld"]).strip().lower().lstrip(".")
        rdap = str(row["rdap_supported"]).strip().lower() == "yes"
        whois = str(row["whois_available"]).strip().lower() == "yes"

        if rdap and whois:
            protocol = "Both"
        elif rdap:
            protocol = "RDAP"
        elif whois:
            protocol = "WHOIS"
        else:
            protocol = "NO_DATA"

        tld_map[tld] = protocol

    return tld_map


def extract_tld(domain: str) -> str:
    """Extract the effective TLD from a domain name using tldextract."""
    extracted = _EXTRACTOR(domain.strip())
    # suffix contains the public suffix / TLD (e.g. "com", "co.uk")
    return extracted.suffix.lower()


def lookup(domain: str, tld_map: dict[str, str]) -> tuple[str, str]:
    """Return (tld, protocol) for a given domain."""
    tld = extract_tld(domain)
    if not tld:
        return ("", "Unknown")
    protocol = tld_map.get(tld, "None")
    return (tld, protocol)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check RDAP/WHOIS protocol support for a domain or list of domains."
    )
    parser.add_argument(
        "reference_csv",
        help="Path to the TLD reference CSV (tld_results_*.csv).",
    )
    parser.add_argument(
        "input",
        help=(
            "A single domain name (e.g. google.com) "
            "OR a .csv file containing one domain per row."
        ),
    )
    args = parser.parse_args()

    tld_map = load_tld_map(args.reference_csv)

    is_csv_input = args.input.lower().endswith(".csv")

    if is_csv_input:

        # ----------------------------------------------------------------
        # Batch mode: read domains from CSV, write CSV to stdout
        # ----------------------------------------------------------------

        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["domain", "tld", "protocol"])

        with open(args.input, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            for row_num, row in enumerate(reader, start=1):
                if not row:
                    continue

                domain = row[0].strip()

                # Skip blank lines and obvious header rows
                if not domain or domain.lower() in ("domain", "domains", "hostname"):
                    continue

                tld, protocol = lookup(domain, tld_map)
                writer.writerow([domain, tld, protocol])

    else:

        # ----------------------------------------------------------------
        # Single-domain mode: pretty print to stdout
        # ----------------------------------------------------------------

        domain = args.input.strip()
        tld, protocol = lookup(domain, tld_map)

        print(f"Domain    : {domain}")
        print(f"TLD       : {tld if tld else '(could not determine)'}")
        print(f"Protocol  : {protocol}")

        if protocol == 'Both':
            print("Preference: RDAP, rdap=1")
        elif protocol == 'WHOIS':
            print("Preference: WHOIS, rdap=2")

if __name__ == "__main__":
    main()
