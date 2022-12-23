# Professional.Services@whoisxmlapi.com
#   Reverse-Proxy example to retrieve data from WHOISXMLAPI.COM
#   Make sure you have the WXAAPIKEY environment variable set

from flask import Flask, request, redirect
import requests
import os, sys

app = Flask(__name__)

@app.route('/')
def reverse_proxy():
    return("Hello.\nThis is a reverse proxy\n")

# In this example, we will use request.args.net to parse the contents of the query string
@app.route("/ipgeo", methods=['GET'])
def proxy_ipgeo():

    ipAddress = request.args.get('ipAddr')

    target = "https://ip-geolocation.whoisxmlapi.com/api/v1?apiKey=" \
            + apiKey \
            + "&ipAddress=" \
            + ipAddress

    response = requests.get(target)
    return response.text

@app.route("/whois", methods=['GET'])
def proxy_whois():

    domainName = request.args.get('domainName')

    target = "https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey=" \
            + apiKey \
            + "&domainName=" \
            + domainName

    response = requests.get(target)
    return response.text

if __name__ == '__main__':
    apiKey = os.getenv("WXAAPIKEY")
    app.run()
