# JELLYRANCHER PROJECT KNOWLEDGE PACK
Generated: 2025-11-12

================================================================================
CRITICAL CONTEXT: WHERE YOU ARE RIGHT NOW
================================================================================

You're building a **Jellyfin media organizer** but suffering from:
- **LLM amnesia** (context loss across sessions)
- **Code duplication** (same files in 6+ locations)
- **Structural chaos** (800MB .git, nested sub-projects, scattered ChromaDB instances)

You're about to **start fresh** using the 9-point workflow below as your foundation.

================================================================================
YOUR 9-POINT WORKFLOW (MASTER SPEC)
================================================================================

PROGRAM SPECIFICATIONS:
-----------------------
- Language: Python 3.12
- Application Type: GUI application
- GUI Framework: PyQt6
- Virtual Environment: Must be in project root, always activated
- Target Platform: Cross-platform (Windows, macOS, Linux)

WORKFLOW:
---------

1. FOLDER SCANNING & INVENTORY
   Allow user to select folders (add/remove from list). Recursively scan each 
   folder to generate a bare file inventory with absolute paths (one per row). 
   Include all filetypes by default. This master list is the foundation for all 
   further actions.

2. HIERARCHICAL OVERVIEW
   Generate a hierarchical view of the master list showing complete folder 
   structure. For each folder, display total size and breakdown by filetype 
   (count + aggregate size, e.g., ".mkv: 178 files (240 GB)"). Individual 
   files are NOT listed at this stage.

3. LLM REORGANIZATION PROPOSAL
   Submit hierarchical folder structure to a reasoning LLM to:
   - Propose Jellyfin-compliant reorganization
   - Detect movies and TV shows from folder names
   - Generate initial restructuring plan

4. METADATA DATABASE BUILDING
   Use LLM-detected list with fuzzy matching to query:
   - TMDB (movies)
   - TVDB (TV shows)
   - Wikipedia (fallback)
   
   Build canonical database with:
   - Correct movie years
   - TV show names, years, season structure
   - Episode titles and numbers
   - For multi-part episodes in single files (e.g., S01E01-E02.mkv), 
     generate Jellyfin-compatible NFO files specifying episode ranges
   
   Respect API rate limits:
   - TMDB: 40 requests per 10 seconds
   - TVDB: Current rate limits
   - Wikipedia: Conservative rates
   - Implement exponential backoff on errors
   - Cache all responses aggressively

5. EDITABLE ACTION TABLE
   Using canonical database + LLM proposal, generate editable table for user 
   review. Each row has:
   
   Color-coded action categories:
   - 🟢 Green (Auto-safe): Perfect metadata match, high confidence
   - 🟡 Yellow (Review recommended): Fuzzy match or minor ambiguity
   - 🟠 Orange (Manual decision needed): Multiple matches or significant deviations
   - 🔴 Red (Cannot process): No metadata match or corrupt filenames
   - 🔵 Blue (No action): Already Jellyfin-compliant or duplicate
   
   Include dry-run mode to preview all operations without execution.

6. SNAPSHOT & TRANSACTION LOG
   Before executing ANY file operations:
   
   Create transaction log (JSON or SQLite) logging each operation BEFORE execution:
```

```json
{
  "timestamp": "2025-11-12T10:30:15",
  "operation": "move",
  "source": "/old/path/file.mkv",
  "destination": "/new/path/file.mkv",
  "source_md5": "abc123...",
  "completed": false
}
```

```markdown
   After successful operation:
   - Update completed: true
   - Add destination_md5
   
   MD5 Strategy:
   - Calculate MD5 once before move
   - Verify after move
   - Don't recalculate on rollback (just reverse the move)
   
   Rollback: Reverse operations in reverse chronological order using the 
   transaction log.

7. EXECUTE REORGANIZATION
   Execute the finalized plan with:
   
   Subtitle handling:
   - Move subtitle files alongside video files
   - Rename per Jellyfin conventions (e.g., movie.en.srt, movie.en.forced.srt)
   
   Error handling:
   - If operation fails: log error, skip file, continue processing
   - Verify MD5 after each move
   - Generate summary report: successful ops, skipped files, errors

8. SUBTITLE COVERAGE EVALUATION
   Evaluate English subtitle coverage using:
   - ffprobe to detect embedded English subtitle tracks
   - File system scan for external English subtitle files (.srt, .ass, etc.)
   
   Logic:
   - If embedded English subtitles OR external English subtitles exist → 
     mark as "covered", SKIP
   - Distinguish regular subtitles from forced subtitles (display only 
     foreign language dialogue)
   - Generate list of TV episodes/movies lacking ANY English subtitles

9. SUBTITLE ACQUISITION
   For files missing subtitles (from step 8):
   
   Primary source: OpenSubtitles.org (with your credentials)
   Fallback sources: OpenSubtitles.com, Podnapisi.NET, Addic7ed.com, Subscene.com
   
   Matching strategy:
   1. Prioritize hash-based matching (video file hash)
   2. Fall back to fuzzy matching by filename/metadata
   
   Download both:
   - Regular English subtitles
   - Forced English subtitles (if available)
   
   Note: Forced subtitles can be added even to files that already have 
   regular subtitles.
   
   Respect all API rate limits and terms of service.

================================================================================
RULES
================================================================================

1. API Courtesy
   Respect rate limits. Implement exponential backoff. Cache aggressively.

2. User Control
   All destructive operations require explicit review and confirmation. 
   Dry-run mode mandatory.

3. Jellyfin Compliance
   Follow official Jellyfin naming conventions and folder structure. NFO files 
   must conform to Jellyfin's XML schema.

4. Data Integrity
   Preserve original file paths in master inventory. Never modify source files 
   until user approves.

5. Transparency
   Indicate confidence levels and reasoning for all actions. Flag ambiguous 
   cases for manual review.

6. Python Environment
   Always use virtual environment in project root. Never execute without 
   activating it first.

================================================================================
YOUR IMMEDIATE ACTION PLAN
================================================================================

BEFORE YOU CODE ANYTHING:
-------------------------
1. Run the consolidation audit script to identify duplicates
2. Create backup ZIP of entire V:/JellyRancher/ directory
3. Read CONSOLIDATION_REPORT.txt to see what's real vs. duplicated
4. Create clean V:/JellyRancher_v2/ with only the "KEEP THIS ONE" files from report

YOUR CLEAN PROJECT STRUCTURE:
------------------------------
```

```
V:/JellyRancher_v2/
  ├─ SPEC.md                  # This workflow (points 1-9)
  ├─ README.md                # Project overview
  ├─ requirements.txt         # Python dependencies
  ├─ .gitignore               # Ignoring .venv, logs, __pycache__, .chroma
  ├─ .venv/                   # Virtual environment (git-ignored)
  │
  ├─ scripts/                 # Main application code
  │   ├─ core/                # Core business logic
  │   │   ├─ scanner.py       # Point 1: Folder scanning
  │   │   ├─ metadata.py      # Point 4: TMDB/TVDB queries
  │   │   ├─ executor.py      # Point 7: File operations
  │   │   └─ subtitles.py     # Points 8-9: Subtitle handling
  │   │
  │   ├─ gui/                 # PyQt6 interface
  │   │   ├─ main_window.py
  │   │   ├─ action_table.py  # Point 5: Editable review table
  │   │   └─ dialogs.py
  │   │
  │   ├─ utils/               # Shared utilities
  │   │   ├─ logger.py
  │   │   ├─ api_client.py    # Rate-limited API wrapper
  │   │   └─ transaction_log.py  # Point 6: Snapshot/rollback
  │   │
  │   └─ tests/               # Unit tests
  │
  ├─ data/                    # Application data (git-ignored)
  │   ├─ cache/               # API response cache
  │   ├─ logs/                # Application logs
  │   └─ transaction_logs/    # Rollback manifests
  │
  └─ docs/                    # Documentation
      └─ WORKFLOW.md          # Detailed workflow docs
```

```markdown
================================================================================
WHAT TO PASTE IN YOUR IDE AI (START OF EACH SESSION)
================================================================================
```

```
Context: Building a Jellyfin media organizer in Python 3.12 + PyQt6.

Workflow: 9-point process (scan folders → metadata enrichment → 
reorganization → subtitle acquisition).

Current task: [DESCRIBE WHAT YOU'RE WORKING ON]

See SPEC.md for full workflow details.

Key constraints:
- Must respect TMDB/TVDB rate limits
- All file operations require transaction logs for rollback
- PyQt6 GUI with color-coded action review table
- Subtitle handling: regular + forced variants

Working directory: V:/JellyRancher_v2/scripts/
```

```markdown
================================================================================
KEY ARCHITECTURAL DECISIONS
================================================================================

Why PyQt6?
----------
- Mature, cross-platform
- Excellent table/tree widgets for action review (point 5)
- Built-in threading for background API calls

Why Transaction Logs Instead of Git?
-------------------------------------
- File operations may span multiple commits
- Need atomic rollback of entire batch
- MD5 verification ensures data integrity

Why MD5 Instead of SHA256?
---------------------------
- "Good enough" for corruption detection
- 3x faster on large video files
- Not doing cryptography, just file integrity checks

Why Separate Regular + Forced Subtitles?
-----------------------------------------
- Jellyfin treats them differently
- Forced subtitles enhance viewing for foreign dialogue scenes
- Users want both when available

================================================================================
COMMON PITFALLS TO AVOID
================================================================================

1. Don't commit .venv/ to git (causes the 800MB bloat you had)
2. Don't nest sub-projects (CodeCop, RavenMaven should be siblings, not children)
3. Don't create multiple ChromaDB instances (one per project max)
4. Don't archive inside the working directory (move archives to external drive)
5. Don't skip dry-run testing (always test reorganization before execution)

================================================================================
YOUR EXISTING CAPABILITIES (FROM CODE-CAPABILITIES.MD)
================================================================================

These scripts already exist in your scattered codebase. Reference them when 
building the new system:

Core Executors:
---------------
- jellyfin_safe_executor.py: Snapshot + rollback system (use as reference 
  for point 6-7)
- batch_queue_processor.py: Batch processing with resume capability

API Clients:
------------
- ravenmaven_client.py: Poe.com API wrapper (adapt for LLM calls in point 3)

Parsers:
--------
- llm_response_parser.py: Parse LLM output into structured JSON (point 3)

GUI Components:
---------------
- ravenmaven_gui.py: Main GUI structure (adapt for PyQt6 implementation)

Action: Use the consolidation audit to find the newest version of each script, 
then extract reusable logic.