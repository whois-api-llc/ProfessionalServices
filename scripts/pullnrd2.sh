#!/bin/bash
# Script to grab a range of NRD2 files 
# Example: bash ./pullnrd 2022 06 1 30
#     year month start_day end_day
# Replace with your API Key from whoisxmlapi.com

nooutput="--quiet"

runYear=$1
runMonth=$2
begDay=$3
endDay=$4

WXAKEY=<Your_API_Key>

echo "Downloading NRD2 Data Feed for $runMonth $begDay through $endDay"

nrdEndpoint="https://newly-registered-domains.whoisxmlapi.com/datafeeds/Newly_Registered_Domains_2.0/ultimate/daily/"

for ((i=${begDay}; i<=${endDay}; i++))
  do
   printf -v nrdDate '%d-%02d-%02d' "$runYear" "$runMonth" "$i"
   nrdURL="$nrdEndpoint$nrdDate/"nrd".$nrdDate."ultimate"."daily.data"."csv"."gz
   cmd="wget $nooutput --user $WXAKEY --password $WXAKEY $nrdURL"
   $($cmd)
   if [ $? -ne 0 ];
      then
         echo "   ** File not found $nrdURL"
      else
         echo "   -> Download successful for $nrdDate"
   fi
done
