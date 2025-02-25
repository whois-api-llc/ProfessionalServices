# lookup_mx_recs.py
#  Uses Whoisxmlapi.com DNS API to obtain MX records for specified domains
#
# -i input_filename - single column list of domains to lookup MX records
# -o output_filename - columns = domainName, number_of_mx_records, and mx_records
#    separated by |
#

import asyncio
import aiohttp
import csv
import argparse
import json

API_KEY = "<Your_API_Key>"  # Replace with your actual API key
BASE_URL = "https://www.whoisxmlapi.com/whoisserver/DNSService"

async def fetch_mx_records(session, domain, semaphore):
    """
    Fetch MX records for a given domain using the WHOISXMLAPI DNS API.
    Parses the JSON response to extract MX records from the 'DNSData' -> 'dnsRecords' field.
    Returns a tuple: (domain, number of MX records, list of MX records).
    """
    url = f"{BASE_URL}?apiKey={API_KEY}&domainName={domain}&type=MX&outputFormat=JSON"
    async with semaphore:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Error: {domain} returned status code {response.status}")
                    return domain, 0, []
                data = await response.json()

                # Check for the expected JSON structure.
                dns_data = data.get("DNSData")
                if not dns_data:
                    print(f"Error: {domain} response does not contain 'DNSData'")
                    return domain, 0, []

                dns_records = dns_data.get("dnsRecords", [])
                mx_records = []
                for record in dns_records:
                    # Ensure we are processing only MX records.
                    if record.get("dnsType", "").upper() == "MX":
                        # Extract the MX record value; here we use the 'target' field.
                        mx_value = record.get("target")
                        if mx_value:
                            mx_records.append(mx_value)
                return domain, len(mx_records), mx_records
        except Exception as e:
            print(f"Exception for {domain}: {e}")
            return domain, 0, []

async def process_domains(input_file, output_file):
    # Limit the concurrency to 10 simultaneous API requests.
    semaphore = asyncio.Semaphore(10)
    tasks = []
    domains = []

    # Read domain names from the input CSV file (one domain per row).
    with open(input_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:  # ignore empty rows
                domains.append(row[0].strip())

    async with aiohttp.ClientSession() as session:
        for domain in domains:
            task = asyncio.create_task(fetch_mx_records(session, domain, semaphore))
            tasks.append(task)
        results = await asyncio.gather(*tasks)

    # Write the results to the output CSV file.
    with open(output_file, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["domainName", "number_of_MX", "MX_records"])
        for domain, count, mx_records in results:
            writer.writerow([domain, count, "|".join(mx_records)])

def parse_args():
    parser = argparse.ArgumentParser(
        description="Lookup MX records using the WHOISXMLAPI DNS API and output results to a CSV file."
    )
    parser.add_argument("-i", "--input", required=True, help="Input CSV file with domain names (one per line).")
    parser.add_argument("-o", "--output", required=True, help="Output CSV file to write the results.")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    asyncio.run(process_domains(args.input, args.output))
