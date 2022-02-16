# Simple Websocket client to connect and continiously read wss: service after sending apiKey
# Be sure to specify your API key
# Requirements: pip3 install websocket-client
# Specifications can be found at: https://domain-registration-streaming.whoisxmlapi.com/specifications/data-streaming
# Sample provided by WHOISXMLAPI.COM, credit goes to https://pypi.org/project/websocket-client/

from websocket import create_connection
import sys, signal
import time

ws = create_connection("wss://nrd-stream.whoisxmlapi.com/ultimate")

apiKey = "at_abcdefghijklmnopqrstuvwxyz"

print("Sending API Key...")
ws.send(apiKey)
print("API Key Sent")

print("Receiving WHOIS data (press ctrl/c to terminate)...")

time.sleep(3)

while True:
    try:
        result =  ws.recv()
        print("Record Received: '%s'" % result)
    except:
        print("Exiting.")
        break

ws.close()

print("Websocket closed.")
