# Set parameters
$nooutput = $true
$nrdlogfile = "wxa-nrd-download.log"
$today = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$rundate = (Get-Date).ToString("yyyy-MM-dd")
$odir = ".\"
$datadir = ".\"
$auth = "YourAPIKey"
$nrdendpoint = "https://newly-registered-domains.whoisxmlapi.com/datafeeds/Newly_Registered_Domains_2.0/"
# NOTE: nrdsub options are basic, enterprise, lite, professional, and ultimate
$nrdsub = "basic"
$nrdurl = "$nrdendpoint$nrdsub/daily/$today/nrd.$today.$nrdsub.daily.data.csv.gz"
$nrdfile = "nrd.$today.$nrdsub.daily.data.csv.gz"
$csvfile = "nrd.$today.$nrdsub.daily.data.csv"
$fetcher = "Invoke-WebRequest"

# Construct the command
$cmd = "$fetcher -Uri $nrdurl -OutFile $($odir + $nrdfile) -Credential (New-Object PSCredential -ArgumentList @('user', (ConvertTo-SecureString -String $auth -AsPlainText -Force)))"

# Log the command
Add-Content -Path $nrdlogfile -Value ("[ $rundate ] Begin download for $today: $cmd")

# Execute the command
try {
    Invoke-Expression -Command $cmd
    Add-Content -Path $nrdlogfile -Value ("Download successful $nrdurl")
    
    # Check if the file exists
    if (Test-Path "$odir$nrdfile") {
        Expand-Archive -Path "$odir$nrdfile" -DestinationPath $datadir -Force
        Add-Content -Path $nrdlogfile -Value ("Successfully decompressed $odir$nrdfile to $datadir$csvfile")
    } else {
        Add-Content -Path $nrdlogfile -Value ("File does not exist: $odir$nrdfile")
    }
} catch {
    Add-Content -Path $nrdlogfile -Value ("File not found $nrdurl")
}
