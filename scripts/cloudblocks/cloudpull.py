# cloudPull.py
#
import csv, sys
import struct, socket, io
import requests, getopt, json
# import Beautiful Soup for Azure
from   bs4 import BeautifulSoup

# only checking for IPv4 in this version

outputFileName = sys.argv[1]
totalCIDRRecords = 0

def processAzure():

    cloudKey = "azure"

    records = 0

    # Azure is processed differently, which MS provides a link to automatically trigger a JS download

    url = "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519"

    resp = requests.get(url)

    # now parse HTML to get the real link

    soup = BeautifulSoup(resp.content, "html.parser")
    link = soup.find('a', {'data-bi-containername':'download retry'})['href']

    file_download = requests.get(link)

    jsonResponse = json.loads(file_download.content.decode())

    for d in jsonResponse["values"]:
        ipList = d["properties"]["addressPrefixes"]

        for ipAddrPreFix in ipList:
            prefix = ipAddrPreFix
            if prefix.find(":") == -1:
                service = d["properties"]["systemService"]
                country = d["properties"]["region"]
                other = ""
                writeCSV(cloudKey,prefix,country, service, other)
                records += 1
        
    print("\t[AZURE] Added", str(records), "prefixes")

def processCloudFlare():

    cloudKey = "cloudflare"

    records = 0


    url = "https://cloudflare.com/ips-v4"

    resp = requests.get(url)

    if resp.status_code != 200:
        print("Loading CloudFlare IP range failed.")
        sys.exit(1)

    blob = resp.content.decode()
    ips = blob.split("\n")

    for x in ips:

       prefix = x

       if prefix.find(":") == -1:
           service = ""
           country = ""
           other = ""

           writeCSV(cloudKey,prefix,country,service,other)
           records += 1

    print("\t[CLOUDFLARE] Added", str(records), "prefixes")

def processOracle():

    cloudKey = "oracle"

    records = 0

    url = "https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json"

    resp = requests.get(url)

    if resp.status_code != 200:
        print("Loading Oracle IP prefixes failed.")
        sys.exit(1)

    jsonResponse = json.loads(resp.content.decode())

    for d in jsonResponse["regions"]:
        region = d["region"]
        IPAddrCidr = d["cidrs"]

        for ipBlock in IPAddrCidr:
            prefix = ipBlock["cidr"]
            if prefix.find(":") == -1: # only do IPv4 for now / quick check
                service = ""
                country = ""
                other = ""
                writeCSV(cloudKey,prefix,country, service, other)
                records += 1

    print("\t[ORACLE] Added", str(records), "prefixes")

def processDigitalOcean():

    cloudKey = "digitalocean"

    records = 0

    url = "https://digitalocean.com/geo/google.csv"

    r = requests.get(url)

    buff = io.StringIO(r.text)

    dr = csv.DictReader(buff, fieldnames=['ipaddr','country','state','city','AS'])
    
    for row in dr:
        prefix = row["ipaddr"]
        if prefix.find(":") == -1: # only do IPv4 for now / quick check
            country = row["country"]
            other = row["AS"]
            service = ""
            writeCSV(cloudKey,prefix,country, service, other)
            records += 1

    print("\t[DigitalOcean] Added", str(records), "prefixes")

def processAWS():

    cloudKey = "aws"
    records = 0

    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"

    resp = requests.get(url)

    if resp.status_code != 200:
        print("Loading AWS IP range failed.")
        sys.exit(1)

    jsonResponse = json.loads(resp.content.decode())

    # ip_prefix = IPv4
    # ipv6_prefix = IPv6

    for d in jsonResponse["prefixes"]:
        prefix = d["ip_prefix"]
        service = d["service"]
        other = d["region"]
        country = other
        writeCSV(cloudKey,prefix,country, service, other)
        records += 1

    print("\t[AWS] Added", str(records), "prefixes") 

def findStartEnd(ipAddrCIDR):
    (ipAddr, cidr) = ipAddrCIDR.split("/")
    cidrBlock = int(cidr)
    ip = ipAddr
    host_bits = 32 - cidrBlock
    i = struct.unpack('>I', socket.inet_aton(ip))[0]
    start = (i >> host_bits) << host_bits
    end = start | ((1 << host_bits) - 1)
    return(start, end)

def writeCSV(cloudKey,prefix,country, service, other):

    global totalCIDRRecords

    (start, end) = findStartEnd(prefix)

    strWrite = \
            cloudKey + "," \
            + prefix + "," \
            + str(start) + "," \
            + str(end) + "," \
            + service + "," \
            + other \
            + "\n"

    outFile.write(strWrite)
    outFile.flush()

    totalCIDRRecords += 1

# BEGIN 

outFile = open(outputFileName, "w")
# header row
headerRow = "cloud,ip_prefix,ip_start,ip_end,country,service,other\n"
outFile.write(headerRow)
outFile.flush()

print("\ncloudPull - v1.0   Ed Gibbs   ed.gibbs@whoisxmlapi.com")
print("Generating Output file: " + outputFileName)
print("Connecting to Cloud Services... ")

processAWS()
processAzure()
processCloudFlare()
processDigitalOcean()
processOracle()

print("Total records written =", str(totalCIDRRecords), "\n")

outFile.close()
