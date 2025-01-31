# Set parameters
$fwlogfile = "fw-download.log"
$today = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$rundate = (Get-Date).ToString("yyyy-MM-dd")

# Set output and data directory
$odir = ".\"
$datadir = ".\"

# Authentication - Replace with your actual username
$api_username = ""
$api_key = ""

# Encode credentials for Basic Authentication
$authString = "$api_username" + ":" + "$api_key"
$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($authString))

# API Endpoint
$fwendpoint = "https://download.whoisxmlapi.com/datafeeds/First_Watch_Malicious_Domains_Data_Feed/pro"

# Construct the download URL
$fwurl = "$fwendpoint/daily/fwmd.$today.pro.daily.data.csv.gz"
$fwfile = "$odir/fw.$today.pro.daily.data.csv.gz"
$csvfile = "$odir/fw.$today.pro.daily.data.csv"

# Log start
Add-Content -Path $fwlogfile -Value ("[ " + $rundate + " ] Begin download for " + $today + ": " + $fwurl)

# Download File
try {
    $headers = @{
        "Authorization" = "Basic $base64AuthInfo"
    }

    Invoke-WebRequest -Uri $fwurl -OutFile $fwfile -Headers $headers
    Add-Content -Path $fwlogfile -Value ("[ " + $rundate + " ] Download successful: " + $fwfile)

    # Check if file exists
    if (Test-Path $fwfile) {
        # Decompress .gz file using System.IO.Compression
        $decompressedFile = $fwfile -replace ".gz", ""

        $fs = New-Object IO.FileStream($fwfile, [IO.FileMode]::Open)
        $gs = New-Object IO.Compression.GzipStream($fs, [IO.Compression.CompressionMode]::Decompress)
        $outFs = [System.IO.File]::Create($decompressedFile)
        $gs.CopyTo($outFs)

        $gs.Close()
        $fs.Close()
        $outFs.Close()

        Add-Content -Path $fwlogfile -Value ("[ " + $rundate + " ] Successfully decompressed: " + $fwfile + " to " + $decompressedFile)
    } else {
        Add-Content -Path $fwlogfile -Value ("[ " + $rundate + " ] Error: File does not exist - " + $fwfile)
    }
} catch {
    Add-Content -Path $fwlogfile -Value ("[ " + $rundate + " ] Error: Download failed - " + $fwurl)
}
