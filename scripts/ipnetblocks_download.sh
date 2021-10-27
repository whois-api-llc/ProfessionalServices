#!/bin/bash
# Simple Daily IP Netblocks Download Script
nooutput="--quiet"
# nooutput=""
ipblock_logfile="ipnetblocks-download.log"
today=$(date '+%Y-%m-%d')
savedir="./"
auth="at_YOURAPIKEY"
ipnetblockURL="https://ip-netblocks.whoisxmlapi.com/datafeeds/IP_Netblocks_WHOIS_Database/"
ip_file="ip_netblocks.$today.full.blocks.csv.gz"
ip_fullURL="$ipnetblockURL$ip_file"
fetcher="wget"
cmd="$fetcher $nooutput --user $auth --password $auth $ip_fullURL -O $savedir$ip_file"
# echo "[ $rundate ] Begin download for $today: $cmd"
echo "[ $rundate ] Begin download for $today: $cmd" >> $ipblock_logfile
wresult=$($cmd)
if [ $? -ne 0 ];
  then
     echo "File not found $savedir$ip_filetype" >> $ipblock_logfile
  else
     echo "Download successful $ip_file" >> $ipblock_logfile
fi
