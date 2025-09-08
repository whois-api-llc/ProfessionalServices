# Powershell to extract JWT token from login API and lookup a domain name entered by the user.
# (C)2025 WHOISXMLAPI.COM
# This script will prompt you to enter your username and password which then will generate a JWT token 
# for subsquent API lookups.
#

function Get-JwtToken {
    param(
        [string]$Username,
        [string]$Password,
        [string]$ApiUrl = "https://firstwatch.yatic.io/api/login"
    )
    
    try {
        # Create the form data
        $body = @{
            username = $Username
            password = $Password
        }
        
        # Make the login request
        Write-Host "Attempting to login and retrieve JWT token..." -ForegroundColor Yellow
        Write-Host "API URL: $ApiUrl" -ForegroundColor Gray
        
        $response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
        
        # Debug: Show the raw response
        Write-Host "Raw API Response:" -ForegroundColor Yellow
        Write-Host ($response | ConvertTo-Json -Depth 3) -ForegroundColor Gray
        
        # Extract JWT token from response
        # Try common token field names
        $jwtToken = $null
        $tokenFields = @('token', 'access_token', 'jwt', 'authToken', 'accessToken', 'bearer')
        
        foreach ($field in $tokenFields) {
            if ($response.$field) {
                $jwtToken = $response.$field
                break
            }
        }
        
        # Check if token was found
        if ([string]::IsNullOrEmpty($jwtToken)) {
            Write-Host "JWT token not found in response" -ForegroundColor Red
            Write-Host "Response was: $($response | ConvertTo-Json)" -ForegroundColor Red
            return $null
        }
        
        return $jwtToken
    }
    catch {
        Write-Host "Failed to make API request:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
            Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
        }
        return $null
    }
}

# Function to check domain feed
function Check-DomainFeed {
    param(
        [string]$DomainName,
        [string]$JwtToken,
        [string]$ApiUrl = "http://firstwatch.yatic.io/api/feed/check"
    )
    
    try {
        # Create headers with the JWT token
        $headers = @{
            'Authorization' = "Bearer $JwtToken"
        }
        
        # Build the API URL with the domain name
        $feedCheckUrl = "$ApiUrl/$DomainName"
        Write-Host "Checking domain: $DomainName" -ForegroundColor Yellow
        Write-Host "API URL: $feedCheckUrl" -ForegroundColor Gray
        
        # Make the domain check API call
        $domainResponse = Invoke-RestMethod -Uri $feedCheckUrl -Method Get -Headers $headers
        
        # Display the domain check results
        Write-Host ""
        Write-Host "=== Domain Check Results ===" -ForegroundColor Green
        Write-Host ($domainResponse | ConvertTo-Json -Depth 3) -ForegroundColor Cyan
        
        return $domainResponse
    }
    catch {
        Write-Host "Failed to check domain:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
            Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
        }
        return $null
    }
}

# Main execution
try {
    # Prompt for username and password
    Write-Host "=== JWT Token Login ===" -ForegroundColor Cyan
    Write-Host ""
    
    $username = Read-Host "Enter username"
    $password = Read-Host "Enter password" -AsSecureString
    
    # Convert SecureString to plain text for the API call
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    Write-Host ""
    
    # Get the JWT token
    $JWT_TOKEN = Get-JwtToken -Username $username -Password $plainPassword
    
    # Check if token retrieval was successful
    if ($JWT_TOKEN) {
        Write-Host "Successfully retrieved JWT token" -ForegroundColor Green
        Write-Host "Token: $JWT_TOKEN" -ForegroundColor Cyan
        
        # Set as environment variable for the current session
        $env:JWT_TOKEN = $JWT_TOKEN
        
        # Also create a global variable for easier access in PowerShell
        $global:JWT_TOKEN = $JWT_TOKEN
        
        Write-Host ""
        Write-Host "Token stored in:" -ForegroundColor Yellow
        Write-Host "  - Environment variable: `$env:JWT_TOKEN" -ForegroundColor Gray
        Write-Host "  - Global variable: `$global:JWT_TOKEN" -ForegroundColor Gray
        Write-Host ""
        
        # Now prompt for domain name lookup
        Write-Host "=== Domain Lookup ===" -ForegroundColor Cyan
        $domainName = Read-Host "Enter domain name to check"
        
        if ([string]::IsNullOrWhiteSpace($domainName)) {
            Write-Host "No domain name provided. Skipping domain lookup." -ForegroundColor Yellow
        }
        else {
            Write-Host ""
            $domainResult = Check-DomainFeed -DomainName $domainName -JwtToken $JWT_TOKEN
        }
    }
    else {
        Write-Host "Failed to retrieve JWT token" -ForegroundColor Red
        Write-Host "Press any key to continue..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}
catch {
    Write-Host "Script execution failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Press any key to continue..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Keep the window open at the end
Write-Host ""
Write-Host "Script completed. Press any key to exit..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
