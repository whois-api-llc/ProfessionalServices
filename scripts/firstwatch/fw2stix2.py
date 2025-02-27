# whoisxmlapi.com - Firstwatch domainName list to TAXII/StIX 2.1 format.
# Version 1.0   2025-02-27
#
# Features:
#   Reads domain names from a text or CSV file.
#   Converts them into STIX 2.1 Indicator objects with domain-name observable type.
#   Generates a TAXII 2.1 compatible STIX bundle.
#   Outputs the JSON file in TAXII format.
#
# Notes:
#   The default behavior generates a compact JSON file (not ideal for human readable format)
#      Example: python convert_to_taxii.py firstwatch-list.csv output.json
#   The --pretty flag pretty-prints the output for readability.
#      Example: Example: python convert_to_taxii.py firstwatch-list.csv output.json --pretty
#

import json
import uuid
import datetime
import argparse
from stix2 import Bundle, Indicator

def generate_stix_bundle(domain_list):
    # generate a STIX 2.1 bundle with Indicator objects for domain names
    indicators = []
    
    for domain in domain_list:
        indicator = Indicator(
            id=f"indicator--{uuid.uuid4()}",
            created=datetime.datetime.utcnow().isoformat() + "Z",
            modified=datetime.datetime.utcnow().isoformat() + "Z",
            name=f"Suspicious Domain: {domain}",
            description="Domain name identified as potentially malicious.",
            pattern=f"[domain-name:value = '{domain}']",
            pattern_type="stix",
            valid_from=datetime.datetime.utcnow().isoformat() + "Z"
        )
        indicators.append(indicator)

    bundle = Bundle(objects=indicators)
    return bundle

def read_domains_from_file(file_path):
    with open(file_path, "r") as f:
        domains = [line.strip() for line in f if line.strip()]
    return domains

def main():
    parser = argparse.ArgumentParser(description="Convert a list of domains to TAXII-compatible STIX format.")
    parser.add_argument("input_file", help="Path to the file containing domain names.")
    parser.add_argument("output_file", help="Path to save the generated STIX JSON file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")

    args = parser.parse_args()

    domains = read_domains_from_file(args.input_file)
    if not domains:
        print("No valid domains found in the input file.")
        return

    stix_bundle = generate_stix_bundle(domains)

    serialized_json = stix_bundle.serialize()
    if args.pretty:
        serialized_json = json.dumps(json.loads(serialized_json), indent=4)

    with open(args.output_file, "w") as f:
        f.write(serialized_json)
    
    print(f"STIX bundle saved to {args.output_file} {'(pretty-printed)' if args.pretty else '(compact JSON)'}")

if __name__ == "__main__":
    main()

