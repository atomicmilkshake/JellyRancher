# Architecture & Design Document
**Project:** Media Library Organizer for Jellyfin  
**Version:** 1.0  
**Last Updated:** November 13, 2025

---

## 1. Overview

A PyQt6 desktop application that automates the organization, renaming, and metadata enrichment of media libraries to ensure Jellyfin compliance. The application uses LLM-assisted analysis, metadata database queries, and intelligent fuzzy matching to propose safe, reversible file operations.

### Core Objectives
- **Safety First**: Transaction-based operations with full rollback capability
- **Jellyfin Compliance**: Enforce official naming conventions and folder structures
- **Intelligence**: LLM-assisted reorganization with metadata validation
- **User Control**: All destructive operations require explicit approval
- **Data Integrity**: MD5 verification for all file operations

---

## 2. Technology Stack

### Core Framework
- **Python**: 3.12
- **GUI Framework**: PyQt6
- **Database**: SQLite (transaction logging, metadata cache)
- **Environment**: Virtual environment in project root

### External Dependencies

#### Metadata & Media Analysis
| Library | Purpose | Status |
|---------|---------|--------|
| `tmdbv3api` | TMDB API wrapper with rate limiting | ✅ Existing |
| `tvdb_v4_official` | TVDB API client | ✅ Existing |
| `wikipedia-api` | Wikipedia metadata queries | ✅ Existing |
| `pymediainfo` | Media file inspection | ✅ Existing |
| `ffmpeg-python` | Media analysis (embedded subtitles) | ✅ Existing |

#### Subtitle Management
| Library | Purpose | Status |
|---------|---------|--------|
| `subliminal` | Multi-source subtitle downloader | ✅ Existing |
| `python-opensubtitles` | OpenSubtitles.org API | ✅ Existing |

#### LLM Integration
| Library | Purpose | Status |
|---------|---------|--------|
| `anthropic` | Claude API client | ✅ Existing |
| `openai` | OpenAI API client | ✅ Existing |
| `langchain` | LLM abstraction layer | ✅ Existing |

#### Utilities
| Library | Purpose | Status |
|---------|---------|--------|
| `rapidfuzz` | Fast fuzzy string matching | ✅ Existing |
| `lxml` | NFO/XML generation | ✅ Existing |
| `pathlib` | Path manipulation | ✅ Standard Library |
| `hashlib` | MD5 checksum calculation | ✅ Standard Library |
| `sqlite3` | Transaction logging | ✅ Standard Library |

---

## 3. Component Architecture

### Layer 1: GUI Layer (PyQt6)
- **Folder Selection Widget**: Add/remove folders, initiate scans
- **Review Table Widget**: Color-coded action table with editing capability
- **Progress Monitor**: Real-time operation tracking and logging

### Layer 2: Orchestration Layer
- **Workflow Controller**: Manages the 10-step workflow state machine
- **State Manager**: Tracks current operation state and user progress
- **Transaction Manager**: Coordinates logging and rollback operations

### Layer 3: Business Logic Layer
- **File Scanner**: Recursive directory scanning and inventory generation
- **LLM Analyzer**: Folder structure analysis and reorganization proposals
- **Metadata Matcher**: Query TMDB/TVDB/Wikipedia with fuzzy matching
- **Jellyfin Validator**: Naming convention and folder structure enforcement
- **Subtitle Manager**: Detection and acquisition of subtitles
- **File Operations**: Execute moves/renames with integrity verification

### Layer 4: Data Access Layer
- **SQLite Repository**: Transaction logs, metadata cache, master inventory
- **API Clients**: TMDB, TVDB, OpenSubtitles, LLM provider wrappers
- **File System Operations**: Low-level file I/O with error handling

---

## 4. Detailed Component Breakdown

### 4.1 File Scanner
**Responsibility**: Recursive directory scanning and inventory generation

**Implementation**:
- Uses `pathlib.Path.rglob()` for recursive scanning
- Generates master file list with absolute paths
- Calculates folder sizes and file type statistics
- **Status**: 🔨 Custom implementation required

---

### 4.2 LLM Analyzer
**Responsibility**: Intelligent folder structure analysis and reorganization proposals

**Implementation**:
- Uses `langchain` for LLM abstraction
- Prompt engineering for:
  - Media type detection (movie vs. TV show)
  - Title extraction from folder names
  - Season/episode structure detection
  - Jellyfin compliance gap analysis
- **Status**: 🔨 Custom implementation required

**Design Considerations**:
- Cache LLM responses to minimize API costs
- Implement retry logic with exponential backoff
- Validate LLM output against expected schema
- Support multiple LLM providers (Claude, GPT-4, etc.)

---

### 4.3 Metadata Matcher
**Responsibility**: Query external databases and fuzzy match media titles

**Implementation**:
- **TMDB**: Use `tmdbv3api` for movies
- **TVDB**: Use `tvdb_v4_official` for TV shows
- **Fuzzy Matching**: `rapidfuzz` for title comparison
- **Caching**: SQLite database for metadata responses
- **Status**: 🔨 Custom orchestration + existing libraries

**Rate Limiting Strategy**:
- TMDB: 40 requests / 10 seconds
- TVDB: Check current tier limits
- Wikipedia: 1 request / 2 seconds (conservative)

**Matching Pipeline**:
1. Exact title match
2. Fuzzy match with threshold ≥ 90%
3. Manual review for threshold 70-89%
4. Flag as unmatched if < 70%

---

### 4.4 Jellyfin Validator
**Responsibility**: Ensure compliance with Jellyfin naming conventions

**Implementation**:
- **Movies**: `Movie Title (Year)/Movie Title (Year).ext`
- **TV Shows**: `Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext`
- **Multi-part episodes**: Generate NFO with `<episodebookmark>` tags
- **Subtitle naming**: `filename.en.srt`, `filename.en.forced.srt`
- **Status**: 🔨 Custom implementation required

**NFO Generation**:
- Use `lxml` for XML generation
- Validate against Jellyfin schema
- Support episode ranges (e.g., S01E01-E02)

---

### 4.5 Transaction Manager
**Responsibility**: Log all operations and enable rollback

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
- Pre-operation: Calculate MD5, log operation
- Post-operation: Verify MD5, update status
- Rollback: Reverse operations in reverse chronological order
- **Status**: 🔨 Custom implementation required

---

### 4.6 File Operations Engine
**Responsibility**: Execute file moves/renames with integrity verification

**Implementation**:
- Use `shutil.move()` for atomic operations
- MD5 verification before and after
- Associated file handling (subtitles, NFO, metadata)
- Collision detection and resolution
- **Status**: 🔨 Custom implementation required

**Error Handling**:
- Log all errors to transaction database
- Skip failed operations, continue processing
- Generate summary report
- Preserve original files until verification complete

---

### 4.7 Subtitle Manager
**Responsibility**: Detect subtitle coverage and acquire missing subtitles

**Implementation**:
- **Detection**: Use `pymediainfo` or `ffmpeg-python` to detect embedded subtitles
- **Acquisition**: Primarily `subliminal` library
- **Fallback chain**: OpenSubtitles.org → OpenSubtitles.com → Podnapisi → Addic7ed → Subscene
- **Hash matching**: Prioritize exact file hash matches
- **Forced subtitles**: Acquire separately from regular subtitles
- **Status**: ✅ Mostly existing (`subliminal`) + minor custom logic

**Configuration Example**:
```
subliminal.download_best_subtitles(
    languages={'eng'},
    providers=['opensubtitles', 'podnapisi', 'addic7ed', 'subscene']
)
```

---

### 4.8 GUI Components

#### Folder Selection Widget
- Add/remove folders
- Display selected folders in list
- "Scan" button to initiate inventory

#### Hierarchical Overview
- Tree view of folder structure
- Display: folder size, file type breakdown
- Expand/collapse navigation

#### Review Table
- **Columns**: Status, Current Path, Proposed Path, Action, Confidence, Notes
- **Color Coding**:
  - 🟢 Green: Auto-safe (≥95% confidence)
  - 🟡 Yellow: Review recommended (70-94% confidence)
  - 🟠 Orange: Manual decision needed (multiple matches)
  - 🔴 Red: Cannot process (no match)
  - 🔵 Blue: No action needed (already compliant)
- Editable cells for manual overrides
- Filter/sort capabilities

#### Progress Monitor
- Real-time progress bar
- Current operation display
- Success/failure counters
- Log output window

**Status**: 🔨 Custom implementation required

---

## 5. Workflow State Machine

**Step 1**: Folder Selection  
**Step 2**: File Scanning → Master Inventory (SQLite)  
**Step 3**: Hierarchy Generation  
**Step 4**: LLM Analysis → Reorganization Proposal  
**Step 5**: Metadata Querying → Canonical Database  
**Step 6**: Operation Planning → Editable Review Table  
**Step 7**: User Review & Approval  
**Step 8**: Transaction Snapshot  
**Step 9**: File Operations → MD5 Verification  
**Step 10**: Subtitle Detection  
**Step 11**: Subtitle Acquisition  
**Final**: Complete / Rollback Available  

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
1. **Read-only scanning**: No modifications until user approval
2. **MD5 verification**: Before and after all operations
3. **Transaction logging**: Complete audit trail
4. **Atomic operations**: Use filesystem-level atomic moves when possible
5. **Rollback capability**: Full restoration from transaction log

### API Reliability
1. **Aggressive caching**: Minimize redundant queries
2. **Exponential backoff**: Handle rate limit errors gracefully
3. **Circuit breaker**: Disable failing providers temporarily
4. **Offline mode**: Allow manual metadata entry if APIs unavailable

### User Experience
1. **Dry run mode**: Preview all changes without execution
2. **Granular control**: Approve operations individually or in bulk
3. **Clear confidence indicators**: Visual color coding + percentage
4. **Undo capability**: Rollback executed operations

---

## 8. Implementation Phases

### Phase 1: Foundation
- [ ] Virtual environment setup
- [ ] PyQt6 GUI skeleton
- [ ] File scanner implementation
- [ ] SQLite schema creation

### Phase 2: Intelligence Layer
- [ ] LLM integration (folder analysis)
- [ ] Metadata API clients (TMDB, TVDB)
- [ ] Fuzzy matching logic
- [ ] Confidence scoring algorithm

### Phase 3: Jellyfin Compliance
- [ ] Naming convention validators
- [ ] NFO generation (including multi-part episodes)
- [ ] Folder structure enforcement

### Phase 4: Operations
- [ ] Transaction manager
- [ ] File operations engine with MD5 verification
- [ ] Rollback mechanism
- [ ] Associated file handling (subtitles)

### Phase 5: Subtitles
- [ ] Subtitle detection (embedded + external)
- [ ] Subliminal integration
- [ ] Forced subtitle acquisition

### Phase 6: Polish
- [ ] Comprehensive error handling
- [ ] Progress monitoring
- [ ] Summary reports
- [ ] User documentation

---

## 9. Configuration Management

### User Configuration File (config.yaml)
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
  tmdb: 40  # requests per 10 seconds
  tvdb: 50
  wikipedia: 1  # requests per 2 seconds
  
subtitle_languages: ["eng"]
subtitle_forced: true
```

---

## 10. Testing Strategy

### Unit Tests
- File scanner accuracy
- Fuzzy matching threshold validation
- NFO generation correctness
- MD5 calculation and verification

### Integration Tests
- API client mocking
- Database transaction integrity
- Rollback completeness

### End-to-End Tests
- Full workflow simulation with test media library
- Dry run validation
- Rollback verification

---

## 11. Open Questions & Design Decisions

1. **LLM Provider**: Claude vs GPT-4? (Recommend Claude for reasoning tasks)
2. **Cache Duration**: How long to cache metadata responses? (Suggest 30 days)
3. **Batch Size**: How many files to process before checkpointing? (Suggest 100)
4. **NFO Strategy**: Generate for all files or only problematic ones? (Suggest selective)
5. **Duplicate Detection**: MD5 matching to identify duplicate files? (Defer to Phase 2)

---

## 12. Future Enhancements

- **Multi-language support**: Extend subtitle acquisition beyond English
- **Duplicate management**: Identify and handle duplicate media files
- **Quality upgrade detection**: Flag lower-quality versions when higher quality exists
- **Scheduling**: Automated periodic scans for new media
- **Jellyfin API integration**: Direct library refresh after reorganization
- **Hardware transcoding detection**: Flag files incompatible with user's Jellyfin server