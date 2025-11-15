#!/usr/bin/env python3
"""
Fetch and parse the "Complete LT/MM Filmography" (erictb.info/ltmm.html) and
produce a chronological JSON file containing each short's canonical title and
release year/date suitable for the project's manual Looney Tunes cache.

Output: scripts/._state/tv_episode_cache/looney_tunes_from_erictb.json

This script is conservative (falls back to the filmography text if parsing
fails) and stores each short with:
- global_index (chronological counter)
- title
- year (or full date if available)
- source_url

Run in the project's virtual environment.
"""
import json
import os
import re
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    raise

URL = "http://www.erictb.info/ltmm.html"
OUT_DIR = os.path.join(os.path.dirname(__file__), '._state', 'tv_episode_cache')
OUT_PATH = os.path.join(OUT_DIR, 'looney_tunes_from_erictb.json')

os.makedirs(OUT_DIR, exist_ok=True)

print(f"Fetching {URL}...")
resp = requests.get(URL, timeout=30)
resp.raise_for_status()
html = resp.text

soup = BeautifulSoup(html, 'html.parser')
# The page is mostly plain text with year headings and list items. We'll extract
# lines and find year headings (e.g., "1930 — 5 titles") and lines beginning
# with numbers or underscores.
text = soup.get_text('\n')
lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

entries = []
current_year = None
global_index = 0

# Regex patterns
year_heading_re = re.compile(r'^(\d{4})(?:\s*—|\s*-|\s*—).*')
# Matches lines like "1. (LT) Sinkin' in the Bathtub (Harman and Ising/1st LT-Apr/LTGC-3) —Bosko, Honey"
item_re = re.compile(r'^(?:\d+\.|____|\d+\.)?\s*(?:\(.*?\))?\s*(?P<title>[^\(\u2014\-–—\n]+)(?:[\(\u2014\-–—].*)?$')
# fallback pattern for lines like "Sinkin' in the Bathtub"
fallback_title_re = re.compile(r"^____\s*(?P<title>.+)$")

for ln in lines:
    # Year headings
    m = year_heading_re.match(ln)
    if m:
        current_year = m.group(1)
        continue
    # Some lines are like "1930 — 5 titles" left in text; skip if not a title
    if ln.lower().startswith('misc.') or ln.lower().startswith('private snafu'):
        current_year = None
        continue
    # Extract titles from lines that start with numbering or underscores
    m2 = item_re.match(ln)
    if m2 and current_year:
        title = m2.group('title').strip()
        # Clean trailing slashes or editorial notes
        title = re.sub(r"\s+--.*$","",title)
        title = title.rstrip(' .-–—')
        # Attempt to find a date in the line
        date_search = re.search(r"/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(\d{1,2})?\s*(?:/|\))?", ln, re.I)
        # Also look for explicit day in formats like "Sep 5" or "Jan 13"
        day_search = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})", ln)
        year = current_year
        date = None
        if day_search:
            date = f"{current_year}-{datetime.strptime(day_search.group(1), '%b').month:02d}-{int(day_search.group(2)):02d}"
        # increment global index
        global_index += 1
        entries.append({
            'global_index': global_index,
            'title': title,
            'year': year,
            'date': date,
            'source': URL
        })
        continue
    # fallback lines starting with underscores
    m3 = fallback_title_re.match(ln)
    if m3 and current_year:
        title = m3.group('title').strip()
        global_index += 1
        entries.append({
            'global_index': global_index,
            'title': title,
            'year': current_year,
            'date': None,
            'source': URL
        })
        continue

print(f"Parsed {len(entries)} entries; writing {OUT_PATH}...")
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({'count': len(entries), 'source': URL, 'entries': entries}, f, indent=2, ensure_ascii=False)

print('Done.')
