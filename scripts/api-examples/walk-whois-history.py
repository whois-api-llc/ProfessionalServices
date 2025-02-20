# Walk-History.py written by Professional.Services@whoisxmlapi.com
# This script is provided from demostration purpposes and uses live API credits. Use at own risk.
# Start with low values to understand the impact.
#
# This script queries historical WHOIS records and reverse WHOIS data from the WhoisXML API to identify email addresses associated with domain registrations and map out domains linked to those email addresses.
#
# Key Functionalities:
#   Retrieve Historical WHOIS Data:
#
# Uses the WhoisXML API to fetch historical WHOIS records for a given domain.
# Extracts registrant email addresses and tracks unique, duplicate, and missing email records.
# Perform Reverse WHOIS Lookup:
#
# Searches for all domains associated with a given email address using the WhoisXML API.
# Supports preview mode (fetching a count of domains) and purchase mode (retrieving full domain lists).
# Generate Reports:
#    Saves discovered email addresses in a CSV file.
#    Writes a summary report listing domains, associated emails, and the number of discovered emails.
#
# Accepts arguments such as:
#   --domainName: Target domain for historical lookup.
#   --depth: Determines whether to run in preview (1) or purchase mode (2).
#   --limit: Restricts the number of domains fetched.
#   --history: Specifies how many WHOIS history records to retrieve.
#
# API Usage Tracking:
#
# Tracks API calls made in both preview and purchase modes.
# Displays API credit usage based on requests.
#
# Example Use Case:
# A researcher wants to analyze all past registrant email addresses linked to example.com.
# The script retrieves these emails and performs reverse WHOIS lookups to identify additional domains registered by those emails.
# The output is stored in a CSV file for further analysis.

from urllib.request import urlopen
import requests
import json
import os, sys
import timeit

apiKey = os.getenv('WXAAPI')

emailArray = []
duplicateEmail = 0
uniqueEmail = 0
noEmailRec = 0
genCount = 0
drsAPIPreview = 0
drsAPIPurchase = 0

def genReport(fileName, domainList, emailAddr, limit):

    newlyDiscovered = 0

    x = 0

    global genCount

    try:
        fOut = open(fileName, "a")
    except:
        print("Unable to open", fileName)
        return -1

    if genCount == 0:
        hfld = "domainName,emailAddr,emailsDiscovered"+ "\n"
        fOut.write(hfld)

    for dn in domainList:

        newlyDiscovered += getHistory(dn)

        dnstr = dn + "," + emailAddr + "," + str(newlyDiscovered) + "\n"

        fOut.write(dnstr)
        x += 1
        if limit != 0 and x == limit:
            break

    fOut.close()

    genCount += 1

def reverseWHOIS(emailAddr, mode, fileName, limit):
    domainCount = 0
    global apiKey 
    global drsAPIPurchase
    global drsAPIPreview

    url = 'https://reverse-whois.whoisxmlapi.com/api/v2'

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    data = {'apiKey': apiKey, 
            'searchType': 'current', 
            'mode': mode,
            'punycode': True,
            'advancedSearchTerms': 
                [ {
                    'field': 'RegistrantContact.Email',
                    'term': emailAddr,
                    'exactMatch': True
                  } 
                ] 
            }

    data = json.dumps(data)

    x = requests.post(url, data=data, headers=headers)

    ret_val = x.status_code

    if ret_val == 200:
        domainCount = int(x.json()['domainsCount'])

        if mode == "purchase":
            genReport(fileName, x.json()['domainsList'], emailAddr, limit)
            drsAPIPurchase += 1
        else:
            drsAPIPreview += 1

    return domainCount

def getHistory(domainName, hdepth): 

    recsAdded = 0
    idx = 0
    global duplicateEmail
    global uniqueEmail
    global noEmailRec 
    global drsAPIPurchase

    print("\nDomainname:", domainName)
    
    url = 'https://whois-history.whoisxmlapi.com/api/v1?' \
        + 'domainName=' + domainName + '&apiKey=' + apiKey + "&mode=purchase" \
        + "&outputFormat=JSON"

    r = json.loads(urlopen(url).read().decode('utf8'))

    record_cnt =  int(r['recordsCount'])

    print("\tTotal Historical WHOIS Records:", record_cnt)
    
    drsAPIPurchase += 1

    for x in range(record_cnt):
        try:
            emailAddr =  r['records'][x]['registrantContact']['email']
        except:
            emailAddr = ""

        if emailAddr != None and len(emailAddr) >= 4:
            if emailAddr.lower() in emailArray:
                duplicateEmail += 1
            else:
                emailAddr = emailAddr.lower()
                emailArray.append(emailAddr)
                recsAdded += 1
                uniqueEmail += 1
                print("\t\tNewly discovered email address:", emailAddr)
        else:
            noEmailRec += 1

#        if x ==  hdepth:
#            break;

        idx += 1

    return recsAdded

if __name__ == '__main__':

    from argparse import ArgumentParser

    startTime = timeit.default_timer()

    PRODUCT="WHOISXMLAPI.COM"
    MYNAME="Walk-History"
    VERSION="0.1a"

    parser=ArgumentParser(
        description = PRODUCT,
        prog=MYNAME)

    parser.add_argument('-v', '--version',
        help='Print version information and exit.',
        action='version',
        version=MYNAME + ' ver. ' + VERSION + '\n(c) WhoisXML API, Inc.')

    parser.add_argument('-n', '--domainName', type=str,
        help="Specify the domainName to start",
        required=True)

    parser.add_argument('-d', '--depth', choices=[1, 2], default=1, type=int,
        help="Discovery horizontal depth (1 or 2). Default is 1",
        required=False)

    parser.add_argument('-l', '--limit', default=5, type=int,
        help="Domain Discovery - 0=unlimited to 10K, or specify limit 1 to 9999. Default is 5",
        required=False)

    parser.add_argument('-e', '--emailfile', default="emails.csv", type=str,
        help="Filename of the file to produce that contains the emails that were discovered.",
        required=False)

    parser.add_argument('-o', '--output', default="output.txt", type=str,
        help='Filename of the report file to generate',
        required=False)

    parser.add_argument('-t', '--history', type=int, default=5, 
        help="Historical Depth. Default=1. 0=unlimited",
        required=False)

    ARGS = parser.parse_args()

    print(f"\nDomainname: {ARGS.domainName}")
    if ARGS.depth == 1:
        print("\tRun in preview mode.")
    else:
        print("\tRun in purchase mode.")
    print(f"Limit: {ARGS.limit}")
    print(f"Horizontal Depth: {ARGS.depth}")
    print(f"Historical Depth: {ARGS.history}")
    print(f"Email file: {ARGS.emailfile}")
    print(f"Output file: {ARGS.output}")

    getHistory(ARGS.domainName, ARGS.history)

    print("\nUnique Emails:", uniqueEmail, "\n")

    for e in emailArray:
        domainCount = reverseWHOIS(e, "preview", "", 0)
        print(f"\t-> {e} has {domainCount:,} additional domains registered")

        if domainCount > 1 and int(ARGS.depth) > 1:

            if ARGS.limit != 0:
                sstr = "but only " + str(int(ARGS.limit)) + " writen"
            else:
                sstr = ""

            print(f"\t\t{domainCount} expanded {sstr} to {ARGS.output}")

            domainCount = reverseWHOIS(e, "purchase", ARGS.output, int(ARGS.limit))
        elif domainCount == 0:
            print("\t\tNothing to expand.")

    print("\nDuplicate Emails:", duplicateEmail)
    print("No Email in Record:", noEmailRec)
    print("DRS API Previews:", drsAPIPreview)
    print("DRS API Purchase:", drsAPIPurchase * 50, "(1 API call = 50 credits)") 

    try:
        efOut = open(ARGS.emailfile, "w")

        efOut.write("emailAddress")
        efOut.write("\n")

        for eml in emailArray:
           emlstr = eml + "\n"
           efOut.write(emlstr)

    except:
        print("Unable to open", ARGS.emailfile)

    stopTime = timeit.default_timer()

    print(f"Elapsed time: {stopTime-startTime:0.2f} seconds.\n")
