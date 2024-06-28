# build_geoIPv4_interval_tree.py 
# Developed by MQ
# Example, and starting point to building an interval tree from IP geolocation datafeeds from WHOISXMLAPI
#   - Ideas: 
#     * Break up the IPv4 file into seperate .pkl files and multi-task the creation
#     * Run as a service, and create a signal to the service that a new .pkl file is ready to reload
#  requires intervaltree and pickle dependencies 

import csv
import intervaltree
import pickle
import os
import time

def build_interval_tree_ipv4(file_path):
    tree = intervaltree.IntervalTree()
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        for i in range(len(reader) - 1):
            start_ip = int(reader[i]['mark'])
            next_start_ip = int(reader[i + 1]['mark'])
            if next_start_ip < 2**32:
                end_ip = next_start_ip
            elif next_start_ip == 0:
                end_ip = 2**32
            else:
                print(f"Error: Detected IPv6 address at line {i + 2}. This input only supports IPv4 addresses.")
                return None
            tree[start_ip:end_ip] = reader[i]
        if reader and int(reader[-1]['mark']) < 2**32:
            start_ip = int(reader[-1]['mark'])
            end_ip = 2**32
            tree[start_ip:end_ip] = reader[-1]
    return tree

file_path = input("Please enter the name of the geoip CSV file: ")
pickle_file_path_ipv4 = input("Please enter the name of the .pkl file to save the IPv4 interval tree: ")

start_time = time.time()

print(f"Reading from {file_path} and building IPv4 tree to {pickle_file_path_ipv4}")

ipv4_tree = build_interval_tree_ipv4(file_path)

if ipv4_tree is not None:
    end_time_ipv4 = time.time()
    print(f"IPv4 interval tree construction took {end_time_ipv4 - start_time:.2f} seconds.")

    with open(pickle_file_path_ipv4, 'wb') as file:
        pickle.dump(ipv4_tree, file, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"IPv4 interval tree serialized to file {pickle_file_path_ipv4}")

    file_size_ipv4 = os.path.getsize(pickle_file_path_ipv4)
    print(f"Serialized IPv4 file size: {file_size_ipv4} bytes")
else:
    print("Failed to build the IPv4 interval tree due to the presence of IPv6 addresses in the input.")
