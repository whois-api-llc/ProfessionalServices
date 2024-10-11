#!/bin/bash
# Simple Daily IP Netblocks Download Script
# Professional.Services@whoisxmlapi.com
#
nooutput="--quiet"
# nooutput=""
ipblock_logfile="ipnetblocks-download.log"
today=$(date '+%Y-%m-%d')
rundate=$(date)  # Capture the full timestamp for logging
savedir="./"
auth="at_YOURAPIKEY"
ipnetblockURL="https://ip-netblocks.whoisxmlapi.com/datafeeds/IP_Netblocks_WHOIS_Database/"
ip_file="ip_netblocks.$today.full.blocks.csv.gz"
ip_fullURL="$ipnetblockURL$ip_file"
fetcher="wget"
cmd="$fetcher $nooutput --user $auth --password $auth $ip_fullURL -O $savedir$ip_file"

# Logging the start of the download
echo "[ $rundate ] Begin download for $today: $cmd" >> $ipblock_logfile

# Executing the download command
wresult=$($cmd)

# Error handling and logging
if [ $? -ne 0 ]; then
    echo "[ $rundate ] File not found or download failed: $savedir$ip_file" >> $ipblock_logfile
else
    echo "[ $rundate ] Download successful: $savedir$ip_file" >> $ipblock_logfile
fi
