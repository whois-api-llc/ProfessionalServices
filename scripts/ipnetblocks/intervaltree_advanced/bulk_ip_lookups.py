import pickle
import os
import logging
import time
import ipaddress
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ip_in_netblock(ip_str, netblock_tree):
    """Check if an IP address falls within a netblock in the interval tree."""
    try:
        ip_int = int(ipaddress.ip_address(ip_str))
    except ValueError:
        logging.warning(f"Invalid IP address: {ip_str}")
        return '0', 'NA', 'NA'
    intervals = netblock_tree[ip_int]
    if intervals:
        # Return the smallest interval (tightest netblock match)
        min_interval = min(intervals, key=lambda x: x.end - x.begin)
        return min_interval.data  # (asn, asnName, country)
    return '0', 'NA', 'NA'

def load_ip_list(csv_file_path):
    """Read IP addresses from a single-column CSV file."""
    ip_list = []
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row:  # Skip empty rows
                    ip_list.append(row[0].strip())  # Take first column
    except FileNotFoundError:
        logging.error(f"Error: IP list file '{csv_file_path}' not found.")
        return None
    except Exception as e:
        logging.error(f"Error reading IP list: {e}")
        return None
    return ip_list

def main():
    pickle_file_path = "test.pkl"
    ip_csv_file_path = input("Enter the path to the IP list CSV file: ").strip()

    # Check if the pickle file exists
    if not os.path.exists(pickle_file_path):
        logging.error(f"Error: Interval tree file '{pickle_file_path}' not found. Please build the tree first.")
        return

    # Load the interval tree from the pickle file
    print(f"Loading Netblock Index from {pickle_file_path}...")
    try:
        with open(pickle_file_path, 'rb') as file:
            start_time = time.time()
            netblock_tree = pickle.load(file)
            end_time = time.time()
        file_size = os.path.getsize(pickle_file_path) / (1024 * 1024)  # Size in MB
        print(f"IP Netblock index loaded in {end_time - start_time:.2f} seconds.")
        print(f"File size: {file_size:.2f} MB")
    except Exception as e:
        logging.error(f"Failed to load index file: {e}")
        return

    # Load the IP list from the CSV file
    ip_list = load_ip_list(ip_csv_file_path)
    if not ip_list:
        return

    # Process each IP and print results
    print(f"\nProcessing {len(ip_list)} IP addresses from '{ip_csv_file_path}'...")
    print("-" * 60)
    start_csv_time = time.time()
    for ip in ip_list:
        #start_query = time.time()
        asn, asn_name, country = ip_in_netblock(ip, netblock_tree)
        #end_query = time.time()
        #print(f"IP: {ip}")
        #print(f"ASN: {asn}")
        #print(f"AS Name: {asn_name}")
        #print(f"Country: {country}")
        #print(f"Query time: {(end_query - start_query) * 1000:.2f} ms")
        #print("-" * 60)
    end_csv_time = time.time()
    print(f"Processed {len(ip_list)} IPs. Done!")
    print(f"Total CSV processing time {end_csv_time - start_csv_time:.2f} seconds.")

if __name__ == "__main__":
    main()
