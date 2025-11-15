# IDE AI Session Starter

**Paste this at the start of EVERY coding session**

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

Example:
- Migrating jelly_rancher_main.py from PyQt5 to PyQt6
- Implementing Point 1 (folder scanning) of the 9-point workflow
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
- Activate before running: `& V:/JellyRancher/.venv/Scripts/Activate.ps1`

---

## Libraries We're Using

**Core:**
- `PyQt6` - GUI framework
- `tmdbv3api` - TMDB API wrapper
- `tvdb_v4_official` - TVDB API wrapper
- `subliminal` - Multi-provider subtitle downloader
- `rapidfuzz` - Fuzzy string matching
- `tenacity` - Exponential backoff
- `ratelimit` - Rate limiting
- `ffmpeg-python` - Media file analysis
- `send2trash` - Safe file deletion
- `anthropic` - Claude API (or use existing Poe wrapper)

**Built-in (no install):**
- `pathlib`, `shutil`, `hashlib`, `sqlite3`, `json`

**Full list:** See `requirements-jelly-rancher.txt`

---

## What to Build Yourself

❌ **No library exists for:**
1. Transaction log system (atomic file rollback)
2. Jellyfin NFO generation (multi-part episodes)
3. Color-coded action review table (PyQt6)
4. Hierarchical folder overview (custom aggregation)
5. LLM → Metadata pipeline integration

✅ **Use existing libraries for:**
- Rate limiting, API wrappers, subtitle downloads, fuzzy matching, file operations

---

## Project Structure

```
V:/JellyRancher/
├─ docs/                    # Documentation
│  ├─ WORKFLOW_SPEC.md      # 9-point workflow details
│  ├─ ARCHITECTURE.md       # Library choices & design
│  └─ PYQT6_MIGRATION.md    # Migration guide
│
├─ scripts/
│  ├─ core/                 # Business logic
│  │  ├─ scanner.py         # Point 1: Folder scanning
│  │  ├─ metadata.py        # Point 4: TMDB/TVDB
│  │  ├─ executor.py        # Point 7: File ops
│  │  └─ subtitles.py       # Points 8-9
│  │
│  ├─ gui/                  # PyQt6 (to be created)
│  │  ├─ main_window.py
│  │  ├─ action_table.py    # Point 5
│  │  └─ dialogs.py
│  │
│  └─ utils/
│     ├─ transaction_log.py # Point 6
│     ├─ api_client.py      # Rate-limited wrappers
│     └─ logger.py
│
├─ data/                    # Git-ignored
│  ├─ cache/                # API responses
│  ├─ logs/
│  └─ transaction_logs/
│
├─ jelly_rancher_main.py       # Current main file (3568 lines)
├─ launch_gui.py            # Entry point
├─ requirements-jelly-rancher.txt
└─ .venv/                   # Virtual environment (git-ignored!)
```

---

## Migration Status

### ✅ Completed
- Phase 1 cleanup (deleted 114 duplicates, archived 678 legacy files)
- Removed legacy GUIs (CustomTkinter, Tkinter)
- Removed all ChromaDB instances (not using semantic search)
- Created archive: `V:\JellyRancher_Archive\2025-11-12_pre-pyqt6\`

### 🚧 In Progress
- PyQt5 → PyQt6 migration
- Restructuring jelly_rancher_main.py (3568 lines → modular)

### ⏳ Next Steps
- [Update based on current work]

---

## Common Questions to Ask Me

**When stuck:**
1. "How do I combine `tenacity` and `ratelimit` decorators?"
2. "Show PyQt6 table with color-coded rows based on confidence"
3. "How to download forced subtitles with subliminal?"
4. "Parse ffprobe output to detect English subtitle tracks"
5. "Create Jellyfin NFO XML for multi-part episodes"
6. "Build SQLite transaction log for file rollback"

**Architecture:**
1. "Should I use async/await for API calls?"
2. "How to structure PyQt6 GUI with multiple tabs?"
3. "Best way to cache TMDB responses?"
4. "How to test file operations without modifying real files?"

**Debugging:**
1. "Why is my rate limiter not working?"
2. "MD5 hash doesn't match after file move"
3. "FFprobe not detecting subtitle tracks"
4. "PyQt6 table not updating after data change"

---

## Quick Commands

```powershell
# Activate virtual environment
& V:/JellyRancher/.venv/Scripts/Activate.ps1

# Install dependencies
pip install -r requirements-jelly-rancher.txt

# Run GUI
python launch_gui.py

# Run tests
pytest

# Check ffmpeg installed
ffmpeg -version
```

---

## Remember

- **Check documentation** before making architecture decisions
- **Small increments** - test each point before moving to next
- **Always dry-run** before executing file operations
- **Transaction logs** are your safety net
- **Rate limits** are not suggestions
- **The 9-point workflow** is your north star

---

**Now tell me: What are you working on today?**
