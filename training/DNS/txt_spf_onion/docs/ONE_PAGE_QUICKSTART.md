# SPF Onion Labs - One Page Quick Start

## 🚀 Three Steps to Get Started

### STEP 1: Install Libraries (30 seconds)
```bash
pip install dnspython tqdm
```

### STEP 2: Run Interactive Python (Open Lab File)
```bash
python -i spf_labs_working.py
```

This loads all the functions and gives you a Python prompt `>>>`

### STEP 3: Run the Analysis
```python
# Quick test (optional - verify it works)
quick_test('your_dataset.csv', 10)

# Lab 1: Scan millions of records (takes 3-5 minutes)
stats = identify_candidates('your_dataset.csv', 'candidates.csv')
generate_phase1_report(stats)

# Lab 2: Deep analysis of candidates (takes 10-20 minutes)
violations = find_violations('candidates.csv')
print(f"Found {len(violations)} violations!")

# Lab 3: Generate reports
generate_executive_report(violations, stats)
generate_technical_report(violations, 'technical_report.txt')
```

---

## ⚡ Quick One-Liner

Run everything at once:

```bash
python -c "from spf_labs_working import run_full_analysis; run_full_analysis('your_dataset.csv')"
```

---

## 💻 What's Happening

The labs analyze DNS TXT records to find "SPF Onions" - complex email authentication records that:
- Have too many DNS lookups (>10, violates RFC 7208)
- Are difficult to manage and audit
- May indicate phishing infrastructure
- Cause email delivery failures

**Phase 1:** Fast scan of ALL records (no DNS lookups)  
**Phase 2:** Deep analysis with DNS lookups (on candidates only)  
**Phase 3:** Generate security reports

---

## 📝 The Workflow

```
┌─────────────────────────────────────────────┐
│  1. python -i spf_labs_working.py           │
│  2. Run commands at >>> prompt              │
│  3. Check generated CSV and TXT files       │
│  4. Review findings                         │
└─────────────────────────────────────────────┘
```

---

## 📊 Quick Commands Reference

| Command | What It Does |
|---------|-------------|
| `python -i spf_labs_working.py` | Load lab file interactively |
| `quick_test('file.csv', 10)` | Test reading first 10 records |
| `identify_candidates(...)` | Phase 1: Fast scan |
| `find_violations(...)` | Phase 2: DNS lookups |
| `run_full_analysis('file.csv')` | Run all 3 phases |
| `exit()` | Exit Python |
| `Ctrl+C` | Stop a running command |

---

## 🐛 Common Errors & Quick Fixes

| Error | Fix |
|-------|-----|
| `No module named 'dns'` | Run: `pip install dnspython` |
| `FileNotFoundError` | Check you're in the right folder with `ls` or `dir` |
| `MemoryError` | Code uses generators by default, shouldn't happen |
| No progress bar | Optional: `pip install tqdm` |

---

## 📊 What Success Looks Like

**After Phase 1:**
```
Found 1,247 candidates from 2,500,000 records
Processing time: 3.2 minutes
Rate: 13,000 records/second
```

**After Phase 2:**
```
Found 89 violations (domains with >10 DNS lookups)
Cache hit rate: 92.3%
Processing time: 8.4 minutes
```

**Files created:**
- `candidates.csv` - Suspicious domains (Phase 1)
- `technical_report.txt` - Detailed findings (Phase 3)

---

## 🎯 Example Session

```bash
$ python -i spf_onion_labs.py

======================================================================
SPF ONION LABS - Interactive Session
======================================================================

Functions available:
  quick_test('your_file.csv')              - Test file reading
  identify_candidates(...)                  - Phase 1: Fast scan
  find_violations(...)                      - Phase 2: Deep analysis
  load_stats_from_candidates('file.csv')   - Reload stats if needed
  run_full_analysis('your_file.csv')        - Run everything

Example:
  >>> quick_test('txt_database.csv')
  >>> stats = identify_candidates('txt_database.csv', 'candidates.csv')
  >>> violations = find_violations('candidates.csv')
  >>> generate_executive_report(violations, stats)

If you lost 'stats' variable:
  >>> stats = load_stats_from_candidates('candidates.csv')
  >>> generate_executive_report(violations, stats)

Or just omit stats:
  >>> generate_executive_report(violations)

>>> quick_test('100K.csv')

Quick Test: Reading first 10 SPF records...

1. 0--0--000-575urepipeline.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

2. 0--0--00000000-0000-0a09-0000-00000005b5c6urepipeline.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

3. 0--0--00000000-mailurepipeline.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

4. 0--0--000000000000.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

5. 0--0--00000000000000000000comstatic-lexarecordsurepipeline.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

6. 0--0--000000000000urepipeline.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

7. 0--0--0000000001pk1013789329107urepipeline.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

8. 0--0--0000000001urepipeline.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

9. 0--0--000000000553comstatic.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

10. 0--0--00000000korea.sendsafely.com
   SPF: v=spf1 -all...
   Mechanisms: 0 total, 0 includes

✓ Successfully read 10 SPF records!


>>> stats = identify_candidates('100K.csv', 'candidates-100K.csv')

======================================================================
PHASE 1: FAST SCAN - Identifying Candidates
======================================================================

Scanning dataset for interesting SPF records...
(This may take 3-5 minutes for millions of DNS TXT records)

Scanning: 55206 SPF records [00:00, 86769.40 SPF records/s]
>>>


>>> generate_phase1_report(stats)

======================================================================
PHASE 1: SCAN RESULTS
======================================================================

Records processed: 55,206
SPF records found: 55,206 (100.0%)
Candidates identified: 5,571 (10.1% of SPF)
Processing time: 0.7 seconds (0.0 minutes)
Processing rate: 83,596 records/second

Top reasons for flagging:
  suspicious_domain        : 5,411 ( 97.1%)
  abused_tld_xyz           : 3,231 ( 58.0%)
  deep_subdomain           : 1,652 ( 29.7%)
  abused_tld_cf            :   361 (  6.5%)
  many_mechanisms          :   153 (  2.7%)
  abused_tld_ga            :    85 (  1.5%)
  abused_tld_top           :    70 (  1.3%)
  many_includes            :     9 (  0.2%)
  abused_tld_pw            :     8 (  0.1%)
  abused_tld_ml            :     7 (  0.1%)

======================================================================

>>> violations = find_violations('candidates-100K.csv')

======================================================================
PHASE 2: DEEP ANALYSIS - DNS Lookups on Candidates
======================================================================

Analyzing 5571 candidates...
(This may take 10-15 minutes with DNS lookups)

Analyzing: 100%|█████████████████████████████████████████| 5571/5571 [00:10<00:00, 520.65 domains/s]

DNS Cache Performance:
  Unique domains queried: 144
  Cache hits: 3,715
  Cache misses: 144
  Hit rate: 96.3%

======================================================================
VIOLATIONS FOUND: 1 domains exceed 10 DNS lookups
======================================================================


>>> print(f"Found {len(violations)} violations!")
Found 1 violations!


>>> generate_executive_report(violations, stats)

======================================================================
EXECUTIVE SUMMARY: SPF ONION ANALYSIS
======================================================================
Analysis Date: 2025-10-21 13:33

Dataset Overview:
  Records Analyzed: 55,206
  SPF Records: 55,206
  Candidates Investigated: 5,571
  RFC Violations Found: 1

Severity Breakdown:
  Critical (>15 lookups): 0
  High (13-15 lookups): 1
  Medium (11-12 lookups): 0

Top 10 Worst Offenders:
   1. 0605.wkre.com                                      - 13 lookups

======================================================================


>>> generate_technical_report(violations, 'technical_report-100K.txt')

✓ Technical report saved to: technical_report-100K.txt
```

---

## 🔍 Understanding the Output

**Candidates** = Domains worth investigating (filtered from millions)
- Many includes (5+)
- Suspicious patterns (free DNS services)
- Many mechanisms (10+)

**Violations** = Domains that exceed RFC 7208 limit
- More than 10 DNS lookups
- Will cause email delivery issues
- Need immediate attention

---

## 🆘 Need Help?

1. Check the full [Student Quick Start Guide](STUDENT_QUICKSTART.md) for details
2. Read error messages - they're usually helpful
3. Try `quick_test()` first to verify basics work
4. Ask your instructor

---

## ✅ TL;DR

```bash
# Install
pip install dnspython tqdm

# Run
python -i spf_labs_working.py

# Analyze
>>> run_full_analysis('your_dataset.csv')

# Done! Check the output files.
```

---

**You've got this! 🎯** The code handles all the complexity - you just run the commands.
