import os
import datetime
import logging
import requests
from requests.auth import HTTPBasicAuth

# be sure to change your path to desired location 
savedir = "./"

# set your API key. Read API key from environment
auth = "YOUR_API_KEY"

ipnetblockURL = "https://ip-netblocks.whoisxmlapi.com/datafeeds/IP_Netblocks_WHOIS_Database/"

yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
rundate = datetime.datetime.now()

ip_file = f"ip_netblocks.{yesterday}.full.blocks.csv.gz"
ip_fullURL = f"{ipnetblockURL}{ip_file}"

file_path = os.path.join(savedir, ip_file)

print(f"Begin download for {yesterday}: {ip_fullURL}")

try:
    with requests.get(ip_fullURL, auth=HTTPBasicAuth(auth, auth), stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)

    print(f"Download successful: {file_path}")

except requests.exceptions.RequestException as e:
    print(f"File not found or download failed: {file_path} - Error: {e}")

