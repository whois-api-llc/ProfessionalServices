#!/usr/bin/env python3
import requests
import json
import sys
import argparse

def query_dns_history(domain_name, api_key="<YOUR_API_KEY>"):
    """
    Query DNS history for a given domain using WhoisXML API
    
    Args:
        domain_name (str): The domain to query
        api_key (str): API key for WhoisXML API
    
    Returns:
        dict: API response as JSON
    """
    
    url = "https://dns-history.whoisxmlapi.com/api/v1"
    
    payload = {
        "apiKey": api_key,
        "searchType": "forward",
        "recordType": "a",
        "domainName": domain_name
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Query DNS history for a domain")
    parser.add_argument("domain", help="Domain name to query (e.g., example.com)")
    parser.add_argument("--api-key", default="<YOUR_API_KEY>", 
                       help="API key for WhoisXML API")
    parser.add_argument("--pretty", action="store_true", 
                       help="Pretty print JSON output")
    
    args = parser.parse_args()
    
    print(f"Querying DNS history for: {args.domain}")
    
    result = query_dns_history(args.domain, args.api_key)
    
    if result is not None:
        if args.pretty:
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result))
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
