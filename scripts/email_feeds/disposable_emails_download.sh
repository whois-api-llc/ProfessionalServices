#!/bin/bash
# Example script to download the disposable data feed daily from WHOISXMLAPI.com
# Professional.Services@whoisxmlapi.com
# - crontab -
# # m h  dom mon dow   command
# 0 4 * * * /var/scripts/efeeds_download.sh
#
nooutput="--quiet"
email_logfile="efeeds_download.log"
yesterday=$(date '+%Y-%m-%d' -d "yesterday")
rundate=($date)
# set the paths
odir="./"
datadir="./"
# read environment variable APIKEY
auth=$APIKEY
email_endpoint="https://download.whoisxmlapi.com/datafeeds/Disposable_Email_Domains/"
disposable_file="disposable-emails.full.$yesterday.txt"
url="$email_endpoint$disposable_file"
cmd="wget $nooutput --user $auth --password $auth $url -O $disposable_file"
echo "[ $rundate ] Begin download for $today: $cmd" >> $email_logfile
echo $cmd
wresult=$($cmd)
cmd_exit_code=$?
if [ $cmd_exit_code -ne 0 ]; then
      echo "File not found or download failed: $url" >> $email_logfile
   else
      echo "Download successful: $url" >> $email_logfile
fi
