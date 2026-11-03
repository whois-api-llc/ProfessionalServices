# High-Throughput Typosquat Scanner

A streaming, multiprocessing Python tool for identifying possible brand impersonation and typosquatting patterns in very large hostname datasets.

WHOISXMLAPI.COM 

The scanner is designed for large CSV files, including gzip-compressed input. It checks brand-like strings within individual DNS labels and across contiguous windows of adjacent labels. For example, it can inspect `micro.soft.login.example.com` for a sequence such as `microsoftlogin` rather than checking each label independently.

> **Important:** A match is an investigative lead, not proof of malicious activity. Legitimate services, customer-controlled subdomains, and unrelated strings can produce matches. Validate findings before using them for blocking or enforcement.

## Features

- **Streaming input:** Processes CSV records incrementally instead of loading the entire dataset into memory.
- **Compressed input:** Supports gzip, bzip2, and uncompressed CSV files.
- **Multiprocessing:** Distributes hostname batches across worker processes.
- **Cross-label matching:** Checks contiguous DNS-label windows to identify brands split across labels.
- **Configurable edit distance:** Uses Levenshtein distance to detect insertion, deletion, and substitution variants.
- **Trigram candidate index:** Reduces the number of brands checked in indexed mode.
- **Exhaustive mode:** Compares every eligible brand against candidate windows for validation and benchmarking.
- **Structured results:** Writes match details to a CSV report.
- **Offline suffix parsing:** Uses `tldextract` with its bundled Public Suffix List snapshot and disables live PSL retrieval.

## Requirements

- Python 3.9 or newer recommended
- `rapidfuzz`
- `tldextract`

Install dependencies:

```bash
python3 -m pip install rapidfuzz tldextract
```

## Project layout

```text
.
├── typo_scan.py       # Scanner
├── brands.txt         # One brand per line
├── input.csv.gz       # Input hostname dataset
└── matches.csv        # Generated results
```

The scanner expects one hostname column in the input CSV. By default, it reads the first column.

## Prepare the brand list

Create `brands.txt` with one brand per line. Use the canonical brand spelling, without spaces or punctuation where appropriate.

```text
microsoft
google
amazon
paypal
```

Blank lines are ignored. Review the list for duplicates and ambiguous or overly short names before running a large scan.

## Basic usage

```bash
python3 typo_scan.py input.csv.gz brands.txt matches.csv
```

For gzip-compressed input, you can specify the compression explicitly:

```bash
python3 typo_scan.py \
    input.csv.gz \
    brands.txt \
    matches.csv \
    --compression gzip
```

## Example: large dataset

For a machine with many CPU cores, this is a reasonable starting configuration:

```bash
python3 typo_scan.py \
    sdp.2026-10-06.weekly.full.csv.gz \
    brands.txt \
    matches.csv \
    --compression gzip \
    --workers 40 \
    --batch-size 5000 \
    --distance 2
```

Tune worker count and batch size against your storage, CPU, and compression throughput. More workers do not always mean faster execution: CSV parsing and gzip decompression occur in the parent process and can become bottlenecks.

## Command-line options

| Option | Purpose |
|---|---|
| `--workers` | Number of worker processes. Default: `40`. |
| `--batch-size` | Number of CSV records submitted per batch. Default: `5000`. |
| `--distance` | Maximum Levenshtein edit distance. Default: `1`. |
| `--compression` | Input compression: `auto`, `none`, `gzip`, or `bz2`. |
| `--has-header` | Treat the first CSV record as a header row. |
| `--column` | Zero-based index of the hostname column. Default: `0`. |
| `--max-labels` | Maximum number of adjacent DNS labels combined into a candidate window. Default: `4`. |
| `--max-candidates` | Maximum indexed brand candidates considered for a window. Default: `300`. |
| `--min-brand-length` | Ignore brands shorter than this many characters. Default: `5`. |
| `--min-score` | Optional minimum RapidFuzz similarity score. Default: `0` (disabled). |
| `--candidate-mode` | Candidate selection mode: `indexed` or `exhaustive`. Default: `indexed`. |
| `--progress-every` | Progress reporting interval, in input records. |

Run the script's help output to see the options supported by your local copy:

```bash
python3 typo_scan.py --help
```

### Edit distance

The `--distance` option controls the maximum number of character edits allowed:

- `0`: Exact string match only.
- `1`: Up to one insertion, deletion, or substitution.
- `2`: Up to two edits.
- Higher values broaden detection and generally increase false positives and processing cost.

Example:

```bash
python3 typo_scan.py input.csv.gz brands.txt matches.csv --distance 2
```

Use the lowest distance that meets your detection requirements. A larger distance is not automatically better.

### Candidate modes

**Indexed mode** (`--candidate-mode indexed`) uses character-trigram overlap to shortlist brands before edit-distance verification. It is intended for production-scale scans, but candidate generation is heuristic. The `--max-candidates` cap can exclude a true candidate, and trigram filtering can miss some valid edit-distance matches.

**Exhaustive mode** (`--candidate-mode exhaustive`) compares each eligible candidate window against every eligible brand. It is substantially more expensive, but useful for testing indexed-mode recall on a representative sample.

Example benchmark:

```bash
python3 typo_scan.py sample.csv brands.txt exhaustive.csv \
    --workers 8 \
    --distance 1 \
    --candidate-mode exhaustive
```

Run indexed and exhaustive modes against the same sample and compare their result sets to estimate candidate-generation misses.

## Output fields

The output is a CSV file containing detected matches. Fields include:

| Field | Description |
|---|---|
| `input_row` | Logical CSV record number processed by the scanner. |
| `hostname` | Original hostname from the input. |
| `registrable_domain` | Registrable domain identified by suffix parsing. |
| `suffix` | Public suffix identified by `tldextract`. |
| `suspected_brand` | Brand from the configured brand list. |
| `detection_method` | Match classification, such as single-label fuzzy or split-label fuzzy. |
| `matched_substring` | Hostname text that matched the brand candidate. |
| `similarity_score` | RapidFuzz similarity score for the compared strings. |
| `edit_distance` | Levenshtein distance for the selected match. |
| `matched_labels` | DNS labels contributing to the match. |

`input_row` is a logical CSV record count, not necessarily a physical file line number. This distinction matters when CSV fields contain embedded newlines.

## How matching works

At a high level, the scanner:

1. Reads hostname records in bounded batches.
2. Parses hostnames into DNS labels and identifies the registrable domain and public suffix.
3. Builds candidate strings from individual labels and contiguous windows of adjacent labels.
4. Retrieves candidate brands using trigram indexing or exhaustive comparison.
5. Verifies candidates using Levenshtein distance and the configured score threshold.
6. Writes qualifying results to the output CSV.

Checking adjacent-label windows helps identify brand strings split across DNS labels. For example, the labels `micro`, `soft`, and `login` can be considered together as `microsoftlogin`.

The scanner does not establish whether a domain is registered by the brand owner, whether a site is active, or whether a hostname is being used maliciously. Those questions require additional enrichment and analysis.

## Performance and operational guidance

- Start with a representative sample before scanning the full dataset.
- Benchmark different `--workers` and `--batch-size` values. Storage throughput and decompression may limit scaling.
- Keep the brand list curated. Short or ambiguous brand names tend to generate noisy results.
- Use `--min-brand-length` to exclude very short names unless there is a specific reason to retain them.
- Use indexed mode for large-scale discovery, then compare it with exhaustive mode on samples to estimate candidate-generation misses.
- If the input contains many repeated hostnames, upstream deduplication may reduce total work. Preserve occurrence counts separately if frequency is analytically important.
- Keep the original input and scanner configuration with the results so findings can be reproduced.

## False positives and validation

This tool is designed for scalable candidate discovery; it does not provide a definitive malicious-domain verdict.

For higher-precision operational use, validate matches with additional signals, such as:

- Whether the registrable domain is controlled by the brand owner.
- DNS history, registration age, and nameserver or hosting changes.
- Certificate Transparency records and TLS certificate details.
- Website content, redirects, favicon or logo similarity, and login-page behavior.
- Email configuration and observed mail activity.
- Passive DNS, hosting relationships, and infrastructure reuse.
- Brand-specific allowlists and known legitimate subdomain patterns.

Calibrate `--distance`, `--min-score`, minimum brand length, and candidate-generation settings against a labeled dataset. Measure precision and recall separately; a high similarity score alone is not a reliable maliciousness indicator.

## Limitations

- The scanner does not currently perform dedicated Unicode homoglyph or IDN-confusable detection.
- Indexed candidate generation is heuristic and can miss matches; exhaustive mode is the comparison path when recall is more important than speed.
- A match across adjacent labels can be legitimate.
- Public suffix parsing depends on the `tldextract` snapshot available in the installed package.
- The scanner analyzes hostnames; it does not fetch websites or independently verify domain ownership or malicious activity.

## License

Add a license before distributing this project. If you intend others to reuse or modify the code, include the corresponding license file in the repository.
