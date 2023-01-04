# WHOISXMLAPI.COM - Code provided as-is with no warrenty or support
# 2022-10-23 v1.0 Professional.Services@whoisxmlapi.com
# script to read IPv4 or IPv6 Geolocation data file provided by WHOISXMLAPI.COM
#
import sys
import ipaddress
import timeit

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
df = pd.read_csv(IPGEOInputFile)

# print info about the pandas data frame - optional
#df.info()

currRow = 0
ipMarkEnd = []
ipAddrStart = []
ipAddrEnd = []

df = pd.read_csv(IPGEOInputFile)

totalRows = df.shape[0]

if IPGEOVersion == '4':
    while (currRow < totalRows):

        ipStartMark = df['mark'].loc[currRow]
        ipAddrStartStr = str(ipaddress.IPv4Address(int(ipStartMark)))
        ipAddrStart.append(ipAddrStartStr)

        # check to see if its the last row
        if currRow+1 == totalRows:
            ipAddrEndStr = str(ipaddress.IPv4Address(int(ipStartMark)))
            ipNextMark = ipStartMark
        else:
            ipNextMark = df['mark'].loc[currRow+1] - 1
            ipAddrEndStr = str(ipaddress.IPv4Address(int(ipNextMark)))

        ipMarkEnd.append(str(ipNextMark))
        ipAddrEnd.append(ipAddrEndStr)

        currRow += 1

        print("Current:", ipStartMark, "Next:", ipNextMark, " Beg:", ipAddrStartStr, "End:", ipAddrEndStr)

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


        print("Current:", ipStartMark, "Next:", ipNextMark, " Beg:", ipAddrStartStr, "End:", ipAddrEndStr)


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

print("-> Write file", IPGEOOutputFile)
df.to_csv(IPGEOOutputFile, index=False)

# end elapsed time counter and print results
stopwatch = timeit.default_timer()
print(f"-> Done, Elapsed time: {stopwatch-startwatch:0.2f} seconds\n")



"""
    --------
    IPv4 Example:
    The WHOISXMLApi IPv4 Geolocation data-file sample (header + 4 rows):

    cat geoip4addresses.csv
    mark,isp,connectionType,country,region,city,lat,lng,postalCode,timezone,geonameId
    16777216,APNIC Research and Development,,AU,State of Queensland,West End,-27.47923,153.0096,,+10:00,6943564
    16777217,APNIC Research and Development,,US,California,Los Angeles,34.05223,-118.24368,90001,-07:00,5368361
    16777218,APNIC Research and Development,,AU,State of Queensland,West End,-27.47923,153.0096,,+10:00,6943564
    16777472,CHINANET-FJ,,CN,Fujian Sheng,Qingzhou,26.53153,117.97718,,+08:00,1797604

    --------
    Run the Script:

    $ python3 ipgeomark.py 4 geoip4addresses.csv out.csv
    Current: 16777216 Next: 16777216  Beg: 1.0.0.0 End: 1.0.0.0
    Current: 16777217 Next: 16777217  Beg: 1.0.0.1 End: 1.0.0.1
    Current: 16777218 Next: 16777471  Beg: 1.0.0.2 End: 1.0.0.255
    Current: 16777472 Next: 16777472  Beg: 1.0.1.0 End: 1.0.1.0

    -> Total Rows: 4
    -> Dropping 5 Columns, adjust as needed to meet your requirements.
    -> Inserting columns: nextMark, ipstart, ipend
    -> Write file output.csv
    -> Done, Elapsed time: 0.82 seconds

    --------
    Display the contents of out.csv:

    $ cat out.csv

    mark,nextMark,ipv4start,ipv4end,country,region,city,lat,lng
    16777216,16777216,1.0.0.0,1.0.0.0,AU,State of Queensland,West End,-27.47923,153.0096
    16777217,16777217,1.0.0.1,1.0.0.1,US,California,Los Angeles,34.05223,-118.24368
    16777218,16777471,1.0.0.2,1.0.0.255,AU,State of Queensland,West End,-27.47923,153.0096
    16777472,16777472,1.0.1.0,1.0.1.0,CN,Fujian Sheng,Qingzhou,26.53153,117.97718

    --------
    We now have a beginning and end mark, start and end IPv4 address, country, region, state, longitude and latitude.

    --------
    IPv6 Example:
    The WHOISXMLApi IPv6 Geolocation data-file sample (header + 4 rows):

    mark,isp,connectionType,country,region,city,lat,lng,postalCode,timezone,geonameId
    50543257672098557030943619659950409595,,,CA,Québec,Montréal,45.50884,-73.58781,,-05:00,6077243
    50511069989384618769877345080126224433,,,US,California,Los Angeles,34.05223,-118.24368,90001,-08:00,5368361
    50676843408750377142345674138325090320,Apple Inc.,,US,New York,New York City,40.71427,-74.00597,10001,-05:00,5128581
    50511294500807422530226244593321867478,"Amazon.com, Inc.",,US,Virginia,Ashburn,39.04372,-77.48749,20146,-05:00,4744870

    --------
    Run the script:

    $ python3 ipgeomark.py 6 geoip6addresses.csv out.csv
    Current: 50676843408750377142345674138325090320 Next: 50511294500807422530226244593321867477  Beg: 2620:149:af0::10 End: 2600:1f18:f88:4313:6df7:f986:f915:78d5
    Current: 50511294500807422530226244593321867478 Next: 50543257672098557030943619659950409594  Beg: 2600:1f18:f88:4313:6df7:f986:f915:78d6 End: 2606:4700:20::ac43:477a
    Current: 50543257672098557030943619659950409595 Next: 50511069989384618769877345080126224432  Beg: 2606:4700:20::ac43:477b End: 2600:1406:5400:5a5::3830
    Current: 50511069989384618769877345080126224433 Next: 50511069989384618769877345080126224433  Beg: 2600:1406:5400:5a5::3831 End: 2600:1406:5400:5a5::3831

    -> Total Rows: 4
    -> Dropping 5 Columns, adjust as needed to meet your requirements.
    -> Inserting columns: nextMark, ipstart, ipend
    -> Write file output.csv
    -> Done, Elapsed time: 1.06 seconds

    --------
    Display the contents of out.csv:

    $ cat out.csv
    50543257672098557030943619659950409595,50543257672098557030943619659950409595,2606:4700:20::ac43:477b,2606:4700:20::ac43:477b,CA,Québec,Montréal,45.50884,-73.58781
    50511069989384618769877345080126224433,50511069989384618769877345080126224433,2600:1406:5400:5a5::3831,2600:1406:5400:5a5::3831,US,California,Los Angeles,34.05223,-118.24368
    50676843408750377142345674138325090320,50676843408750377142345674138325090320,2620:149:af0::10,2620:149:af0::10,US,New York,New York City,40.71427,-74.00597
    50511294500807422530226244593321867478,50511294500807422530226244593321867478,2600:1f18:f88:4313:6df7:f986:f915:78d6,2600:1f18:f88:4313:6df7:f986:f915:78d6,US,Virginia,Ashburn,39.04372,-77.48749

    --------
    We now have a beginning and end mark, start and end IPv6 address, country, region, state, longitude and latitude.
    """
