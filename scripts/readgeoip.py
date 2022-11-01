# WHOISXMLAPI.COM - Code provided as-is with no warrenty or support
# 2022-10-23 v1.0 Professional.Services@whoisxmlapi.com
# script to read IPv4 Geolocation data file provided by WHOISXMLAPI.COM
#
import sys
import ipaddress

try:
    import pandas as pd
except:
    print("This script requires pandas be installed.")
    print("   https://pandas.pydata.org/docs/getting_started/install.html")
    sys.exit(1)

if len(sys.argv) < 3:
    print("\nPlease specify <inputfile> <outputfile>\n")
    sys.exit(1) 

IPGEOInputFile = sys.argv[1]
IPGEOOutputFile = sys.argv[2]

currRow = 0
ipMarkEnd = []
ipAddrStart = []
ipAddrEnd = []

df = pd.read_csv(IPGEOInputFile)

# print info about the pandas data frame - optional
# df.info()

totalRows = df.shape[0] 

print("-> Total Rows:", totalRows)

while (currRow < totalRows):
        
    ipStartMark = df['mark'].iloc[currRow]
    ipAddrStartStr = str(ipaddress.ip_address(int(ipStartMark)))
    ipAddrStart.append(ipAddrStartStr)

    # check to see if its the last row
    if currRow+1 == totalRows:
        ipAddrEndStr = str(ipaddress.ip_address(int(ipStartMark))) 
        ipNextMark = ipStartMark
    else:
        ipNextMark = df['mark'].iloc[currRow+1] - 1
        ipAddrEndStr = str(ipaddress.ip_address(int(ipNextMark)))

    ipMarkEnd.append(str(ipNextMark))
    ipAddrEnd.append(ipAddrEndStr)

    currRow += 1

    print("Current:", ipStartMark, "Next:", ipNextMark, " Beg:", ipAddrStartStr, "End:", ipAddrEndStr)

# Adjust to your requirements
print("-> Dropping 5 Columns, adjust as needed to meet your requirements.")
df.drop(columns=['isp','connectionType','postalCode','timezone','geonameId'], inplace=True)

print("-> Inserting columns: nextMark, ipv4start, ipv4end")
df.insert(1,"nextMark", ipMarkEnd)
df.insert(2,"ipv4start", ipAddrStart)
df.insert(3,"ipv4end", ipAddrEnd)

print("-> Write file", IPGEOOutputFile)
df.to_csv(IPGEOOutputFile, index=False)
print("-> Done")

"""
Example:

THe WHOISXMLApi IPv4 Geolocation data-file sample (header + 4 rows):

cat geoip4addresses.csv
mark,isp,connectionType,country,region,city,lat,lng,postalCode,timezone,geonameId
16777216,APNIC Research and Development,,AU,State of Queensland,West End,-27.47923,153.0096,,+10:00,6943564
16777217,APNIC Research and Development,,US,California,Los Angeles,34.05223,-118.24368,90001,-07:00,5368361
16777218,APNIC Research and Development,,AU,State of Queensland,West End,-27.47923,153.0096,,+10:00,6943564
16777472,CHINANET-FJ,,CN,Fujian Sheng,Qingzhou,26.53153,117.97718,,+08:00,1797604

$ python3 ipgeomark.py geoip4addresses.csv out.csv
-> Total Rows: 4
Current: 16777216 Next: 16777216  Beg: 1.0.0.0 End: 1.0.0.0
Current: 16777217 Next: 16777217  Beg: 1.0.0.1 End: 1.0.0.1
Current: 16777218 Next: 16777471  Beg: 1.0.0.2 End: 1.0.0.255
Current: 16777472 Next: 16777472  Beg: 1.0.1.0 End: 1.0.1.0
-> Dropping 6 Columns, adjust as needed to meet your requirements.
-> Inserting columns: nextMark, ipv4start, ipv4end
-> Write file out.csv
-> Done

Display the contents of out.csv:
$ cat out.csv
mark,nextMark,ipv4start,ipv4end,country,region,city,lat,lng
16777216,16777216,1.0.0.0,1.0.0.0,AU,State of Queensland,West End,-27.47923,153.0096
16777217,16777217,1.0.0.1,1.0.0.1,US,California,Los Angeles,34.05223,-118.24368
16777218,16777471,1.0.0.2,1.0.0.255,AU,State of Queensland,West End,-27.47923,153.0096
16777472,16777472,1.0.1.0,1.0.1.0,CN,Fujian Sheng,Qingzhou,26.53153,117.97718

We now have a beginning and end mark, start and end IPv4 address, country, region, state, longitude and latitude.

"""
