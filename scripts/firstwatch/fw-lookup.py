#!/usr/bin/env python3
# Python script to extract JWT token from login API and lookup a domain name entered by the user.
# (C)2025 WHOISXMLAPI.COM
# This script will prompt you to enter your username and password which then will generate a JWT token 
# for subsquent API lookups.
#

import requests
import json
import getpass
import sys
from typing import Optional, Dict, Any

def get_jwt_token(username: str, password: str, api_url: str = "https://firstwatch.yatic.io/api/login") -> Optional[str]:
    """
    Extract JWT token from login API
    
    Args:
        username: User's username
        password: User's password
        api_url: Login API endpoint
        
    Returns:
        JWT token string or None if failed
    """
    try:
        # Create the form data
        data = {
            'username': username,
            'password': password
        }
        
        # Make the login request
        print("Attempting to login and retrieve JWT token...")
        print(f"API URL: {api_url}")
        
        response = requests.post(
            api_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        response_data = response.json()
        
        # Debug: Show the raw response
        print("Raw API Response:")
        print(json.dumps(response_data, indent=2))
        
        # Extract JWT token from response
        # Try common token field names
        token_fields = ['token', 'access_token', 'jwt', 'authToken', 'accessToken', 'bearer']
        jwt_token = None
        
        for field in token_fields:
            if field in response_data and response_data[field]:
                jwt_token = response_data[field]
                break
        
        # Check if token was found
        if not jwt_token:
            print("ERROR: JWT token not found in response")
            print(f"Response was: {json.dumps(response_data, indent=2)}")
            return None
        
        return jwt_token
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to make API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return None

def check_domain_feed(domain_name: str, jwt_token: str, api_url: str = "http://firstwatch.yatic.io/api/feed/check") -> Optional[Dict[Any, Any]]:
    """
    Check domain feed using JWT token
    
    Args:
        domain_name: Domain to check
        jwt_token: JWT token for authentication
        api_url: Domain check API endpoint
        
    Returns:
        Response data dictionary or None if failed
    """
    try:
        # Create headers with the JWT token
        headers = {
            'Authorization': f'Bearer {jwt_token}'
        }
        
        # Build the API URL with the domain name
        feed_check_url = f"{api_url}/{domain_name}"
        print(f"Checking domain: {domain_name}")
        print(f"API URL: {feed_check_url}")
        
        # Make the domain check API call
        response = requests.get(feed_check_url, headers=headers)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        domain_response = response.json()
        
        # Display the domain check results
        print("\n=== Domain Check Results ===")
        print(json.dumps(domain_response, indent=2))
        
        return domain_response
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to check domain: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return None

def main():
    """Main execution function"""
    try:
        # Prompt for username and password
        print("=== JWT Token Login ===")
        print()
        
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        
        print()
        
        # Get the JWT token
        jwt_token = get_jwt_token(username, password)
        
        # Check if token retrieval was successful
        if jwt_token:
            print("Successfully retrieved JWT token")
            print(f"Token: {jwt_token}")
            
            print()
            print("Token stored in local variable for this session")
            print()
            
            # Now prompt for domain name lookup
            print("=== Domain Lookup ===")
            domain_name = input("Enter domain name to check: ")
            
            if not domain_name.strip():
                print("No domain name provided. Skipping domain lookup.")
            else:
                print()
                domain_result = check_domain_feed(domain_name.strip(), jwt_token)
                
                if domain_result:
                    print("\nDomain check completed successfully!")
                else:
                    print("\nDomain check failed!")
        else:
            print("Failed to retrieve JWT token")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Script execution failed: {e}")
        sys.exit(1)
    
    # Keep the script running briefly
    print()
    input("Script completed. Press Enter to exit...")

if __name__ == "__main__":
    main()
