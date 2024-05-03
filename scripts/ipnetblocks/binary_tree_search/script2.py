import pickle
import os
import logging
import time
import ipaddress

def ip_in_netblock(ip_str, netblock_tree):
    try:
        ip_int = int(ipaddress.ip_address(ip_str))
    except ValueError:
        return '0', 'NA', 'NA', 'NA'
    intervals = netblock_tree[ip_int]
    if intervals:
        min_interval = min(intervals, key=lambda x: x.end - x.begin)
        return min_interval.data
    else:
        return '0', 'NA', 'NA', 'NA'

def main():
    # Prompt the user to input the file names
    pickle_file_path = input("Please enter the name of the .pkl file: ")
    client_ip = input("Please enter the IP address to search for: ")

    # Check if the pickle file exists
    if not os.path.exists(pickle_file_path):
        logging.error("Error: Interval tree file not found. Please build the tree first.")
        return

    # Load the interval tree from the pickle file
    print(f"Loading Interval tree from {pickle_file_path}...")
    with open(pickle_file_path, 'rb') as file:
        start_time = time.time()
        netblock_tree = pickle.load(file)
        end_time = time.time()
    print(f"Interval tree has been loaded from the file in {end_time - start_time:.2f} seconds.")

    # Check if the IP address is in the netblock
    print(f"Checking for IP address: {client_ip}")
    asn, country, as_name, netname = ip_in_netblock(client_ip, netblock_tree)

    # Print out the details directly
    print(f"ASN: {asn}")
    print(f"Country: {country}")
    print(f"AS Name: {as_name}")
    print(f"Netname: {netname}")

if __name__ == "__main__":
    main()
