import sqlite3
import sys
import struct
import socket
import ipaddress

ipfile = sys.argv[1]

def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

if __name__ == '__main__':

	invalidIPs = 0
	totalIPs = 0

	dbconn = sqlite3.connect("geoip4.db")

	with open(ipfile, 'r') as file:

		for linestr in file:
			try:
				ip_addr = ipaddress.ip_address(linestr.strip())
				totalIPs += 1
			except ValueError:
				invalidIPs += 1
				continue

			sqlquery = "select * from geoip where " + str(ip2int(str(ip_addr))) + " between mark and nextmark limit 1"

			cur = dbconn.cursor()

			for row in cur.execute(sqlquery):
				mark_ip = row[0]
				end_ip = row[1]
				start_ipd = row[2]
				end_ipd = row[3]
				country_code = row[4]
				region = row[5]
				city = row[6]
				lat = row[7]
				long = row[8]

			print(f"{str(ip_addr)},{mark_ip},{end_ip},{start_ipd},{end_ipd},{country_code},{region},{city},{lat},{long}")
		
print("\nTotal IP Adddresses processed: ", totalIPs)
print("Total skipped lines          : ", invalidIPs)
