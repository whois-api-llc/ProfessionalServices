# 🛰️ FirstWatch™
### Malicious Domain Registration Monitoring & Early-Stage Threat Intelligence

> **Detect threats at domain creation — not after damage is done.**

---

## 🔍 Overview


FirstWatch is a domain registration monitoring and WHOIS intelligence solution that provides early visibility into newly registered and potentially abusive domains.
Many cyber threats—including phishing, malware delivery, fraud, and brand impersonation—rely on domains registered shortly before use. Traditional reputation-based systems often identify these domains only after abuse has already occurred.
FirstWatch enables organizations to identify, investigate, and operationalize intelligence on suspicious domains at the earliest stages of their lifecycle.

## ✨ Why Use FirstWatch?

   FirstWatch helps organizations move upstream in the threat lifecycle by focusing on domain creation and registration behavior, rather than waiting for domains to accumulate reputation.

   Organizations use FirstWatch to:

   - Monitor newly registered and high-risk domains
   - Identify brand impersonation and typo-squatting activity
   - Detect infrastructure associated with phishing, fraud, and malware campaigns
   - Enrich investigations with WHOIS, registrar, and nameserver context
   - Integrate early indicators into existing security and intelligence workflows

## 🤖 What the Automation Script Provides

   The FirstWatch API delivers domain intelligence at scale. This automation script operationalizes that data for security, intelligence, and research use cases.

** Core Capabilities **

Domain Discovery

   - Exact domain lookup for known indicators
   - Fuzzy search for look-alike, typo-squatted, and brand-abuse domains
   - Optional fallback from exact lookup to fuzzy search
   - Flexible Output Formats
   - CSV for analyst review and reporting
   - JSON / JSONL for automation and data pipelines
   - STIX 2.1 bundle output for threat intelligence platforms
   - Threat Intelligence Integration
   - Generates STIX Indicators and Domain Name objects
   - Applies configurable TLP markings (CLEAR, GREEN, AMBER, RED)
   - Supports configurable classification (e.g., malicious, benign, anomalous)
   - Preserves original FirstWatch response data as structured enrichment

Operational Reliability

   - JWT-based authentication with automatic token refresh
   - Rate-limit-aware request handling with retry logic
   - Optional quota validation before execution
   - Streaming output suitable for large domain lists

** Configuration-Driven Operation **

   - Default behavior defined via configuration file
   - Command-line overrides when required
   - Designed for scheduled jobs, CI/CD pipelines, and SOAR integrations

** How FirstWatch Fits Into Your Security Stack **

   - FirstWatch is designed to complement existing security and intelligence platforms, not replace them.
   - It typically operates upstream of enforcement and response controls, providing early indicators that enhance downstream systems.

** Common integration patterns include: **

   Threat Intelligence Platforms (TIPs)
      - Ingest FirstWatch STIX bundles to enrich existing indicator repositories and support analyst investigations.

   SIEM and SOAR Platforms
      - Feed newly observed domains into correlation rules, enrichment workflows, and automated response playbooks.

   Email and Web Security Controls
      - Identify suspicious domains before they appear in phishing or malicious URLs.

   Brand Protection and Fraud Systems
      - Detect impersonation and scam infrastructure during registration rather than after customer impact.

   Incident Response and Hunting Workflows
      - Pivot from known IOCs to related domain infrastructure during investigations.

   By focusing on domain registration activity, FirstWatch adds visibility at a stage where many security stacks traditionally have limited coverage.

** Who Uses FirstWatch and How **

   - Security Operations (SOC)
      - Monitor newly registered domains related to alerts or brands	Earlier detection of phishing and fraud
   - Threat Intelligence Teams
      - Track emerging infrastructure and campaign setup	Improved campaign visibility and correlation
   - Brand Protection Teams
      - Identify impersonation and typo-squatting domains
      - Reduced brand and customer abuse
   - Incident Response
        - Pivot from known indicators to related domains	Faster scoping and containment
   - SOAR & Automation Engineers
      - Feed indicators into automated workflows
      - Reduced manual effort and faster response
   - Fraud & Trust Teams
      - Detect scam infrastructure early
      - Lower financial and reputational risk
   - Researchers & Analysts
      - Analyze registration patterns and abuse trends
      - Improved intelligence reporting

** Summary **

FirstWatch provides early, actionable insight into domain registrations, which are often the first observable step in cyber abuse. By combining domain monitoring, WHOIS intelligence, and automation-ready outputs—including STIX—FirstWatch enables organizations to detect, investigate, and respond to threats earlier in their lifecycle.  For teams that require proactive domain intelligence rather than reactive reputation checks, FirstWatch offers a practical and scalable solution.
