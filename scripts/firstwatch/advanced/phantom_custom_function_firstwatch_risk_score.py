"""
Splunk SOAR (Phantom) Custom Function (Reference)
File: phantom_custom_function_firstwatch_risk_score.py

Purpose:
  Compute a simple, explainable risk score for newly registered domains enriched by FirstWatch.

How to use:
  - Create a Custom Function in Splunk SOAR named: firstwatch_risk_score
  - Paste this code into the function body
  - In a playbook, call the custom function with the inputs described below

Inputs (recommended):
  - confidence (int/float): FirstWatch/STIX confidence score (0-100)
  - tlp (str): CLEAR/GREEN/AMBER/RED
  - classification (str): malicious/benign/anomalous/unknown
  - domain_age_days (int): age since registration
  - brand_similarity (float): 0.0-1.0 (if available from fuzzy matching)
  - has_dns (bool): whether domain resolves (A/AAAA/CNAME)
  - pDNS_hits (int): passive DNS count (if available)
  - corroborated (bool): confirmed by email/web/proxy telemetry

Outputs:
  - risk_score (int): 0-100
  - risk_level (str): LOW/MEDIUM/HIGH/CRITICAL
  - reasons (list[str]): human-readable explanation for auditability
"""

def _clamp(n, low=0, high=100):
    return max(low, min(high, int(round(n))))

def _risk_level(score):
    if score >= 85:
        return "CRITICAL"
    if score >= 70:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"

def firstwatch_risk_score(confidence=0, tlp="AMBER", classification="unknown",
                          domain_age_days=None, brand_similarity=None,
                          has_dns=None, pDNS_hits=None, corroborated=False):
    score = 0
    reasons = []

    # Confidence weighting (0-100)
    try:
        c = float(confidence)
    except Exception:
        c = 0.0
    score += 0.45 * c
    reasons.append(f"Confidence contributes {0.45*c:.1f} points.")

    # Classification bias
    cls = (classification or "unknown").lower()
    if cls in ("malicious", "phishing", "fraud"):
        score += 15
        reasons.append("Classification indicates malicious intent (+15).")
    elif cls in ("anomalous", "suspicious"):
        score += 8
        reasons.append("Classification indicates anomalous behavior (+8).")
    elif cls in ("benign",):
        score -= 10
        reasons.append("Classification indicates benign (-10).")

    # Domain age: newer = riskier (early-stage)
    if domain_age_days is not None:
        try:
            age = int(domain_age_days)
            if age <= 1:
                score += 15
                reasons.append("Domain age <= 1 day (+15).")
            elif age <= 7:
                score += 10
                reasons.append("Domain age <= 7 days (+10).")
            elif age <= 30:
                score += 5
                reasons.append("Domain age <= 30 days (+5).")
        except Exception:
            pass

    # Brand similarity (0-1)
    if brand_similarity is not None:
        try:
            sim = float(brand_similarity)
            if sim >= 0.92:
                score += 18
                reasons.append("High brand similarity (>=0.92) (+18).")
            elif sim >= 0.85:
                score += 10
                reasons.append("Moderate brand similarity (>=0.85) (+10).")
        except Exception:
            pass

    # DNS presence (resolves = more actionable)
    if has_dns is True:
        score += 6
        reasons.append("Domain resolves (DNS present) (+6).")
    elif has_dns is False:
        score -= 3
        reasons.append("Domain does not resolve (DNS absent) (-3).")

    # Passive DNS volume
    if pDNS_hits is not None:
        try:
            hits = int(pDNS_hits)
            if hits >= 25:
                score += 8
                reasons.append("High passive DNS volume (>=25) (+8).")
            elif hits >= 5:
                score += 4
                reasons.append("Moderate passive DNS volume (>=5) (+4).")
        except Exception:
            pass

    # Corroboration (telemetry confirmation)
    if corroborated:
        score += 25
        reasons.append("Corroborated by telemetry (+25).")

    # TLP is not a risk factor; it controls handling. Keep as note only.
    reasons.append(f"TLP is {tlp} (handling guidance, not risk).")

    score = _clamp(score)
    return {
        "risk_score": score,
        "risk_level": _risk_level(score),
        "reasons": reasons
    }
