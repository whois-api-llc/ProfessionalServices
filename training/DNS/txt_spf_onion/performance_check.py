import csv
import time
import sys

start = time.time()
count = 0
with open(sys.argv[1], 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        count += 1
        if count >= 100000:  # Test 100K records
            break

elapsed = time.time() - start
rate = 100000 / elapsed
print(f"Processing rate: {rate:,.0f} records/second")
print(f"Estimated time for 6.8M: {6800000/rate/60:.1f} minutes")
