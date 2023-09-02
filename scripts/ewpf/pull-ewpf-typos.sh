#!/bin/bash
wGetoutput="--quiet"
runYear=$1
runMonth=$2
begDay=$3
endDay=$4
# SET your api key or change code to use environmental variable
WXAKEY=<YOUR_API_KEY>
echo "Downloading Data Feed for $runMonth $begDay through $endDay"
ewpfendpoint="https://threat-prediction.whoisxmlapi.com/datafeeds/Early_Warning_Phishing_Data_Feed/"
for ((i=${begDay}; i<=${endDay}; i++))
  do
   printf -v typodate '%d-%02d-%02d' "$runYear" "$runMonth" "$i" 
   typocnturl="$ewpfendpoint"ewpf.typosquatting."$typodate".counts.csv
   echo $typocnturl
   cmd="wget $wGetoutput --user $WXAKEY --password $WXAKEY $typocnturl"
   $($cmd)
   if [ $? -ne 0 ];
      then
         echo "   ** File not found $typocnturl" 
      else
         echo "   -> Download successful for $typodate" 
   fi
   
   typodataurl="$ewpfendpoint"ewpf.typosquatting."$typodate".csv
   echo $typodataurl
   cmd="wget $wGetoutput --user $WXAKEY --password $WXAKEY $typodataurl"
   $($cmd)
   if [ $? -ne 0 ];
      then
         echo "   ** File not found $typodataurl" 
      else
         echo "   -> Download successful for $typodate" 
   fi
done
