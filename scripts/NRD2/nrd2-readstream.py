#!/usr/bin/env python3

import os
import json
import sys
import signal
from websocket import create_connection

# Read API key from environment variable
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    print("ERROR: API_KEY environment variable not set.")
    sys.exit(1)

# WebSocket connection
ws_url = "wss://nrd-stream.whoisxmlapi.com/ultimate"
print(f"Connecting to {ws_url}...")
ws = create_connection(ws_url)

print("Sending API Key...")
ws.send(API_KEY)
print("API Key Sent")

print("Receiving WHOIS data (press Ctrl+C to terminate)...")

# Initialize counters
txCounter = 0
recCounter = 0
unknownVerb = 0
domainAdded = 0
domainUpdated = 0
domainDiscovered = 0
domainDropped = 0

# Graceful shutdown
def signal_handler(sig, frame):
    print("\nClosing WebSocket connection...")
    ws.close()
    print("WebSocket closed.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Read and process data continuously
while True:
    try:
        txCounter += 1
        result = ws.recv()
        rLength = len(result)
        print(f"{rLength} characters received in transaction '{txCounter}'")

        recTxCounter = 0

        for json_line in result.splitlines():
            recCounter += 1
            recTxCounter += 1
            try:
                record = json.loads(json_line)
                domainReason = record.get("reason", "unknown")
                domainName = record.get("domainName", "N/A")
                IANAID = record.get("registrarIANAID", "N/A")
                domainRegistrar = record.get("registrarName", "N/A")

                if domainReason == "added":
                    domainAdded += 1
                elif domainReason == "discovered":
                    domainDiscovered += 1
                elif domainReason == "updated":
                    domainUpdated += 1
                elif domainReason == "dropped":
                    domainDropped += 1
                else:
                    unknownVerb += 1

                print(f"\n[Record#:{recCounter}] reason:{domainReason:<12} "
                      f"registrarIANAID:{IANAID:<5} domainName:{domainName}  "
                      f"(registrarName:{domainRegistrar})\n")

            except json.JSONDecodeError as e:
                print(f"ERROR: Record no. {recCounter} FAILED TO DECODE.")
                print(f"ERROR: {str(e)}")

        print(f"\n+++ End of transaction {txCounter}, added: {domainAdded}, "
              f"discovered: {domainDiscovered}, updated: {domainUpdated}, "
              f"dropped: {domainDropped}")
        print(f"{recTxCounter} records received in transaction {txCounter}, "
              f"{recCounter} in total.")

    except Exception as e:
        print(f"Unexpected error: {e}")
        break

# Close the WebSocket
ws.close()
print("WebSocket closed.")
