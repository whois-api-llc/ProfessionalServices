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
$ python -i spf_labs_working.py

>>> # Test it works
>>> quick_test('txt_database.csv', 5)

>>> # Run Phase 1 (fast scan)
>>> stats = identify_candidates('txt_database.csv', 'candidates.csv')
Scanning: 2500000 records [03:24, 12245 records/s]
Found 1,247 candidates

>>> # Run Phase 2 (DNS lookups)
>>> violations = find_violations('candidates.csv')
Analyzing: 1247 domains [08:23, 2.48 domains/s]
Found 89 violations

>>> # Generate reports
>>> generate_executive_report(violations, stats)
>>> generate_technical_report(violations)
✓ Technical report saved to: technical_report.txt

>>> exit()
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
