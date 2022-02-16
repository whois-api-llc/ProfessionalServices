# Simple Websocket client to connect to wss: service and read response after sending apiKey
# Be sure to specify your API key
# Specifications can be found at: https://domain-registration-streaming.whoisxmlapi.com/specifications/data-streaming
# Sample provided by WHOISXMLAPI.COM 

from websocket import create_connection

ws = create_connection("wss://nrd-stream.whoisxmlapi.com/ultimate")

apiKey = "at_abcdefghijklmnopqrstuvwxyz"

print("Sending API Key...")

ws.send(apiKey)

print("Sent")

print("Receiving WHOIS data...")

# read response 

result =  ws.recv()

# Show record

print("Received '%s'" % result)

# Close Connection

ws.close()
