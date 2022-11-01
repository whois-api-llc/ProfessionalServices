#!/usr/bin/env python3
# Professional.Services@whoisxmlapi.com

import sys
import os
from time import sleep
from copy import deepcopy
from urllib.request import Request, urlopen
import json
import pandas as pd

#Infile is a csv having a "domainName" field
INFILE = sys.argv[1]
#(Output files will be INFILE_chunk_%d.csv,
#    %d being the ordinal number of the chunk)

#The wait time before checking again the API status
API_WAIT_SECONDS = 30

#API key from environment
API_KEY = os.getenv('APIKEY')

#size of chunks and thus the max no of records in the output csvs
CHUNKSIZE = 1000


csvMode = 'w'
csvHeader = True
url = 'https://www.whoisxmlapi.com/BulkWhoisLookup/bulkServices/'
chunkno = 0
for df in pd.read_csv(INFILE,
                      iterator=True,
                      chunksize=CHUNKSIZE,
                      low_memory=False,
                      keep_default_na=False):
    chunk = deepcopy(df)
    chunkno += 1
    domains = list(chunk['domainName'])
    n_domains = len(domains)
    payload_data = {'domains': domains, 'apiKey': API_KEY, 'outputFormat': 'JSON'}
    request = Request(url + 'bulkWhois')
    response = json.loads(urlopen(
        request, json.dumps(payload_data).encode()).read())
    print(response)
    
    request_id = response['requestId']
    print("Bulk WHOIS request id: ", request_id)
    payload_data.update({'requestId':request_id,
                         'searchType':'all',
                         'maxRecords':1,
                         'startIndex':1})
    del payload_data['domains']
    n_remaining = n_domains
    request = Request(url + 'getRecords')
    while n_remaining > 0:
        print("Waiting %d seconds"%API_WAIT_SECONDS)
        sys.stdout.flush()
        sleep(API_WAIT_SECONDS)
        raw_response = urlopen(request, json.dumps(payload_data).encode()).read()
        response = json.loads(raw_response.decode('utf-8', 'ignore'))
        n_remaining = response['recordsLeft']
        print("%d of %d domains to be processed"%(n_remaining, n_domains))
        sys.stdout.flush()
    print("Done, downloading data in csv")
    download_request = Request(url + 'download')
    download_payload = {'apiKey': API_KEY, 'requestId': request_id, 'searchType': 'all'}
    download_response = urlopen(download_request,
                                json.dumps(download_payload).encode()).read()
    with open(INFILE + '_chunk_%d.csv'%chunkno, 'wt') as outfile:
        outfile.write(download_response.decode('utf8', 'ignore'))
        outfile.close()
