# JellyRancher Workflow Specification

**Version:** 2.0  
**Date:** November 12, 2025  
**Status:** Active - PyQt6 Migration in Progress

---

## Program Specifications

- **Language:** Python 3.12
- **Application Type:** Desktop GUI Application
- **GUI Framework:** PyQt6
- **Virtual Environment:** `.venv/` in project root (always activated)
- **Target Platform:** Cross-platform (Windows, macOS, Linux)

---

## The 9-Point Workflow

### 1. Folder Scanning & Inventory

**Purpose:** Generate master file list for all operations

**Implementation:**
- Allow user to select multiple folders (add/remove from list)
- Recursively scan each folder
- Generate bare file inventory with absolute paths (one per row)
- Include all filetypes by default
- This master list is the foundation for all further actions

**Output:** List of absolute file paths

---

### 2. Hierarchical Overview

**Purpose:** Display folder structure with size metrics

**Implementation:**
- Generate hierarchical view of master list
- Show complete folder structure
- For each folder, display:
  - Total size
  - Breakdown by filetype (e.g., ".mkv: 178 files (240 GB)")
  - Individual files NOT listed at this stage

**Output:** Tree view with aggregated statistics

---

### 3. LLM Reorganization Proposal

**Purpose:** Get AI-generated restructuring plan

**Implementation:**
- Submit hierarchical folder structure to reasoning LLM
- LLM proposes Jellyfin-compliant reorganization
- Detects movies and TV shows from folder names
- Generates initial restructuring plan

**LLM Integration:**
- Use Claude API (via `anthropic` SDK) or Poe.com wrapper
- Provide context about Jellyfin naming conventions
- Request structured JSON output

**Output:** JSON with proposed file moves and renames

---

### 4. Metadata Database Building

**Purpose:** Build canonical metadata from authoritative sources

**Implementation:**

**Sources (in priority order):**
1. **TMDB** (movies) - via `tmdbv3api`
2. **TVDB** (TV shows) - via `tvdb_v4_official`
3. **Wikipedia** (fallback) - manual scraping

**Process:**
1. Use LLM-detected list with fuzzy matching (`rapidfuzz`)
2. Query APIs respecting rate limits:
   - TMDB: 40 requests per 10 seconds
   - TVDB: Current rate limits
   - Wikipedia: Conservative rates
3. Implement exponential backoff on errors (`tenacity`)
4. Cache all responses aggressively (SQLite or JSON files)

**Build Canonical Database With:**
- Correct movie years
- TV show names, years, season structure
- Episode titles and numbers
- **Special:** Multi-part episodes in single files (e.g., S01E01-E02.mkv)
  → Generate Jellyfin-compatible NFO files specifying episode ranges

**Rate Limiting Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)  # TMDB limit
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60)
)
def query_tmdb_safe(movie_name):
    # API call here
    pass
```

**Output:** Canonical metadata database (SQLite or JSON)

---

### 5. Editable Action Table

**Purpose:** User review and approval of all operations

**Implementation:**

**Color-Coded Categories:**
- 🟢 **Green (Auto-safe):** Perfect metadata match, high confidence
- 🟡 **Yellow (Review recommended):** Fuzzy match or minor ambiguity
- 🟠 **Orange (Manual decision):** Multiple matches or significant deviations
- 🔴 **Red (Cannot process):** No metadata match or corrupt filenames
- 🔵 **Blue (No action):** Already Jellyfin-compliant or duplicate

**Each Row Contains:**
- Source file path
- Proposed destination path
- Action type (move, rename, create NFO, etc.)
- Confidence level / color
- Metadata source (TMDB, TVDB, etc.)
- User override checkbox

**Features:**
- Editable cells for manual correction
- Dry-run mode to preview without execution
- Filter by color/action type
- Export to CSV for external review

**PyQt6 Implementation:**
```python
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor

item = QTableWidgetItem('movie.mkv')
if confidence == 'high':
    item.setBackground(QColor(200, 255, 200))  # Light green
table.setItem(row, col, item)
```

**Output:** Finalized action plan approved by user

---

### 6. Snapshot & Transaction Log

**Purpose:** Enable complete rollback of file operations

**Implementation:**

**Before Executing ANY File Operations:**

1. **Create Transaction Log** (SQLite recommended):

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    operation TEXT,  -- 'move', 'rename', 'create', 'delete'
    source_path TEXT,
    destination_path TEXT,
    source_md5 TEXT,
    destination_md5 TEXT,
    completed BOOLEAN DEFAULT 0,
    error TEXT
);
```

2. **For Each Operation:**
   - Log BEFORE execution
   - Calculate source MD5 (once, before move)
   - Execute operation
   - Verify with destination MD5
   - Update `completed = true`
   - If error: log error, skip file, continue

3. **MD5 Strategy:**
   - Calculate MD5 once before move
   - Verify after move
   - Don't recalculate on rollback (just reverse the move)

**Rollback Process:**
- Read transaction log in reverse chronological order
- For each completed operation:
  - Reverse the operation (move destination back to source)
  - Verify MD5 matches original
  - Mark as rolled back

**File Safety:**
- Use `send2trash` instead of permanent deletion
- Keep transaction logs for 30 days
- Generate rollback scripts for manual review

**Output:** Transaction log (SQLite database)

---

### 7. Execute Reorganization

**Purpose:** Perform approved file operations safely

**Implementation:**

**Execution Process:**
1. Validate all destination paths exist or can be created
2. Check for conflicts (existing files at destinations)
3. Execute operations in transaction log order
4. For each operation:
   - Move/rename file
   - Move subtitle files alongside
   - Rename subtitles per Jellyfin conventions
   - Verify MD5 after move
   - Update transaction log

**Subtitle Handling:**
- Move subtitle files (.srt, .ass, .sub, etc.) alongside video files
- Rename per Jellyfin conventions:
  - `movie.en.srt` (regular English subtitles)
  - `movie.en.forced.srt` (forced subtitles)
  - `show.S01E01.en.srt` (TV episode subtitles)

**Error Handling:**
- If operation fails: log error, skip file, continue processing
- Never leave partial operations
- Verify MD5 after each move
- Generate summary report:
  - Successful operations
  - Skipped files
  - Errors with details

**Output:** Reorganized files + transaction log + summary report

---

### 8. Subtitle Coverage Evaluation

**Purpose:** Identify files missing English subtitles

**Implementation:**

**Detection Strategy:**

1. **Embedded Subtitles** (using `ffmpeg-python`):
```python
import ffmpeg

probe = ffmpeg.probe('movie.mkv')
subtitle_streams = [
    s for s in probe['streams'] 
    if s['codec_type'] == 'subtitle'
]

for sub in subtitle_streams:
    lang = sub.get('tags', {}).get('language', '')
    forced = sub.get('disposition', {}).get('forced', 0)
    if lang == 'eng' or lang == 'en':
        # Has English subtitles
        pass
```

2. **External Subtitle Files:**
   - Scan for `.srt`, `.ass`, `.sub`, `.ssa` files
   - Match to video files by naming convention
   - Parse filename for language code (e.g., `.en.srt`)

**Evaluation Logic:**
```
IF (embedded English subs OR external English subs exist):
    Mark as "covered", SKIP
ELSE:
    Add to download list
```

**Distinguish:**
- Regular subtitles (full dialogue)
- Forced subtitles (only foreign language dialogue)

**Output:** List of files missing English subtitles

---

### 9. Subtitle Acquisition

**Purpose:** Download missing subtitles from multiple sources

**Implementation:**

**Use `subliminal` Library:**
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

**Sources (in order):**
1. **OpenSubtitles.org** (primary, requires credentials)
2. **OpenSubtitles.com** (fallback)
3. **Podnapisi.NET**
4. **Addic7ed.com**
5. **Subscene.com**

**Matching Strategy:**
1. **Hash-based matching** (most accurate)
   - Calculate video file hash
   - Query subtitle databases by hash
2. **Fuzzy filename matching** (fallback)
   - Use `rapidfuzz` to match filename
   - Score by similarity + metadata match

**Download Both:**
- Regular English subtitles
- Forced English subtitles (if available)

**Note:** Forced subtitles can be added even to files that already have regular subtitles

**Respect:**
- All API rate limits
- Terms of service for each provider
- Implement exponential backoff (`tenacity`)

**Output:** Downloaded subtitle files placed alongside videos

---

## Architecture & Design Decisions

### Why PyQt6?
- Mature, cross-platform
- Excellent table/tree widgets for action review (Point 5)
- Built-in threading (`QThread`) for background API calls
- Professional appearance

### Why Transaction Logs Instead of Git?
- File operations may span multiple commits
- Need atomic rollback of entire batch
- MD5 verification ensures data integrity
- Git tracks code, not file system state

### Why MD5 Instead of SHA256?
- "Good enough" for corruption detection
- 3x faster on large video files
- Not doing cryptography, just file integrity checks

### Why Separate Regular + Forced Subtitles?
- Jellyfin treats them differently
- Forced subtitles enhance viewing for foreign dialogue scenes
- Users want both when available

---

## Rules & Constraints

### 1. API Courtesy
- Respect all rate limits
- Implement exponential backoff
- Cache aggressively (30+ day cache for metadata)

### 2. User Control
- All destructive operations require explicit review
- Dry-run mode mandatory before execution
- Export action plan for external review

### 3. Jellyfin Compliance
- Follow official Jellyfin naming conventions
- NFO files must conform to Jellyfin's XML schema
- Folder structure must match Jellyfin expectations

### 4. Data Integrity
- Preserve original file paths in master inventory
- Never modify source files until user approves
- MD5 verification for all moves
- Transaction logs for complete rollback

### 5. Transparency
- Indicate confidence levels for all actions
- Show reasoning for AI decisions
- Flag ambiguous cases for manual review
- Generate detailed reports

### 6. Python Environment
- Always use virtual environment in project root
- Never execute without activating `.venv` first
- Keep requirements.txt up to date

---

## Success Metrics

You'll know the workflow is working when:

✅ You can scan a folder and see accurate file counts  
✅ Hierarchical view shows aggregated file sizes by type  
✅ LLM generates valid Jellyfin-compliant proposals  
✅ Metadata lookup succeeds with <5% failures  
✅ Action table displays with correct color coding  
✅ Dry-run mode shows accurate preview of changes  
✅ Execution completes without file corruption (MD5 verified)  
✅ Rollback successfully reverses all operations  
✅ Subtitle coverage evaluation finds all existing subs  
✅ Subtitle downloads succeed for 90%+ of missing files  

---

## Next Steps

See `ARCHITECTURE.md` for library choices and implementation details.  
See `MIGRATION_GUIDE.md` for PyQt6 migration instructions.  
See `API_USAGE.md` for TMDB/TVDB/subtitle provider integration.
