import sqlite3
import sys
import struct
import socket

ipaddr = sys.argv[1]

def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

if __name__ == '__main__':

	dbconn = sqlite3.connect("geoip4.db")

	cur = dbconn.cursor()

	sqlquery = "select * from geoip where " + str(ip2int(ipaddr)) + " between mark and nextMark limit 1"

	for row in cur.execute(sqlquery):
   		print(row)
