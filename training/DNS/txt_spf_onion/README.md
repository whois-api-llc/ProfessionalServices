# SPF Onion Detection Labs

> **Hands-on workshop for finding malicious and misconfigured SPF records in massive DNS datasets**

A practical cybersecurity workshop that teaches threat hunting techniques by analyzing millions of DNS TXT records to identify SPF "onions" - complex, multi-layered email authentication records that violate RFC 7208 and may indicate phishing infrastructure.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Overview

This workshop provides hands-on experience with:
- **Big data processing** - Efficiently analyze millions of DNS TXT records
- **Threat hunting** - Two-phase analysis strategy (fast scan → deep analysis)
- **Email security** - Understanding SPF, DKIM, and DMARC
- **Network programming** - DNS queries, caching, and recursive algorithms

### What is an SPF Onion?

An SPF Onion is a complex SPF (Sender Policy Framework) record where:
- Multiple `include:` directives create deep chains
- Total DNS lookups exceed the RFC 7208 limit of 10
- Records become unmanageable and pose security risks
- Often used by phishers to obfuscate infrastructure

**Real-world example from the wild:**
```
suspicious-domain.com
└─ include:layer1.dynu.net
   ├─ include:layer2a.ddns.net
   │  └─ include:layer3a.freeddns.org (and more...)
   └─ include:layer2b.casacam.net
      └─ include:layer3b.kozow.com (and more...)
      
Total: 18 DNS lookups (RFC limit: 10) ❌
```

## 🎯 Learning Objectives

Students will learn:
1. How to process millions of records efficiently
2. Multi-phase threat hunting strategies
3. DNS protocol and SPF record structure
4. Performance optimization (streaming, caching)
5. Real-world security analysis techniques

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- 6.8M DNS TXT record dataset (or use your own)
- ~30 minutes for full analysis

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/spf-onion-labs.git
cd spf-onion-labs

# Install dependencies
pip install -r requirements.txt
```

### Run Analysis

```bash
# Interactive mode
python -i spf_labs_working.py

>>> # Quick test
>>> quick_test('your_dataset.csv', 10)

>>> # Run full analysis
>>> run_full_analysis('your_dataset.csv')
```

**See detailed instructions:** [Student Quick Start Guide](docs/STUDENT_QUICKSTART.md)

**Just want the essentials?** [One Page Quick Start](docs/ONE_PAGE_QUICKSTART.md)

## 📚 Workshop Structure

### Phase 1: Fast Scan (3-5 minutes)
- Stream through ALL records (memory efficient)
- Pattern matching only (no DNS lookups)
- Identify suspicious candidates
- **Output:** `candidates.csv`

### Phase 2: Deep Analysis (10-20 minutes)
- DNS lookups on candidates only
- Recursive chain following
- Count actual DNS lookups
- **Output:** List of RFC violations

### Phase 3: Reporting (1-2 minutes)
- Executive summary
- Technical findings
- Remediation recommendations
- **Output:** `technical_report.txt`

## 📊 Example Results

```
======================================================================
ANALYSIS COMPLETE
======================================================================
Dataset: 6,800,000 records analyzed
Candidates: 1,247 suspicious domains identified
Violations: 89 domains exceed RFC 7208 limit

Top Violations:
  1. enterprise-spammer.com - 23 DNS lookups
  2. phishing-chain.dynu.net - 18 DNS lookups
  3. complex-marketing.com - 16 DNS lookups

Processing Time: 11.6 minutes
Cache Hit Rate: 92.3%
```

## 🗂️ Repository Structure

```
spf-onion-labs/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── spf_labs_working.py           # Main lab file (complete)
├── test_setup.py                 # Pre-workshop verification
├── docs/
│   ├── STUDENT_QUICKSTART.md     # Detailed student guide
│   ├── ONE_PAGE_QUICKSTART.md    # Essential commands only
│   └── INSTRUCTOR_GUIDE.md       # Teaching notes
├── examples/
│   └── sample_dataset.csv        # Small sample for testing
└── results/
    └── example_report.txt        # Sample output
```

## 🔬 Technical Details

### Performance Optimizations

- **Streaming:** Generator-based file processing (KB memory usage, not GB)
- **Caching:** 92-95% cache hit rate on DNS queries
- **Filtering:** Two-phase approach reduces DNS queries by 99%

### Key Algorithms

1. **Fast Pattern Matching:** Regex-based mechanism counting (no DNS)
2. **Recursive Lookup Counter:** Traverses SPF chains with circular reference detection
3. **Threat Scoring:** Multi-factor analysis of SPF configurations

## 📖 Documentation

- **[Student Quick Start Guide](docs/STUDENT_QUICKSTART.md)** - Complete setup and usage
- **[One Page Quick Start](docs/ONE_PAGE_QUICKSTART.md)** - Essential commands
- **[Instructor Guide](docs/INSTRUCTOR_GUIDE.md)** - Workshop facilitation notes
- **[API Reference](docs/API.md)** - Function documentation

## 🎓 Workshop Format

**Duration:** 60 minutes  
**Audience:** Intermediate to advanced cybersecurity professionals  
**Format:** Hands-on coding labs

**Timeline:**
- 00:00-00:10 - Introduction & setup
- 00:10-00:25 - Lab 1: Fast scanning
- 00:25-00:50 - Lab 2: Deep analysis
- 00:50-01:00 - Lab 3: Reporting & discussion

## 🔍 Real-World Applications

This workshop teaches techniques applicable to:
- **Email security auditing** - Analyze your organization's SPF records
- **Threat intelligence** - Identify phishing infrastructure
- **Incident response** - Investigate suspicious domains
- **Compliance** - Ensure proper email authentication

## 🛠️ Technologies Used

- **Python 3.7+** - Core language
- **dnspython** - DNS queries
- **tqdm** - Progress bars (optional)
- **csv** - Data processing
- **regex** - Pattern matching

## 📈 Performance Benchmarks

Tested on MacBook Pro (M1, 16GB RAM):

| Phase | Records | Time | Rate |
|-------|---------|------|------|
| Phase 1 (scan) | 6,800,000 | 3.4 min | 33,000/sec |
| Phase 2 (analysis) | 1,247 | 8.4 min | 2.5/sec |
| Total | 6,800,000 | 11.8 min | - |

DNS queries: 412 unique, 95.8% cache hit rate

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.


## 🙏 Acknowledgments

- WHOISXMLAPI.com for DNS data and tools
- RFC 7208 (SPF specification)
- The cybersecurity community
- Provided "AS-IS" by: 
    WHOIS API, Inc.   www.whoisxmlapi.com
    Product: DNS Database

      Developers: 
         ed.gibbs@whoisxmlapi.com
         alex.ronquillo@whoisxmlapi.com, VP of Products
      Contributing authors of the original paper, "The SPF Onion - Enter the World of SPF Chaos"
         [Original Document](https://main.whoisxmlapi.com/blog/the-spf-onion-enter-the-world-of-spf-chaos)
         ed.gibbs@whoisxmlpapi.com
         jeff@vogelogic.com, Jeff Vogelpohl

## 📧 Contact

- Email: ed.gibbs@whoisxmlapi.com
- Email: alex.ronquillo@whoisxmlapi.com

## 🔗 Additional Resources

- [RFC 7208 - SPF Specification](https://www.rfc-editor.org/rfc/rfc7208)
- [WHOISXMLAPI Tools](https://www.whoisxmlapi.com)
- [Email Security Best Practices](https://dmarcian.com)

---

**⭐ Star this repo if you find it useful!**

**🎯 Ready to hunt some SPF Onions?** Check out the [Quick Start Guide](docs/ONE_PAGE_QUICKSTART.md)!
