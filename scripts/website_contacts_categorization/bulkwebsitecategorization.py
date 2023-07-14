# WHOISXMLAPI.COM (C)2023     Professional.Services@whoisxmlapi.com
# This script is provided as is with no guarentee or support.
# This script ingest a jason file containing 'id' and 'url' and produces
# a json and csv file of the webcategories.

import http.client
import json
import sys
# pip install pandas
import pandas as pd

if __name__ == '__main__':

    inputFilename = sys.argv[1]

    apiKey = "YOURAPIKEY"
    wItems = 0

    f = open(inputFilename)

    data = json.load(f)

    fOut = open("output.json", "w")
    fOut.write("[\n")

    url = "/api/v3?apiKey=" \
          + apiKey + \
          "&url="

    payload = ''
    headers = {}

    lastItem = len(data)

    for x in data:
        try:
            conn = http.client.HTTPSConnection("website-categorization.whoisxmlapi.com")
        except Exception as E:
            print("Unable to connect to API endpoint.  Aborting")
            print(E)
            sys.exit(1)
        print("Processing ID:", x['id'], "URL: ", x['url'])
        uri = url + x['url']

        conn.request("GET", uri, payload, headers)
        res = conn.getresponse()
        dataRes = res.read()
        fOut.write(dataRes.decode('utf8'))
        wItems += 1

        if wItems == lastItem:
            fOut.write("\n")
        else:
            fOut.write(",\n")

    fOut.write("]\n")
    fOut.close()

    df = pd.read_json('output.json')
    df.to_csv('output.csv', index = None)
    f.close()
