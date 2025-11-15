# JellyRancher Architecture Reference

**Version:** 2.0  
**Date:** November 12, 2025

---

## Overview

This document describes the architectural decisions and library choices for the JellyRancher Jellyfin media organizer. It answers: "What libraries should we use?" and "What must we build ourselves?"

---

## Libraries We're Using

### GUI Framework

**PyQt6** - Desktop GUI
```bash
pip install PyQt6>=6.6.0
```

**Why:** Mature, cross-platform, excellent widgets for tables/trees, built-in threading

**Usage Example:**
```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget
from PyQt6.QtCore import QThread

app = QApplication([])
window = QMainWindow()
window.show()
app.exec()
```

---

### API Wrappers

#### TMDB (The Movie Database)

**tmdbv3api** - Official TMDB wrapper
```bash
pip install tmdbv3api>=1.9.0
```

**Usage:**
```python
from tmdbv3api import TMDb, Movie

tmdb = TMDb()
tmdb.api_key = 'YOUR_API_KEY'
tmdb.language = 'en'

movie = Movie()
search = movie.search('The Matrix')
for result in search:
    print(result.title, result.release_date)
```

**Rate Limit:** 40 requests per 10 seconds

---

#### TVDB (TheTVDB)

**tvdb_v4_official** - Official TVDB v4 wrapper
```bash
pip install tvdb_v4_official>=1.0.0
```

**Usage:**
```python
from tvdb_v4_official import TVDB

tvdb = TVDB('YOUR_API_KEY')
results = tvdb.search('Breaking Bad')
series = tvdb.get_series(results[0]['tvdb_id'])
```

---

### Rate Limiting & Retry Logic

#### Tenacity - Exponential Backoff

```bash
pip install tenacity>=8.2.0
```

**Usage:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60)
)
def query_api_with_retry():
    # Automatically retries with 2s, 4s, 8s, 16s, 32s delays
    pass
```

---

#### Ratelimit - Simple Rate Limiting

```bash
pip install ratelimit>=2.2.1
```

**Usage:**
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)  # TMDB limit
def query_tmdb():
    # Automatically sleeps if rate limit exceeded
    pass
```

---

#### Combined Usage

**Best practice - combine both decorators:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)  # Rate limit
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60)  # Backoff
)
def query_tmdb_safe(movie_name):
    # Rate limited AND retries with backoff on errors
    pass
```

---

### Subtitle Handling

#### Subliminal - Multi-Provider Subtitle Downloader

```bash
pip install subliminal>=2.1.0
```

**Supports:**
- OpenSubtitles.org
- OpenSubtitles.com
- Podnapisi.NET
- Addic7ed.com
- Subscene.com
- TVSubtitles
- And more...

**Features:**
- Hash-based matching (most accurate)
- Fuzzy filename matching (fallback)
- Automatic language detection
- Subtitle scoring/ranking

**Usage:**
```python
from subliminal import download_best_subtitles, save_subtitles
from babelfish import Language

video = Video.fromname('movie.mkv')
subtitles = download_best_subtitles(
    {video}, 
    {Language('eng')},
    providers=['opensubtitles', 'podnapisi', 'addic7ed']
)
save_subtitles(video, subtitles[video])
```

**Distinguishing Forced Subtitles:**
Check subtitle metadata after download - forced flag may be available depending on provider.

---

#### FFmpeg-Python - Media File Analysis

```bash
pip install ffmpeg-python>=0.2.0
```

**Purpose:** Detect embedded subtitle tracks

**Usage:**
```python
import ffmpeg

probe = ffmpeg.probe('movie.mkv')
subtitle_streams = [
    stream for stream in probe['streams'] 
    if stream['codec_type'] == 'subtitle'
]

for sub in subtitle_streams:
    language = sub.get('tags', {}).get('language', 'unknown')
    forced = sub.get('disposition', {}).get('forced', 0)
    print(f"Subtitle: {language}, Forced: {bool(forced)}")
```

**Note:** Requires ffmpeg/ffprobe to be installed on system

---

### Fuzzy String Matching

#### RapidFuzz - Fast Fuzzy Matching

```bash
pip install rapidfuzz>=3.5.0
```

**Why:** 10-100x faster than fuzzywuzzy, same API

**Usage:**
```python
from rapidfuzz import fuzz, process

# Simple similarity ratio (0-100)
similarity = fuzz.ratio("The Matrix", "Matrix, The")

# Find best match from list
choices = ["The Matrix", "The Matrix Reloaded", "Matrix Revolutions"]
best_match = process.extractOne("matrix", choices)
print(best_match)  # ('The Matrix', 90.0, 0)

# Get top N matches
top_matches = process.extract("matrix", choices, limit=3)
```

**Use Cases:**
- Match messy filenames to clean TMDB/TVDB titles
- Detect duplicates with slight variations
- User input matching

---

### File Operations

#### Send2Trash - Safe Deletion

```bash
pip install send2trash>=1.8.2
```

**Why:** Moves to recycle bin instead of permanent deletion

**Usage:**
```python
from send2trash import send2trash

# Safe - goes to recycle bin
send2trash('file.mkv')

# Instead of:
# os.remove('file.mkv')  # Permanent, can't undo
```

---

### LLM Integration

#### Anthropic - Claude API

```bash
pip install anthropic>=0.18.0
```

**Usage:**
```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Analyze this folder structure..."}
    ]
)
print(message.content)
```

**Alternative:** Keep existing `ravenmaven_client.py` for Poe.com API

---

### Built-In Python Libraries (No Install Needed)

#### pathlib - Modern Path Handling

```python
from pathlib import Path

path = Path('/some/folder/file.mkv')
print(path.name)        # file.mkv
print(path.stem)        # file
print(path.suffix)      # .mkv
print(path.parent)      # /some/folder

# Portable path construction
new_path = path.parent / 'subfolder' / 'newfile.mkv'
```

**Use instead of:** `os.path.join()`, string concatenation

---

#### shutil - File Operations

```python
import shutil

# Copy file
shutil.copy2('source.mkv', 'dest.mkv')  # Preserves metadata

# Move file
shutil.move('source.mkv', 'dest.mkv')

# Copy entire directory tree
shutil.copytree('source_dir', 'dest_dir')
```

---

#### hashlib - MD5 Hashing

```python
import hashlib

def md5_hash_file(filepath, chunk_size=8192):
    """Calculate MD5 without loading entire file into memory"""
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()

# Usage
hash_before = md5_hash_file('movie.mkv')
# ... move file ...
hash_after = md5_hash_file('movie_new.mkv')
assert hash_before == hash_after, "File corrupted during move!"
```

---

#### sqlite3 - Transaction Log Storage

```python
import sqlite3

# Create transaction log database
conn = sqlite3.connect('transaction_log.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    operation TEXT,
    source_path TEXT,
    destination_path TEXT,
    source_md5 TEXT,
    completed BOOLEAN DEFAULT 0
)
''')

# Log operation
cursor.execute('''
INSERT INTO transactions (timestamp, operation, source_path, destination_path, source_md5)
VALUES (?, ?, ?, ?, ?)
''', (datetime.now().isoformat(), 'move', source, dest, md5_hash))

conn.commit()
```

---

#### json - Structured Data

```python
import json

# Save cache
cache = {'movie': {'title': 'The Matrix', 'year': 1999}}
with open('cache.json', 'w') as f:
    json.dump(cache, f, indent=2)

# Load cache
with open('cache.json', 'r') as f:
    cache = json.load(f)
```

---

## What We Must Build Ourselves

These features have **NO existing library** and must be custom-built:

### 1. ❌ Transaction Log System

**What:** Atomic file operation rollback for entire batches

**Why No Library:** No Python library does "move 500 files, then undo all 500 if one fails"

**Our Approach:**
- Use SQLite for transaction log (built-in)
- Log BEFORE execution
- Calculate MD5 before move
- Verify MD5 after move
- Rollback reverses operations in reverse order

**Reference:** Existing `jellyfin_safe_executor.py` has foundation

---

### 2. ❌ Jellyfin NFO File Generation

**What:** XML files for multi-part episodes

**Why No Library:** Jellyfin's NFO schema is specific, must write manually

**Example:**
```python
import xml.etree.ElementTree as ET

root = ET.Element('episodedetails')
ET.SubElement(root, 'title').text = 'Episode Title'
ET.SubElement(root, 'season').text = '1'
ET.SubElement(root, 'episode').text = '1'  # First episode in file
ET.SubElement(root, 'displayepisode').text = '1'
ET.SubElement(root, 'displayseason').text = '1'

tree = ET.ElementTree(root)
tree.write('episode.nfo', encoding='utf-8', xml_declaration=True)
```

---

### 3. ❌ Color-Coded Action Review Table

**What:** PyQt6 table with confidence-based color coding

**Why No Library:** Need custom business logic for color assignment

**Implementation:**
```python
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor

def add_action_row(table, file, action, confidence):
    row = table.rowCount()
    table.insertRow(row)
    
    item = QTableWidgetItem(file)
    
    # Color code by confidence
    if confidence == 'high':
        item.setBackground(QColor(200, 255, 200))  # Green
    elif confidence == 'medium':
        item.setBackground(QColor(255, 255, 200))  # Yellow
    else:
        item.setBackground(QColor(255, 200, 200))  # Red
    
    table.setItem(row, 0, item)
```

---

### 4. ❌ Hierarchical Folder Overview

**What:** Tree view with filetype aggregation

**Why No Library:** Custom aggregation logic needed

**Implementation:**
```python
from collections import defaultdict
from pathlib import Path

def build_folder_tree(file_list):
    tree = defaultdict(lambda: defaultdict(int))
    
    for filepath in file_list:
        path = Path(filepath)
        folder = str(path.parent)
        ext = path.suffix.lower()
        size = path.stat().st_size
        
        tree[folder][ext] += size
    
    return tree
```

---

### 5. ❌ LLM → Metadata Pipeline Integration

**What:** Parse LLM output → Query TMDB/TVDB → Build canonical database

**Why No Library:** Custom business logic connecting multiple APIs

**Flow:**
1. LLM generates proposals (JSON)
2. Extract movie/show names
3. Fuzzy match with `rapidfuzz`
4. Query TMDB/TVDB with rate limiting
5. Build canonical database
6. Generate action plan

---

## Complete requirements.txt

```txt
# GUI Framework
PyQt6>=6.6.0

# API Wrappers
tmdbv3api>=1.9.0
tvdb_v4_official>=1.0.0

# Rate Limiting & Retry
tenacity>=8.2.0
ratelimit>=2.2.1

# Subtitle Handling
subliminal>=2.1.0
ffmpeg-python>=0.2.0

# Fuzzy Matching
rapidfuzz>=3.5.0

# File Safety
send2trash>=1.8.2

# LLM Integration
anthropic>=0.18.0

# Built-in (no install):
# - pathlib
# - shutil
# - hashlib
# - sqlite3
# - json
# - xml.etree.ElementTree
```

---

## Common Questions

### Q: Should we use async/await?

**A:** Not initially. PyQt6's `QThread` is sufficient for background API calls. If performance becomes an issue, consider:
- `aiohttp` for async HTTP
- `aiolimiter` for async rate limiting
- `asyncio` for concurrent API calls

But start with simple threading first.

---

### Q: How do we handle large file moves?

**A:** Use `shutil.move()` with MD5 verification:
1. Calculate MD5 before move (chunked reading)
2. Move file
3. Calculate MD5 after move
4. Compare hashes

For very large files (>50GB), consider showing progress bar in GUI.

---

### Q: Should we use a database for metadata cache?

**A:** Yes - SQLite is built-in and perfect for this:

```python
# Create cache
conn = sqlite3.connect('metadata_cache.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS movies (
    title TEXT,
    year INTEGER,
    tmdb_id INTEGER,
    metadata TEXT,
    cached_at TEXT
)
''')

# Query cache before API
cursor.execute('SELECT metadata FROM movies WHERE title=? AND year=?', 
               (title, year))
result = cursor.fetchone()

if result:
    return json.loads(result[0])  # Cache hit
else:
    # Cache miss - query API
    pass
```

Benefits:
- Built-in to Python
- Fast lookups
- Easy SQL queries
- Can store JSON as TEXT

---

### Q: How do we test without modifying real files?

**A:** Use temporary directories:

```python
import tempfile
import shutil
from pathlib import Path

def test_file_operations():
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create test files
        (test_dir / 'movie.mkv').touch()
        (test_dir / 'movie.srt').touch()
        
        # Run operations
        # ...
        
        # Cleanup automatic on exit
```

---

## Next Steps

1. Install all dependencies: `pip install -r requirements.txt`
2. Verify ffmpeg is installed: `ffmpeg -version`
3. Get API keys for TMDB, TVDB, OpenSubtitles
4. Start with Point 1 (folder scanning) using `pathlib`
5. Build incrementally, testing each point

See `WORKFLOW_SPEC.md` for the complete 9-point workflow.
