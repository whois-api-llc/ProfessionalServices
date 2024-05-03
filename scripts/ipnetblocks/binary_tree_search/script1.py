import csv
import intervaltree
import pickle
import os
import time

# Prompt the user to input the file names
file_path = input("Please enter the name of the netblock file: ")
pickle_file_path = input("Please enter the name of the .pkl file: ")

start_time = time.time()

print(f"Reading from {file_path} and building tree to {pickle_file_path}")

netblock_tree = intervaltree.IntervalTree()

with open(file_path, 'r', newline='', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        inetnumFirst = int(row['inetnumFirst'])
        inetnumLast = int(row['inetnumLast'])

        # Store data in the interval tree
        netblock_tree[inetnumFirst:inetnumLast + 1] = (row['asn'], row['country'], row['as_name'], row['netname'])

end_time = time.time()
print(f"Interval tree construction took {end_time - start_time:.2f} seconds.")

# Serialize the interval tree and save it
with open(pickle_file_path, 'wb') as file:
    pickle.dump(netblock_tree, file, protocol=pickle.HIGHEST_PROTOCOL)
print(f"Interval tree serialized to file {pickle_file_path}")

file_size = os.path.getsize(pickle_file_path)
print(f"Serialized file size: {file_size} bytes")


