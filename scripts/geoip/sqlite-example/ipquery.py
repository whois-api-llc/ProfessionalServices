import sqlite3
import sys
import struct
import socket

def last_octet(ip):
    octets = ip.split('.')
    octets[-1] = '0'
    new_ip = '.'.join(octets)
    return new_ip

def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

if __name__=='__main__':

    dbconn = sqlite3.connect(sys.argv[1])

    cur = dbconn.cursor()

    # convert ipv4 address to integer rounding down the last octet to 0 and converting it to int
    ipaddr_str = str(ip2int(last_octet(sys.argv[2])))

    sqlquery = "select * from geoip_table where mark = " + ipaddr_str + " ;"

    print("Issuing query:", sqlquery)

    for row in cur.execute(sqlquery):
        print(row)

# example:
# python query-ipgeo-db.py ipgeo.db 4.4.4.4
#
# output:
# (67372032, 'Level 3 Communications, Inc.', '', 'US', 'Hawaii', 'Woodlawn', 21.31808, -157.80676, '', '-10:00', 5854894)
