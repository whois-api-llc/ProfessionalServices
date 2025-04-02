#!/bin/bash

# Set parameters
fwlogfile="fw-download.log"
today=$(date -d "yesterday" +%Y-%m-%d)
rundate=$(date +%Y-%m-%d)

# Set output and data directory
odir="./"
datadir="./"

# Authentication - Replace with your actual API key
api_key="YOUR_API_KEY"

# Construct the auth string for Basic Authentication (username = api_key, password = api_key)

# API Endpoint
fwendpoint="https://download.whoisxmlapi.com/datafeeds/First_Watch_Malicious_Domains_Data_Feed/pro"

# Construct the download URL and file paths
fwurl="${fwendpoint}/fwmd.${today}.pro.daily.data.csv.gz"
fwfile="${odir}fw.${today}.pro.daily.data.csv.gz"
csvfile="${odir}fw.${today}.pro.daily.data.csv"

# Log start
echo "[ ${rundate} ] Begin download for ${today}: ${fwurl}" >> "$fwlogfile"

# Download File
cmd="wget --user $api_key --password $api_key $fwurl -O $fwfile"

echo "*************"
echo $cmd
echo "*************"

wresult=$($cmd)

# Check if download was successful
if [ $? -eq 0 ]; then
    echo "[ ${rundate} ] Download successful: ${fwfile}" >> "$fwlogfile"

    # Check if file exists
    if [ -f "$fwfile" ]; then
        # Decompress .gz file
        gunzip "$fwfile"
        
        if [ $? -eq 0 ]; then
            echo "[ ${rundate} ] Successfully decompressed: ${fwfile} to ${csvfile}" >> "$fwlogfile"
        else
            echo "[ ${rundate} ] Error: Decompression failed - ${fwfile}" >> "$fwlogfile"
        fi
    else
        echo "[ ${rundate} ] Error: File does not exist - ${fwfile}" >> "$fwlogfile"
    fi
else
    echo "[ ${rundate} ] Error: Download failed - ${fwurl}" >> "$fwlogfile"
fi
