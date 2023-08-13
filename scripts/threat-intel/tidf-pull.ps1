 # The code provided is provided "as-is" for demonstration purposes.
 # The file will format the date as yesterdays date. 
 # You can add this to the Windows Schedular to run daily.

# Set colors
$redText = [char]27 + '[31m'
$greenText = [char]27 + '[32m'
$yellowText = [char]27 + '[33m'
$blueText = [char]27 + '[34m'
$resetColor = [char]27 + '[0m'

Write-Host "Downloading Theat Intel data from whoisxmlapi.com"
Write-Host "Contact sales@whoisxmlapi.com for more information."

# Define the list of files to download.  Modify list to match your use case.
$tidfFileNamePreFix = "tidf."
$tidfFileNameExtension = ".gz"
$tidfFileNames = @( 	
			"deny-cidrs.v4",
			"deny-cidrs.v6",
			"deny-domains",
			"deny-ips.v4",
			"deny-ips.v6",
			"hosts",
			"malicious-cidrs.v4.csv",
			"malicious-cidrs.v4.jsonl",
			"malicious-cidrs.v6.csv",
			"malicious-cidrs.v6.jsonl",
			"malicious-domains.csv",
			"malicious-domains.jsonl",
			"malicious-file-hashes.csv",
			"malicious-file-hashes.jsonl",
			"malicious-ips.v4.csv",
			"malicious-ips.v6.csv",
			"malicious-ips.v4.jsonl",
			"malicious-ips.v6.jsonl"
			"malicious-urls.csv",
			"malicious-urls.jsonl",
			"nginx-access.v4",
			"nginx-access.v6"
		)

# Define the base URL where the WXA Threat Intel files are located
$baseUrl = "https://threat-intelligence.whoisxmlapi.com/datafeeds/Threat_Intelligence_Data_Feeds/"

# Manually define the WHOISXMLAPI.COM API Key
$apiKey = "<YOUR_API_KEY>"
# Better to define it in the environment
#$apiKey = $env:WXAAPIKEY

# Credentials for username/password authentication, setting both to $apiKEy
$username = $apiKey
$password = $apiKey | ConvertTo-SecureString -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential -ArgumentList @($username, $password)

# Specify the local path where you want to save the downloaded zip file
$localPath = "C:\TEMP"

# Get the current date in the desired format (YYYY-MM-DD)
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")

Write-Host "Preparing to download $($tidfFileNames.Count) files for $yesterday"

$iterationCount = 0

foreach ($tdifFileName in $tidfFileNames) {

	$iterationCount++

	# Construct the URL for tdif.YYYY-MM-DD.daily.
	$tdifGetFile = "tidf.${yesterday}.daily.${tdifFileName}${tidfFileNameExtension}"

	$completeURI = $baseUrl + $tdifGetFile

	# Create the full local path for the zip file
	$localFilePath = Join-Path -Path $localPath -ChildPath $tdifGetFile

	# Use the Invoke-WebRequest cmdlet to download the zip file
	try {
		Write-Host "${yellowText} $iterationCount ... Downloading $tdifGetFile file to: $localFilePath${resetColor}"
    		Invoke-WebRequest -Uri $completeURI -OutFile $localFilePath -Credential $credential
		Write-Host "${greenText}  Success${resetColor}" 
	} catch {
    		Write-Host "${redText}  An error occurred while downloading the $tdifGetFile file${resetColor}"
    		Write-Host "${redText}  Error details: $($_.Exception.Message)${resetColor}"
	}
}
