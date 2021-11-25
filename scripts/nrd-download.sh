#!/bin/bash
# Example script to download the NRD 2.0 data feed from WHOISXMLAPI.com
# ed@whoisxmlapi.com
# - crontab -
# # m h  dom mon dow   command
# 0 4 * * * /var/scripts/nrd-download.sh
#
nooutput="--quiet"
nrdlogfile="wxa-nrd-download.log"
today=$(date '+%Y-%m-%d' -d "yesterday")
rundate=($date)
odir="./"
datadir="./"
auth=<<<YourAPIKey>>>
nrdendpoint="https://newly-registered-domains.whoisxmlapi.com/datafeeds/Newly_Registered_Domains_2.0/"
# NOTE: nrdsub options are basic, enterprise, lite, professional, and ultimate
nrdsub="basic"
nrdurl="$nrdendpoint"$nrdsub/daily/"$today"/nrd."$today".$nrdsub.daily.data.csv.gz
nrdfile="nrd.$today.$nrdsub.daily.data.csv.gz"
csvfile="nrd.$today.$nrdsub.daily.data.csv"
fetcher="wget"
cmd="$fetcher $nooutput --user $auth --password $auth $nrdurl -O $odir$nrdfile"
echo "[ $rundate ] Begin download for $today: $cmd" >> $nrdlogfile
wresult=$($cmd)
if [ $? -ne 0 ];
   then
      echo "File not found $nrdurl" >> $nrdlogfile
   else
      echo "Download successful $nrdurl" >> $nrdlogfile
      if [[ -f $odir$nrdfile ]]
         then
         gunzip -c $odir$nrdfile > $datadir$csvfile
         echo "Successfuly decompressed $odir$nrdfile to $datadir$csvfile" >> $nrdlogfile
       else
         echo "File does not exist: $odir$nrdfile" >> $nrdlogfile
      fi
fi
