# kyc.py by WHOISXMLAPI.COM
# Developed by Professional.Services@whoisxmlapi.com  v1.2   17 April 2023
# This file is provided "as-is" with no warranty or support
# You will need to obtain a valid API key with sufficient credits from whoisxmlapi.com
#  WHOISXMLAPI GitHub Repository can be found at https://github.com/whois-api-llc/
# The purpose of this file is to demonstrate how to use various APIs to obtain kyc artifacts
# Contact sales@whoisxmlapi.com for more information
# Min Req: Python 3.11+
# To check the versions of the modules installed, use 'pip show <module-name>'.  For example: pip show whois-api
# NOTE: This code is writen at a very basic level for demonstration purposes.
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
#
# standard python modules
from urllib.request import urlopen, pathname2url
import json
import sys, os
import timeit
from datetime import datetime
from collections import Counter

#hard coded
apiKey = '<SET_API_KEY>'
# or obtained from environmental variable
# apiKey = os.getenv("APIKEYNAME")

countryCodes = []

def whoisHistory(domainName):

	whohistClient = whohist.ApiClient(apiKey)

	print("\n\tThe number of WHOIS historical records for this domain is: ", whohistClient.preview(domainName))


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


def run_email_results(result):

	i = 0

	sdDNS = dns.Client(apiKey)
	rmxclient = rmx.Client(apiKey)
	sdsClient = sds.Client(apiKey)

	emailAddr = result['emailAddress']

	print(f"\n\tE-mail: {emailAddr}")

	print(f"\t\tFormat Check......... {result['formatCheck']}")

	if result['formatCheck'] == 'false':
		print("\t\t\tFailed format check, done.\n")
		return 0

	print(f"\t\tSMTP Check........... {result['smtpCheck']}")

	# if result['smtpCheck'] == 'false':
	#	print("\t\t\tFailed SMTP check, done.\n")
	#	return 0

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

	countryCodes.append(geoResults['location']['country'])

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
				rmxresult = rmxclient.data(tmp)
				print(f"\t\t\t\tThere are {rmxresult.size} domains on this email server.")

	sdsResponse = sdsClient.get(domainName)

	if sdsResponse.result.count == 0:
		print(f"\n\tWARNING: {domainName} has no subdomains")
	else:
		print(f"\n\tThe domain \"{domainName}\" has {sdsResponse.result.count} subdomains.")
	

	printSSLcert(domainName)

	return 1	

def printSSLcert(domainName):

	api_url = 'https://ssl-certificates.whoisxmlapi.com/api/v1'

	url = api_url\
    		+ '?domainName=' + pathname2url(domainName)\
    		+ '&apiKey=' + pathname2url(apiKey)
	
	result = json.loads(urlopen(url).read().decode('utf8'))

	print("\n\tSSL Certificate Information:")

	try:
		if result['code'] >= 400:
			print(f"Unable to get certificate information, error {result['code']}")
			return 0;
	except:
		cert = result['certificates'][0]

		countryCodes.append(cert['issuer']['country'])

		print(f"\t\tIP.............: {result['ip']}")
		print(f"\t\tPort...........: {result['port']}")
		print(f"\t\tChain Hierachy.: {cert['chainHierarchy']}")
		print(f"\t\tValidation type: {cert['validationType']}")
		print(f"\t\tValid from.....: {cert['validFrom']}")
		print(f"\t\tValid to.......: {cert['validTo']}")
		print(f"\t\tSubject CN.....: {cert['subject']['commonName']}")
		print(f"\t\tIssuer Country.: {cert['issuer']['country']}")
		print(f"\t\tOrganization...: {cert['issuer']['organization']}")

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

	# if no arguments are present, run interactive

	if len(sys.argv) == 1:

		print("\nKYC Evaluation:")
		print("\n\t1) E-mail Address (default)")
		print("\tq) Quit\n")
	
		eval_selection = input("Enter selection: ")

		if eval_selection == "q":
			sys.exit(0)

		emailAddr = input("\nEnter e-mail Address: ")

		startwatch = timeit.default_timer()	

		print("\nStarting data collection process... ")

		retcode = load_email(emailAddr)

		if retcode == 0:
			sys.exit(0)

		domainName = emailAddr[emailAddr.index('@') + 1 : ]

		print("\n\tChecking Domain name reputation for", domainName)

		domainReputation(domainName)

		whoisRecord(domainName)

		whoisHistory(domainName)

		countryCodes.sort()

		countryCounter = Counter(countryCodes)

		print(f"\n\tCountries reported during this interrogation: {str(len(countryCounter))}\n\n\t\t", end="")

		for cnt in countryCounter:
			print(cnt, " ", end="")

		stopwatch = timeit.default_timer()

		print(f"\n\nDone, Elapsed time: {stopwatch-startwatch:0.2f} seconds.")
