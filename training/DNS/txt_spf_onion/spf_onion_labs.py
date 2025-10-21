#!/usr/bin/env python3
"""
SPF ONION DETECTION LABS - COMPLETE WORKING VERSION
====================================================
This version has all functions fully implemented and ready to run.

Provided by: 
    WHOIS API, Inc.   www.whoisxmlapi.com
    Product: DNS Database

      Developers: 
         ed.gibbs@whoisxmlapi.com
         alex.ronquillo@whoisxmlapi.com, VP of Products
      Contributing authors of the original paper, "The SPF Onion"
         URL: https://main.whoisxmlapi.com/blog/the-spf-onion-enter-the-world-of-spf-chaos
         ed.gibbs@whoisxmlpapi.com
         jeff@vogelogic.com, Jeff Vogelpohl

Quick Start:
    python -i spf_labs_working.py
    
    >>> stats = identify_candidates('txt_database.csv', 'candidates.csv')
    >>> print(stats)

For millions of DNS TXT records, Phase 1 takes 3-5 minutes.
"""

import csv
import re
import time
from typing import List, Dict, Set, Tuple, Generator
from collections import defaultdict, Counter
from datetime import datetime

# Optional: progress bars
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Optional: DNS lookups for Lab 2
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("Note: Install dnspython for Lab 2: pip install dnspython")

# ==============================================================================
# LAB 1: FAST SCAN - FULLY IMPLEMENTED
# ==============================================================================

def stream_spf_records(csv_file: str) -> Generator[Dict, None, None]:
    """
    Stream SPF records from large CSV file without loading all into memory.
    
    Args:
        csv_file: Path to CSV file with columns: d, du, txt
        
    Yields:
        Dictionary with domain, timestamp, and SPF record
    """
    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            txt = row['txt'].strip()
            if txt.startswith('v=spf1'):
                yield {
                    'domain': row['d'],
                    'timestamp': row.get('du', ''),
                    'spf_record': txt
                }


def quick_parse_spf(spf_record: str) -> Dict[str, int]:
    """
    Fast mechanism counter - NO DNS lookups, just counting!
    
    Args:
        spf_record: SPF record string
        
    Returns:
        Dictionary with counts of each mechanism type
    """
    counts = {
        'ip4': len(re.findall(r'ip4:', spf_record)),
        'ip6': len(re.findall(r'ip6:', spf_record)),
        'include': len(re.findall(r'include:', spf_record)),
        'a': len(re.findall(r'\sa\s|^a\s|^a:|^a$|\sa$', spf_record)),
        'mx': len(re.findall(r'\smx\s|^mx\s|^mx:|^mx$|\smx$', spf_record)),
        'ptr': len(re.findall(r'ptr:', spf_record)),
        'exists': len(re.findall(r'exists:', spf_record)),
        'redirect': len(re.findall(r'redirect=', spf_record)),
    }
    return counts


def is_suspicious_domain(domain: str, spf_record: str) -> Tuple[bool, List[str]]:
    """
    Check if domain/SPF record uses suspicious patterns.
    
    Args:
        domain: Domain name
        spf_record: SPF record content
        
    Returns:
        Tuple of (is_suspicious, list_of_reasons)
    """
    reasons = []
    
    # Suspicious free DNS services
    suspicious_services = [
        'dynu.net', 'dynu.com', 'ddns.net', 'ddnsfree.com', 'ddnsgeek.com',
        'freeddns.org', 'accesscam.org', 'casacam.net', 'duckdns.org',
        'giize.com', 'gleeze.com', 'kozow.com', 'cloudns.', 
        'noip.com', 'dyndns.org', 'freedns.afraid.org'
    ]
    
    # Commonly abused TLDs
    abused_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.pw']
    
    # Check domain and SPF content
    content = (domain + ' ' + spf_record).lower()
    
    for service in suspicious_services:
        if service in content:
            reasons.append(f'uses_{service.split(".")[0]}')
            break  # Only flag once
    
    for tld in abused_tlds:
        if tld in content:
            reasons.append(f'abused_tld_{tld[1:]}')
            break  # Only flag once
    
    # Check subdomain depth (e.g., a.b.c.d.e.f.example.com)
    if domain.count('.') > 5:
        reasons.append('deep_subdomain')
    
    return len(reasons) > 0, reasons


def identify_candidates(csv_file: str, output_file: str = 'candidates.csv') -> Dict:
    """
    Phase 1: Fast scan through ALL records to identify candidates.
    
    Args:
        csv_file: Input CSV with millions of records
        output_file: Output CSV with filtered candidates
        
    Returns:
        Statistics dictionary
    """
    stats = {
        'total_records': 0,
        'spf_records': 0,
        'candidates': 0,
        'processing_time': 0,
        'reasons': Counter()
    }
    
    start_time = time.time()
    candidates = []
    
    print(f"\n{'='*70}")
    print("PHASE 1: FAST SCAN - Identifying Candidates")
    print(f"{'='*70}\n")
    print("Scanning dataset for interesting SPF records...")
    print("(This may take 3-5 minutes for millions of DNS TXT records)\n")
    
    # Stream through records
    record_iter = stream_spf_records(csv_file)
    if TQDM_AVAILABLE:
        record_iter = tqdm(record_iter, desc="Scanning", unit=" SPF records")
    
    for record in record_iter:
        stats['total_records'] += 1
        stats['spf_records'] += 1
        
        # Quick parse
        counts = quick_parse_spf(record['spf_record'])
        
        # Apply filtering criteria
        reasons = []
        
        # Many includes (complex chains)
        if counts['include'] >= 5:
            reasons.append('many_includes')
        
        # Many total mechanisms
        total_mechanisms = sum(counts.values())
        if total_mechanisms >= 10:
            reasons.append('many_mechanisms')
        
        # Deprecated ptr
        if counts['ptr'] > 0:
            reasons.append('deprecated_ptr')
        
        # Unusual redirect count
        if counts['redirect'] >= 2:
            reasons.append('many_redirects')
        
        # Many exists (unusual)
        if counts['exists'] >= 3:
            reasons.append('many_exists')
        
        # Suspicious domains
        is_susp, susp_reasons = is_suspicious_domain(record['domain'], record['spf_record'])
        if is_susp:
            reasons.append('suspicious_domain')
            reasons.extend(susp_reasons)
        
        # If any criteria met, save as candidate
        if reasons:
            stats['candidates'] += 1
            for reason in reasons:
                stats['reasons'][reason] += 1
            
            candidates.append({
                'domain': record['domain'],
                'spf_record': record['spf_record'],
                'reasons': ','.join(reasons),
                **counts
            })
    
    # Write candidates to file
    if candidates:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=candidates[0].keys())
            writer.writeheader()
            writer.writerows(candidates)
    
    stats['processing_time'] = time.time() - start_time
    
    return stats


def generate_phase1_report(stats: Dict):
    """Generate summary report of Phase 1 scanning."""
    print(f"\n{'='*70}")
    print("PHASE 1: SCAN RESULTS")
    print(f"{'='*70}\n")
    
    print(f"Records processed: {stats['total_records']:,}")
    print(f"SPF records found: {stats['spf_records']:,} ({stats['spf_records']/max(stats['total_records'],1)*100:.1f}%)")
    print(f"Candidates identified: {stats['candidates']:,} ({stats['candidates']/max(stats['spf_records'],1)*100:.1f}% of SPF)")
    print(f"Processing time: {stats['processing_time']:.1f} seconds ({stats['processing_time']/60:.1f} minutes)")
    
    if stats['total_records'] > 0:
        rate = stats['total_records'] / stats['processing_time']
        print(f"Processing rate: {rate:,.0f} records/second")
    
    print(f"\nTop reasons for flagging:")
    for reason, count in stats['reasons'].most_common(10):
        pct = count / max(stats['candidates'], 1) * 100
        print(f"  {reason:25s}: {count:5,} ({pct:5.1f}%)")
    
    print(f"\n{'='*70}\n")


# ==============================================================================
# LAB 2: DEEP ANALYSIS - FULLY IMPLEMENTED
# ==============================================================================

class CachedDNSResolver:
    """DNS resolver with caching to avoid duplicate lookups."""
    
    def __init__(self, timeout: float = 2.0):
        self.cache = {}
        self.hits = 0
        self.misses = 0
        
        if DNS_AVAILABLE:
            self.resolver = dns.resolver.Resolver()
            self.resolver.timeout = timeout
            self.resolver.lifetime = timeout
        else:
            self.resolver = None
    
    def query_spf(self, domain: str) -> str:
        """Query SPF record with caching."""
        if domain in self.cache:
            self.hits += 1
            return self.cache[domain]
        
        self.misses += 1
        
        if not DNS_AVAILABLE:
            self.cache[domain] = ""
            return ""
        
        try:
            answers = self.resolver.resolve(domain, 'TXT')
            for rdata in answers:
                txt_string = b''.join(rdata.strings).decode('utf-8')
                if txt_string.startswith('v=spf1'):
                    self.cache[domain] = txt_string
                    return txt_string
        except Exception:
            pass
        
        self.cache[domain] = ""
        return ""
    
    def get_stats(self) -> Dict:
        """Return cache statistics."""
        total = self.hits + self.misses
        return {
            'cache_size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total if total > 0 else 0
        }


def count_dns_lookups(domain: str, spf_record: str, 
                     resolver: CachedDNSResolver,
                     visited: Set[str] = None,
                     depth: int = 0, 
                     max_depth: int = 20) -> Tuple[int, List[str]]:
    """
    Recursively count DNS lookups in an SPF record chain.
    
    Args:
        domain: Domain being analyzed
        spf_record: SPF record to analyze
        resolver: Cached DNS resolver
        visited: Set of visited domains (circular reference detection)
        depth: Current recursion depth
        max_depth: Maximum recursion depth
        
    Returns:
        Tuple of (lookup_count, warnings)
    """
    if visited is None:
        visited = set()
    
    warnings = []
    lookup_count = 0
    
    # Check for circular reference
    if domain in visited:
        warnings.append(f"Circular reference: {domain}")
        return 0, warnings
    
    # Check max depth
    if depth > max_depth:
        warnings.append(f"Maximum depth exceeded at {domain}")
        return lookup_count, warnings
    
    visited.add(domain)
    
    # Parse mechanisms
    counts = quick_parse_spf(spf_record)
    
    # Count lookups for simple mechanisms (1 lookup each)
    lookup_count += counts['a']
    lookup_count += counts['mx']
    lookup_count += counts['ptr']
    lookup_count += counts['exists']
    
    # Handle includes (1 lookup + recursive count)
    includes = re.findall(r'include:([^\s]+)', spf_record)
    for include_domain in includes:
        lookup_count += 1  # The include itself
        
        # Query the included domain
        included_spf = resolver.query_spf(include_domain)
        if included_spf:
            recursive_count, recursive_warnings = count_dns_lookups(
                include_domain, included_spf, resolver, visited, depth + 1, max_depth
            )
            lookup_count += recursive_count
            warnings.extend(recursive_warnings)
    
    # Handle redirects (1 lookup + recursive count)
    redirects = re.findall(r'redirect=([^\s]+)', spf_record)
    for redirect_domain in redirects:
        lookup_count += 1  # The redirect itself
        
        redirected_spf = resolver.query_spf(redirect_domain)
        if redirected_spf:
            recursive_count, recursive_warnings = count_dns_lookups(
                redirect_domain, redirected_spf, resolver, visited, depth + 1, max_depth
            )
            lookup_count += recursive_count
            warnings.extend(recursive_warnings)
    
    return lookup_count, warnings


def find_violations(candidates_file: str) -> List[Dict]:
    """
    Phase 2: Deep analysis to find actual RFC 7208 violations.
    
    Args:
        candidates_file: CSV file with candidates from Phase 1
        
    Returns:
        List of violations with details
    """
    print(f"\n{'='*70}")
    print("PHASE 2: DEEP ANALYSIS - DNS Lookups on Candidates")
    print(f"{'='*70}\n")
    
    if not DNS_AVAILABLE:
        print("⚠ dnspython not installed - skipping DNS lookups")
        print("  Install with: pip install dnspython")
        return []
    
    violations = []
    resolver = CachedDNSResolver()
    
    # Load candidates
    candidates = []
    with open(candidates_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        candidates = list(reader)
    
    print(f"Analyzing {len(candidates)} candidates...")
    print("(This may take 10-15 minutes with DNS lookups)\n")
    
    # Analyze each candidate
    candidate_iter = candidates
    if TQDM_AVAILABLE:
        candidate_iter = tqdm(candidates, desc="Analyzing", unit=" domains")
    
    for candidate in candidate_iter:
        domain = candidate['domain']
        spf_record = candidate['spf_record']
        
        # Count DNS lookups recursively
        lookup_count, warnings = count_dns_lookups(
            domain, spf_record, resolver
        )
        
        # Check if violates RFC 7208 (>10 lookups)
        if lookup_count > 10:
            violations.append({
                'domain': domain,
                'lookup_count': lookup_count,
                'exceeds_limit': True,
                'warnings': warnings,
                'spf_record': spf_record[:200]  # Truncate for display
            })
    
    # Show cache stats
    cache_stats = resolver.get_stats()
    print(f"\nDNS Cache Performance:")
    print(f"  Unique domains queried: {cache_stats['cache_size']}")
    print(f"  Cache hits: {cache_stats['hits']:,}")
    print(f"  Cache misses: {cache_stats['misses']:,}")
    print(f"  Hit rate: {cache_stats['hit_rate']*100:.1f}%")
    
    print(f"\n{'='*70}")
    print(f"VIOLATIONS FOUND: {len(violations)} domains exceed 10 DNS lookups")
    print(f"{'='*70}\n")
    
    return violations


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def load_stats_from_candidates(candidates_file: str) -> Dict:
    """
    Reconstruct basic stats from candidates file.
    Useful if you ran Phase 1 in a previous session.
    """
    try:
        with open(candidates_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            candidates = list(reader)
        
        return {
            'total_records': 0,  # Unknown
            'spf_records': 0,    # Unknown
            'candidates': len(candidates),
            'processing_time': 0
        }
    except FileNotFoundError:
        return {
            'total_records': 0,
            'spf_records': 0,
            'candidates': 0,
            'processing_time': 0
        }


# ==============================================================================
# LAB 3: REPORTING - FULLY IMPLEMENTED
# ==============================================================================

def generate_executive_report(violations: List[Dict], stats: Dict = None):
    """Generate executive summary for leadership."""
    print(f"\n{'='*70}")
    print("EXECUTIVE SUMMARY: SPF ONION ANALYSIS")
    print(f"{'='*70}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    if stats:
        print(f"Dataset Overview:")
        print(f"  Records Analyzed: {stats['total_records']:,}")
        print(f"  SPF Records: {stats['spf_records']:,}")
        print(f"  Candidates Investigated: {stats['candidates']:,}")
        print(f"  RFC Violations Found: {len(violations):,}\n")
    else:
        print(f"Analysis Overview:")
        print(f"  RFC Violations Found: {len(violations):,}")
        print(f"  (Run Phase 1 to see full statistics)\n")
    
    if violations:
        print(f"Severity Breakdown:")
        critical = sum(1 for v in violations if v['lookup_count'] > 15)
        high = sum(1 for v in violations if 13 <= v['lookup_count'] <= 15)
        medium = sum(1 for v in violations if 11 <= v['lookup_count'] <= 12)
        
        print(f"  Critical (>15 lookups): {critical}")
        print(f"  High (13-15 lookups): {high}")
        print(f"  Medium (11-12 lookups): {medium}\n")
        
        print(f"Top 10 Worst Offenders:")
        sorted_violations = sorted(violations, key=lambda x: x['lookup_count'], reverse=True)
        for i, v in enumerate(sorted_violations[:10], 1):
            print(f"  {i:2d}. {v['domain']:50s} - {v['lookup_count']} lookups")
    
    print(f"\n{'='*70}\n")


def generate_technical_report(violations: List[Dict], output_file: str = 'technical_report.txt'):
    """Generate detailed technical report."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("SPF ONION DETECTION - TECHNICAL REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"VIOLATIONS FOUND: {len(violations)}\n\n")
        
        for i, v in enumerate(violations, 1):
            f.write(f"\n{'-'*70}\n")
            f.write(f"VIOLATION #{i}\n")
            f.write(f"{'-'*70}\n")
            f.write(f"Domain: {v['domain']}\n")
            f.write(f"DNS Lookups: {v['lookup_count']} (RFC 7208 limit: 10)\n")
            f.write(f"SPF Record: {v['spf_record']}\n")
            
            if v['warnings']:
                f.write(f"\nWarnings:\n")
                for warning in v['warnings']:
                    f.write(f"  - {warning}\n")
            
            f.write(f"\nRecommendations:\n")
            f.write(f"  - Flatten SPF record to reduce includes\n")
            f.write(f"  - Use subdomains for different mail services\n")
            f.write(f"  - Consolidate third-party services\n")
    
    print(f"\n✓ Technical report saved to: {output_file}")


# ==============================================================================
# QUICK TEST / DEMO FUNCTIONS
# ==============================================================================

def quick_test(csv_file: str, num_records: int = 10):
    """Quick test to verify file is readable."""
    print(f"\nQuick Test: Reading first {num_records} SPF records...\n")
    
    count = 0
    for record in stream_spf_records(csv_file):
        print(f"{count+1}. {record['domain']}")
        print(f"   SPF: {record['spf_record'][:80]}...")
        counts = quick_parse_spf(record['spf_record'])
        print(f"   Mechanisms: {sum(counts.values())} total, {counts['include']} includes")
        print()
        
        count += 1
        if count >= num_records:
            break
    
    print(f"✓ Successfully read {count} SPF records!")


def run_full_analysis(csv_file: str):
    """Run complete analysis pipeline."""
    print("\n" + "="*70)
    print("SPF ONION DETECTION - FULL ANALYSIS")
    print("="*70)
    
    # Phase 1
    stats = identify_candidates(csv_file, 'candidates.csv')
    generate_phase1_report(stats)
    
    if stats['candidates'] == 0:
        print("\n⚠ No candidates found - nothing to analyze in Phase 2")
        return
    
    # Phase 2
    violations = find_violations('candidates.csv')
    
    # Phase 3
    if violations:
        generate_executive_report(violations, stats)
        generate_technical_report(violations)
    else:
        print("\n✓ No RFC 7208 violations found!")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE!")
    print("="*70)
    print("\nGenerated files:")
    print("  - candidates.csv (Phase 1 results)")
    if violations:
        print("  - technical_report.txt (Phase 2 detailed findings)")
    print()


# ==============================================================================
# MAIN - FOR INTERACTIVE USE
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("SPF ONION LABS - Interactive Session")
    print("="*70)
    print("\nFunctions available:")
    print("  quick_test('your_file.csv')              - Test file reading")
    print("  identify_candidates(...)                  - Phase 1: Fast scan")
    print("  find_violations(...)                      - Phase 2: Deep analysis")
    print("  load_stats_from_candidates('file.csv')   - Reload stats if needed")
    print("  run_full_analysis('your_file.csv')        - Run everything")
    print("\nExample:")
    print("  >>> quick_test('txt_database.csv')")
    print("  >>> stats = identify_candidates('txt_database.csv', 'candidates.csv')")
    print("  >>> violations = find_violations('candidates.csv')")
    print("  >>> generate_executive_report(violations, stats)")
    print("\nIf you lost 'stats' variable:")
    print("  >>> stats = load_stats_from_candidates('candidates.csv')")
    print("  >>> generate_executive_report(violations, stats)")
    print("\nOr just omit stats:")
    print("  >>> generate_executive_report(violations)")
    print()
    
    # If file provided as argument, run quick test
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        print(f"Testing with file: {csv_file}\n")
        quick_test(csv_file, num_records=5)
