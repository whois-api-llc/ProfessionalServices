#!/usr/bin/env python3
"""
KYC (Know Your Customer) Email Verification Tool

A refactored and optimized version of the WHOISXMLAPI KYC demonstration script.
Uses async/await for concurrent API calls, proper error handling, and modern Python practices.

Original by WHOISXMLAPI.COM - Refactored for production use.

Requirements:
    pip install aiohttp whoisapi subdomains-lookup domain-reputation dns-lookup-api
    pip install simple-geoip reverse-mx whois-history ip-netblocks requests

Usage:
    python kyc_refactored.py [email_address]
    
Environment Variables:
    WHOISXML_API_KEY: Your WHOISXMLAPI.com API key (required)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import quote

import aiohttp

# WHOISXMLAPI modules
import domainreputation as dr
import dnslookupapi as dns
import ipnetblocks as ipnb
import reversemx as rmx
import simple_geoip as geoip
import whoisapi as who
import whoishistory as whohist


# =============================================================================
# Configuration
# =============================================================================

class Config:
    """Centralized configuration management."""
    
    API_KEY: str = os.environ.get("WHOISXML_API_KEY", "")
    
    # API Endpoints
    EMAIL_VERIFICATION_URL = "https://emailverification.whoisxmlapi.com/api/v3"
    GEO_LOCATION_URL = "https://ip-geolocation.whoisxmlapi.com/api/v1"
    THREAT_INTEL_URL = "https://threat-intelligence.whoisxmlapi.com/api/v1"
    SSL_CERT_URL = "https://ssl-certificates.whoisxmlapi.com/api/v1"
    
    # Thresholds
    REPUTATION_SCORE_THRESHOLD = 72
    NEW_DOMAIN_DAYS_THRESHOLD = 30
    
    # Concurrency limits
    MAX_CONCURRENT_REQUESTS = 10
    REQUEST_TIMEOUT = 30
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.API_KEY:
            raise ConfigurationError(
                "API key not found. Set WHOISXML_API_KEY environment variable."
            )


# =============================================================================
# Custom Exceptions
# =============================================================================

class KYCError(Exception):
    """Base exception for KYC operations."""
    pass


class ConfigurationError(KYCError):
    """Raised when configuration is invalid."""
    pass


class APIError(KYCError):
    """Raised when an API call fails."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ValidationError(KYCError):
    """Raised when email validation fails."""
    pass


# =============================================================================
# Data Classes
# =============================================================================

class CheckStatus(Enum):
    """Status of various email checks."""
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class GeoLocation:
    """Geographic location data."""
    country: str = "Unknown"
    region: str = "Unknown"
    city: str = "Unknown"
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeoLocation:
        location = data.get("location", {})
        return cls(
            country=location.get("country", "Unknown"),
            region=location.get("region", "Unknown"),
            city=location.get("city", "Unknown"),
        )


@dataclass
class NetBlockInfo:
    """Network block information."""
    asn: int = 0
    name: str = "Unknown"


@dataclass
class ThreatIntelResult:
    """Threat intelligence data for an IOC."""
    value: str
    first_seen: str
    last_seen: str
    threat_type: str
    ioc_type: str


@dataclass
class SSLCertInfo:
    """SSL certificate information."""
    ip: str
    domain: str
    port: int
    chain_hierarchy: str
    validation_type: str
    valid_from: str
    valid_to: str
    subject_cn: str
    issuer_country: str
    organization: str
    netblock: NetBlockInfo


@dataclass
class EmailVerificationResult:
    """Results of email verification checks."""
    email_address: str
    format_check: CheckStatus = CheckStatus.UNKNOWN
    smtp_check: CheckStatus = CheckStatus.UNKNOWN
    dns_check: CheckStatus = CheckStatus.UNKNOWN
    free_check: CheckStatus = CheckStatus.UNKNOWN
    disposable_check: CheckStatus = CheckStatus.UNKNOWN
    mx_records: list[str] = field(default_factory=list)
    
    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> EmailVerificationResult:
        """Create from API response."""
        def parse_check(value: str) -> CheckStatus:
            if value == "true":
                return CheckStatus.PASSED
            elif value == "false":
                return CheckStatus.FAILED
            return CheckStatus.UNKNOWN
        
        return cls(
            email_address=data.get("emailAddress", ""),
            format_check=parse_check(data.get("formatCheck", "")),
            smtp_check=parse_check(data.get("smtpCheck", "")),
            dns_check=parse_check(data.get("dnsCheck", "")),
            free_check=parse_check(data.get("freeCheck", "")),
            disposable_check=parse_check(data.get("disposableCheck", "")),
            mx_records=data.get("mxRecords", []),
        )
    
    def is_valid(self) -> tuple[bool, str]:
        """
        Check if email passed all validation checks.
        
        Returns:
            Tuple of (is_valid, failure_reason)
        """
        checks = [
            (self.format_check, "format"),
            (self.smtp_check, "SMTP"),
            (self.dns_check, "DNS"),
        ]
        
        for status, name in checks:
            if status == CheckStatus.FAILED:
                return False, f"Failed {name} check"
        
        if self.free_check == CheckStatus.PASSED:
            return False, "Free email address"
        
        if self.disposable_check == CheckStatus.PASSED:
            return False, "Disposable email address"
        
        return True, ""


@dataclass
class DNSRecordInfo:
    """DNS record information with geo and netblock data."""
    hostname: str
    ip_address: str
    geo: GeoLocation | None = None
    netblock: NetBlockInfo | None = None


@dataclass 
class KYCReport:
    """Complete KYC verification report."""
    email: str
    domain: str
    email_verification: EmailVerificationResult | None = None
    email_geo: GeoLocation | None = None
    domain_reputation_score: int | None = None
    domain_age_days: int | None = None
    whois_registrant: str | None = None
    whois_registrar: str | None = None
    whois_contact_email: str | None = None
    whois_history_count: int | None = None
    ns_records: list[DNSRecordInfo] = field(default_factory=list)
    mx_records: list[DNSRecordInfo] = field(default_factory=list)
    mx_domain_counts: dict[str, int] = field(default_factory=dict)
    threat_intel: dict[str, list[ThreatIntelResult]] = field(default_factory=dict)
    ssl_cert: SSLCertInfo | None = None
    countries_seen: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    elapsed_time: float = 0.0


# =============================================================================
# Async HTTP Client
# =============================================================================

class AsyncAPIClient:
    """Async HTTP client with connection pooling and rate limiting."""
    
    def __init__(self, api_key: str, max_concurrent: int = 10, timeout: int = 30):
        self.api_key = api_key
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None
    
    async def __aenter__(self) -> AsyncAPIClient:
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, *args) -> None:
        if self._session:
            await self._session.close()
    
    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        return self._session
    
    async def get_json(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Make an async GET request and return JSON response."""
        async with self.semaphore:
            params = params or {}
            params["apiKey"] = self.api_key
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise APIError(f"API error: {text}", response.status)
                    return await response.json()
            except aiohttp.ClientError as e:
                raise APIError(f"Request failed: {e}")


# =============================================================================
# API Service Classes
# =============================================================================

class EmailVerificationService:
    """Service for email verification operations."""
    
    def __init__(self, client: AsyncAPIClient):
        self.client = client
    
    async def verify_email(self, email: str) -> EmailVerificationResult:
        """Verify an email address."""
        data = await self.client.get_json(
            Config.EMAIL_VERIFICATION_URL,
            {"emailAddress": email, "outputFormat": "json"}
        )
        return EmailVerificationResult.from_api_response(data)
    
    async def get_geo_by_email(self, email: str) -> GeoLocation:
        """Get geolocation data for an email address."""
        data = await self.client.get_json(
            Config.GEO_LOCATION_URL,
            {"email": email}
        )
        return GeoLocation.from_dict(data)


class ThreatIntelService:
    """Service for threat intelligence lookups."""
    
    def __init__(self, client: AsyncAPIClient):
        self.client = client
    
    async def lookup(self, ioc: str) -> list[ThreatIntelResult]:
        """Look up threat intelligence for an IOC (IP or domain)."""
        try:
            data = await self.client.get_json(
                Config.THREAT_INTEL_URL,
                {"ioc": ioc}
            )
            
            results = []
            for item in data.get("results", []):
                results.append(ThreatIntelResult(
                    value=item.get("value", ""),
                    first_seen=item.get("firstSeen", ""),
                    last_seen=item.get("lastSeen", ""),
                    threat_type=item.get("threatType", ""),
                    ioc_type=item.get("iocType", ""),
                ))
            return results
        except APIError:
            return []
    
    async def lookup_batch(self, iocs: list[str]) -> dict[str, list[ThreatIntelResult]]:
        """Look up threat intelligence for multiple IOCs concurrently."""
        tasks = {ioc: self.lookup(ioc) for ioc in iocs}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        return {
            ioc: result if isinstance(result, list) else []
            for ioc, result in zip(tasks.keys(), results)
        }


class SSLCertService:
    """Service for SSL certificate lookups."""
    
    def __init__(self, client: AsyncAPIClient, api_key: str):
        self.client = client
        self.api_key = api_key
    
    async def get_cert_info(self, domain: str) -> SSLCertInfo | None:
        """Get SSL certificate information for a domain."""
        try:
            data = await self.client.get_json(
                Config.SSL_CERT_URL,
                {"domainName": domain}
            )
            
            # Check for error response
            if data.get("code", 0) >= 400:
                return None
            
            certs = data.get("certificates", [])
            if not certs:
                return None
            
            cert = certs[0]
            issuer = cert.get("issuer", {})
            subject = cert.get("subject", {})
            
            # Get netblock info
            ip = data.get("ip", "")
            netblock = await self._get_netblock(ip) if ip else NetBlockInfo()
            
            return SSLCertInfo(
                ip=ip,
                domain=data.get("domain", ""),
                port=data.get("port", 443),
                chain_hierarchy=cert.get("chainHierarchy", ""),
                validation_type=cert.get("validationType", ""),
                valid_from=cert.get("validFrom", ""),
                valid_to=cert.get("validTo", ""),
                subject_cn=subject.get("commonName", ""),
                issuer_country=issuer.get("country", ""),
                organization=issuer.get("organization", ""),
                netblock=netblock,
            )
        except (APIError, KeyError):
            return None
    
    async def _get_netblock(self, ip: str) -> NetBlockInfo:
        """Get netblock info for an IP address."""
        try:
            ipnb_client = ipnb.Client(self.api_key)
            response = ipnb_client.get(ip)
            
            if response.count > 0:
                as_info = response["inetnums"][0]["AS"]
                return NetBlockInfo(asn=as_info["asn"], name=as_info["name"])
        except Exception:
            pass
        return NetBlockInfo()


# =============================================================================
# Synchronous API Wrappers (for libraries without async support)
# =============================================================================

class SyncAPIServices:
    """Wrapper for synchronous WHOISXMLAPI libraries."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._dns_client = dns.Client(api_key)
        self._geo_client = geoip.GeoIP(api_key)
        self._whois_client = who.Client(api_key=api_key)
        self._whois_history_client = whohist.ApiClient(api_key)
        self._reputation_client = dr.Client(api_key)
        self._rmx_client = rmx.Client(api_key)
        self._netblock_client = ipnb.Client(api_key)
    
    def get_dns_records(self, domain: str, record_type: str) -> list[str]:
        """Get DNS records for a domain."""
        try:
            response = self._dns_client.get(domain, record_type)
            records = response.records_by_type.get(record_type, [])
            
            values = []
            for record in records:
                value = record.value if hasattr(record, 'value') else record.get('value', '')
                # Strip trailing dot from DNS names
                if value.endswith('.'):
                    value = value[:-1]
                values.append(value)
            return values
        except Exception:
            return []
    
    def get_a_records(self, hostname: str) -> list[str]:
        """Get A records (IP addresses) for a hostname."""
        return self.get_dns_records(hostname, 'A')
    
    def get_geo_by_ip(self, ip: str) -> GeoLocation:
        """Get geolocation for an IP address."""
        try:
            data = self._geo_client.lookup(ip)
            return GeoLocation.from_dict(data)
        except Exception:
            return GeoLocation()
    
    def get_netblock(self, ip: str) -> NetBlockInfo:
        """Get netblock information for an IP address."""
        try:
            response = self._netblock_client.get(ip)
            if response.count > 0:
                as_info = response["inetnums"][0]["AS"]
                return NetBlockInfo(asn=as_info["asn"], name=as_info["name"])
        except Exception as e:
            # Uncomment for debugging: print(f"Netblock error for {ip}: {e}")
            pass
        return NetBlockInfo()
    
    def get_domain_reputation(self, domain: str) -> int | None:
        """Get domain reputation score."""
        try:
            response = self._reputation_client.get(domain)
            return response.reputation_score
        except Exception:
            return None
    
    def get_whois(self, domain: str) -> dict[str, Any]:
        """Get WHOIS data for a domain."""
        try:
            whois = self._whois_client.data(domain)
            
            creation_date = None
            age_days = None
            
            if whois.created_date_normalized:
                try:
                    creation_date = datetime.strptime(
                        str(whois.created_date_normalized), 
                        "%Y-%m-%d %H:%M:%S"
                    )
                    age_days = (datetime.now() - creation_date).days
                except ValueError:
                    pass
            
            return {
                "creation_date": str(whois.created_date_normalized) if whois.created_date_normalized else None,
                "age_days": age_days,
                "registrant": whois.registrant.name if whois.registrant else None,
                "registrar": whois.registrar_name,
                "contact_email": whois.contact_email,
            }
        except Exception:
            return {}
    
    def get_whois_history_count(self, domain: str) -> int | None:
        """Get count of historical WHOIS records."""
        try:
            return self._whois_history_client.preview(domain)
        except Exception:
            return None
    
    def get_mx_domain_count(self, mx_hostname: str) -> int:
        """Get count of domains using an MX server."""
        try:
            result = self._rmx_client.data(mx_hostname)
            return result.size if hasattr(result, 'size') else 0
        except Exception:
            return 0


# =============================================================================
# Main KYC Processor
# =============================================================================

class KYCProcessor:
    """Main processor for KYC verification."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.sync_services = SyncAPIServices(api_key)
        self.countries_seen: list[str] = []
    
    def _add_country(self, country: str) -> None:
        """Track a country code seen during processing."""
        if country and country != "Unknown":
            self.countries_seen.append(country)
    
    async def process_email(self, email: str) -> KYCReport:
        """
        Process full KYC verification for an email address.
        
        Args:
            email: Email address to verify
            
        Returns:
            Complete KYC report
        """
        start_time = time.perf_counter()
        self.countries_seen = []
        
        domain = email.split('@')[1] if '@' in email else ""
        report = KYCReport(email=email, domain=domain)
        
        async with AsyncAPIClient(
            self.api_key,
            max_concurrent=Config.MAX_CONCURRENT_REQUESTS,
            timeout=Config.REQUEST_TIMEOUT
        ) as client:
            
            # Initialize async services
            email_service = EmailVerificationService(client)
            threat_service = ThreatIntelService(client)
            ssl_service = SSLCertService(client, self.api_key)
            
            # Step 1: Email verification
            print("\n[1/6] Verifying email address...")
            try:
                report.email_verification = await email_service.verify_email(email)
                self._print_email_verification(report.email_verification)
                
                is_valid, reason = report.email_verification.is_valid()
                if not is_valid:
                    report.errors.append(f"Email validation failed: {reason}")
                    print(f"      ❌ {reason}")
                    report.elapsed_time = time.perf_counter() - start_time
                    return report
                
                print("      ✓ Email verification passed")
                
                # Get email geolocation
                report.email_geo = await email_service.get_geo_by_email(email)
                if report.email_geo:
                    self._add_country(report.email_geo.country)
                    print(f"      Location: {report.email_geo.city}, {report.email_geo.region}, {report.email_geo.country}")
                    
            except APIError as e:
                report.errors.append(f"Email verification failed: {e}")
                print(f"      ❌ Error: {e}")
            
            # Step 2: DNS record collection (NS and MX)
            print("\n[2/6] Collecting DNS records...")
            ns_hostnames = self.sync_services.get_dns_records(domain, 'NS')
            mx_hostnames = report.email_verification.mx_records if report.email_verification else []
            
            print(f"      Found {len(ns_hostnames)} NS records, {len(mx_hostnames)} MX records")
            
            # Resolve all hostnames to IPs and get geo/netblock info
            report.ns_records = self._resolve_dns_records(ns_hostnames, "NS")
            report.mx_records = self._resolve_dns_records(mx_hostnames, "MX")
            
            # Get MX domain counts
            for mx_record in report.mx_records:
                count = self.sync_services.get_mx_domain_count(mx_record.hostname)
                report.mx_domain_counts[mx_record.hostname] = count
            
            if not mx_hostnames:
                report.errors.append("No MX records found - invalid email configuration")
                print("      ❌ No MX records found")
            
            # Step 3: Domain reputation and WHOIS
            print("\n[3/6] Checking domain reputation and WHOIS...")
            
            report.domain_reputation_score = self.sync_services.get_domain_reputation(domain)
            if report.domain_reputation_score is not None:
                status = "✓" if report.domain_reputation_score > Config.REPUTATION_SCORE_THRESHOLD else "⚠"
                print(f"      {status} Reputation score: {report.domain_reputation_score}")
            
            whois_data = self.sync_services.get_whois(domain)
            report.domain_age_days = whois_data.get("age_days")
            report.whois_registrant = whois_data.get("registrant")
            report.whois_registrar = whois_data.get("registrar")
            report.whois_contact_email = whois_data.get("contact_email")
            
            if report.domain_age_days is not None:
                if report.domain_age_days < Config.NEW_DOMAIN_DAYS_THRESHOLD:
                    print(f"      ⚠ Domain is only {report.domain_age_days} days old")
                else:
                    print(f"      ✓ Domain is {report.domain_age_days} days old")
            
            report.whois_history_count = self.sync_services.get_whois_history_count(domain)
            if report.whois_history_count:
                print(f"      Historical WHOIS records: {report.whois_history_count}")
            
            # Step 4: Threat intelligence (concurrent batch lookups)
            print("\n[4/6] Checking threat intelligence...")
            
            all_iocs = self._collect_iocs(domain, report)
            report.threat_intel = await threat_service.lookup_batch(all_iocs)
            
            threats_found = sum(len(v) for v in report.threat_intel.values())
            if threats_found:
                print(f"      ⚠ Found {threats_found} threat intelligence records")
            else:
                print("      ✓ No threat intelligence records found")
            
            # Step 5: SSL certificate
            print("\n[5/6] Checking SSL certificate...")
            
            report.ssl_cert = await ssl_service.get_cert_info(domain)
            if report.ssl_cert:
                self._add_country(report.ssl_cert.issuer_country)
                print(f"      ✓ Valid from {report.ssl_cert.valid_from} to {report.ssl_cert.valid_to}")
                print(f"      Issuer: {report.ssl_cert.organization} ({report.ssl_cert.issuer_country})")
                
                # Additional threat intel for SSL
                if report.ssl_cert.ip:
                    ssl_threat = await threat_service.lookup(report.ssl_cert.ip)
                    if ssl_threat:
                        report.threat_intel[f"ssl_ip:{report.ssl_cert.ip}"] = ssl_threat
            else:
                print("      ⚠ Could not retrieve SSL certificate")
            
            # Step 6: Summary
            print("\n[6/6] Generating summary...")
            report.countries_seen = sorted(set(self.countries_seen))
            print(f"      Countries observed: {', '.join(report.countries_seen) or 'None'}")
        
        report.elapsed_time = time.perf_counter() - start_time
        return report
    
    def _resolve_dns_records(self, hostnames: list[str], record_type: str) -> list[DNSRecordInfo]:
        """Resolve hostnames to IPs and collect geo/netblock data."""
        records = []
        
        for hostname in hostnames:
            ips = self.sync_services.get_a_records(hostname)
            
            for ip in ips:
                geo = self.sync_services.get_geo_by_ip(ip)
                netblock = self.sync_services.get_netblock(ip)
                
                if geo:
                    self._add_country(geo.country)
                
                records.append(DNSRecordInfo(
                    hostname=hostname,
                    ip_address=ip,
                    geo=geo,
                    netblock=netblock,
                ))
                
                print(f"      {record_type}: {hostname} -> {ip}")
                print(f"           Location: {geo.city}, {geo.region}, {geo.country}")
                print(f"           ASN: {netblock.asn} ({netblock.name})")
        
        return records
    
    def _collect_iocs(self, domain: str, report: KYCReport) -> list[str]:
        """Collect all IOCs for threat intelligence lookup."""
        iocs = [domain]
        
        for record in report.ns_records + report.mx_records:
            if record.hostname not in iocs:
                iocs.append(record.hostname)
            if record.ip_address not in iocs:
                iocs.append(record.ip_address)
        
        return iocs
    
    def _print_email_verification(self, result: EmailVerificationResult) -> None:
        """Print email verification results."""
        checks = [
            ("Format", result.format_check),
            ("SMTP", result.smtp_check),
            ("DNS", result.dns_check),
            ("Free email", result.free_check),
            ("Disposable", result.disposable_check),
        ]
        
        for name, status in checks:
            symbol = "✓" if status == CheckStatus.PASSED else "✗" if status == CheckStatus.FAILED else "?"
            # For free/disposable, we want FAILED to be good
            if name in ("Free email", "Disposable"):
                symbol = "✓" if status == CheckStatus.FAILED else "✗" if status == CheckStatus.PASSED else "?"
            print(f"      {symbol} {name}: {status.value}")


# =============================================================================
# Report Printer
# =============================================================================

class ReportPrinter:
    """Formats and prints KYC reports."""
    
    @staticmethod
    def print_full_report(report: KYCReport) -> None:
        """Print a complete KYC report."""
        print("\n" + "=" * 70)
        print("                        KYC VERIFICATION REPORT")
        print("=" * 70)
        
        print(f"\nEmail: {report.email}")
        print(f"Domain: {report.domain}")
        print(f"Processing time: {report.elapsed_time:.2f} seconds")
        
        # Email verification
        if report.email_verification:
            print("\n--- Email Verification ---")
            is_valid, reason = report.email_verification.is_valid()
            print(f"Status: {'PASSED' if is_valid else f'FAILED - {reason}'}")
            
            if report.email_geo:
                print(f"Email Geo: {report.email_geo.city}, {report.email_geo.region}, {report.email_geo.country}")
        
        # Domain info
        print("\n--- Domain Information ---")
        if report.domain_reputation_score is not None:
            status = "OK" if report.domain_reputation_score > Config.REPUTATION_SCORE_THRESHOLD else "LOW"
            print(f"Reputation Score: {report.domain_reputation_score} ({status})")
        
        if report.domain_age_days is not None:
            print(f"Domain Age: {report.domain_age_days} days")
        
        if report.whois_registrant:
            print(f"Registrant: {report.whois_registrant}")
        if report.whois_registrar:
            print(f"Registrar: {report.whois_registrar}")
        if report.whois_history_count:
            print(f"WHOIS History Records: {report.whois_history_count}")
        
        # DNS Records
        if report.ns_records:
            print("\n--- NS Records ---")
            for record in report.ns_records:
                print(f"  {record.hostname} -> {record.ip_address}")
                if record.geo:
                    print(f"    Location: {record.geo.country}")
                if record.netblock:
                    print(f"    ASN: {record.netblock.asn} ({record.netblock.name})")
        
        if report.mx_records:
            print("\n--- MX Records ---")
            for record in report.mx_records:
                print(f"  {record.hostname} -> {record.ip_address}")
                if record.hostname in report.mx_domain_counts:
                    print(f"    Domains on server: {report.mx_domain_counts[record.hostname]}")
                if record.geo:
                    print(f"    Location: {record.geo.country}")
                if record.netblock:
                    print(f"    ASN: {record.netblock.asn} ({record.netblock.name})")
        
        # Threat Intelligence
        threats = {k: v for k, v in report.threat_intel.items() if v}
        if threats:
            print("\n--- Threat Intelligence ---")
            for ioc, results in threats.items():
                print(f"\n  {ioc}:")
                for result in results:
                    print(f"    Type: {result.threat_type}")
                    print(f"    First seen: {result.first_seen}")
                    print(f"    Last seen: {result.last_seen}")
        else:
            print("\n--- Threat Intelligence ---")
            print("  No threats detected")
        
        # SSL Certificate
        if report.ssl_cert:
            print("\n--- SSL Certificate ---")
            print(f"  IP: {report.ssl_cert.ip}")
            print(f"  Valid: {report.ssl_cert.valid_from} to {report.ssl_cert.valid_to}")
            print(f"  Subject: {report.ssl_cert.subject_cn}")
            print(f"  Issuer: {report.ssl_cert.organization} ({report.ssl_cert.issuer_country})")
            print(f"  ASN: {report.ssl_cert.netblock.asn} ({report.ssl_cert.netblock.name})")
        
        # Countries
        if report.countries_seen:
            print("\n--- Countries Observed ---")
            counter = Counter(report.countries_seen)
            print(f"  {', '.join(f'{c}({n})' for c, n in counter.most_common())}")
        
        # Errors
        if report.errors:
            print("\n--- Errors ---")
            for error in report.errors:
                print(f"  ⚠ {error}")
        
        print("\n" + "=" * 70)


# =============================================================================
# Main Entry Point
# =============================================================================

async def main(email: str | None = None) -> int:
    """Main entry point for KYC verification."""
    
    # Validate configuration
    try:
        Config.validate()
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("\nTo set your API key:")
        print("  export WHOISXML_API_KEY='your-api-key-here'")
        return 1
    
    # Get email address
    if not email:
        email = input("\nEnter email address: ").strip()
    
    if not email or '@' not in email:
        print("Invalid email address")
        return 1
    
    print(f"\nStarting KYC verification for: {email}")
    print("-" * 50)
    
    # Process
    processor = KYCProcessor(Config.API_KEY)
    report = await processor.process_email(email)
    
    # Print report
    ReportPrinter.print_full_report(report)
    
    return 0 if not report.errors else 1


def run():
    """Synchronous wrapper for main()."""
    email = sys.argv[1] if len(sys.argv) > 1 else None
    return asyncio.run(main(email))


if __name__ == "__main__":
    sys.exit(run())
