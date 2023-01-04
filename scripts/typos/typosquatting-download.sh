# Example: Daily download of Typosquatting Data Feed
# ed@whoisxmlapi.com
nooutput="--quiet"
logfile="/var/log/wxa-typosquatting-download.log"
today=$(date '+%Y-%m-%d' -d "yesterday")
datadir="/data/typos/"
auth=<<<YOURAPIKEY>>>
datafeedurl=https://subdomains.whoisxmlapi.com/datafeeds/Typosquatting_DataFeed/typosquatting."$today".daily.full.basic.csv
fetcher="wget"
cmd="$fetcher $nooutput --user $auth --password $auth $datafeedurl -O $datadir"typosquatting".$today.daily.full.basic.csv"
echo "[$today] Begin download for $today: $cmd" >> $logfile
wresult=$($cmd)
#add logic to evaluate wresult
