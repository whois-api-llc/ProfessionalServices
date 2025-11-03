#!/usr/bin/env python3
# usage: python hunt_txt.py domains.txt

# top_hashes_top_spf_cohorts.py

import sys, subprocess, hashlib, re, unicodedata
from collections import defaultdict

ESC = re.compile(r'\\([0-9]{1,3})')
def decode_mixed_escapes(s):
    def de(m):
        n = m.group(1)
        if any(c in '89' for c in n): return chr(int(n,10))
        o, d = int(n,8), int(n,10)
        c = o if (o < 256 and (o in (9,10,13) or 32 <= o < 127)) else d
        return chr(c)
    s = ESC.sub(de, s)
    s = s.replace('\u00A0',' ').replace('\u200B',' ').replace('\ufeff',' ')
    return unicodedata.normalize('NFKC', s)

def pull_txt(domain):
    out = subprocess.run(['dig','+short','TXT',domain], capture_output=True, text=True).stdout
    return out.strip().replace('"','')

ip_re = re.compile(r'\b((25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}(25[0-5]|2[0-4]\d|1?\d{1,2})\b')
clusters, ips = defaultdict(list), defaultdict(list)

for d in map(str.strip, open(sys.argv[1])):
    raw = pull_txt(d)
    norm = ' '.join(decode_mixed_escapes(raw).lower().split())
    h = hashlib.sha1(norm.encode()).hexdigest()
    clusters[h].append(d)
    for ip in ip_re.findall(norm):
        ips[ip[0]].append(d)

print('[Top TXT-hash cohorts]')
for h, ds in sorted(clusters.items(), key=lambda kv: len(kv[1]), reverse=True)[:10]:
    print(len(ds), h, ds[:10])

print('\n[Top SPF ip4: cohorts]')
for ip, ds in sorted(ips.items(), key=lambda kv: len(kv[1]), reverse=True)[:10]:
    print(len(ds), ip, ds[:10])
