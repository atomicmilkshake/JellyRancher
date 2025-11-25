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

See `docs/WORKFLOW_SPEC.md` for complete implementation details.

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

## Recent Changes

### November 12, 2025
- ✅ **Git removed** - `.git/`, `.github/`, `.gitignore` deleted
- ✅ **ChromaDB removed** - All semantic search functionality removed (~285MB freed)
- ✅ **Memory tab removed** - GUI reduced from 7 to 6 tabs
- ✅ **Root folder organized** - Moved 46 files to `tools/`, `data/`, `docs/`, `reports/`, `archive/`
- ✅ **Clean root directory** - Only 5 essential files remain in root

See `docs/CLEANUP_GIT_CHROMADB_20251112.md` for details.

---

## Configuration

### Required API Keys
- **TMDB API Key** - https://www.themoviedb.org/settings/api
- **TVDB API Key** - https://thetvdb.com/api-information
- **Anthropic API Key** (optional) - For Claude AI integration

Configure in Settings tab or via credential manager.

---

## Troubleshooting

### Common Issues

**Import errors for backend modules:**
- These are runtime-resolved from the `scripts/` directory
- Ensure virtual environment is activated
- Check `sys.path` modifications in main files

**GUI doesn't launch:**
- Check Python version (3.12+ required)
- Verify PyQt5 is installed: `pip list | Select-String pyqt5`
- Check logs in `logs/` directory

**API rate limits:**
- TMDB: 40 requests per 10 seconds
- TVDB: Check current limits
- Rate limiting is built-in via `tenacity` + `ratelimit`

See `docs/COMMON_PITFALLS.md` for more troubleshooting tips.

---

## Contributing

This is a personal project, but suggestions are welcome via issues.

---

## License

Personal Use Only

---

## Credits

**Developer:** JellyRancher Project  
**AI Assistance:** Claude (Anthropic)  
**Inspired By:** Jellyfin media server ecosystem

---

## Support

For issues or questions:
1. Check `docs/` directory for detailed guides
2. Review `docs/COMMON_PITFALLS.md` for known issues
3. Check logs in `logs/` directory
4. Review audit trail in `audit-logs/`

---

**Last Updated:** November 12, 2025  
**Status:** Active Development (PyQt6 migration in progress)
