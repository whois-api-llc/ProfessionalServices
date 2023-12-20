# Simple Websocket client to connect and continiously read wss: service after sending apiKey
# Version 2 - added counters based on the verb, as well as additional output such as the registrar
# Be sure to specify your API key
# Requirements: pip3 install websocket-client
# Specifications can be found at: https://domain-registration-streaming.whoisxmlapi.com/specifications/data-streaming
# Sample provided by WHOISXMLAPI.COM, credit goes to https://pypi.org/project/websocket-client/ 
# Professional.Services@whoisxmlapi.com

#!/usr/bin/env python3

import os
import json
from websocket import create_connection

recCounter = 0

ws = create_connection("wss://nrd-stream.whoisxmlapi.com/ultimate")

# define environment variable: API_KEY and read it in

apiKey = os.getenv('APIKEY')

print("Sending API Key...")
ws.send(apiKey)
print("API Key Sent")

print("Receiving WHOIS data (press ctrl/c to terminate)...")

txCounter = 0
recCounter = 0
verbCount = 0
unknownVerb = 0
domainAdded = 0
domainUpdated =0
domainDeleted = 0
domainDiscovered = 0
domainDropped = 0

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
         domainReason = record['reason']
         domainName = record['domainName']
         IANAID = record['registrarIANAID']
         domainRegistrar = record['registrarName']

         if domainReason == "added":
            domainAdded += 1
            verbCount = domainAdded
         elif domainReason == "discovered":
            domainDiscovered += 1
            verbCount = domainDiscovered
         elif domainReason == "updated":
            domainUpdated += 1
            verbCount = domainAdded
         elif domainReason == "dropped":
            domainDropped += 1
            verbCount = domainDropped
         else:
            unknownVerb += 1
            verbCount = unknownVerb

         print("\n[rec#:%d] V:%-12s VC:%-9d IANAID:%-5d D:%s  (DR:%s)\n"%(recCounter, domainReason, verbCount, IANAID, domainName, domainRegistrar))
      except Exception as e:
         print("ERROR: Record no. %d FAILED TO DECODE."%(recCounter))
         print("ERROR: %s"%str(e))
   print("\n+++End of transaction %d, added: %d, discovered: %d, updated: %d, dropped: %d"%(txCounter, domainAdded, domainDiscovered, domainUpdated, domainDropped))
   print("%d records received in transaction %d, %d in total: "%(recTxCounter, txCounter, recCounter))
# close the websocket
ws.close()
print("Websocket closed.")
