# WHOISXMLAPI.COM - Code provided as-is with no warranty or support
# 2022-10-23 v1.0 Professional.Services@whoisxmlapi.com
# script to read IPv4 or IPv6 Geolocation data file provided by WHOISXMLAPI.COM
#    + includes adding CIDR column
#

import sys
import ipaddress
import timeit
from netaddr import spanning_cidr

# start elapsed time counter
startwatch = timeit.default_timer()

# check if pandas library is present, if not provide the link to download
try:
    import pandas as pd
except:
    print("This script requires pandas be installed.")
    print("   https://pandas.pydata.org/docs/getting_started/install.html")
    sys.exit(1)

# check for all required arguments, print the below statement if not present
if len(sys.argv) < 4:
    print("\nPlease specify <ip_version> <inputfile> <outputfile>\n")
    sys.exit(1)

# define input arguments
IPGEOVersion = sys.argv[1]
IPGEOInputFile = sys.argv[2]
IPGEOOutputFile = sys.argv[3]

# define input file as 'df'
df = pd.read_csv(IPGEOInputFile, dtype='unicode', low_memory=False)

# print info about the pandas data frame - optional
#df.info()

currRow = 0
ipMarkEnd = []
ipAddrStart = []
ipAddrEnd = []
ipCIDR = []

df = pd.read_csv(IPGEOInputFile)

totalRows = df.shape[0]

if IPGEOVersion == '4':
    while (currRow < totalRows):

        ipStartMark = df['mark'].loc[currRow]
        ipAddrStartStr = str(ipaddress.IPv4Address(int(ipStartMark)))
        ipAddrStart.append(ipAddrStartStr)

        # check to see if it's the last row
        if currRow+1 == totalRows:
            ipAddrEndStr = str(ipaddress.IPv4Address(int(ipStartMark)))
            ipNextMark = ipStartMark
        else:
            ipNextMark = df['mark'].loc[currRow+1] - 1
            ipAddrEndStr = str(ipaddress.IPv4Address(int(ipNextMark)))

        ipMarkEnd.append(str(ipNextMark))
        ipAddrEnd.append(ipAddrEndStr)

        currRow += 1

        cidrBlock = spanning_cidr([ipAddrStartStr, ipAddrEndStr])

        ipCIDR.append(cidrBlock)

        print("CurrentRec:", ipStartMark, "Next:", ipNextMark, "CIDR", cidrBlock, "Beg:", ipAddrStartStr, "End:", ipAddrEndStr)

elif IPGEOVersion == '6':
    while (currRow < totalRows):
        df["mark"] = df["mark"].apply(int)
        ipStartMark = df['mark'].loc[currRow]
        ipAddrStartStr = str(ipaddress.IPv6Address(int(ipStartMark)))
        ipAddrStart.append(ipAddrStartStr)

        # check to see if its the last row
        if currRow+1 == totalRows:
            ipAddrEndStr = str(ipaddress.IPv6Address(int(ipStartMark)))
            ipNextMark = ipStartMark
        else:
            ipNextMark = df['mark'].loc[currRow+1] - 1
            ipAddrEndStr = str(ipaddress.IPv6Address(int(ipNextMark)))

        ipMarkEnd.append(str(ipNextMark))
        ipAddrEnd.append(ipAddrEndStr)

        currRow += 1

        cidrBlock = spanning_cidr([ipAddrStartStr, ipAddrEndStr])

        ipCIDR.append(cidrBlock)

        # Uncomment to print
        #print("CurrentRec:", ipStartMark, "Next:", ipNextMark, "CIDR", cidrBlock, "Beg:", ipAddrStartStr, "End:", ipAddrEndStr)

        if currRow == 10:
            break
else:
    print("\n IP Version Invalid, input '4' OR '6' before <inputfile> <outputfile>\n")
    sys.exit(1)

print("\n-> Total Rows:", totalRows)
# Adjust to your requirements
print("-> Dropping 5 Columns, adjust as needed to meet your requirements.")
df.drop(columns=['isp','connectionType','postalCode','timezone','geonameId'], inplace=True)

print("-> Inserting columns: nextMark, ipstart, ipend")
df.insert(1,"nextMark", ipMarkEnd)
df.insert(2,"ipstart", ipAddrStart)
df.insert(3,"ipend", ipAddrEnd)
df.insert(4,"cidr", ipCIDR)

print("-> Write file", IPGEOOutputFile)
df.to_csv(IPGEOOutputFile, index=False)

# end elapsed time counter and print results
stopwatch = timeit.default_timer()
print(f"-> Done, Elapsed time: {stopwatch-startwatch:0.2f} seconds\n")
