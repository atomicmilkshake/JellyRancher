# JellyBase: Comprehensive Jellyfin Library Management Tool

## Overview

Transform the existing Jellyfin validation tools into "JellyBase" - a comprehensive library management tool. Restructure the main window to have top-level tabs: "JellyRancher" (existing workflow) and "JellyBase" (library management).

## Current State

- **Command-line tools:** `validate_jellyfin_files.py`, `remove_jellyfin_duplicates.py`
- **GUI tool:** `scripts/ui/jellyfin_cleanup_view.py` (currently accessible via Tools menu)
- **API client:** `scripts/core/jellyfin_client.py` (already has collections, delete, refresh methods)
- **Main window:** `jelly_rancher_studio.py` (currently has workspace with Round-Up Explorer + tab widget)

## UI Restructuring (Critical First Step)

### Main Window Restructure

**File:** `jelly_rancher_studio.py`

- Add top-level QTabWidget with two tabs:
- **"JellyRancher" Tab:** Contains existing workspace (splitter with Round-Up Explorer + workflow tabs: Scan, Scan Results, Analysis, Review, Execution, Subtitles)
- **"JellyBase" Tab:** Contains new JellyBase library management tool
- Restructure `_create_main_layout()`:
- Top-level tab widget wraps both JellyRancher workspace and JellyBase view
- Welcome Screen still shows when no Round-Up is open (above top-level tabs)
- Maintain all existing JellyRancher functionality
- Remove Tools menu item for Jellyfin Cleanup (now accessible via JellyBase tab)

## Phase 1: Enhance Existing Validation (A)

### 1.1 Enhanced Validation Checks

**File:** `scripts/core/jellyfin_validator.py` (new module)

- Add metadata validation (missing ProviderIds, incomplete metadata)
- Add quality checks (resolution, codec, bitrate analysis)
- Add subtitle coverage validation (missing languages)
- Add duplicate content detection (hash-based, not just path-based)
- Add orphan detection (files on disk not in Jellyfin)

### 1.2 Improved Reporting

**File:** `scripts/ui/jellybase_view.py` (will be created from cleanup_view)

- Add statistics dashboard (total items, by type, by library)
- Add export options (JSON, CSV, HTML report)
- Add validation history/trends
- Add severity levels (critical, warning, info)

## Phase 2: Add New Features (B)

### 2.1 Item Management API Methods

**File:** `scripts/core/jellyfin_client.py`

- `add_item_by_path(path: str)` - Trigger scan of new path to add items
- `remove_from_collection(collection_id: str, item_ids: List[str])` - Remove items from collection
- `update_item_metadata(item_id: str, metadata: Dict)` - Update item metadata
- `get_item_statistics()` - Get library statistics (counts, sizes, etc.)
- `search_items(query: str, filters: Dict)` - Advanced search with filters

### 2.2 Collection Management Tools

**File:** `scripts/core/jellyfin_collections.py` (new module)

- `create_collection_by_genre(genre: str)` - Auto-group by genre
- `create_collection_by_year(year: int)` - Group by release year
- `create_collection_by_series(series_name: str)` - Group TV series
- `merge_collections(collection_ids: List[str])` - Merge multiple collections
- `split_collection(collection_id: str, criteria: Dict)` - Split collection by criteria

### 2.3 Batch Operations

**File:** `scripts/core/jellyfin_batch.py` (new module)

- Batch add items (multiple paths)
- Batch remove items (with confirmation)
- Batch update metadata (bulk ProviderId updates)
- Batch collection operations

## Phase 3: Improve GUI (C)

### 3.1 JellyBase Main View

**File:** `scripts/ui/jellybase_view.py` (rename/expand `jellyfin_cleanup_view.py`)

- **Dashboard Tab:**
- Library statistics (total items, by type, by library)
- Recent additions/changes
- Validation status overview
- Quick actions panel

- **Items Tab:**
- Comprehensive item table (all metadata visible)
- Advanced filtering (genre, year, quality, library)
- Multi-select for batch operations
- Inline editing (metadata, tags)
- Search with autocomplete

- **Collections Tab:**
- List all collections
- Create new collection (with wizard)
- Edit collection (add/remove items)
- Auto-grouping tools (by genre, year, etc.)
- Collection statistics

- **Validation Tab:**
- Enhanced validation results (from Phase 1)
- Filter by issue type
- Bulk fix actions (refresh metadata, remove duplicates)
- Validation history

- **Tools Tab:**
- Add items (path picker, scan trigger)
- Remove items (with preview)
- Refresh library (full or targeted)
- Export/import operations

### 3.2 Enhanced UI Features

- Real-time updates (polling or WebSocket if available)
- Progress indicators for long operations
- Undo/redo for operations
- Keyboard shortcuts
- Dark mode support (already exists)
- Responsive layout

## Phase 4: Comprehensive JellyBase Tool (D)

### 4.1 Core Architecture

**File:** `scripts/core/jellybase_manager.py` (new module)

- Central manager class for all JellyBase operations
- State management (current library, filters, selections)
- Operation queue (batch operations with progress)
- History/audit log

### 4.2 Advanced Features

#### 4.2.1 Smart Grouping

**File:** `scripts/core/jellybase_grouping.py` (new module)

- Group by genre (with fuzzy matching)
- Group by series (TV show detection)
- Group by franchise (Marvel, Star Wars, etc.)
- Group by director/actor
- Custom grouping rules (user-defined)

#### 4.2.2 Metadata Enhancement

**File:** `scripts/core/jellybase_metadata.py` (new module)

- Bulk metadata refresh
- Provider ID correction (fix missing TMDb/TVDB IDs)
- Tag management (add/remove tags in bulk)
- Custom metadata fields

#### 4.2.3 Library Analysis

**File:** `scripts/core/jellybase_analyzer.py` (new module)

- Duplicate detection (content-based, not just path)
- Quality analysis (resolution distribution, codec usage)
- Coverage analysis (missing metadata, missing subtitles)
- Library health score

### 4.3 Integration Points

- Integrate with existing Round-Up workflow (optional)
- Export/import Round-Up data
- Cross-reference with local filesystem scans

## Implementation Strategy

### Step 1: UI Restructuring (Critical)

1. Restructure `jelly_rancher_studio.py` to add top-level tabs
2. Move existing workspace into "JellyRancher" tab
3. Create placeholder "JellyBase" tab with existing cleanup view
4. Test that all existing functionality still works

### Step 2: Foundation (Phase 1 + 2.1)

1. Create `jellyfin_validator.py` with enhanced checks
2. Expand `jellyfin_client.py` with new API methods
3. Rename/expand cleanup view to JellyBase view

### Step 3: Core Features (Phase 2.2 + 2.3)

1. Create collection management module
2. Create batch operations module
3. Add to JellyBase GUI

### Step 4: GUI Enhancement (Phase 3)

1. Expand JellyBase view with tabbed interface
2. Implement dashboard and statistics
3. Add all tabs (Items, Collections, Validation, Tools)

### Step 5: Advanced Features (Phase 4)

1. Create JellyBase manager
2. Implement smart grouping
3. Add metadata enhancement tools
4. Add library analysis

## Files to Create/Modify

### New Files:

- `scripts/core/jellyfin_validator.py` - Enhanced validation logic
- `scripts/core/jellyfin_collections.py` - Collection management tools
- `scripts/core/jellyfin_batch.py` - Batch operations
- `scripts/core/jellybase_manager.py` - Core manager
- `scripts/core/jellybase_grouping.py` - Smart grouping
- `scripts/core/jellybase_metadata.py` - Metadata enhancement
- `scripts/core/jellybase_analyzer.py` - Library analysis
- `scripts/ui/jellybase_view.py` - Main GUI (rename from cleanup_view)

### Modified Files:

- `jelly_rancher_studio.py` - **CRITICAL:** Restructure to top-level tabs (JellyRancher/JellyBase), remove Tools menu item
- `scripts/core/jellyfin_client.py` - Add new API methods
- `validate_jellyfin_files.py` - Use new validator module
- `remove_jellyfin_duplicates.py` - Integrate with JellyBase

### Tests:

- `tests/test_jellyfin_validator.py` - Validation tests
- `tests/test_jellyfin_collections.py` - Collection tests
- `tests/test_jellybase_manager.py` - Manager tests
- `tests/test_jellybase_view.py` - GUI tests
- `tests/test_main_window_restructure.py` - Test top-level tab structure

## Notes

- **UI Restructuring is the critical first step** - must be done before other phases
- Jellyfin API is comprehensive - no need to clone server repo for basic operations
- All operations should be non-destructive by default (dry-run mode)
- Comprehensive logging for all operations
- Follow existing codebase patterns (error handling, logging, testing)
- Maintain backward compatibility with existing cleanup tools
- Welcome Screen should remain accessible (shown when no Round-Up is open)