#!/usr/bin/env python3

import json
import sys
import signal
from websocket import create_connection
from datetime import datetime

API_KEY = "<YOUR_API_KEY>"  
BUFFER_SIZE = 100

if len(sys.argv) != 2:
    print("ERROR: Please specify an output file as command line argument.")
    print("Usage: python3 script.py output_file.txt")
    sys.exit(1)

OUTPUT_FILE = sys.argv[1]

try:
    output_file = open(OUTPUT_FILE, 'w')
    output_file.write("Timestamp,DomainName\n")
except IOError as e:
    print(f"ERROR: Could not open output file {OUTPUT_FILE}: {e}")
    sys.exit(1)

ws_url = "wss://nrd-stream.whoisxmlapi.com/ultimate"
print(f"Connecting to {ws_url}...")
ws = create_connection(ws_url)
ws.send(API_KEY)
print("API Key Sent")
print("Receiving WHOIS data (press Ctrl+C to terminate)...")

txCounter = 0
recCounter = 0
unknownVerb = 0
domainAdded = 0
domainUpdated = 0
domainDiscovered = 0
domainDropped = 0
write_buffer = []

def signal_handler(sig, frame):
    if write_buffer:
        output_file.writelines(write_buffer)
    print("\nClosing WebSocket connection...")
    ws.close()
    print("WebSocket closed.")
    output_file.close()
    print(f"Output file {OUTPUT_FILE} closed.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

while True:
    try:
        txCounter += 1
        result = ws.recv()
        rLength = len(result)
        print(f"{rLength} characters received in transaction '{txCounter}'")

        recTxCounter = 0
        for json_line in result.splitlines():
            json_line = json_line.strip()
            if not json_line:
                continue
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
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    write_buffer.append(f"{timestamp},{domainName}\n")
                    if len(write_buffer) >= BUFFER_SIZE:
                        output_file.writelines(write_buffer)
                        output_file.flush()
                        write_buffer.clear()
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
                print(f"ERROR: Record no. {recCounter} FAILED TO DECODE: {e}")

        if write_buffer:
            output_file.writelines(write_buffer)
            output_file.flush()
            write_buffer.clear()

        print(f"\n+++ End of transaction {txCounter}, added: {domainAdded}, "
              f"discovered: {domainDiscovered}, updated: {domainUpdated}, "
              f"dropped: {domainDropped}")
        print(f"{recTxCounter} records received in transaction {txCounter}, "
              f"{recCounter} in total.")

    except ConnectionError:
        print("Connection error occurred.")
        break
    except TimeoutError:
        print("Receive timeout.")
        continue

ws.close()
if write_buffer:
    output_file.writelines(write_buffer)
output_file.close()
print("WebSocket and output file closed.")
