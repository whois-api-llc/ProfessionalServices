#!/usr/bin/env python3
"""
Test MX Record Detection
Demonstrates the MX record checking functionality
WHOISXMLAPI.COM
"""

import dns.resolver

def test_mx_records():
    """Test MX record detection for various domains"""
    
    print("=" * 60)
    print("MX Record Detection Test")
    print("=" * 60)
    
    # Test domains - mix of domains with and without MX records
    test_domains = [
        "google.com",       # Has MX records
        "gmail.com",        # Has MX records (Google)
        "example.com",      # May or may not have MX
        "github.com",       # Has MX records
        "cloudflare.com",   # Has MX records
        "wikipedia.org",    # Has MX records
    ]
    
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5
    
    for domain in test_domains:
        print(f"\nChecking {domain}:")
        
        # Check for MX records
        mx_records = []
        try:
            mx_results = resolver.resolve(domain, 'MX')
            for rdata in mx_results:
                mx_records.append({
                    'priority': rdata.preference,
                    'exchange': str(rdata.exchange),
                    'full': f"{rdata.preference}:{rdata.exchange}"
                })
            
            print(f"  ✓ Has MX records ({len(mx_records)} found)")
            print(f"  📧 Email capable: Yes")
            
            # Show first 3 MX records
            for i, mx in enumerate(mx_records[:3]):
                print(f"     {i+1}. Priority {mx['priority']}: {mx['exchange']}")
            
            if len(mx_records) > 3:
                print(f"     ... and {len(mx_records)-3} more")
                
        except dns.resolver.NXDOMAIN:
            print(f"  ✗ Domain does not exist")
            
        except dns.resolver.NoAnswer:
            print(f"  ✗ No MX records found")
            print(f"  📧 Email capable: No")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("MX Record Analysis Summary")
    print("=" * 60)
    print("\nWhy MX records matter for categorization:")
    print("1. Legitimate businesses usually have MX records")
    print("2. Phishing sites often lack proper email setup")
    print("3. Parked domains typically have no MX records")
    print("4. Email capability indicates operational domain")
    
    print("\nSecurity implications:")
    print("• Domain with MX = Can receive email responses")
    print("• No MX records = Cannot receive email, possibly suspicious")
    print("• MX to unusual servers = Potential red flag")


def check_specific_domain():
    """Interactive domain MX check"""
    
    print("\n" + "=" * 60)
    print("Interactive MX Record Check")
    print("=" * 60)
    
    domain = input("\nEnter a domain to check (or press Enter to skip): ").strip()
    
    if not domain:
        return
    
    # Clean domain
    domain = domain.replace('http://', '').replace('https://', '').split('/')[0]
    
    print(f"\nChecking MX records for: {domain}")
    
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    
    try:
        # Check MX records
        mx_results = resolver.resolve(domain, 'MX')
        mx_records = []
        
        for rdata in mx_results:
            mx_records.append({
                'priority': rdata.preference,
                'exchange': str(rdata.exchange),
            })
        
        # Sort by priority (lower = higher priority)
        mx_records.sort(key=lambda x: x['priority'])
        
        print(f"\n✓ Found {len(mx_records)} MX record(s):")
        print("-" * 40)
        
        for i, mx in enumerate(mx_records):
            print(f"{i+1}. Priority {mx['priority']:3d}: {mx['exchange']}")
        
        print("-" * 40)
        print(f"✓ {domain} can receive email")
        
        # Additional analysis
        print("\nAnalysis:")
        
        # Check if using common email providers
        common_providers = {
            'google': 'Google Workspace',
            'outlook': 'Microsoft 365',
            'zoho': 'Zoho Mail',
            'mxrecord.io': 'MXrecord.io',
            'secureserver': 'GoDaddy',
            'pphosted': 'Proofpoint',
            'messagelabs': 'Symantec',
        }
        
        for mx in mx_records:
            exchange_lower = mx['exchange'].lower()
            for provider, name in common_providers.items():
                if provider in exchange_lower:
                    print(f"  • Using {name} for email")
                    break
        
        # Check for suspicious patterns
        if len(mx_records) > 10:
            print("  ⚠ Unusually high number of MX records")
        
        if all(mx['priority'] == mx_records[0]['priority'] for mx in mx_records):
            print("  ℹ All MX records have same priority (load balancing)")
            
    except dns.resolver.NXDOMAIN:
        print(f"\n✗ Domain '{domain}' does not exist")
        
    except dns.resolver.NoAnswer:
        print(f"\n✗ No MX records found for {domain}")
        print(f"✗ {domain} cannot receive email")
        print("\nPossible reasons:")
        print("  • Domain doesn't use email")
        print("  • Website-only domain")
        print("  • Parked or inactive domain")
        print("  • Newly registered (DNS not configured)")
        
    except Exception as e:
        print(f"\n✗ Error checking MX records: {e}")


if __name__ == "__main__":
    # Run automatic test
    test_mx_records()
    
    # Interactive check
    check_specific_domain()
    
    print("\n✓ Test complete!")
