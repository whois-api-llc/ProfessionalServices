import csv
import intervaltree
import pickle
import time
from os.path import getsize

# File path to BGP Enriched full IP Netblock csv file
file_path = "ip_netblocks.2025-04-08.full.blocks.csv"
# output file
pickle_file_path = "test.pkl"

# Chunk size (adjust based on your system's memory)
CHUNK_SIZE = 50000  # Number of rows per chunk

# Initialize variables
line = 0
netblock_tree = intervaltree.IntervalTree()
start_time = time.time()

print(f"Reading from {file_path} and building tree to {pickle_file_path}")

try:
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        chunk = []
        
        for row in csv_reader:
            line += 1
            chunk.append(row)
            
            # Process chunk when it reaches CHUNK_SIZE
            if len(chunk) >= CHUNK_SIZE:
                for chunk_row in chunk:
                    try:
                        inetnumFirst = int(chunk_row[1])
                        inetnumLast = int(chunk_row[2])
                        asn = chunk_row[3]
                        asnName = chunk_row[7]
                        country = chunk_row[9]
                        
                        # Add to interval tree
                        netblock_tree[inetnumFirst:inetnumLast + 1] = (asn, asnName, country)
                        
                    except (IndexError, ValueError) as e:
                        print(f"Error in row {line}: {e}")
                        continue
                
                # Clear chunk to free memory
                chunk = []
        
        # Process remaining rows (if any)
        for chunk_row in chunk:
            try:
                inetnumFirst = int(chunk_row[1])
                inetnumLast = int(chunk_row[2])
                asn = chunk_row[3]
                asnName = chunk_row[7]
                country = chunk_row[9]
                
                netblock_tree[inetnumFirst:inetnumLast + 1] = (asn, asnName, country)
            except (IndexError, ValueError) as e:
                print(f"Error in row {line}: {e}")
                continue

except FileNotFoundError:
    print(f"Error: File {file_path} not found.")
    exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    exit(1)

# Timing and serialization
end_time = time.time()
print(f"Interval tree construction took {end_time - start_time:.2f} seconds.")

with open(pickle_file_path, 'wb') as file:
    pickle.dump(netblock_tree, file, protocol=pickle.HIGHEST_PROTOCOL)
print(f"Interval tree serialized to file {pickle_file_path}")

file_size = getsize(pickle_file_path)
print(f"Serialized file size: {file_size} bytes")
print(f"Total rows processed: {line}")
print("done")
