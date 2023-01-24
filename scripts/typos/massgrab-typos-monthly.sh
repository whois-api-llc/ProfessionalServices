#!/bin/bash
wGetoutput="--quiet"
runYear=$1
startMonth=$2
endMonth=$3
WXAKEY=<YOURAPIKEY>"
echo "Downloading Typosquatting Data Feed for $runYear $startMonth $endMonth"
typoendpoint="https://typosquatting.whoisxmlapi.com/datafeeds/Typosquatting_DataFeed/"
for ((i=${startMonth}; i<=${endMonth}; i++))
  do
   printf -v typoDate '%d-%02d-01' "$runYear" "$i"
   echo -n "Now downloading (date).... $typoDate"
   typourl="$typoendpoint"typosquatting."$typoDate".monthly.full.enriched.csv
   cmd="wget $wGetoutput --user $WXAKEY --password $WXAKEY $typourl"
   $($cmd)
   if [ $? -ne 0 ];
      then
         echo "   ** File not found $typourl" 
      else
         echo "   Download successful" 
   fi
done
