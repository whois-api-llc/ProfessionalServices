import csv
import intervaltree
import pickle
import os
import time
import ipaddress

def convert_to_ipv6_if_needed(ip_value):
    if ip_value == 0:
        return int(ipaddress.IPv6Address('::'))
    return ip_value

def build_interval_tree_ipv6(file_path):
    tree = intervaltree.IntervalTree()
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        for i in range(len(reader) - 1):
            start_ip = convert_to_ipv6_if_needed(int(reader[i]['mark']))
            next_start_ip = convert_to_ipv6_if_needed(int(reader[i + 1]['mark']))
            end_ip = next_start_ip
            tree[start_ip:end_ip] = reader[i]
        if reader:
            start_ip = convert_to_ipv6_if_needed(int(reader[-1]['mark']))
            end_ip = start_ip + 1
            tree[start_ip:end_ip] = reader[-1]
    return tree

file_path = input("Please enter the name of the geoip CSV file: ")
pickle_file_path_ipv6 = input("Please enter the name of the .pkl file to save the IPv6 interval tree: ")

start_time = time.time()

print(f"Reading from {file_path} and building IPv6 tree to {pickle_file_path_ipv6}")

ipv6_tree = build_interval_tree_ipv6(file_path)

if ipv6_tree is not None:
    end_time_ipv6 = time.time()
    print(f"IPv6 interval tree construction took {end_time_ipv6 - start_time:.2f} seconds.")

    with open(pickle_file_path_ipv6, 'wb') as file:
        pickle.dump(ipv6_tree, file, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"IPv6 interval tree serialized to file {pickle_file_path_ipv6}")

    file_size_ipv6 = os.path.getsize(pickle_file_path_ipv6)
    print(f"Serialized IPv6 file size: {file_size_ipv6} bytes")
else:
    print("Failed to build the IPv6 interval tree.")
