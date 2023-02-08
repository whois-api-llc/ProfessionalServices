#!/bin/bash
# Professional.Services@whoisxmlapi.com
#   Unsupported. This script will attempt to identify when a new quarterly release is ready based on the time its run.
#
# gTLD base URL
baseurl="https://domainwhoisdatabase.com/whois_database/v"

# Quarterly Release Months 
qMonths=(00 02 03 00 00 06 00 00 09 00 00 12)
qStartYear=2023

quarterlyVersion=()
quarterlyYear=()
quarterlyMonths=()
quarterlyDates=()

# Quarterly Release Day + 1
qReleaseDay=02
# Signal to proceed to download
proceed=0
inc=0
tmp=0
mon=0
ver=0

# Get date vars
year=$(date +%Y)
month=$(date +%m)
day=$(date +%d)
ymdate=$(date +%Y+%m)

for x in {43..60}
do
	if (( $qStartYear > $year )); then
		break
	fi

	quarterlyVersion[$tmp]+=$x

	if [[ $inc == "4" ]]; then 
		inc=0
		mon=0
		((qStartYear++))
	fi

	quarterlyYear[$tmp]+=$qStartYear

	for months in ${qMonths[@]}; do
		dmt=${quarterlyYear[$tmp]}"$months$qReleaseDay"
		#echo "Date=[$dmt] Version=[${quarterlyVersion[$tmp]}"
	done
	
	((tmp++))
	((inc++))
done					  

# DEBUG Map
tmp=0
#echo "******************** QUARTERLY VERSION MAP **********************"
for y in "${quarterlyVersion[@]}"; do
	#echo "Version # $y Year = ${quarterlyYear[$tmp]}"
	((tmp++))
done

# Determine if this is a quarterly yera, month, and day matches

tmp=0
for i in "${quarterlyVersion[@]}"; do
	if [[ $proceed = "1" ]]; then
			  break
	fi

	if [[ $year == ${quarterlyYear[$tmp]} ]] ; then
		for m in "${qMonths[@]}"; do
			if [[ $month = $m ]] ; then
				if [[ $day = $qReleaseDay ]]; then
					ver=$i
					echo "Found Quarterly Release: $ver"
					proceed=1
				fi
			fi
		done
	fi
	((tmp++))
done

if [[ "$proceed" -eq 1 ]]; then
	fullurl="$baseurl$ver"
	status_code=$(curl --write-out %{http_code} --silent --output /dev/null ${fullurl})

	if [[ "$status_code" -ne 403 ]] ; then
		echo "Quarterly is Available"
	else
		echo "Quarterly Not Available Yet"
		exit 1
	fi
else
	echo "No match on quarterlies."
fi

echo "Done"
exit 0
