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

### Overview
A PyQt6 desktop application that automates the organization, renaming, and metadata enrichment of media libraries to ensure Jellyfin compliance. The application uses LLM-assisted analysis, metadata database queries, and intelligent fuzzy matching to propose safe, reversible file operations.

### Point 1: Multi-Folder Scanning & Inventory
**Goal:** Scan selected folders recursively to obtain a complete file list with metadata enrichment.

**Requirements:**
- Recursive scanning of single or multiple folders
- MD5 hash computation for each file (baseline for verification/duplicates)
- Optional Jellyfin API cross-referencing for existing items
- Extension-based filtering (videos, subtitles, etc.)
- Optional AniList/AniDB metadata enrichment for anime libraries
- Parallelized hashing for performance on large libraries

**Key Data Structure:**
```python
@dataclass
class FileRecord:
    absolute_path: Path
    size_bytes: int
    extension: str
    parent_folder: Path
    md5_hash: str  # For duplicate detection/verification
    scan_timestamp: datetime
    # Jellyfin enrichment fields
    jellyfin_id: Optional[str] = None
    jellyfin_item_type: Optional[str] = None
    jellyfin_library_id: Optional[str] = None
    jellyfin_provider_ids: Optional[Dict[str, str]] = None
    jellyfin_matched: bool = False
```

### Point 2: Structural Summary & Analysis
**Goal:** Provide hierarchical overview of folder structure with statistics and Jellyfin comparison.

**Requirements:**
- Folder-by-folder breakdown with file counts and sizes
- File type distribution analysis
- MD5-based duplicate detection and grouping
- Jellyfin integration status (matched vs unmatched files per folder)
- Playback statistics integration (if Playback Reporting plugin available)
- Visual tree representation of folder hierarchy
- Before/after comparison capability

**Example Output:**
```
Movies/
├── Action (45 videos, 234.5 GB, 38 in Jellyfin, 2 duplicates)
├── Comedy (23 videos, 145.2 GB, 20 in Jellyfin, 0 duplicates)
└── Drama (67 videos, 312.8 GB, 45 in Jellyfin, 5 duplicates)
```

### Point 3: LLM-Assisted Reorganization Analysis
**Goal:** Use reasoning LLM to analyze structure and propose Jellyfin-compliant organization.

**Requirements:**
- Submit folder structure summary to LLM (avoiding file-by-file enumeration)
- Include Jellyfin context (existing items, collections, provider IDs)
- Include MD5 duplicate information for intelligent proposals
- Include playback/watching history data (Trakt integration)
- Generate detected media list (movies/shows with confidence scores)
- Generate reorganization proposal with folder restructuring
- Support API-driven actions (collection creation, etc.)

**LLM Input Structure:**
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

### Point 4: Canonical Metadata Database
**Goal:** Build authoritative metadata database from LLM detections and external APIs.

**Requirements:**
- Query TMDB/TVDB/OMDb for canonical titles, years, episode data
- Cross-reference with Jellyfin provider IDs for consistency
- Handle multi-part episodes (generate NFO files for proper Jellyfin indexing)
- Include artwork integration (Fanart.tv posters/backdrops)
- Include theme songs (Themerr plugin)
- Support duplicate/merge logic (Merge Versions plugin integration)
- Persist canonical database as JSON for reuse

**Canonical Database Structure:**
```json
{
  "movies": [
    {
      "title": "The Matrix",
      "year": 1999,
      "tmdb_id": 603,
      "imdb_id": "tt0133093",
      "poster_path": "/path/to/poster.jpg",
      "llm_detection": {...}
    }
  ],
  "tv_shows": [
    {
      "title": "Breaking Bad",
      "year": 2008,
      "tvdb_id": 81189,
      "tmdb_id": 1396,
      "seasons": [
        {
          "season_number": 1,
          "episodes": [
            {
              "episode_number": 1,
              "title": "Pilot",
              "is_multi_part": false,
              "needs_nfo": false
            }
          ]
        }
      ]
    }
  ],
  "multi_part_episodes": [
    {
      "show_title": "Star Trek: The Next Generation",
      "season": 1,
      "episode": 1,
      "parts": 2,
      "needs_nfo": true
    }
  ]
}
```

### Point 5: Interactive Review Table
**Goal:** Present editable action plan for user approval before execution.

**Requirements:**
- Generate proposed operations from canonical DB and LLM proposals
- Interactive table with columns: Status, Current Path, Proposed Path, Action, Confidence, Notes
- Color-coded confidence levels (Green ≥95%, Yellow 70-94%, Orange manual review, Red error)
- Jellyfin status column (Already in Library, New, Path Mismatch)
- MD5 verification columns (current/proposed hashes)
- Bulk edit capabilities and filtering
- Artwork/theme previews
- Collection/box set suggestions

### Point 6: Safe Execution with Verification
**Goal:** Execute approved reorganization plan with full rollback capability.

**Requirements:**
- Transaction-based operations with MD5 verification
- Pre-operation: Calculate source MD5, log to database
- Post-operation: Verify destination MD5 matches source
- Associated file handling (subtitles follow video files)
- Jellyfin API integration (targeted refreshes, collection creation)
- Automatic artwork/theme downloads
- Change journal with full audit trail
- Rollback capability for failed operations

### Point 7: Subtitle Coverage Analysis
**Goal:** Assess subtitle availability using multiple detection methods.

**Requirements:**
- Local analysis with ffprobe for embedded subtitles
- Jellyfin API validation (GET /Items/{itemId}?Fields=MediaStreams)
- MD5-based subtitle verification
- Language detection and forced subtitle identification
- Integration with Kodi Sync Queue for client validation
- Support for WizdomSubs and other language-specific sources

### Point 8: Automated Subtitle Acquisition
**Goal:** Download missing subtitles with verification and Jellyfin integration.

**Requirements:**
- Multi-provider subtitle search (OpenSubtitles.org/com, Podnapisi, Addic7ed, etc.)
- Hash-based matching for accuracy
- Language preference configuration
- Forced subtitle acquisition
- Post-download API refresh (POST /Items/{itemId}/Refresh)
- MD5 verification of downloaded files
- Integration with Bazarr for enhanced automation

---

## Technology Stack & Dependencies

### Core Framework
- **Python:** 3.12 (with virtual environment in project root)
- **GUI Framework:** PyQt6 (mature, cross-platform, excellent for tables/trees/threading)
- **Database:** SQLite (built-in, transaction logging, metadata cache)
- **Path Handling:** pathlib (modern, cross-platform)

### Metadata & Media Analysis Libraries

#### External APIs
| Library | Purpose | Status | Rate Limits |
|---------|---------|--------|-------------|
| `tmdbv3api` | TMDB API client | ✅ Available | 40 req/10s |
| `tvdb_v4_official` | TVDB API client | ✅ Available | Varies by tier |
| `wikipedia-api` | Wikipedia metadata | ✅ Available | 1 req/2s (conservative) |
| `pymediainfo` | Media file inspection | ✅ Available | N/A |
| `ffmpeg-python` | Embedded subtitle detection | ✅ Available | N/A |

#### Subtitle Management
| Library | Purpose | Status |
|---------|---------|--------|
| `subliminal` | Multi-provider subtitle downloader | ✅ Available |
| `python-opensubtitles` | OpenSubtitles.org API | ✅ Available |

#### LLM Integration
| Library | Purpose | Status |
|---------|---------|--------|
| `anthropic` | Claude API client | ✅ Available |
| `openai` | OpenAI API client | ✅ Available |
| `langchain` | LLM abstraction layer | ✅ Available |

#### Utilities
| Library | Purpose | Status |
|---------|---------|--------|
| `rapidfuzz` | Fast fuzzy string matching | ✅ Available |
| `lxml` | NFO/XML generation | ✅ Available |
| `tenacity` | Exponential backoff retry | ✅ Available |
| `ratelimit` | Rate limiting decorators | ✅ Available |
| `send2trash` | Safe file deletion | ✅ Available |

### Built-in Python Libraries (No Installation Needed)
- `pathlib` - Modern path handling
- `shutil` - File operations
- `hashlib` - MD5 computation
- `sqlite3` - Transaction database
- `json` - Configuration/data persistence
- `xml.etree.ElementTree` - XML manipulation

### Complete requirements.txt
```txt
# Core Framework
PyQt6>=6.6.0

# Metadata APIs
tmdbv3api>=1.9.0
tvdb_v4_official>=1.0.0
wikipedia-api>=0.6.0
pymediainfo>=6.0.0
ffmpeg-python>=0.2.0

# Subtitle Management
subliminal>=2.1.0
python-opensubtitles>=0.2.0

# LLM Integration
anthropic>=0.18.0
openai>=1.0.0
langchain>=0.1.0

# Utilities
rapidfuzz>=3.5.0
lxml>=4.9.0
tenacity>=8.2.0
ratelimit>=2.2.1
send2trash>=1.8.2
```

---

## Component Architecture

### Layer 1: GUI Layer (PyQt6)
- **Folder Selection Widget:** Add/remove folders, initiate scans
- **Review Table Widget:** Color-coded action table with editing capability
- **Progress Monitor:** Real-time operation tracking and logging

### Layer 2: Orchestration Layer
- **Workflow Controller:** Manages the 8-point workflow state machine
- **State Manager:** Tracks current operation state and user progress
- **Transaction Manager:** Coordinates logging and rollback operations

### Layer 3: Business Logic Layer
- **File Scanner:** Recursive directory scanning and inventory generation
- **LLM Analyzer:** Folder structure analysis and reorganization proposals
- **Metadata Matcher:** Query TMDB/TVDB with fuzzy matching
- **Jellyfin Validator:** Naming convention and folder structure enforcement
- **Subtitle Manager:** Detection and acquisition of subtitles
- **File Operations:** Execute moves/renames with integrity verification

### Layer 4: Data Access Layer
- **SQLite Repository:** Transaction logs, metadata cache, master inventory
- **API Clients:** TMDB, TVDB, OpenSubtitles, LLM provider wrappers
- **File System Operations:** Low-level file I/O with error handling

---

## Jellyfin API Integration Strategy

### API Overview
The Jellyfin API is a RESTful HTTP interface that provides complete programmatic access to server functionality. It supports both read operations (getting data) and write operations (modifying library state).

### Key Integration Points by Workflow Step

#### Step 1: Scanning & Inventory
**API Action:** `GET /Items?Recursive=true&IncludeItemTypes=Movie,Episode&Fields=Path,ProviderIds`
- **Purpose:** Cross-reference local files against Jellyfin's existing library
- **Value:** Identifies already-imported media, enriches file records with ProviderIds
- **Implementation:** `JellyfinClient.get_all_items()` builds path-to-item mapping

#### Step 2: Structure Summary
**API Action:** `GET /Views` or `GET /UserViews`
- **Purpose:** Get high-level library structure as Jellyfin sees it
- **Value:** Enables before/after comparison in LLM analysis
- **Implementation:** Include in structure summary sent to LLM

#### Step 3: LLM Analysis
**API Action:** `GET /Items/{itemId}?Fields=ProviderIds`
- **Purpose:** Include existing metadata in LLM prompt
- **Value:** LLM can leverage canonical TMDb/TVDB IDs instead of guessing
- **Implementation:** Include ProviderIds in folder structure summary

#### Step 4: Metadata Lookup
**API Action:** `POST /Items/{itemId}/Refresh`
- **Purpose:** Test NFO generation with server validation
- **Value:** Verify multi-part episode handling works correctly
- **Implementation:** Sample validation during canonical DB building

#### Step 5: Action Review
**API Action:** Uses data from Step 1
- **Purpose:** Display Jellyfin status in review table
- **Value:** Clear indication of what will happen (Already in Library, New, Path Mismatch)
- **Implementation:** Add "Jellyfin Status" column to review table

#### Step 6: Execution
**API Actions:**
- `POST /Libraries/{libraryId}/Refresh` - Trigger library scan after moves
- `POST /Collections/{collectionId}/Items` - Create/populate collections
- `POST /Items/{itemId}/Refresh` - Targeted refresh for specific items
- **Purpose:** Update Jellyfin state immediately after file operations
- **Value:** Changes appear instantly instead of waiting for scheduled scans

#### Step 7: Subtitle Analysis
**API Action:** `GET /Items/{itemId}?Fields=MediaStreams`
- **Purpose:** Server-side validation of subtitle tracks
- **Value:** More reliable than local ffprobe, confirms Jellyfin's view
- **Implementation:** Cross-reference with local subtitle detection

#### Step 8: Subtitle Acquisition
**API Action:** `POST /Items/{itemId}/Refresh`
- **Purpose:** Make Jellyfin recognize newly downloaded subtitles
- **Value:** Subtitles become available immediately for playback

### Remote Access
- **Server Address:** `http://localhost:8096` or `https://domain.com`
- **Authentication:** API key from Jellyfin Dashboard (Admin > Advanced > API Keys)
- **Network Requirements:** HTTP/HTTPS access to server
- **Benefits:** Works with remote Jellyfin servers, full functionality available

### Recommended Integration Approach
1. **Phase 1 (Read-Only):** Gather Jellyfin context before LLM analysis
2. **Phase 2 (Read-Write):** Use API to update state after file operations

---

## Workflow State Machine

**Complete 8-Point Workflow:**

1. **Folder Selection** → User selects scan targets
2. **File Scanning** → Build master inventory with metadata
3. **Hierarchy Generation** → Create folder structure overview
4. **LLM Analysis** → Generate reorganization proposal + detected media
5. **Metadata Querying** → Build canonical database from external APIs
6. **Operation Planning** → Generate editable review table
7. **User Review & Approval** → Manual review and bulk edits
8. **Transaction Snapshot** → Pre-execution backup
9. **File Operations** → Execute with MD5 verification
10. **Subtitle Detection** → Analyze coverage locally + via API
11. **Subtitle Acquisition** → Download missing subtitles
**Final:** Complete / Rollback Available

---

## Data Models

### FileRecord (Master Inventory)
```python
@dataclass
class FileRecord:
    absolute_path: Path
    size_bytes: int
    extension: str
    parent_folder: Path
    md5_hash: str
    scan_timestamp: datetime
    # Jellyfin enrichment
    jellyfin_id: Optional[str] = None
    jellyfin_item_type: Optional[str] = None
    jellyfin_library_id: Optional[str] = None
    jellyfin_provider_ids: Optional[Dict[str, str]] = None
    jellyfin_matched: bool = False
```

### Media Metadata
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

### Proposed Operation
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

### Transaction Log Schema
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    transaction_batch_id TEXT,
    timestamp DATETIME,
    operation_type TEXT, -- 'move', 'rename', 'nfo_create', 'delete'
    source_path TEXT,
    destination_path TEXT,
    source_md5 TEXT,
    destination_md5 TEXT,
    status TEXT, -- 'pending', 'completed', 'failed', 'rolled_back'
    error_message TEXT,
    jellyfin_item_id TEXT,
    user_notes TEXT
);
```

---

## Implementation Status Assessment

### Point 1: Scanning & Inventory
**✅ Implemented:**
- Multi-folder recursive scanning (`FileScanner.scan_folder()`)
- Persistent inventory storage (`InventoryRepository.add_file_records()`)
- Extension-based filtering
- Jellyfin cross-referencing with ProviderIds enrichment

**❌ Not Implemented:**
- MD5 baseline hashing during scan (exists in `FileHasher` but not integrated)
- AniList/AniDB scraping during scan
- Parallelized hashing for performance

### Point 2: Structural Summary
**✅ Implemented:**
- Hierarchical folder overview with counts/sizes (`FileScanner.get_folder_structure()`)
- Per-folder Jellyfin match counts
- QTreeWidget visualization in GUI

**❌ Not Implemented:**
- MD5-based duplicate grouping in overview
- Playback statistics integration
- Rich before/after comparison mode

### Point 3: LLM Analysis
**✅ Implemented:**
- Complete LLM analysis pipeline (`LLMAnalysisWorker`, `LLMStructureAnalyzer`)
- Structure-to-LLM conversion avoiding file enumeration
- Detected media + reorganization proposal output
- GUI integration with results display

**❌ Not Implemented:**
- MD5 duplicate context in LLM prompts
- Trakt/Ani-Sync watch history integration
- Direct API automation from LLM suggestions

### Point 4: Canonical Metadata
**✅ Implemented:**
- TMDB/TVDB/OMDb lookup pipeline (`MediaMetadataLookup`)
- Canonical database building and persistence
- Multi-part episode detection and tagging

**❌ Not Implemented:**
- NFO file generation for multi-part episodes
- Artwork/theme integration (Fanart.tv, Themerr)
- Advanced duplicate/merge handling
- Robust file-to-metadata mapping

---

## Risk Mitigation & Safety

### Data Loss Prevention
1. **Read-only scanning:** No modifications until user approval
2. **MD5 verification:** Before and after all operations
3. **Transaction logging:** Complete audit trail with rollback capability
4. **Atomic operations:** Use filesystem-level atomic moves where possible
5. **Dry-run mode:** Preview all changes without execution

### API Reliability
1. **Aggressive caching:** Minimize redundant queries (SQLite metadata cache)
2. **Exponential backoff:** Handle rate limit errors gracefully (`tenacity`)
3. **Circuit breaker:** Disable failing providers temporarily
4. **Offline mode:** Allow manual metadata entry if APIs unavailable

### User Experience
1. **Granular control:** Approve operations individually or in bulk
2. **Clear confidence indicators:** Visual color coding + percentage scores
3. **Undo capability:** Full rollback from transaction log
4. **Progress monitoring:** Real-time operation tracking

---

## Open Questions & Future Enhancements

### Design Decisions Needed
1. **LLM Provider Selection:** Claude vs GPT-4 for reasoning tasks (Current: Claude preferred)
2. **Cache Duration:** How long to cache metadata responses (Suggested: 30 days)
3. **Batch Size:** Operations per checkpoint (Suggested: 100)
4. **NFO Strategy:** Generate for all files or only problematic ones (Suggested: selective)

### Future Enhancements
- **Multi-language subtitle support:** Extend beyond English
- **Duplicate management:** Identify and handle duplicate media files
- **Quality upgrade detection:** Flag lower-quality versions when higher quality exists
- **Scheduling:** Automated periodic scans for new media
- **Jellyfin API integration:** Direct library refresh after reorganization
- **Hardware transcoding detection:** Flag files incompatible with user's Jellyfin server
- **Plugin ecosystem:** Install as Jellyfin plugin for real-time hooks
- **Advanced analytics:** Post-reorg dashboards from Playback Reporting plugin

---

## Configuration Management

### User Configuration (data/app_config.json)
```json
{
  "api_keys": {
    "tmdb": "YOUR_TMDB_KEY",
    "tvdb": "YOUR_TVDB_KEY",
    "anthropic": "YOUR_CLAUDE_KEY",
    "opensubtitles_org": {
      "username": "user",
      "password": "pass"
    }
  },
  "preferences": {
    "llm_provider": "anthropic",
    "dry_run_default": true,
    "auto_approve_threshold": 0.95
  },
  "rate_limits": {
    "tmdb": 40,
    "tvdb": 50,
    "wikipedia": 1
  },
  "subtitle_languages": ["eng"],
  "subtitle_forced": true
}
```

---

## Testing Strategy

### Unit Tests
- File scanner accuracy and path handling
- Fuzzy matching threshold validation
- NFO generation correctness
- MD5 calculation and verification
- Transaction rollback completeness

### Integration Tests
- API client mocking and rate limiting
- Database transaction integrity
- End-to-end workflow simulation
- Rollback verification with test media

---

**This consolidated reference serves as the authoritative guide for JellyRancher development. All original source documents remain intact for historical reference.**
