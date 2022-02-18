# Simple Websocket client to connect and continiously read wss: service after sending apiKey
# Be sure to specify your API key
# Requirements: pip3 install websocket-client
# Specifications can be found at: https://domain-registration-streaming.whoisxmlapi.com/specifications/data-streaming
# Sample provided by WHOISXMLAPI.COM, credit goes to https://pypi.org/project/websocket-client/ 
# Thanks MK for your help!

#!/usr/bin/env python3

import os
import json
from websocket import create_connection

recCounter = 0

ws = create_connection("wss://nrd-stream.whoisxmlapi.com/ultimate")

# define environment variable: API_KEY and read it in

apiKey = os.getenv('API_KEY')

print("Sending API Key...")
ws.send(apiKey)
print("API Key Sent")

print("Receiving WHOIS data (press ctrl/c to terminate)...")

txCounter = 0
recCounter = 0
while True:
    txCounter += 1
    result = ws.recv()
    # determine the length of the result
    rLength = len(result)
    print("%d characters received in transaction '%d'" %(rLength, txCounter))
    recTxCounter = 0
    # read in case of multi-line jsonl
    for json_line  in result.splitlines():
        recCounter += 1
        recTxCounter += 1
        try:
            record = json.loads(json_line)
            print("\n-----------------\nRecord no. %d:\n%s"%(recCounter, str(record)))
        except Exception as e:
            print("Record no. %d FAILDED TO DECODE."%(recCounter))
            print("The error was: %s"%str(e))
    print("\n++++++++++++End of transaction %d"%txCounter)
    print("%d records received in transaction %d, %d in total: '"%(
        recTxCounter, txCounter, recCounter))
#close the websocket
ws.close()
print("Websocket closed.")
