# Example python script to download the disposable data feed daily from WHOISXMLAPI.com
# Professional.Services@whoisxmlapi.com

import os
import requests
from datetime import datetime, timedelta

email_logfile = "efeeds_download.log"
yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
rundate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

odir = "./"
datadir = "./"

auth = os.getenv('APIKEY')

email_endpoint = "https://download.whoisxmlapi.com/datafeeds/Disposable_Email_Domains/"
disposable_file = f"disposable-emails.full.{yesterday}.txt"
url = f"{email_endpoint}{disposable_file}"

with open(email_logfile, "a") as log_file:
    log_file.write(f"[ {rundate} ] Begin download for {yesterday}: {url}\n")

try:
    response = requests.get(url, auth=(auth, auth), stream=True)
    response.raise_for_status()  # Check if the request was successful

    with open(disposable_file, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # Filter out keep-alive new chunks
                file.write(chunk)

    with open(email_logfile, "a") as log_file:
        log_file.write(f"Download successful: {url}\n")

except requests.exceptions.RequestException as e:
    with open(email_logfile, "a") as log_file:
        log_file.write(f"File not found or download failed: {url}\n")
        log_file.write(f"Error: {e}\n")

