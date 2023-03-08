# DomainAPIExpansion by WHOIS.py
# Developed by Professional.Services@whoisxmlapi.com  v1.0   14 Feb 2023
# This file is provided "as-is" with no warranty or support
# You will need to obtain a valid API key with sufficient credits from whoisxmlapi.com
#  WHOISXMLAPI GitHub Repository can be found at https://github.com/whois-api-llc/
# The purpose of this file is to demonstrate how to use various APIs
# Contact sales@whoisxmlapi.com for more information
# Min Req: Python 3.6+

import sys
# pip install subdomains-lookup
import subdomainslookup as sd
# pip install whois-api
import whoisapi as who
# pip install domain-reputation
import domainreputation as dr
# pip install dns-lookup-api
import dnslookupapi as dns
# pip install reverse-ip
import reverseip as rip
# pip install simple-geoip
import simple_geoip as geoip

# Visit www.whoisxmlapi.com, create a free account or sign-in to obtain your API key
apiKey="<YOURAPIKEY>"

def domainReputation(domainName):
    print("\tDomain Reputation")

    drClient = dr.Client(apiKey)

    drResponse = drClient.get(domainName, drClient.MODE_FULL)

    print("\t\tReputation Score:" + str(drResponse.reputation_score))

    for x in drResponse.test_results:
        print("\t\t\t\tTest:" + str(x.test))
        print("\t\t\t\tTest Code:" + str(x.test_code))
        print("\t\t\t\tWarning:" + str(x.warnings))
        print("\t\t\t\tWarning Code:" + str(x.warning_codes))

def subDomains(domainName):
    x = 0
    print("\tEnumerating Subdomains")
    sdClient = sd.Client(apiKey)
    sdResponse = sdClient.get(domainName)

    for record in sdResponse.result.records:
        print("\t\tSub-Domain[{}]: {}".format(str(x), record.domain))
        x+=1

def dnsLookUps(domainName):
    print("\tDNS Records")
    sdDNS = dns.Client(apiKey)
    sdRIP = rip.Client(apiKey)
    sdGeo = geoip.GeoIP(apiKey)

    sdResponse = sdDNS.get(domainName)

    for rec in sdResponse.records_by_type['A']:
        ipAddr = str(rec.value)
        print("\t\tA Record:" + ipAddr)
        print("\t\t\tIP Geo Location:")
        geoData = sdGeo.lookup(ipAddr)
        print("\t\t\t\tCountry: {}, Region: {}, City: {}".format(
            geoData['location']['country'],
            geoData['location']['region'],
            geoData['location']['city']))
        print("\t\t\t\tLong: {}, Lat: {}, Zipcode {}, Timezone: {}".format(
            geoData['location']['lng'],
            geoData['location']['lat'],
            geoData['location']['postalCode'],
            geoData['location']['timezone'] ) )
        result = sdRIP.data(str(rec.value))
        for record in result.result:
            print("\t\t\tReverse IP: {}, visited: {}".format(record.name, record.last_visit))

    for rec in sdResponse.records_by_type['MX']:
        print("\t\tMX Record:" + str(rec.value))

    for rec in sdResponse.records_by_type['NS']:
        print("\t\tNS Record:" + str(rec.value))

    for rec in sdResponse.records_by_type['TXT']:
        print("\t\tTXT Record:" + str(rec.value))

def whoisRecord(domainName):
    print("\tWHOIS Record")
    whoClient = who.Client(api_key=apiKey)
    whois = whoClient.data(domainName)
    print("\t\tWHOIS Creation Date:" + str(whois.created_date_normalized))
    print("\t\tWHOIS Expiration Date:" + str(whois.expires_date_normalized))
    print("\t\tWHOIS Server(s):" + whois.whois_server)
    for x in whois.name_servers.host_names:
        print("\t\t\t" + x)
    print("\t\tWHOIS Registrant:" + whois.registrant.name)
    print("\t\tWHOIS Registrar:" + whois.registrar_name)
    print("\t\tWHOIS IANAID:" + whois.registrar_ianaid)
    print("\t\tWHOIS Contact Email:" + whois.contact_email)

if __name__ == '__main__':
  
# mapdomains.csv is a list of all the domain names to expand

    try:
        f = open("mapdomains.csv", "r")
    except:
        print("Failed to open mapdomains.csv file")
        sys.exit(0)

    for x in f:
        domainName = x.strip()
        print("Domain: " + domainName)

        whoisRecord(domainName)
        domainReputation(domainName)
        dnsLookUps(domainName)
        subDomains(domainName)

