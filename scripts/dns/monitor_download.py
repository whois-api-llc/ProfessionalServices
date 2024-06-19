import os
import time
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

url = 'URL of DNS file or contact your WHOIS account manager for more details'

apiKey = "<<<YOUR__API__KEY>>>"

download_directory = './test'
username = apiKey
password = apiKey

if not os.path.exists(download_directory):
    os.makedirs(download_directory)

def get_file_list(url, auth):
    response = requests.get(url, auth=auth)
    soup = BeautifulSoup(response.text, 'html.parser')
    files = [a['href'] for a in soup.find_all('a') if a['href'] not in ('../', './')]
    return files

def download_file(url, filename, auth):
    response = requests.get(url + filename, auth=auth)
    with open(os.path.join(download_directory, filename), 'wb') as f:
        f.write(response.content)

downloaded_files = set()

auth = HTTPBasicAuth(username, password)

while True:
    print("Load list of current files....")
    current_files = set(get_file_list(url, auth))
    print("build list of new files...")
    new_files = current_files - downloaded_files
    
    for new_file in new_files:
        print(f"New file detected: {new_file}... downloading")
        # Uncomment the below line to download files
        # download_file(url, new_file, auth)
        print(f"Add new file to list")
        downloaded_files.add(new_file)
    
    print("Sleep 300 seconds")
    time.sleep(300)
