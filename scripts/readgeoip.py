# WHOISXMLAPI.COM - Code provided as-is with no warrenty or support
# 2022-10-23 v1.0 ed@whoisxmlapi.com
# script to read IPv4 Geolocation data file provided by WHOISXMLAPI.COM
#
import sys
import ipaddress
import getopt

try:
    import pandas as pd
except:
    print("This script requires pandas be installed.")
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
