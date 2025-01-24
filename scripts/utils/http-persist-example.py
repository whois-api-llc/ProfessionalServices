# in this example, we will be using the WHOISXMLAPI.COM DNS API to send requests 
# using a persistent connection to minimize and optimize the full API requests.

import csv
import os
import sys
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def resolve_fqdn(input_file, output_file):
    # Get the API key from the environment variable
    api_key = os.getenv("WXAAPIKEY")
  
    if not api_key:
        print("Error: API key not found in environment variable 'WXAAPIKEY'.")
        sys.exit(1)

    # Configure HTTP session with persistence and retries
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.8, status_forcelist=[500, 502, 503, 504])
  
    session.mount("https://", HTTPAdapter(max_retries=retries))

    # Open the input file and read the FQDNs
    with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Write the header to the output CSV file
        writer.writerow(["FQDN", "IP Address"])

        for row in reader:
            fqdn = row[0].strip()
            if fqdn:
                # Format the API URL
                url = f"https://www.whoisxmlapi.com/whoisserver/DNSService?apiKey={api_key}&domainName={fqdn}&type=A&outputFormat=JSON"

                try:
                    # Make the API request using the session
                    response = session.get(url)
                    response.raise_for_status()

                    # Parse the response JSON
                    data = response.json()
                    dns_data = data.get("DNSData", {})
                    dns_records = dns_data.get("dnsRecords", [])

                    if dns_records:
                        # Extract the first IP address from the dnsRecords
                        ip_address = dns_records[0].get("address", "")
                        writer.writerow([fqdn, ip_address])
                        print(f"Resolved {fqdn} to {ip_address}")
                    else:
                        print(f"No A records found for {fqdn}")
                        writer.writerow([fqdn, "No A records found"])

                except requests.exceptions.RequestException as e:
                    print(f"Error resolving {fqdn}: {e}")
                    writer.writerow([fqdn, f"Error: {e}"])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python resolve_fqdn.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    resolve_fqdn(input_file, output_file)
