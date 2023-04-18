# kyc-apis by WHOIS.py
# Developed by Professional.Services@whoisxmlapi.com  v1.0   17 April 2023
# This file is provided "as-is" with no warranty or support
# You will need to obtain a valid API key with sufficient credits from whoisxmlapi.com
#  WHOISXMLAPI GitHub Repository can be found at https://github.com/whois-api-llc/
# The purpose of this file is to demonstrate how to use various APIs to obtain kyc artifacts
# Contact sales@whoisxmlapi.com for more information
# Min Req: Python 3.6+
# To check the versions of the modules installed, use 'pip show <module-name>'.  For example: pip show whois-api
# NOTE: This code is writen at a very basic level for demonstration purposes.

from urllib.request import urlopen, pathname2url
# load WHOISXMLAPI modules
import whoisapi as who
import domainreputation as dr
import dnslookupapi as dns
import simple_geoip as geoip
# standard python modules
import json
import sys

# set the API key
apiKey = ''

def domainReputation(domainName):

	drClient = dr.Client(apiKey)

	drResponse = drClient.get(domainName)

	if drResponse.reputation_score <= 72:
		print("\t\tDomain Reputation Score too low.\n")
	else:
		print("\t\tDomain Reputation score passed: ", drResponse.reputation_score)

def whoisRecord(domainName):
	
	print("\tWHOIS Record")

	whoClient = who.Client(api_key=apiKey)

	whois = whoClient.data(domainName)

	print("\t\t\tWHOIS Creation Date:" + str(whois.created_date_normalized))
	print("\t\t\tWHOIS Server(s):" + whois.whois_server)
	for x in whois.name_servers.host_names:
		print("\t\t\t\t" + x)
	print("\t\t\tWHOIS Registrant:" + whois.registrant.name)
	print("\t\t\tWHOIS Registrar:" + whois.registrar_name)
	print("\t\t\tWHOIS Contact Email:" + whois.contact_email)


def run_email_results(result):

	i = 0

	sdDNS = dns.Client(apiKey)

	emailAddr = result['emailAddress']

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
		printf("\t\t\tThis email domain is reported as disposbile, done.\n")
		return 0

	geoResults = geobyEmail(emailAddr)

	print(f"\t\tGeo Location data....")

	print(f"\t\t\tCountry: {geoResults['location']['country']}, State: {geoResults['location']['region']}, City: {geoResults['location']['city']}")

	print("\tE-Mail Verification Results.. PASSED\n")

	domainName = emailAddr[emailAddr.index('@') + 1 : ]

	print("\tNow checking for DNS NS records for", domainName)

	nsResponse = sdDNS.get(domainName, 'NS')

	if 'NS' in nsResponse.records_by_type:
		for rec in nsResponse.records_by_type['NS']:

			ns = rec.value[:-1]
			
			nsResponse = sdDNS.get(ns, 'A')

			if 'A' in nsResponse.records_by_type:
				#print(">>>>>>>> LEN ", str(nsResponse.records_by_type['A']))
				for nsrec in nsResponse.records_by_type['A']:
					geoByIP(ns, nsrec['value'])
					print("\t\t\t\t", ns, nsrec['value'])

	print("\tNow checking for DNS MX domain records such as domain creation dates, country codes")

	mxRecCount = len(result['mxRecords'])

	print("\t\tThere are", str(mxRecCount), "MX Record(s):")

	if mxRecCount == 0:
		print("\t\tBecause there are zero MX records, this is not a valid email configuration, done.\n")
		sys.exit(1)

	for mx_records in result['mxRecords']:
		tmp = mx_records[:-1]

		sdResponse = sdDNS.get(tmp, 'A')

		if 'A' in sdResponse.records_by_type:
			for rec in sdResponse.records_by_type['A']:
				geoByIP(tmp, rec['value'])

	return 1

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


def load_email(emailAddr):

	api_url = 'https://emailverification.whoisxmlapi.com/api/v1'

	url = api_url\
    		+ '?emailAddress=' + pathname2url(emailAddr)\
    		+ '&apiKey=' + pathname2url(apiKey)\
    		+ '&outputFormat='
	
	output_format = 'json'

	api_url = url + pathname2url(output_format)

	result = json.loads(urlopen(api_url).read().decode('utf8'))

	retcode = run_email_results(result)

	return retcode


if __name__ == '__main__':

	print("\nKYC Evaluation:")
	print("\n\t1) E-mail Address")
	print("\t2) E-mail Address and Source IP Address")
	print("\t3) E-Mail Address, Source IP Address, and Domain Name")
	print("\tq) Quit\n")
	
	eval_selection = input("Enter selection: ")

	if eval_selection == "q":
		sys.exit(0)

	emailAddr = input("Enter e-mail Address: ")

	retcode = load_email(emailAddr)

	if retcode == 0:
		sys.exit(0)

	domainName = emailAddr[emailAddr.index('@') + 1 : ]

	print("\nChecking Domain name reputation for", domainName)

	domainReputation(domainName)
