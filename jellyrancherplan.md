# Jellyfin Media Organizer - Application Specification

## Core Workflow

### **1. Scan Media Folders**
Recursively scan one or more selected folders to produce a complete file inventory.

**Output Requirements:**
- One file path per row (complete, absolute paths)
- Include file metadata: size, modification date
- Compute MD5 hash for each file (enables duplicate detection and integrity verification)
- Filter by media types: video files (`.mkv`, `.mp4`, `.avi`, etc.) and subtitle files (`.srt`, `.ass`, `.sub`)

**Error Handling:**
- Log inaccessible files (permission denied, corrupt files)
- Skip system folders and hidden directories by default

---

### **2. Generate Structure Summary**
Transform the raw file list into a hierarchical summary suitable for LLM analysis.

**Summary Format:**
```
/media/tv/Star Trek The Next Generation/
  ├── Season 1/ (26 videos, 18 subtitles)
  ├── Season 2/ (22 videos, 20 subtitles)
  ├── Season 3/ (26 videos, 26 subtitles)
  └── [Loose files]/ (4 videos)
  
/media/movies/
  ├── Action/ (47 movies)
  ├── Drama/ (23 movies)
  └── [Unsorted]/ (156 movies)
```

**Key Metrics per Folder:**
- Total video count
- Total subtitle count
- Total size (GB)
- Folder depth and hierarchy

**Rationale:** LLMs cannot process 10,000 individual filenames efficiently. The summary provides structural context without overwhelming the model's context window.

---

### **3. LLM Analysis & Reorganization Proposal**
Submit the structure summary to a reasoning-capable LLM (Claude Opus, GPT-4, etc.) for analysis.

**LLM Tasks:**
1. **Detect Media Titles:** Extract movie names and TV show names from folder/file names
2. **Propose Reorganization:** Suggest folder structure aligned with Jellyfin best practices
3. **Identify Anomalies:** Flag potential duplicates, misplaced files, or unclear naming

**LLM Output Format:**
(JSON structure with detected_titles, reorganization_proposal, and anomalies)

**Guardrails:**
- Validate LLM-detected titles against known patterns (e.g., `S01E05` regex)
- Flag low-confidence detections for manual review
- Cache LLM responses to avoid redundant API calls on re-runs

---

### **4. Build Canonical Metadata Database**
Query authoritative metadata sources to create a ground-truth database of all detected media.

**Data Sources (in priority order):**
1. **TMDb API** (The Movie Database) - Movies and TV shows
2. **TVDb API** (TheTVDB) - TV shows (fallback/supplement)
3. **AniDB API** - Anime-specific metadata

**Database Schema (SQLite):**
Tables for movies, shows, episodes, and file_mappings with appropriate foreign keys and constraints.

**Multi-Part Episode Handling:**
- Detect multi-part episodes via episode titles (e.g., "Part 1", "Part 2") or runtime (>80 minutes)
- Assign `multi_part_group` identifier to link related episodes
- Generate NFO file specifying correct episode numbering

**NFO Example (for Encounter at Farpoint feature-length file):**
XML episodedetails with displayepisode spanning multiple episodes (e.g., 1-2)

**Conflict Resolution:**
- If metadata sources disagree (e.g., different episode counts), prioritize TMDb
- Flag conflicts for user review

---

### **5. Generate Review Table**
Combine the canonical database with the LLM's reorganization proposal to produce an actionable review table.

**Table Columns:**
Current Path | Proposed Path | Media Title | Action | Metadata Match | Conflicts | MD5 Hash

**Available Actions:**
- `move` - Rename and relocate to proposed path
- `delete` - Remove file (for duplicates or junk files)
- `merge` - Combine multi-part episodes into single entry with NFO
- `skip` - Do nothing (keep file as-is)
- `review` - Flag for manual inspection

**UI Requirements:**
- Sortable and filterable (by action, media type, conflict status)
- Bulk edit operations ("Mark all duplicates for deletion")
- Export to CSV for external review/editing
- Import edited CSV back into application

**Validation:**
- Warn if proposed paths would overwrite existing files
- Check disk space availability for moves
- Flag files with no metadata match

---

### **6. Execute Organization Plan**
Execute the finalized, user-approved organization plan with full safety measures.

**Execution Workflow (per file):**
1. **Pre-Move Verification:**
   - Verify source file exists and is readable
   - Check MD5 hash matches database record
   - Verify destination path doesn't exist (prevent overwrites)
   - Check sufficient disk space at destination

2. **Copy-Verify-Delete Pattern:**
   - Copy source to destination
   - Verify destination MD5 matches source MD5
   - Only then delete source
   - **Never** rename files in-place or use direct move operations

3. **Subtitle Handling:**
   - Detect subtitle files matching video file name
   - Copy subtitles alongside video file
   - Rename according to Jellyfin conventions

4. **NFO Generation:**
   - Create NFO files for multi-part episodes
   - Place NFO adjacent to video file
   - Follow Jellyfin NFO format specifications

5. **Operation Logging:**
   - Log every operation to SQLite journal
   - Record: timestamp, original path, destination path, action, MD5 hashes, result

**Safety Features:**
- `--dry-run` mode: Log all operations without executing
- Atomic operations: All-or-nothing for multi-file moves (video + subtitles)
- Rollback capability: Keep operation log to enable undo
- Progress tracking: Resume after interruption

**Error Handling:**
- If any verification fails (MD5 mismatch, disk full), abort operation for that file
- Log error details
- Continue with remaining files
- Generate error report at completion

---

### **7. Audit Subtitle Coverage**
Analyze all media files to determine subtitle availability and quality.

**Audit Process:**
1. **Detect Subtitles:**
   - External: Check for `.srt`, `.ass`, `.sub` files matching video filename
   - Embedded: Use `ffprobe` to inspect video file streams for subtitle tracks

2. **Validate Subtitle Quality:**
   - **Language Identification:** Confirm language matches expected
   - **Format Check:** Ensure codec is text-based (SubRip, ASS, WebVTT)
   - **Encoding Validation:** Verify file is UTF-8 encoded and not corrupted
   - **Sync Check:** Optionally verify subtitle timing isn't drastically off

3. **Generate Report:**
   Summary with total files, complete coverage, missing subtitles, and quality issues

**Output Formats:**
- Summary report (text/HTML)
- Detailed CSV with file paths and subtitle status
- Prioritized fetch list (files needing subtitles)

---

### **8. Fetch Missing Subtitles**
Automatically download subtitles for files identified in Step 7's audit.

**Subtitle Sources (in priority order):**
1. **OpenSubtitles API** - Hash-based matching (most accurate)
2. **Subscene** - Filename matching (requires web scraping)
3. **Addic7ed** - TV shows, release-specific (requires web scraping)

**Matching Strategy:**
1. **Hash-based (preferred):** Compute video file hash, query API
2. **Metadata-based (fallback):** Query using TMDb/TVDb IDs + season/episode
3. **Filename-based (last resort):** Search using cleaned filename

**Download Workflow:**
1. Query subtitle source with file identifiers
2. Filter results by language preference, hearing impaired flag, release match
3. Download highest-rated subtitle
4. Save with Jellyfin-compliant naming
5. Validate downloaded file (not empty, valid UTF-8)

**User Configuration:**
Preferred languages, include SDH/forced, auto-download toggle, source API keys

**Post-Download Actions:**
- Re-run Step 7 audit to verify coverage improved
- Log all downloads to database
- Generate summary of download success rate

---

## Post-MVP Enhancements (Deferred)

These features should **not** be included in the initial release but may be added as separate modules/plugins:

- Jellyfin API integration (trigger library refreshes)
- Duplicate detection via perceptual hashing (for different encodes of same video)
- Integration with *arr suite (Sonarr, Radarr) for ongoing automation
- Trakt/AniList sync for watched status
- Advanced analytics and reporting
- Plugin/extension system for additional metadata sources