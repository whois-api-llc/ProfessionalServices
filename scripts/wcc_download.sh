#!/bin/bash
#
# Set the API key. Recommend not hard coding this but making it read from an environmental variable.
#    for example apiKey = os.getenv('WXAAPIKEY')
apiKey="<YOUR_API_KEY>"
echo "Download Completed."
# Format todays date in YYYY-MM-DD format
today=$(date '+%Y_%m_%d')
#
echo "Downloading web contacts and categories for $today"
# format the urls
contacts_url="ftp://user:"$apiKey"@datafeeds.whoisxmlapi.com:21210/Daily_Website_Contacts_and_Categorization/daily_full_dumps_contacts/"
categories_url="ftp://user:"$apiKey"@datafeeds.whoisxmlapi.com:21210/Daily_Website_Contacts_and_Categorization/daily_full_dumps_categories/"
# format the name files
categories_file="categories_$today".csv.gz
contacts_file="contacts_$today".csv.gz
echo "Contacts file to retrieve = $contacts_file"
echo "Categories file to retrieve = $categories_file"
categories_cmd=$categories_url$categories_file
contacts_cmd=$contacts_url$contacts_file
fetch="wget -m ftp"
# In this interactive example, --progress=bar is used. Recommend switching to -q for quiet mode
fetch_options="-c --progress=bar:force -O"
# Get the contacts file first
cmdcontacts="$fetch $contacts_cmd $fetch_options $contacts_file"
echo "[ $rundate ] Begin Contacts download for $today using $cmdprod"
wresult=$($cmdcontacts)
# recommending evaluating the results stored in wresult and performing action such as decompressing the file
# Get the categories file next
cmdcat="$fetch $categories_cmd $fetch_options $categories_file"
echo "[ $rundate] Begin Categories download for $today using $cmdcat"
wresult=$($cmdcat)
# recommending evaluating the results stored in wresult and performing action such as decompressing the file
echo "Download Completed."
