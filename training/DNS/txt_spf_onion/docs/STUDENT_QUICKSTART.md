# SPF Onion Detection Labs - Student Quick Start Guide

## 📥 Setup (Do This First!)

### Step 1: Install Required Libraries

Open your terminal/command prompt and run:

```bash
pip install dnspython tqdm
```

Or if you're using Python 3 specifically:

```bash
pip3 install dnspython tqdm
```

**Verify installation:**
```bash
python -c "import dns.resolver; import tqdm; print('✓ All libraries installed!')"
```

### Step 2: Get the Lab Files

You should have received:
- `spf_labs_working.py` - Main lab file with complete implementation
- `your_dataset.csv` - The DNS TXT record dataset
- This Quick Start Guide

Put all files in the same folder/directory.

### Step 3: Verify Your Dataset

Check that your dataset has the right format:

```bash
# View first few lines (Mac/Linux)
head -5 your_dataset.csv

# View first few lines (Windows PowerShell)
Get-Content your_dataset.csv -Head 5
```

You should see:
```
d,du,txt
example.com,1721486026,v=spf1 ip4:192.0.2.1 -all
another.com,1721486027,v=spf1 include:_spf.google.com -all
...
```

---

## 🚀 How to Run the Labs

### Method 1: Interactive Python (Recommended for Learning)

**Open Python in interactive mode:**

```bash
python -i spf_labs_working.py
```

This loads all the functions and drops you into an interactive Python session where you can test things.

**Then run Lab 1 commands:**

```python
# Lab 1: Scan the dataset for candidates
stats = identify_candidates('your_dataset.csv', 'candidates.csv')

# View the results
generate_phase1_report(stats)

# See the candidates file
print("Candidates saved to: candidates.csv")
```

**Then run Lab 2 commands:**

```python
# Lab 2: Deep analysis of candidates
violations = find_violations('candidates.csv')

# View violations
for v in violations[:5]:  # Show first 5
    print(f"{v['domain']}: {v['lookup_count']} lookups")
```

**Then run Lab 3 commands:**

```python
# Lab 3: Generate reports
generate_executive_report(violations, stats)
generate_technical_report(violations, 'technical_report.txt')
```

**Exit when done:**
```python
exit()
```

### Method 2: Write Your Own Script

**Create a new file called `run_labs.py`:**

```python
# run_labs.py
from spf_labs_working import *

print("="*70)
print("SPF ONION ANALYSIS - Starting")
print("="*70)

# LAB 1: Fast Scan
print("\n[LAB 1] Scanning dataset...")
stats = identify_candidates('your_dataset.csv', 'candidates.csv')
generate_phase1_report(stats)

# LAB 2: Deep Analysis
print("\n[LAB 2] Analyzing candidates...")
violations = find_violations('candidates.csv')
print(f"\nFound {len(violations)} violations!")

# LAB 3: Generate Reports
print("\n[LAB 3] Generating reports...")
generate_executive_report(violations, stats)
generate_technical_report(violations, 'technical_report.txt')

print("\n✓ Analysis complete! Check the output files.")
```

**Run it:**
```bash
python run_labs.py
```

### Method 3: One-Line Full Analysis

**Run everything at once:**

```bash
python -c "from spf_labs_working import run_full_analysis; run_full_analysis('your_dataset.csv')"
```

### Method 4: Jupyter Notebook (If You Prefer)

**Create a notebook with cells:**

**Cell 1:**
```python
from spf_labs_working import *
import pandas as pd
```

**Cell 2:**
```python
# Lab 1
stats = identify_candidates('your_dataset.csv', 'candidates.csv')
print(f"Found {stats['candidates']} candidates from {stats['total_records']} records")
```

**Cell 3:**
```python
# Lab 2
violations = find_violations('candidates.csv')
print(f"Found {len(violations)} violations")
```

**Cell 4:**
```python
# Lab 3
generate_executive_report(violations, stats)
generate_technical_report(violations)
```

---

## 📋 Lab-by-Lab Walkthrough

### LAB 1: Fast Scan (Phase 1)

**Goal:** Scan millions of records quickly to identify candidates worth investigating.

**What it does:**
- Streams through ALL records (memory efficient)
- Identifies SPF records
- Filters for suspicious patterns
- **No DNS lookups** (keeps it fast!)

**Run it:**
```python
stats = identify_candidates('your_dataset.csv', 'candidates.csv')
generate_phase1_report(stats)
```

**Expected output:**
```
Records processed: 2,500,000
SPF records found: 450,000 (18.0%)
Candidates identified: 1,247
Processing time: 3.2 minutes
```

**What gets flagged:**
- 5+ include directives (complex chains)
- 10+ total mechanisms
- Suspicious domains (free DNS services, abused TLDs)
- Deprecated mechanisms (ptr)

### LAB 2: Deep Analysis (Phase 2)

**Goal:** Perform DNS lookups on candidates to find actual RFC violations.

**What it does:**
- DNS lookups on filtered candidates only
- Recursively follows SPF chains
- Counts actual DNS lookups
- Uses aggressive caching

**Run it:**
```python
violations = find_violations('candidates.csv')
```

**Expected output:**
```
Analyzing 1,247 candidates...
DNS Cache Performance:
  Unique domains queried: 412
  Cache hit rate: 92.3%
VIOLATIONS FOUND: 89 domains exceed 10 DNS lookups
```

**What counts as a violation:**
- More than 10 DNS lookups (RFC 7208 limit)
- These domains will have email delivery issues

### LAB 3: Reporting (Phase 3)

**Goal:** Generate actionable reports for security teams.

**What it does:**
- Executive summary (high-level stats)
- Technical report (detailed findings)
- Threat scoring
- Remediation recommendations

**Run it:**
```python
generate_executive_report(violations, stats)
generate_technical_report(violations, 'technical_report.txt')
```

**Generated files:**
- `technical_report.txt` - Detailed findings with recommendations

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'dns'"

**Fix:**
```bash
pip install dnspython
# NOT just "pip install dns" - that's a different package!
```

### Error: "FileNotFoundError: [Errno 2] No such file or directory"

**Fix:** Make sure you're in the right directory
```bash
# Check your current directory
pwd  # Mac/Linux
cd   # Windows

# List files in current directory
ls   # Mac/Linux
dir  # Windows

# Change to the correct directory
cd /path/to/your/lab/files
```

### Error: "MemoryError" or Python crashes

**Cause:** Loading too much data into memory at once

**Fix:** The code uses generators by default, but if you modified it:
```python
# WRONG - loads everything into memory:
records = list(stream_spf_records('your_dataset.csv'))

# RIGHT - processes one at a time:
for record in stream_spf_records('your_dataset.csv'):
    process(record)
```

### Program is running very slowly

**Check:**
1. Are you using an HDD (not SSD)? This will be slower
2. Are you reading the file multiple times?
3. Are you using the caching resolver?

**Speed test:**
```python
import time
start = time.time()
count = sum(1 for _ in stream_spf_records('your_dataset.csv'))
elapsed = time.time() - start
print(f"Processed {count} records in {elapsed:.2f} seconds")
print(f"Rate: {count/elapsed:,.0f} records/second")
```

Should see: 50,000+ records/second

### No progress bar showing

**Install tqdm:**
```bash
pip install tqdm
```

The code works without it, but progress bars make long operations easier to monitor.

---

## 💡 Tips for Success

### 1. Start Small, Then Scale

Test with a quick run first:

```python
# Quick test - just view sample records
quick_test('your_dataset.csv', num_records=10)
```

### 2. Use Print Statements for Debugging

```python
# Check what you have
print(f"Candidates: {len(candidates)}")
print(f"Violations: {len(violations)}")
```

### 3. Save Intermediate Results

Don't reprocess everything each time:

```python
# Run Phase 1 once, save candidates
identify_candidates('your_dataset.csv', 'candidates.csv')

# Later, just load candidates for Phase 2
violations = find_violations('candidates.csv')  # Much faster!
```

### 4. Check File Sizes

Verify output files were created:

```bash
# Mac/Linux
ls -lh *.csv *.txt

# Windows
dir *.csv *.txt
```

---

## 📊 Expected Results

After running all labs, you should see:

**Phase 1 Output:**
```
======================================================================
PHASE 1: FAST SCAN RESULTS
======================================================================
Total records processed: 2,500,000
SPF records found: 450,000 (18.0%)
Candidates identified: 1,247
Processing time: 3.2 minutes
Processing rate: 13,000 records/second

Top reasons for flagging:
  many_includes: 487 (39.1%)
  suspicious_domain: 312 (25.0%)
  many_mechanisms: 289 (23.2%)
  deprecated_ptr: 159 (12.7%)
```

**Phase 2 Output:**
```
======================================================================
PHASE 2: DEEP ANALYSIS RESULTS
======================================================================
Candidates analyzed: 1,247
Violations found (>10 lookups): 89 (7.1%)
DNS queries made: 412 unique domains
Cache hit rate: 92.3%
Processing time: 8.4 minutes

TOP VIOLATIONS:
1. enterprise-mega-corp.com - 23 DNS lookups
2. suspicious-dynu-chain.net - 18 DNS lookups
3. complex-marketing-saas.com - 16 DNS lookups
```

**Generated Files:**
- `candidates.csv` - Filtered domains from Phase 1
- `technical_report.txt` - Detailed findings from Phase 2/3

---

## 🎯 Quick Reference Commands

**Start interactive session:**
```bash
python -i spf_labs_working.py
```

**Run full analysis:**
```python
# All-in-one command
run_full_analysis('your_dataset.csv')

# Or step-by-step:
stats = identify_candidates('your_dataset.csv', 'candidates.csv')
violations = find_violations('candidates.csv')
generate_executive_report(violations, stats)
generate_technical_report(violations)
```

**Quick test:**
```python
quick_test('your_dataset.csv', num_records=10)
```

**Exit Python:**
```python
exit()
# or Ctrl+D (Mac/Linux) / Ctrl+Z then Enter (Windows)
```

---

## 🆘 Getting Help

1. **Check error messages** - they usually tell you what's wrong
2. **Use print() statements** - see what your code is doing
3. **Start simple** - test with small datasets first
4. **Ask the instructor** - raise your hand!

---

## ✅ Success Checklist

**Before you start:**
- [ ] Python 3.7+ installed
- [ ] dnspython library installed
- [ ] tqdm library installed (optional but recommended)
- [ ] Dataset file in same folder as lab file
- [ ] Can open the lab file in your editor

**You're ready when:**
- [ ] Can run `python -i spf_labs_working.py` without errors
- [ ] Can call `quick_test()` and see output
- [ ] Dataset file loads correctly

**You've completed Lab 1 when:**
- [ ] Scanned all records
- [ ] Generated candidates.csv
- [ ] See statistics output
- [ ] Identified candidates

**You've completed Lab 2 when:**
- [ ] Analyzed all candidates
- [ ] Found violations (>10 DNS lookups)
- [ ] See cache statistics
- [ ] Have list of violating domains

**You've completed Lab 3 when:**
- [ ] Generated executive summary
- [ ] Created technical_report.txt
- [ ] Have actionable findings

---

## 📚 Understanding the Analysis

### What is an SPF Onion?

An SPF Onion is a complex, multi-layered SPF record where:
- Multiple `include:` directives reference other domains
- Each referenced domain may have more includes
- The chain can be many layers deep
- Total DNS lookups exceed the RFC 7208 limit of 10

### Why Does This Matter?

**Technical Impact:**
- Email delivery failures (when >10 lookups)
- Increased DNS load
- Slower email processing

**Security Impact:**
- Complex records are harder to audit
- Third-party services increase attack surface
- Can be used to obfuscate phishing infrastructure

### The Two-Phase Strategy

**Phase 1: Fast Scan (Static Analysis)**
- No network calls
- Pure pattern matching
- Process millions of records in minutes
- Goal: Find candidates worth investigating

**Phase 2: Deep Analysis (Dynamic Analysis)**
- DNS lookups (slow but accurate)
- Only on filtered candidates
- Recursive chain following
- Goal: Find actual violations

This is the same strategy used in real threat hunting!

---

## 🎓 Learning Objectives

By completing these labs, you'll learn:

1. **Big Data Processing**
   - Streaming large files efficiently
   - Memory-efficient algorithms
   - Performance optimization

2. **Network Programming**
   - DNS queries and caching
   - Recursive algorithms
   - Error handling at scale

3. **Threat Hunting**
   - Multi-phase analysis strategy
   - Prioritization under constraints
   - Pattern recognition

4. **Security Analysis**
   - Email authentication protocols
   - RFC compliance checking
   - Threat scoring

---

**Good luck! Remember: The goal is to learn. Don't hesitate to ask for help if you get stuck!** 🚀

---

For more information about DNS intelligence and threat detection tools, visit [WhoisXML API](https://www.whoisxmlapi.com).
