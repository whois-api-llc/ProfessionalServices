#!/usr/bin/env python3
# Python script to extract JWT token from login API and lookup domain names from CSV file.
# (C)2025 WHOISXMLAPI.COM
# This script reads credentials from firstwatch.conf, processes domains from CSV file,
# and outputs results to a specified file.
#
# Create sample configuration file
#    python script.py --create-config
# Run with default config file
#   python script.py domains.csv results.csv
# Run with custom config file  
#   python script.py -c myconfig.conf domains.csv results.csv

import requests
import json
import sys
import csv
import argparse
import configparser
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import time

def load_config(config_file: str = "firstwatch.conf") -> Dict[str, str]:
    """
    Load configuration from file
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Dictionary with configuration values
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found")
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Check if required sections exist
    if 'credentials' not in config:
        raise ValueError("Missing 'credentials' section in configuration file")
    
    credentials = config['credentials']
    required_fields = ['username', 'password']
    
    for field in required_fields:
        if field not in credentials:
            raise ValueError(f"Missing '{field}' in credentials section")
    
    # Optional API URLs with defaults
    result = {
        'username': credentials['username'],
        'password': credentials['password'],
        'login_url': 'https://firstwatch.yatic.io/api/login',
        'domain_check_url': 'http://firstwatch.yatic.io/api/feed/check',
        'delay': 1.0
    }
    
    # Override with API section values if they exist
    if 'api' in config:
        api_config = config['api']
        if 'login_url' in api_config:
            result['login_url'] = api_config['login_url']
        if 'domain_check_url' in api_config:
            result['domain_check_url'] = api_config['domain_check_url']
        if 'delay' in api_config:
            result['delay'] = float(api_config['delay'])
    
    return result

def load_domains_from_csv(csv_file: str) -> List[str]:
    """
    Load domain names from CSV file (single column)
    
    Args:
        csv_file: Path to CSV file with domain names
        
    Returns:
        List of domain names
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file '{csv_file}' not found")
    
    domains = []
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            
            # Skip header row if it looks like a header
            first_row = next(csv_reader, None)
            if first_row and not first_row[0].strip().replace('.', '').replace('-', '').isalnum():
                # If first row doesn't look like a domain, treat it as header
                pass
            else:
                # First row looks like a domain, include it
                if first_row:
                    domain = first_row[0].strip()
                    if domain:
                        domains.append(domain)
            
            # Read remaining rows
            for row in csv_reader:
                if row:  # Skip empty rows
                    domain = row[0].strip()
                    if domain:
                        domains.append(domain)
    
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")
    
    return domains

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
        
        print("Successfully retrieved JWT token")
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
        
        # Make the domain check API call
        response = requests.get(feed_check_url, headers=headers)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        domain_response = response.json()
        
        return domain_response
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to check domain '{domain_name}': {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON response for '{domain_name}': {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error checking '{domain_name}': {e}")
        return None

def write_results_header(output_file):
    """Write CSV header for results"""
    output_file.write("timestamp,domain,status,response\n")

def write_result_to_file(output_file, domain: str, result: Optional[Dict[Any, Any]], status: str):
    """
    Write a single result to the output file
    
    Args:
        output_file: Open file handle
        domain: Domain name that was checked
        result: API response dictionary or None
        status: Status string (success/failed)
    """
    timestamp = datetime.now().isoformat()
    
    # Escape the JSON response for CSV
    if result:
        response_json = json.dumps(result).replace('"', '""')
    else:
        response_json = ""
    
    # Write CSV row
    output_file.write(f'"{timestamp}","{domain}","{status}","{response_json}"\n')
    output_file.flush()  # Ensure data is written immediately

def process_domains(domains: List[str], jwt_token: str, config: Dict[str, str], output_file) -> Dict[str, int]:
    """
    Process all domains and write results to file
    
    Args:
        domains: List of domain names to check
        jwt_token: JWT authentication token
        config: Configuration dictionary
        output_file: Open file handle for output
        
    Returns:
        Dictionary with processing statistics
    """
    stats = {'total': len(domains), 'success': 0, 'failed': 0}
    delay = config.get('delay', 1.0)
    domain_check_url = config.get('domain_check_url')
    
    print(f"\nProcessing {stats['total']} domains...")
    print(f"Delay between requests: {delay} seconds")
    print("=" * 50)
    
    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{stats['total']}] Checking: {domain}")
        
        # Check the domain
        result = check_domain_feed(domain, jwt_token, domain_check_url)
        
        if result:
            stats['success'] += 1
            status = "success"
            print(f"✓ Success")
        else:
            stats['failed'] += 1
            status = "failed"
            print(f"✗ Failed")
        
        # Write result to file
        write_result_to_file(output_file, domain, result, status)
        
        # Add delay between requests (except for the last one)
        if i < stats['total'] and delay > 0:
            time.sleep(delay)
    
    return stats

def create_sample_config():
    """Create a sample configuration file"""
    sample_config = """# FirstWatch API Configuration File
# Copy this file to firstwatch.conf and update with your credentials

[credentials]
username = your_username_here
password = your_password_here

[api]
# Optional: Override default API URLs
# login_url = https://firstwatch.yatic.io/api/login
# domain_check_url = http://firstwatch.yatic.io/api/feed/check

# Optional: Delay between API requests (seconds) to avoid rate limiting
# delay = 1.0
"""
    
    with open("firstwatch.conf.sample", "w") as f:
        f.write(sample_config)
    
    print("Sample configuration file created: firstwatch.conf.sample")
    print("Copy it to firstwatch.conf and update with your credentials.")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Batch domain lookup tool using FirstWatch API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s domains.csv results.csv
  %(prog)s -c myconfig.conf domains.csv results.csv
  %(prog)s --create-config
        """
    )
    
    parser.add_argument(
        'csv_file', 
        nargs='?',
        help='CSV file containing domain names (single column)'
    )
    
    parser.add_argument(
        'output_file',
        nargs='?', 
        help='Output file for results'
    )
    
    parser.add_argument(
        '-c', '--config',
        default='firstwatch.conf',
        help='Configuration file (default: firstwatch.conf)'
    )
    
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create a sample configuration file'
    )
    
    args = parser.parse_args()
    
    # Handle create-config option
    if args.create_config:
        create_sample_config()
        return
    
    # Validate required arguments
    if not args.csv_file or not args.output_file:
        parser.error("Both csv_file and output_file are required (unless using --create-config)")
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config(args.config)
        print(f"Configuration loaded from: {args.config}")
        
        # Load domains from CSV
        print(f"Loading domains from: {args.csv_file}")
        domains = load_domains_from_csv(args.csv_file)
        print(f"Loaded {len(domains)} domains")
        
        if not domains:
            print("ERROR: No domains found in CSV file")
            sys.exit(1)
        
        # Get JWT token
        jwt_token = get_jwt_token(
            config['username'], 
            config['password'], 
            config['login_url']
        )
        
        if not jwt_token:
            print("ERROR: Failed to retrieve JWT token")
            sys.exit(1)
        
        # Open output file and process domains
        with open(args.output_file, 'w', newline='', encoding='utf-8') as output_file:
            # Write header
            write_results_header(output_file)
            
            # Process all domains
            stats = process_domains(domains, jwt_token, config, output_file)
            
            # Print final statistics
            print("\n" + "=" * 50)
            print("PROCESSING COMPLETE")
            print(f"Total domains: {stats['total']}")
            print(f"Successful: {stats['success']}")
            print(f"Failed: {stats['failed']}")
            print(f"Success rate: {stats['success']/stats['total']*100:.1f}%")
            print(f"Results written to: {args.output_file}")
        
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Script execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
