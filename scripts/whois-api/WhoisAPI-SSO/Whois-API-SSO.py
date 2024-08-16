# WHOISXMLAPI.COM
# Example of how to use the WHOIS API with Server-Side SSO
# Developed by MK, 08-16-2024 

import os
import sys
import requests
import base64
import json

# Configuration
oauth_token_url = 'https://main.whoisxmlapi.com/oauth/token'
whois_service = 'https://www.whoisxmlapi.com/whoisserver/WhoisService'

def print_ascii_art():
    art = """
        \033[96m
         _       ____          _     _  __ __  _____          ___    ____  ____
        | |     / / /_  ____  (_)___| |/ //  |/  / /         /   |  / __ \/  _/
        | | /| / / __ \/ __ \/ / ___/   // /|_/ / /         / /| | / /_/ // /  
        | |/ |/ / / / / /_/ / (__  )   |/ /  / / /___      / ___ |/ ____// /   
        |__/|__/_/ /_/\____/_/____/_/|_/_/  /_/_____/     /_/  |_/_/   /___/   
        \033[0m
    """
    print(art)

def print_readme():
    readme = """
        \033[93mWhois-SSO.py written by Professional.Services@whoisxmlapi.com
        =============================================================\033[0m

        This script is provided for demonstration purposes and uses live API credits. Use at your own risk.

        \033[92mInstructions:\033[0m
        -------------
        1. Ensure you have your API key set as an environment variable named 'WXAAPI'.
           - On Unix/Linux/MacOS: export WXAAPI="your_api_key_here"
           - On Windows: set WXAAPI=your_api_key_here

        2. Run the script with a domain name as the first argument, and optionally provide an `expiresIn` value as the second argument:
           The token's lifetime is \033[94m1800\033[0m (30 mins), \033[94m3600\033[0m (1 hour), \033[94m7200\033[0m (2 hours), or \033[94m10800\033[0m seconds (3 hours)

           \033[94mpython Whois-SSO.py <domain_name> [expiresIn]\033[0m

           Example:
           \033[94mpython Whois-SSO.py google.com\033[0m
           \033[94mpython Whois-SSO.py google.com 3600\033[0m

        3. The script will first obtain an access token, and then perform both GET and POST requests to the Whois API using the provided domain name.

        If no domain name is provided, this README message will be displayed.
    """
    print(readme)

def verbose_print(step, message):
    print(f"\033[97mStep {step}:\033[0m {message}")

# Step 1: Obtain an access token
def get_access_token(api_key, expires_in=7200):
    headers = {
        'Authorization': f'Bearer {base64.b64encode(api_key.encode()).decode()}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "grantType": "access_token",
        "expiresIn": expires_in
    }

    verbose_print(1, f"\033[93mRequesting access token from the OAuth endpoint with expiresIn={expires_in}.\033[0m")
    response = requests.post(oauth_token_url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    token_data = response.json()
    access_token = token_data.get("accessToken")
    verbose_print(1, f"\033[92mAccess Token received:\033[0m {access_token}\n")
    return access_token

# Step 2: Perform a GET request using the access token
def perform_get_request(access_token, domain_name):
    params = {
        'domainName': domain_name,
        'outputFormat': 'JSON'  # Add this parameter to ensure JSON response
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    verbose_print(2, f"\033[93mMaking GET request to WHOIS API for domain:\033[0m {domain_name}")
    print("\n\033[92mGET Request Example:\033[0m")
    print(f"\033[94mcurl --location 'https://www.whoisxmlapi.com/whoisserver/WhoisService?domainName={domain_name}&outputFormat=JSON' \\\n"
          f"--header 'Authorization: Bearer {access_token}' \033[0m\n")

    response = requests.get(whois_service, headers=headers, params=params)
    response.raise_for_status()

    return filter_whois_response(response.json())

# Step 3: Perform a POST request using the access token
def perform_post_request(access_token, domain_name):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    data = {
        "domainName": domain_name,
        'outputFormat': 'JSON'  # Include this parameter in the POST data if required by the API
    }

    verbose_print(3, f"\033[93mMaking POST request to WHOIS API for domain:\033[0m {domain_name}")
    print("\n\033[92mPOST Request Example:\033[0m")
    print(f"\033[94mcurl --location 'https://www.whoisxmlapi.com/whoisserver/WhoisService' \\\n"
          f"--header 'Content-Type: application/json' \\\n"
          f"--header 'Authorization: Bearer {access_token}' \\\n"
          f"--data '{json.dumps(data)}'\033[0m\n")

    response = requests.post(whois_service, headers=headers, data=json.dumps(data))
    response.raise_for_status()

    return filter_whois_response(response.json())

# Function to filter the WHOIS response to only include specific fields
def filter_whois_response(response):
    whois_record = response.get("WhoisRecord", {})
    filtered_response = {
        "domainName": whois_record.get("domainName"),
        "createdDate": whois_record.get("createdDate"),
        "expiresDate": whois_record.get("expiresDate"),
        "registrant": whois_record.get("registrant", {}).get("organization"),
        "nameServers": whois_record.get("nameServers", {}).get("hostNames", [])
    }
    return filtered_response

# Main script
if __name__ == '__main__':
    print_ascii_art()
    print_readme()
    
    if len(sys.argv) < 2:
        # No arguments provided, show the README
        print("\033[91mNo domain name provided. Exiting...\033[0m")
        sys.exit(0)
    else:
        try:
            verbose_print(0, "\033[93mStarting the SSO Demo Script\033[0m")

            # Read API key from environment variable
            api_key = os.getenv('WXAAPI')
            if not api_key:
                raise ValueError("\033[91mAPI key not found in environment variable 'WXAAPI'. Please set it before running the script.\033[0m")
            
            # Read the domain name and optional expiresIn value
            domain = sys.argv[1]
            expires_in = int(sys.argv[2]) if len(sys.argv) > 2 else 7200
            
            # Get access token
            token = get_access_token(api_key, expires_in)
            
            # GET request example
            get_response = perform_get_request(token, domain)
            
            if get_response:
                print("\033[92mGET Request Response:\033[0m")
                print(json.dumps(get_response, indent=4))
            else:
                print("\033[91mNo relevant data found or an error occurred.\033[0m")

            # POST request example
            post_response = perform_post_request(token, domain)
            
            if post_response:
                print("\033[92mPOST Request Response:\033[0m")
                print(json.dumps(post_response, indent=4))
            else:
                print("\033[91mNo relevant data found or an error occurred.\033[0m")
            
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"\033[91mAn error occurred:\033[0m {e}")
