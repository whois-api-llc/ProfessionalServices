# Reverse NS API with auto-pagination
#
# Replease with your own API Key
#
# Usage: python reverse-ns.py ns1.example.com
#

from reversens import *
import sys

cnt = 0
client = Client('YOUR_API_KEY')

ns_server = sys.argv[1]

client.name_server = ns_server

f = open("output.txt", "w")

for page in client:
    for row in page.result:
        cnt += 1
        print(f"{cnt}, d = {row.name}")
        f.write(f"{row.name}\n")

print(f"Total pages: {client.last_result.size}, count: {cnt}")
print("Done")
