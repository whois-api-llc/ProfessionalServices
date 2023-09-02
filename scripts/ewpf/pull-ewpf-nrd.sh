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
   printf -v nrddate '%d-%02d-%02d' "$runYear" "$runMonth" "$i" 
   nrdcnturl="$ewpfendpoint"ewpf.nrd."$nrddate".counts.csv
   echo $nrdcnturl
   cmd="wget $wGetoutput --user $WXAKEY --password $WXAKEY $nrdcnturl"
   $($cmd)
   if [ $? -ne 0 ];
      then
         echo "   ** File not found $nrdcnturl" 
      else
         echo "   -> Download successful for $nrddate" 
   fi
   
   nrddataurl="$ewpfendpoint"ewpf.nrd."$nrddate".csv
   echo $nrddataurl
   cmd="wget $wGetoutput --user $WXAKEY --password $WXAKEY $nrddataurl"
   $($cmd)
   if [ $? -ne 0 ];
      then
         echo "   ** File not found $nrddataurl" 
      else
         echo "   -> Download successful for $nrddate" 
   fi
done
