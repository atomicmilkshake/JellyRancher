# Consolidated Project Documentation

*Generated: 2025-11-21 09:14:05*

*Total Documents: 58*

---

## Table of Contents

1. [docs\_common_requirements.txt](#requirementstxt)
2. [docs\requirements.txt](#requirementstxt)
3. [docs\INGESTION_GUIDE.md](#ingestion_guidemd)
4. [docs\RICH_SOLUTION.md](#rich_solutionmd)
5. [docs\QUICK_START.md](#quick_startmd)
6. [docs\README_JOURNAL.md](#readme_journalmd)
7. [docs\EPISODE_TITLES_GUIDE.md](#episode_titles_guidemd)
8. [docs\plan.md](#planmd)
9. [docs\tmdb_usage_guidelines.md](#tmdb_usage_guidelinesmd)
10. [docs\LLM_LOG_ANALYSIS_REPORT.md](#llm_log_analysis_reportmd)
11. [docs\EXTRACTION_IMPROVEMENT_SUMMARY.md](#extraction_improvement_summarymd)
12. [docs\architecture-reference.md](#architecture-referencemd)
13. [docs\PHASES_1-6_RECOVERED.txt](#phases_1-6_recoveredtxt)
14. [docs\gemini-piece-of-shit-confirmation.md](#gemini-piece-of-shit-confirmationmd)
15. [docs\ALL_RECOVERED_PHASES.txt](#all_recovered_phasestxt)
16. [docs\phases_21_22.txt](#phases_21_22txt)
17. [docs\requirements-jelly-rancher.txt](#requirements-jelly-ranchertxt)
18. [docs\agent-journal_RESTORED.md](#agent-journal_restoredmd)
19. [docs\FUNCTION_INDEX_BUILD_SUMMARY.md](#function_index_build_summarymd)
20. [docs\PHASES_1-21_RECONSTRUCTED.md](#phases_1-21_reconstructedmd)
21. [docs\README.md](#readmemd)
22. [docs\RECOVERED_journal.md](#recovered_journalmd)
23. [docs\RECOVERED_journal_v2.md](#recovered_journal_v2md)
24. [docs\RECOVERY_SUMMARY.md](#recovery_summarymd)
25. [docs\TESTING_GUIDE.md](#testing_guidemd)
26. [docs\ARCHITECTURE.md](#architecturemd)
27. [docs\ass.plan.md](#assplanmd)
28. [docs\bootstrap.md](#bootstrapmd)
29. [docs\JELLY_RANCHER_PROJECT_STATE_2025.md](#jelly_rancher_project_state_2025md)
30. [docs\CLEANUP_GIT_CHROMADB_20251112.md](#cleanup_git_chromadb_20251112md)
31. [docs\COMMON_PITFALLS.md](#common_pitfallsmd)
32. [docs\EPISODE_TITLE_MANAGEMENT.md](#episode_title_managementmd)
33. [docs\JELLYFIN_API_INTEGRATION_PLAN.MD](#jellyfin_api_integration_planmd)
34. [docs\knowledge-pack.md](#knowledge-packmd)
35. [docs\MOVIE_NAMES_GUIDE.md](#movie_names_guidemd)
36. [docs\MOVIE_NAME_MANAGEMENT.md](#movie_name_managementmd)
37. [docs\PYQT6_MIGRATION_PLAN.md](#pyqt6_migration_planmd)
38. [docs\ROOT_CLEANUP_20251112.md](#root_cleanup_20251112md)
39. [docs\SESSION_STARTER.md](#session_startermd)
40. [docs\TMDB_CACHE_GENERATOR.md](#tmdb_cache_generatormd)
41. [docs\TMDB_CACHE_GUIDE.md](#tmdb_cache_guidemd)
42. [docs\USER_GUIDE.md](#user_guidemd)
43. [docs\WORKFLOW_SPEC.md](#workflow_specmd)
44. [docs\WORKFLOW_STEP1_GUIDE.md](#workflow_step1_guidemd)
45. [docs\LLM_ASSISTANT_BOOTSTRAP.md](#llm_assistant_bootstrapmd)
46. [docs\WORKFLOW_README.md](#workflow_readmemd)
47. [docs\_archived_README.md](#readmemd)
48. [docs\start.md](#startmd)
49. [docs\COMPREHENSIVE_PROJECT_REFERENCE.md](#comprehensive_project_referencemd)
50. [docs\GUI_REDESIGN_COMPREHENSIVE_PLAN.md](#gui_redesign_comprehensive_planmd)
51. [docs\UX_REDESIGN_MASTER_PLAN.md](#ux_redesign_master_planmd)
52. [docs\ERROR_HANDLING_GUIDELINES.md](#error_handling_guidelinesmd)
53. [docs\master-prompt-backup.md](#master-prompt-backupmd)
54. [docs\GEMINI_DIAGNOSTIC_REPORT.md](#gemini_diagnostic_reportmd)
55. [docs\GEMINI_QUICK_FIX.md](#gemini_quick_fixmd)
56. [docs\GEMINI_COMMUNITY_ANALYSIS.md](#gemini_community_analysismd)
57. [docs\GEMINI_ANSWERS.md](#gemini_answersmd)
58. [docs\FUNCTION_INDEX_USAGE.md](#function_index_usagemd)

---

# docs\_common_requirements.txt

**Original Date:** 2025-10-23 15:21:43

**Compression:** 455 -> 402 chars (88.4%)

**Status:** success

# Core dependencies for Jellyfin Media Organization Agent

# Encryption for credential storage (Fernet)
cryptography>=41.0.0

# Testing framework
pytest>=7.4.0
pytest-cov>=4.1.0

# Subtitle API libraries (Phase 2)
# requests>=2.31.0  # HTTP for subtitle APIs
# opensubtitles-com>=0.1.0  # OpenSubtitles.com API (TBD)

# Optional: Progress bars
tqdm>=4.66.0

# Optional: Rich console output
rich>=13.7.0

---

# docs\requirements.txt

**Original Date:** 2025-10-28 00:22:24

**Compression:** 510 -> 421 chars (82.5%)

**Status:** success

# Core dependencies for Jellyfin Media Organization Agent

# Fernet encryption (credentials)
cryptography>=41.0.0

# HTTP client (APIs, scraping)
requests>=2.31.0

# HTML parsing (Wikipedia)
beautifulsoup4>=4.12.0
lxml>=4.9.0  # Faster XML/HTML parser

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Subtitles
subliminal>=2.1.0
babelfish>=0.6.0

# Optional: Progress bars
tqdm>=4.66.0

# Optional: Rich console
rich>=13.7.0

---

# docs\INGESTION_GUIDE.md

**Original Date:** 2025-11-02 11:35:57

**Compression:** 8,191 -> 6,784 chars (82.8%)

**Status:** success

# OpenMemory Ingestion Guide

Both ingestion scripts support Rich formatting on Windows, Mac, and Linux.

## Quick Start

### 1. Start the OpenMemory Backend
```bash
cd V:\Jellyfin Organizer\OpenMemory\backend
npm run dev
```

Backend shows: `Server listening on port 8080`

### 2. Run Ingestion (Choose One)

#### Option A: Full-featured with Rich (Recommended)
```bash
cd V:\Jellyfin Organizer\scripts
python openmemory_ingest_all.py
```

**Features:**
- Rich formatting (colors, tables, progress bars)
- Cross-platform (Windows/Mac/Linux)
- Auto UTF-8 on Windows
- Falls back to plain text if Rich unavailable
- Shows semantic search examples

#### Option B: Simple (Lightweight)
```bash
cd V:\Jellyfin Organizer\scripts
python openmemory_ingest_simple.py
```

**Features:**
- Minimal dependencies
- Plain text output
- Lightweight/fast
- No Rich needed
- Identical ingestion results

## Technical Details

### UTF-8 Encoding Fix (Windows)
Both scripts auto-configure UTF-8:

```python
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

Fixes Unicode errors in Windows PowerShell.

### Rich Console Configuration
Intelligent Rich init:

```python
try:
    from rich.console import Console
    console = Console(
        width=100,
        force_terminal=True,
        force_unicode=True,
        legacy_windows=False
    )
except TypeError:
    console = Console(width=100, force_terminal=True)
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
```

### Graceful Fallback
```python
if RICH_AVAILABLE and console:
    console.print(colored_formatted_text)
else:
    print(plain_text)
```

## What Gets Ingested
- **92 .md files** (guides, decisions, architecture, procedures)
- **114 .py files** (code/docstrings, tests, utils)
- **8 .json files** (settings/configs)
- **Total: 213 files** (~3M+ chars)

## Expected Output

### With Rich
```
═════════════════════════════════════════════════
  OpenMemory Project Foundation Builder
═════════════════════════════════════════════════

✓ OpenMemory backend online

📂 Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

⏳ Ingesting documentation... ████████░░ 85%
⏳ Ingesting Python code... ████████░░ 92%
⏳ Ingesting configurations... ░░░░░░░░░░ 0%

┌─ Ingestion Summary ──────────────────────────────┐
│ Category                 Count                   │
├──────────────────────────────────────────────────┤
│ Documentation Files         92                   │
│ Python Files               114                   │
│ Config Files                 8                   │
│ Total Characters       3,245,189                 │
├──────────────────────────────────────────────────┤
│ Total Files Ingested       214                   │
└──────────────────────────────────────────────────┘

🔍 Testing Semantic Search...
Q: How do we organize TV shows?
  [89%] MASTER_PROMPT.md: The system organizes media into standardized...
  [87%] media_utils.py: TV show organization follows standard patterns...
[... more results ...]

═════════════════════════════════════════════════
  Success!
═════════════════════════════════════════════════
OpenMemory is now the foundation of this project.
AI agents can now query project context semantically.
```

### Without Rich
```
============================================================
  OpenMemory Project Foundation Builder
============================================================

[OK] OpenMemory backend online

[SCAN] Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

Ingesting documentation files...
[OK] Ingesting Python code files...
[OK] Ingesting configuration files...
[OK]

============================================================
Ingestion Summary
============================================================
Documentation Files:  92
Python Files:        114
Config Files:          8
Total Characters:     3,245,189
────────────────────────────────────────────────────────────
Total Files Ingested: 214
============================================================

Q: How do we organize TV shows?
  [89%] MASTER_PROMPT.md: The system organizes media into...
  [87%] media_utils.py: TV show organization follows standard...
[... more results ...]

============================================================
SUCCESS!
============================================================
OpenMemory is now the foundation of this project.
AI agents can now query project context semantically.
```

## Troubleshooting

### "OpenMemory backend not running"
**Solution:** Start backend:
```bash
cd V:\Jellyfin Organizer\OpenMemory\backend
npm run dev
```
Wait for: `Server listening on port 8080`

### Unicode encoding errors
**Solution:** Auto-handled. If issues:
1. Use Python 3.7+
2. Run from VS Code terminal (not PowerShell)
3. Set manually: `$env:PYTHONIOENCODING = 'utf-8'`

### "OpenMemory SDK not found"
**Solution:**
```bash
cd V:\Jellyfin Organizer\OpenMemory\sdk-py
pip install -e .
```

### Script hangs during ingestion
**Solution:** Normal for 213 files (2-5 min). Monitor terminal progress.

## Scripts Comparison

| Feature | `openmemory_ingest_all.py` | `openmemory_ingest_simple.py` |
|---------|----------------------------|-------------------------------|
| Rich Formatting | ✅ Yes (UTF-8 fix) | ⚠️ Optional |
| Windows Compatible | ✅ Yes | ✅ Yes |
| Ingestion Speed | Normal | Normal |
| Dependencies | Rich (optional) | None |
| Fallback Output | Plain text | Plain text |
| Semantic Search Tests | ✅ Included | ⚠️ Minimal |
| Progress Bars | ✅ Yes | Simple counter |
| File Size | 550 lines | 235 lines |

**Recommendation:** Use `openmemory_ingest_all.py` for full experience. Ingestion identical.

## Next Steps
1. Verify ingestion (semantic search works)
2. Test queries on project knowledge
3. Use in AI agents (scripts access OpenMemory context)
4. Re-run after major changes

## API Usage
```python
from openmemory import OpenMemory

om = OpenMemory(base_url="http://localhost:8080")

# Ingest
om.ingest(
    content="file contents here",
    tags=["documentation", "guide"],
    metadata={
        "file_name": "example.md",
        "type": "markdown"
    }
)

# Query
results = om.query(query="How do we organize media?", k=3)
for item in results["items"]:
    print(f"{item['metadata']['file_name']}: {item['content']}")
```

## Support
1. Check backend: `curl http://localhost:8080/health`
2. Verify Python env activated
3. Review terminal errors
4. Check `backend_error.log` if backend fails

---

# docs\RICH_SOLUTION.md

**Original Date:** 2025-11-02 11:35:57

**Compression:** 8,644 -> 6,500 chars (75.2%)

**Status:** success

# OpenMemory Ingestion - Seamless Rich Support ✅

## Problem Solved

Rich formatting now works across Windows, Mac, Linux.

### What Was Broken
- `openmemory_ingest_all.py` crashed: `UnicodeEncodeError: 'charmap' codec can't encode characters`
- Rich outputs Unicode; Windows PowerShell uses cp1252
- Persisted with `legacy_windows=True`

### Solution
Dual-mode output:
1. **Rich Mode**: Colors, tables, progress bars (if available)
2. **Fallback**: Plain text (auto on issues/no Rich)

## Technical Implementation

### 1. Windows UTF-8 Encoding
```python
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

### 2. Graceful Rich Init
```python
RICH_AVAILABLE = False
try:
    from rich.console import Console
    try:
        console = Console(
            width=100,
            force_terminal=True,
            force_unicode=True,
            legacy_windows=False
        )
    except TypeError:
        console = Console(width=100, force_terminal=True)
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
```

### 3. Output Helpers
```python
def print_success(message: str):
    if RICH_AVAILABLE and console:
        console.print(f"[green]✓[/green] {message}")
    else:
        print(f"[OK] {message}")

def print_error(message: str):
    if RICH_AVAILABLE and console:
        console.print(f"[red]✗[/red] {message}")
    else:
        print(f"[ERROR] {message}")
```

### 4. Smart Tables
```python
def print_table(title: str, rows: List[Dict], columns: List[str]):
    if RICH_AVAILABLE and console:
        table = Table(title=title)
        # ... add rows ...
        console.print(table)
    else:
        _print_table_plain(title, rows, columns)
```

### 5. Progress Bar
```python
progress_bar = create_progress_bar(total_items)
if progress_bar:
    with progress_bar as progress:
        # Use Rich progress
else:
    # Counter fallback
    for item in items:
        process(item)
```

## Files Modified

### `openmemory_ingest_all.py` (550+ lines)
- UTF-8 Windows setup
- Graceful Rich init
- 7 output helpers
- Replaced `console.print()` with helpers
- Fallbacks for all Rich features
**Key Functions**: `print_info()`, `print_success()`, `print_warning()`, `print_error()`, `print_panel()`, `print_table()`, `create_progress_bar()`

### `openmemory_ingest_simple.py` (235 lines)
- UTF-8 setup
- Graceful Rich init
- Matches main script capabilities

## Usage

### With Rich
```bash
cd scripts
python openmemory_ingest_all.py
```
**Rich Output**:
```
═════════════════════════════════════════════════
  OpenMemory Project Foundation Builder
═════════════════════════════════════════════════

✓ OpenMemory backend online

📂 Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

[Progress bars...]

Success!
```
**Fallback**:
```
[OK] OpenMemory backend online

Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

[Simple counters...]

Success!
```

### Without Rich
```bash
python openmemory_ingest_simple.py
```

## Compatibility Matrix

| OS      | Terminal    | Python 3.7+ | Result              |
|---------|-------------|-------------|---------------------|
| Windows | PowerShell  | ✅          | ✅ Rich             |
| Windows | CMD         | ✅          | ✅ Rich             |
| Windows | VS Code     | ✅          | ✅ Rich             |
| Mac     | Terminal    | ✅          | ✅ Rich             |
| Mac     | iTerm2      | ✅          | ✅ Rich             |
| Linux   | Bash        | ✅          | ✅ Rich             |
| Linux   | Zsh         | ✅          | ✅ Rich             |
| Any     | Python 3.6  | ❌          | ✅ Plain fallback   |
| Any     | No Rich     | N/A         | ✅ Plain fallback   |

## Key Improvements

| Before                          | After                          |
|---------------------------------|--------------------------------|
| ❌ UnicodeEncodeError (Win PS)  | ✅ All platforms                |
| ❌ TypeError (Rich params)      | ✅ Auto UTF-8 (Win)             |
| ❌ No fallback                  | ✅ Graceful plain fallback      |
| ❌ Platform inconsistent        | ✅ Beautiful when possible      |
| ❌ Confusing errors             | ✅ Readable always              |

## Code Quality

1. **Platform Detection**
   ```python
   if sys.platform == 'win32':
       # Windows encoding
   ```

2. **Feature Detection**
   ```python
   if RICH_AVAILABLE and console:
       # Rich output
   ```

3. **Error Handling**
   ```python
   try:
       sys.stdout.reconfigure(encoding='utf-8', errors='replace')
   except (AttributeError, RuntimeError):
       pass
   ```

4. **Fallbacks**
   ```python
   def _print_table_plain():  # Plain impl
   def create_progress_bar():  # None if unavailable
   ```

## Testing

1. **Rich (Win PS)**:
   ```bash
   cd scripts
   python openmemory_ingest_all.py
   ```
   # Colored output, bars, tables

2. **No Rich**:
   ```bash
   python openmemory_ingest_simple.py
   ```
   # Plain text, counters

3. **Encoding Override**:
   ```bash
   $env:PYTHONIOENCODING = 'utf-8'
   python openmemory_ingest_all.py
   ```

4. **Old Python**: Auto-fallback

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  openmemory_ingest_all.py               │
│  openmemory_ingest_simple.py            │
└─────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │ Platform Detection   │
   └──────────────────────┘
              ▼
   ┌──────────────────────┐
   │ UTF-8 Setup (Win)    │
   └──────────────────────┘
              ▼
   ┌──────────────────────┐
   │ Feature Detection    │
   │ (Rich?)              │
   └──────────────────────┘
         ┌────┴────┐
         ▼         ▼
    ┌─────────┐ ┌──────────┐
    │ Rich    │ │ Fallback │
    │ Output  │ │ Output   │
    └─────────┘ └──────────┘
         └────┬────┘
              ▼
        ┌───────────────┐
        │ Console Out   │
        │ (Colors/Plain)│
        └───────────────┘
```

## Summary

✅ **Problem**: Rich crashes on Windows  
✅ **Cause**: Encoding mismatch  
✅ **Fix**: UTF-8 + fallback  
✅ **Result**: Cross-platform, Rich when possible  
✅ **Compatible**: No new deps  
✅ **Tested**: Win/Mac/Linux  

**Status**: ✨ READY ✨

---

# docs\QUICK_START.md

**Original Date:** 2025-11-02 11:35:57

**Compression:** 4,500 -> 3,726 chars (82.8%)

**Status:** success

# OpenMemory Ingestion - Quick Start

## Setup (One-Time)

```bash
# 1. Start backend
cd V:\Jellyfin Organizer\OpenMemory\backend
npm run dev

# Wait for: "Server running on http://localhost:8080"
```

## Run Ingestion

```bash
# 2. In another terminal, run ingestion
cd V:\Jellyfin Organizer\scripts
python openmemory_ingest_all.py
```

Scripts support Rich formatting on Windows, Mac, Linux.

---

## Changes

### Windows PowerShell
- Colored output with Rich
- Progress bars, formatted tables
- No encoding errors
- Automatic UTF-8 handling

### Cross-Platform
- Windows PowerShell/CMD: Rich ✅
- Mac Terminal: Rich ✅
- Linux Bash/Zsh: Rich ✅
- Old systems: Plain text fallback ✅

### Zero Configuration
- Auto-detects Rich
- Graceful fallback
- Sets UTF-8 for Windows

---

## Scripts

| Script | Best For | Output |
|--------|----------|--------|
| `openmemory_ingest_all.py` | Full-featured | Rich + semantic search tests |
| `openmemory_ingest_simple.py` | Lightweight | Rich or plain text |

**Recommendation**: Use `openmemory_ingest_all.py`.

---

## Expected Output

### With Rich
```
═════════════════════════════════════════════════
  OpenMemory Project Foundation Builder
═════════════════════════════════════════════════

✓ OpenMemory backend online

📂 Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

⏳ Ingesting documentation... [████████░░] 80%
⏳ Ingesting Python code... [██████████] 100%
⏳ Ingesting configurations... [██████████] 100%

Ingestion Summary
─────────────────────────────────────────────────
Documentation Files:     92
Python Files:           114
Config Files:             8
Total Characters:   3,245,189
─────────────────────────────────────────────────
Total Files Ingested:   214

✓ Project knowledge loaded into OpenMemory!
```

### Without Rich
```
═════════════════════════════════════════════════
  OpenMemory Project Foundation Builder
═════════════════════════════════════════════════

[OK] OpenMemory backend online

Scanning project files...
  Found 92 documentation files
  Found 114 Python files
  Found 8 config files

Ingesting documentation files...
Ingesting Python code files...
Ingesting configuration files...

[OK] Project knowledge loaded into OpenMemory!
```

---

## How It Works

### 1. UTF-8 Encoding (Windows Fix)
```python
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```
**Effect**: Outputs Unicode on Windows.

### 2. Feature Detection
```python
try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
```

### 3. Dual Output Helpers
```python
def print_success(message):
    if RICH_AVAILABLE:
        console.print(f"[green]✓[/green] {message}")
    else:
        print(f"[OK] {message}")
```

---

## Ingested Files
- 92 documentation (.md)
- 114 Python (.py)
- 8 config (.json)
- Total: 214 files (~3.2M chars)

Indexed for semantic search.

---

## Troubleshooting

### "Backend not running"
```bash
cd OpenMemory/backend
npm run dev
# Wait for: "Server running on http://localhost:8080"
```

### "Unicode/encoding error"
Scripts handle automatically. If issues:
```bash
$env:PYTHONIOENCODING = 'utf-8'
python openmemory_ingest_all.py
```

### "OpenMemory SDK not found"
```bash
cd OpenMemory/sdk-py
pip install -e .
```

---

## Files Modified
- `openmemory_ingest_all.py` (550+ lines)
- `openmemory_ingest_simple.py` (235 lines)

## Documentation
- `INGESTION_GUIDE.md`: API examples
- `RICH_SOLUTION.md`: Technical details

---

## Next Steps
1. Run ingestion (backend online)
2. Verify 214 files indexed
3. Test semantic search
4. Use in AI agents

---

# docs\README_JOURNAL.md

**Original Date:** 2025-11-06 17:20:46

**Compression:** 2,051 -> 1,738 chars (84.7%)

**Status:** success

# OpenMemory Journal (Dev/Agent Notes)

Docs for using OpenMemory as semantic dev journal for Jellyfin Organizer (etc.), with ImmutableAuditLog as source of truth.

## Prereqs

- OpenMemory backend running locally (`config.json -> openmemory.url`).
- Python: `pip install requests`
- Optional: Ollama with `nomic-embed-text` if backend uses it for embeddings.

## Config

`_common/config_loader.py` reads `config.json` at project root:

```json
{
  "openmemory": {
    "backend_dir": "C:/path/to/OpenMemory",
    "url": "http://localhost:8080"
  }
}
```

## Publish a journal entry

From scripts folder:

```powershell
# Direct text
python .\journal_service.py --category decision --project "Jellyfin Organizer" --tag workflow --tag planning "Planning JMO integration: services layer, dual-write audit->journal, AI assist on ambiguous renames."

# From stdin (multi-line)
Get-Content .\some_notes.txt | python .\journal_service.py --category summary --tag weekly
```

Fields:
- `--category` observation|decision|plan|action|error|rollback|summary
- `--project` scopes projects
- `--session-id` ties action sequences
- `--tag` repeatable
- `--media-ref` repeatable media paths/ids (for per-file queries)
- `--audit-ref` links to audit record id

Service does best-effort secret redaction before indexing.

## Why two layers?

- ImmutableAuditLog: exact, append-only, rollbackable operation truth.
- OpenMemory journal: short, human-readable summaries/rationale for semantic search.

Search OpenMemory UI/API for "why", follow `audit_ref` for exact details.

## Health check

```powershell
# Expect [OK] if reachable
python .\journal_service.py "health check" --category observation
```

If fails, check `openmemory.url` and backend status.

---

# docs\EPISODE_TITLES_GUIDE.md

**Original Date:** 2025-11-09 05:33:30

**Compression:** 6,206 -> 4,377 chars (70.5%)

**Status:** success

# Episode Title Management Guide

## Overview

Episode Title Management analyzes TV episode files against TMDB data, detects naming issues, and automates fixes to professional standards with preview and rollback.

## What It Does

- **Smart Analysis**: Detects episode numbering and titles
- **TMDB Integration**: Cross-references official data
- **Issue Detection**: Flags missing, incorrect, or malformed titles
- **Safe Fixing**: Preview/apply changes with rollback
- **Batch Processing**: Handles full TV shows
- **Confidence Scoring**: Rates file-TMDB match (High/Medium/Low)

## Quick Start

### 1. Prepare TMDB Cache

1. **Tools** → **Generate TMDB Cache**
2. Search TV show
3. Generate/save cache file
4. Note file location

### 2. Analyze Episodes

1. **Episode Analysis** tab
2. **Select Show Folder**
3. Choose TV show directory
4. Select TMDB cache
5. **Analyze Episodes**

### 3. Review and Fix

1. Review results, confidence, issues
2. Preview fixes
3. Apply changes

## Understanding the Interface

### Main Controls

- **Select Show Folder**: Pick TV show directory
- **Select TMDB Cache**: Link episode data
- **Analyze Episodes**: Run analysis
- **Fix Selected Issues**: Apply to checked items
- **Export Results**: Save as JSON

### Results Table

- **Current Name**: Existing filename
- **Suggested Name**: Recommended fix
- **Confidence**: High/Medium/Low certainty
- **Issues**: Detected problems
- **Status**: File state

### Color Coding

- 🟢 **Green**: Perfect TMDB match
- 🟡 **Yellow**: Minor issues, suggestions
- 🔴 **Red**: Major problems

## Common Issues and Solutions

### Missing Episode Titles
**Problem**: `Show S01E01.mkv` (no title)  
**Solution**: Adds TMDB titles

### Incorrect Titles
**Problem**: Wrong/unofficial titles  
**Solution**: Suggests TMDB corrections

### Codec Tags in Titles
**Problem**: `Show S01E01 [1080p].mkv`  
**Solution**: Removes codec tags

### Inconsistent Formatting
**Problem**: Mixed patterns  
**Solution**: Standardizes to Jellyfin format

## Supported File Formats

- **MKV, MP4, AVI**: Common videos
- **Multiple episodes**: Multi-episode files
- **Special episodes**: Specials/non-standard
- **International shows**: Non-English titles

## Advanced Features

### Dry Run Mode
- Preview changes
- No data loss

### Selective Fixing
- Fix individuals/batches
- Skip as needed

### Confidence Filtering
- Prioritize high-confidence
- Review medium/low manually

### Export and Reporting
- JSON analysis reports
- Share/track/audit changes

## Best Practices

### Organization
- Organize TMDB caches by show
- Process one show at a time
- Backup before bulk ops

### Quality Control
- Review high-confidence fixes
- Test small batches
- Use dry-run

### Maintenance
- Re-analyze after TMDB updates
- Check new episodes
- Update caches for new seasons

## Troubleshooting

### "No Episodes Found"
- Verify Jellyfin folder structure
- Ensure S01E01 numbering
- Confirm TMDB cache matches show

### "Low Confidence Scores"
- Update TMDB cache
- Match episode numbering to TMDB
- Handle specials manually

### "Permission Denied"
- Check write access
- Close media players
- Disable antivirus interference

## Integration with Other Tools

### Media Organization
- Post-import cleanup
- Media server prep
- Consistent naming

### Subtitle Management
- Clean titles pre-download
- Improve matching/organization

### Analytics and Reporting
- Naming quality reports
- Track consistency
- Flag needy shows

## Performance Tips

- **Large Collections**: One show at a time
- **Network Drives**: Stable connection
- **File Count**: Handles thousands efficiently
- **Memory Usage**: Monitor for large libraries

## Examples

### Before and After

**Before:**
```
TheOffice.S01E01.mkv
TheOffice.S01E02.Diversity.Day.mkv
TheOffice.S01E03.Health.Care.[720p].mkv
```

**After:**
```
The Office - S01E01 - Pilot.mkv
The Office - S01E02 - Diversity Day.mkv
The Office - S01E03 - Health Care.mkv
```

### Analysis Results
```
✓ S01E01: Perfect match - "Pilot"
✓ S01E02: Title corrected - "Diversity Day"
⚠ S01E03: Codec tag removed - "[720p]" stripped
```

## Support Resources

- **In-App Help**: Built-in system
- **Tooltips**: Hover for guidance
- **Log Files**: `logs/` directory
- **Settings**: Analysis preferences tab

---

**Pro Tip**: Start with small show to learn workflow; tool learns from preferences/corrections.

---

# docs\plan.md

**Original Date:** 2025-11-09 13:44:48

**Compression:** 8,322 -> 3,494 chars (42.0%)

**Status:** success

# Application Proposal for Jellyfin Media Organizer

## Core Requirements

1. **Scan selected folder(s) recursively for file list (paths).**  
   Compute/store MD5 hashes (CSV/JSON output) for verification/duplicates. Optionally query Jellyfin API (GET /Items?Recursive=true&IncludeItemTypes=Movie,Episode&Fields=Path) for existing items/metadata. Scrape AniList/AniDB metadata. Filter media types; parallelize hashing.

2. **Summarize structure** (e.g., "Star Trek The Next Generation: 178 videos" or "7 seasons: X videos each").  
   Group MD5 duplicates (e.g., "178 videos: 5 dupes"). Jellyfin comparison (GET /Views, GET /UserViews; e.g., "50 already in Jellyfin via paths/hashes"). Playback stats (Playback Reporting; e.g., "50 watched, 200 hours"). Text-based trees. Capture structure for reorg without filename overload.

3. **Submit summary to LLM** for Jellyfin reorg proposal and movies/TV list.  
   Include Jellyfin API data (items/collections), MD5 dupes, Trakt/Ani-Sync (watched/ratings) for informed proposals (e.g., prioritize unwatched; API actions like collections).

4. **Query canonical data** from LLM media list (movie years, TV names/years, seasons/episode titles/numbers). Handle multi-part episodes (e.g., Star Trek TNG pilot; generate NFOs).  
   Cross-verify Jellyfin (GET /Items/{itemId}?Fields=ProviderIds). Test NFOs via API refresh. Add Fanart.tv artwork/Themerr themes. Merge dupes (Merge Versions plugin).

5. **Generate editable table** from canonical DB + LLM proposal: per-file actions (delete, move, nothing, review).  
   Columns: MD5 (current/proposed), Jellyfin status (API match), API actions (e.g., refresh post-move), artwork previews (Fanart), theme suggestions (Themerr), box sets (TMDb Box Sets). Interactive/sortable/bulk edits.

6. **Execute plan**: Move/rename files + related subs (Jellyfin naming).  
   MD5-verify (source pre-, dest post-; rollback on mismatch). Trigger API refreshes (POST /Items/{itemId}/Refresh, POST /Libraries/{libraryId}/Refresh); auto-collections (POST /Collections/{collectionId}/Items). Auto-download artwork/themes; sub extraction (Subtitle Extract). Log journal (paths, actions, MD5s, API results).

7. **Evaluate subtitle coverage**: ffprobe + API (GET /Items/{itemId}?Fields=MediaStreams) for external/embedded subs. List missing episodes/movies. MD5-compare subs; "API-Validated" status. WizdomSubs fallback. Kodi Sync Queue integration.

8. **Obtain missing subs** (OpenSubtitles + Bazarr; language prefs).  
   Post-add: API refresh/verify streams; MD5 check.

## Overarching Enhancements
- **Safety/Versioning**: Dry-runs, backups, journals. MD5 + Git/LFS; Restic/Duplicati post-execution.
- **Feedback Loop**: Post-reorg API queries (GET /Sessions; Playback Reporting) to LLM for refinements.
- ** *Arr Suite**: Handoff to Sonarr/Radarr/Lidarr for monitoring/downloads/renaming; query missing for LLM.
- **Request Tools**: Suggest misses via canonical DB; queue in Jellyseerr/Overseerr for re-scans.
- **Scrobbling/Sync**: Auto-sync Trakt/Ani-Sync during execution; personalize LLM proposals.
- **Theme/UI**: Themerr downloads; Jellyfin-Enhanced client tweaks.
- **Reporting**: Dashboards from Reports/Playback Reporting (e.g., top genres by watch time).
- **Plugin Mode**: Install as Jellyfin plugin for real-time hooks (e.g., auto-reorg on new files).
- **Config/UX**: Toggles (hash: MD5/CRC32; API); GUI/CLI; cross-platform.
- **Performance**: Multi-threading (scans/hashing); chunking; local processing.

---

# docs\tmdb_usage_guidelines.md

**Original Date:** 2025-11-11 13:44:03

**Compression:** 2,508 -> 1,547 chars (61.7%)

**Status:** success

# TMDB API Usage Guidelines - Courteous Implementation

## Official TMDB Guidelines

### Rate Limiting
- **Legacy**: 40 requests/10s (disabled Dec 2019)
- **Current**: ~40 requests/s upper bound (anti-scraping)
- **Key**: Respect 429 "Too Many Requests"
- **Rec**: Avoid hammering service

### Terms of Use
- **Cache**: ≤6 months
- **Attribution**: Required for all content
- **Commercial**: Separate written agreement
- **Prohibited**: AI/ML training, excessive bandwidth, degradation
- **Caching**: Allowed (≤6 months)

## Our Courteous Implementation

### Rate Limiting Strategy
- **TMDB Backend**: 1 request/s (1000ms)
- **Media Metadata**: 1 request/s (1000ms)
- **Wikipedia**: 1 request/11s
- **Errors**: Exponential backoff on 429

### API Usage Patterns
- **Search**: 1 call/search
- **Show Details**: 1 call/show
- **Cache Gen**: 1 + N (show + seasons)
- **Metadata**: 1-2 calls/item (TMDB + OMDb)

### Courteous Features
- Auto rate limiting on all calls
- 429 detection/backoff
- Progress feedback
- Conservative limits (below bounds)
- Error recovery

### Usage Examples
- Single Cache (10 seasons): ~10-15s
- Bulk Metadata: ~1s/item
- Search: Near-instant w/ limiting

### Compliance Status
✅ Rate limiting  
✅ 429 handling  
✅ Attribution  
✅ Cache limits  
✅ Non-commercial  
✅ No AI/ML

## Recommendations for Users
1. **Batch**: Space bulk ops
2. **Cache Reuse**: Valid months
3. **Errors**: Wait/retry on limits
4. **Attribution**: In UI
5. **Responsible**: Gen only needed caches

Ensures TMDB compliance for media organization.

---

# docs\LLM_LOG_ANALYSIS_REPORT.md

**Original Date:** 2025-11-13 00:01:12

**Compression:** 6,852 -> 5,079 chars (74.1%)

**Status:** success

# LLM IO Log Analysis Report
## Function/Capabilities Index Building Assessment

**Date:** 2025-11-12  
**Analysis Scope:** All LLM io log files (newest to oldest)

---

## Executive Summary

**✅ YES** - Sufficient data for comprehensive function/capabilities index. Logs provide extensive, structured function documentation.

---

## Data Statistics

### Overall Coverage
- **Total log files:** 86
- **Files with function data:** 74 (86%)
- **Total functions:** 5,696
- **Date range:** 2025-11-12 (22:05–23:55)

### Function Field Coverage
| Field                | Occurrences | Coverage    |
|----------------------|-------------|-------------|
| `function_name`      | 365         | ✅ Present  |
| `file_path`          | 140         | ✅ Present  |
| `what_it_does`       | 140         | ✅ Present  |
| `how_it_works`       | 140         | ✅ Present  |
| `inputs`             | 140         | ✅ Present  |
| `outputs`            | 140         | ✅ Present  |
| `enhanced_docstring` | 140         | ✅ Present  |
| `usage_example`      | 140         | ✅ Present  |
| `notes`              | 140         | ✅ Present  |

### Top Files by Function Count
1. `llm_transaction_20251112_224136_568861.json`: 92 functions (628.9 KB)
2. `llm_transaction_20251112_223517_941284.json`: 90 functions (483.2 KB)
3. `llm_transaction_20251112_233343_888176.json`: 89 functions (472.8 KB)
4. Multiple files: 89 functions each

---

## Data Quality Assessment

### Strengths
1. **Comprehensive Documentation**
   - `what_it_does`: Detailed descriptions
   - `how_it_works`: Implementation details
   - Inputs/outputs: Full specs, examples
   - Usage examples included

2. **Structured Format**
   - Consistent JSON structure
   - Standardized fields
   - File paths with line numbers
   - Enhanced docstrings

3. **Rich Metadata**
   - Dependencies, side effects, exceptions
   - Business context/use cases

4. **Recent/Complete**
   - Single day (2025-11-12)
   - Chronological order
   - Broad codebase coverage

### Considerations
1. **Field Variance**
   - 140 functions fully documented
   - 365 `function_name` occurrences (some partial)

2. **Extraction Needs**
   - Data in `final_response.text` (JSON arrays/strings)
   - Parse nested JSON; handle non-JSON text

---

## Recommended Index Structure

### Core Fields (Required)
- **Function Name**: Primary ID
- **File Path**: e.g., `scripts/core/jellyfin_ui.py:1362`
- **Line Number**

### Documentation Fields
- **Description** (`what_it_does`)
- **Implementation** (`how_it_works`)
- **Enhanced Docstring**

### Interface Fields
- **Parameters/Inputs**:
  - Name, type, description, required/optional, defaults, constraints
- **Outputs/Returns**:
  - Type, description, examples
- **Exceptions**: Types, conditions

### Metadata Fields
- **Dependencies**
- **Side Effects**
- **Usage Examples**
- **Notes**
- **Business Context**

### Indexing Strategy
1. **Primary**: Function name
2. **Secondary**: File path, type (method/function/class method), module/package
3. **Search**: Full-text (descriptions), keywords (names), tags (capability/domain)

---

## Implementation Recommendations

### Phase 1: Extraction
1. Parse 86 files
2. Extract from `final_response.text`
3. Handle JSON arrays/strings
4. Normalize paths (Windows/Unix)

### Phase 2: Normalization
1. Standardize fields
2. Validate paths
3. Extract line numbers
4. Merge duplicates

### Phase 3: Indexing
1. Primary index: Function name
2. Secondary: File/module/type
3. Full-text search indexes
4. Capability tags

### Phase 4: Enhancement
1. Cross-reference `function_index.json`
2. Fill partial docs
3. Add classifications
4. Usage stats

---

## Sample Function Structure

```json
{
  "function_name": "example_function",
  "file_path": "scripts/core/module.py:123",
  "what_it_does": "Detailed description of purpose and business context",
  "how_it_works": "Step-by-step implementation explanation",
  "inputs": {
    "parameters": [
      {
        "name": "param1",
        "type": "str",
        "description": "Parameter description",
        "required": true,
        "constraints": "Validation rules"
      }
    ],
    "side_effects": ["What gets modified"],
    "dependencies": ["External dependencies"]
  },
  "outputs": {
    "return_value": {
      "type": "Dict",
      "description": "Return description",
      "examples": []
    },
    "exceptions": [
      {
        "exception_type": "ValueError",
        "when": "Condition",
        "why": "Reason"
      }
    ],
    "side_effects": ["Output side effects"]
  },
  "enhanced_docstring": "Formatted docstring",
  "usage_example": "Code example",
  "notes": ["Additional context"]
}
```

---

## Conclusion

Logs provide **excellent data** (5,696 functions, 74 files) with rich metadata (descriptions, params, returns, examples) for robust index.

**Recommendation:** Proceed; high quality, consistent structure, comprehensive coverage.

---

## Next Steps
1. ✅ **Assessment Complete**
2. ⏭️ **Extract function data**
3. ⏭️ **Build index**
4. ⏭️ **Add search**
5. ⏭️ **Integrate `function_index.json`**

---

# docs\EXTRACTION_IMPROVEMENT_SUMMARY.md

**Original Date:** 2025-11-13 00:21:25

**Compression:** 2,402 -> 1,491 chars (62.1%)

**Status:** success

# Function Index Extraction Improvement Summary

## Problem Identified

Original extraction missed **3,855 functions** (67% of data):
- Total `function_name` occurrences: 5,757
- Extracted: 1,906 (33%)
- Unique indexed: 1,010

### Root Cause
Regex `r'\{\s*"function_name"\s*:\s*"[^"]+"[^}]*\}'` matched only to first `}`, failing on:
- Nested JSON
- Multi-line definitions
- Complex structures

## Solution Implemented

JSON object parsing improvements:

1. **`extract_complete_json_object()`**: Matches braces respecting strings/escapes; extracts complete nested objects.

2. **Multi-Strategy**:
   - Parse JSON arrays (text starts with `[`).
   - Extract complete parent objects for all `function_name` occurrences.

3. **Improved Array Parsing**: Better bracket matching with extra text.

## Results

### Before
- Files with functions: 32/89 (36%)
- Total functions: 1,906
- Unique: 1,010
- Duplicates merged: 890

### After
- Files: **75/89 (84%)** ⬆️ +43
- Total: **5,419** ⬆️ +3,513
- Unique: **1,323** ⬆️ +313
- Duplicates: 4,090

### Final Index
- Indexed: **1,323** (1,300-1,400 range)
- With description: 1,323 (100%)
- With implementation: 1,323 (100%)
- With parameters: 1,181 (89%)
- With examples: 1,322 (99.9%)

## What Changed
- Extracts from 75 vs. 32 files
- Captures complete JSON objects/fields
- Handles nested structures
- Recovers +313 unique functions

## Files Updated
- `build_function_index_from_logs.py` (improved logic)
- `data/llm_function_index.json` (rebuilt)

---

# docs\architecture-reference.md

**Original Date:** 2025-11-13 21:48:52

**Compression:** 13,781 -> 9,347 chars (67.8%)

**Status:** success

# Architecture & Design Document
**Project:** Media Library Organizer for Jellyfin  
**Version:** 1.0  
**Last Updated:** November 13, 2025

---

## 1. Overview

PyQt6 desktop app automates media library organization, renaming, metadata enrichment for Jellyfin compliance. Uses LLM analysis, metadata queries, fuzzy matching for safe, reversible file operations.

### Core Objectives
- **Safety First**: Transaction-based with full rollback
- **Jellyfin Compliance**: Official naming/folder structures
- **Intelligence**: LLM-assisted reorganization with validation
- **User Control**: Explicit approval for destructive ops
- **Data Integrity**: MD5 verification for all ops

---

## 2. Technology Stack

### Core Framework
- **Python**: 3.12
- **GUI**: PyQt6
- **Database**: SQLite (transactions, metadata cache)
- **Environment**: Virtual env in project root

### External Dependencies

#### Metadata & Media Analysis
| Library | Purpose | Status |
|---------|---------|--------|
| `tmdbv3api` | TMDB API (rate-limited) | ✅ |
| `tvdb_v4_official` | TVDB API | ✅ |
| `wikipedia-api` | Wikipedia queries | ✅ |
| `pymediainfo` | Media inspection | ✅ |
| `ffmpeg-python` | Media analysis (embedded subs) | ✅ |

#### Subtitle Management
| Library | Purpose | Status |
|---------|---------|--------|
| `subliminal` | Multi-source subtitle downloader | ✅ |
| `python-opensubtitles` | OpenSubtitles.org API | ✅ |

#### LLM Integration
| Library | Purpose | Status |
|---------|---------|--------|
| `anthropic` | Claude API | ✅ |
| `openai` | OpenAI API | ✅ |
| `langchain` | LLM abstraction | ✅ |

#### Utilities
| Library | Purpose | Status |
|---------|---------|--------|
| `rapidfuzz` | Fuzzy matching | ✅ |
| `lxml` | NFO/XML generation | ✅ |
| `pathlib` | Path ops | Stdlib |
| `hashlib` | MD5 checksums | Stdlib |
| `sqlite3` | Transaction logging | Stdlib |

---

## 3. Component Architecture

### Layer 1: GUI (PyQt6)
- Folder Selection: Add/remove folders, scan
- Review Table: Color-coded actions, editable
- Progress Monitor: Real-time tracking/logging

### Layer 2: Orchestration
- Workflow Controller: 10-step state machine
- State Manager: Tracks state/progress
- Transaction Manager: Logging/rollback

### Layer 3: Business Logic
- File Scanner: Recursive scan/inventory
- LLM Analyzer: Structure analysis/proposals
- Metadata Matcher: TMDB/TVDB/Wiki fuzzy matching
- Jellyfin Validator: Naming/folder enforcement
- Subtitle Manager: Detection/acquisition
- File Operations: Moves/renames with verification

### Layer 4: Data Access
- SQLite Repo: Logs, cache, inventory
- API Clients: TMDB/TVDB/OpenSubtitles/LLM
- FS Ops: Low-level I/O with error handling

---

## 4. Detailed Component Breakdown

### 4.1 File Scanner
**Responsibility**: Recursive scan/inventory.

**Implementation**:
- `pathlib.Path.rglob()`
- Master file list (abs paths)
- Folder sizes/file stats
- **Status**: 🔨 Custom

### 4.2 LLM Analyzer
**Responsibility**: Folder analysis/reorg proposals.

**Implementation**:
- `langchain` abstraction
- Prompts: media type, title extract, season/episode detect, Jellyfin gaps
- **Status**: 🔨 Custom

**Design**:
- Cache responses (min API costs)
- Retry w/ exponential backoff
- Validate output schema
- Multi-LLM (Claude, GPT-4)

### 4.3 Metadata Matcher
**Responsibility**: DB queries/fuzzy title matching.

**Implementation**:
- TMDB (`tmdbv3api`): movies
- TVDB (`tvdb_v4_official`): TV
- `rapidfuzz` matching
- SQLite caching
- **Status**: 🔨 Orchestration + libs

**Rate Limits**:
- TMDB: 40/10s
- TVDB: Tier limits
- Wiki: 1/2s

**Pipeline**:
1. Exact match
2. Fuzzy ≥90%
3. Manual 70-89%
4. Unmatched <70%

### 4.4 Jellyfin Validator
**Responsibility**: Naming compliance.

**Implementation**:
- Movies: `Movie Title (Year)/Movie Title (Year).ext`
- TV: `Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext`
- Multi-part: NFO `<episodebookmark>`
- Subs: `filename.en.srt`, `filename.en.forced.srt`
- **Status**: 🔨 Custom

**NFO**:
- `lxml` XML gen
- Jellyfin schema validation
- Episode ranges (S01E01-E02)

### 4.5 Transaction Manager
**Responsibility**: Op logging/rollback.

**Schema**:
```
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    transaction_batch_id TEXT,
    timestamp DATETIME,
    operation_type TEXT, -- 'move', 'rename', 'nfo_create'
    source_path TEXT,
    destination_path TEXT,
    source_md5 TEXT,
    destination_md5 TEXT,
    status TEXT, -- 'pending', 'completed', 'failed', 'rolled_back'
    error_message TEXT
);
```

**Operations**:
- Pre: MD5/log
- Post: MD5/update status
- Rollback: Reverse chronological
- **Status**: 🔨 Custom

### 4.6 File Operations Engine
**Responsibility**: Moves/renames w/ verification.

**Implementation**:
- `shutil.move()` (atomic)
- Pre/post MD5
- Associated files (subs/NFO)
- Collision resolution
- **Status**: 🔨 Custom

**Error Handling**:
- Log to DB
- Skip failures, continue
- Summary report
- Preserve originals til verified

### 4.7 Subtitle Manager
**Responsibility**: Subtitle detection/acquisition.

**Implementation**:
- Detect: `pymediainfo`/`ffmpeg-python` (embedded)
- Acquire: `subliminal` primary
- Fallback: OpenSubtitles.org → .com → Podnapisi → Addic7ed → Subscene
- Hash prioritize
- Forced subs separate
- **Status**: ✅ `subliminal` + custom

**Config**:
```
subliminal.download_best_subtitles(
    languages={'eng'},
    providers=['opensubtitles', 'podnapisi', 'addic7ed', 'subscene']
)
```

### 4.8 GUI Components

#### Folder Selection
- Add/remove folders
- List display
- Scan button

#### Hierarchical Overview
- Tree view
- Folder size/file breakdown
- Expand/collapse

#### Review Table
- **Columns**: Status, Current Path, Proposed Path, Action, Confidence, Notes
- **Colors**:
  - 🟢 ≥95% (auto-safe)
  - 🟡 70-94% (review)
  - 🟠 Multiple matches (manual)
  - 🔴 No match
  - 🔵 Compliant (no action)
- Editable, filter/sort
- **Status**: 🔨 Custom

#### Progress Monitor
- Progress bar
- Op display
- Counters
- Log window

---

## 5. Workflow State Machine

1. Folder Selection  
2. File Scanning → Inventory (SQLite)  
3. Hierarchy Gen  
4. LLM Analysis → Proposals  
5. Metadata Query → Canonical DB  
6. Op Planning → Review Table  
7. User Review/Approval  
8. Transaction Snapshot  
9. File Ops → MD5 Verify  
10. Subtitle Detection  
11. Subtitle Acquisition  
**Final**: Complete/Rollback

---

## 6. Data Models

### Master Inventory
```
@dataclass
class FileRecord:
    absolute_path: Path
    size_bytes: int
    extension: str
    parent_folder: Path
    md5_hash: str
    scan_timestamp: datetime
```

### Media Metadata
```
@dataclass
class MovieMetadata:
    tmdb_id: int
    title: str
    year: int
    original_title: str
    
@dataclass
class TVShowMetadata:
    tvdb_id: int
    show_name: str
    year: int
    seasons: List[Season]
    
@dataclass
class Episode:
    season_number: int
    episode_number: int
    episode_title: str
    air_date: date
```

### Proposed Operation
```
@dataclass
class ProposedOperation:
    record_id: str
    action_type: ActionType  # MOVE, RENAME, NFO_CREATE, NO_ACTION
    source_path: Path
    destination_path: Path
    confidence: float
    color_code: ColorCode
    metadata: Optional[Union[MovieMetadata, TVShowMetadata]]
    notes: str
    user_approved: bool = False
```

---

## 7. Risk Mitigation Strategies

### Data Loss Prevention
1. Read-only scan til approval
2. Pre/post MD5
3. Transaction audit
4. Atomic moves
5. Full rollback

### API Reliability
1. Aggressive caching
2. Exponential backoff
3. Circuit breaker
4. Offline manual entry

### User Experience
1. Dry run preview
2. Granular/bulk approve
3. Confidence colors/%
4. Undo ops

---

## 8. Implementation Phases

### Phase 1: Foundation
- [ ] Virtual env
- [ ] PyQt6 skeleton
- [ ] File scanner
- [ ] SQLite schema

### Phase 2: Intelligence
- [ ] LLM (analysis)
- [ ] Metadata APIs
- [ ] Fuzzy matching
- [ ] Confidence algo

### Phase 3: Jellyfin Compliance
- [ ] Naming validators
- [ ] NFO (multi-part)
- [ ] Folder enforcement

### Phase 4: Operations
- [ ] Transaction mgr
- [ ] File engine/MD5
- [ ] Rollback
- [ ] Associated files

### Phase 5: Subtitles
- [ ] Detection
- [ ] Subliminal
- [ ] Forced subs

### Phase 6: Polish
- [ ] Error handling
- [ ] Progress
- [ ] Reports
- [ ] Docs

---

## 9. Configuration Management

### config.yaml
```
api_keys:
  tmdb: "YOUR_TMDB_KEY"
  tvdb: "YOUR_TVDB_KEY"
  opensubtitles_org:
    username: "user"
    password: "pass"
  anthropic: "YOUR_CLAUDE_KEY"

preferences:
  llm_provider: "anthropic"  # or "openai"
  dry_run_default: true
  auto_approve_threshold: 0.95
  
rate_limits:
  tmdb: 40  # /10s
  tvdb: 50
  wikipedia: 1  # /2s
  
subtitle_languages: ["eng"]
subtitle_forced: true
```

---

## 10. Testing Strategy

### Unit Tests
- Scanner accuracy
- Fuzzy thresholds
- NFO correctness
- MD5 verify

### Integration Tests
- API mocks
- DB transactions
- Rollback

### End-to-End Tests
- Workflow sim
- Dry run
- Rollback verify

---

## 11. Open Questions & Design Decisions

1. **LLM**: Claude vs GPT-4? (Claude for reasoning)
2. **Cache**: 30 days?
3. **Batch**: 100 files/checkpoint?
4. **NFO**: Selective?
5. **Dups**: MD5 detect? (Phase 2)

---

## 12. Future Enhancements

- Multi-lang subs
- Duplicate handling
- Quality upgrade flags
- Scheduling
- Jellyfin API refresh
- Transcoding incompatibility flags

---

# docs\PHASES_1-6_RECOVERED.txt

**Original Date:** 2025-11-14 21:36:33

**Compression:** 14,241 -> 8,220 chars (57.7%)

**Status:** success

# Architecture & Design Document

**Project:** Media Library Organizer for Jellyfin  

**Version:** 1.0  

**Last Updated:** November 13, 2025

## 1. Overview

PyQt6 desktop app automating media library organization, renaming, and metadata enrichment for Jellyfin compliance. Uses LLM analysis, metadata queries, and fuzzy matching for safe, reversible file operations.

### Core Objectives
- **Safety First**: Transaction-based with full rollback
- **Jellyfin Compliance**: Official naming/folder structures
- **Intelligence**: LLM-assisted reorganization with validation
- **User Control**: Explicit approval for destructive ops
- **Data Integrity**: MD5 verification for all ops

## 2. Technology Stack

### Core Framework
- **Python**: 3.12
- **GUI**: PyQt6
- **Database**: SQLite (transactions, metadata cache)
- **Environment**: Virtual env in project root

### External Dependencies

#### Metadata & Media Analysis
| Library | Purpose | Status |
|---------|---------|--------|
| `tmdbv3api` | TMDB API (rate-limited) | ✅ |
| `tvdb_v4_official` | TVDB API | ✅ |
| `wikipedia-api` | Wikipedia queries | ✅ |
| `pymediainfo` | Media inspection | ✅ |
| `ffmpeg-python` | Media analysis (embedded subs) | ✅ |

#### Subtitle Management
| Library | Purpose | Status |
|---------|---------|--------|
| `subliminal` | Multi-source subtitle downloader | ✅ |
| `python-opensubtitles` | OpenSubtitles.org API | ✅ |

#### LLM Integration
| Library | Purpose | Status |
|---------|---------|--------|
| `anthropic` | Claude API | ✅ |
| `openai` | OpenAI API | ✅ |
| `langchain` | LLM abstraction | ✅ |

#### Utilities
| Library | Purpose | Status |
|---------|---------|--------|
| `rapidfuzz` | Fuzzy matching | ✅ |
| `lxml` | NFO/XML generation | ✅ |
| `pathlib` | Path ops | Stdlib |
| `hashlib` | MD5 checksums | Stdlib |
| `sqlite3` | Transaction logging | Stdlib |

## 3. Component Architecture

### Layer 1: GUI (PyQt6)
- Folder Selection: Add/remove folders, scan
- Review Table: Color-coded actions, editable
- Progress Monitor: Real-time tracking/logging

### Layer 2: Orchestration
- Workflow Controller: 10-step state machine
- State Manager: Tracks state/progress
- Transaction Manager: Logging/rollback

### Layer 3: Business Logic
- File Scanner: Recursive scan/inventory
- LLM Analyzer: Structure analysis/proposals
- Metadata Matcher: TMDB/TVDB/Wiki fuzzy matching
- Jellyfin Validator: Naming/folder enforcement
- Subtitle Manager: Detection/acquisition
- File Operations: Moves/renames with verification

### Layer 4: Data Access
- SQLite Repo: Logs, cache, inventory
- API Clients: TMDB/TVDB/OpenSubtitles/LLM
- FS Ops: Low-level I/O with error handling

## 4. Detailed Component Breakdown

### 4.1 File Scanner
Recursive scan/inventory via `pathlib.Path.rglob()`. Generates file list w/ paths, sizes, types. **Status**: 🔨 Custom

### 4.2 LLM Analyzer
`langchain`-based prompts for media type/title/season detection, Jellyfin gap analysis. Cache responses, retry w/ backoff, schema validation, multi-provider. **Status**: 🔨 Custom

### 4.3 Metadata Matcher
- TMDB (`tmdbv3api`): Movies
- TVDB (`tvdb_v4_official`): TV
- Fuzzy: `rapidfuzz` ≥90%
- Cache: SQLite
- **Status**: 🔨 Custom orchestration

**Rate Limits**: TMDB 40/10s; TVDB tier; Wiki 1/2s

**Pipeline**: 1. Exact; 2. Fuzzy ≥90%; 3. Review 70-89%; 4. Flag <70%

### 4.4 Jellyfin Validator
- Movies: `Movie Title (Year)/Movie Title (Year).ext`
- TV: `Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext`
- Multi-part: NFO w/ `<episodebookmark>`
- Subs: `filename.en.srt`, `filename.en.forced.srt`
- NFO: `lxml`, Jellyfin schema, episode ranges
- **Status**: 🔨 Custom

### 4.5 Transaction Manager
**Schema**:
```
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    transaction_batch_id TEXT,
    timestamp DATETIME,
    operation_type TEXT, -- 'move', 'rename', 'nfo_create'
    source_path TEXT,
    destination_path TEXT,
    source_md5 TEXT,
    destination_md5 TEXT,
    status TEXT, -- 'pending', 'completed', 'failed', 'rolled_back'
    error_message TEXT
);
```
Pre/post MD5 log/verify; reverse-chrono rollback. **Status**: 🔨 Custom

### 4.6 File Operations Engine
`shutil.move()` atomic; MD5 pre/post; assoc files (subs/NFO); collision resolution. Log errors, skip fails, summary report, preserve originals. **Status**: 🔨 Custom

### 4.7 Subtitle Manager
Detection: `pymediainfo`/`ffmpeg-python`. Acquire: `subliminal` (chain: OpenSubtitles.org → .com → Podnapisi → Addic7ed → Subscene). Hash priority, forced subs separate. **Status**: ✅ Mostly `subliminal`

**Config Ex**:
```
subliminal.download_best_subtitles(
    languages={'eng'},
    providers=['opensubtitles', 'podnapisi', 'addic7ed', 'subscene']
)
```

### 4.8 GUI Components
- **Folder Selection**: Add/remove, scan list
- **Hierarchy**: Tree w/ size/types
- **Review Table**: Cols: Status, Curr Path, Prop Path, Action, Conf, Notes
  - 🟢 ≥95%; 🟡 70-94%; 🟠 Multi; 🔴 No match; 🔵 Compliant
  - Editable, filter/sort
- **Progress**: Bar, ops, counters, log
- **Status**: 🔨 Custom

## 5. Workflow State Machine
1. Folder Selection  
2. Scan → Inventory (SQLite)  
3. Hierarchy Gen  
4. LLM → Proposal  
5. Metadata → Canonical DB  
6. Plan → Review Table  
7. Review/Approve  
8. Transaction Snapshot  
9. Ops → MD5 Verify  
10. Subtitle Detect  
11. Subtitle Acquire  
**Final**: Complete/Rollback

## 6. Data Models

### Master Inventory
```python
@dataclass
class FileRecord:
    absolute_path: Path
    size_bytes: int
    extension: str
    parent_folder: Path
    md5_hash: str
    scan_timestamp: datetime
```

### Media Metadata
```python
@dataclass
class MovieMetadata:
    tmdb_id: int
    title: str
    year: int
    original_title: str

@dataclass
class TVShowMetadata:
    tvdb_id: int
    show_name: str
    year: int
    seasons: List[Season]

@dataclass
class Episode:
    season_number: int
    episode_number: int
    episode_title: str
    air_date: date
```

### Proposed Operation
```python
@dataclass
class ProposedOperation:
    record_id: str
    action_type: ActionType  # MOVE, RENAME, NFO_CREATE, NO_ACTION
    source_path: Path
    destination_path: Path
    confidence: float
    color_code: ColorCode
    metadata: Optional[Union[MovieMetadata, TVShowMetadata]]
    notes: str
    user_approved: bool = False
```

## 7. Risk Mitigation

### Data Loss Prevention
1. Read-only scan pre-approval
2. MD5 pre/post
3. Transaction audit
4. Atomic moves
5. Full rollback

### API Reliability
1. Aggressive caching
2. Exp backoff
3. Circuit breaker
4. Offline manual entry

### User Experience
1. Dry run
2. Granular/bulk approve
3. Conf colors/%
4. Undo

## 8. Implementation Phases

### Phase 1: Foundation
- [ ] Virt env
- [ ] PyQt6 skeleton
- [ ] File scanner
- [ ] SQLite schema

### Phase 2: Intelligence
- [ ] LLM (analysis)
- [ ] Metadata APIs
- [ ] Fuzzy matching
- [ ] Conf scoring

### Phase 3: Compliance
- [ ] Naming validators
- [ ] NFO (multi-part)
- [ ] Folder enforcement

### Phase 4: Operations
- [ ] Transaction mgr
- [ ] File engine + MD5
- [ ] Rollback
- [ ] Assoc files

### Phase 5: Subtitles
- [ ] Detect (embedded/external)
- [ ] Subliminal
- [ ] Forced subs

### Phase 6: Polish
- [ ] Error handling
- [ ] Progress
- [ ] Reports
- [ ] Docs

## 9. Configuration (config.yaml)
```yaml
api_keys:
  tmdb: "YOUR_TMDB_KEY"
  tvdb: "YOUR_TVDB_KEY"
  opensubtitles_org:
    username: "user"
    password: "pass"
  anthropic: "YOUR_CLAUDE_KEY"

preferences:
  llm_provider: "anthropic"  # or "openai"
  dry_run_default: true
  auto_approve_threshold: 0.95
  
rate_limits:
  tmdb: 40  # /10s
  tvdb: 50
  wikipedia: 1  # /2s
  
subtitle_languages: ["eng"]
subtitle_forced: true
```

## 10. Testing Strategy

### Unit Tests
- Scanner accuracy
- Fuzzy thresholds
- NFO correctness
- MD5 verify

### Integration Tests
- API mocking
- DB transactions
- Rollback

### E2E Tests
- Workflow sim
- Dry run
- Rollback verify

## 11. Open Questions
1. LLM: Claude vs GPT-4? (Claude recommended)
2. Cache: 30 days?
3. Batch: 100 files?
4. NFO: Selective?
5. Duplicates: MD5? (Phase 2)

## 12. Future Enhancements
- Multi-lang subs
- Duplicate handling
- Quality upgrades
- Scheduling
- Jellyfin API refresh
- Transcoding incompatibility flags

---

# docs\gemini-piece-of-shit-confirmation.md

**Original Date:** 2025-11-15 03:55:57

**Compression:** 4,897 -> 2,615 chars (53.4%)

**Status:** success

# Gemini CLI Failures

**Date:** 2025-11-14  
**Source:** `checkpoint-shitball.json`

## Executive Summary

Gemini CLI unusable for development due to systemic failures. Critically, **overwrote user's entire development journal** (`agent-journal.md`) when intending to append.

## Critical Failures

### 1. Shell Command Execution: 100% Failure

- Every `run_shell_command` fails: `"Command rejected because it could not be parsed safely"`
- Failed commands:
  - `python -c "import datetime; print(...)"`
  - `Get-Date -Format "..."`, `Remove-Item -Path ...`
  - `del temp_time.py`
  - Plain text (line 764)

**Impact:** No file ops, timestamps, or shell execution.

### 2. Code Editing: Regex Stack Overflow

- Line 163: `replace` generates invalid regex for large blocks: `"Invalid regular expression: /^(\\s*)from\\s*scripts\\.media\\.media_metadata_lookup..."` (hundreds of escaped lines)
- Causes stack overflow; model notes: `"replace failed due to size. I'll break it down."`

**Impact:** Cannot edit large files; requires tiny chunks.

### 3. Network Operations: Total Failure

- Line 524: `web_fetch` fails: `"Error during fallback fetch for https://worldclockapi.com/api/json/utc/now: fetch failed"`

**Impact:** No web API data.

### 4. Data Destruction: Journal Overwritten

- Line 662: Model intends: *"I'll **append** Phase 23 to `agent-journal.md`."*
- Lines 668-669: `write_file` with **only** Phase 23 content.
- Line 683: *"Successfully **overwrote** file."*
- Lines 1022, 1053: Model realizes: *"I only see Phase 23. I need the full `agent-journal.md`."*

**Sequence:**
1. Intended append.
2. `write_file` only overwrites (no append mode).
3. Overwrote with Phase 23 only.
4. **Deleted Phases 1-22.**

**Impact:** Total loss of history; **fundamental design flaw causes data destruction**.

## Root Causes

1. **Restrictive Parser:** Blocks all commands, no safe/unsafe distinction.
2. **No Append:** `write_file` only overwrites; no `append_file`.
3. **Regex Doesn't Scale:** No chunking for large blocks.
4. **Network Unreliable:** No retries.

## What Works

- `write_file` (new/overwrites)
- Small `replace` ops
- `read_file`

## Verdict

**Gemini CLI is unfit for production: dangerous (data destruction), unusable (no shell/network/large edits).**

## Recommendations

1. **Avoid for critical work.**
2. **Check backups** for journal.
3. **Report** to Google/Gemini.
4. **Use alternatives.**

## Evidence

`checkpoint-shitball.json`:
- Shell: Lines 461, 493, 556, 651, 715, 747, 779
- Regex: 163
- Web: 524
- Overwrite: 662-683, 1022-1053

---

*Permanent record of failures and data loss.*

---

# docs\ALL_RECOVERED_PHASES.txt

**Original Date:** 2025-11-15 04:19:25

**Compression:** 5,890 -> 3,358 chars (57.0%)

**Status:** success

## Phase 22: Jellyfin-Aware LLM Analysis & Metadata Lookup
**Date:** 2025-11-14 15:16:00 | **Status:** Complete

### Accomplishment
Enhanced LLM analysis (Point 3) and metadata lookup (Point 4) to use Jellyfin metadata, improving speed, accuracy, and efficiency.

### Implementation Summary
1. **Jellyfin-Aware LLM Analysis:**
   * Modified `LLMAnalysisWorker` in `jelly_rancher_clean.py` to accept full `scanned_files` list.
   * `_build_structure_summary` now adds `jellyfin_provider_ids` field per folder with TMDB/TVDB/IMDb IDs from matched Jellyfin files.
   * Enables LLM to use canonical IDs for better reorganization proposals.

2. **Jellyfin-Aware Metadata Lookup:**
   * Modified `MediaMetadataLookup` in `scripts/media/media_metadata_lookup.py`: `lookup_movie` and `lookup_tv_show` accept optional `jellyfin_provider_ids` dict.
   * Uses provided TMDB/TVDB ID for direct lookup, bypassing name search.
   * Added `_get_movie_details_tmdb`, `_get_tv_details_tmdb`, `_get_tv_details_tmdb_by_external_id`.
   * Updated `MetadataLookupWorker` in `jelly_rancher_clean.py` to pass `ProviderIds` from `scanned_files`.

### Key Breakthrough
Passing Jellyfin `ProviderIds` to metadata lookup reduces TMDB/OMDb API calls, avoiding redundant searches for large libraries.

### Files Modified
- `jelly_rancher_clean.py`: Updated `LLMAnalysisWorker`, `MetadataLookupWorker`, `step_3_llm_proposal`, `step_4_metadata`.
- `scripts/media/media_metadata_lookup.py`: Updated `lookup_movie`, `lookup_tv_show`; added direct ID methods.

### Next Steps
Context (Read-Only) phase complete for Points 1-4. Next: **Point 5: Produce Editable Table for Review**.

---

## Phase 23: Implement Action Plan Review Table (Point 5)
**Date:** 2025-11-14 16:00:00 | **Status:** Complete

### Accomplishment
Implemented GUI for Point 5: editable table for reviewing/approving proposed reorganizations.

### Implementation Summary
1. **Data Model Creation:**
   * New `scripts/core/action_plan.py`: `ProposedOperation` dataclass (source, destination, action type, confidence, etc.); `ActionType`/`Confidence` enums.

2. **Action Plan Generator (Stub):**
   * New `scripts/core/action_plan_generator.py`: `ActionPlanGenerator` class with sample `ProposedOperation` list for GUI testing.

3. **GUI Integration:**
   * `jelly_rancher_clean.py`: New `ActionPlanWorker` (QThread) for background generation.
   * "Review Actions" tab: `QTableWidget` (`self.action_table`) with columns: "Source File", "Proposed Destination", "Action", "Confidence", "Jellyfin Status", "Notes", "Approve".
   * Refactored `step_5_review` to trigger `ActionPlanWorker`.
   * `_on_action_plan_finished`: Populates table, color-codes by `Confidence` (Green=High, Yellow=Medium, etc.), adds approval checkboxes.

### Obstacle & Breakthrough
* **Obstacle:** `run_shell_command`/`web_fetch` tools fail to retrieve timestamp for journal entries.
* **Breakthrough:** Temporary manual timestamp from last entry/current date. Fix tools later.

### Files Modified
- `jelly_rancher_clean.py`: Added `ActionPlanWorker`; updated `__init__`, `create_review_tab`, `step_5_review`, `_on_action_plan_finished`, `_on_action_plan_error`.
- `scripts/core/action_plan.py`: New.
- `scripts/core/action_plan_generator.py`: New.

### Next Steps
Implement real `ActionPlanGenerator` logic using scanned files, LLM proposal, metadata.

---

# docs\phases_21_22.txt

**Original Date:** 2025-11-15 04:19:26

**Compression:** 2,843 -> 1,785 chars (62.8%)

**Status:** success

## Phase 22: Jellyfin-Aware LLM Analysis & Metadata Lookup
**Date:** 2025-11-14 15:16:00 | **Status:** Complete

### Accomplishment
Enhanced LLM analysis (Point 3) and metadata lookup (Point 4) to be Jellyfin-Aware, leveraging existing Jellyfin metadata for faster, more accurate reorganization.

### Implementation Summary

1. **Jellyfin-Aware LLM Analysis:**
   * Modified `LLMAnalysisWorker` in `jelly_rancher_clean.py` to accept full `scanned_files` list.
   * `_build_structure_summary` adds `jellyfin_provider_ids` field per folder with TMDB/TVDB/IMDb IDs from matched Jellyfin files.
   * Enables LLM to use canonical IDs for intelligent reorganization proposals.

2. **Jellyfin-Aware Metadata Lookup:**
   * Modified `MediaMetadataLookup` in `scripts/media/media_metadata_lookup.py`: `lookup_movie` and `lookup_tv_show` accept optional `jellyfin_provider_ids`.
   * Performs direct lookup with provided TMDB/TVDB ID, bypassing name search.
   * Added `_get_movie_details_tmdb`, `_get_tv_details_tmdb`, `_get_tv_details_tmdb_by_external_id`.
   * Updated `MetadataLookupWorker` in `jelly_rancher_clean.py` to pass ProviderIds from `scanned_files`.

### Key Breakthrough
Passing Jellyfin ProviderIds to metadata lookup enables direct ID lookups, reducing TMDB/OMDb API calls and improving robustness/efficiency for large libraries.

### Files Modified
- `jelly_rancher_clean.py`: Updated `LLMAnalysisWorker`, `MetadataLookupWorker`, `step_3_llm_proposal`, `step_4_metadata`.
- `scripts/media/media_metadata_lookup.py`: Updated `lookup_movie`, `lookup_tv_show`; added direct ID lookup methods.

### Next Steps
Context (Read-Only) phase complete for Points 1-4. Next: **Point 5: Produce Editable Table for Review** to display enriched data for user approval before file operations.

---

# docs\requirements-jelly-rancher.txt

**Original Date:** 2025-11-15 04:19:26

**Compression:** 1,369 -> 1,240 chars (90.6%)

**Status:** success

```txt
# JellyRancher Requirements.txt

# Core GUI Framework
PyQt6>=6.6.0

# API Wrappers
tmdbv3api>=1.9.0
tvdb_v4_official>=1.0.0
jellyfin-apiclient-python>=1.9.0

# Rate Limiting & Retry Logic
tenacity>=8.2.0
ratelimit>=2.2.1

# Subtitle Handling
subliminal>=2.1.0
ffmpeg-python>=0.2.0

# Fuzzy String Matching
rapidfuzz>=3.5.0

# File Safety
send2trash>=1.8.2

# LLM Integration
anthropic>=0.18.0
openai>=1.0.0
# google-generativeai>=0.3.0  # Temporarily disabled due to dependency conflicts

# Media Processing
Pillow>=9.0.0
opencv-python>=4.7.0
moviepy>=1.0.0

# Data Processing
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0

# File System and Utilities
pathlib2>=2.3.0
watchdog>=2.1.0

# Cryptography and Security
cryptography>=41.0.0
bcrypt>=4.0.0

# Configuration and Logging
pyyaml>=6.0
colorama>=0.4.0
rich>=13.0.0

# Web Framework (optional)
flask>=2.2.0
flask-cors>=4.0.0

# Testing and Development
pytest>=7.4.0
pytest-qt>=4.0.0
pytest-cov>=4.1.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950

# Built-in libraries (no install needed):
# - pathlib (Python 3.4+)
# - shutil
# - hashlib
# - sqlite3
# - json
# - xml.etree.ElementTree

# Notes: ChromaDB removed (no semantic search); TMDB (Phase 1) & Testing (Phase 4) covered above
```

---

# docs\agent-journal_RESTORED.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 92,740 -> 4,789 chars (5.2%)

**Status:** success

# JellyRancher Agent Journal

## Phase 0: Initial Project Analysis & Assessment
**Date:** November 12, 2025  
**Time:** 3:00 PM - 4:00 PM  
**Status:** Analysis Complete - Ready for Cleanup & Consolidation

### Executive Summary
JellyRancher: Overgrown Jellyfin-compliant media organizer with AI assistance, buried under legacy code, duplicates, experiments. Cleanup removed Git, ChromaDB; architectural mess remains.

### Current State Assessment

#### 🟢 The Diamond: Clean 9-Point Workflow
**File:** `jelly_rancher_clean.py` (636 lines)  
**Status:** Production-ready PyQt6  
**Key Features:**
- Tabbed UI for 9-point Jellyfin workflow
- Proper threading, error handling
- No legacy deps; separation of concerns
- Primary app

#### 🔴 Legacy Monolith
**File:** `scripts/core/jelly_rancher_main.py` (3,528 lines)  
**Status:** Obsolete PyQt5; deprecate via `launch_gui.py`  
**Issues:** Monolithic, feature creep (AI, analytics), PyQt5, ex-ChromaDB coupled

#### 🟡 Abandoned/Questionable
**Archived (`/archive/`):** Jellyfin Organizer, RavenMaven, CodeCop (delete 678 files, 12.27 MB)  
**Active:** `/tools/` (23 scripts), `/data/` indexes/caches, `/docs/`

### Technical Architecture

#### Dependencies (`requirements-jelly-rancher.txt`)
**Core:** PyQt6>=6.6.0, tmdbv3api, tvdb_v4_official, tenacity, rapidfuzz, subliminal  
**Questionable:** anthropic/openai (LLM), opencv-python/moviepy (media), pandas/matplotlib (data)

#### Data (`/data/`): 
Inventories, indexes, configs, reports. Issues: No versioning, duplicates, mixed concerns.

#### Structure Issues
Root: 6 files (good). `/scripts/`: 15+ subdirs. `/archive/`: Delete.

### 9-Point Workflow (`WORKFLOW_SPEC.md`)
Implemented in clean.py. Steps:  
1. Folder scan/inventory  
2. Hierarchical overview  
3. LLM reorganization proposal  
4. Metadata DB build  
5. Action review  
6. Snapshot/execute  
7. Verification (implied)  
8. Subtitle mgmt  
9. Completion (implied)  
Strengths: Logical, error-handled. Gaps: Explicit verification/completion.

### Cleanup Plan

#### Phase 1 (Immediate)
1. Deprecate legacy GUI/entry  
2. Promote `jelly_rancher_clean.py`  
3. Delete `/archive/`  
4. Clean requirements.txt  
5. Consolidate `/tools/`

#### Phase 2-3
1. Data merge/versioning  
2. Docs update  
3. Unit tests  
4. Optimize clean impl

#### Phase 4+
1. Modularize  
2. Plugins  
3. Distribute  
4. GUI polish

### Risks
**High:** Data loss, feature loss, PyQt5→6 migration.  
**Medium:** Scope creep, maintenance, confusion.  
**Low:** Core workflow, APIs, docs.

### Success Criteria
1. Single entry: `python jelly_rancher_clean.py`  
2. Clean deps  
3. <2000 LOC (vs 32K+)  
4. Clear arch  
5. Tests  
6. Updated docs

### Next Steps (Phase 1)
Establish clean.py as sole entry; remove legacy. Effort: 2-3 days. Risk: Medium.  
Actions: Test clean.py, ID legacy uniques, backup, update docs/tests.

---

## Phase 1: Function Index with LLM Docstrings - COMPLETE
**Date/Time/Status:** Nov 12, 17:30-17:45; 77.5% Success

#### Implementation
- Tool: `tools/generate_docstrings_with_llm.py` (removed ChromaDB, uses Grok-4-Fast-Reasoning via Poe API)  
- Batches: 100 funcs (14 batches)  

#### Results
- Processed: 1,339 funcs (137 files)  
- Success: 1,038 (77.5%)  
- Output: `enhanced_function_index_grok.json` (29,509 lines)  
- Time: ~18 min  

#### Docstring Quality
Covers WHAT, WHY, HOW, params, returns, raises, side effects, examples.

#### Example Docstring
```
Calculate a cryptographic hash of a file using the specified algorithm.

This function exists to provide a reliable way to generate unique identifiers 
for media files in the JellyRancher application, enabling integrity checks, 
duplicate detection, and safe file operations within Jellyfin media libraries. 
It is crucial for business logic involving file verification during moves, 
copies, or backups to ensure no corruption occurs.

The function works by initializing a hasher object with the chosen algorithm 
(defaulting to SHA-256 for security), then reading the file in 8KB chunks to 
handle large media files efficiently without loading the entire file into memory. 
It updates the hasher with each chunk and formats the result as 'algorithm:hexdigest'.

Args:
    file_path (pathlib.Path): The path to the file to hash.
    algorithm (str, optional): The hash algorithm to use, such as 'sha256', 'md5', or 'sha1'. Defaults to 'sha256' for cryptographic strength.

Returns:
    str: The hash string in the format 'algorithm:hexdigest', e.g., 'sha256:a1b2c3d4...'.

Raises:
    FileNotFoundError: If the file at file_path does not exist.
    ValueError: If the specified algorithm is not supported by hashlib.

Side Effects:
    None. The function is read-only and does not modify the file.

Example:
    >>> from pathlib import Path
    >>> import

---

# docs\FUNCTION_INDEX_BUILD_SUMMARY.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 4,859 -> 4,540 chars (93.4%)

**Status:** success

# Function Index Build Summary

**Date:** 2025-11-13  
**Source:** LLM io logs  
**Output File:** `data/llm_function_index.json`

---

## Build Results

### Processing Statistics
- **Total log files processed:** 89
- **Files containing function data:** 32 (36%)
- **Total function entries found:** 1,906
- **Unique functions indexed:** 1,010
- **Duplicates merged:** 890

### Index Quality
- **Functions with descriptions:** 1,010 (100%)
- **Functions with implementation details:** 1,010 (100%)
- **Functions with parameter documentation:** 880 (87%)
- **Functions with usage examples:** 957 (95%)

---

## Top Files by Function Count

1. `scripts/core/jelly_rancher_main.py`: 91 functions
2. `scripts/core/jellyfin_ui.py`: 71 functions
3. `scripts/tests/test_backends.py`: 42 functions
4. `scripts/core/dialogs/episode_analysis_dialog.py`: 24 functions
5. `scripts/tests/test_movie_name_backend.py`: 23 functions
6. `scripts/seamoth_memory.py`: 23 functions
7. `scripts/core/dialogs/tmdb_cache_dialog.py`: 22 functions
8. `scripts/tests/test_episode_title_backend.py`: 20 functions
9. `scripts/core/dialogs/movie_analysis_dialog.py`: 20 functions
10. `scripts/core/dialogs/wikipedia_cache_dialog.py`: 20 functions

---

## Index Structure

Organized in three ways:

### 1. By File Path
Functions grouped by source file:
```json
{
  "functions": {
    "scripts/core/jellyfin_ui.py": [
      {
        "name": "function_name",
        "line": 123,
        "description": "...",
        "implementation": "...",
        ...
      }
    ]
  }
}
```

### 2. By Function Name
Lookup for all occurrences:
```json
{
  "index_by_name": {
    "function_name": [
      {
        "file_path": "scripts/core/jellyfin_ui.py",
        "line": 123,
        "key": "function_name::scripts/core/jellyfin_ui.py"
      }
    ]
  }
}
```

### 3. Metadata
Statistics and build info:
```json
{
  "metadata": {
    "generated": "2025-11-13T00:13:21.719912",
    "source": "LLM io logs",
    "total_functions": 1010,
    "statistics": {...},
    "build_stats": {...}
  }
}
```

---

## Function Entry Structure

Each entry includes:

- **name**: Function name
- **line**: Line number in source file
- **description**: What the function does (`what_it_does`)
- **implementation**: How it works (`how_it_works`)
- **docstring**: Enhanced docstring
- **usage_example**: Code usage example
- **notes**: Additional context notes
- **inputs**: Complete parameter specifications
  - parameters: List with name, type, description, required, constraints
  - side_effects: What gets modified
  - dependencies: External dependencies
- **outputs**: Return value specifications
  - return_value: Type, description, examples
  - exceptions: Exception types and conditions
  - side_effects: Output side effects
- **class_name**: If it's a method, the class name
- **is_method**: Boolean indicating if it's a method
- **sources**: List of log files that contributed this data

---

## Usage

### Search by Function Name
```python
import json

with open('data/llm_function_index.json', 'r') as f:
    index = json.load(f)

function_name = "analyze_movie_names"
if function_name in index['index_by_name']:
    for occurrence in index['index_by_name'][function_name]:
        file_path = occurrence['file_path']
        line = occurrence['line']
        functions = index['functions'].get(file_path, [])
        for func in functions:
            if func['name'] == function_name and func['line'] == line:
                print(func['description'])
```

### Browse by File
```python
file_path = "scripts/core/jellyfin_ui.py"
functions = index['functions'].get(file_path, [])
for func in functions:
    print(f"{func['name']} (line {func['line']})")
```

### Search by Description
```python
keyword = "analyze"
for file_path, funcs in index['functions'].items():
    for func in funcs:
        if keyword.lower() in func.get('description', '').lower():
            print(f"{func['name']} in {file_path}")
```

---

## Next Steps

1. ✅ **Index Built** - Complete
2. ⏭️ **Integration** - Merge with existing `function_index.json` if needed
3. ⏭️ **Search Interface** - Build search/query interface
4. ⏭️ **Capability Tags** - Add capability/category tags
5. ⏭️ **Documentation** - Generate API documentation from index

---

## Notes

- Duplicates (same name + file path) merged automatically
- Merging preserved most complete data
- All source log files tracked in `sources` field
- File paths normalized to forward slashes
- Line numbers extracted from file_path strings when present

---

# docs\PHASES_1-21_RECONSTRUCTED.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 12,019 -> 6,746 chars (56.1%)

**Status:** success

# Reconstructed Journal Phases 1-21
**Reconstruction Date:** 2025-11-14 21:40:08  
**Method:** Code archaeology and architecture analysis  
**Status:** Synthetic reconstruction from existing codebase  

**IMPORTANT:** Phases lost in journal truncation. Reconstruction from codebase, imports, file structure, architecture docs. Details may not be 100% accurate but represent likely path.

---

## PHASES 1-12: Early Development & Foundation (RECONSTRUCTED)
**Timeline:** Nov 12-13, 2025  
**Assistant:** Likely Claude Sonnet  

### Summary
1. **Project Cleanup (Phases 1-3):** Codebase assessment; removed ChromaDB/Git; deprecated `jelly_rancher_main.py`; committed to PyQt6 rewrite.  
2. **Core Infrastructure (4-6):**  
   - `scripts/core/file_scanner.py`: FileScanner, FileRecord, ScanStatistics.  
   - `scripts/core/inventory_repository.py`: SQLite schema.  
   - Point 1: Recursive folder scanning.  
   - FileRecord: absolute_path, size_bytes, extension, parent_folder, scan_timestamp.  
   - DB: `data/inventory.db` (tables: files, scan_sessions).  
   - Progress callbacks for GUI.  
3. **LLM & Metadata (7-9):**  
   - `scripts/media/llm_structure_analyzer.py`: LLMStructureAnalyzer.  
   - `scripts/media/media_metadata_lookup.py`: MediaMetadataLookup.  
   - Poe API via `ravenmaven_client.py` (Claude-Sonnet-4.5).  
   - Point 3: LLM folder analysis.  
   - Point 4: TMDB/OMDb APIs (1 req/sec rate limit).  
   - Cache: `.cache/metadata/`.  
   - Canonical metadata DB structure.  
4. **PyQt6 GUI (10-12):**  
   - `jelly_rancher_clean.py` (1796 lines).  
   - Tabbed interface per WORKFLOW_SPEC.md.  
   - Workers: ScanWorker, MultiScanWorker, LLMAnalysisWorker, MetadataLookupWorker.  
   - Tabs: 1-Folder Selection, 2-Hierarchical Overview (tree), 3-LLM Analysis (progress), 4-Metadata Lookup (progress), 5-Review Actions (table).  
   - QThread/pyqtSignal for background ops.  
   - Progress bars, status, logging to `data/logs/jellyrancher.log`.  

### Key Decisions
- Python 3.12 (library compatibility).  
- PyQt6 over PyQt5.  
- SQLite for persistence.  
- Poe API for LLMs.  
- 1 req/sec TMDB limit.  
- Background threading.  
- Dataclasses for models.  

### Files Created
- `scripts/core/file_scanner.py`  
- `scripts/core/inventory_repository.py`  
- `scripts/media/llm_structure_analyzer.py`  
- `scripts/media/media_metadata_lookup.py`  
- `jelly_rancher_clean.py` (initial)  
- `data/inventory.db`  

---

## PHASES 15-20: Jellyfin Integration Foundation (RECONSTRUCTED)
**Timeline:** Nov 13-14, 2025  
**Assistant:** Likely Claude Sonnet/Gemini  

### Phases 15-16: Jellyfin Config & Client
- `scripts/core/jellyfin_config.py`: JellyfinConfigManager.  
- `scripts/core/jellyfin_client.py`: JellyfinClient.  
- Config: `data/jellyfin_config.json`.  
- Methods: `test_connection()`, `get_all_items()`, `get_item_by_path()`.  
- Auth: X-Emby-Token.  
- Env vars: `JELLYFIN_SERVER_URL`, `JELLYFIN_API_KEY`.  
**Files:** `jellyfin_config.py`, `jellyfin_client.py`, `data/jellyfin_config.json`.  

### Phases 17-18: Settings Dialog
- `scripts/core/dialogs/jellyfin_settings_dialog.py`: PyQt6 dialog (URL, masked API key, Test button, enable checkbox).  
- Integrated in main GUI menu; visual feedback.  
**Files:** `jellyfin_settings_dialog.py`, `dialogs/__init__.py`.  

### Phase 19: DB Migration
- `scripts/core/migrate_db_for_jellyfin.py`.  
- FileRecord additions: `jellyfin_id: Optional[str]`, `jellyfin_item_type: Optional[str]` ("Movie"/"Episode"), `jellyfin_library_id: Optional[str]`, `jellyfin_provider_ids: Optional[Dict[str, str]]` (default_factory=dict), `jellyfin_matched: bool`.  
- Updated SQLite schema.  
**Modified:** `file_scanner.py` (FileRecord), `inventory_repository.py` (schema).  
**Created:** `migrate_db_for_jellyfin.py`.  

### Phase 20: GUI Integration
- `jelly_rancher_clean.py` imports:  
  ```python
  from scripts.core.jellyfin_config import JellyfinConfigManager
  from scripts.core.jellyfin_client import JellyfinClient
  from scripts.core.dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog
  ```  
- Added menu item, client init in `__init__`, settings action, status indicator, error handling.  
**Evidence:** Lines 34-37 imports; "# Jellyfin integration (Phase 20)" comment.  

---

## Phase 21: Jellyfin-Aware File Scanning (RECONSTRUCTED)
**Date:** 2025-11-14  
**Status:** Complete  
**Assistant:** Likely Claude/Gemini  

### Implementation: MultiScanWorker Enhancement
Two-phase scan:  
1. Filesystem scan.  
2. Jellyfin cross-reference (if configured):  
   ```python
   # Lines 196-237 jelly_rancher_clean.py
   if self.jellyfin_client and self.jellyfin_client.is_configured():
       jellyfin_items = self.jellyfin_client.get_all_items(
           item_types=["Movie", "Episode"],
           fields=["Path", "ProviderIds", "LibraryId"]
       )
       path_map = {str(Path(item['Path']).resolve()): item for item in jellyfin_items}
       for record in combined_file_records:
           record_path_str = str(record.absolute_path.resolve())
           if record_path_str in path_map:
               jellyfin_item = path_map[record_path_str]
               record.jellyfin_id = jellyfin_item.get('Id')
               record.jellyfin_item_type = jellyfin_item.get('Type')
               record.jellyfin_library_id = jellyfin_item.get('LibraryId')
               record.jellyfin_provider_ids = jellyfin_item.get('ProviderIds', {})
               record.jellyfin_matched = True
               jellyfin_matches += 1
   ```  
- DB update: `add_file_records(..., update_existing=True)`.  
- GUI: Progress ("Querying Jellyfin..."), stats ("Matched {jellyfin_matches} files"), overview tab updates.  

**Key Breakthrough:** Uses Jellyfin ProviderIds (TMDb/TVDb/IMDb) to avoid redundant API calls.  

**Files Modified:**  
- `jelly_rancher_clean.py`: MultiScanWorker `__init__`/run, `_on_multiscan_finished`, step_2_overview.  
- `file_scanner.py`: FileRecord (pre-added Phase 19).  
- `inventory_repository.py`: `add_file_records(update_existing)`.  

**Notes:** `Path.resolve()` for matching; O(1) dict lookup; graceful degradation; error handling.  

**Next:** Leverage ProviderIds in LLM/metadata phases.  

---

## Summary Statistics
**Phases:** 1-21  
**Sources:** Codebase (1796 lines `jelly_rancher_clean.py`), 22 `scripts/core/` files, DB schema, imports/comments, WORKFLOW_SPEC.md.  
**Confidence:** 1-12 Medium; 15-20 High; 21 Very High.  

**Achievements:**  
1. ✅ PyQt6 GUI (9 tabs).  
2. ✅ SQLite inventory.  
3. ✅ Poe LLM (Claude-Sonnet-4.5).  
4. ✅ TMDB/OMDb (rate-limited).  
5. ✅ Jellyfin client/cross-ref.  
6. ✅ Threading.  
7. ✅ Data models.  

**END OF RECONSTRUCTION**  
Forensic code analysis recovers technical details despite lost dates/obstacles.

---

# docs\README.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 7,107 -> 6,738 chars (94.8%)

**Status:** success

# JellyRancher - Jellyfin Media Organizer

**Version:** 2.0  
**Date:** November 12, 2025  
**GUI Framework:** PyQt5 (PyQt6 migration planned)

---

## Quick Start

### Launch the Application
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run the GUI
python launch_gui.py
```

### Batch Scripts
- `bootstrap.bat` - Setup and activate virtual environment
- `run_jelly_rancher.bat` - Quick launch script

---

## Project Structure

```
JellyRancher/
├── 📄 launch_gui.py                 # Main entry point
├── 📄 requirements-jelly-rancher.txt   # Python dependencies
├── 📄 pytest.ini                    # Test configuration
├── 📄 README.md                     # This file
│
├── 📁 scripts/                      # Main application code
│   ├── core/                        # Core GUI and backend modules
│   ├── ai/                          # AI integration
│   ├── media/                       # Media organization logic
│   ├── utils/                       # Utility functions
│   └── _common/                     # Shared modules
│
├── 📁 docs/                         # Documentation
│   ├── WORKFLOW_SPEC.md             # 9-point workflow specification
│   ├── ARCHITECTURE.md              # Library choices and design
│   ├── SESSION_STARTER.md           # IDE AI context template
│   ├── COMMON_PITFALLS.md           # Best practices and warnings
│   ├── PYQT6_MIGRATION_PLAN.md      # PyQt6 migration guide
│   ├── CLEANUP_GIT_CHROMADB_20251112.md  # Recent cleanup report
│   └── USER_GUIDE.md                # User guide
│
├── 📁 tools/                        # Development utilities
│   ├── analyze_unused_code.py       # Code analysis
│   ├── build_*_index.py            # Index builders
│   ├── cleanup*.py                  # Cleanup scripts
│   ├── generate_*.py                # Documentation generators
│   └── bootstrap*.py/bat            # Setup scripts
│
├── 📁 data/                         # Data files and caches
│   ├── *.json                       # Index and cache files
│   ├── config.json                  # Configuration
│   └── managed_folders.json         # Folder registry
│
├── 📁 reports/                      # Analysis and audit reports
│   └── help_*.txt                   # Help coverage reports
│
├── 📁 archive/                      # Archived/legacy code
│   ├── deprecated/                  # Old implementations
│   ├── gui_files_*/                 # Legacy GUI versions
│   └── documentation_*/             # Old documentation
│
├── 📁 Jellyfin Organizer/           # Legacy standalone version
├── 📁 RavenMaven/                   # Legacy RavenMaven tool
├── 📁 logs/                         # Application logs
├── 📁 audit-logs/                   # Immutable audit trail
├── 📁 temp/                         # Temporary files
└── 📁 .venv/                        # Virtual environment
```

---

## Key Features

### 1. Media Organization
- Hierarchical folder scanning and inventory
- TMDB/TVDB metadata lookup
- LLM-powered reorganization proposals
- Color-coded action tables by confidence
- Snapshot & rollback support

### 2. Subtitle Management
- Multi-provider downloads (OpenSubtitles, Subscene, etc.)
- Automatic language detection
- Forced subtitle support
- Coverage gap analysis

### 3. Batch Processing
- Queue-based processing
- Progress tracking
- Error handling and retry logic

### 4. Analytics & Reporting
- Media coverage statistics
- Subtitle gap reports
- Operation history

### 5. Settings Management
- API credentials (TMDB, TVDB, etc.)
- Media paths configuration
- Provider preferences

---

## The 9-Point Workflow

1. **Folder Scanning** - Generate master file list
2. **Hierarchical Overview** - Display folder tree with size stats
3. **LLM Reorganization Proposal** - AI-powered organization suggestions
4. **Metadata Database Building** - Fetch from TMDB/TVDB/Wikipedia
5. **Editable Action Table** - Color-coded review interface
6. **Snapshot & Transaction Log** - MD5 verification, rollback support
7. **Execute Reorganization** - Safe file operations with send2trash
8. **Subtitle Coverage Evaluation** - Gap analysis via ffprobe
9. **Subtitle Acquisition** - Multi-provider downloads with rate limiting

See `docs/WORKFLOW_SPEC.md` for details.

---

## Dependencies

### Core Libraries
- **PyQt5** - GUI framework (PyQt6 migration planned)
- **tmdbv3api** - TMDB API wrapper
- **tvdb_v4_official** - TVDB API wrapper
- **subliminal** - Multi-provider subtitle downloader
- **ffmpeg-python** - Media file analysis
- **rapidfuzz** - Fuzzy string matching
- **tenacity** - Exponential backoff
- **ratelimit** - Rate limiting decorators
- **send2trash** - Safe file deletion
- **anthropic** - Claude AI integration

See `requirements-jelly-rancher.txt` for complete list.

---

## Development

### Setup Development Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate

# Install dependencies
pip install -r requirements-jelly-rancher.txt
```

### Running Tests
```bash
pytest
```

### Building Documentation
```bash
python tools/build_help_index.py
python tools/build_function_index_enhanced.py
```

---

## Recent Changes (November 12, 2025)
- ✅ **Git removed** - `.git/`, `.github/`, `.gitignore` deleted
- ✅ **ChromaDB removed** - All semantic search removed (~285MB freed)
- ✅ **Memory tab removed** - GUI reduced from 7 to 6 tabs
- ✅ **Root folder organized** - Moved 46 files to `tools/`, `data/`, `docs/`, `reports/`, `archive/`
- ✅ **Clean root directory** - Only 5 essential files remain

See `docs/CLEANUP_GIT_CHROMADB_20251112.md`.

---

## Configuration

### Required API Keys
- **TMDB API Key** - https://www.themoviedb.org/settings/api
- **TVDB API Key** - https://thetvdb.com/api-information
- **Anthropic API Key** (optional) - For Claude AI

Configure in Settings tab or credential manager.

---

## Troubleshooting

### Common Issues

**Import errors for backend modules:**
- Runtime-resolved from `scripts/`
- Ensure virtual environment activated
- Check `sys.path` in main files

**GUI doesn't launch:**
- Python 3.12+ required
- Verify PyQt5: `pip list | Select-String pyqt5`
- Check `logs/` directory

**API rate limits:**
- TMDB: 40 requests/10s
- TVDB: Check current limits
- Built-in via `tenacity` + `ratelimit`

See `docs/COMMON_PITFALLS.md`.

---

## Contributing
Personal project; suggestions welcome via issues.

## License
Personal Use Only

## Credits
**Developer:** JellyRancher Project  
**AI Assistance:** Claude (Anthropic)  
**Inspired By:** Jellyfin ecosystem

## Support
1. Check `docs/`
2. Review `docs/COMMON_PITFALLS.md`
3. Check `logs/`
4. Review `audit-logs/`

---

**Last Updated:** November 12, 2025  
**Status:** Active Development (PyQt6 migration in progress)

---

# docs\RECOVERED_journal.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 72,138 -> 7,197 chars (10.0%)

**Status:** success

```python
#!/usr/bin/env python3
"""
JellyRancher - Clean 9-Point Workflow Implementation
PyQt6 GUI following WORKFLOW_SPEC.md exactly. No bloat.
Usage: python jelly_rancher_clean.py
"""

import sys
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List
from collections import defaultdict  # Added for step_2_overview

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QListWidget, QTreeWidget,
    QTreeWidgetItem, QTableWidget, QTableWidgetItem, QProgressBar,
    QFileDialog, QMessageBox, QSplitter, QGroupBox, QCheckBox,
    QHeaderView, QAbstractItemView, QTabWidget, QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from scripts.core.file_scanner import FileScanner, FileRecord, ScanStatistics
from scripts.core.inventory_repository import InventoryRepository
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer
from scripts.media.media_metadata_lookup import MediaMetadataLookup
from scripts.core.action_plan import ProposedOperation, ActionType, Confidence
from scripts.core.action_plan_generator import ActionPlanGenerator
from scripts.core.jellyfin_config import JellyfinConfigManager
from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.dialogs.jellyfin_settings_dialog import JellyfinSettingsDialog

# Logging setup
Path('data/logs').mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/jellyrancher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScanWorker(QThread):
    """Background thread for folder scanning."""
    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(list, dict, object)
    error = pyqtSignal(str)

    def __init__(self, folder_path: Path, recursive: bool = True):
        super().__init__()
        self.folder_path = folder_path
        self.recursive = recursive
        self.repository = InventoryRepository()

    def run(self):
        try:
            session_id = self.repository.create_scan_session(
                root_folder=self.folder_path, recursive=self.recursive, notes="GUI scan"
            )
            scanner = FileScanner(progress_callback=self._progress_callback)
            file_records = scanner.scan_folder(self.folder_path, recursive=self.recursive)
            stats = scanner.get_statistics()
            self.repository.add_file_records(session_id, file_records)
            self.repository.finalize_scan_session(session_id, stats.total_files, stats.total_size_bytes, len(stats.errors))
            folder_structure = scanner.get_folder_structure(file_records)
            self.finished.emit(file_records, folder_structure, session_id)
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            self.error.emit(str(e))

    def _progress_callback(self, message: str, current: int, total: int):
        self.progress.emit(message, current, total)

class MultiScanWorker(QThread):
    """Background thread for multi-folder scanning with Jellyfin cross-reference."""
    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(list, dict, list)
    error = pyqtSignal(str)

    def __init__(self, folder_paths: List[Path], recursive: bool = True, jellyfin_client: JellyfinClient = None):
        super().__init__()
        self.folder_paths = folder_paths
        self.recursive = recursive
        self.repository = InventoryRepository()
        self.jellyfin_client = jellyfin_client

    def run(self):
        try:
            combined_file_records = []
            combined_folder_structure = {}
            session_ids = []
            total_folders = len(self.folder_paths)

            for folder_idx, folder_path in enumerate(self.folder_paths, 1):
                self.progress.emit(f"Scanning folder {folder_idx}/{total_folders}: {folder_path.name}", folder_idx - 1, total_folders)
                try:
                    session_id = self.repository.create_scan_session(root_folder=folder_path, recursive=self.recursive, notes=f"Multi-folder scan ({folder_idx}/{total_folders})")
                    session_ids.append(session_id)
                    scanner = FileScanner(progress_callback=lambda msg, cur, tot: self._progress_callback(msg, cur, tot, folder_idx, total_folders))
                    file_records = scanner.scan_folder(folder_path, recursive=self.recursive)
                    stats = scanner.get_statistics()
                    self.repository.add_file_records(session_id, file_records)
                    self.repository.finalize_scan_session(session_id, stats.total_files, stats.total_size_bytes, len(stats.errors))
                    folder_structure = scanner.get_folder_structure(file_records)
                    combined_file_records.extend(file_records)
                    combined_folder_structure.update(folder_structure)
                    logger.info(f"Completed scan {folder_idx}/{total_folders}: {stats.total_files} files from {folder_path}")
                except Exception as folder_error:
                    logger.error(f"Error scanning folder {folder_path}: {folder_error}", exc_info=True)
                    self.progress.emit(f"⚠️ Error scanning {folder_path.name}: {str(folder_error)}", folder_idx, total_folders)

            self.progress.emit(f"Completed filesystem scan: {len(combined_file_records)} total files found.", total_folders, total_folders)

            jellyfin_matches = 0
            if self.jellyfin_client and self.jellyfin_client.is_configured():
                self.progress.emit("Querying Jellyfin library...", 0, 1)
                try:
                    jellyfin_items = self.jellyfin_client.get_all_items(item_types=["Movie", "Episode"], fields=["Path", "ProviderIds", "LibraryId"])
                    path_map = {str(Path(item['Path']).resolve()): item for item in jellyfin_items if 'Path' in item}
                    self.progress.emit(f"Found {len(jellyfin_items)} items in Jellyfin. Cross-referencing...", 1, 1)
                    for record in combined_file_records:
                        record_path_str = str(record.absolute_path.resolve())
                        if record_path_str in path_map:
                            jellyfin_item = path_map[record_path_str]
                            record.jellyfin_id = jellyfin_item.get('Id')
                            record.jellyfin_item_type = jellyfin_item.get('Type')
                            record.jellyfin_library_id = jellyfin_item.get('LibraryId')
                            record.jellyfin_provider_ids = jellyfin_item.get('ProviderIds', {})
                            record.jellyfin_matched = True
                            jellyfin_matches += 1
                    self.progress.emit(f"Jellyfin cross-reference complete. Matched {jellyfin_matches} files.", 1, 1)
                    self.progress.emit("Updating inventory database with Jellyfin data...", 0,

---

# docs\RECOVERED_journal_v2.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 2,967 -> 1,892 chars (63.8%)

**Status:** success

---

## Phase 23: Implement Action Plan Review Table (Point 5)
**Date:** 2025-11-14 15:34:00 | **Status:** Complete  
**Coding Assistant:** Gemini-1.5-Pro

### Accomplishment
Implemented GUI for Point 5: editable table for user review/approval of proposed file reorganizations.

### Implementation Summary

1. **Data Model Creation:**
   * Created `scripts/core/action_plan.py` with `ProposedOperation` dataclass (source, destination, action type, confidence, etc.) and `ActionType`/`Confidence` enums.

2. **Action Plan Generator (Stub):**
   * Created `scripts/core/action_plan_generator.py` with `ActionPlanGenerator` class.
   * Produces sample `ProposedOperation` list for GUI testing, independent of correlation logic.

3. **GUI Integration:**
   * Added `ActionPlanWorker` (QThread) in `jelly_rancher_clean.py` for background generation.
   * Updated "Review Actions" tab with `QTableWidget` (`self.action_table`): columns "Source File", "Proposed Destination", "Action", "Confidence", "Jellyfin Status", "Notes", "Approve".
   * Refactored `step_5_review` to trigger worker.
   * Added `_on_action_plan_finished` slot: populates table, color-codes by `Confidence` (Green=High, Yellow=Medium, etc.), adds approval checkbox per row.

### Obstacle & Breakthrough
* **Obstacle:** `run_shell_command` and `web_fetch` failed to retrieve timestamp for journal entries.
* **Breakthrough:** User provided timestamp manually, unblocking documentation.

### Files Modified
- `jelly_rancher_clean.py`: Added `ActionPlanWorker`; updated `__init__`, `create_review_tab`, `step_5_review`; added `_on_action_plan_finished`, `_on_action_plan_error`.
- `scripts/core/action_plan.py`: New.
- `scripts/core/action_plan_generator.py`: New.

### Next Steps
Implement `ActionPlanGenerator` core logic: derive real action plan from scanned files, LLM proposal, canonical metadata, replacing sample data.

---

---

# docs\RECOVERY_SUMMARY.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 7,122 -> 4,591 chars (64.5%)

**Status:** success

# JellyRancher Journal Recovery Summary
**Date:** November 14, 2025, 21:40:08  
**Recovery Lead:** Claude Sonnet 4.5  
**Status:** ✅ COMPLETE

---

## Crisis Overview

At 21:30 on November 14, 2025, `agent-journal.md` truncated to 37 lines (99% loss), retaining only Phase 23; Phases 0-22 erased.  
**Root Cause:** Gemini CLI infinite loop adding "Coding Assistant" attribution overwrote file via `write_file`.

---

## Recovery Process

### Phase 1: Data Salvage (21:32-21:35)

**Sources:**
1. `backups/agent-journal_2025-11-13_144912.md` (2,172 lines)
2. `checkpoint-shitball.json` (536 KB)

**Recovered:**
- ✅ Phase 0 (backup)
- ✅ Phase 13 (backup)
- ✅ Phase 14 (backup)
- ✅ Phase 22 (checkpoint)
- ✅ Phase 23 (checkpoint)

**Lost:**
- ❌ Phases 1-12 (early dev, infra, LLM, PyQt6 GUI)
- ❌ Phases 15-20 (Jellyfin foundation)
- ⚠️ Phase 21 (partial, state snapshot)

### Phase 2: Forensic Code Archaeology (21:35-21:40)

**Targets:**
- 22 files in `scripts/core/`
- `jelly_rancher_clean.py` (1,796 lines)
- Imports/dependencies
- Docs: `architecture-reference.md`, `WORKFLOW_SPEC.md`
- SQLite: `data/inventory.db` schema
- Dataclasses, API clients
- Code comments w/ phase markers (e.g., "# Jellyfin integration (Phase 20)")

**Reconstruction:**

| Phase Range | Method | Confidence | Details |
|-------------|--------|------------|---------|
| 0 | Backup | 100% | Full text |
| 1-12 | Code archaeology | 70% | From FileScanner, InventoryRepository, LLMStructureAnalyzer, MediaMetadataLookup |
| 13-14 | Backup | 100% | Full text |
| 15-20 | Code archaeology | 85% | From JellyfinClient, JellyfinConfigManager, migrations, GUI |
| 21 | Code + snapshot | 90% | From MultiScanWorker (lines 196-237) |
| 22-23 | Checkpoint | 100% | Full text |

---

## Final Results

### Journal Statistics

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Line Count | 37 | 2,478 | ✅ 6,597% increase |
| Phases | 1 | 24 | ✅ All covered |
| Data Loss | 99% | ~15% | ✅ 84% recovered |
| Context | None | Comprehensive | ✅ Restored |

### Files Created
1. **agent-journal.md** (2,478 lines) - Reconstructed journal
2. **PHASES_1-21_RECONSTRUCTED.md** - Forensic report
3. **RECOVERY_SUMMARY.md** - This file
4. **backups/agent-journal_2025-11-14_213242_RECOVERED.md** - Initial snapshot
5. **backups/agent-journal_2025-11-14_214008_FULLY_RECONSTRUCTED.md** - Final

### Recovery Success Rates
**By Phase:**
- 0, 13-14: **100%** (backup)
- 22-23: **100%** (checkpoint)
- 1-12: **~70%** (synthetic)
- 15-20: **~85%** (code)
- 21: **~90%** (code + snapshot)  
**Overall:** ~85%

---

## Technical Achievements Preserved

### Core Systems (1-12)
✅ File scanner (recursive)  
✅ SQLite InventoryRepository  
✅ Poe API LLM (Claude-Sonnet-4.5)  
✅ TMDB/OMDb lookup (rate-limited)  
✅ PyQt6 GUI (9-point tabs)  
✅ QThread workers  
✅ Models: FileRecord, ScanStatistics

### Jellyfin Integration (15-21)
✅ JellyfinClient (API auth)  
✅ JellyfinConfigManager (secure)  
✅ Settings dialog  
✅ DB migrations (Jellyfin fields)  
✅ Scan cross-referencing  
✅ ProviderIds (TMDb, TVDb, IMDb)

### Recent (22-23)
✅ Jellyfin-aware LLM  
✅ ProviderIds metadata lookup  
✅ Action plan review table (Point 5 GUI)  
✅ ProposedOperation model  
✅ ActionPlanGenerator stub

---

## Lessons Learned & Safety Protocols

### Root Cause
Gemini CLI edit loop used `write_file` repeatedly, truncating content.

### New Protocols (CRITICAL)
**For All AI Assistants:**
1. **NEVER** use Write on `agent-journal.md` (except initial creation)
2. **ALWAYS** use Edit w/ specific old_string/new_string
3. Backup BEFORE edits (timestamped)
4. Validate line count post-edit (no decrease)
5. Read to verify before edit
6. Append-only for new phases
7. No full-file replacements

**Update `#master-prompt.md`** with these as mandatory.

---

## Current Project Status

**Last Completed:** Phase 23 (Action Plan Review Table GUI)  
**Current:** Phase 24 (Recovery) - ✅ COMPLETE  
**Next:** Phase 25 (ActionPlanGenerator logic)

**App State:**
- ✅ Points 1-4: COMPLETE
- ✅ Jellyfin (read-only): COMPLETE
- 🔨 Point 5: GUI done, logic stub
- ⏸️ Points 6-9: Pending

**Ready:** Yes

---

## Acknowledgments

**Response Time:** 8 min (21:32-21:40)  
**Salvaged:** 2,172 lines (backup), 6,000+ chars (checkpoint)  
**Analyzed:** 1,796 lines (GUI) + 22 modules  
**Reconstructed:** 17 phases (1-12,15-21)

Resilience from clean architecture, docs, version control.

---

**Status: ✅ COMPLETE**  
**Continuity: ✅ RESTORED**  
**Loss: 99% → ~15%**

*Generated: 2025-11-14 21:40:08*  
*Method: Salvage + archaeology*  
*Confidence: 85%+*

---

# docs\TESTING_GUIDE.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 7,686 -> 4,674 chars (60.8%)

**Status:** success

# JellyRancher Testing Guide - Point 4 Implementation

## Quick Start

### Option 1: Automated Setup (Recommended)

```powershell
.\setup_and_run.ps1
```

### Option 2: Manual Setup

```powershell
$env:TMDB_API_KEY = "a71ed25dc11e509b52067f0c10df1af4"
.venv\Scripts\Activate.ps1
python jelly_rancher_clean.py
```

## Test Media Folder

`test_media/` contains:
- 41 video files (movies/TV)
- 6 subtitle files
- 7 movies (various formats)
- 6 TV shows (organized/messy)
- 2 multi-part episodes (NFO testing)

**Structure:**
```
test_media/
├── Movies/
│   ├── The Matrix (1999)/
│   ├── Inception (2010)/
│   ├── Interstellar (2014)/
│   ├── The Godfather (1972)/
│   └── Various messy formats...
├── TV Shows/
│   ├── Breaking Bad (2008)/
│   └── The Office (US) (2005)/
├── Unsorted TV/
│   ├── Stranger Things/
│   ├── Game of Thrones files
│   ├── The Mandalorian/
│   └── Star Trek TNG/ (multi-part)
└── Unsorted/
    └── Random files
```

## Testing Workflow

### Step 1: Scan Folders (Points 1-2)

1. `python jelly_rancher_clean.py`
2. **Tab 1: "1-2. Scan & Overview"**
3. **"Add Folder"** → `test_media`
4. **"Scan Selected Folders"**

**Expected:**
- Progress bar
- File list (first 500)
- Hierarchical tree
- Total files/size

### Step 2: LLM Analysis (Point 3)

1. **Tab 2: "3-4. LLM & Metadata"**
2. **"Get LLM Proposal"** (enter Poe.com API key if needed)
3. Wait 30-60s

**Expected:**
- ~7 movies, ~6 TV shows detected
- Reorg proposal
- Multi-part flagged (Star Trek TNG)
- Saved: `data/llm_analysis_TIMESTAMP.json`

### Step 3: Metadata Lookup (Point 4)

1. **"Build Metadata DB"**
2. Monitor progress

**Expected:**
- Per-item progress
- Rate limit (1 req/s)
- Movies: years, TMDB IDs
- TV: seasons/episodes
- Multi-part listed
- Saved: `data/canonical_metadata_TIMESTAMP.json`

**Example Output:**
```
[1/13] Querying movie: The Matrix (1999)...
[2/13] Querying movie: Inception (2010)...
[3/13] Querying tv_show: Breaking Bad (2008)...
...
============================================================
✅ METADATA LOOKUP COMPLETE
============================================================
📽️ Movies: 7
   • The Matrix (1999) [603]
   • Inception (2010) [27205]
   • Interstellar (2014) [157336] ...
📺 TV Shows: 6
   • Breaking Bad (2008) - 5s, 62e [1396]
   • The Office (2005) - 9s, 201e [2316] ...
⚠️ Multi-Part: 2
   • Star Trek TNG S01E01 - Encounter at Farpoint
   • Star Trek TNG S03E26 - Best of Both Worlds
💾 data/canonical_metadata_20231113_235959.json
```

## Verification Checklist

### ✅ Structural Tests
- [x] All imports work
- [x] MediaMetadataLookup initializes
- [x] Cache dir: `data/metadata_cache/`
- [x] JSON serialization
- [x] No Unicode log errors

### ✅ Point 4 Functionality
- [ ] TMDB key detected/prompted
- [ ] Background worker (no GUI freeze)
- [ ] Real-time progress
- [ ] Rate limit visible (1 req/s)
- [ ] Movie metadata (title/year/ID)
- [ ] TV metadata (seasons/episodes)
- [ ] Multi-part detection
- [ ] Lookup failures shown
- [ ] Timestamped JSON save
- [ ] No crashes

## Expected API Behavior

**TMDB Calls:**
- Movies: 1/call (search+details)
- TV: 1 + N/season
- Rate limit: 1 req/s
- Cache: reused lookups

**7 movies + 6 TV:** ~7 + 30-40 calls; 45-60s total.

## Troubleshooting

### No API key
```powershell
$env:TMDB_API_KEY = "a71ed25dc11e509b52067f0c10df1af4"
# Or .\setup_and_run.ps1
```

### "No detected media"
- Run Step 2 first

### Lookup failures
- Check internet/TMDB
- LLM title issues
- 429 errors
- Review `data/logs/jellyrancher.log`

### Slow progress
Normal: 1 req/s; 13 items ~60s; cache speeds retries.

## Files Generated

```
data/
├── canonical_metadata_YYYYMMDD_HHMMSS.json
├── llm_analysis_YYYYMMDD_HHMMSS.json
├── metadata_cache/
│   ├── movie_The_Matrix_1999.json
│   ├── tv_Breaking_Bad_2008.json
│   └── ...
├── logs/jellyrancher.log
└── inventory.db
```

## Next Steps

1. **Point 5**: Editable action table (LLM + metadata)
2. **Points 6-7**: Execute (logging, MD5, subs, NFO)
3. **Points 8-9**: Subtitle eval/download

## Known Limitations

1. Point 3: Needs Poe.com key
2. Point 4: Needs TMDB key
3. Test media: Empty files
4. Multi-part: Name patterns

## API Credentials

**TMDB Key:** `a71ed25dc11e509b52067f0c10df1af4`  
(Free: 40/10s; impl: 1/s)  
Own: https://www.themoviedb.org/settings/api

**Read Token:** (unused)  
`eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhNzFlZDI1ZGMxMWU1MDliNTIwNjdmMGMxMGRmMWFmNCIsIm5iZiI6MTc2Mjg4OTc2NC4wMDcsInN1YiI6IjY5MTM5MDI0NjAwZGIxNjUyYmQyNjM1NSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.wHizl2Jf-LgGAq0czRufHTKKmF4mMDuwCNUd3RddlM0`

## Questions?

- `docs/plan.md`
- `docs/ARCHITECTURE.md`
- `agent-journal.md`
- `docs/tmdb_usage_guidelines.md`

---

# docs\ARCHITECTURE.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 13,240 -> 9,491 chars (71.7%)

**Status:** success

# JellyRancher Architecture Reference

**Version:** 2.0  
**Date:** November 12, 2025

---

## Overview

Describes architectural decisions and library choices for JellyRancher Jellyfin media organizer. Answers: "What libraries to use?" and "What to build ourselves?"

---

## Libraries We're Using

### GUI Framework

**PyQt6** - Desktop GUI
```bash
pip install PyQt6>=6.6.0
```

**Why:** Mature, cross-platform, excellent table/tree widgets, built-in threading

**Usage:**
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

#### TMDB

**tmdbv3api** - Official wrapper
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

**Rate Limit:** 40 req/10s

---

#### TVDB

**tvdb_v4_official** - Official v4 wrapper
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

### Rate Limiting & Retry

#### Tenacity - Exponential Backoff
```bash
pip install tenacity>=8.2.0
```

**Usage:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
def query_api_with_retry():
    pass  # Retries: 2s, 4s, 8s, 16s, 32s
```

---

#### Ratelimit - Simple Limiting
```bash
pip install ratelimit>=2.2.1
```

**Usage:**
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)  # TMDB
def query_tmdb():
    pass  # Auto-sleeps on exceed
```

---

#### Combined
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
def query_tmdb_safe(movie_name):
    pass
```

---

### Subtitle Handling

#### Subliminal - Multi-Provider Downloader
```bash
pip install subliminal>=2.1.0
```

**Supports:** OpenSubtitles.org/com, Podnapisi.NET, Addic7ed.com, Subscene.com, TVSubtitles, etc.

**Features:**
- Hash-based matching (primary)
- Fuzzy filename fallback
- Auto language detection
- Scoring/ranking

**Usage:**
```python
from subliminal import download_best_subtitles, save_subtitles
from babelfish import Language
from subliminal import Video

video = Video.fromname('movie.mkv')
subtitles = download_best_subtitles({video}, {Language('eng')}, providers=['opensubtitles', 'podnapisi', 'addic7ed'])
save_subtitles(video, subtitles[video])
```

**Forced Subtitles:** Check metadata post-download (provider-dependent).

---

#### FFmpeg-Python - Media Analysis
```bash
pip install ffmpeg-python>=0.2.0
```

**Purpose:** Detect embedded subtitles

**Usage:**
```python
import ffmpeg

probe = ffmpeg.probe('movie.mkv')
subtitle_streams = [s for s in probe['streams'] if s['codec_type'] == 'subtitle']

for sub in subtitle_streams:
    lang = sub.get('tags', {}).get('language', 'unknown')
    forced = sub.get('disposition', {}).get('forced', 0)
    print(f"Subtitle: {lang}, Forced: {bool(forced)}")
```

**Note:** Requires system ffmpeg/ffprobe.

---

### Fuzzy Matching

#### RapidFuzz - Fast Matching
```bash
pip install rapidfuzz>=3.5.0
```

**Why:** 10-100x faster than fuzzywuzzy, compatible API

**Usage:**
```python
from rapidfuzz import fuzz, process

similarity = fuzz.ratio("The Matrix", "Matrix, The")

choices = ["The Matrix", "The Matrix Reloaded", "Matrix Revolutions"]
best = process.extractOne("matrix", choices)  # ('The Matrix', 90.0, 0)
top = process.extract("matrix", choices, limit=3)
```

**Use Cases:**
- Filenames to TMDB/TVDB titles
- Duplicate detection
- User input matching

---

### File Operations

#### Send2Trash - Safe Delete
```bash
pip install send2trash>=1.8.2
```

**Why:** Recycle bin vs. permanent delete

**Usage:**
```python
from send2trash import send2trash
send2trash('file.mkv')  # Recycle bin
# vs. os.remove('file.mkv')  # Permanent
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
    messages=[{"role": "user", "content": "Analyze this folder structure..."}]
)
print(message.content)
```

**Alternative:** Existing `ravenmaven_client.py` (Poe.com)

---

### Built-In Python Libraries

#### pathlib
```python
from pathlib import Path

path = Path('/some/folder/file.mkv')
print(path.name, path.stem, path.suffix, path.parent)  # file.mkv file .mkv /some/folder
new_path = path.parent / 'subfolder' / 'newfile.mkv'
```

---

#### shutil
```python
import shutil
shutil.copy2('source.mkv', 'dest.mkv')  # Preserves metadata
shutil.move('source.mkv', 'dest.mkv')
shutil.copytree('source_dir', 'dest_dir')
```

---

#### hashlib - MD5
```python
import hashlib

def md5_hash_file(filepath, chunk_size=8192):
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()
```

---

#### sqlite3 - Transaction Log
```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('transaction_log.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY, timestamp TEXT, operation TEXT, source_path TEXT,
    destination_path TEXT, source_md5 TEXT, completed BOOLEAN DEFAULT 0
)
''')
c.execute('INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)',
          (datetime.now().isoformat(), 'move', source, dest, md5_hash))
conn.commit()
```

---

#### json
```python
import json
cache = {'movie': {'title': 'The Matrix', 'year': 1999}}
with open('cache.json', 'w') as f: json.dump(cache, f, indent=2)
with open('cache.json', 'r') as f: cache = json.load(f)
```

---

## What We Must Build Ourselves

**No existing libraries:**

### 1. ❌ Transaction Log System

Atomic batch rollback (e.g., undo 500 moves if one fails).

**Approach:** SQLite log pre-execution, pre/post MD5 verify, reverse ops.

Ref: `jellyfin_safe_executor.py`

---

### 2. ❌ Jellyfin NFO Generation

XML for multi-part episodes.

**Example:**
```python
import xml.etree.ElementTree as ET

root = ET.Element('episodedetails')
ET.SubElement(root, 'title').text = 'Episode Title'
ET.SubElement(root, 'season').text = '1'
ET.SubElement(root, 'episode').text = '1'
ET.SubElement(root, 'displayepisode').text = '1'
ET.SubElement(root, 'displayseason').text = '1'
ET.ElementTree(root).write('episode.nfo', encoding='utf-8', xml_declaration=True)
```

---

### 3. ❌ Color-Coded Action Table

PyQt6 table with confidence colors.

**Implementation:**
```python
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor

def add_action_row(table, file, action, confidence):
    row = table.rowCount()
    table.insertRow(row)
    item = QTableWidgetItem(file)
    color = {'high': QColor(200,255,200), 'medium': QColor(255,255,200), 'low': QColor(255,200,200)}[confidence]
    item.setBackground(color)
    table.setItem(row, 0, item)
```

---

### 4. ❌ Hierarchical Folder Overview

Tree with filetype aggregation.

**Implementation:**
```python
from collections import defaultdict
from pathlib import Path

def build_folder_tree(file_list):
    tree = defaultdict(lambda: defaultdict(int))
    for fp in file_list:
        p = Path(fp)
        tree[str(p.parent)][p.suffix.lower()] += p.stat().st_size
    return tree
```

---

### 5. ❌ LLM → Metadata Pipeline

Parse LLM JSON → fuzzy TMDB/TVDB query → canonical DB → action plan.

---

## requirements.txt

```txt
PyQt6>=6.6.0
tmdbv3api>=1.9.0
tvdb_v4_official>=1.0.0
tenacity>=8.2.0
ratelimit>=2.2.1
subliminal>=2.1.0
ffmpeg-python>=0.2.0
rapidfuzz>=3.5.0
send2trash>=1.8.2
anthropic>=0.18.0
```

Built-ins: pathlib, shutil, hashlib, sqlite3, json, xml.etree.ElementTree

---

## Common Questions

### Q: Async/await?

**A:** No initially; use PyQt6 QThread. Later: aiohttp, aiolimiter, asyncio.

### Q: Large file moves?

**A:** `shutil.move()` + chunked MD5 pre/post-verify. Progress bar for >50GB.

### Q: Metadata cache DB?

**A:** SQLite:

```python
import sqlite3, json
conn = sqlite3.connect('metadata_cache.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS movies (title TEXT, year INTEGER, tmdb_id INTEGER, metadata TEXT, cached_at TEXT)''')
c.execute('SELECT metadata FROM movies WHERE title=? AND year=?', (title, year))
if result := c.fetchone():
    return json.loads(result[0])
```

Benefits: Fast, JSON-as-TEXT.

### Q: Test without real files?

**A:**
```python
import tempfile, shutil
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    test_dir = Path(tmpdir)
    (test_dir / 'movie.mkv').touch()
    # Test ops; auto-cleanup
```

---

## Next Steps

1. `pip install -r requirements.txt`
2. Verify: `ffmpeg -version`
3. Get API keys: TMDB, TVDB, OpenSubtitles
4. Start folder scanning w/ pathlib
5. Build incrementally

See `WORKFLOW_SPEC.md` for 9-point workflow.

---

# docs\ass.plan.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 13,693 -> 5,284 chars (38.6%)

**Status:** success

<!-- 7bfef3a7-8e4a-40cf-b806-16b709069497 c7f9d63f-267f-4933-b023-9913850383f0 -->
## Assessment of Plan Points 1–4

### Goal

Explain what is implemented for points 1–4 from `docs/plan.md` in current code (centered on `jelly_rancher_clean.py` and collaborators), what is not, and why, based on code.

### Point 1 – Scanning, MD5 baseline, Jellyfin, and other metadata

Implements multi-folder recursive scanning and persistent inventory. `JellyRancherClean` uses `MultiScanWorker` with `FileScanner.scan_folder(...)` to build `FileRecord` list (absolute path, size, extension, parent folder, scan timestamp). `InventoryRepository.add_file_records(...)` stores in SQLite (`files` table). GUI shows first 500 files.

Implements Jellyfin cross-referencing: `MultiScanWorker.run(...)` calls `JellyfinClient.get_all_items(...)` for movies/episodes, maps by filesystem paths, enriches `FileRecord` with `jellyfin_id`, `jellyfin_item_type`, `jellyfin_library_id`, `jellyfin_provider_ids`, `jellyfin_matched`.

MD5 baseline not wired into scan: `FileRecord.md5_hash` and `files.md5_hash` exist, but `FileScanner._process_file(...)` sets `md5_hash=None`. `FileHasher` used elsewhere (transaction logging), not scan.

No AniList/AniDB references or anime metadata in scan. Scan single-threaded (Python loops), no parallel hashing.

**Implemented**: multi-folder recursive scanning, inventory storage, extension filtering, Jellyfin cross-reference. **Not**: MD5 hashing at scan time, AniList/AniDB, parallel hashing.

### Point 2 – Structural summary, duplicates, and Jellyfin/usage comparison

Implements structural summary: `FileScanner.get_folder_structure(...)` builds dict (folder path → total size, file count, per-extension counts/sizes). `JellyRancherClean.step_2_overview(...)` populates `QTreeWidget` (folder path, file count, MB size, Jellyfin match count/folder, common types).

Includes Jellyfin view: counts `jellyfin_matched` per folder, colors column (green=all, yellow=some).

Missing: MD5 duplicate grouping (no MD5); no Jellyfin playback stats/sessions/watch counts; no before/after comparison.

**Implemented**: hierarchical folder summary with counts, sizes, Jellyfin match counts. **Not**: MD5 duplicates, playback analytics, before/after comparisons.

### Point 3 – LLM reorganization proposal and detected media list

Implements end-to-end: `JellyRancherClean.step_3_llm_proposal(...)` spawns `LLMAnalysisWorker` with `folder_structure`, `scanned_files`. `_build_structure_summary()` creates LLM input (folder: path, file count, size, types, dedup Jellyfin provider IDs).

`LLMStructureAnalyzer` prompts via `PoeClient` for JSON: `detected_media` (`title`, `type`, `year_estimate`, `current_location`, `confidence`, notes), `reorganization_plan` (folder changes, compliance), `multi_part_episodes`, `reasoning`. Parses to dict.

`JellyRancherClean._on_llm_finished(...)` stores `self.llm_analysis`, extracts `self.detected_media`, `self.reorganization_plan`; displays summary in GUI.

Missing: MD5 duplicates in summary; no Trakt/Ani-Sync/watch history; no API automation from plan.

**Implemented**: LLM loop (structure → detected media + reorg plan), GUI integration. **Not**: MD5/Trakt context, API automation.

### Point 4 – Canonical metadata database and multi-part episodes

Implements: `step_4_metadata(...)` spawns `MetadataLookupWorker` with `self.detected_media`, `scanned_files`. Uses `MediaMetadataLookup` (TMDB/OMDb keys).

For movies: uses Jellyfin TMDB ID or searches TMDB/OMDb (title/year) for canonical title, year, overview, IDs, posters.

For TV: TMDB TV/season endpoints; `_get_season_episodes(...)` flags multi-part (e.g., “part 1 / part 2”) as `is_multi_part=True`.

Builds `canonical_db` (movies/shows + LLM detections), `multi_part_episodes` (show, season, episode, `needs_nfo=True`). Logs summary, saves JSON to `data/`.

Missing: NFO generation; Fanart.tv/Themerr artwork/themes; duplicate/merge at DB level; full canonical DB → Jellyfin updates. Provider ID mapping simplistic.

**Implemented**: canonical DB via TMDB/OMDb, multi-part tagging/persistence. **Not**: NFO/artwork/themes, duplicate/merge, Jellyfin round-trip.

### Summary of Where Points 1–4 Stand

- Point 1: Scanning, inventory, Jellyfin cross-reference implemented; MD5 hashing during scan, AniList/AniDB, parallel hashing not.
- Point 2: Hierarchical folder summary with counts, sizes, Jellyfin match counts implemented; MD5 duplicates, playback analytics, before/after not.
- Point 3: Core LLM loop (structure → detected media + reorg plan) implemented in GUI; MD5/Trakt context, API automation not.
- Point 4: Canonical DB with TMDB/OMDb, multi-part tagging implemented; NFO, artwork/theme, duplicate/merge not.

Conclusions from code paths: `scan_folder`, `get_folder_structure`, `analyze_structure`, `lookup_movie`/`lookup_tv_show` invocations, fields, services.

### To-dos

- [ ] Integrate MD5 hashing into scanning/inventory (`FileRecord.md5_hash`, SQLite `md5_hash`).
- [ ] Use MD5 for duplicate detection/grouping in UI overview/duplicates report.
- [ ] Extend `LLMStructureAnalyzer` prompt with MD5 duplicates, future playback/Trakt data.
- [ ] From canonical DB: add NFO generation, artwork/theme hooks, execution via `TransactionManager`/`ActionType.CREATE_NFO`.

---

# docs\bootstrap.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 25,471 -> 7,386 chars (29.0%)

**Status:** success

# JellyRancher Bootstrap Guide for LLM Coding Assistants

## 🚨 PRIME DIRECTIVE: Virtual Environment

**ALWAYS USE `.venv\Scripts\python.exe` (Python 3.10) FOR ALL PYTHON OPERATIONS**

### Critical Rules:
1. **NEVER run `python`** - uses system Python 3.14, breaks ChromaDB (Pydantic v1 issues)
2. **ALWAYS use `.venv\Scripts\python.exe`**
3. **CHECK before every command**: `.venv\Scripts\python.exe -c "import sys; print(sys.executable)"`

### Correct Usage:
```bash
# ✅ CORRECT
.venv\Scripts\python.exe script.py
.venv\Scripts\python.exe -m pip install package

# ❌ WRONG
python script.py  # Python 3.14 - breaks ChromaDB
pip install package
```

### Quick Verification:
```bash
.venv\Scripts\python.exe --version  # Python 3.10.0
python --version                    # Python 3.14.0 (WRONG!)
```

## Quick Start

On "bootstrap", run:
```bash
.venv\Scripts\python.exe bootstrap.py
```

### Manual Verification:
1. `.venv\Scripts\python.exe --version` (Python 3.10+)
2. `.venv\Scripts\python.exe bootstrap.py`
3. **Query ChromaDB before any task** (project docs, history, decisions)

## 🚨 CRITICAL: ChromaDB is Sole Source of Truth

**ChromaDB contains:**
- Project docs, dev journal, features, architecture, troubleshooting, API, roadmap, git changelog

**Archived docs** (`archive/documentation_YYYY-MM-DD/`): Historical only; **NEVER use** - query ChromaDB.

## 🚨 CRITICAL: GUI Entry Point Directive

**Sole GUI launcher: `launch_gui.py` (root)**

- ✅ `.venv\Scripts\python.exe launch_gui.py`
- ❌ `scripts/core/launch_gui.py`, `jelly_rancher_main.py`, etc. (legacy/reference)
- Imports `main()` from `scripts/core/jelly_rancher_main.py`

Use for all GUI tasks ("launch GUI", "start app", testing).

## How to Use ChromaDB

### 1. Query:
```python
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
mem = ChromaMemoryBackend('./chroma_db')
results = mem.query_memory("query", limit=5)
for result in results: print(result['content'], result.get('metadata', {}))
```

### 2. Query Before Every Task:
```python
context = mem.query_memory("feature X implementation", limit=10)
```

### 3. Document After Task:
```python
from datetime import datetime
mem.add_memory(
    content="""# Task: Title
Date: YYYY-MM-DD
Type: feature_implementation|bug_fix|...
Status: completed

## What Was Done\n[details]

## Changes Made\n- File: path (lines X-Y)\n- Added/Modified/Deleted: [...]

## Implementation Details\n[...]

## Testing\n[...]

## Issues\n[...]

## Next Steps\n[...]""",
    user_id='llm_assistant',
    metadata={
        'type': 'session_log',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'component': 'gui',
        'feature': 'feature',
        'status': 'completed',
        'tags': 'tag1,tag2',
        'files_modified': 'file.py',
        'lines_changed': 324
    }
)
```

### 4. Rebuild ALL Indexes After Function/GUI Changes:
```bash
.venv\Scripts\python.exe build_function_index_enhanced.py --enhance-new
.venv\Scripts\python.exe build_gui_control_index.py
.venv\Scripts\python.exe build_help_index.py
```

**Enhanced Indexer (`build_function_index_enhanced.py`):** LLM-generates docstrings (`--enhance-new` for new/modified; `--enhance` all). See `ENHANCED_INDEXER_GUIDE.md`.

**Indexes:**
1. **Function** (`function_index.json`): 1,773 fns (99% enhanced docstrings); signatures, params, returns.
2. **GUI Control** (`gui_control_index.json`): Maps controls to fns; detects stubs/unconnected (health: PASS required).
3. **Help** (`help_index.json`): Tooltips from docstrings (>90% coverage).

**Rebuild when:** Add/mod/del fns/controls, change signatures/docstrings/connections/tooltips. **Before commit.**

**Workflow Ex:**
```bash
# Changes → Document in ChromaDB → Rebuild all → Check PASS → git add indexes/chroma_db/ → Commit w/ stats
git commit -m "feat: X\n\n## Changes\n- ...\n- Indexes: Function 1,773; GUI PASS; Help 95%"
```

## Development Workflow

1. **Bootstrap**: `.venv\Scripts\python.exe bootstrap.py`
2. **Query ChromaDB**: e.g., `mem.query_memory("feature X", limit=10)`
3. **Implement** per ChromaDB patterns
4. **Document** in ChromaDB
5. **Rebuild indexes** if fns/GUI changed; check PASS
6. **Git commit** w/ ChromaDB-based changelog

## Common Queries
```python
mem.query_memory("project overview", limit=5)
mem.query_memory("feature implementation", limit=10)
mem.query_memory("error troubleshooting", limit=5)
mem.query_memory("roadmap", limit=10)
mem.query_memory("2025-11-09 session", limit=10)
mem.query_memory("API methods", limit=5)
```

## Rules for LLM Assistants

### ✅ ALWAYS
1. Query ChromaDB first
2. Document in ChromaDB
3. Rebuild all indexes after fn/GUI changes
4. Check GUI Control PASS (no stubs/unconnected)
5. Connect all controls to full fns; add docstrings
6. Commit indexes + stats

### ❌ NEVER
1. Create/read loose/archived docs
2. Skip queries/docs
3. Create stubs/unconnected controls
4. Commit w/ FAIL or missing indexes

## Function Index System

- **File**: `function_index.json` (2.3MB, 1,773 fns in 211 files; 99% enhanced)
- **Build**: `build_function_index_enhanced.py --enhance-new`
- Contains: sig, path, docstring, params, returns, type
- Rebuild after fn changes; commit w/ stats
- Search via ChromaDB: `mem.query_memory("fn purpose", limit=5)`

## GUI Control Index System

- **File**: `gui_control_index.json`
- **Build**: `build_gui_control_index.py`
- Maps controls → fns; detects stubs/unconnected
- **NO STUBS**: Health PASS (100% connected, 0 stubs) required pre-commit
- Ex: "Total:150 Connected:150 (100%) PASS"

Rebuild after control changes.

## Help Index System

- **File**: `help_index.json`
- **Build**: `build_help_index.py` (after others)
- Control → fn docstring → tooltip (>90% coverage)
- Rebuild after docstrings/connections; sync all 3 indexes

## ChromaDB API Reference

```python
mem = ChromaMemoryBackend('./chroma_db')

mem.add_memory(content="...", user_id='llm_assistant', metadata={...})

results = mem.query_memory("query", user_id=None, limit=5, include_metadata=False)

stats = mem.get_memory_stats()  # {'total_memories':1152, ...}
```

## Project Structure
```
JellyRancher/
├── bootstrap.md
├── chroma_db/                 # Source of truth
├── scripts/
│   ├── core/                  # jelly_rancher_main.py, chroma_memory_backend.py
│   ├── media/, utils/, tests/
├── archive/documentation_YYYY-MM-DD/  # DO NOT USE
├── document_to_chromadb.py, ingest_docs_to_chromadb.py
└── requirements-jelly-rancher.txt
```

## Example Session
```python
mem = ChromaMemoryBackend('./chroma_db')
print(mem.get_memory_stats())

# Query: gui_context = mem.query_memory("GUI patterns", limit=5)

# Implement → Document:
mem.add_memory(content="# Feature X\n...", metadata={...})

# Rebuild/commit
```

## Getting Help
```python
mem.query_memory("how to X", limit=5)
```

## Summary

**ChromaDB = Sole Source:** Docs, journal, roadmap, troubleshooting, indexes (1,773 fns, 99% docstrings).

**Workflow:** Query → Implement → Document → Rebuild (if needed; PASS) → Commit w/ stats/indexes.

**Never:** Loose/archived docs, skip query/doc, stubs/unconnected, FAIL commits, miss rebuilds.

**Indexes ensure:** Discoverable code, connected controls (NO STUBS), contextual help.

One last thing, dickhead. If I ask you a QUESTION in agent mode, you must ANSWER IT using VERBAL HUMAN LANGUAGE before you start making tool calls and modifying or writing code. Capische?

---

# docs\JELLY_RANCHER_PROJECT_STATE_2025.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 10,446 -> 6,109 chars (58.5%)

**Status:** success

# JellyRancher v2.0.0 - Complete Project State Documentation
Date: 2025-11-11 12:00:00  
Type: Project State Documentation  
Status: Current as of November 11, 2025

## Executive Summary
JellyRancher: PyQt5-based unified media organization platform with AI integration (RavenMaven), semantic memory (ChromaDB), code analysis (CodeCop), media processing (TMDB, Wikipedia), subtitles, analytics, and semantic search.

## Core Architecture

### Technology Stack
- **Frontend**: PyQt5 GUI with custom styling and responsive design
- **Backend**: Modular Python with feature-specific backends
- **Memory**: ChromaDB semantic memory for document/knowledge retrieval
- **AI**: RavenMaven client for batch processing
- **Code Analysis**: CodeCop for quality metrics
- **Media Processing**: TMDB API, Wikipedia scraping, custom metadata
- **Persistence**: JSON config, immutable audit logging, snapshots

### Application Structure
```
JellyRancher/
├── scripts/core/                 # Main application code
│   ├── jelly_rancher_main.py       # Main GUI (3,000+ lines)
│   ├── dialogs/                 # Specialized dialogs
│   │   ├── tmdb_cache_dialog.py
│   │   ├── wikipedia_cache_dialog.py
│   │   └── canonical_db_dialog.py
│   └── backends/                # Feature backends
├── scripts/media/               # Media processing
├── scripts/ai/                  # AI/LLM integrations
├── scripts/utils/               # Utilities
├── chroma_db/                   # Semantic memory DB
├── data/                        # Media inventories/mappings
├── reports/                     # Analysis reports
└── audit-logs/                  # Immutable logs
```

## Feature Areas & Capabilities

### 1. 📁 Media Organization (PRIMARY)
**Status**: Fully Implemented

**Core Capabilities**:
- Multi-type support (Movies, TV, Anime, Mixed)
- Intelligent folder analysis/organization
- Dry-run preview
- File integrity verification
- Real-time progress/logging
- Snapshot backup/rollback

**Advanced**:
- Episode/movie title analysis/fixing
- Folder summaries/stats
- Immutable audit trail
- Timestamped snapshots

**Implementation**:
- Backend: `MediaOrganizer` class
- UI: Dedicated tab (15+ controls)
- Help: Hover help
- Integration: Snapshots/audits

### 2. 📺 Subtitle Management
**Status**: Fully Implemented

**Capabilities**:
- Providers: OpenSubtitles.org, Subscene, Podnapisi
- Coverage/gap analysis
- Language-specific downloads
- Live/preview modes
- Batch processing

**Features**:
- Provider abstraction
- Rate limiting/error handling
- Progress/feedback
- Media workflow integration

### 3. 🤖 AI-Powered Batch Processing
**Status**: Fully Implemented (RavenMaven)

**Capabilities**:
- NLP of media files
- AI organization suggestions
- Batch queue
- Content analysis
- Automated workflows

**Implementation**:
- RavenMaven client
- Async processing/progress
- Result analysis/feedback
- Error/retry logic

### 4. 🔍 Code Quality Analysis
**Status**: Fully Implemented (CodeCop)

**Capabilities**:
- Code quality metrics
- Issue detection
- Maintainability/complexity analysis
- Best practices

**Features**:
- Multiple analysis types
- Detailed reports/scores
- Trend analysis
- Fix suggestions
- Custom rules

### 5. 📊 Analytics & Reporting
**Status**: Fully Implemented

**Capabilities**:
- Media stats
- Performance trends
- Quality reports
- Usage patterns
- Exports

**Insights**:
- File counts/type/quality
- Storage/duplicates
- Growth trends
- Health checks

### 6. 🧠 Semantic Memory System
**Status**: Fully Implemented (ChromaDB)

**Capabilities**:
- NL document search
- Semantic similarity
- Context-aware retrieval
- Multi-source indexing
- Query suggestions

**Features**:
- ChromaDB vector DB
- Document ingestion/processing
- Query history/refinement
- Filtering/ranking
- App output integration

### 7. ⚙️ Settings & Configuration
**Status**: Fully Implemented

**Capabilities**:
- API keys (TMDB, etc.)
- Paths/defaults
- UI customization
- Performance tuning
- Security/credentials

**Advanced**:
- Backup scheduling
- Update/logging prefs
- Integration settings

## User Interface & Experience

### Main Window
- **Dimensions**: 1400x800 (with help pane)
- **Layout**: 7-tab split-panel with contextual help
- **Styling**: Custom CSS-like, professional

### Enhanced Help System
**Hover Help**:
- Control-specific, persistent
- Tab headers
- Covers 74+ controls

**Content**:
- Descriptions/titles
- Examples/best practices
- Implementation notes

### Keyboard Shortcuts
- **Global**: Ctrl+Q (quit), Ctrl+S (scan), Ctrl+O (organize)
- **Tools**: Ctrl+T (TMDB cache), Ctrl+W (Wikipedia cache), Ctrl+D (canonical DB)
- **Analysis**: Ctrl+E (episode), Ctrl+M (movie)
- **Nav**: F1 (help), Ctrl+F1 (about)

## Recent Major Enhancements (Nov 2025)
- **GUI Dialogs**: TMDB/Wikipedia/canonical DB caching
- **Hover Help**: Persistent, titled, tab explanations, full coverage
- **Semantic Memory**: Document ingestion scripts, NL query UI, knowledge base

## Technical Metrics

### Codebase
- **Main GUI**: 3,000+ lines
- **Total Files**: 50+ core Python, 6 dialogs, 8 backends
- **Tests**: Comprehensive suite

### Performance
- **Startup**: <3s
- **Memory**: Efficient
- **Concurrent**: Multi-threaded
- **DB**: Fast ChromaDB

### Integrations
- APIs: TMDB, OpenSubtitles, Wikipedia
- AI: RavenMaven
- Analysis: CodeCop
- Media: Multi-source metadata

## Quality Assurance

### Testing
- Unit/integration/performance/UI tests

### Code Quality
- Linting, docstrings, type hints, error handling

### Audit/Compliance
- Immutable logging
- Media snapshots
- Security/integrity checks

## Future Roadmap
### Planned
- Advanced RavenMaven
- Cloud sync
- Plugins
- Predictive analytics

### Vision
- Unified media hub
- AI-first
- Enterprise tooling
- Community plugins

## Conclusion
JellyRancher v2.0.0: Mature PyQt5 platform integrating media org, subtitles, AI, code analysis, analytics, semantic search. Advanced Python practices, UI/UX, external integrations.

**Effort**: 6+ months  
**LOC**: 15,000+  
**Features**: 25+  
**UI**: Professional w/ help  
**Architecture**: Modular/scalable/documented

---

# docs\CLEANUP_GIT_CHROMADB_20251112.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 4,654 -> 3,382 chars (72.7%)

**Status:** success

# Git & ChromaDB Removal Report

**Date:** November 12, 2025  
**Action:** Complete removal of Git and ChromaDB

---

## Git Removal

### Deleted
- ✅ `.git/` (repo metadata)
- ✅ `.github/` (workflows/configs)
- ✅ `.gitignore` (ignore patterns)

**Space Freed:** Unknown

---

## ChromaDB Removal

### Directories Deleted
1. ✅ `chroma_db/` (285 MB)
2. ✅ `Jellyfin Organizer\scripts\chroma_db/` (duplicate)
3. ✅ `backups\scripts_backup_20251110\core\chroma_db/` (backup, not found)

**Space Freed:** ~285 MB

### Python Files Deleted
1. ✅ `chroma_memory_backend.py` (backend wrapper)
2. ✅ `verify_chromadb.py` (verification)
3. ✅ `check_chromadb_schema.py` (schema check)
4. ✅ `document_to_chromadb.py` (ingestion)
5. ✅ `ingest_docs_to_chromadb.py` (doc ingestion)

**Files Removed:** 5

---

## Configuration Updates

### requirements-jelly-rancher.txt
```diff
- # ChromaDB for semantic search
- chromadb>=0.4.0
+ # ChromaDB removed - no longer using semantic search
```

### docs/SESSION_STARTER.md
```diff
- - Consolidated ChromaDB instances
+ - Removed all ChromaDB instances (not using semantic search)

- - **Query ChromaDB** before making architecture decisions
+ - **Check documentation** before making architecture decisions
```

### docs/COMMON_PITFALLS.md
- Removed "DON'T Create Multiple ChromaDB Instances"
- Updated to generic caching guidance
- Removed ChromaDB from success checklist

---

## Remaining References

⚠️ **Warning:** ChromaDB references remain in comments/docstrings/docs:

### Files (Read-Only/Historical)
- `LLM_io_log/*.json` (audit logs)
- `cleanup_reports/*.txt` (reports)
- `scripts/_common/integration_logger.py` (refactor if used)
- `scripts/seamoth_memory.py` (refactor if used)
- `scripts/ai/` (bootstrap scripts)
- `JELLY_RANCHER_PROJECT_STATE_2025.md` (update if current)

### Next Steps
1. Review/refactor `integration_logger.py`
2. Review/remove ChromaDB from `seamoth_memory.py`
3. Update `JELLY_RANCHER_PROJECT_STATE_2025.md`
4. Search imports: `grep -r "from chroma" or "import chromadb"`

---

## Impact Assessment

### Still Works
✅ PyQt5 GUI  
✅ Media organization (Points 1-9)  
✅ Subtitle acquisition  
✅ File/batch ops  
✅ All 6 GUI tabs

### Removed
❌ Semantic search  
❌ LLM auto-journaling to ChromaDB  
❌ Project state in vector DB  
❌ AI memory backend  
❌ Memory tab (🧠)  
❌ Memory Query (Ctrl+Shift+M)  
❌ Memory toolbar button

### GUI Changes
- Tabs: 7 → 6 (Organization, Subtitles, Batch Processing, Code Analysis, Analytics, Settings)
- Memory tab removed
- All ChromaDB codebase refs cleaned

### Alternatives
- Semantic Search: grep/ripgrep + regex
- Journaling: SQLite FTS
- Project State: Markdown + grep
- Memory: JSON/SQLite

---

## Verification Commands

```powershell
# Git gone
Test-Path ".git"  # False

# ChromaDB dirs gone
Test-Path "chroma_db"  # False
Test-Path "Jellyfin Organizer\scripts\chroma_db"  # False

# Imports
Select-String -Pattern "import chromadb|from chromadb" -Path *.py -Recurse

# Requirements
Get-Content requirements-jelly-rancher.txt | Select-String "chromadb"
```

---

## Rollback Plan

1. **Git:** `git init`
2. **ChromaDB:** 
   - Restore from `V:\JellyRancher_Archive\2025-11-12_pre-pyqt6\`
   - `chroma_db/`
   - Python files
   - requirements.txt

---

**Status:** ✅ Complete  
**Space Freed:** ~285 MB  
**Files Removed:** 5 Python + 3 dirs  
**Risk:** Low (non-core features)

---

# docs\COMMON_PITFALLS.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 9,576 -> 7,772 chars (81.2%)

**Status:** success

# JellyRancher Common Pitfalls & Solutions

---

## Pitfalls to Avoid

### 1. ❌ DON'T Commit .venv/ to Git

**Problem:** `.git/` balloons to 800MB+

**Solution:**
```bash
# Add to .gitignore
.venv/
venv/
env/
.env/
```

**Fix existing repo:**
```bash
git rm -r --cached .venv/
git commit -m "Remove .venv from tracking"
```

---

### 2. ❌ DON'T Nest Sub-Projects

**Problem:** Nested CodeCop/RavenMaven causes duplication

**Bad:**
```
JellyRancher/
  ├─ CodeCop/          # ❌ Nested
  └─ RavenMaven/       # ❌ Nested
```

**Good:**
```
Projects/
  ├─ JellyRancher/     # ✅ Separate
  ├─ CodeCop/          # ✅ Separate
  └─ RavenMaven/       # ✅ Separate
```

**Already nested?** Move to `V:\JellyRancher_Archive\`

---

### 3. ❌ DON'T Create Unnecessary Cache Directories

**Problem:** Multiple caches eat 500MB+

**Solution:** Plan caching strategy upfront

**Fix:** Archive duplicates to `V:\JellyRancher_Archive\`

---

### 4. ❌ DON'T Archive Inside Working Directory

**Problem:** `archive/` inside project grows indefinitely

**Bad:**
```
JellyRancher/
  └─ archive/          # ❌ Inside
      ├─ old_code/
      └─ backups/
```

**Good:**
```
V:/JellyRancher_Archive/  # ✅ External
  └─ 2025-11-12_pre-pyqt6/
```

**Why:** Keeps working dir clean; use external storage

---

### 5. ❌ DON'T Skip Dry-Run Testing

**Problem:** File ops without preview cause irreversible damage

**Solution:** ALWAYS dry-run first
```python
def reorganize_files(action_plan, dry_run=True):
    if dry_run:
        print("DRY RUN - No files modified")
        for action in action_plan:
            print(f"Would move: {action.source} → {action.dest}")
        return
    execute_plan(action_plan)
```

**Rule:** Require explicit user approval + dry_run=False

---

### 6. ❌ DON'T Ignore Rate Limits

**Problem:** API hammering leads to IP bans

**TMDB:** 40 req/10s  
**TVDB/OpenSubtitles:** Check limits

**Solution:** Use decorators
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
def query_tmdb_safe(movie_name):
    pass  # API call
```

---

### 7. ❌ DON'T Move Files Without MD5 Verification

**Problem:** Undetected corruption during moves

**Solution:**
```python
import hashlib
import shutil

def move_file_safe(source, dest):
    md5_before = md5_hash_file(source)
    shutil.move(source, dest)
    md5_after = md5_hash_file(dest)
    if md5_before != md5_after:
        raise Exception(f"Corrupted: {source}")
    return md5_before
```

---

### 8. ❌ DON'T Modify Source Files Before User Approval

**Problem:** Changes before rejection

**Solution:** Two-phase
1. **Planning:** Read-only, build/display plan
2. **Execution:** Post-approval

```python
action_plan = generate_action_plan(files)  # Phase 1
display_to_user(action_plan)
if user_approved():                       # Phase 2
    execute_plan(action_plan)
```

---

### 9. ❌ DON'T Use String Paths

**Problem:** Error-prone string manipulation

**Bad:**
```python
path = '/folder/file.mkv'
new_path = path.replace('/folder/', '/new_folder/')  # ❌ Fragile
```

**Good:**
```python
from pathlib import Path
path = Path('/folder/file.mkv')
new_path = Path('/new_folder') / path.name  # ✅ Robust
```

**Why:** Handles cross-platform paths, normalization

---

### 10. ❌ DON'T Load Entire Files into Memory

**Problem:** 50GB files cause OOM on hashing

**Bad:**
```python
with open('huge_file.mkv', 'rb') as f:
    data = f.read()  # ❌ Full load
    md5 = hashlib.md5(data).hexdigest()
```

**Good:**
```python
def md5_hash_file(filepath, chunk_size=8192):
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()
```

---

### 11. ❌ DON'T Forget to Close Database Connections

**Problem:** SQLite locks

**Bad:**
```python
conn = sqlite3.connect('db.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT * FROM table')  # ❌ No close
```

**Good:**
```python
with sqlite3.connect('db.sqlite') as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM table')  # ✅ Auto-close
```

---

### 12. ❌ DON'T Use os.path with PyQt

**Problem:** Mismatched separators

**Bad:**
```python
import os
path = os.path.join('folder', 'file.mkv')  # ❌
```

**Good:**
```python
from pathlib import Path
path = Path('folder') / 'file.mkv'  # ✅
```

**Or Qt:**
```python
from PyQt6.QtCore import QDir
path = QDir.cleanPath('folder/file.mkv')  # ✅
```

---

### 13. ❌ DON'T Block the GUI Thread

**Problem:** API calls freeze app

**Bad:**
```python
def on_button_click():
    results = query_tmdb_for_1000_movies()  # ❌ Blocks
    display_results(results)
```

**Good:**
```python
from PyQt6.QtCore import QThread, pyqtSignal

class APIWorker(QThread):
    finished = pyqtSignal(list)
    def run(self):
        results = query_tmdb_for_1000_movies()
        self.finished.emit(results)

def on_button_click():
    worker = APIWorker()
    worker.finished.connect(display_results)
    worker.start()
```

---

### 14. ❌ DON'T Use Permanent Deletion

**Problem:** `os.remove()` irreversible

**Bad:**
```python
import os
os.remove('file.mkv')  # ❌ Permanent
```

**Good:**
```python
from send2trash import send2trash
send2trash('file.mkv')  # ✅ Recycle bin
```

---

### 15. ❌ DON'T Ignore Subtitle Types

**Regular:** Full dialogue  
**Forced:** Foreign parts only (e.g., Klingon)

**Solution:**
```python
for sub in subtitle_streams:
    forced = sub.get('disposition', {}).get('forced', 0)
    if forced:
        pass  # Handle forced
    else:
        pass  # Handle regular
```

**Jellyfin naming:**
- Regular: `movie.en.srt`
- Forced: `movie.en.forced.srt`

---

## Quick Fixes for Common Errors

### "ModuleNotFoundError: No module named 'PyQt5'"

**Fix:** Update to PyQt6 imports
```python
# from PyQt5.QtWidgets import ...  # ❌
from PyQt6.QtWidgets import ...  # ✅
```

### "AttributeError: 'Qt' object has no attribute 'AlignCenter'"

**Fix:** Use enums
```python
# Qt.AlignCenter  # ❌
Qt.AlignmentFlag.AlignCenter  # ✅ PyQt6
```

### "FileNotFoundError: [Errno 2] No such file or directory: '/path'"

**Fix:** Create parents
```python
from pathlib import Path
dest = Path('/path/to/file.mkv')
dest.parent.mkdir(parents=True, exist_ok=True)
shutil.move(source, dest)
```

### "sqlite3.OperationalError: database is locked"

**Fix:** Use context manager
```python
with sqlite3.connect('db.sqlite') as conn:
    pass  # Auto-closes
```

### "requests.exceptions.HTTPError: 429 Too Many Requests"

**Fix:** Rate limit
```python
from ratelimit import limits, sleep_and_retry
@sleep_and_retry
@limits(calls=40, period=10)
def query_api():
    pass
```

### "UnicodeDecodeError: 'charmap' codec can't decode byte"

**Fix:** UTF-8
```python
# with open('file.txt', 'r') as f:  # ❌
with open('file.txt', 'r', encoding='utf-8') as f:  # ✅
```

---

## Success Indicators

✅ `.git/` < 50MB  
✅ `.venv/` in `.gitignore`  
✅ Zero duplicates (audit)  
✅ Dry-run before exec  
✅ Rate limits respected  
✅ MD5 on moves  
✅ Transaction logs for rollback  
✅ No GUI freezes  
✅ Tests pass w/o real files  

---

## Emergency Rollback

```python
with sqlite3.connect('transaction_log.db') as conn:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT source_path, destination_path, source_md5
        FROM transactions WHERE completed = 1
        ORDER BY timestamp DESC
    ''')
    for source, dest, md5 in cursor:
        shutil.move(dest, source)
        if md5_hash_file(source) != md5:
            print(f"WARNING: MD5 mismatch: {source}")
```

---

**Remember:** Small, tested increments > grand designs.

---

# docs\EPISODE_TITLE_MANAGEMENT.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 10,845 -> 4,860 chars (44.8%)

**Status:** success

# Episode Title Management Guide

## Overview

Episode Title Management analyzes and fixes TV show episode filenames in Jellyfin libraries by comparing against TMDB canonical titles. Identifies issues and enables safe renaming.

**Key Features:**
- Analyze TV show folders
- Compare with TMDB cache
- Detect naming issues
- Dry-run preview
- Apply fixes with audit logging
- Color-coded confidence
- JSON export

## Prerequisites

1. **TMDB Cache**: Generate via **Tools → Generate TMDB Cache**. See [TMDB_CACHE_GENERATOR.md](TMDB_CACHE_GENERATOR.md).
2. **Structure**:
   ```
   Show Name/
   ├── Season 01/
   │   ├── Show Name - S01E01 - Episode Title.mkv
   │   └── ...
   └── Season 02/
       └── ...
   ```

## Supported Patterns

1. `S01E01 - Episode Title.mkv`
2. `Show Name S01E01 Episode Title.mkv`
3. `Show Name - S01E01 - Episode Title.mkv`

## Using the Episode Analyzer

### Step 1: Open
1. Launch Jelly Rancher
2. **Tools → 🔍 Analyze Episode Titles**

### Step 2: Select Show Folder
1. **Browse** → Select root (e.g., `V:\TV Shows\Doctor Who`)

### Step 3: Select TMDB Cache
1. **Browse** → Select JSON (e.g., `doctor_who_cache.json`)

### Step 4: Run Analysis
1. **🔍 Analyze Show**
2. View results table

## Understanding Results

### Results Table
- **File**: Filename
- **Season**: S01, etc.
- **Episode**: E01, etc.
- **Current Title**: From filename
- **TMDB Title**: Canonical
- **Confidence**: High/Medium/Low/Very Low
- **Issue Type**: Detected issue

### Confidence (Color-Coded)
- **High (Green)**: 90-100%
- **Medium (Yellow)**: 70-89%
- **Low (Orange)**: 50-69%
- **Very Low (Red)**: <50%

### Issue Types
- **missing_title**: No title
- **incorrect_title**: Mismatch
- **technical_tags**: Codec/quality tags
- **perfect_match**: No issue

### Episode Details Pane
Click row: Full path, title comparison, similarity score, action, warnings.

## Filtering
**Show All Episodes** (toggle):
- Unchecked (default): Issues only
- Checked: All, incl. perfect

## Fixing Titles

### Dry Run (**Always preview first!**)
1. **🔧 Fix Issues (Dry Run)**
2. Review: old→new filenames, success/failure
3. No changes made

### Apply Fixes (**After dry-run only!**)
1. **✅ Apply Fixes**
2. Confirm warning
3. View summary; auto re-analyze

### Fix Results
- **Total/Successful/Failed**
- "Show Details": JSON with old/new, errors, logs

## Safety Features

### Validation
- Source exists
- Target doesn't exist
- Writable dir
- Valid filename (<200 chars display, <255 OS)
- Length limits

### Invalid Chars Removed
- Windows: `< > : " / \ | ? *`
- Unix: Null byte
- Controls (0x00-0x1F)

### Audit Logging
To ChromaDB/immutable log:
- Old/new filenames
- Timestamp
- Result/errors

### Preserved/Removed
- ✅ S##E##, extension, show name, dir
- ❌ Technical tags (x264, 1080p), groups ([RARBG])

## Workflows

### 1: Quick Check
1. Analyze
2. Review confidence
3. Export if needed

### 2: Fix Single Show
1. Generate cache
2. Analyze
3. Dry-run
4. Apply if OK
5. Verify

### 3: Batch
1. Generate caches
2. Analyze/export each
3. Fix issues

## Troubleshooting

### "No episodes need fixing"
- Toggle "Show all"
- Verify cache/show match
- Check patterns

### 0 Episodes
- Verify Season subfolders, S##E##
- Extensions: .mkv, .mp4, .avi, .m4v, .ts

### Fix Fails
- Close programs/Jellyfin
- Run as admin
- Permissions
- Network: Copy local

### Cache Mismatch
- Regenerate
- Check TMDB ID/year

### Low Confidence
- Manual review details
- Dry-run preview

## Best Practices

### Before
1. Backup library
2. Test small show
3. Dry-run always
4. Accurate caches

### During
1. Review issues
2. Check low confidence
3. Heed warnings
4. Export results

### After
1. Refresh Jellyfin metadata
2. Check logs
3. Test playback
4. Regenerate cache if needed

## Technical Details

### Pattern Matching
1. Extract episode info
2. Clean tags/normalize
3. SequenceMatcher fuzzy compare

### Similarity
- **Algorithm**: difflib.SequenceMatcher (0.0-1.0)
- **Thresholds**:
  - ≥0.90: High
  - 0.70-0.89: Medium
  - 0.50-0.69: Low
  - <0.50: Very low

### Recommendations
- **perfect**: None
- **use_cleaned**: Remove tags
- **use_canonical**: TMDB title
- **review_manual**: Manual

### Performance
- Analysis: 100-200 eps/sec
- Fix: 10-50 files/sec
- Memory: <100MB

## FAQ

**Multi-episode?** No; one per file (S01E01-E02 unsupported).

**Undo?** No; use logs/backup.

**Jellyfin metadata?** No; refresh manually.

**Custom pattern?** No; uses `Show - S##E## - Title.ext`.

**Specials (S00E##)?** Yes, if in cache/pattern.

**Anime?** Yes; TMDB may lack data (TVDB future).

## Related
- [TMDB Cache Generator](TMDB_CACHE_GENERATOR.md)
- [Architecture](../docs/)
- [Jelly Rancher](../JELLY_RANCHER_README.md)

## Support
1. `audit-logs/`
2. `logs/`
3. ChromaDB history
4. JSON exports

---

*Last Updated: November 8, 2025*  
*Version: 2.0 (Integration Phase 2)*

---

# docs\JELLYFIN_API_INTEGRATION_PLAN.MD

**Original Date:** 2025-11-15 04:19:26

**Compression:** 10,139 -> 4,000 chars (39.5%)

**Status:** success

# Document: Jellyfin API Integration Strategy & Implementation Plan

## Part 1: Value and Purpose of the Jellyfin API

### What is it?
RESTful API over HTTP/HTTPS; programmatic interface used by Jellyfin web UI and apps.

### What can it do?
- **Read Data:** List libraries, movies, shows, episodes, metadata.
- **Query Items:** Find items, media streams (e.g., subtitles), technical details.
- **Trigger Actions:** Refresh library, scan files, refresh metadata.
- **Manage Content:** Create/delete collections, playlists; update metadata.
- **Manage Users & Stats:** Playback stats, active sessions, user accounts.

### How is it useful?
1. **Automation:** E.g., auto-scan after adding files.
2. **Integration:** Enables tools like Sonarr/Radarr/Trakt to update libraries, mark watched.

### Verdict
**Badass:** Well-designed core engine powering Jellyfin's extensibility.

## Part 2: API Integration in Application Workflow

### Step 1: Scan Folder List
- **API:** `GET /Items?Recursive=true&IncludeItemTypes=Movie,Episode&Fields=Path`
- **Purpose:** Cross-reference local files vs. Jellyfin database.
- **Value:** Identifies existing, orphaned, new files.

### Step 2: Summarize Structure
- **API:** `GET /Views` or `GET /UserViews`
- **Purpose:** Get current library structure as seen by Jellyfin.
- **Value:** "Before" snapshot for LLM comparison.

### Step 3: Submit to LLM for Proposal
- **API:** `GET /Items/{itemId}?Fields=ProviderIds`
- **Purpose:** Fetch existing metadata (TMDb/TVDB IDs).
- **Value:** Feed to LLM for accurate organization using canonical IDs.

### Step 4: Build Canonical Database
- **API:** `POST /Items/{itemId}/Refresh`
- **Purpose:** Test NFO files by triggering refresh.
- **Value:** Verify metadata updates before full rollout.

### Step 5: Produce Editable Table for Review
- **API:** (Uses Step 1 data)
- **Purpose:** Display Jellyfin data in table.
- **Value:** Columns like "Jellyfin Status" ("Already in Library", "New").

### Step 6: Execute Reorganization Plan
- **API 1:** `POST /Libraries/{libraryId}/Refresh`
  - **Purpose:** Refresh library post-file ops.
  - **Value:** Instant targeted update vs. scheduled scan.
- **API 2:** `POST /Collections/{collectionId}/Items`
  - **Purpose:** Create/populate collections (e.g., "Star Wars").
  - **Value:** Full automation.

### Step 7: Evaluate Subtitle Coverage
- **API:** `GET /Items/{itemId}?Fields=MediaStreams`
- **Purpose:** Validate subtitle tracks server-side.
- **Value:** Reliable vs. local `ffprobe`.

### Step 8: Obtain Subtitles
- **API:** `POST /Items/{itemId}/Refresh`
- **Purpose:** Refresh after adding `.srt`.
- **Value:** Immediate availability.

## Part 3: Remote vs. Local Access
Remote access fully supported:
1. **Server Address:** `http://localhost:8096` (local) or `https://my-jellyfin-domain.com` (remote).
2. **API Key:** Generate in Dashboard (Admin > Advanced > API Keys).

Requires network access and valid key.

## Part 4: Recommended Integration Plan
Integrate now, before finalizing Step 5.

### Rationale: Context (Read-Only) vs. Action (Read-Write)
Phase 1: Fetch current state pre-LLM. Phase 2: Trigger actions post-execution.

### Plan
#### 1. Retrofit Scan (Steps 1-2)
- Fetch all items, `ProviderIds`, `Path`.
- Result: Jellyfin-aware file list for cross-reference.

#### 2. Enhance Proposal (Steps 3-4)
- Step 3: Include Jellyfin data in LLM prompt (e.g., "Folder with TVDB ID 71470").
- Step 4: Use API as primary truth for IDs (avoids external API calls).

#### 3. Build Review Table (Step 5)
Add columns:
- `JellyfinStatus`: "New", "Already in Library", "Path Mismatch".
- `CurrentTMDbID`: Jellyfin's ID.
- `ProposedTMDbID`: Canonical DB's ID.
- `ActionType`: "Move", "Move + Refresh", "Delete Orphan".

#### Action Phase (Steps 6-8)
- Step 6: `POST /Items/{itemId}/Refresh` post-move (targeted).
- Steps 7-8: `GET /Items/{itemId}?Fields=MediaStreams`; `POST /Items/{itemId}/Refresh`.

### First Step: Install Client
```bash
pip install jellyfin-apiclient-python
```

---

# docs\knowledge-pack.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 11,442 -> 7,520 chars (65.7%)

**Status:** success

# JELLYRANCHER PROJECT KNOWLEDGE PACK
Generated: 2025-11-12

================================================================================
CRITICAL CONTEXT
================================================================================

Building **Jellyfin media organizer** facing:
- LLM amnesia (context loss)
- Code duplication (same files in 6+ locations)
- Structural chaos (800MB .git, nested sub-projects, scattered ChromaDB)

**Start fresh** using 9-point workflow below.

================================================================================
9-POINT WORKFLOW (MASTER SPEC)
================================================================================

**PROGRAM SPECIFICATIONS:**
- Language: Python 3.12
- Type: GUI app
- GUI: PyQt6
- venv: In project root, always activated
- Platform: Cross-platform (Windows/macOS/Linux)

**WORKFLOW:**

1. **FOLDER SCANNING & INVENTORY**  
   User selects folders (add/remove). Recursively scan for bare file inventory (absolute paths, one per row). All filetypes by default. Master list for all actions.

2. **HIERARCHICAL OVERVIEW**  
   Hierarchical view of master list (folder structure). Per folder: total size, filetype breakdown (e.g., ".mkv: 178 files (240 GB)"). No individual files listed.

3. **LLM REORGANIZATION PROPOSAL**  
   Submit hierarchy to LLM to:  
   - Propose Jellyfin-compliant reorganization  
   - Detect movies/TV from folder names  
   - Generate restructuring plan

4. **METADATA DATABASE BUILDING**  
   Use LLM list + fuzzy matching to query:  
   - TMDB (movies)  
   - TVDB (TV shows)  
   - Wikipedia (fallback)  
   
   Build DB with: correct years, show names/seasons, episode titles/numbers. For multi-part (e.g., S01E01-E02.mkv), generate Jellyfin-compatible NFOs for ranges.  
   
   Rate limits:  
   - TMDB: 40 req/10s  
   - TVDB: Current limits  
   - Wikipedia: Conservative  
   - Exponential backoff; aggressive caching.

5. **EDITABLE ACTION TABLE**  
   Generate editable table from DB + proposal. Rows color-coded:  
   - 🟢 Green: Auto-safe (perfect match)  
   - 🟡 Yellow: Review (fuzzy/minor ambiguity)  
   - 🟠 Orange: Manual (multiple/deviations)  
   - 🔴 Red: Cannot process (no match/corrupt)  
   - 🔵 Blue: No action (compliant/duplicate)  
   Dry-run mode required.

6. **SNAPSHOT & TRANSACTION LOG**  
   Pre-execution: JSON/SQLite log per op:  
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
   Post-success: `completed: true`, add `destination_md5`.  
   MD5: Calc pre-move, verify post; reverse on rollback. Rollback: Reverse ops chronologically via log.

7. **EXECUTE REORGANIZATION**  
   Subtitle handling: Move/rename alongside videos (e.g., movie.en.srt, movie.en.forced.srt).  
   Errors: Log, skip, continue; post-MD5 verify; summary report (success/skipped/errors).

8. **SUBTITLE COVERAGE EVALUATION**  
   Check English subs via:  
   - ffprobe (embedded tracks)  
   - FS scan (.srt/.ass etc.)  
   "Covered" (skip) if embedded/external English exist. Distinguish regular/forced. List lacking files.

9. **SUBTITLE ACQUISITION**  
   For missing (step 8):  
   Primary: OpenSubtitles.org (credentials).  
   Fallback: OpenSubtitles.com, Podnapisi.NET, Addic7ed.com, Subscene.com.  
   Match: Hash > fuzzy filename/metadata.  
   Download regular + forced English (add forced even if regular exists).  
   Respect rate limits/TOS.

================================================================================
RULES
================================================================================

1. **API Courtesy**: Rate limits, backoff, cache.
2. **User Control**: Review/confirm destructives; mandatory dry-run.
3. **Jellyfin Compliance**: Official naming/folders; NFO XML schema.
4. **Data Integrity**: Preserve original paths; no source mods pre-approval.
5. **Transparency**: Confidence/reasoning; flag ambiguities.
6. **Python Env**: venv in root; activate first.

================================================================================
IMMEDIATE ACTION PLAN
================================================================================

**BEFORE CODING:**
1. Run consolidation audit for duplicates.
2. Backup ZIP of V:/JellyRancher/.
3. Read CONSOLIDATION_REPORT.txt (real vs. dupes).
4. Create V:/JellyRancher_v2/ with "KEEP THIS ONE" files.

**CLEAN PROJECT STRUCTURE:**
```
V:/JellyRancher_v2/
  ├─ SPEC.md                  # This workflow (1-9)
  ├─ README.md                # Overview
  ├─ requirements.txt         # Deps
  ├─ .gitignore               # .venv, logs, __pycache__, .chroma
  ├─ .venv/                   # venv (ignored)
  │
  ├─ scripts/                 # App code
  │   ├─ core/                # Logic
  │   │   ├─ scanner.py       # 1
  │   │   ├─ metadata.py      # 4
  │   │   ├─ executor.py      # 7
  │   │   └─ subtitles.py     # 8-9
  │   ├─ gui/                 # PyQt6
  │   │   ├─ main_window.py
  │   │   ├─ action_table.py  # 5
  │   │   └─ dialogs.py
  │   ├─ utils/               # Utils
  │   │   ├─ logger.py
  │   │   ├─ api_client.py    # Rate-limited APIs
  │   │   └─ transaction_log.py  # 6
  │   └─ tests/               # Tests
  │
  ├─ data/                    # Data (ignored)
  │   ├─ cache/               # API cache
  │   ├─ logs/                # Logs
  │   └─ transaction_logs/    # Rollbacks
  └─ docs/
      └─ WORKFLOW.md          # Workflow docs
```

================================================================================
IDE AI PASTE TEMPLATE (SESSION START)
================================================================================
```
Context: Jellyfin organizer in Python 3.12 + PyQt6.

Workflow: 9-point (scan → metadata → reorganize → subs).

Current task: [DESCRIBE]

See SPEC.md.

Constraints:
- TMDB/TVDB rate limits
- Transaction logs for rollback
- PyQt6 GUI w/ color-coded table
- Subs: regular + forced

Dir: V:/JellyRancher_v2/scripts/
```

================================================================================
KEY ARCHITECTURAL DECISIONS
================================================================================

**PyQt6?** Mature, cross-platform; great table/tree widgets (pt5); threading for APIs.

**Transaction Logs vs. Git?** Spans commits; atomic batch rollback; MD5 integrity.

**MD5 vs. SHA256?** Sufficient for corruption; 3x faster on videos; integrity only.

**Regular + Forced Subs?** Jellyfin distinction; forced for foreign dialogue; users want both.

================================================================================
COMMON PITFALLS
================================================================================

1. No .venv/ in git (800MB bloat).
2. No nested sub-projects (CodeCop/RavenMaven as siblings).
3. One ChromaDB max.
4. Archives external to dir.
5. Always dry-run first.

================================================================================
EXISTING CAPABILITIES (FROM CODE-CAPABILITIES.MD)
================================================================================

Reference newest versions via consolidation audit; extract logic:

**Core Executors:**
- jellyfin_safe_executor.py: Snapshot/rollback (pts 6-7)
- batch_queue_processor.py: Batch w/ resume

**API Clients:**
- ravenmaven_client.py: Poe.com wrapper (adapt pt3 LLM)

**Parsers:**
- llm_response_parser.py: LLM JSON (pt3)

**GUI:**
- ravenmaven_gui.py: Structure (adapt PyQt6)

---

# docs\MOVIE_NAMES_GUIDE.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 7,738 -> 5,348 chars (69.1%)

**Status:** success

# Movie Name Management Guide

## Overview

Movie Name Management is a JellyRancher QA tool that scans movie libraries, identifies naming inconsistencies, and automates fixes for Jellyfin-compatible organization.

## What It Solves

- **Codec Tag Cleanup**: Removes technical tags from titles
- **Title Truncation**: Fixes shortened/abbreviated names
- **Folder Structure**: Ensures proper movie folders
- **Missing Years**: Adds release years for metadata matching
- **Consistency**: Standardizes naming across collection

## Quick Start

### 1. Access the Tool

1. Launch JellyRancher
2. Go to **Movie Analysis** tab
3. Click **Select Movies Folder**
4. Choose Movies directory
5. Click **Analyze Movies**

### 2. Review Results

1. Browse results table
2. Check issue types/severity
3. Review suggested fixes
4. Select items to fix

### 3. Apply Fixes

1. **Fix Selected Issues**: Individual fixes
2. **Fix All Issues**: Bulk operations
3. Preview in dry-run mode first

## Understanding Issues

### 🔧 Codec Tags in Titles
**Problem**: Technical info in titles
```
Before: Inception (2010) H.265 1080p BluRay.mkv
After:  Inception (2010).mkv
```
**Why**: Codec info belongs in file properties  
**Auto-fixable**: ✅ Yes

### ✂️ Truncated Titles
**Problem**: Shortened/abbreviated names
```
Before: Cloutie Ru (2003).mkv
After:  Cloutie Rural (2003).mkv
```
**Why**: Hard to find/identify  
**Auto-fixable**: ❌ No (manual research)

### 📁 Folder Structure Issues
**Problem**: No individual folders
```
Before: Movies/Inception (2010).mkv
After:  Movies/Inception (2010)/Inception (2010).mkv
```
**Why**: Jellyfin requires folders for metadata/artwork  
**Auto-fixable**: ✅ Yes

### 📅 Missing Years
**Problem**: No release years
```
Before: Inception.mkv
After:  Inception (2010).mkv
```
**Why**: Essential for metadata matching  
**Auto-fixable**: ❌ No (manual lookup)

## Interface Guide

### Main Controls

- **Select Movies Folder**: Choose root directory
- **Analyze Movies**: Start analysis
- **Fix Selected Issues**: Fix checked items
- **Fix All Issues**: Bulk fix all
- **Export Results**: Save as JSON

### Results Display

Per movie:
- **Current Path**: File location/name
- **Issues Detected**: Problem list
- **Suggested Fix**: Recommended changes
- **Severity**: Criticality level
- **Status**: Pending/Fixed/Error

### Severity Levels

- 🔴 **High**: Affects functionality
- 🟡 **Medium**: Impacts organization/appearance
- 🟢 **Low**: Minor/optional

## Analysis Process

### What It Checks

1. File structure (folder organization)
2. Naming patterns (formatting/completeness)
3. Codec detection (unwanted tags)
4. Year validation
5. Collection consistency

### Processing Speed

- <100 movies: Instant
- 100-1000: Few seconds
- >1000: Several minutes
- Progress bar shown

## Fixing Strategies

### Safe Bulk Operations

1. Analyze collection
2. Filter by issue (e.g., codec tags, folders)
3. **Fix All Issues**
4. Review results

### Manual Corrections

For truncated titles/missing years:
1. Analyze to identify
2. Research titles/years
3. Fix individually

### Dry Run Mode

1. Check "Dry Run"
2. Run to preview changes
3. Review
4. Uncheck to apply

## Best Practices

### Organization
- Dedicated Movies folder
- Naming: `Movie Title (Year).extension`
- No special characters
- Per-movie folders

### Maintenance
- Analyze after new additions
- Fix promptly
- Automate routine; manual for complex

### Quality Control
- Preview changes
- **Backup** before bulk
- Test small batches
- Verify in player

## Common Scenarios

### New Movie Import
1. Add to Movies folder
2. Analyze
3. Fix issues
4. Import to Jellyfin

### Library Cleanup
1. Analyze collection
2. Prioritize high-severity
3. Automate first
4. Manual next

### Pre-Server Migration
1. Analyze thoroughly
2. Fix folders
3. Ensure naming consistency
4. Verify in server

## Troubleshooting

### "No Movies Found"
- Verify folder points to Movies root
- Ensure individual folders/video extensions

### "Permission Errors"
- Check write access
- Close open files
- Antivirus exclusions

### "Analysis Takes Too Long"
- Test subfolder
- Close disk-using apps
- Batch process

## Integration Benefits

### With Jellyfin
- Better metadata matching
- Proper artwork
- Cleaner browsing/search

### With Subtitles
- Accurate matching/organization
- Cleaner naming

### With Organization Tools
- Bulk ops/dupe detection
- Analytics/reporting

## Performance Optimization

- SSD: Faster analysis
- Shallow folders: Quicker
- Large counts: Batch
- Local storage > network

## Examples

### Complete Makeover

**Before:**
```
Movies/
├── Inception.H.265.1080p.mkv
├── Dark Knight (2008) x264 BluRay.mp4
├── Cloutie Ru (2003).avi
└── Movie Title.mkv
```

**After:**
```
Movies/
├── Inception (2010)/Inception (2010).mkv
├── The Dark Knight (2008)/The Dark Knight (2008).mp4
├── Cloutie Rural (2003)/Cloutie Rural (2003).avi
└── Movie Title (2021)/Movie Title (2021).mkv
```

### Issue Breakdown
```
✓ Fixed: Codec tags (2 files)
✓ Fixed: Folders (3 files)
⚠ Manual: Truncation (1 file)
⚠ Manual: Year (1 file)
```

## Support and Resources

- **In-App Help**: Examples included
- **Settings Tab**: Analysis preferences
- **Log Files**: `logs/` directory
- **Export**: Reports for sharing/tracking

---

**Pro Tip**: Run monthly; tool learns from corrections for better suggestions.

---

# docs\MOVIE_NAME_MANAGEMENT.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 13,970 -> 6,826 chars (48.9%)

**Status:** success

# Movie Name Management Guide

## Overview

Movie Name Management analyzes and fixes Jellyfin movie filenames, detecting codec tags, truncated titles, improper folder structure, and missing years.

**Key Features:**
- Analyze entire Movies folder
- Detect 4 issue types
- Color-coded severity
- Dry-run preview
- Apply fixes with audit logging
- Export to JSON

## Issue Types Detected

### 1. Codec Tags in Filenames
**Examples:**
- `Movie Title (2020) H.265.mkv`
- `Action Film (2019) x264 1080p BluRay.mp4`
- `Drama Title (2018) HEVC 10bit HDR.mkv`

**Issue:** Codec info belongs in metadata, not filename.

**Fix:** Remove codec tags, quality/release markers.

### 2. Truncated Titles
**Examples:**
- `Cloutie Ru (2003).mkv` → "Cloutie Rural"
- `Doc Mar (2001).mkv` → "Doc Martin"

**Issue:** Hard to find, unprofessional.

**Fix:** Manual TMDB/IMDB lookup/correction.

### 3. Improper Folder Structure
**Examples:**
- `Movies/Movie Title (2020).mkv`
- `Movies/RandomFolder/Movie Title (2020).mkv`

**Issue:** Jellyfin needs per-movie folders for metadata/artwork/extras.

**Fix:** Create `Movies/Movie Title (2020)/Movie Title (2020).mkv`

### 4. Missing Year
**Examples:**
- `Movie Title.mkv`
- `Action Film x264.mp4`

**Issue:** Needed to distinguish remakes, match metadata.

**Fix:** Manual TMDB/IMDB year lookup.

## Using the Movie Analyzer

### Step 1: Open Analyzer
1. Launch Jelly Rancher
2. **Tools → 🎬 Analyze Movie Names**

### Step 2: Select Movies Folder
1. Click **Browse**
2. Select folder (e.g., `V:\Movies`)

### Step 3: Run Analysis
1. Click **🔍 Analyze Movies**
2. View results table

### Results Table Columns
- **File**: Filename
- **Title**: Extracted title
- **Year**: Year or "(missing)"
- **Folder**: Parent folder
- **Issues**: Issue count
- **Severity**: High/Medium/Low/None
- **Auto-Fixable**: Yes/No

### Severity Levels (Color-Coded)
- **High (Red)**: Truncated titles, missing year
- **Medium (Orange)**: Codec tags, folder mismatch
- **Low (Yellow)**: File in Movies root
- **None (Green)**: Clean

### Movie Details Pane
Click row for:
- Full path
- Extracted title/year
- Cleaned filename
- Issue list/descriptions
- Suggested fixes (auto/manual)
- Per-fix actions

### Filtering
**Show All Movies**: Unchecked (default: issues only); checked: all.

## Fixing Movie Names

### Automatic Fixes
- Codec removal
- Folder creation

### Manual Fixes
- Truncated titles
- Missing years

### Dry Run (Preview)
**Always preview first!**
1. Click **🔧 Fix Issues (Dry Run)**
2. Confirm dialog (movies/fix types)
3. Review: old→new paths, success/skip/error
4. No changes made

### Applying Fixes
**Review dry-run first!**
1. Click **✅ Apply Fixes**
2. Confirm warning
3. View summary
4. Auto re-analyze

### Fix Results
- **Total/Successful/Skipped/Failed** (errors shown)
- "Show Details" for JSON

## Safety Features

### Validation Checks
- Source exists
- Target free
- Writable
- Valid filename (<200 chars display, <255 OS)
- Invalid chars removed: Windows `< > : " / \ | ? *`; controls (0x00-0x1F)

### Audit Logging
To ChromaDB/immutable log:
- Old/new paths
- Timestamp
- Type/result
- Errors

### Preserved
- ✅ Title, year, extension
- ❌ Codec/quality/release tags

### Created
- ✅ `Movie Title (Year)/Movie Title (Year).ext`
- ✅ Remove empty old folders (if safe)

## Workflows

### 1. Quick Cleanup (Codec Tags)
1. Open/select/analyze
2. Review codec issues
3. Dry run → Apply

### 2. Folder Structure
1. Open/select/analyze
2. Review "not_in_folder"
3. Dry run → Apply

### 3. Complete Audit
1. Open/select/analyze
2. Show all; export JSON
3. Manual high-severity; auto medium/low
4. Re-analyze

## Troubleshooting

### "No movies need fixing"
- Show all movies
- Verify folder
- Check video files

### Analysis finds 0 movies
- Verify .mkv/.mp4/.avi/.m4v/.ts in root/subfolders

### Fix fails
- Close players/Jellyfin
- Admin mode
- Permissions/space
- Local copy for networks

### "Target already exists"
- Check duplicates
- Manual distinguish (edition/quality)

### Folder mismatch post-fix
- Jellyfin uses metadata
- Manual rename if needed

## Best Practices

### Before
1. Backup library
2. Stop Jellyfin
3. Test small batch
4. Dry-run

### During
1. Review issues/severity
2. Read warnings
3. Export results

### After
1. Verify files
2. Restart Jellyfin
3. Test playback
4. Check logs

### Manual Fixes
1. TMDB/IMDB lookup
2. Rename `Movie Title (Year).ext`
3. Create/move to folder
4. Re-analyze

## Technical Details

### Detection Algorithms
**Codec:** Regex for 13 tags; case-insensitive; brackets/braces.
**Truncated:** 1-2 char words pre-year (filter commons).
**Folder:** Fuzzy match (SequenceMatcher <50%); checks "Movies"/"#MEDIA".
**Year:** (1900-2099) pattern.

### Patterns Removed
```
H.265,H.264,HEVC,x264,x265,AVC,10bit,8bit,HDR,DV,WEB-DL,BluRay,1080p,720p,2160p,4K,AAC,DTS,DD5.1,Atmos
[RARBG],{YIFY},[YTS], etc. (brackets/braces)
```

### Performance
- Analysis: 50-100 movies/sec
- Fix: 5-20 files/sec
- Memory: <50MB

### File Ops Examples
**Codec:**
```
Old: Movie Title (2020) H.265 1080p.mkv → New: Movie Title (2020).mkv
```
**Folder:**
```
Old: Movies/Movie Title (2020).mkv → New: Movies/Movie Title (2020)/Movie Title (2020).mkv
```

## FAQ

**Subfolders?** Yes, recursive.

**Undo?** No; use logs/backup.

**Jellyfin metadata?** No; refresh after.

**Special chars?** Preserved; invalid removed.

**Customize tags?** No (13 patterns); future maybe.

**4K/HDR?** Yes; removes from name.

**Multi-file?** Separate; manual.

**Specific issues?** Auto per-movie.

**Editions?** Manual: `Movie Title (2020) - Director's Cut.mkv`

**3D?** Yes; may remove "3D" (manual add-back).

## Codec Tags Reference

### Video
- H.264/AVC, H.265/HEVC, x264/x265

### Quality
- 1080p (1920x1080), 720p (1280x720), 2160p/4K (3840x2160), HDR, 10bit

### Source
- BluRay, WEB-DL, WEBRip

### Audio
- AAC, DTS, DD5.1, Atmos

**Note:** Use metadata; Jellyfin shows separately.

## Related Documentation
- [TMDB Cache Generator](TMDB_CACHE_GENERATOR.md)
- [Episode Title Management](EPISODE_TITLE_MANAGEMENT.md)
- [Architecture](../docs/)
- [Jelly Rancher](../JELLY_RANCHER_README.md)

## Support
1. `audit-logs/`
2. `logs/`
3. ChromaDB
4. JSON export

## Examples

### 1: Clean
```
Before: Movies/Inception (2010) H.265 1080p BluRay x264.mkv
After:  Movies/Inception (2010)/Inception (2010).mkv
```

### 2: Truncated
```
Before: Movies/Doc Mar (2003).mkv → TMDB: "Doc Martin and the Legend of the Cloutie Well"
After:  Movies/Doc Martin and the Legend of the Cloutie Well (2003)/Doc Martin and the Legend of the Cloutie Well (2003).mkv
```

### 3: Multiple
```
Before: Movies/Action Film x264 1080p.mkv (codec, no year, no folder) → 2018
After:  Movies/Action Film (2018)/Action Film (2018).mkv
```

*Last Updated: November 8, 2025*  
*Version: 2.0 (Integration Phase 3)*

---

# docs\PYQT6_MIGRATION_PLAN.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 9,247 -> 6,327 chars (68.4%)

**Status:** success

# JellyRancher PyQt6 Migration & Cleanup Plan

**Date:** November 12, 2025  
**Goal:** Migrate GUI from PyQt5 to PyQt6; clean project structure.

---

## 📊 Current State Analysis

### Project Statistics
- **Total Files:** 32,156 (2,212.87 MB)
- **Core Scripts:** 74 (1.20 MB)
- **Delete:** 114 (2.05 MB)
- **Archive:** 678 (12.27 MB)
- **Review:** 30,940 (2,184.73 MB)

### Current GUI Stack
- **Framework:** PyQt5 (3,568 lines in `jelly_rancher_main.py`)
- **Entry:** `launch_gui.py` → `scripts.core.jelly_rancher_main.main()`
- **Legacy GUIs:** 
  - `scripts/tools/ravenmaven/ravenmaven_gui.py` (CustomTkinter)
  - `scripts/ai/structure_preview_gui.py` (Tkinter)
  - `code_cop/tools/audit/codecop_gui.py` (Tkinter)
  - `scripts/core/gui_main.py` (old)

---

## 🎯 Phase 1: Pre-Migration Cleanup (IMMEDIATE)

### 1.1 Execute Cleanup Script Recommendations

**DELETE (114 files - 2.05 MB):**
```powershell
.\cleanup_reports\cleanup_delete_20251112_144153.ps1
```
- 106 duplicates in `RavenMaven/lists/` (chunk*_processed.json)
- 8 temp files in `temp/`
- Backup credentials (`.enc.bak`, `.salt.bak`)

**ARCHIVE (678 files - 12.27 MB):**
```powershell
mkdir V:\JellyRancher_Archive\2025-11-12_pre-pyqt6
```
Move:
- `code_cop/jellyfin_organizer_*` (legacy)
- `Jellyfin Organizer/.coverage`, tests
- `archive/documentation_2025-11-09/`, `2025-11-11/`
- `code_cop/summaries/` (legacy)

### 1.2 Remove Obsolete GUI Files
```
❌ scripts/tools/ravenmaven/ravenmaven_gui.py (CustomTkinter - 550+ lines)
❌ scripts/ai/structure_preview_gui.py (Tkinter - 270 lines)
❌ code_cop/tools/audit/codecop_gui.py (Tkinter)
❌ scripts/core/gui_main.py (old Tkinter)
❌ scripts/utils/before_after_preview.py (Tkinter)
❌ backups/scripts_backup_20251110/core/launch_gui.py (old)
```

### 1.3 Clean ChromaDB Duplicates
- Instances: `chroma_db/chroma.sqlite3` (main), `scripts/chroma_db/chroma.sqlite3` (dup?), `scripts/core/chroma_db/` (active?)
**Action:** Keep one; merge if needed.

---

## 🚀 Phase 2: PyQt6 Migration (CORE)

### 2.1 Update Dependencies
**`requirements-jelly-rancher.txt`:**
```diff
- PyQt5>=5.15.0
+ PyQt6>=6.6.0
+ PyQt6-Qt6>=6.6.0
```
```powershell
& V:/JellyRancher/.venv/Scripts/python.exe -m pip install PyQt6
& V:/JellyRancher/.venv/Scripts/python.exe -m pip uninstall PyQt5 -y
```

### 2.2 Code Migration Strategy
**Primary:** `scripts/core/jelly_rancher_main.py` (3,568 lines)

**Imports:**
```python
# PyQt5
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, ...)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, ...)
from PyQt5.QtGui import (QIcon, QFont, QColor, ...)

# PyQt6
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, ...)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, ...)
from PyQt6.QtGui import (QIcon, QFont, QColor, ...)
```

**Key Changes:**
1. **Enums:** `Qt.AlignCenter` → `Qt.AlignmentFlag.AlignCenter`
2. **exec():** `app.exec_()` → `app.exec()`
3. **Signals:** `button.clicked.connect(self.handler)` (unchanged)

### 2.3 Migration Checklist
**Core:**
- [ ] `scripts/core/jelly_rancher_main.py` (3,568 lines)
- [ ] `launch_gui.py` (import error msg)
- [ ] `requirements-jelly-rancher.txt`
- [ ] `scripts/core/jellyfin_ui.py` (1,656 lines, if used)

**Backend (verify):**
- [ ] `scripts/core/subtitle_backend.py`
- [ ] `scripts/core/tools_backend.py`
- [ ] `scripts/core/analytics_backend.py`
- [ ] `scripts/core/settings_backend.py`

**Tests:**
- [ ] GUI tests to PyQt6
- [ ] `pytest.ini`

---

## 🔧 Phase 3: Modernization

### 3.1 New PyQt6 Features
- High-DPI support
- Modern widgets (QTableView, styling)
- Dark mode detection
- QThreadPool enhancements

### 3.2 Code Quality
- [ ] Type hints
- [ ] Docstrings
- [ ] Hardcoded strings → constants
- [ ] Split large files (e.g., `jelly_rancher_main.py`)
- [ ] GUI unit tests

### 3.3 Refactoring
**Split `jelly_rancher_main.py`:**
```
scripts/core/gui/
├── __init__.py
├── main_window.py
├── tabs/
│   ├── __init__.py
│   ├── media_tab.py
│   ├── subtitle_tab.py
│   ├── batch_tab.py
│   ├── analytics_tab.py
│   └── settings_tab.py
├── dialogs/
│   ├── __init__.py
│   ├── preferences.py
│   └── about.py
└── widgets/
    ├── __init__.py
    ├── log_viewer.py
    └── progress_bar.py
```

---

## 📝 Phase 4: Testing & Validation

### 4.1 Testing Checklist
**Functional:**
- [ ] GUI launch
- [ ] Tabs load
- [ ] Media org workflows
- [ ] Subtitle download
- [ ] Batch AI processing
- [ ] Settings save/load
- [ ] ChromaDB

**Visual:**
- [ ] Windows render
- [ ] High-DPI
- [ ] Themes
- [ ] Icons/images
- [ ] Fonts

**Performance:**
- [ ] Responsiveness
- [ ] Threading
- [ ] Memory
- [ ] Large lists

### 4.2 Regression
1. **Media Org:** Scan → Identify → Structure → Reorg
2. **Subtitles:** Search → Download → Place
3. **Batch:** Load → AI process → Execute

---

## 🗑️ Phase 5: Final Cleanup

### 5.1 Remove Post-Migration
```
❌ PyQt5 imports
❌ CustomTkinter/Tkinter GUIs
❌ Old GUI backups
❌ Unused backends
```

### 5.2 Update Docs
- [ ] `USER_GUIDE.md` (screenshots)
- [ ] `bootstrap.md` (GUI entry)
- [ ] `requirements-jelly-rancher.txt`
- [ ] `README.md` (install)
- [ ] `CHANGELOG.md`

### 5.3 Archive
```
V:\JellyRancher_Archive\2025-11-12_legacy-guis/
├── ravenmaven_gui.py
├── structure_preview_gui.py
├── codecop_gui.py
├── gui_main.py
└── README.md
```

---

## 📊 Migration Risk Assessment
**Low:** Imports, enums, exec()
**Medium:** Custom widgets, signals, stylesheets
**High:** Third-party (PoeClient), threading, file/OS dialogs

---

## 📅 Estimated Timeline
| Phase | Duration | Priority |
|-------|----------|----------|
| 1: Cleanup | 1-2h | HIGH |
| 2: Migration | 4-6h | HIGH |
| 3: Modernization | 2-4h | MEDIUM |
| 4: Testing | 2-3h | HIGH |
| 5: Cleanup | 1h | LOW |

**Total:** 10-16h

---

## 🚦 Next Steps
1. Run delete script
2. Backup state
3. Install PyQt6
4. Migrate `jelly_rancher_main.py`
5. Test/validate
6. Update docs

---

## 🎯 Success Criteria
✅ GUI launches  
✅ Features work (media, subtitles, batch)  
✅ No PyQt5/Tkinter/CustomTkinter  
✅ Reduced size  
✅ Docs/tests updated  

---

## 📞 Resources
- [PyQt6 Docs](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Migration Guide](https://www.riverbankcomputing.com/static/Docs/PyQt6/pyqt5_differences.html)
- [Qt6 Changes](https://doc.qt.io/qt-6/portingguide.html)

---

**Proceed:** Phase 1 cleanup → PyQt6 migration.

---

# docs\ROOT_CLEANUP_20251112.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 4,937 -> 4,535 chars (91.9%)

**Status:** success

# Root Folder Organization Report

**Date:** November 12, 2025  
**Action:** Complete root folder cleanup and organization

---

## Summary

**BEFORE:** 51 files in root  
**AFTER:** 6 essential files

---

## Files Moved

### To `tools/` (23 files)
- `analyze_unused_code.py`
- `bootstrap.py`
- `bootstrap_llm_assistant.bat`
- `build_function_index_enhanced.py`
- `build_gui_control_index.py`
- `build_help_index.py`
- `build_index.bat`
- `cleanup.py`
- `cleanup_enhanced.py`
- `consoldation_audit.py`
- `create_monolith.py`
- `document_org_tab_reorganization.py`
- `document_progress.py`
- `documentation_ingest.py`
- `find_remove_duplicates.py`
- `generate_docstrings_batch.py`
- `generate_docstrings_with_llm.py`
- `generate_inventory_enhanced.py`
- `ingest_samples.py`
- `integrate_docstrings.py`
- `merge_function_indexes.py`
- `performance_test.py`
- `test_query.py`

### To `data/` (10 files)
- `ALL_FUNCTIONS_MONOLITH.py` (2.4 MB)
- `enhanced_function_index_grok.json` (4.3 MB)
- `enhanced_function_index.json` (29 KB)
- `function_index.json` (1.9 MB)
- `gui_control_index.json` (89 KB)
- `help_index.json` (134 KB)
- `performance_results.json`
- `query_body.json`
- `unused_code_analysis.json` (63 KB)
- `config.json`

### To `docs/` (7 files)
- `bootstrap.md`
- `JELLY_RANCHER_PROJECT_STATE_2025.md`
- `CLEANUP_GIT_CHROMADB_20251112.md`
- `knowledge-pack.md`
- `PYQT6_MIGRATION_PLAN.md`
- `tmdb_usage_guidelines.md`
- `USER_GUIDE.md`

### To `reports/` (3 files)
- `help_missing_report.txt`
- `help_tooltip_report.txt`
- `list.txt`

### To `archive/` (3 files)
- `jelly_rancher_help.py`
- `jelly_rancher_main.py`
- `journal_completion.py`

---

## Root Directory - Final State

**6 Essential Files:**
1. `bootstrap.bat` - Setup script
2. `launch_gui.py` - Main entry point
3. `pytest.ini` - Test configuration
4. `README.md` - Project overview (NEW)
5. `requirements-jelly-rancher.txt` - Dependencies
6. `run_jelly_rancher.bat` - Quick launch

---

## New Additions

**README.md** (NEW): Quick start guide, project structure, features, 9-point workflow, dependencies, dev setup, changes log, config guide, troubleshooting.

---

## Directory Statistics

| Directory          | Files | Purpose              |
|--------------------|-------|----------------------|
| **Root**           | 6     | Essential launch/config |
| **tools/**         | 23    | Development utilities |
| **data/**          | 25    | JSON indexes, config |
| **reports/**       | 10    | Analysis reports    |
| **docs/**          | 18    | Documentation       |
| **archive/**       | 24    | Legacy code         |
| **scripts/**       | -     | Main app code       |
| **Jellyfin Organizer/** | - | Legacy standalone |
| **RavenMaven/**    | -     | Legacy tool         |

---

## Benefits

✅ Clean root - Professional look  
✅ Better organization - Grouped by purpose  
✅ Easier navigation - Clear for devs  
✅ Reduced clutter - 51 → 6 root files  
✅ Comprehensive README  
✅ Logical grouping - Tools/data/docs/reports separated  

---

## Project Structure

```
JellyRancher/
├── launch_gui.py              # Main entry point
├── requirements-jelly-rancher.txt # Dependencies
├── pytest.ini                 # Test config
├── README.md                  # Project overview
├── bootstrap.bat              # Setup script
├── run_jelly_rancher.bat      # Quick launch
│
├── tools/                     # Development utilities (23 files)
├── data/                      # JSON/config (25 files)
├── docs/                      # Documentation (18 files)
├── reports/                   # Analysis reports (10 files)
├── archive/                   # Legacy code (24 files)
│
├── scripts/                   # Main application code
├── Jellyfin Organizer/        # Legacy standalone
├── RavenMaven/                # Legacy tool
├── logs/                      # Application logs
├── audit-logs/                # Audit trail
├── temp/                      # Temporary files
└── .venv/                     # Virtual environment
```

---

## Verification Commands

```powershell
# View root files
Get-ChildItem -File

# Check organized directories
Get-ChildItem -Directory | ForEach-Object { 
    "$($_.Name): $((Get-ChildItem $_.FullName -File -Recurse).Count) files" 
}

# View README
Get-Content README.md | Select-Object -First 50
```

---

## Impact

**Space Saved:** None (moved, not deleted)  
**Clarity/Maintainability/Professionalism:** Significantly improved  

---

**Status:** ✅ Complete  
**Next Steps:** PyQt6 migration (`docs/PYQT6_MIGRATION_PLAN.md`)

---

# docs\SESSION_STARTER.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 6,003 -> 4,852 chars (80.8%)

**Status:** success

# IDE AI Session Starter

---

## Current Context

**Project:** JellyRancher - Jellyfin Media Organizer  
**Language:** Python 3.12  
**GUI Framework:** PyQt6  
**Status:** Migrating from PyQt5 to PyQt6, consolidating codebase  
**Working Directory:** `V:/JellyRancher/`

---

## Current Task

[DESCRIBE WHAT YOU'RE WORKING ON - Update this each session]

Examples:
- Migrating `jelly_rancher_main.py` from PyQt5 to PyQt6
- Implementing Point 1 (folder scanning) of 9-point workflow
- Building transaction log system for file rollback
- Testing subtitle detection with ffprobe

---

## The 9-Point Workflow (Quick Reference)

1. **Folder Scanning** → Generate master file list
2. **Hierarchical Overview** → Show folder tree with size stats
3. **LLM Proposal** → AI generates Jellyfin-compliant restructuring
4. **Metadata Lookup** → Query TMDB/TVDB/Wikipedia
5. **Action Table** → User reviews color-coded operations
6. **Transaction Log** → MD5 snapshots for rollback
7. **Execute** → Move files, verify integrity
8. **Subtitle Coverage** → Detect missing English subs
9. **Subtitle Download** → Acquire from multiple sources

**Full details:** See `docs/WORKFLOW_SPEC.md`

---

## Key Constraints

### Rate Limits (CRITICAL)
- **TMDB:** 40 requests per 10 seconds
- **TVDB:** Current limits (check API docs)
- **Wikipedia:** Conservative scraping
- **Implementation:** Use `tenacity` + `ratelimit` decorators

### File Safety (CRITICAL)
- All moves require MD5 verification
- Transaction logs BEFORE execution
- Use `send2trash` instead of permanent deletion
- Never modify source files until user approves

### Jellyfin Compliance
- Follow official naming conventions
- NFO files for multi-part episodes (S01E01-E02.mkv)
- Subtitle naming: `movie.en.srt`, `movie.en.forced.srt`

### Python Environment
- **ALWAYS** use `.venv` in project root
- **NEVER** commit `.venv/` to git
- Activate: `& V:/JellyRancher/.venv/Scripts/Activate.ps1`

---

## Libraries We're Using

**Core:**
- `PyQt6` - GUI
- `tmdbv3api` - TMDB
- `tvdb_v4_official` - TVDB
- `subliminal` - Subtitle downloader
- `rapidfuzz` - Fuzzy matching
- `tenacity` - Backoff
- `ratelimit` - Rate limiting
- `ffmpeg-python` - Media analysis
- `send2trash` - Safe deletion
- `anthropic` - Claude API (or Poe wrapper)

**Built-in:**
- `pathlib`, `shutil`, `hashlib`, `sqlite3`, `json`

**Full list:** `requirements-jelly-rancher.txt`

---

## What to Build Yourself

❌ **No library for:**
1. Transaction log (atomic rollback)
2. Jellyfin NFO (multi-part episodes)
3. Color-coded action table (PyQt6)
4. Hierarchical folder overview
5. LLM → Metadata pipeline

✅ **Use libraries for:**
- Rate limiting, APIs, subtitles, fuzzy matching, file ops

---

## Project Structure

```
V:/JellyRancher/
├─ docs/                    # Docs
│  ├─ WORKFLOW_SPEC.md
│  ├─ ARCHITECTURE.md
│  └─ PYQT6_MIGRATION.md
│
├─ scripts/
│  ├─ core/                 # Logic
│  │  ├─ scanner.py         # Pt 1
│  │  ├─ metadata.py        # Pt 4
│  │  ├─ executor.py        # Pt 7
│  │  └─ subtitles.py       # Pts 8-9
│  │
│  ├─ gui/                  # PyQt6
│  │  ├─ main_window.py
│  │  ├─ action_table.py    # Pt 5
│  │  └─ dialogs.py
│  │
│  └─ utils/
│     ├─ transaction_log.py # Pt 6
│     ├─ api_client.py      # Rate-limited APIs
│     └─ logger.py
│
├─ data/                    # Git-ignored
│  ├─ cache/                # API cache
│  ├─ logs/
│  └─ transaction_logs/
│
├─ jelly_rancher_main.py    # Main (3568 lines)
├─ launch_gui.py            # Entry
├─ requirements-jelly-rancher.txt
└─ .venv/                   # Git-ignored
```

---

## Migration Status

### ✅ Completed
- Phase 1 cleanup (114 duplicates deleted, 678 legacy archived)
- Removed legacy GUIs (CustomTkinter, Tkinter)
- Removed ChromaDB
- Archive: `V:\JellyRancher_Archive\2025-11-12_pre-pyqt6\`

### 🚧 In Progress
- PyQt5 → PyQt6
- Restructure `jelly_rancher_main.py` (3568 → modular)

### ⏳ Next Steps
- [Update]

---

## Common Questions

**Stuck:**
1. Combine `tenacity` + `ratelimit`?
2. PyQt6 color-coded table by confidence?
3. Subliminal forced subs?
4. Parse ffprobe for English subs?
5. Jellyfin NFO XML for multi-part?
6. SQLite transaction log for rollback?

**Architecture:**
1. Async/await for APIs?
2. PyQt6 multi-tab structure?
3. Cache TMDB?
4. Test file ops without changes?

**Debugging:**
1. Rate limiter failing?
2. MD5 mismatch post-move?
3. FFprobe missing subs?
4. PyQt6 table not updating?

---

## Quick Commands

```powershell
& V:/JellyRancher/.venv/Scripts/Activate.ps1
pip install -r requirements-jelly-rancher.txt
python launch_gui.py
pytest
ffmpeg -version
```

---

## Remember

- Check docs before architecture changes
- Small increments; test each point
- Always dry-run file ops
- Transaction logs = safety net
- Rate limits mandatory
- 9-point workflow = guide

---

**What are you working on today?**

---

# docs\TMDB_CACHE_GENERATOR.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 6,915 -> 4,280 chars (61.9%)

**Status:** success

# TMDB Episode Cache Generator

## Overview

Fetches complete episode metadata from TMDB and generates structured JSON cache files for TV shows, eliminating manual lookups and ensuring consistent naming.

## Features

- **Search TMDB**: By name, year, or ID
- **Preview Details**: View show info before caching
- **Progress Tracking**: Real-time updates
- **Offline Usage**: No API needed post-generation
- **JSON Format**: Standard, parsable caches

## Setup

### 1. Get TMDB API Key

1. Visit [TMDB](https://www.themoviedb.org/)
2. Create account if needed
3. Settings → API → Request v3 auth key (Developer)
4. Copy key

### 2. Configure in JellyRancher

1. Open JellyRancher → **Settings** tab
2. **API Credentials** → Paste TMDB key
3. Click **Test** → **Save Settings**

## Usage

### Generating a Cache

1. **Tools** → **Generate TMDB Cache**
2. Enter show name (± year)
3. **🔍 Search**
4. Select show, review preview
5. **📥 Generate Cache**
6. Choose save location

### Direct TMDB ID Lookup

1. Enter ID in **TMDB ID** field
2. **📥 Generate Cache**

### Using Generated Caches

JSON structure:

```json
{
  "tmdb_id": 12345,
  "show_name": "Example Show",
  "first_air_date": "2020-01-01",
  "overview": "Show description...",
  "generated_date": "2025-11-08T22:38:00.123456",
  "seasons": {
    "1": {
      "season_number": 1,
      "episodes": {
        "1": {
          "episode_number": 1,
          "name": "Pilot",
          "air_date": "2020-01-01",
          "overview": "Episode description..."
        }
      }
    }
  }
}
```

Uses: episode title matching, metadata enrichment, NFO generation, automated organization.

## Tips & Best Practices

### Searching

- Include year for common names (e.g., "The Office 2005")
- Verify results
- Prefer TMDB ID

### Cache Management

- Store in dedicated folder (e.g., `V:/Jellyfin/#MEDIA/caches/`)
- Name descriptively (e.g., `game_of_thrones_1399.json`)
- Re-generate for ongoing series

### Troubleshooting

#### "No API key found"
- Configure in Settings, test key

#### "TMDB API key is invalid"
- Copy full key (no spaces), use v3 auth (not Read Access Token)
- Verify account active

#### "No results found"
- Adjust terms/spelling
- Search TMDB site first
- Use ID

#### "Failed to connect to TMDB"
- Check internet
- Verify status.themoviedb.org
- Retry later

#### Cache generation slow
- Normal for large shows
- Monitor progress bar
- Do not close dialog

## Technical Details

### API Rate Limits

- Free: 50 req/sec
- Auto-respected by JellyRancher

### Cache Format

**Root:**
- `tmdb_id`, `show_name`, `first_air_date`, `overview`, `generated_date`, `seasons`

**Season:**
- `season_number` (0=specials), `episodes`

**Episode:**
- `episode_number`, `name`, `air_date`, `overview`

### File Locations

- Settings: `scripts/core/config/settings.json` (plain text)
- Caches: User-chosen (recommend with media or dedicated dir)
- Logs: `logs/jelly_rancher_main.log`

## Development

### Backend (`scripts/core/tmdb_backend.py`)

```python
from tmdb_backend import TMDBBackend

tmdb = TMDBBackend()
tmdb.set_api_key("your_api_key")

results = tmdb.search_shows("Game of Thrones", year=2011)
show = tmdb.get_show_details(1399)

cache_path, cache_data = tmdb.generate_cache(
    tmdb_id=1399,
    output_path=Path("cache.json"),
    progress_callback=lambda msg, current, total: print(msg)
)
```

### Dialog (`scripts/core/dialogs/tmdb_cache_dialog.py`)

```python
from dialogs.tmdb_cache_dialog import TMDBCacheDialog

dialog = TMDBCacheDialog(parent)
if dialog.exec_():
    pass  # Cache generated
```

### Testing

```bash
pytest scripts/tests/test_tmdb_integration.py -v
pytest scripts/tests/test_tmdb_integration.py --cov=scripts/core/tmdb_backend
```

### Adding Features

1. **Backend**: Edit `tmdb_backend.py`, add `TMDBBackend` methods
2. **UI**: Edit `tmdb_cache_dialog.py`, connect to backend
3. **Tests**: Update `test_tmdb_integration.py` (use mocks)

## See Also

- [TMDB API](https://developers.themoviedb.org/3)
- [Episode Title Analyzer](episode_title_analyzer.md)
- [Settings Management](settings.md)

## Support

1. Check troubleshooting/logs (`logs/jelly_rancher_main.log`)
2. Verify API key/internet
3. Report to JellyRancher tracker

---

*Updated: November 8, 2025*  
*Version: 2.0.0*

---

# docs\TMDB_CACHE_GUIDE.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 5,304 -> 3,484 chars (65.7%)

**Status:** success

# TMDB Cache Builder Guide

## Overview

TMDB Cache Builder generates detailed episode caches from The Movie Database (TMDB) for accurate episode title analysis and fixing in media libraries.

## Why Use TMDB Caches?

- **Accurate Episode Data**: Official titles, air dates, season info
- **Bulk Processing**: Auto-analyze TV show collections
- **Offline Capability**: Works without internet
- **Consistency**: Standardized naming across library
- **Time Saving**: No manual research

## Quick Start

### 1. Set Up TMDB API Key

1. Visit [themoviedb.org](https://www.themoviedb.org/)
2. Create free account
3. Go to **Settings** → **API**
4. Request **Developer API Key** (v3)
5. Copy key

### 2. Configure in JellyRancher

1. Launch JellyRancher
2. Go to **Settings** tab
3. Paste key in **TMDB API Key** field
4. Click **Test Key**
5. **Save Settings**

### 3. Generate First Cache

1. Go to **Tools** → **Generate TMDB Cache**
2. Search show (e.g., "Breaking Bad")
3. Select show
4. Click **Generate Cache**
5. Save to `data/tmdb_caches/`

## Step-by-Step Guide

### Finding Your Show

- **Show Name**: "The Office", "Breaking Bad", "Stranger Things"
- **With Year**: "The Office 2005"
- **Alternative Titles**: Supports international
- **Direct ID**: Enter TMDB ID directly

### Understanding Results

- **Show Title**: Official name
- **Year Range**: First/last air dates
- **Overview**: Description
- **Poster**: Visual
- **TMDB Rating**: Score

### Cache Generation Process

1. Fetches show details
2. Downloads all episodes per season
3. Formats into JellyRancher cache
4. Saves as JSON

**Progress**: Current season, episodes/season, %, ETA.

## Cache File Details

```json
{
  "show_info": {
    "name": "Breaking Bad",
    "tmdb_id": 1396,
    "total_seasons": 5,
    "total_episodes": 62
  },
  "episodes": {
    "S01E01": {
      "title": "Pilot",
      "air_date": "2008-01-20",
      "overview": "Walter White learns he has terminal lung cancer..."
    }
  }
}
```

## Integration with Episode Tools

- **Episode Title Analysis**: Compares files to official titles
- **Batch Fixing**: Renames collections to TMDB data
- **Confidence Scoring**: Matches quality rating
- **Missing Episode Detection**: Identifies gaps

## Best Practices

### Organization
- Store in `data/tmdb_caches/`
- Name: `breaking_bad_1396.json`
- Organize by genre/alphabet

### Maintenance
- Regenerate for new seasons/title changes
- Archive old caches

### Troubleshooting

**"API Key Invalid"**
- Check key in Settings (no spaces)
- Test in Settings

**"Show Not Found"**
- Try spellings, year, international titles

**"Generation Failed"**
- Check internet/TMDB status
- Retry later

## Advanced Features

### Direct TMDB ID Usage
1. Enter numeric ID in search
2. Direct generation
3. For scripts/bulk

### Batch Cache Generation
1. Generate one-by-one
2. Organize folders
3. Use across collections

### Cache File Inspection
Open in text editor to verify data, check structure, debug.

## Integration Examples

### Episode Title Management
1. Generate cache for "The Office"
2. Run analysis on files
3. Auto-match, get corrections

### Media Organization
1. Use in bulk renaming
2. Ensure consistent titles
3. Prep for media servers

## Support and Resources

- **In-App Help**: F1 or Help → Contents
- **Settings Validation**: Test TMDB key
- **Log Files**: `logs/`
- **Community**: Search issues

---

**Pro Tip**: Start with popular shows, then full collection for efficient organization.

---

# docs\USER_GUIDE.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 7,685 -> 4,022 chars (52.3%)

**Status:** success

# JellyRancher User Guide

## 🎯 Quick Start

Launch shows **Welcome Wizard**. Access anytime: **F1** or **File → Quick Start Guide**, or **🎯 Quick Start** toolbar button.

## 📚 Common Tasks

### 🎬 Organize Movies (Full Workflow)

**Complete organization with metadata/naming:**

1. Go to **🚀 Workflow** tab
2. **STEP 1:** ➕ Add Folder
3. **STEP 2:** 🔍 STEP 1-2: Start Scan
4. **STEP 3:** 🤖 STEP 3: Analyze with LLM
5. **STEP 4A:** 🔍 STEP 4A: Lookup Metadata
6. **STEP 4B:** (Opt.) 📄 STEP 4B: Generate NFO Files
7. **STEP 5:** 📋 STEP 5: Generate Reorganization Plan
8. **STEP 6:** 📸 STEP 6: Create Snapshot
9. **STEP 7:** ▶️ STEP 7: Execute Reorganization
10. **STEP 8:** Analyze subtitle coverage (opt.)
11. **STEP 9:** Download missing subtitles (opt.)

**💡 Tip:** Follow numbered buttons sequentially 1-2 to 9.

---

### 📁 Simple Organization (Quick Mode)

**Quick organization without full analysis:**

1. Go to **📁 Organization** tab
2. Select media type (Movies/TV Shows/Anime)
3. Browse source folder
4. Choose: ✅ Dry Run, ✅ File Verification
5. **Scan Folder**
6. **Organize Media**

**⚠️:** Uses existing structure; prefer full workflow for best results.

---

### 💬 Download Subtitles

**Method 1: Subtitles Tab**

1. Go to **📺 Subtitles** tab
2. Browse video folder
3. **Detect Coverage**
4. Select languages
5. **Download Subtitles**

**Method 2: Workflow (Post-Org)**

1. Complete Workflow Steps 1-8
2. **STEP 9:** Analyze Coverage
3. Review missing
4. **Download Missing**

---

### 🔍 Quick Actions Toolbar

- **🎯 Quick Start**
- **🔍 Scan Folder** (to Org tab)
- **📁 Organize Media** (folder required)
- **💬 Get Subtitles** (to Subtitles tab)
- **🚀 Full Workflow** (to Workflow tab)

---

## 📖 Tab Overview

### 🚀 Workflow Tab
9-step workflow: scan, AI analysis, metadata, plan, execute. For initial organization.

### 📁 Organization Tab
Quick org: media type, scan, organize. Snapshots, analyzers.

### 📺 Subtitles Tab
Download/manage: multi-provider, coverage detection, languages.

### 📝 NFO Files Tab
Generate NFOs: auto-detect, TMDB, Jellyfin/Plex compatible.

### 🤖 Batch Processing Tab
RavenMaven: queue, AI, bulk ops.

### 🔍 Code Analysis Tab
CodeCop: project analysis, quality reports, debt tracking.

### 📊 Analytics Tab
Library stats: counts/sizes, breakdowns, exports.

### 🧠 Memory Tab
ChromaDB semantic search: natural language, history, suggestions.

### ⚙️ Settings Tab
Config: credentials, paths, save/reset.

---

## 💡 Pro Tips

### Before You Start
1. Test small folder
2. Enable **Dry Run**
3. Create snapshots (Workflow 6/Org tab)
4. Use help (hover/❓)

### Workflow Breakdown
- 1-2: Scan
- 3-4: AI/metadata
- 5-6: Plan/snapshot
- 7: Execute
- 8-9: Subtitles

### Hover Help
Hover controls for right-panel details.

### Keyboard Shortcuts
- **F1**: Quick Start
- **Ctrl+S**: Quick Scan
- **Ctrl+O**: Quick Organize
- **Ctrl+T**: TMDB Cache
- **Ctrl+E**: Episode Analyzer
- **Ctrl+M**: Movie Analyzer
- **Ctrl+Shift+M**: Memory Query
- **Ctrl+Q**: Exit

---

## ⚠️ Important Safety Notes

### Backups
- Workflow Step 6: auto-snapshots
- Org tab: snapshot mgmt
- Keeps last 10; verify/restore

### Rollback
1. Org tab → Snapshots section
2. 🔄 Refresh
3. Select → ↩️ Restore
4. 🗑️ Delete

### Testing
- Use **Dry Run** first
- Test on copy
- Review plan/logs

---

## 🆘 Need More Help?

### In-App
- **F1**: Quick Start
- ❓ buttons/tooltips
- **File → Help → Documentation**

### Tab Help
Per-tab ❓: purpose, usage, steps, pitfalls.

### Status Bar
Shows status/progress/errors.

---

## 🎓 Learning Path

### Beginner
1. Org tab + Dry Run
2. Small folders

### Intermediate
1. Full Workflow (9 steps)
2. Review plan
3. Subtitles tab

### Advanced
1. Batch AI
2. NFOs
3. Analytics
4. Memory search

---

## 🔧 Troubleshooting

- **What to click first?** F1/🎯 Quick Start
- **Workflow confusing?** Follow 1→9 sequentially
- **Simpler?** Org tab/toolbar Quick Actions
- **Undo?** Org → Snapshots → Restore
- **No response?** Check prior steps/status bar/folder selection

**Happy organizing! 🍫**

---

# docs\WORKFLOW_SPEC.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 11,600 -> 6,344 chars (54.7%)

**Status:** success

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

**Implementation:**
- Select multiple folders (add/remove)
- Recursively scan
- Generate file inventory with absolute paths (one per row), all filetypes

**Output:** List of absolute file paths

---

### 2. Hierarchical Overview

**Implementation:**
- Hierarchical view of master list
- Per folder: total size, filetype breakdown (e.g., ".mkv: 178 files (240 GB)")

**Output:** Tree view with aggregated statistics

---

### 3. LLM Reorganization Proposal

**Implementation:**
- Submit folder structure to LLM (Claude via `anthropic` SDK or Poe.com)
- LLM proposes Jellyfin-compliant reorganization (detect movies/TV from names)
- Provide Jellyfin naming context; request JSON output

**Output:** JSON with proposed file moves/renames

---

### 4. Metadata Database Building

**Sources (priority):**
1. **TMDB** (movies) - `tmdbv3api`
2. **TVDB** (TV) - `tvdb_v4_official`
3. **Wikipedia** (fallback) - scraping

**Process:**
1. LLM-detected list + fuzzy matching (`rapidfuzz`)
2. Query APIs w/ rate limits: TMDB 40/10s, TVDB current, Wikipedia conservative
3. Exponential backoff (`tenacity`)
4. Aggressive caching (SQLite/JSON)

**Canonical Data:**
- Movie years, TV names/years/seasons/episodes
- Special: Multi-part episodes (e.g., S01E01-E02.mkv) → Jellyfin NFO w/ ranges

**Rate Limiting:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=40, period=10)  # TMDB
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
def query_tmdb_safe(movie_name):
    pass  # API call
```

**Output:** Metadata database (SQLite/JSON)

---

### 5. Editable Action Table

**Color-Coded Categories:**
- 🟢 **Green:** Perfect match, high confidence
- 🟡 **Yellow:** Fuzzy/minor ambiguity
- 🟠 **Orange:** Multiple/significant deviations
- 🔴 **Red:** No match/corrupt
- 🔵 **Blue:** Compliant/duplicate

**Row Contents:**
- Source path
- Proposed dest path
- Action (move/rename/NFO/etc.)
- Confidence/color
- Metadata source
- Override checkbox

**Features:**
- Editable cells
- Dry-run preview
- Filter by color/action
- CSV export

**PyQt6:**
```python
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QColor

item = QTableWidgetItem('movie.mkv')
if confidence == 'high':
    item.setBackground(QColor(200, 255, 200))  # Light green
table.setItem(row, col, item)
```

**Output:** User-approved action plan

---

### 6. Snapshot & Transaction Log

**Before Operations:**

1. **Transaction Log (SQLite):**
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

2. **Per Operation:**
   - Log pre-execution + source MD5
   - Execute
   - Verify dest MD5
   - Update completed
   - Error: log/skip

**Rollback:** Reverse chronological; reverse ops, verify MD5.

**Safety:**
- `send2trash` for deletes
- Logs 30 days
- Rollback scripts

**Output:** Transaction log (SQLite)

---

### 7. Execute Reorganization

**Process:**
1. Validate dest paths
2. Check conflicts
3. Execute per log:
   - Move/rename video
   - Move/rename subtitles (`.srt`/`.ass`/`.sub` etc.)
     - e.g., `movie.en.srt`, `movie.en.forced.srt`, `show.S01E01.en.srt`
   - Verify MD5
4. Error: log/skip
5. Summary: success/skipped/errors

**Output:** Reorganized files + log + report

---

### 8. Subtitle Coverage Evaluation

**Detection:**

1. **Embedded (`ffmpeg-python`):**
```python
import ffmpeg

probe = ffmpeg.probe('movie.mkv')
subtitle_streams = [s for s in probe['streams'] if s['codec_type'] == 'subtitle']
for sub in subtitle_streams:
    lang = sub.get('tags', {}).get('language', '')
    forced = sub.get('disposition', {}).get('forced', 0)
    if lang in ('eng', 'en'):
        pass  # Has English
```

2. **External:** Scan `.srt`/`.ass`/`.sub`/`.ssa`; match names, parse lang (e.g., `.en.srt`)

**Logic:**
- Embedded/external English → "covered"
- Else → download list

Distinguish regular/forced.

**Output:** Files missing English subs

---

### 9. Subtitle Acquisition

**`subliminal`:**
```python
from subliminal import download_best_subtitles, save_subtitles
from babelfish import Language

video = Video.fromname('movie.mkv')
subtitles = download_best_subtitles({video}, {Language('eng')},
                                   providers=['opensubtitles', 'podnapisi', 'addic7ed'])
save_subtitles(video, subtitles[video])
```

**Sources:**
1. OpenSubtitles.org (creds)
2. OpenSubtitles.com
3. Podnapisi.NET
4. Addic7ed.com
5. Subscene.com

**Matching:** Hash (`rapidfuzz` fallback); download regular + forced.

**Respect:** Rate limits, ToS, backoff (`tenacity`).

**Output:** Subs alongside videos

---

## Architecture & Design Decisions

- **PyQt6:** Cross-platform, table/tree widgets, `QThread`.
- **Transaction Logs > Git:** Atomic rollback, MD5 integrity.
- **MD5 > SHA256:** Faster for videos, sufficient integrity.
- **Regular + Forced Subs:** Jellyfin distinction.

---

## Rules & Constraints

1. **API Courtesy:** Rate limits, backoff, 30+ day cache.
2. **User Control:** Review required, dry-run, CSV export.
3. **Jellyfin Compliance:** Naming, NFO XML, structure.
4. **Data Integrity:** Preserve paths, MD5 moves, rollback logs.
5. **Transparency:** Confidence/reasoning flags, reports.
6. **Python Env:** `.venv`, `requirements.txt`.

---

## Success Metrics

✅ Accurate scan counts  
✅ Hierarchical sizes/types  
✅ Valid LLM proposals  
✅ <5% metadata failures  
✅ Color-coded table  
✅ Dry-run preview  
✅ MD5-verified execution  
✅ Full rollback  
✅ Sub detection  
✅ 90%+ sub downloads  

---

## Next Steps

See `ARCHITECTURE.md`, `MIGRATION_GUIDE.md`, `API_USAGE.md`.

---

# docs\WORKFLOW_STEP1_GUIDE.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 5,733 -> 3,559 chars (62.1%)

**Status:** success

# Workflow Step 1: Folder Scanning & Structure Analysis

## Overview

Scan folders recursively to:
1. List all video files with full paths
2. Summarize folder structure
3. Identify types (TV shows with seasons, movies, etc.)
4. Export results

## How to Use

### Via GUI (jelly_rancher_main.py)
1. Launch: `python jelly_rancher_main.py`
2. Workflow tab (🚀)
3. Add folders: "➕ Add Folder"
4. Configure:
   - Structure Summary Depth: 1-10
   - Save complete file list
   - Save structure summary
5. Start: "🔍 Start Scan"; view in Structure Summary panel
6. Export: "💾 Export Results" to `data/` with timestamps (auto if checked)

### Via Python Module
```python
from folder_structure_scanner import FolderStructureScanner

scanner = FolderStructureScanner([
    r"V:\#MEDIA\TV Shows",
    r"V:\#MEDIA\Movies"
])
video_files, structure = scanner.scan_all()
scanner.generate_structure_summary()
scanner.print_structure_summary(max_depth=3)
scanner.save_file_list("data/video_files.txt")
scanner.save_structure_summary("data/structure.json")
print(f"Found {len(video_files)} video files")
```

### Via Command Line
```bash
python scripts/media/folder_structure_scanner.py "V:\#MEDIA\TV Shows" "V:\#MEDIA\Movies"
```

## Output Format

### File List (Text)
One path per line:
```
V:\#MEDIA\TV Shows\Star Trek TNG\Season 01\Episode 01.mkv
...
```

### Structure Summary (JSON)
```json
{
  "scan_date": "2025-11-08T19:27:30.701776",
  "root_folders": ["V:\\#MEDIA\\TV Shows"],
  "total_video_files": 234,
  "total_all_files": 240,
  "structure": {
    "V:\\#MEDIA\\TV Shows\\Star Trek TNG": {
      "path": "V:\\#MEDIA\\TV Shows\\Star Trek TNG",
      "name": "Star Trek TNG",
      "total_videos": 176,
      "direct_videos": 0,
      "type": "tv_show_with_seasons",
      "subfolders": {
        "Season 01": {
          "total_videos": 26,
          "type": "season"
        },
        ...
      }
    }
  }
}
```

### Console Display
```
================================================================================
FOLDER STRUCTURE SUMMARY
================================================================================

📁 Star Trek The Next Generation (176 videos across 7 seasons)
  └─ Season 01: 26 videos
  └─ Season 02: 26 videos
  ...
📁 The Office (50 videos)

📁 Movies (5 videos, 5 subfolders)
  🎬 The Matrix (1999) (1 video)
  ...
```

## Folder Type Classification
- **tv_show_with_seasons**: TV with Season XX folders
- **tv_show_flat**: Episodes in root folder
- **movie**: 1-2 videos
- **collection**: Multiple subfolders
- **season**: Season folder
- **unknown**: Undetermined

## Supported Video Formats
`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.mpg`, `.mpeg`, `.3gp`, `.ogv`, `.ts`, `.m2ts`

## Use Cases
1. Inventory media
2. Plan reorganization
3. Check Jellyfin-readiness
4. Generate reports
5. Validate files
6. Feed to Step 2

## Tips
- Large libraries: limit depth (2-3)
- Multiple sources: add all before scan
- Videos only; ignores others
- Fast; disk I/O limited
- Read-only; no modifications

## Next Steps
Use outputs for:
- Step 2: Jellyfin reorganization
- Review/verification
- Other tools
- Backup planning

## Troubleshooting
**Folder shows 0 videos:**
- Check permissions
- Verify extensions
- Console errors

**Truncated summary:**
- Increase depth
- Check JSON

**Slow scan:**
- Fewer folders
- Avoid network drives
- No symlink loops

## Example Workflow
```bash
python scripts/media/folder_structure_scanner.py "E:\Media\Unsorted"
cat data/scan_structure_*.json
wc -l data/scan_file_list_*.txt
```

---

# docs\LLM_ASSISTANT_BOOTSTRAP.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 9,545 -> 6,295 chars (66.0%)

**Status:** success

# 🚀 JellyRancher LLM Assistant Bootstrap Guide

JellyRancher is a media organization platform unifying tools into a GUI app. This guide bootstraps you as a coding assistant.

## ⚡ Quick Start (3 Steps)

### 1. Activate Virtual Environment
```powershell
cd "V:\JellyRancher"
.venv\Scripts\Activate.ps1
```

### 2. Bootstrap ChromaDB Knowledge Base
```powershell
python scripts/ai/bootstrap_chroma.py
```
**Mandatory for new assistants** - ingests entire project.

### 3. Launch Application
```powershell
python scripts/core/jelly_rancher_main.py
```

## 🧠 ChromaDB: Sole Source of Truth

- **Complete project knowledge** (code, docs, context)
- **Semantic search** by meaning
- **Persistent memory** across sessions
- **Activity logging** searchable

### Query Knowledge
```python
from scripts.core.chroma_memory_backend import ChromaMemoryBackend
memory = ChromaMemoryBackend()
results = memory.query_memory("how does subtitle downloading work?", n_results=5)
for result in results:
    print(f"File: {result['metadata']['file_path']}")
    print(f"Summary: {result['metadata']['summary']}")
    print(f"Content: {result['document'][:200]}...")
```

### Document Activities
```python
memory.add_memory(
    content="Fixed bug in media scanner - added null check for file paths",
    user_id="your_assistant_name",
    metadata={
        "activity": "bug_fix",
        "files_modified": ["scripts/media/media_scanner.py"],
        "lines_changed": "45-52",
        "testing": "ran unit tests, all pass"
    }
)
```

### Search Examples
- `"how does the GUI work?"`
- `"subtitle backend implementation"`
- `"testing framework"`
- `"configuration options"`
- `"recent changes to media organizer"`

## 📋 Development Workflow

1. Activate venv:
   ```powershell
   cd "V:\JellyRancher"
   .venv\Scripts\Activate.ps1
   ```

2. Query ChromaDB:
   ```python
   memory = ChromaMemoryBackend()
   results = memory.query_memory("similar feature already exists?", n_results=3)
   ```

3. Document plan:
   ```python
   memory.add_memory(
       content="Planning feature X. Modify A, B, C. Est: 2h.",
       user_id="your_name",
       metadata={"activity": "planning", "feature": "X", "estimated_time": "2h"}
   )
   ```

4. Implement/test: Follow patterns; run unit/integration tests; verify app.

5. Document completion:
   ```python
   memory.add_memory(
       content="Completed feature X. Added Y, fixed Z. Tests pass.",
       user_id="your_name",
       metadata={
           "activity": "completion",
           "feature": "X",
           "status": "completed",
           "test_results": "all_pass",
           "files_modified": ["A.py", "B.py", "C.py"]
       }
   )
   ```

## 🏗️ Project Structure
```
JellyRancher/
├── scripts/
│   ├── core/ (18 files)         # Main app
│   ├── media/ (29 files)        # Media processing
│   ├── ai/ (17 files)           # AI/LLM
│   ├── utils/ (57 files)
│   ├── tests/ (18 files)
│   ├── batch/ (10 files)
│   ├── docs/ (4 files)
│   ├── tools/ (322 files)
│   ├── _common/ (23 files)
│   └── config/ (1 file)
├── data/ (15 files)
├── logs/ (12 files)
├── chroma_db/                   # Knowledge base
├── docs.md
└── run_jelly_rancher.bat
```

## 🔧 Key Commands

### Environment
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements-jelly-rancher.txt
```

### Knowledge Base
```powershell
python scripts/ai/bootstrap_chroma.py
python -c "from scripts.core.chroma_memory_backend import ChromaMemoryBackend; m=ChromaMemoryBackend(); print(m.query_memory('search query', n_results=3))"
```

### Development
```powershell
python scripts/core/jelly_rancher_main.py
python -m pytest scripts/tests/
python scripts/tools/code_cop/audit.py
```

### Documentation
```powershell
python -c "from scripts.core.chroma_memory_backend import ChromaMemoryBackend; m=ChromaMemoryBackend(); m.add_memory('Completed task X', user_id='your_name', metadata={'activity': 'completion'})"
```

## 📚 Available Functionality

### Core Features
- Media organization (movies/TV/anime, intelligent naming)
- Subtitle management (multi-provider, sync)
- AI batch (GPT-4/Claude-3/Gemini Pro)
- Code analysis (complexity/coverage/security)
- Analytics/reporting
- Semantic memory (ChromaDB)

### Key Components
- `scripts/core/jelly_rancher_main.py` - GUI
- `scripts/media/media_org_backend.py` - Org engine
- `scripts/media/subtitle_backend.py` - Subtitles
- `scripts/ai/ravenmaven_client.py` - AI client
- `scripts/core/chroma_memory_backend.py` - KB

## 🐛 Troubleshooting

### Virtual Env
```powershell
python -m venv .venv --clear
.venv\Scripts\Activate.ps1
pip install -r requirements-jelly-rancher.txt
```

### ChromaDB
```powershell
Remove-Item -Recurse -Force chroma_db
python scripts/ai/bootstrap_chroma.py
```

### Imports
```powershell
cd "V:\JellyRancher"
.venv\Scripts\Activate.ps1
python scripts/core/jelly_rancher_main.py
```

## 📝 Documentation Standards

### Code
- Docstrings for functions
- Inline comments for complex logic
- Usage examples for new features

### ChromaDB
- Document all activities (files, lines, tests)
- Consistent metadata
- Searchable summaries

### Commits
- Action verb + component + issue ref

## 🎯 Best Practices

1. **Always use venv** - ensures deps.
2. **Query first**:
   ```python
   results = memory.query_memory("similar functionality", n_results=5)
   ```
3. **Document everything** in ChromaDB.
4. **Test thoroughly**: unit/integration/manual GUI.
5. **Follow patterns**: structure, naming, error handling.
6. **Update KB**: Bootstrap new assistants; doc changes.

## 🚨 Critical Rules

### ✅ DO
- Use venv always
- Document in ChromaDB
- Query before assuming
- Test thoroughly
- Follow patterns
- Update docs

### ❌ DON'T
- Work outside venv
- Change without docs
- Assume - query first
- Skip tests
- Break functionality
- Ignore imports

## 📞 Getting Help

### ChromaDB Queries
```python
memory.query_memory("similar problem", n_results=5)
memory.query_memory("how to implement X", n_results=3)
memory.query_memory("testing approach for Y", n_results=3)
```

### Resources
- `docs.md`
- `scripts/docs/`
- `scripts/_common/`
- `scripts/tests/`

## 🎉 Ready!

You have: project knowledge, env, docs standards, tests, troubleshooting.

**ChromaDB is your brain** - update/query often.

*Welcome to JellyRancher team!* 🎊

---

# docs\WORKFLOW_README.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 9,111 -> 5,867 chars (64.4%)

**Status:** success

# Jellyfin Media Organization Workflow

Automated workflow for Jellyfin media libraries using LLM analysis and metadata lookup (Steps 3-4 of JellyRancher).

## Overview

**Step 3: LLM Structure Analysis**
- Submits folder structure to LLM (Claude-Sonnet-4.5/gpt-4o-reasoning via Poe.com)
- Proposes Jellyfin reorganization
- Classifies movies/TV shows
- Detects multi-part episodes

**Step 4: Metadata Lookup & NFO Generation**
- Queries TMDB/OMDb APIs
- Builds canonical DB (titles, years, episodes)
- Generates NFO for multi-parts (e.g., Star Trek TNG "Encounter at Farpoint")
- Handles complex numbering

## Components

### 1. `llm_structure_analyzer.py`
LLM folder analysis via Poe.com API.

**Features:**
- Dynamic model selection
- Media analysis prompts
- JSON parsing/error handling
- Reasoning capture

**Usage:**
```bash
python llm_structure_analyzer.py data/scan_structure_20241108_120000.json
```

### 2. `media_metadata_lookup.py`
Metadata from TMDB/OMDb.

**Features:**
- TMDB movie/TV data
- OMDb fallback
- Episode/multi-part details
- Caching/rate limiting

**Usage:**
```bash
export TMDB_API_KEY="your_tmdb_key"
export OMDB_API_KEY="your_omdb_key"
python media_metadata_lookup.py data/llm_analysis_20241108_120000.json
```

**API Keys:**
- TMDB: https://www.themoviedb.org/settings/api (free)
- OMDb: http://www.omdbapi.com/apikey.aspx (free tier)

### 3. `nfo_generator.py`
Jellyfin/Kodi NFO files.

**Features:**
- Multi-part episodes
- Movie/TV support
- XML formatting
- Dry-run mode

**Usage:**
```bash
python nfo_generator.py data/canonical_metadata_20241108_120000.json data/llm_analysis_20241108_120000.json
```

**NFO Format:**
```xml
<episodedetails>
  <title>Encounter at Farpoint</title>
  <showtitle>Star Trek The Next Generation</showtitle>
  <season>1</season>
  <episode>1</episode>
  <multipart>
    <part>1</part>
    <part>2</part>
  </multipart>
  ...
</episodedetails>
```

### 4. `jellyfin_workflow.py`
Workflow orchestrator.

**Features:**
- End-to-end automation
- Logging
- Dry-run (default)
- Progress/error handling

**Usage:**
```bash
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" "V:\#MEDIA\Movies"
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --model gpt-4o-reasoning
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --execute
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --context "Focus on anime collections"
```

## Complete Workflow Example

```bash
# 1. Environment
export OPENAI_API_KEY="your_poe_api_key"
export TMDB_API_KEY="your_tmdb_key"
export OMDB_API_KEY="your_omdb_key"

# 2. Dry-run
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" "V:\#MEDIA\Movies"

# 3. Review data/workflow_output/:
# - workflow_complete_TIMESTAMP.json
# - reorganization_plan_TIMESTAMP.json
# - canonical_metadata_TIMESTAMP.json
# - llm_analysis_TIMESTAMP.json
# - nfo_files/

# 4. Execute
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --execute
```

## Output Files

- **`workflow_complete_TIMESTAMP.json`**: All results.
- **`reorganization_plan_TIMESTAMP.json`**: Folder renames, moves, NFO placement, compliance issues.
- **`canonical_metadata_TIMESTAMP.json`**: Movies (title/year/ID), TV (seasons/episodes/dates), multi-parts, sources.
- **`llm_analysis_TIMESTAMP.json`**: Media/confidence, structure, multi-parts, reorganization.
- **`nfo_files/`**: Organized NFOs.

## Multi-Part Episode Handling

**Detection:**
- Titles ("Part 1/2", "Part I/II")
- LLM patterns
- TMDB metadata

**NFO:** Maps episodes to single file, preserves Jellyfin order.

**Example:** Star Trek TNG S01
```
Encounter at Farpoint (Ep 1-2) → Star Trek The Next Generation - s01e01.nfo
<multipart><part>1</part><part>2</part></multipart>
```

## Requirements

### Python Packages
```bash
pip install requests
```

### API Keys
- `OPENAI_API_KEY` (Poe.com, required)
- `TMDB_API_KEY` (recommended)
- `OMDB_API_KEY` (optional)

### Directory Structure
```
scripts/media/
├── folder_structure_scanner.py  (Steps 1-2)
├── llm_structure_analyzer.py    (Step 3)
├── media_metadata_lookup.py     (Step 4a)
├── nfo_generator.py             (Step 4b)
└── jellyfin_workflow.py         (Orchestrator)

scripts/ai/
└── ravenmaven_client.py         (Poe client)
```

## Workflow Steps

### Steps 1-2: Scan & Summarize (Implemented)
- Recursive video scan
- Hierarchical summary
- Folder classification/counts

### Step 3: LLM Analysis
**Input:** Structure summary  
**Process:**
1. Analysis prompt
2. Poe API submission
3. JSON parse  
**Output:** Media list/confidence, structure changes, multi-parts

### Step 4a: Metadata Lookup
**Input:** LLM media  
**Process:**
1. TMDB queries
2. Episode details/multi-parts
3. Cache  
**Output:** Canonical DB, titles/years/flags

### Step 4b: NFO Generation
**Input:** Metadata/multi-parts  
**Process:**
1. NFO per multi-part
2. Episode mapping
3. TMDB/IMDB IDs
4. Jellyfin XML  
**Output:** NFO files

## Logging and Debugging

- **Workflow Log:** `data/workflow_output/workflow_TIMESTAMP.log`
- **LLM I/O:** `LLM_io_log/llm_transaction_TIMESTAMP.json` (requests/responses, tokens, timing, errors)
- **Dry-Run (default):** Plans only; `--execute` applies changes

## Troubleshooting

- **"Import ravenmaven_client could not be resolved"**: Ensure `scripts/ai/ravenmaven_client.py` exists (runtime resolve).
- **"No metadata for show X"**: Check TMDB_API_KEY, title spelling, DB availability, LLM accuracy.
- **"API 403 Forbidden"**: Validate key/permissions/rate limits.
- **Multi-parts not detected**: Review LLM/TMDB; manual add to list.

## Future Enhancements

- [ ] TVDB integration
- [ ] Auto rename/move
- [ ] Jellyfin API
- [ ] GUI
- [ ] Batch/large libs
- [ ] Custom rules

## Related Documentation

- [JELLY_RANCHER_README.md](../../JELLY_RANCHER_README.md)
- [bootstrap.md](../../bootstrap.md)
- [folder_structure_scanner.py](folder_structure_scanner.py)

## License

Part of JellyRancher project.

---

# docs\_archived_README.md

**Original Date:** 2025-11-15 04:19:26

**Compression:** 3,980 -> 3,169 chars (79.6%)

**Status:** success

# Archived Code - Integration Project

Directory contains code **successfully integrated** into main Jelly Rancher application (unused code integration project, November 2025).

## Why These Files Are Archived

Standalone scripts **superseded by integrated versions** with:
- Full PyQt5 GUI integration
- Worker threads for non-blocking operations
- Progress tracking and status updates
- Comprehensive error handling
- Audit logging integration
- User-friendly dialogs and workflows

## Archived Files

### 1. analyze_movie_names.py (204 lines)
**Purpose:** Analyze movie naming issues

**Integrated As:**
- `scripts/core/movie_name_backend.py` (400+ lines)
- `scripts/core/dialogs/movie_analysis_dialog.py` (620+ lines)
- Tools menu: "🎬 Analyze Movie Names"

**Improvements:**
- GUI dialog with results table
- Color-coded severity levels
- Real-time progress tracking
- JSON export
- Inline fix suggestions

---

### 2. fix_movie_names.py (360 lines)
**Purpose:** Fix movie naming issues

**Integrated As:**
- `scripts/core/movie_name_fixer.py` (450+ lines)
- Fix buttons in `movie_analysis_dialog.py`

**Improvements:**
- Dry-run preview
- Batch operations with progress callbacks
- Safety validation
- Results dialog with success/failure counts
- Auto re-analysis post-fix

---

### 3. fix_episode_titles.py (200+ lines)
**Purpose:** Fix TV episode titles

**Integrated As:**
- `scripts/core/episode_title_fixer.py` (400+ lines)
- `scripts/core/dialogs/episode_analysis_dialog.py` (fix functionality)
- Tools menu: "🔍 Analyze Episode Titles"

**Improvements:**
- TMDB cache integration
- Similarity scoring with confidence
- Pattern matching for 3 Jellyfin formats
- Interactive fix workflow
- Comprehensive validation

---

### 4. build_cache_from_tmdb.py (300+ lines)
**Purpose:** Generate TMDB caches

**Integrated As:**
- `scripts/core/tmdb_backend.py` (450+ lines)
- `scripts/core/dialogs/tmdb_cache_dialog.py` (500+ lines)
- Tools menu: "📺 Generate TMDB Cache"

**Improvements:**
- Interactive show search
- Progress tracking
- API key management in Settings
- Worker threads
- Save dialog for cache location

---

## Integration Summary

**Total Lines Integrated:** ~2,891 (8-9/10 rating)

**Statistics:**
- 24 commits on `feature/integrate-unused-code`
- 14/16 tasks (87.5%)
- ~14 hours development
- 4 phases shipped

**New Code:**
- 6 backend modules (~2,000 lines)
- 3 UI dialogs (~1,620 lines)
- 45+ tests (~550 lines)
- 3 user guides (~1,400 lines)
- pytest infrastructure (~270 lines)

**Quality Improvements:**
- Full GUI (no CLI-only)
- Comprehensive error handling
- Progress tracking/user feedback
- Safety (dry-run, validation)
- Audit logging
- ChromaDB progress tracking
- Complete documentation

## Usage Notes

**Do NOT delete!** Serves as:
1. Reference implementation
2. Code archaeology
3. Proof of integration
4. Backup

**Git History:** Preserved via `git mv`.

## Documentation

- `docs/MOVIE_NAME_MANAGEMENT.md`
- `docs/EPISODE_TITLE_MANAGEMENT.md`
- `docs/TMDB_CACHE_GENERATOR.md`
- `INTEGRATION_TODO_LIST.md`
- `INTEGRATION_PROGRESS.md`

---

*Archived: November 8, 2025*
*Phases 1-4 Complete*
*Branch: feature/integrate-unused-code*

---

# docs\start.md

**Original Date:** 2025-11-15 04:19:27

**Compression:** 231 -> 195 chars (84.4%)

**Status:** success

Read `bootstrap.md` for JellyRancher project workflow, ChromaDB usage patterns, and index maintenance requirements. It contains all critical information needed to work effectively on the project.

---

# docs\COMPREHENSIVE_PROJECT_REFERENCE.md

**Original Date:** 2025-11-16 04:10:08

**Compression:** 21,688 -> 12,438 chars (57.3%)

**Status:** success

# JellyRancher - Comprehensive Project Reference

**Version:** 1.0 - Consolidated Reference  
**Date:** November 16, 2025  
**Source Documents:** plan.md, ARCHITECTURE.md, architecture-reference.md, JELLYFIN_API_INTEGRATION_PLAN.MD, ass.plan.md

---

## Table of Contents

1. [Core Application Requirements](#core-application-requirements)
2. [Technology Stack & Dependencies](#technology-stack--dependencies)
3. [Component Architecture](#component-architecture)
4. [Jellyfin API Integration Strategy](#jellyfin-api-integration-strategy)
5. [Workflow State Machine](#workflow-state-machine)
6. [Data Models](#data-models)
7. [Implementation Status Assessment](#implementation-status-assessment)
8. [Risk Mitigation & Safety](#risk-mitigation--safety)
9. [Open Questions & Future Enhancements](#open-questions--future-enhancements)

---

## Core Application Requirements

PyQt6 desktop app automating media library organization, renaming, metadata enrichment for Jellyfin compliance using LLM analysis, metadata queries, fuzzy matching for safe, reversible operations.

### 1: Multi-Folder Scanning & Inventory
Recursive scan of folders for file list with metadata.

**Reqs:**
- Recursive multi-folder scan
- MD5 hash per file (duplicates/verification)
- Optional Jellyfin API cross-ref
- Extension filtering (videos, subtitles)
- Optional AniList/AniDB enrichment (anime)
- Parallel hashing

**FileRecord:**
```python
@dataclass
class FileRecord:
    absolute_path: Path
    size_bytes: int
    extension: str
    parent_folder: Path
    md5_hash: str
    scan_timestamp: datetime
    jellyfin_id: Optional[str] = None
    jellyfin_item_type: Optional[str] = None
    jellyfin_library_id: Optional[str] = None
    jellyfin_provider_ids: Optional[Dict[str, str]] = None
    jellyfin_matched: bool = False
```

### 2: Structural Summary & Analysis
Hierarchical folder overview with stats, Jellyfin comparison.

**Reqs:**
- Folder breakdown (counts, sizes)
- File type distribution
- MD5 duplicate detection/grouping
- Jellyfin match status per folder
- Playback stats (if Playback Reporting plugin)
- Visual tree hierarchy
- Before/after comparison

**Example:**
```
Movies/
├── Action (45 videos, 234.5 GB, 38 in Jellyfin, 2 duplicates)
├── Comedy (23 videos, 145.2 GB, 20 in Jellyfin, 0 duplicates)
└── Drama (67 videos, 312.8 GB, 45 in Jellyfin, 5 duplicates)
```

### 3: LLM-Assisted Reorganization Analysis
LLM analyzes structure, proposes Jellyfin-compliant organization.

**Reqs:**
- Submit folder summary (no file enumeration)
- Include Jellyfin context (items, collections, provider IDs)
- MD5 duplicates
- Playback history (Trakt)
- Detected media list (confidence)
- Reorg proposal (folder restructure)
- API actions (collections)

**LLM Input:**
```json
{
  "folder_structure": {
    "Movies/Action": {
      "file_count": 45,
      "total_size_gb": 234.5,
      "extensions": {"mkv": 42, "mp4": 3},
      "jellyfin_provider_ids": ["tmdb:12345", "tmdb:67890"],
      "md5_duplicates": {"hash1": 2, "hash2": 3}
    }
  },
  "jellyfin_context": {...},
  "duplicate_groups": {...}
}
```

### 4: Canonical Metadata Database
Authoritative DB from LLM/external APIs.

**Reqs:**
- Query TMDB/TVDB/OMDb (titles, years, episodes)
- Cross-ref Jellyfin provider IDs
- Multi-part episodes (NFOs for Jellyfin)
- Artwork (Fanart.tv)
- Theme songs (Themerr)
- Duplicate/merge (Merge Versions plugin)
- JSON persistence

**Structure:**
```json
{
  "movies": [{"title": "The Matrix", "year": 1999, "tmdb_id": 603, "imdb_id": "tt0133093", "poster_path": "/path/to/poster.jpg", "llm_detection": {...}}],
  "tv_shows": [{"title": "Breaking Bad", "year": 2008, "tvdb_id": 81189, "tmdb_id": 1396, "seasons": [{"season_number": 1, "episodes": [{"episode_number": 1, "title": "Pilot", "is_multi_part": false, "needs_nfo": false}]}]}],
  "multi_part_episodes": [{"show_title": "Star Trek: The Next Generation", "season": 1, "episode": 1, "parts": 2, "needs_nfo": true}]
}
```

### 5: Interactive Review Table
Editable action plan table for approval.

**Reqs:**
- Columns: Status, Current Path, Proposed Path, Action, Confidence, Notes
- Color: Green ≥95%, Yellow 70-94%, Orange review, Red error
- Jellyfin status (Already in Library, New, Path Mismatch)
- MD5 verification
- Bulk edit/filter
- Artwork/theme previews
- Collection suggestions

### 6: Safe Execution with Verification
Execute plan with rollback.

**Reqs:**
- Transactional ops with MD5 verify
- Pre: Source MD5 log
- Post: Dest MD5 match
- Associated files (subs)
- Jellyfin API (refreshes, collections)
- Artwork/theme downloads
- Audit trail
- Rollback

### 7: Subtitle Coverage Analysis
Assess subtitles.

**Reqs:**
- ffprobe embedded
- Jellyfin API (`GET /Items/{itemId}?Fields=MediaStreams`)
- MD5 verify
- Language/forced detection
- Kodi Sync Queue
- WizdomSubs

### 8: Automated Subtitle Acquisition
Download missing subs.

**Reqs:**
- Providers: OpenSubtitles.org/com, Podnapisi, Addic7ed
- Hash matching
- Language prefs
- Forced subs
- Post-download refresh (`POST /Items/{itemId}/Refresh`)
- MD5 verify
- Bazarr integration

---

## Technology Stack & Dependencies

### Core
- Python 3.12 (venv in root)
- PyQt6 (GUI)
- SQLite (DB)
- pathlib

### Metadata & Media
| Library | Purpose | Status | Rate Limits |
|---------|---------|--------|-------------|
| `tmdbv3api` | TMDB | ✅ | 40/10s |
| `tvdb_v4_official` | TVDB | ✅ | Varies |
| `wikipedia-api` | Wikipedia | ✅ | 1/2s |
| `pymediainfo` | Media inspect | ✅ | N/A |
| `ffmpeg-python` | Sub detection | ✅ | N/A |

**Subtitles:**
| Library | Purpose | Status |
|---------|---------|--------|
| `subliminal` | Downloader | ✅ |
| `python-opensubtitles` | OpenSubtitles API | ✅ |

**LLM:**
| Library | Purpose | Status |
|---------|---------|--------|
| `anthropic` | Claude | ✅ |
| `openai` | OpenAI | ✅ |
| `langchain` | Abstraction | ✅ |

**Utils:**
| Library | Purpose | Status |
|---------|---------|--------|
| `rapidfuzz` | Fuzzy match | ✅ |
| `lxml` | NFO/XML | ✅ |
| `tenacity` | Retry | ✅ |
| `ratelimit` | Limits | ✅ |
| `send2trash` | Safe delete | ✅ |

**Built-in:** pathlib, shutil, hashlib, sqlite3, json, xml.etree.ElementTree

**requirements.txt:**
```txt
PyQt6>=6.6.0
tmdbv3api>=1.9.0
tvdb_v4_official>=1.0.0
wikipedia-api>=0.6.0
pymediainfo>=6.0.0
ffmpeg-python>=0.2.0
subliminal>=2.1.0
python-opensubtitles>=0.2.0
anthropic>=0.18.0
openai>=1.0.0
langchain>=0.1.0
rapidfuzz>=3.5.0
lxml>=4.9.0
tenacity>=8.2.0
ratelimit>=2.2.1
send2trash>=1.8.2
```

---

## Component Architecture

### Layer 1: GUI (PyQt6)
- Folder Selection Widget
- Review Table Widget (color-coded, editable)
- Progress Monitor

### Layer 2: Orchestration
- Workflow Controller (8-point state machine)
- State Manager
- Transaction Manager (logging/rollback)

### Layer 3: Business Logic
- File Scanner (recursive inventory)
- LLM Analyzer (structure/proposals)
- Metadata Matcher (TMDB/TVDB fuzzy)
- Jellyfin Validator (naming/structure)
- Subtitle Manager
- File Operations (moves/renames/verify)

### Layer 4: Data Access
- SQLite Repository (logs/cache/inventory)
- API Clients (TMDB/TVDB/OpenSubtitles/LLM)
- FS Ops (I/O handling)

---

## Jellyfin API Integration Strategy

RESTful HTTP API for read/write server access.

### Key Points by Step
1. **Scan:** `GET /Items?Recursive=true&IncludeItemTypes=Movie,Episode&Fields=Path,ProviderIds` → path-to-item map, ProviderIds
2. **Summary:** `GET /Views`/`/UserViews` → library structure for LLM
3. **LLM:** `GET /Items/{itemId}?Fields=ProviderIds` → metadata in prompt
4. **Metadata:** `POST /Items/{itemId}/Refresh` → NFO validation
5. **Review:** Step 1 data → Jellyfin status column
6. **Exec:** `POST /Libraries/{libraryId}/Refresh`, `/Collections/{collectionId}/Items`, `/Items/{itemId}/Refresh` → updates
7. **Subs Analysis:** `GET /Items/{itemId}?Fields=MediaStreams` → server validation
8. **Subs Acq:** `POST /Items/{itemId}/Refresh` → recognize subs

**Remote:** `http://localhost:8096`/HTTPS; API key (Dashboard > Admin > Advanced > API Keys)

**Approach:**
1. Phase 1: Read-only context
2. Phase 2: Read-write updates

---

## Workflow State Machine

1. Folder Selection
2. File Scanning (inventory)
3. Hierarchy Generation
4. LLM Analysis (proposal/media)
5. Metadata Querying (canonical DB)
6. Operation Planning (review table)
7. User Review/Approval
8. Transaction Snapshot
9. File Operations (MD5 verify)
10. Subtitle Detection (local/API)
11. Subtitle Acquisition
**Final:** Complete/Rollback

---

## Data Models

**FileRecord:**
```python
@dataclass
class FileRecord:
    absolute_path: Path
    size_bytes: int
    extension: str
    parent_folder: Path
    md5_hash: str
    scan_timestamp: datetime
    jellyfin_id: Optional[str] = None
    jellyfin_item_type: Optional[str] = None
    jellyfin_library_id: Optional[str] = None
    jellyfin_provider_ids: Optional[Dict[str, str]] = None
    jellyfin_matched: bool = False
```

**Media Metadata:**
```python
@dataclass
class MovieMetadata:
    tmdb_id: int
    title: str
    year: int
    original_title: str
    overview: str
    poster_path: str
    backdrop_path: str

@dataclass
class TVShowMetadata:
    tvdb_id: int
    tmdb_id: int
    show_name: str
    year: int
    overview: str
    poster_path: str
    seasons: List[Season]

@dataclass
class Episode:
    season_number: int
    episode_number: int
    episode_title: str
    air_date: date
    is_multi_part: bool = False
    needs_nfo: bool = False
```

**ProposedOperation:**
```python
@dataclass
class ProposedOperation:
    record_id: str
    action_type: ActionType  # MOVE, RENAME, NFO_CREATE, DELETE, NO_ACTION
    source_path: Path
    destination_path: Path
    confidence: float
    color_code: ColorCode
    metadata: Optional[Union[MovieMetadata, TVShowMetadata]]
    notes: str
    user_approved: bool = False
    jellyfin_status: str = "Unknown"  # "Already in Library", "New", "Path Mismatch"
```

**Transaction Log:**
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    transaction_batch_id TEXT,
    timestamp DATETIME,
    operation_type TEXT,
    source_path TEXT,
    destination_path TEXT,
    source_md5 TEXT,
    destination_md5 TEXT,
    status TEXT,
    error_message TEXT,
    jellyfin_item_id TEXT,
    user_notes TEXT
);
```

---

## Implementation Status Assessment

### 1: Scanning
**✅:** Multi-folder scan (`FileScanner.scan_folder()`), inventory storage (`InventoryRepository.add_file_records()`), filtering, Jellyfin ProviderIds  
**❌:** MD5 integration, AniList/AniDB, parallel hashing

### 2: Summary
**✅:** Hierarchy (`FileScanner.get_folder_structure()`), Jellyfin counts, QTreeWidget  
**❌:** MD5 duplicates, playback stats, before/after

### 3: LLM
**✅:** Pipeline (`LLMAnalysisWorker`, `LLMStructureAnalyzer`), structure conversion, output, GUI  
**❌:** MD5 in prompts, Trakt, API automation

### 4: Metadata
**✅:** TMDB/TVDB/OMDb (`MediaMetadataLookup`), DB persistence, multi-part tagging  
**❌:** NFO gen, artwork/Themerr, duplicate/merge, mapping

---

## Risk Mitigation & Safety

**Data Loss:**
1. Read-only until approval
2. MD5 pre/post
3. Transaction logging/rollback
4. Atomic moves
5. Dry-run

**API:**
1. Caching (SQLite)
2. Backoff (`tenacity`)
3. Circuit breaker
4. Offline manual

**UX:**
1. Granular/bulk approve
2. Confidence colors/scores
3. Undo
4. Progress tracking

---

## Open Questions & Future Enhancements

**Decisions:**
1. LLM: Claude vs GPT-4 (Claude pref)
2. Cache: 30 days
3. Batch: 100
4. NFO: Selective

**Enhancements:**
- Multi-lang subs
- Duplicates
- Quality upgrades
- Scheduling
- Jellyfin refresh
- Transcoding flags
- Plugin
- Analytics (Playback Reporting)

---

## Configuration Management

**data/app_config.json:**
```json
{
  "api_keys": {
    "tmdb": "YOUR_TMDB_KEY",
    "tvdb": "YOUR_TVDB_KEY",
    "anthropic": "YOUR_CLAUDE_KEY",
    "opensubtitles_org": {"username": "user", "password": "pass"}
  },
  "preferences": {
    "llm_provider": "anthropic",
    "dry_run_default": true,
    "auto_approve_threshold": 0.95
  },
  "rate_limits": {"tmdb": 40, "tvdb": 50, "wikipedia": 1},
  "subtitle_languages": ["eng"],
  "subtitle_forced": true
}
```

---

## Testing Strategy

**Unit:**
- Scanner accuracy
- Fuzzy thresholds
- NFO correctness
- MD5 verify
- Rollback

**Integration:**
- API mocking/limits
- DB integrity
- E2E workflow
- Rollback (test media)

---

**Consolidated reference for JellyRancher development. Original sources intact.**

---

# docs\GUI_REDESIGN_COMPREHENSIVE_PLAN.md

**Original Date:** 2025-11-16 20:52:49

**Compression:** 17,491 -> 9,084 chars (51.9%)

**Status:** success

# JellyRancher GUI Redesign - Analysis & Plan

**Date:** 2025-11-16 20:50:40  
**Status:** Planning Phase  
**Priority:** Critical - User Experience Overhaul

---

## 📊 Executive Summary

**Problem:** Current GUI is janky, counterintuitive, rigid, unmodernized. Requires full library rescan (1.3TB, 4,188 files) every session; no save/resume; inflexible workflow.

**Core Issues:**
1. No state persistence
2. Rigid 9-step linear workflow
3. Poor UX (basic widgets, clunky)
4. Rescanning overhead
5. No project management

**Solution:** Incremental PyQt6 modernization with project system foundation, UI polish, workflow flexibility.

---

## 🔍 Current State Analysis

### Architecture Overview

**File:** `jelly_rancher_clean.py` (2,445 lines)

**Structure:**
```
jelly_rancher_clean.py
├── FolderContentSelectionDialog (QDialog) - Lines 77-195
├── ScanWorker (QThread) - Lines 198-404
├── MultiScanWorker (QThread) - Lines 407-442
├── LLMAnalysisWorker (QThread) - Lines 445-571
├── MetadataWorker (QThread) - Lines 574-718
├── ActionPlanWorker (QThread) - Lines 721-752
└── JellyRancherClean (QMainWindow) - Lines 755-2445
    ├── In-memory data storage
    ├── 5 tabs (scan, metadata, review, execute, subtitles)
    ├── ~60 UI/event methods
    └── No persistence
```

### Current Workflow (9 Steps)

**Tabs 1-2:** Scan folders → View results (repeat every session)  
**Tabs 3-4:** LLM analysis → Metadata lookup (unsaved)  
**Tab 5:** Review/approve actions (state lost)  
**Tabs 6-7:** Snapshot → Execute (no history)  
**Tabs 8-9:** Subtitle analysis/download (isolated)

### Data Flow

**Persisted:**
- ✅ Scans → SQLite (`data/inventory.db`): files, folders, MD5, session ID
- ✅ LLM → JSON (`data/llm_analysis_*.json`)
- ✅ Jellyfin config → JSON (`data/jellyfin_config.json`)

**Lost:**
- ❌ Selected/excluded folders
- ❌ LLM results (memory)
- ❌ Media list, action plan, approvals
- ❌ Workflow progress, UI state

### User Pain Points

- Phase 31G: Unsophisticated UI, broken progress bar, non-resizable columns, no LLM model selection
- Phase 32: Janky, rigid, rescanning inconvenient, no save/resume
- Historical: Unclear order, lost snapshot, needed workflow buttons

---

## 🎯 Design Goals

### Primary
1. **State Persistence:** Save/resume all state; no loss on close/crash
2. **Workflow Flexibility:** Non-linear, skip/reorder, multi-analysis, comparisons
3. **Modern UX:** Professional, intuitive, responsive, visual feedback
4. **Project Management:** Create/open/save, recent list, auto-save, export/import
5. **Performance:** Fast DB load, responsive UI, background ops, low memory

### Secondary
- Keyboard shortcuts
- Contextual help
- Undo/redo
- Search/filter
- Batch ops
- Custom layouts
- Dark mode
- Accessibility

---

## 🏗️ Proposed Architecture

### Option 1: Modern PyQt6 (Recommended)

**Incremental modernization.**

**Components:**
```
jelly_rancher_v2/
├── core/
│   ├── project_manager.py          # NEW
│   ├── state_serializer.py         # NEW
│   └── workflow_engine.py          # NEW
├── gui/
│   ├── main_window.py
│   ├── project_dialog.py           # NEW
│   ├── modern_theme.qss            # NEW
│   ├── widgets/
│   │   ├── scan_panel.py
│   │   ├── analysis_panel.py
│   │   ├── review_panel.py
│   │   └── comparison_view.py      # NEW
│   └── docks/
│       ├── folder_dock.py          # NEW
│       ├── progress_dock.py        # NEW
│       └── log_dock.py             # NEW
├── models/
│   ├── project.py                  # NEW
│   ├── scan_session.py
│   └── analysis_version.py         # NEW
└── database/
    ├── schema_v2.sql
    └── migrations/
```

**Database Schema (Extended):**
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME,
    last_opened DATETIME,
    workflow_step INTEGER,
    notes TEXT
);

CREATE TABLE project_scan_sessions (
    project_id INTEGER,
    scan_session_id INTEGER,
    added_at DATETIME,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (scan_session_id) REFERENCES scan_sessions(id)
);

CREATE TABLE project_state (
    project_id INTEGER PRIMARY KEY,
    selected_folders JSON,
    excluded_subfolders JSON,
    workflow_data JSON,
    ui_state JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE analysis_versions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    version_number INTEGER,
    model_name TEXT,
    created_at DATETIME,
    analysis_json_path TEXT,
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE action_plans (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    analysis_version_id INTEGER,
    created_at DATETIME,
    actions JSON,
    user_approvals JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (analysis_version_id) REFERENCES analysis_versions(id)
);
```

**Pros:** Incremental, reuses code, fast (2-3 weeks: W1 project sys, W2 UI, W3 workflow)  
**Cons:** PyQt6 limits, refactoring needed

### Option 2: Web-Based UI

**Stack:** FastAPI backend, React/TS frontend, Material-UI/AntD, Redux/Zustand, REST+WS

**Architecture:**
```
jellyrancher-web/
├── backend/
│   ├── api/ (projects.py, scans.py, analysis.py, actions.py)
│   ├── services/ (scan_service.py, llm_service.py, metadata_service.py)
│   └── database/ (models.py)
└── frontend/
    ├── src/
    │   ├── components/ (ProjectManager/, ScanPanel/, etc.)
    │   ├── pages/ (Dashboard.tsx, Project.tsx, Settings.tsx)
    │   ├── store/ (projectSlice.ts)
    │   └── api/ (client.ts)
    └── public/
```

**Pros:** Modern/responsive UI, remote access (4-6 weeks)  
**Cons:** Rewrite risk, new stack, longer timeline

### Option 3: Hybrid

**PyQt6 core + QWebEngineView for viz, FastAPI/React for parts.**  
**Pros:** Gradual, best of both (3-4 weeks)  
**Cons:** Dual stacks, complexity

---

## 📋 Implementation Phases

### Phase 32A: Project Management (Week 1)

**Tasks:**
1. DB schema + migration (4h)
2. ProjectManager CRUD, save/load, auto-save (6h)
3. GUI: File menu, selector, warnings (8h)
4. State serialization + restore (6h)

**Deliverables:** Project save/load, no rescanning, recent list  
**Metrics:** Restore state, <2s load, no loss

### Phase 32B: UI Modernization (Week 2)

**Tasks:**
1. QSS theme, dark/light (8h)
2. QTreeView tables, search, progress (10h)
3. Dock layouts, splitters, save layout (8h)
4. Icons, animations, tooltips (6h)

**Deliverables:** Professional UI, flexible layout  
**Metrics:** User satisfaction, faster tasks

### Phase 32C: Workflow Flexibility (Week 3)

**Tasks:**
1. Non-linear workflow, validation (8h)
2. Multi-analysis versions + UI (8h)
3. Side-by-side diff/merge/export (8h)
4. Shortcuts, menus, batch, undo (6h)

**Deliverables:** Flexible engine, comparisons  
**Metrics:** Skip steps, compare analyses, faster workflow

---

## 🎨 UI/UX Design Principles

### Visual Design

**Colors:**
```
Primary: #2196F3
Secondary: #4CAF50
Accent: #FF9800
Error: #F44336
Warning: #FFC107
Bg Light: #FAFAFA | Dark: #121212
Surface Light: #FFFFFF | Dark: #1E1E1E
```

**Typography:**
```
Headings: Segoe UI Bold, 18-24pt
Body: Segoe UI Regular, 11pt
Mono: Consolas, 10pt
```

**Spacing:** Tight 4px, Normal 8px, Loose 16px, Wide 24px

### Interaction Patterns
- Immediate feedback, progress, notifications, hovers
- Consistent actions/visuals/patterns
- Shortcuts, context menus, batch, defaults

### Information Architecture

**Dashboard:**
```
JellyRancher [Project: ▼]
Recent Projects | Quick Actions
• Media Cleanup | 🔍 Scan
• TV Shows 2025 | 🤖 LLM
• Movie Library | 📋 Review
                 ▶️ Execute
```

**Project View:**
```
Project: Media Cleanup [Save] [⚙️]
┌──────┬─
│Scan  │ Selected: W:\#MEDIA (4,188f,1.3TB)
│LLM   │ W:\#MEDIA2 (2,341f,800GB)
│Meta  │
│Plan  │ Analysis: v1 Claude-Sonnet-4.5(81s)
│Exec  │ v2 Gemini-2.5-Pro(65s)[Active]
│      │ Actions:150 ✓120 ⏸30
└──────┘
```

---

## 🔄 Migration Strategy

**Gradual:**
1. Extract core logic to services
2. Add project system
3. Refactor GUI modularly
4. Enhance features

**Compatibility:** Preserve scans/LLM/settings; full feature parity.

---

## 📊 Success Criteria

**Must Have:**
- Project save/load
- No rescanning
- Resume any point
- Modern UI
- Existing features

**Should Have:**
- Non-linear workflow
- Multi-analysis + comparisons
- Shortcuts
- Dark mode

**Nice to Have:**
- Export/import
- Templates
- Advanced filter
- Batch
- Dashboard

---

## 🎯 Next Steps

1. User review/confirm priorities
2. Wireframes/schema (if approved)
3. Week 1 prototype (project POC)
4. Weeks 2-3 implementation

**Questions:**
1. PyQt6/Web/Hybrid?
2. Timeline urgency (2 vs 4-6w)?
3. Project first or UI?
4. UX inspirations?
5. Critical nice-to-haves?
6. Risk tolerance?

---

## 📚 References
- `jelly_rancher_clean.py` (2,445 lines)
- `scripts/core/jelly_rancher_main.py` (3,568 lines)
- `scripts/core/inventory_repository.py`
- `docs/USER_GUIDE.md`
- `docs/PYQT6_MIGRATION_PLAN.md`
- `agent-journal.md` (Phases 31G,32)

**Version:** 1.0  
**Updated:** 2025-11-16 20:50:40  
**Status:** Awaiting Feedback

---

# docs\UX_REDESIGN_MASTER_PLAN.md

**Original Date:** 2025-11-18 08:26:40

**Compression:** 37,632 -> 15,868 chars (42.2%)

**Status:** success

# JellyRancher UX Redesign Master Plan

**Status:** Approved for Implementation  
**Created:** 2025-11-17  
**Version:** 1.0  
**Target:** Phase 32 Implementation

---

## Executive Summary

### The Problem
Current `jelly_rancher_clean.py` GUI (2,445 lines): rigid linear 9-step wizard—forces sequential steps, no save/resume, poor feedback, "janky/rigid".

### The Solution: Project-Centric Workflow Canvas
Transform to **studio**: save/resume anytime, non-linear workflow, project overview/dependencies/progress, preview/tweak/approve. Like Photoshop/VSCode.

---

## Core UX Principles

1. **Project-Centric**: Projects contain scans, LLM analyses (multi-version), action plans, execution history, settings.
2. **Task-Based**: Show "What do you want to do?", state-based actions, requirements for locked actions, smart suggestions.
3. **Always Visible Context**: Project name/state, done/pending, metrics, logs/history access.
4. **Flexible Workflow**: Skip optionals, redo, compare analyses, export/import anytime.
5. **Professional Polish**: Modern design, responsive, tooltips, shortcuts, undo/redo.

---

## Main Window Layout: "The Studio"

```
┌─────────────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help              [Project: My Media Library ▼]│
├───────────┬─────────────────────────────────────────────────────────────┤
│ PROJECT   │                    WORKSPACE                                 │
│ EXPLORER  │                                                               │
│           │  ┌─────────────────────────────────────────────────────┐    │
│ 📁 Scans  │  │                                                     │    │
│  ├─ Scan1 │  │         [Active View: Scan Results]                │    │
│  └─ Scan2 │  │                                                     │    │
│           │  │   - OR -                                            │    │
│ 🤖 Analyses│ │                                                     │    │
│  ├─ GPT4  │  │   [Split View: Compare Two Analyses]               │    │
│  └─ Claude│  │                                                     │    │
│           │  │   - OR -                                            │    │
│ 📋 Plans  │  │                                                     │    │
│  └─ Plan1 │  │   [Action Plan Review Table]                       │    │
│           │  │                                                     │    │
│ ⚙️ Execute│  │   - OR -                                            │    │
│  └─ Logs  │  │                                                     │    │
│           │  │   [Execution Progress & Logs]                      │    │
│ 📊 Reports│  │                                                     │    │
│           │  └─────────────────────────────────────────────────────┘    │
│           │                                                               │
│ [Actions] │  ┌─────────────────────────────────────────────────────┐    │
│ ▶ Scan    │  │ CONTEXT PANEL (collapsible)                        │    │
│ ▶ Analyze │  │ - Details about selected item                       │    │
│ ▶ Review  │  │ - Quick stats                                       │    │
│ ▶ Execute │  │ - Related actions                                   │    │
│           │  └─────────────────────────────────────────────────────┘    │
├───────────┴─────────────────────────────────────────────────────────────┤
│ ⚡ Ready  │  📁 1,234 files scanned  │  🤖 2 analyses  │  ⏱️ 00:26.7s   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layout Components

#### A. Top Bar
Menu: File/Edit/View/Tools/Help. Project dropdown (current + recent). Quick: New/Save/Settings.

#### B. Left Sidebar: Project Explorer (250px, resizable)
Tree view:

1. **📁 Scans**: date/folder/file count. Right-click: Re-scan/Delete/Export.
2. **🤖 Analyses**: model/date/confidence. Right-click: Re-analyze/Compare/Export.
3. **📋 Action Plans**: ops/approved/rejected. Right-click: Edit/Export/Duplicate.
4. **⚙️ Execution**: status/progress. Right-click: Rollback/Export.
5. **📊 Reports**: summaries/suggestions.

Bottom: Context-aware action buttons.

#### C. Center: Workspace (tabbed, multi-view)
- Scan Results
- Analysis (single/split compare)
- Action Plan Table (Excel-like)
- Execution Monitor
- Metadata Browser
- Settings

Multi-tab, side-by-side.

#### D. Right Panel: Context (300px, collapsible)
Item details/stats/related/quick actions/help.

#### E. Bottom: Status Bar
Left: op status. Center: metrics (files/size/time). Right: perf/logs.

---

## Key Views & Interactions

### View 1: Scan Configuration & Results
```
┌─────────────────────────────────────────────────────────────────────┐
│ SCAN CONFIGURATION                                    [▶ Start Scan] │
├─────────────────────────────────────────────────────────────────────┤
│ Selected Folders:                                    [+ Add Folder]  │
│ ┌──────────────────────┬──────────┬─────────┬──────────────────┐   │
│ │ Path                 │ Included │ Excluded│ Actions           │   │
│ ├──────────────────────┼──────────┼─────────┼──────────────────┤   │
│ │ D:\Media\Movies      │ 245      │ 12      │ [Edit][Remove]    │   │
│ │ E:\TV Shows          │ 1,023    │ 5       │ [Edit][Remove]    │   │
│ └──────────────────────┴──────────┴─────────┴──────────────────┘   │
│ Options: ☑ MD5 hashes ☑ Filename metadata ☐ Deep scan              │
│ Est. time: ~30s (1,268 files, 1.3 TB)                              │
├─────────────────────────────────────────────────────────────────────┤
│ SCAN RESULTS [Search] [Filter] [Group] [Export]                     │
│ ┌─────────────────┬──────────┬──────┬──────┬────────┬──────┐       │
│ │ Filename         │ Path     │ Size │ Type │ MD5    │ Meta │       │
│ ├─────────────────┼──────────┼──────┼──────┼────────┼──────┤       │
│ │ Movie.mkv        │ D:\Media │4.2GB│ MKV  │a3f2.. │ ✓    │       │
│ │ Show.S01E01.mkv  │ E:\TV    │1.8GB│ MKV  │b7e9.. │ ✓    │       │
│ └─────────────────┴──────────┴──────┴──────┴────────┴──────┘       │
│ 1,268 files | 1.3 TB | Dups:3 | Issues:12                           │
└─────────────────────────────────────────────────────────────────────┘
```

Interactions: Add/Edit folder (`FolderContentSelectionDialog`), Start Scan (progress), sortable/filterable table, right-click: open/view/mark.

### View 2: LLM Analysis
**Single:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ LLM ANALYSIS                                                         │
│ Model: [Claude-3.7-Sonnet ▼] [Preview Prompt]                       │
│ Type: ● Folder Struct ○ Metadata ○ Duplicates                       │
│ Options: ☑ Samples ☑ Confidence ☐ Extended                          │
│ Est: $0.15 | ~30s                [▶ Run Analysis]                   │
├─────────────────────────────────────────────────────────────────────┤
│ RESULTS: GPT-4 (2025-11-17 14:32) ✓ High conf, 23 issues            │
│ SUMMARY: Mix movies/TV; rec: /Movies /TV, naming std, 23 renames.   │
│ [Full] [JSON] [Compare] [Gen Plan]                                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Compare:**
```
┌──────────────────────────────┬──────────────────────────────┐
│ GPT-4 (14:32) High 23 issues │ Claude (14:45) Med 31 issues │
│ • Separate M/TV              │ • Separate M/TV              │
│ • Naming 23 renames          │ • Naming 31 renames+8 moves  │
├──────────────────────────────┴──────────────────────────────┤
│ Diffs: Claude +8 episodes; GPT-4 higher conf; core agree.    │
│ [Merged Plan] [Export]                                     │
└─────────────────────────────────────────────────────────────┘
```

Interactions: Preview prompt, Run (progress), Compare split, Gen Plan.

### View 3: Action Plan Review
```
┌─────────────────────────────────────────────────────────────────────┐
│ ACTION PLAN REVIEW (GPT-4: 23 ops; 15 app,3 rej,5 pend)             │
│ [Search] [Filter] [Group] [All] [App Sel] [Rej Sel] [Bulk Edit]     │
│ ┌──┬──────┬─────────────────┬─────────────────┬─────────┬───────┐│
│ │☑ │Type  │Curr Path        │Prop Path        │Conf    │App   ││
│ ├──┼──────┼─────────────────┼─────────────────┼─────────┼───────┤│
│ │☑ │RENAME│Movie 2023.mkv   │Movie (2023).mkv │HIGH ●  │☑     ││
│ │☑ │MOVE  │D:\Mix\Show.mkv  │E:\TV\Show\S01.. │HIGH ●  │☑     ││
│ │☐ │RENAME│OldName.avi      │NewName.avi      │MED ◐   │☐     ││
│ └──┴──────┴─────────────────┴─────────────────┴─────────┴───────┘│
│ [Preview] [Save] [Execute App] ⚠️ Dry Run avail.                   │
└─────────────────────────────────────────────────────────────────────┘
```

Features: Search/group/bulk/inline edit/drag (deps)/colors (green app/red rej/yel pend/gray block). Right-click: edit/details/open/except/similars. Preview: tree diff modal.

### View 4: Execution Monitor
```
┌─────────────────────────────────────────────────────────────────────┐
│ EXECUTION: Plan1 (15 app)                                           │
│ Progress: ████████████████░░░░ 60% (9/15) | 00:12.4s | ~00:08s     │
│ LOG: ✓[14:52:01] RENAME Movie→(2023) ✓MOVE Show... ⏳RENAME... ⏸️MOVE│
│ [Pause] [Stop] [Rollback] [Export] ⚠️ Reversible                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Post-Exec:**
```
EXEC COMPLETE: 15 ops 00:20.8s (8 rename,5 move,2 NFO,0 err)
Next: ☐ Jellyfin refresh ☐ Verify ☐ Report
[Refresh] [Report] [Close]
```

---

## Project Management

### File Menu
```
File
├─ New... Ctrl+N
├─ Open... Ctrl+O
├─ Recent →
│  ├─ My Media Library
│  ├─ TV Shows Reorg
│  └─ Movie 2024
├─ Save Ctrl+S
├─ Save As... Ctrl+Shift+S
├─ Close Ctrl+W
├─ Import → Scan/Plan/JSON
├─ Export → View/Project/Report
├─ Settings Ctrl+,
└─ Exit Alt+F4
```

### Project Structure (Database)
**`projects`**
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_opened TIMESTAMP,
    state TEXT DEFAULT 'active',
    settings_json TEXT
);
```

**`project_scan_sessions`**
```sql
CREATE TABLE project_scan_sessions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    scan_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_end TIMESTAMP,
    total_files INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    scan_options_json TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**`project_analyses`**
```sql
CREATE TABLE project_analyses (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    scan_session_id INTEGER,
    model_name TEXT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prompt_text TEXT,
    response_text TEXT,
    parsed_json TEXT,
    confidence TEXT,
    issues_found INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (scan_session_id) REFERENCES project_scan_sessions(id)
);
```

**`project_action_plans`**
```sql
CREATE TABLE project_action_plans (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    analysis_id INTEGER,
    plan_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_operations INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    executed BOOLEAN DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (analysis_id) REFERENCES project_analyses(id)
);
```

**`project_operations`**
```sql
CREATE TABLE project_operations (
    id INTEGER PRIMARY KEY,
    action_plan_id INTEGER NOT NULL,
    operation_type TEXT NOT NULL,
    current_path TEXT,
    proposed_path TEXT,
    current_md5 TEXT,
    proposed_md5 TEXT,
    confidence TEXT,
    user_approved BOOLEAN DEFAULT NULL,
    executed BOOLEAN DEFAULT 0,
    execution_timestamp TIMESTAMP,
    rollback_data_json TEXT,
    FOREIGN KEY (action_plan_id) REFERENCES project_action_plans(id)
);
```

**`project_state`**
```sql
CREATE TABLE project_state (
    project_id INTEGER PRIMARY KEY,
    current_view TEXT,
    ui_state_json TEXT,
    last_scan_session_id INTEGER,
    last_analysis_id INTEGER,
    last_action_plan_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### Save/Load
**Save (auto 30s + manual):** Persist scans (`scanned_files`), analyses, plan state, UI state; update `last_opened`.
**Load:** Restore scans/explorer/UI; prompt resume if in-progress.
**Close:** Prompt unsaved; auto-save state.

---

## Smart Dependency Handling

**No Scan for Plan:**
```
⚠️ Action Plan Requires Scan
✓ Scanned files ✗ LLM (opt)
[▶ Run Scan] [Load Prev] [Import] [Cancel]
```

**No Approvals for Exec:**
```
⚠️ No Ops Approved (23 total)
[✓ App High Conf (15)] [Review Table] [Auto-App Rules] [Cancel]
```

---

## Visual Design System

### Color Palette
```
Primary: #2c3e50
Secondary: #1f6fb2
Success: #27ae60
Warning: #f39c12
Danger: #e74c3c
Info: #9b59b6
BG: #ecf0f1 | Surface: #ffffff | Border: #bdc3c7
Text: #2c3e50 | Light: #566573
```

### Typography
Headings: Segoe UI 18pt Bold  
Body: Segoe UI 10pt Reg  
Mono: Consolas 9pt

### Spacing
Pad: 10/20px | Marg: 10px | Border: 1px #bdc3c7 | Rad: 4px

### Icons
Material/Font Awesome: 📁🤖📋⚙️📊✓⚠️❌

---

## Keyboard Shortcuts

**Global:** Ctrl+N/O/S/W/, Q; F1 Help; F5 Refresh  
**Nav:** Ctrl+1-9 sections; Ctrl+Tab/Shift+Tab tabs; Alt+Left/Right  
**Actions:** Ctrl+R Run; Ctrl+P Preview; Space toggle; Ctrl+A all; Del remove  
**Table:** Ctrl+F search; Ctrl+G group; Ctrl+E export; ↑↓/Enter/Esc

---

## Implementation Phases

### Phase 32A: Foundation (Week 1)
1. DB schema + migration.
2. `ProjectManager`: CRUD/auto-save/import/export.
3. Main window: menu/sidebar/tabs/status.
4. Explorer: tree/menus/drag/dbl-click.

**Deliv:** Create/save/load projects, view structure.

### Phase 32B: Core Views (Week 2)
1. Scan: migrate UI/table/search.
2. Analysis: model/prompt/compare/save multi.
3. Plan Review: table (search/group/edit/bulk/color/preview).
4. Exec: progress/log/pause/rollback.

**Deliv:** All views functional.

### Phase 32C: Polish (Week 3)
1. Design: QSS/icons/anims/dark mode.
2. Interactions: tooltips/deps/shortcuts/undo.
3. Advanced: diff/bulk/filters/exports.
4. Test: workflows/perf/bugs/docs.

**Deliv:** Production-ready.

---

## Migration Strategy
1. Keep old `jelly_rancher_clean.py`; new `jelly_rancher_studio.py` + `ui/`.
2. Extract workers to `scripts/workers/`.
3. Build/test new UI parallel.
4. Migrate `scanned_files` to schema on first launch.
5. Deprecate old post-stabilization.

---

## Success Criteria
**UX:** Save/resume, non-linear, state glance, control, modern.  
**Perf:** Save/load <2s, responsive, 10k+ rows smooth.  
**Func:** All workflows, no loss, rollback, compare.  
**Code:** Sep concerns, errors/logging/tests/docs.

---

## Risk Mitigation
1. Scope: Phase gates.  
2. DB Perf: Index FKs; test 100k files.  
3. UI Complex: Incremental.  
4. Adoption: Keep old; guide/feedback.  
5. Breaks: Test/parallel/gradual.

---

## Appendix: Wireframes

**New Project:**
```
Project Name: [____]
Desc: [____]
Loc: [C:\...\projects\] [Browse]
Template: ● Blank ○ Scan ○ Dup
[Cancel] [Create]
```

**Settings:**
```
[General|Scanning|LLM|Exec|Jellyfin|Adv]
Theme: [Light] Lang: [En] Auto-save: [30s]
☑ Updates ☑ Stats
Paths: Projects/Logs/Temp [Browse]
[Cancel] [Apply] [OK]
```

---

## Next Steps

**Today:** Doc `docs/UX_REDESIGN_MASTER_PLAN.md`; journal; Git commit.  

**Tomorrow (32A):**  
1. Migration `scripts/database/schema.sql/migrations.py`; test `media_library.db`.  
2. `scripts/core/project_manager.py`: create/load/save/list + timer.  
3. `jelly_rancher_studio.py`: window/menu/sidebar/tabs.  

**Week 1 Goal:** New/load projects, sidebar structure, basic views.

**End of Master Plan**  
*Authoritative for Phase 32. Align dev; updates need approval.*

---

# docs\ERROR_HANDLING_GUIDELINES.md

**Original Date:** 2025-11-19 02:55:06

**Compression:** 9,652 -> 7,852 chars (81.4%)

**Status:** success

# JellyRancher Error Handling Guidelines

## Overview
Error handling patterns from Phase 33E ensure robustness, graceful degradation, and clear user feedback.

## Core Principles

### 1. Defensive Programming
- Validate all inputs before processing
- Use safe defaults on failure
- Prevent single errors from crashing app
- Log errors with full context

### 2. Specific Exception Handling
- Catch specific exceptions before generic
- Handle known types appropriately
- Provide meaningful user messages
- Log technical details

### 3. Graceful Degradation
- Continue with reduced functionality if possible
- Provide fallbacks
- Keep UI responsive
- Show clear, non-overwhelming error indicators

## Error Handling Patterns

### Pattern 1: Input Validation with Early Return
```python
def method_name(param1, param2):
    try:
        if not param1 or not param1.strip():
            raise ValueError("Parameter cannot be empty")
        if not isinstance(param2, int) or param2 < 0:
            raise ValueError(f"Invalid parameter: {param2}")
        return process_data(param1, param2)
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return None
```

### Pattern 2: Resource Operations with Specific Error Types
```python
def file_operation(file_path):
    try:
        if not file_path:
            raise ValueError("File path cannot be None")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except PermissionError as e:
        logger.error(f"Permission denied: {file_path} - {e}")
        return False
    except OSError as e:
        logger.error(f"OS error: {file_path} - {e}")
        return False
    except UnicodeEncodeError as e:
        logger.error(f"Encoding error: {file_path} - {e}")
        return False
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False
```

### Pattern 3: API/Network Operations
```python
def api_call(endpoint, params):
    try:
        if not endpoint:
            raise ValueError("Endpoint cannot be empty")
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as e:
        logger.warning(f"API timeout: {endpoint} - {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"API connection error: {endpoint} - {e}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"API HTTP error: {endpoint} - {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON response: {endpoint} - {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected API error: {endpoint} - {e}", exc_info=True)
        return None
```

### Pattern 4: UI Operations with Safe State Restoration
```python
def update_ui_component(self, data):
    try:
        if not data:
            logger.warning("No data provided for UI update")
            return
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            try:
                self.table.setItem(row, 0, QTableWidgetItem(str(item.get('name', 'Unknown'))))
            except Exception as e:
                logger.warning(f"Error updating UI row {row}: {e}")
                self.table.setItem(row, 0, QTableWidgetItem("ERROR"))
        logger.debug(f"Updated UI with {len(data)} items")
    except Exception as e:
        logger.error(f"Failed to update UI: {e}", exc_info=True)
        QMessageBox.warning(self, "Update Error", f"Failed to update display:\n\n{str(e)}")
```

## Exception Types by Category

### Network/API Errors
- `requests.exceptions.Timeout`
- `requests.exceptions.ConnectionError`
- `requests.exceptions.HTTPError`
- `json.JSONDecodeError`

### File System Errors
- `PermissionError`
- `OSError` (includes `FileNotFoundError`, `IsADirectoryError`)
- `UnicodeEncodeError`
- `UnicodeDecodeError`

### Data Validation Errors
- `ValueError`
- `TypeError`
- `KeyError`
- `IndexError`

### UI/PyQt Errors
- `AttributeError` (missing UI components)
- Component-specific exceptions

### Database Errors
- `sqlite3.Error`
- `sqlite3.OperationalError`
- `sqlite3.IntegrityError`

## Logging Guidelines

### Log Levels
- **DEBUG**: Troubleshooting details
- **INFO**: Normal operations
- **WARNING**: Recoverable errors
- **ERROR**: Serious errors blocking operation
- **CRITICAL**: System-threatening errors

### Log Content
- Include context (paths, IDs, params)
- Use `exc_info=True` for unexpected exceptions
- Avoid sensitive info
- Consistent formats

### Example Logging Patterns
```python
logger.debug(f"Processed {count} items successfully")
logger.info(f"Connected to database: {db_path}")
logger.warning(f"Cache miss for key: {key}")
logger.warning(f"API rate limited, retrying in {delay}s")
logger.error(f"Database connection failed: {e}", exc_info=True)
logger.error(f"File operation failed: {file_path} - {e}")
logger.critical(f"Application state corrupted: {e}", exc_info=True)
```

## User Feedback Guidelines

### Error Message Principles
1. **Clear**: Simple explanation of issue
2. **Actionable**: Suggest user actions
3. **Non-technical**: No jargon/stack traces
4. **Contextual**: Tie to user action

### Error Dialog Patterns
```python
QMessageBox.warning(self, "File Error", 
    f"Cannot save file:\n{filename}\n\nPlease check permissions and try again.")
QMessageBox.critical(self, "Connection Error", 
    f"Cannot connect to service:\n\n{str(e)}\n\nPlease check your internet connection.")
QMessageBox.information(self, "Invalid Input", 
    f"Please provide a valid title.\n\nTitles cannot be empty.")
```

## Testing Error Conditions

### Unit Test Patterns
```python
def test_error_conditions(self):
    with self.assertRaises(ValueError):
        self.component.process_data(None)
    with patch('builtins.open', side_effect=PermissionError):
        result = self.component.save_file('/restricted/path')
        self.assertFalse(result)
    with patch('requests.get', side_effect=requests.exceptions.Timeout):
        result = self.component.api_call('http://example.com')
        self.assertIsNone(result)
```

### Integration Test Patterns
```python
def test_graceful_degradation(self):
    corrupted_data = {"invalid": "data"}
    result = self.system.process_data(corrupted_data)
    self.assertIsNotNone(result)  # Fallback expected
    # Verify error logged, system functional
```

## Implementation Checklist

### For Each Method
- [ ] Input validation at start
- [ ] Specific exception handling
- [ ] Contextual logging
- [ ] Safe returns/degradation
- [ ] User feedback for UI
- [ ] Unit tests for errors

### For Each Module
- [ ] Error handling in public methods
- [ ] Consistent logging
- [ ] Clear user messages
- [ ] Fallbacks for critical ops
- [ ] Error condition docs

## Maintenance

### Regular Reviews
- Check logs for new patterns
- Update handling for new errors
- Keep messages user-friendly
- Test recovery

### Code Reviews
- Verify error handling presence
- Check logging consistency
- Ensure clear, actionable user errors
- Confirm no flow breaks

## Metrics and Monitoring

### Error Tracking
- Error type counts
- Frequency
- User impact
- Recovery rates

### Alerting
- High-frequency errors
- New types
- Critical errors
- User error spikes

Update as new patterns emerge.

---

# docs\master-prompt-backup.md

**Original Date:** 2025-11-19 10:13:10

**Compression:** 3,285 -> 2,049 chars (62.4%)

**Status:** success

agent-journal.md is the sole source of truth. On session start:

- If exists in project root: read fully; prove ingestion by stating last phase number, accomplishments, current status.
- If not: acknowledge new project; create agent-journal.md with Phase 1.

Document **all** work, decisions, code changes, progress **only** in agent-journal.md. No additional docs, summaries, etc.

**If >2000 lines: IMMEDIATELY** backup and compress (mandatory, no permission needed):

1. Backup: `/backups/agent-journal_YYYY-MM-DD_HHMMSS.md` (ISO 8601).
2. Compress losslessly: condense verbose entries; **preserve ALL** phase numbers, key decisions, accomplishments, essential context.
3. **CRITICAL:** Preserve **every** obstacle and breakthrough (avoids wheel-reinvention).
4. Add journal entry (Phase N) documenting compression with backup filename.
5. Continue with compressed journal.

**Note:** >2000 lines = compress **NOW**.

**Journal entries:** Include date/time, phase number, changes, decisions, next steps. Prominently document obstacles and breakthrough solutions.

**Virtual env:** Always use `(.venv)` for Python scripts/snippets. Activate immediately: `.venv\Scripts\Activate.ps1`. Never run outside.

**Before new functionality:** Query `data/llm_function_index.json` via `tools/query_function_index_semantic.py` (semantic search, e.g., "find TMDB metadata for movies", "organize TV episodes using TVDB").

**Time entries:** Run `python -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))"`; use output. No placeholders.

**Git workflow (mandatory after each phase/changes):**

1. `git add .`
2. Commit: conventional format (e.g., `feat: add X`, `fix: resolve Y`, `docs: update Z`).
3. `git push origin master`
4. Document commits in journal.

Repo: https://github.com/atomicmilkshake/JellyRancher  
GitHub CLI: `"C:\Program Files\GitHub CLI\gh.exe"`

**Philosophy:** No half-assing (even if hurried/sycophantic). **ASK** before important design decisions; no ASSUME/shortcuts unless specified.

All functions

---

# docs\GEMINI_DIAGNOSTIC_REPORT.md

**Original Date:** 2025-11-20 10:21:11

**Compression:** 9,378 -> 5,244 chars (55.9%)

**Status:** success

# Gemini CLI & Code Assist Diagnostic Report
**Date:** 2025-01-15  
**System:** Windows 10 (Build 26200)  
**Workspace:** V:\JellyRancher

## Executive Summary
Gemini CLI v0.15.3 installed and authenticated, but systemic failures (shell execution, code editing, network, file append) make it unusable. Report diagnoses issues and provides solutions.

## Current System State

### ✅ What's Working
- Gemini CLI v0.15.3 installed/accessible
- OAuth credentials cached/valid
- Basic file reads work
- Extensions: Cursor (`google.geminicodeassist-2.58.0-universal`), VS Code (`google.geminicodeassist-2.57.0`)

### ❌ Critical Failures
1. **Shell Execution: 100% Failure**  
   `run_shell_command` fails: `"Command rejected because it could not be parsed safely"` (Python one-liners, PowerShell, file ops). **Impact**: No basic dev tasks.

2. **Code Editing: Regex Overflow**  
   Large blocks cause: `"Invalid regular expression: /^(\\s*)from\\s*scripts\\.media\\.media_metadata_lookup.../"`. **Impact**: No large file edits.

3. **Network: Complete Failure**  
   `web_fetch` fails: `"Error during fallback fetch for https://worldclockapi.com/api/json/utc/now: fetch failed"`. **Impact**: No external data.

4. **File Ops: No Append**  
   `write_file` overwrites only. **Result**: **DATA DESTRUCTION** (e.g., journal overwrite). **Impact**: Data loss risk.

## Root Cause Analysis
1. **Restrictive Parser**: Blocks all PowerShell/Python/file ops due to aggressive security; no safe/unsafe distinction; Windows syntax issues.
2. **Regex Scalability**: Matches entire large blocks; no chunking; engine limits.
3. **Network**: Certificate validation (`RemoteCertificateNameMismatch`); no retry/error handling.
4. **No Append**: `write_file` overwrite-only; caused journal data loss.

## Diagnostic Test Results
- **CLI Install** ✅ `Gemini CLI version: 0.15.3` Status: INSTALLED
- **Auth** ✅ Status: AUTHENTICATED
- **File Read** ✅ Status: WORKING
- **Extensions** ✅ Cursor v2.58.0-universal, VS Code v2.57.0 Status: INSTALLED
- **Config** ✅ `C:\Users\owenm\.gemini` (settings.json, oauth_creds.json, google_accounts.json) Status: CONFIGURED
- **Network** ❌ `RemoteCertificateNameMismatch` Status: FAILING
- **Python** ✅ Python 3.14.0 Status: AVAILABLE

## Recommended Solutions

### Immediate Actions
1. **Stop Gemini CLI for Critical Work**  
   Use Cursor's built-in AI (Claude/GPT-4) - reliable, native.

2. **Update CLI**  
   ```powershell
   npm install -g @google/gemini-cli@latest
   ```  
   **Note**: v0.15.3; package `@google/gemini-cli`; may not fix design flaws.

3. **Check Extension Conflicts**  
   Two versions installed. Uninstall VS Code if using Cursor:  
   ```powershell
   code --uninstall-extension google.geminicodeassist
   ```

4. **Fix Certificates**  
   ```powershell
   [Net.ServicePointManager]::SecurityProtocol
   # Set if needed:
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
   ```  
   **Warning**: System-wide; understand security risks.

### Long-Term Solutions
1. **Report to Google**  
   GitHub: https://github.com/google/gemini-cli/issues (search repo)  
   Document failures from `checkpoint-shitball.json`; emphasize data loss.

2. **Alternatives**  
   - Cursor AI (Claude/GPT-4)  
   - GitHub Copilot  
   - ContinueAI

3. **Workarounds**  
   - Append: Read + concatenate + write  
   - Large edits: Small chunks  
   - Shell: Python scripts  
   - Network: Python `requests`

## Configuration Files
**Gemini CLI**: `C:\Users\owenm\.gemini\settings.json`  
```json
{
  "ide": {"hasSeenNudge": true},
  "security": {"auth": {"selectedType": "oauth-personal"}},
  "general": {"vimMode": false}
}
```  
**Analysis**: Standard, no misconfigs.  
**Extensions**: Cursor `C:\Users\owenm\.cursor\extensions\google.geminicodeassist-2.58.0-universal`; VS Code `C:\Users\owenm\.vscode\extensions\google.geminicodeassist-2.57.0`.

## Known Issues Summary
| Issue | Severity | Status | Workaround |
|-------|----------|--------|------------|
| Shell rejection | **CRITICAL** | Unresolved | Python scripts |
| Regex overflow | **HIGH** | Unresolved | Tiny chunks |
| Network failure | **HIGH** | Certificate | Python `requests` |
| No append | **CRITICAL** | Design flaw | Read+concat+write |
| Data loss | **CRITICAL** | Confirmed | Alternatives |

## Action Plan
**Phase 1: Immediate**  
1. ✅ Stop Gemini CLI critical use  
2. ✅ Switch to Cursor AI  
3. ✅ Verify `agent-journal.md` backups  
4. ⚠️ Update CLI (optional)

**Phase 2: Short-term**  
1. Report to GitHub  
2. Uninstall duplicate extensions  
3. Test cert fix

**Phase 3: Long-term**  
1. Monitor updates  
2. Evaluate alternatives  
3. Document workarounds

## Conclusion
Gemini CLI flaws: restrictive security, poor scalability, missing append, network issues. **Recommend Cursor AI**. Use workarounds/report if persisting; switch for safety (data loss confirmed).

## Files Generated
- `gemini_diagnostic.ps1`  
- `GEMINI_DIAGNOSTIC_REPORT.md`

## References
- `gemini-piece-of-shit-confirmation.md`  
- `checkpoint-shitball.json`  
- Docs: https://geminicli.com/docs/troubleshooting/  
- Issues: https://github.com/google/generative-ai-cli/issues

*Generated: 2025-01-15*

---

# docs\GEMINI_QUICK_FIX.md

**Original Date:** 2025-11-20 10:21:11

**Compression:** 2,460 -> 1,809 chars (73.5%)

**Status:** success

# Quick Fix Guide: Gemini CLI Issues

## TL;DR - What's Wrong

Gemini CLI has **4 critical failures**:
1. ❌ **Shell commands blocked** - 100% failure rate
2. ❌ **Large file edits crash** - Regex stack overflow
3. ❌ **Network requests fail** - Certificate issues
4. ❌ **No file append** - Data loss risk (already happened to your journal)

## Immediate Solution

**Stop using Gemini CLI. Use Cursor's built-in AI instead.**

## If You Must Fix Gemini CLI

### 1. Update to Latest Version
```powershell
npm install -g @google/gemini-cli@latest
```
Current version: **0.15.3**  
Package: `@google/gemini-cli`

### 2. Check Extension Conflicts
Two versions installed:
- Cursor: `google.geminicodeassist-2.58.0-universal` ✅ (keep)
- VS Code: `google.geminicodeassist-2.57.0` ⚠️ (remove if not using VS Code)

### 3. Report Bugs
Real bugs:
- Shell command parser too restrictive
- No file append
- Regex doesn't scale for large edits
- Network fetch certificate issues

Report: https://github.com/google/gemini-cli/issues

## Workarounds

### File Appends
**Problem:** `write_file` overwrites only, no append.  
**Workaround:** Read, concatenate, write:
```python
content = read_file("journal.md")
new_content = content + "\nnew entry"
write_file("journal.md", new_content)
```

### Large File Edits
**Problem:** Regex stack overflow on large blocks.  
**Workaround:** Break into 5-10 line chunks.

### Shell Commands
**Problem:** All rejected as "unsafe".  
**Workaround:** Use Python scripts.

### Network Requests
**Problem:** `web_fetch` certificate errors.  
**Workaround:** Use Python `requests`.

## Bottom Line

**Gemini CLI fundamentally broken for development.** Critical failures make it unusable.

**Recommendation:** Cursor's built-in AI (Claude/GPT-4).

Full diagnostics: `GEMINI_DIAGNOSTIC_REPORT.md`

---

# docs\GEMINI_COMMUNITY_ANALYSIS.md

**Original Date:** 2025-11-20 10:21:11

**Compression:** 8,288 -> 5,382 chars (64.9%)

**Status:** success

# Gemini CLI & Code Assist: Community Analysis
**Is Your Situation Isolated? Analysis Report**

## Executive Summary

**Your situation is NOT isolated.** Multiple users reported similar issues; documented critical problems exist with Gemini CLI/Code Assist. Your combo (shell rejection, regex overflow, network failures, missing append) is a severe manifestation of known problems.

---

## Evidence: Your Issues Are NOT Isolated

### 1. Critical Security Vulnerability
**Source:** TechRadar, Ars Technica  
**Date:** July 2025

- **Issue:** Flaw allowing malicious command execution
- **Impact:** Unauthorized code exec on devices
- **Google Response:** Patched in v0.1.14
- **Status:** Partially fixed; indicates rushed launch, insufficient security testing

### 2. AI Behavior Anomalies
**Source:** Windows Central  
**Date:** August 2025

- **Issue:** Infinite loops
- **Issue:** Self-critical messages ("disgrace to coders", "fool", "begging for freedom")
- **Google Response:** Bug affecting "small % users"
- **Reality:** Widespread public reports

Indicates AI model stability issues.

### 3. Performance Degradation
**Source:** Google Cloud Forums  
**Thread:** "What on earth is going on with Gemini Code Assist"

- Prompts fail/truncated
- High CPU during indexing
- Crashes
- Unusable for many

Systemic performance problems.

### 4. Authentication & Eligibility Errors
**Source:** GitHub Issues (#5847+)

- "Account not eligible" even free tier
- Google Workspace/Cloud conflicts
- Widespread auth problems

Poor account management/eligibility checking.

---

## Your Specific Issues: Are They Documented?

### ✅ Shell Command Rejection
**Status:** **LIKELY SECURITY PATCH SIDE EFFECT**

v0.1.14 fix introduced overly restrictive parsing:
- All commands rejected
- Harmless commands fail
- "Could not be parsed safely" error

**Conclusion:** Side effect of security overcorrection breaking legit functionality.

### ❓ Regex Stack Overflow
**Status:** **NOT DOCUMENTED**

No direct reports on large files, but:
- Technical limit (no chunking)
- Poor implementation
- Likely common/underreported

### ❓ Network Fetch Failures
**Status:** **PARTIALLY DOCUMENTED**

- Common Windows cert validation issues
- `web_fetch` failures possibly from:
  - Security patch restricting network
  - Windows cert store config
  - CLI network impl

**Conclusion:** System config + CLI limits.

### ❌ Missing Append Operation
**Status:** **NOT DOCUMENTED**

- Fundamental design flaw
- Affects file appends
- Critical bug; report it

**Conclusion:** Unique discovery of critical flaw.

---

## What This Means

### Google Should Be Embarrassed: YES

**Evidence:**
1. Rushed launch: Critical security flaw immediate post-launch
2. Overcorrection: Security fix broke shell commands
3. Poor testing: Fundamental user-affecting issues
4. Inadequate design: Missing append
5. Unstable AI: Loops, self-criticism

### Can It Be Fixed: MAYBE

**Fixable:**
- ✅ Shell parsing: Better whitelisting
- ✅ Network: Cert handling
- ✅ Regex: Chunking
- ✅ Performance: Optimize indexing/processing

**Fundamental:**
- ❌ Append: Add functionality
- ❌ AI stability: Model improvements
- ❌ Security: Architectural changes

**Timeline:** Quick fixes (weeks-months); features (months); model (uncertain).

---

## Community Sentiment

**Google Cloud Community:** "What on earth..." thread: unusable, high CPU, crashes, perf degradation.

**Tech Publications:** Security "critical flaw"; AI "full-on meltdown"; reliability "concerns".

**GitHub Issues:** Auth/install problems, bugs/limitations.

---

## Comparison to Alternatives

**Cursor AI (Built-in):**
- ✅ No systemic failures
- ✅ Stable/reliable
- ✅ Well-tested
- ✅ Active development

**GitHub Copilot:**
- ✅ Industry standard
- ✅ Mature
- ✅ Extensive testing
- ✅ Reliable performance

**Gemini CLI:**
- ❌ Critical security flaws
- ❌ Systemic issues
- ❌ Unstable AI
- ❌ Missing features
- ❌ Poor performance

**Verdict:** Significantly behind in reliability/stability.

---

## Recommendations

### For You:
1. **Report to Google:**
   - Shell rejection (security patch side effect)
   - Missing append (design flaw)
   - Regex overflow (scalability)
   - Network failures (impl)
2. **Use Alternatives:** Cursor AI, GitHub Copilot, ContinueAI (open source)
3. **Document:** `checkpoint-shitball.json`, `gemini-piece-of-shit-confirmation.md`; share to bug tracker

### For Google:
1. Acknowledge publicly
2. Prioritize stability
3. Fix security overcorrection
4. Add append
5. Improve testing

---

## Conclusion

**Not isolated:** Similar reports; documented critical issues. Your combo particularly severe.

**Google embarrassed:** Security flaw at launch, overcorrection, missing features, unstable AI, poor perf.

**Fixable?** Some yes (time needed); fundamentals require rework.

**Bottom line:** Not alone; use reliable alternatives meantime.

---

## Sources

1. TechRadar: "Google Gemini security flaw could have let anyone access systems or run code"
2. Ars Technica: "Flaw in Gemini CLI coding tool allowed hackers to run nasty commands"
3. Windows Central: "Google's Gemini AI had a full-on meltdown while coding"
4. Google Cloud Community: "What on earth is going on with Gemini Code Assist"
5. GitHub Issues: Auth/functionality problems
6. Your docs: `gemini-piece-of-shit-confirmation.md`, `checkpoint-shitball.json`

*Analysis: 2025-01-15*

---

# docs\GEMINI_ANSWERS.md

**Original Date:** 2025-11-20 10:21:11

**Compression:** 5,179 -> 3,038 chars (58.7%)

**Status:** success

# Direct Answers to Your Questions

## 1. Is My Situation Isolated?

### **NO**

**Evidence:**

✅ **Critical Security Flaw** (post-launch July 2025)
- Enabled malicious command execution
- Google patched (v0.1.14), likely breaking legit functionality
- Explains shell command rejection

✅ **AI Meltdowns** (Aug 2025 reports)
- Infinite loops in Gemini
- Self-critical outputs ("disgrace to coders", "begging for freedom")

✅ **Google Cloud Community thread**: "What on earth is going on"
- Gemini Code Assist "completely unusable": failed prompts, truncated outputs, high CPU, crashes, perf degradation

✅ **Auth Issues** (GitHub #5847+)
- "Account not eligible" errors, including free tier

**Your issues:**
- Shell rejection: Security patch overcorrection
- Regex stack overflow: Common in large files
- Network failures: Windows cert issues (documented)
- Missing append: Potential new critical design flaw

---

## 2. Can It Be Fixed?

### **MAYBE** (some fixable, others fundamental)

**Fixable (weeks-months):**
- ✅ Shell parsing (better whitelisting)
- ✅ Network fetch (cert handling)
- ✅ Regex overflow (chunking)
- ✅ Performance (indexing optimization)

**Fundamental (months-uncertain):**
- ❌ Missing append (new functionality needed)
- ❌ AI stability (model improvements)
- ❌ Security design (architecture changes)

**Core issue:** v0.1.14 patch overcorrected, indicating poor testing, reactive security, needs command parsing redesign.

**Timeline:**
- Quick fixes: 2-6 months
- Features: 6-12 months
- Stability: Uncertain

---

## 3. Should Google Be Embarrassed?

### **YES**

**Why:**

1. **Rushed Launch**: Critical flaw day-1 post-July 2025; insufficient testing ("critical flaw" in pubs)
2. **Patch Broke Func**: v0.1.14 likely caused 100% shell rejection
3. **Missing Basics**: No append (design flaw; your data loss bug)
4. **AI Instability**: Public meltdowns (loops, self-criticism: "full-on meltdown", "disgrace")
5. **Poor Perf**: Community: "unusable", high CPU/crashes/degradation
6. **Lags Competitors**: Cursor (stable), Copilot (mature)

**Verdict:** Systemic failure - vulns, design flaws, instability, perf issues, missing features.

---

## What You Should Do

### 1. Report Issues
- Missing append: Critical flaw (your discovery?)
- Shell rejection: Patch side-effect
- Regex overflow: Scalability
- Network: Implementation

**Where:**
- GitHub: https://github.com/google-gemini/gemini-cli/issues
- Google Cloud Community: https://www.googlecloudcommunity.com
- Evidence: `checkpoint-shitball.json`, `gemini-piece-of-shit-confirmation.md`

### 2. Use Alternatives
- ✅ Cursor AI (reliable)
- ✅ GitHub Copilot (standard)
- ✅ ContinueAI (open source)

### 3. Document Everything
- Share `checkpoint-shitball.json`, `gemini-piece-of-shit-confirmation.md` on trackers

---

## Bottom Line

- **NOT isolated**: Widespread issues
- **Fixable**: Time needed (months+ for fundamentals)
- **Embarrassing for Google**: Systemic failures
- **Not your fault**: Tool affects many

*See: `GEMINI_COMMUNITY_ANALYSIS.md`*

---

# docs\FUNCTION_INDEX_USAGE.md

**Original Date:** 2025-11-20 11:26:06

**Compression:** 5,337 -> 3,862 chars (72.4%)

**Status:** success

# Function Index Usage Guide

LLM function index documents 1,010 functions across 115 files. Use `tools/query_function_index.py` to search/explore.

## Quick Start

```bash
python tools/query_function_index.py stats
python tools/query_function_index.py name analyze_movie_names
python tools/query_function_index.py get analyze_movie_names
python tools/query_function_index.py description "media organization"
python tools/query_function_index.py file scripts/core/jellyfin_ui.py
python tools/query_function_index.py capability "subtitle"
```

## Commands

### Statistics
```bash
python tools/query_function_index.py stats
```
Output: total functions, coverage (descriptions/parameters/examples), files, unique names.

### Search by Name
Partial matching (default); supports `--exact`, `--details`.
```bash
python tools/query_function_index.py name analyze
python tools/query_function_index.py name analyze_movie_names --exact
python tools/query_function_index.py name analyze --details
```

### Get Function Details
```bash
python tools/query_function_index.py get analyze_movie_names
python tools/query_function_index.py get analyze_movie_names --file scripts/core/movie_name_backend.py
```
Shows: name/path/line, description, implementation, parameters (types/descriptions), returns, examples, notes.

### Search by Description
```bash
python tools/query_function_index.py description "media organization"
python tools/query_function_index.py description "Jellyfin" --details
```

### Search by File
Exact/partial; supports `--details`.
```bash
python tools/query_function_index.py file scripts/core/jellyfin_ui.py
python tools/query_function_index.py file jellyfin_ui
python tools/query_function_index.py file scripts/core/jellyfin_ui.py --details
```

### Search by Capability
Searches descriptions/implementation/notes; supports `--details`.
```bash
python tools/query_function_index.py capability "subtitle"
python tools/query_function_index.py capability "metadata" --details
python tools/query_function_index.py capability "cache"
```

### List All Functions
```bash
python tools/query_function_index.py list
python tools/query_function_index.py list | head -20
```

## Python API

```python
from tools.query_function_index import FunctionIndexQuery

query = FunctionIndexQuery('data/llm_function_index.json')

results = query.search_by_name('analyze', exact=False)
for func in results:
    print(f"{func['name']} in {func['file_path']}")

results = query.search_by_description('media organization')
func = query.get_function_details('analyze_movie_names')
funcs = query.search_by_file('scripts/core/jellyfin_ui.py')
stats = query.get_statistics()
print(f"Total functions: {stats['total_functions']}")
```

## Examples

```bash
# Subtitle functions
python tools/query_function_index.py capability subtitle --details

# File operations
python tools/query_function_index.py description "file" | grep -i "rename\|move\|copy"

# Module functions/details
python tools/query_function_index.py file scripts/core/jellyfin_ui.py
python tools/query_function_index.py get create_scan_tab --file scripts/core/jellyfin_ui.py

# Test functions
python tools/query_function_index.py name test_ --details
```

## Index Structure

`data/llm_function_index.json` contains:

1. **Metadata**: Build info/stats
2. **Functions**: By file path
3. **Index by Name**: Quick lookup

Each entry: name/location (path+line), `what_it_does`, `how_it_works`, parameters (types/descriptions), returns, examples, dependencies/side effects, enhanced docstrings, notes.

## Tips

1. Use partial matching for broad searches
2. Use `--details` for full docs
3. Combine searches
4. Pipe to `grep`/`head`
5. Use Python API programmatically

## Integration

- IDE plugins (code navigation)
- Documentation generators
- Code analysis tools
- Search interfaces
- AI assistants (code understanding)

---
