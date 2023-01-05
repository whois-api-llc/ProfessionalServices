#!/bin/bash
wGetoutput="--quiet"
runYear=$1
runMonth=$2
begDay=$3
endDay=$4
# SET your api key or change code to use environmental variable
WXAKEY=$WXAAPIKEY
echo "Downloading Typosquatting Community Data Feed for $runMonth $begDay through $endDay"
typoendpoint="https://typosquatting.whoisxmlapi.com/datafeeds/Typosquatting_DataFeed/"
for ((i=${begDay}; i<=${endDay}; i++))
  do
   printf -v typoDate '%d-%02d-%02d' "$runYear" "$runMonth" "$i"
   typourl="$typoendpoint"typosquatting."$typoDate".daily.trial.enriched.csv
   cmd="wget $wGetoutput --user $WXAKEY --password $WXAKEY $typourl"
   $($cmd)
   if [ $? -ne 0 ];
      then
         echo "   ** File not found $typourl" 
      else
         echo "   -> Download successful for $typoDate" 
   fi
done
