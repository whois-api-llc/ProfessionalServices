# kyc.py by WHOISXMLAPI.COM
# Developed by Professional.Services@whoisxmlapi.com  v2.0   Feb 2024
# This file is provided "as-is" with no warranty or support
# You will need to obtain a valid API key with sufficient credits from whoisxmlapi.com
#  WHOISXMLAPI GitHub Repository can be found at https://github.com/whois-api-llc/
# The purpose of this file is to demonstrate how to use various APIs to obtain kyc artifacts
# Contact sales@whoisxmlapi.com for more information
# Min Req: Python 3.11+
# To check the versions of the modules installed, use 'pip show <module-name>'.  For example: pip show whois-api
# This code is writen at a very basic level for demonstration purposes.
#
# <<< load WHOISXMLAPI modules >>>
# You can load each module as needed or run 'pip install -r requirements.txt"
# pip install whois-api
import whoisapi as who
# pip install subdomains-lookup
import subdomainslookup as sds
# pip install domain-reputation
import domainreputation as dr
# pip install dns-lookup-api
import dnslookupapi as dns
# pip install simple-geoip
import simple_geoip as geoip
# pip install reverse-mx
import reversemx as rmx
# pip install whois-history
import whoishistory as whohist
# pip install ip-netblocks
import ipnetblocks as ipnb
#
# standard python modules
from urllib.request import urlopen, pathname2url
import json
import sys
import timeit
import requests
from datetime import datetime
from collections import Counter
import json


# Set your API Key. Best practice is to set it from an environmental variable.

apiKey = '<YOUR_API_KEY>'
countryCodes = []

def whoisHistory(domainName):

	whohistClient = whohist.ApiClient(apiKey)

	print("\n\tThe number of WHOIS historical records for this domain is: ", whohistClient.preview(domainName))

def ipNetBlock(ipAddress):

    ipnbClient = ipnb.Client(apiKey)

    ipnbResponse = ipnbClient.get(ipAddress)

    if ipnbResponse.count > 0:
        asn = ipnbResponse['inetnums'][0]['AS']['asn']
        blockName = ipnbResponse['inetnums'][0]['AS']['name']
    else:
        asn = 0
        blockName = "Unknown"

    return asn, blockName


def domainReputation(domainName):

	drClient = dr.Client(apiKey)

	drResponse = drClient.get(domainName)

	if drResponse.reputation_score <= 72:
		print("\t\tDomain Reputation Score too low.\n")
	else:
		print("\t\tDomain Reputation score passed: ", drResponse.reputation_score)

def whoisRecord(domainName):
	
	print("\n\tWHOIS Record")

	whoClient = who.Client(api_key=apiKey)

	whois = whoClient.data(domainName)

	creation_date = datetime.strptime(str(whois.created_date_normalized), "%Y-%m-%d %H:%M:%S")
	t_date = datetime.today().strftime('%Y-%m-%d')
	todays_date = datetime.strptime(t_date, "%Y-%m-%d")
	delta = todays_date - creation_date

	print("\t\tCreation Date:" + str(whois.created_date_normalized))

	if delta.days <= 30:
		print(f"\t\tWARNING: Newly created domain, less than {delta.days} old.")
	else:
		print(f"\t\tDomain name is {delta.days} days old.")

	print("\t\tWHOIS Registrant:" + whois.registrant.name)
	print("\t\tWHOIS Registrar:" + whois.registrar_name)
	print("\t\tWHOIS Contact Email:" + whois.contact_email)


def extract_ips_from_dns_response(dns_response):
    ips = []
    if 'A' in dns_response.records_by_type:
        for record in dns_response.records_by_type['A']:
            ips.append(record['value'])
    return ips

def run_email_results(result):
    sdDNS = dns.Client(apiKey)
    rmxclient = rmx.Client(apiKey)
    sdsClient = sds.Client(apiKey)

    emailAddr = result['emailAddress']
    domainName = emailAddr[emailAddr.index('@') + 1 : ]

    print(f"\n\tE-mail: {emailAddr}")

    print(f"\t\tFormat Check......... {result['formatCheck']}")
    if result['formatCheck'] == 'false':
        print("\t\t\tFailed format check, done.\n")
        return 0

    print(f"\t\tSMTP Check........... {result['smtpCheck']}")
    if result['smtpCheck'] == 'false':
       print("\t\t\tFailed SMTP check, done.\n")
       return 0

    print(f"\t\tDNS Check............ {result['dnsCheck']}")
    if result['dnsCheck'] == 'false':
        print("\t\t\tFailed DNS Check, done.\n")
        return 0

    print(f"\t\tFree Email Check..... {result['freeCheck']}")
    if result['freeCheck'] == 'true':
        print("\t\t\tThis is reported as a free mail address, done.\n")
        return 0

    print(f"\t\tDisposible Check..... {result['disposableCheck']}")
    if result['disposableCheck'] == 'true':
        print("\t\t\tThis email domain is reported as disposable, done.\n")
        return 0

    geoResults = geobyEmail(emailAddr)
    print(f"\t\tGeo Location data....")
    print(f"\t\t\tCountry: {geoResults['location']['country']}, State: {geoResults['location']['region']}, City: {geoResults['location']['city']}")

    print("\tE-Mail Verification Results.. PASSED\n")

    ns_ips = []
    ns_domains = []
    print("\tNow checking for DNS NS records for", domainName)
    nsResponse = sdDNS.get(domainName, 'NS')
    if 'NS' in nsResponse.records_by_type:
        for rec in nsResponse.records_by_type['NS']:
            ns = rec.value[:-1]
            #print('HERE‘s NSSSSSS', ns, '----------------------')
            if ns not in ns_domains:
                 ns_domains.append(ns)
            ns_dns_response = sdDNS.get(ns, 'A')
            ns_ips.extend(extract_ips_from_dns_response(ns_dns_response))

            # NS IP
            for nsrec in ns_dns_response.records_by_type['A']:
                geoByIP(ns, nsrec['value'])
                print("\t\t\t\t", ns, nsrec['value'])
                ipASN, ipBlockName = ipNetBlock(nsrec['value'])
                print("\t\t\t\t ASN:", ipASN, "Name:", ipBlockName)
   # print("Extracted NS IPs:", ns_ips)
    #print(ns_domains)

    # MX IP
    mx_ips = []
    mx_domains = []
    print("\tNow checking DNS MX domain records for", domainName)
    mxRecCount = len(result['mxRecords'])
    print("\t\tThere are", str(mxRecCount), "MX Record(s):")
    if mxRecCount == 0:
        print("\t\tBecause there are zero MX records, this is not a valid email configuration.\n")
        sys.exit(1)

    for mx_record in result['mxRecords']:
        mx = mx_record[:-1]
        if mx not in mx_domains:
                 mx_domains.append(mx)
        mx_dns_response = sdDNS.get(mx, 'A')
        mx_ips.extend(extract_ips_from_dns_response(mx_dns_response))

        # Each MX IP Address
        for rec in mx_dns_response.records_by_type['A']:
            geoByIP(mx, rec['value'])
            rmxresult = rmxclient.data(mx)
            print(f"\t\t\t\tThere are {rmxresult.size} domains on this email server.")
            ipASN, ipBlockName = ipNetBlock(rec['value'])
            print(f"\t\t\t\tASN:", ipASN, "Name:", ipBlockName)
    #print("Extracted MS IPs:", mx_ips)
    #print(mx_domains)
    return 1, ns_ips, mx_ips, ns_domains, mx_domains


def load_email(emailAddr):

	api_url = 'https://emailverification.whoisxmlapi.com/api/v3'

	url = api_url\
    		+ '?emailAddress=' + pathname2url(emailAddr)\
    		+ '&apiKey=' + pathname2url(apiKey)\
    		+ '&outputFormat='
	
	output_format = 'json'

	api_url = url + pathname2url(output_format)

	result = json.loads(urlopen(api_url).read().decode('utf8'))

	retcode, ns_ips, mx_ips,ns_domains, mx_domains = run_email_results(result)    
	return retcode, ns_ips, mx_ips,ns_domains, mx_domains


def printSSLcert(domainName):
    api_url = 'https://ssl-certificates.whoisxmlapi.com/api/v1'

    url = api_url + '?domainName=' + pathname2url(domainName) + '&apiKey=' + pathname2url(apiKey)

    result = json.loads(urlopen(url).read().decode('utf8'))

    print("\n\tSSL Certificate Information:")

    try:
        if result['code'] >= 400:
            print(f"Unable to get certificate information, error {result['code']}")
            return None
    except:
        cert = result['certificates'][0]

        countryCodes.append(cert['issuer']['country'])

        ipASN, ipBlockName = ipNetBlock(result['ip'])

        print(f"\t\tIP.............: {result['ip']}")
        print(f"\t\tNetblock ASN...: {ipASN}")
        print(f"\t\tNetblock Name..: {ipBlockName}")
        print(f"\t\tPort...........: {result['port']}")
        print(f"\t\tChain Hierachy.: {cert['chainHierarchy']}")
        print(f"\t\tValidation type: {cert['validationType']}")
        print(f"\t\tValid from.....: {cert['validFrom']}")
        print(f"\t\tValid to.......: {cert['validTo']}")
        print(f"\t\tSubject CN.....: {cert['subject']['commonName']}")
        print(f"\t\tIssuer Country.: {cert['issuer']['country']}")
        print(f"\t\tOrganization...: {cert['issuer']['organization']}")

        return result['ip'],result['domain']


def geobyEmail(emailAddr):

	api_url = 'https://ip-geolocation.whoisxmlapi.com/api/v1'

	url = api_url\
    		+ '?email=' + pathname2url(emailAddr)\
    		+ '&apiKey=' + pathname2url(apiKey)
	
	result = json.loads(urlopen(url).read().decode('utf8'))

	return(result)

def geoByIP(fqdn, ipAddr):

	sdGeo = geoip.GeoIP(apiKey)

	geoData = sdGeo.lookup(ipAddr)

	print("\t\t\t{}, Country: {}, State/Region: {}, City: {}".format(
		fqdn,
		geoData['location']['country'],
		geoData['location']['region'],
		geoData['location']['city']))

	countryCodes.append(geoData['location']['country'])


### Threat-Intel
def get_threat_intel(ioc_value, apiKey):
    base_url = "https://threat-intelligence.whoisxmlapi.com/api/v1"
    url = f"{base_url}?apiKey={apiKey}&ioc={ioc_value}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"\t\tError retrieving Threat Intelligence for {ioc_value}: {response.status_code}, {response.text}")
        return None

def print_threat_intel_data(data, domainName):
    if data and "results" in data and len(data["results"]) > 0:
        print("\n\tThreat Intelligence Data:")
        for result in data["results"]:
            print(f"\t\tValue: {result['value']}")
            print(f"\t\tFirst Seen: {result['firstSeen']}")
            print(f"\t\tLast Seen: {result['lastSeen']}")
            print(f"\t\tThreat Type: {result['threatType']}")
            print(f"\t\tIOC Type: {result['iocType']}\n")
    else:
        print("\t\tNo IoC records found for " + domainName)

def query_and_print_threat_intel_for_ips(ns_ips, mx_ips, apiKey):
    # Threat-intel for NS IP
    for ip in ns_ips:
        threat_intel_data = get_threat_intel(ip, apiKey)
        if threat_intel_data:
            print(f"\n\t\tThreat Intelligence for NS IP {ip}:")
            print_threat_intel_data(threat_intel_data, ip)
        else:
            print(f"\n\t\tNo IoC records found for NS IP {ip}")

    # Threat-intel for MX IP
    for ip in mx_ips:
        threat_intel_data = get_threat_intel(ip, apiKey)
        if threat_intel_data:
            print(f"\n\t\tThreat Intelligence for MX IP {ip}:")
            print_threat_intel_data(threat_intel_data, ip)
        else:
            print(f"\n\t\tNo IoC records found for MX IP {ip}")

def query_and_print_threat_intel_for_domains(ns_domains, mx_domains, apiKey):
    # Threat-intel for NS domains
    for domain in ns_domains:
        threat_intel_data = get_threat_intel(domain, apiKey)
        if threat_intel_data:
            print(f"\n\t\tThreat Intelligence for NS domain {domain}:")
            print_threat_intel_data(threat_intel_data, domain)
        else:
            print(f"\n\t\tNo IoC records found for  {domain}")

    # Threat-intel for MX domains 
    for domain in mx_domains:
        threat_intel_data = get_threat_intel(domain, apiKey)
        if threat_intel_data:
            print(f"\n\t\tThreat Intelligence for MX domain {domain}:")
            print_threat_intel_data(threat_intel_data, domain)
        else:
            print(f"\n\t\tNo IoC records found for MX domain {domain}")


# Web_Categorization
def get_website_categorization(domain_value, apiKey):
    base_url = "https://website-categorization.whoisxmlapi.com/api/v3"
    url = f"{base_url}?apiKey={apiKey}&url={domain_value}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error Response: {response.text}")
        return {"error": f"HTTP Error: {response.status_code}"}

def print_website_categorization(response):
    domain_name = response.get('domainName', 'N/A')
    print(f"\n\t\tProcessing Domain: {domain_name}")
    if "error" in response:
        print(f"\t\tError: {response['error']}")
    else:
        as_info = response.get('as', {})
        print(f"\t\tASN: {as_info.get('asn', 'N/A')}")
        print(f"\t\tDomain: {as_info.get('domain', 'N/A')}")
        print(f"\t\tName: {as_info.get('name', 'N/A')}")
        print(f"\t\tRoute: {as_info.get('route', 'N/A')}")
        print(f"\t\tType: {as_info.get('type', 'N/A')}")

        print(f"\t\tDomain Name: {domain_name}")

        print("\t\tCategories:")
        for cat in response.get('categories', []):
            confidence = cat.get('confidence', 'N/A')
            name = cat.get('name', 'N/A')
            print(f"\t\t\tConfidence: {confidence}, Name: {name}")

        created_date = response.get('createdDate', 'N/A')
        print(f"\t\tCreated Date: {created_date}")

        website_responded = response.get('websiteResponded', 'N/A')
        print(f"\t\tWebsite Responded: {website_responded}")
    print('')
    
def categorize_domains(domains, apiKey):
    categorization_results = {}
    for domain in domains:
        try:
            response = get_website_categorization(domain, apiKey)
            categorization_results[domain] = response
            print_website_categorization(response)  
        except Exception as e:
            error_message = f"Error categorizing {domain}: {e}"
            error_response = {"error": error_message}
            categorization_results[domain] = error_response
            print_website_categorization(error_response) 
    return categorization_results

     

if __name__ == '__main__':
    
    # Check if the script is run without command-line arguments
    if len(sys.argv) == 1:

        print("\nKYC Evaluation:")
        print("\n\t1) E-mail Address")
        print("\tq) Quit\n")

        eval_selection = input("Enter selection: ")

        # Exit if the user selects 'q'
        if eval_selection == "q":
            sys.exit(0)

        emailAddr = input("\nEnter e-mail Address: ")

        startwatch = timeit.default_timer()    
        print("\nStarting data collection process... ")

        retcode, ns_ips, mx_ips,ns_domains, mx_domains = load_email(emailAddr)

        if retcode == 0:
            sys.exit(0)

        domainName = emailAddr[emailAddr.index('@') + 1:]
        print("\n\tChecking Domain name reputation for", domainName)
        
        domainReputation(domainName)
        whoisRecord(domainName)
        whoisHistory(domainName)
        
        countryCodes.sort()
        countryCounter = Counter(countryCodes)
        
        print(f"\n\tCountries reported during this interrogation: {str(len(countryCounter))}\n\n\t\t", end="")
        for cnt in countryCounter:
            print(cnt, " ", end="")

        if eval_selection == '2':
            print("Phase 2 Under Construction")
        if eval_selection == '3':
            print("Phase 3 Under Construction")

        # Check Threat Intelligence data for email domain
        threat_intel_data = get_threat_intel(domainName, apiKey)
        print("\n\tChecking Domain Threat Intelligence Data for", domainName)
        if threat_intel_data:
            print_threat_intel_data(threat_intel_data, domainName)
        # Check Threat Intelligence data for email domain related MX/NS ip
        print('\n\tChecking IP Threat Intelligence Data for', domainName)
        query_and_print_threat_intel_for_ips(ns_ips, mx_ips, apiKey)
        
        # Check Threat Intelligence data for email domain related MX/NS domain
        print('\n\tChecking Domain Threat Intelligence Data for', domainName)
        query_and_print_threat_intel_for_domains(ns_domains, mx_domains, apiKey)

        # Check for website categorization
        website_categorization_data = get_website_categorization(domainName, apiKey)
        print("\n\tWebsite Categorization for", domainName)
        print_website_categorization(website_categorization_data)
        # Check for NS and MX website cateforization
        print("\n\tWebsite Categorization for NS Domains:")
        website_categorization_data_ns = categorize_domains(ns_domains, apiKey)

        print("\n\tWebsite Categorization for MX Domains:")
        website_categorization_data_mx = categorize_domains(mx_domains, apiKey)

        # Threat intelligence and Web-categorization for SSL
        print("\n\tWebsite Categorization and Threat Intelligence for SSL IP and domain:")
        ip_address,domain_name = printSSLcert(domainName)
        # Threat intelligence
        print('\n\tThreat Intelligence Check for SSL Domain', domain_name)
        threat_intel_data = get_threat_intel(domain_name, apiKey)
        if threat_intel_data:
             print_threat_intel_data(threat_intel_data, domain_name)
        print('\n\tThreat Intelligence Check for SSL IP', ip_address)
        threat_intel_data = get_threat_intel(ip_address, apiKey)
        if threat_intel_data:
             print_threat_intel_data(threat_intel_data, ip_address)
        # Web categorization
        print('\n\tWebsite Cateforization Check for SSL domain', domain_name)
        website_categorization_data = get_website_categorization(domain_name, apiKey)
        if website_categorization_data:
             print_website_categorization(website_categorization_data) 
        
        stopwatch = timeit.default_timer()
        print(f"\n\nDone, Elapsed time: {stopwatch-startwatch:0.2f} seconds.")
