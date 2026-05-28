# Professional.Services@whoisxmlapi.com
# Reverse-Proxy example to retrieve data from WHOISXMLAPI.COM
# Make sure you have the WXAAPIKEY environment variable set

from flask import Flask, request, jsonify
import requests
import os

# Read once at import time so the key is available under any WSGI server
# (not just when running via __main__).
API_KEY = os.getenv("WXAAPIKEY", "")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return "Hello.\nThis is a reverse proxy\n"


# ---------------------------------------------------------------------------
# Existing routes
# ---------------------------------------------------------------------------

@app.route("/ipgeo", methods=['GET'])
def proxy_ipgeo():
    """IP Geolocation — ?ipAddr=<ip>"""
    ip_address = request.args.get('ipAddr')
    target = (
        "https://ip-geolocation.whoisxmlapi.com/api/v1"
        f"?apiKey={API_KEY}&ipAddress={ip_address}"
    )
    response = requests.get(target)
    return response.text


@app.route("/whois", methods=['GET'])
def proxy_whois():
    """WHOIS Lookup — ?domainName=<domain>"""
    domain_name = request.args.get('domainName')
    target = (
        "https://www.whoisxmlapi.com/whoisserver/WhoisService"
        f"?apiKey={API_KEY}&domainName={domain_name}&outputFormat=JSON"
    )
    response = requests.get(target)
    return response.text


# ---------------------------------------------------------------------------
# New routes
# ---------------------------------------------------------------------------

@app.route("/reverse-whois", methods=['GET'])
def proxy_reverse_whois():
    """
    Reverse WHOIS — find domains by registrant contact field (name, email, org).

    Required:  ?term=<search_term>
    Optional:  &searchType=current|historic   (default: current)
               &mode=purchase|preview          (default: purchase)
               &createdDateFrom=YYYY-MM-DD
               &createdDateTo=YYYY-MM-DD
    """
    term        = request.args.get('term', '')
    search_type = request.args.get('searchType', 'current')
    mode        = request.args.get('mode', 'purchase')

    payload = {
        "apiKey": API_KEY,
        "searchType": search_type,
        "mode": mode,
        "basicSearchTerms": {"include": [term]},
    }

    # Optional date filters
    if request.args.get('createdDateFrom'):
        payload['createdDateFrom'] = request.args.get('createdDateFrom')
    if request.args.get('createdDateTo'):
        payload['createdDateTo'] = request.args.get('createdDateTo')

    response = requests.post(
        "https://reverse.whoisxmlapi.com/api/v1",
        json=payload
    )
    return response.text


@app.route("/whois-history", methods=['GET'])
def proxy_whois_history():
    """
    WHOIS History — full ownership timeline for a domain.

    Required:  ?domainName=<domain>
    """
    domain_name = request.args.get('domainName')
    target = (
        "https://whois-history.whoisxmlapi.com/api/v1"
        f"?apiKey={API_KEY}&domainName={domain_name}&outputFormat=JSON"
    )
    response = requests.get(target)
    return response.text


@app.route("/bulk-whois", methods=['POST'])
def proxy_bulk_whois():
    """
    Bulk WHOIS — WHOIS lookups for up to 10,000 domains in one call.

    POST a JSON body:  {"domains": ["example.com", "google.com", ...]}

    Large jobs may return a jobId instead of inline results; poll
    /bulk-whois-status?jobId=<id> until complete.
    """
    body = request.get_json(force=True) or {}
    domains = body.get('domains', [])

    payload = {
        "apiKey": API_KEY,
        "domains": domains,
    }
    response = requests.post(
        "https://bulk.whoisxmlapi.com/api/v1",
        json=payload
    )
    return response.text


@app.route("/bulk-whois-status", methods=['GET'])
def proxy_bulk_whois_status():
    """
    Bulk WHOIS job status — poll while a bulk job is still running.

    Required:  ?jobId=<id>
    """
    job_id = request.args.get('jobId')
    target = (
        "https://bulk.whoisxmlapi.com/api/v1"
        f"?apiKey={API_KEY}&jobId={job_id}"
    )
    response = requests.get(target)
    return response.text


@app.route("/brand-alert", methods=['GET'])
def proxy_brand_alert():
    """
    Brand Alert — newly added/dropped/updated domains matching a brand term.

    Required:  ?term=<brand>  &action=added|dropped|updated
    Optional:  &mode=purchase|preview   (default: purchase)
               &date=YYYY-MM-DD
               &withTypos=true|false
    """
    term   = request.args.get('term', '')
    action = request.args.get('action', 'added')
    mode   = request.args.get('mode', 'purchase')

    payload = {
        "apiKey": API_KEY,
        "action": action,
        "mode": mode,
        "basicSearchTerms": {"include": [term]},
    }
    if request.args.get('date'):
        payload['sinceDate'] = request.args.get('date')
    if request.args.get('withTypos', '').lower() == 'true':
        payload['withTypos'] = True

    response = requests.post(
        "https://brand-alert.whoisxmlapi.com/api/v1",
        json=payload
    )
    return response.text


@app.route("/domain-info", methods=['GET'])
def proxy_domain_info():
    """
    Domain Info — enriched WHOIS that backfills redacted fields from history.

    Required:  ?domainName=<domain>
    """
    domain_name = request.args.get('domainName')
    target = (
        "https://domain-info.whoisxmlapi.com/api/v1"
        f"?apiKey={API_KEY}&domainName={domain_name}&outputFormat=JSON"
    )
    response = requests.get(target)
    return response.text


@app.route("/subdomains", methods=['GET'])
def proxy_subdomains():
    """
    Subdomain Lookup — enumerate all known subdomains of an apex domain.

    Required:  ?domainName=<domain>
    Optional:  &limit=<1-500>  (default 500)
               &nextPageToken=<token>   (for pagination)
    """
    domain_name     = request.args.get('domainName')
    limit           = request.args.get('limit', '500')
    next_page_token = request.args.get('nextPageToken', '')

    target = (
        "https://subdomains.whoisxmlapi.com/api/v1"
        f"?apiKey={API_KEY}&domainName={domain_name}&limit={limit}"
    )
    if next_page_token:
        target += f"&nextPageToken={next_page_token}"

    response = requests.get(target)
    return response.text


@app.route("/ssl", methods=['GET'])
def proxy_ssl():
    """
    SSL Certificates — TLS cert details, SANs, validity, and chain info.

    Required:  ?domainName=<domain>
    Optional:  &includeChain=true|false   (default false)
               &fresh=true|false          (default false; true bypasses cache)
    """
    domain_name   = request.args.get('domainName')
    include_chain = request.args.get('includeChain', 'false').lower()
    fresh         = request.args.get('fresh', 'false').lower()

    target = (
        "https://ssl-certificates.whoisxmlapi.com/api/v1"
        f"?apiKey={API_KEY}&domainName={domain_name}"
        f"&includeChain={include_chain}&useFreshData={fresh}"
        f"&outputFormat=JSON"
    )
    response = requests.get(target)
    return response.text


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    if not API_KEY:
        raise EnvironmentError("WXAAPIKEY environment variable is not set.")
    app.run()
