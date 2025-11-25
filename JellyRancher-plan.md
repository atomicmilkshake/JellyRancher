### **Jellyfin Media Organizer: Polished Project Specification**

---

## **Application Purpose**
Prepare chaotic media libraries for Jellyfin by scanning, analyzing, reorganizing, and enriching files with metadata and subtitles—all with mandatory human review before execution.

---

## **Core Workflow (8 Steps)**

### **Step 1: Recursive File Scan**

**Objective:** Build a complete inventory of media files with integrity verification.

**Implementation Requirements:**
- Scan selected folder(s) recursively, outputting one complete file path per row
- **Compute MD5 hash for every file** during scan (integrity baseline + duplicate detection)
- **Filter by media extensions:** `.mkv`, `.mp4`, `.avi`, `.m4v`, `.srt`, `.ass`, `.sub`, etc.
- **Parallelize hashing** for performance (use thread pool, respect I/O limits)
- **Log scan errors:** Unreadable files, permission denied, filesystem errors

**Output Format (JSON):**
```json
{
  "scan_timestamp": "2025-01-15T14:30:00",
  "root_paths": ["/media/tv", "/media/movies"],
  "files": [
    {
      "path": "/media/tv/Star Trek TNG/Season 1/episode01.mkv",
      "size_bytes": 1073741824,
      "md5": "5d41402abc4b2a76b9719d911017c592",
      "extension": ".mkv",
      "modified_date": "2024-12-01T10:15:00"
    }
  ],
  "summary": {
    "total_files": 1523,
    "total_size_gb": 2048.5,
    "video_files": 1450,
    "subtitle_files": 73,
    "scan_duration_seconds": 185
  }
}
```

**Error Handling:**
- Skip (don't crash on) unreadable files; log them for user review
- Warn if MD5 computation is slow (>10 files/second indicates I/O bottleneck)

---

### **Step 2: Structural Summary**

**Objective:** Condense file inventory into hierarchical structure for LLM analysis—preserving context without overwhelming token limits.

**Implementation Requirements:**
- Group files by parent directory hierarchy
- Count video files per folder/subfolder
- Detect season folder patterns (`Season 1`, `S01`, `s01`, etc.)
- Calculate aggregate statistics (total size, video/subtitle ratio)

**Output Format (Text for LLM):**
```
📁 /media/tv/
  📁 Star Trek The Next Generation/ (178 videos, 42 subtitles, 256.3 GB)
    📁 Season 1/ (26 videos, 8 subtitles)
    📁 Season 2/ (22 videos, 10 subtitles)
    📁 Season 3/ (26 videos, 6 subtitles)
    📁 Season 4/ (26 videos, 5 subtitles)
    📁 Season 5/ (26 videos, 4 subtitles)
    📁 Season 6/ (26 videos, 5 subtitles)
    📁 Season 7/ (26 videos, 4 subtitles)
  📁 Battlestar Galactica/ (73 videos, 15 subtitles, 98.7 GB)
    📁 Season 1/ (13 videos, 3 subtitles)
    [...]

📁 /media/movies/
  📂 Action/ (87 videos, 23 subtitles, 145.2 GB)
  📂 Sci-Fi/ (54 videos, 12 subtitles, 89.1 GB)
  [...]
```

**Key Insight:** This summary is **human-readable AND LLM-optimized**. No filenames—just structure.

---

### **Step 3: LLM Proposal & Title Detection**

**Objective:** Get reorganization recommendations and extract detected media titles for metadata lookup.

**LLM Prompt Template:**
```
You are a media library organizer preparing files for Jellyfin. Analyze this structure:

[PASTE STEP 2 SUMMARY]

Tasks:
1. Propose a Jellyfin-compliant folder reorganization
2. List all detected TV shows and movies with confidence scores

Guidelines:
- TV shows: /TV Shows/{Show Name} ({Year})/Season {NN}/{Show Name} - S{NN}E{EE} - {Episode Title}.ext
- Movies: /Movies/{Movie Name} ({Year})/{Movie Name} ({Year}).ext
- Flag ambiguous cases (e.g., movies vs miniseries)
- Identify multi-part episodes (e.g., "Encounter at Farpoint Parts 1 & 2" in one file)

Output in this JSON structure:
{
  "reorganization_proposal": {
    "tv_shows": [
      {
        "current_path": "/media/tv/Star Trek TNG/",
        "proposed_path": "/media/TV Shows/Star Trek The Next Generation (1987)/",
        "rationale": "Standardize naming, add year for disambiguation"
      }
    ],
    "movies": [...]
  },
  "detected_titles": {
    "tv_shows": [
      {
        "title": "Star Trek: The Next Generation",
        "year": 1987,
        "confidence": 0.95,
        "notes": "Season 1 Episode 1-2 may be combined as 'Encounter at Farpoint'"
      }
    ],
    "movies": [...]
  }
}
```

**Implementation Notes:**
- **Pre-clean folder names** before sending to LLM: `Star.Trek.TNG.1080p.BluRay` → `Star Trek TNG`
- **Validate LLM output** against regex patterns (don't blindly trust it)
- **Use rule-based detection first** for obvious cases (S01E05 patterns), LLM for ambiguous ones
- **Cache LLM responses** by folder structure hash (don't re-query identical structures)

**Error Handling:**
- If LLM returns invalid JSON, retry with more explicit formatting instructions
- If LLM hallucinates (invents episodes), validation in Step 4 will catch it

---

### **Step 4: Canonical Database Construction**

**Objective:** Query authoritative metadata sources to build ground truth for all detected media.

**Metadata Sources:**
- **Movies:** TMDb API (free, well-documented)
- **TV Shows:** TMDb API or TVDb (TMDb now has comprehensive TV data)
- **Anime:** AniDB or AniList (essential for accurate anime metadata)

**Database Schema (SQLite):**
```sql
-- Movies Table
CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER NOT NULL,
    tmdb_id INTEGER UNIQUE,
    imdb_id TEXT,
    runtime_minutes INTEGER,
    poster_url TEXT,
    nfo_generated BOOLEAN DEFAULT 0
);

-- TV Shows Table
CREATE TABLE tv_shows (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER NOT NULL,
    tmdb_id INTEGER UNIQUE,
    tvdb_id INTEGER,
    total_seasons INTEGER,
    poster_url TEXT
);

-- Episodes Table
CREATE TABLE episodes (
    id INTEGER PRIMARY KEY,
    show_id INTEGER REFERENCES tv_shows(id),
    season_number INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    title TEXT,
    air_date DATE,
    multi_part_group TEXT,  -- e.g., "Encounter_at_Farpoint" for linked episodes
    runtime_minutes INTEGER,
    nfo_generated BOOLEAN DEFAULT 0,
    UNIQUE(show_id, season_number, episode_number)
);

-- File Mapping Table (links files to canonical entries)
CREATE TABLE file_mappings (
    id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    md5 TEXT NOT NULL,
    media_type TEXT CHECK(media_type IN ('movie', 'episode')) NOT NULL,
    movie_id INTEGER REFERENCES movies(id),
    episode_id INTEGER REFERENCES episodes(id),
    proposed_path TEXT,
    action TEXT CHECK(action IN ('move', 'delete', 'merge', 'do_nothing', 'review')) DEFAULT 'review',
    user_modified BOOLEAN DEFAULT 0
);

-- Subtitle Inventory Table
CREATE TABLE subtitles (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    md5 TEXT NOT NULL,
    language TEXT,
    format TEXT,  -- 'srt', 'ass', 'embedded'
    is_forced BOOLEAN DEFAULT 0,
    parent_video_path TEXT REFERENCES file_mappings(file_path)
);
```

**Multi-Part Episode Handling:**
- If LLM flags "Encounter at Farpoint" as single file containing episodes 1+2:
  - Create two rows in `episodes` table (S01E01, S01E02)
  - Set `multi_part_group = 'Encounter_at_Farpoint'` for both
  - Generate NFO with `<episodebookmark>` tags for Jellyfin

**NFO Generation Example (Multi-Part):**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
  <title>Encounter at Farpoint</title>
  <showtitle>Star Trek: The Next Generation</showtitle>
  <season>1</season>
  <episode>1</episode>
  <displayseason>1</displayseason>
  <displayepisode>1-2</displayepisode>
  <plot>Combined pilot episode featuring parts 1 and 2.</plot>
  <aired>1987-09-28</aired>
  <studio>Paramount</studio>
</episodedetails>
```

**Conflict Resolution:**
- If TMDb says Season 1 has 26 episodes but you detect 24 files:
  - Flag as `action='review'` in `file_mappings`
  - Show user the discrepancy in Step 5's table

**Error Handling:**
- Rate-limit TMDb API calls (40 requests/10 seconds for free tier)
- Cache metadata locally (don't re-query for same title)
- Handle 404s gracefully (some shows aren't in TMDb; flag for manual research)

---

### **Step 5: Review Table Generation**

**Objective:** Present user with an editable, actionable plan derived from Steps 3-4.

**Table Columns:**
| Current Path | MD5 | Proposed Path | Metadata Match | Action | Conflicts | Notes |
|--------------|-----|---------------|----------------|--------|-----------|-------|
| `/media/tv/Star Trek TNG/Season 1/episode01.mkv` | `5d41402a...` | `/media/TV Shows/Star Trek The Next Generation (1987)/Season 01/Star Trek The Next Generation - S01E01-02 - Encounter at Farpoint.mkv` | ✅ TMDb S01E01-02 | `move` | Multi-part episode | NFO required |
| `/media/movies/Inception.2010.1080p.mkv` | `abc12345...` | `/media/Movies/Inception (2010)/Inception (2010).mkv` | ✅ TMDb | `move` | None | — |
| `/media/tv/Duplicate.Show.S01E01.mkv` | `xyz98765...` | — | ❌ No match | `delete` | Duplicate MD5 detected | Same file exists in proper location |

**Actions (User-Selectable):**
- `move`: Rename and relocate file (default for clean matches)
- `delete`: Remove file (for duplicates or junk)
- `merge`: Combine files (for split multi-part episodes detected separately)
- `do_nothing`: Keep file as-is in current location
- `review`: Flag for manual inspection (ambiguous metadata, conflicts)

**UI Requirements:**
- **Sortable/filterable:** By action, conflict status, media type
- **Bulk operations:** "Mark all duplicates for deletion", "Move all clean matches"
- **Inline editing:** User can change proposed path or action
- **Conflict highlighting:** Red rows for unresolved issues, yellow for warnings

**Implementation Format:**
- Export table as CSV/JSON for portability
- Persist user edits back to `file_mappings` table in database
- Generate execution plan only after user approves (clicks "Finalize Plan")

---

### **Step 6: Execution with Verification**

**Objective:** Safely execute approved plan with rollback capability and comprehensive logging.

**Execution Sequence (Per File):**
```
1. Pre-flight checks:
   - Verify source file exists and MD5 matches database
   - Check destination path is valid (filesystem limits, special chars)
   - Verify sufficient disk space at destination

2. Copy operation:
   - Copy (don't move) source → destination
   - If video file: check for related subtitle files
     - Pattern: {video_basename}.{lang}.srt, {video_basename}.{lang}.forced.srt
     - Copy subtitles using same naming pattern at destination

3. Verification:
   - Compute MD5 of destination file
   - Compare destination MD5 to source MD5
   - If mismatch: Delete destination, log error, STOP execution

4. Commit (only if verification passes):
   - Delete source file
   - Update file_mappings.file_path to new location
   - Log operation to journal

5. Handle failures:
   - On any error: Log to error journal, mark file as 'failed'
   - Continue with next file (don't abort entire job)
```

**Subtitle Naming (Jellyfin Standard):**
```
Movie.mkv
Movie.en.srt           # English subtitle
Movie.en.forced.srt    # Forced English (foreign language parts only)
Movie.es.srt           # Spanish subtitle

Show Name - S01E01.mkv
Show Name - S01E01.en.srt
Show Name - S01E01.en.forced.srt
```

**Operation Journal (SQLite Table):**
```sql
CREATE TABLE operation_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    file_path_source TEXT NOT NULL,
    file_path_dest TEXT,
    md5_source TEXT NOT NULL,
    md5_dest TEXT,
    action TEXT NOT NULL,  -- 'move', 'delete', 'copy'
    status TEXT NOT NULL,  -- 'pending', 'success', 'failed', 'rolled_back'
    error_message TEXT,
    related_subtitles TEXT  -- JSON array of subtitle paths moved
);
```

**Rollback Capability:**
- `--resume` flag: Skip files with status='success', retry status='failed'
- `--rollback` flag: Reverse all operations (copy dest → source, delete dest)
- Rollback only possible if source files weren't deleted (verify first!)

**Dry-Run Mode:**
- `--dry-run` flag: Log all actions without executing
- Output detailed preview: "Would move 1,523 files, delete 47 duplicates, total 2.1 TB"

**Post-Execution (Optional):**
- Trigger Jellyfin library refresh via API: `POST /Library/Refresh`
- Generate summary report: files moved, errors encountered, disk space freed

---

### **Step 7: Subtitle Coverage Audit**

**Objective:** Identify which media files lack subtitles (embedded or external).

**Detection Methods:**
1. **External subtitles:** Check for `.srt`, `.ass`, `.sub` files matching video basename
2. **Embedded subtitles:** Use `ffprobe` or `MediaInfo` to query subtitle streams

**ffprobe Command:**
```bash
ffprobe -v quiet -print_format json -show_streams "video.mkv"
```

**Parse JSON Output:**
```json
{
  "streams": [
    {"codec_type": "video", ...},
    {"codec_type": "audio", ...},
    {
      "codec_type": "subtitle",
      "codec_name": "subrip",
      "tags": {
        "language": "eng",
        "title": "English"
      }
    }
  ]
}
```

**Validation Criteria:**
- Subtitle exists (external file OR embedded stream)
- Language is identified (not "und" or "unknown")
- Codec is text-based (SubRip, ASS, WebVTT—skip VobSub/PGS if text required)

**Audit Report (Store in Database):**
```sql
UPDATE file_mappings
SET subtitle_status = CASE
    WHEN (external_sub_count + embedded_sub_count) = 0 THEN 'missing'
    WHEN language = 'und' THEN 'unknown_language'
    WHEN codec IN ('dvd_subtitle', 'hdmv_pgs_subtitle') THEN 'image_based'
    ELSE 'ok'
END;
```

**Output for User:**
```
Subtitle Coverage Report:
- 1,245 files with English subtitles ✅
- 178 files with unknown language 🟡
- 87 files with NO subtitles ❌
- 13 files with image-based subs only 🟡

Missing Subtitles (87 files):
  /media/TV Shows/Star Trek TNG (1987)/Season 01/S01E15.mkv
  /media/Movies/Inception (2010)/Inception (2010).mkv
  [...]
```

---

### **Step 8: Subtitle Acquisition**

**Objective:** Fetch missing subtitles from external sources.

**Subtitle Sources (Prioritized):**
1. **OpenSubtitles.org** (hash-based matching, requires free account)
2. **Subscene** (filename matching, web scraping required)
3. **Addic7ed** (TV shows, web scraping required)

**Matching Strategy:**
1. **Hash-based (best):** Compute video file hash using OpenSubtitles algorithm
2. **Metadata-based (fallback):** Query using TMDb ID + season/episode
3. **Filename-based (last resort):** Search using cleaned filename

**Language Preferences:**
- User specifies: "English (priority 1), Spanish (priority 2)"
- Download all available languages or only preferred?

**Post-Download:**
1. Save subtitle to proper location: `{video_basename}.{lang}.srt`
2. Verify subtitle file is valid (not empty, correct encoding)
3. Update `subtitles` table in database
4. Trigger Jellyfin refresh for that specific item (optional)

**Error Handling:**
- If no subtitle found: Log as `subtitle_status='unavailable'`
- If multiple matches: Present options to user (don't auto-select)
- If download fails: Retry 3 times with exponential backoff

---

## **Safety & Resilience**

### **Mandatory Features:**
1. **Dry-run mode** (`--dry-run`): Preview all operations without executing
2. **Operation logging**: SQLite journal of every file operation with timestamps
3. **MD5 verification**: Pre/post move hash comparison; rollback on mismatch
4. **Atomic operations**: Copy → Verify → Delete source (never move directly)
5. **Resume capability** (`--resume`): Skip completed operations, retry failed ones
6. **Rollback capability** (`--rollback`): Reverse all operations if Jellyfin doesn't recognize structure

### **User Control Gates:**
- **Step 3 → 4:** User must approve LLM's detected titles before metadata lookup
- **Step 5 → 6:** User must review and finalize table before execution
- **Step 6:** User must explicitly start execution (no auto-start)

---

## **Deferred to Post-MVP (Phase 2+)**

**Do NOT implement in initial version:**
- Jellyfin plugin mode (real-time file monitoring)
- Advanced analytics dashboards
- Integration with *arr suite (Sonarr, Radarr)
- Trakt/Ani-Sync scrobbling
- Theme song downloads (Themerr)
- Automated scheduling/cron jobs

**Rationale:** These are valuable extensions but add complexity and maintenance burden. Ship a working core workflow first, then iterate.

---

## **Technology Stack Recommendations**

**Core:**
- **Language:** Python 3.11+ (async I/O for performance)
- **Database:** SQLite (bundled, zero-config, perfect for local apps)
- **GUI:** PyQt6 (native look, cross-platform)
- **Hashing:** `hashlib.md5()` with threading
- **Metadata:** `requests` + TMDb API wrapper

**Media Analysis:**
- **Metadata extraction:** `pymediainfo` (more reliable than ffprobe for complex formats)
- **Subtitle parsing:** `pysrt` (validate downloaded subs)

**Testing:**
- **Unit tests:** `pytest` for core logic
- **Integration tests:** Test on real media library (not just synthetic data)

---

## **Success Criteria**

**MVP is complete when:**
1. ✅ User can scan 10,000+ files in <5 minutes (with MD5 hashing)
2. ✅ LLM proposal generates valid, Jellyfin-compliant paths
3. ✅ Canonical database matches TMDb metadata with 95%+ accuracy
4. ✅ Review table allows full manual override of any proposed action
5. ✅ Execution safely moves files with MD5 verification and rollback
6. ✅ Subtitle audit correctly identifies missing/embedded subs
7. ✅ Subtitle fetching works for at least OpenSubtitles source

**Jellyfin Integration Test:**
- After execution, Jellyfin recognizes all media without manual intervention
- Multi-part episodes display correctly (via NFO files)
- Subtitles are selectable in Jellyfin player

---

## **Next Immediate Action**

**Before writing code:**
1. **Create database schema** (run the SQL above in SQLite to create `organizer.db`)
2. **Test TMDb API** (write throwaway script to query your actual media titles)
3. **Mock Step 5 table** (create CSV with 10-20 sample rows to validate column design)

**First code to write:**
- `scan.py`: Implement Step 1 (recursive scan + MD5)
- Test on your real library: Does it handle 10,000+ files without crashing?
- Benchmark: How long does full scan take? (Target: <5 min for 10K files)

**Then proceed sequentially:** Step 2 → 3 → 4 → 5 → 6 → 7 → 8

Do not skip ahead. Each step depends on the previous.