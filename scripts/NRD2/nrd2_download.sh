#!/bin/bash
# v2:  NRD 2.0 Downloader   12/2/2025
# Downloads Newly Registered Domains data from WhoisXMLAPI
# Requires environment variable WXAKEY to contain API key

set -euo pipefail

############################################
# Configuration
############################################

: "${WXAKEY:?Environment variable WXAKEY must be set}"

LOGFILE="wxa-nrd-download.log"
TODAY=$(date -d "yesterday" '+%Y-%m-%d')

# Change to match your environment 
ODIR="./"        # Output directory
DATADIR="./"     # Decompressed CSV directory

NRD_ENDPOINT="https://newly-registered-domains.whoisxmlapi.com/datafeeds/Newly_Registered_Domains_2.0"
NRD_SUB="ultimate"  # Options: basic, enterprise, lite, professional, ultimate

############################################
# File Paths
############################################

NRD_URL="${NRD_ENDPOINT}/${NRD_SUB}/daily/${TODAY}/nrd.${TODAY}.${NRD_SUB}.daily.data.csv.gz"
GZ_FILE="${ODIR}nrd.${TODAY}.${NRD_SUB}.daily.data.csv.gz"
CSV_FILE="${DATADIR}nrd.${TODAY}.${NRD_SUB}.daily.data.csv"

############################################
# Logging function
############################################
log() {
    echo "[ $(date '+%Y-%m-%d %H:%M:%S') ] $1" | tee -a "$LOGFILE"
}

log "Beginning download for date ${TODAY}"
log "URL: ${NRD_URL}"

############################################
# Download file
############################################

if command -v curl >/dev/null 2>&1; then
    log "Using curl for download, please stand by..."
    if ! curl -s -u "$WXAKEY:$WXAKEY" -o "$GZ_FILE" "$NRD_URL"; then
        log "ERROR: Failed to download file from $NRD_URL"
        exit 1
    fi
else
    log "Using wget for download, please stand by..."
    if ! wget --quiet --user="$WXAKEY" --password="$WXAKEY" -O "$GZ_FILE" "$NRD_URL"; then
        log "ERROR: Failed to download file from $NRD_URL"
        exit 1
    fi
fi

log "Download successful: $GZ_FILE , decompressing, please stand by..."

############################################
# Decompress
############################################
if [[ -f "$GZ_FILE" ]]; then
    gunzip -c "$GZ_FILE" > "$CSV_FILE"
    log "Successfully decompressed to: $CSV_FILE"
else
    log "ERROR: File not found after download: $GZ_FILE"
    exit 1
fi

log "Completed NRD download and extract operation."

