# Pre-Release Preview
#
from urllib.request import urlopen
import requests
import json
import os, sys

#obtain the API key from an environmental variable.
# if you do not have an environmental variable defined, you can hard code it
# by using the statement apiKey = "at_alkdsjflakjdflkajdflkajdflkajdf"
#
apiKey = os.getenv('WXAAPI')

emailArray = []
duplicateEmail = 0
uniqueEmail = 0
noEmailRec = 0

def reverseWHOIS(emailAddr):
    domainCount = 0
    global apiKey

    url = 'https://reverse-whois.whoisxmlapi.com/api/v2'

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    data = {'apiKey': apiKey, 
            'searchType': 'current', 
            'mode': "preview",
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

    return domainCount

def getHistory(domainName): 
    idx = 0
    global duplicateEmail
    global uniqueEmail
    global noEmailRec 

    print("Domainname:", domainName)
    
    url = 'https://whois-history.whoisxmlapi.com/api/v1?' \
        + 'domainName=' + domainName + '&apiKey=' + apiKey + "&mode=purchase" \
        + "&outputFormat=JSON"

    r = json.loads(urlopen(url).read().decode('utf8'))

    record_cnt =  int(r['recordsCount'])

    print("\tTotal Historical WHOIS Records:", record_cnt)

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
                uniqueEmail += 1
        else:
            noEmailRec += 1

        idx += 1

if __name__ == '__main__':

    domainName = sys.argv[1]

    getHistory(domainName)
    print("Unique Emails     :", uniqueEmail)
    for e in emailArray:
        domainCount = reverseWHOIS(e)
        print(f"\t-> {e} has {domainCount:,} domains registered")
    print("Duplicate Emails  :", duplicateEmail)
    print("No Email in Record:", noEmailRec)
