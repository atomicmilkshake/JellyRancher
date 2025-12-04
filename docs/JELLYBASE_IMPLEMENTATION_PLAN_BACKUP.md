# JellyBase: Comprehensive Jellyfin Library Management Tool - Implementation Plan

**Version:** 1.0  
**Date:** 2025-12-02  
**Status:** Planning Complete - Ready for Implementation

---

## Executive Summary

Transform the existing Jellyfin validation tools (`validate_jellyfin_files.py`, `remove_jellyfin_duplicates.py`, `jellyfin_cleanup_view.py`) into "JellyBase" - a comprehensive library management tool integrated into JellyRancher Studio. JellyBase provides complete visibility and control over the Jellyfin library through a unified UI, including validation, bulk operations, collection management, and metadata editing.

**Key Decision:** No need for Jellyfin server/client repo code - REST API is sufficient for all planned features.

---

## Current State

### Existing Tools
- **Command-line tools:**
  - `validate_jellyfin_files.py` - Validates Jellyfin entries point to real files
  - `remove_jellyfin_duplicates.py` - Finds duplicate entries (case-sensitive path issues)

- **GUI tool:**
  - `scripts/ui/jellyfin_cleanup_view.py` - Studio tab (Tools → Jellyfin Cleanup)
    - Validation worker
    - Duplicate detection
    - Safe deletion (dry-run mode)
    - CSV export

- **API client:**
  - `scripts/core/jellyfin_client.py` - Comprehensive REST API client
    - Collections: `create_collection()`, `add_to_collection()`, `get_collections()`
    - Items: `get_all_items()`, `get_item_by_id()`, `delete_item()`
    - Metadata: `update_provider_ids()`, `refresh_item()`, `refresh_library()`
    - Libraries: `get_libraries()`, `refresh_library_by_path()`

### Main Window Structure
- `jelly_rancher_studio.py` - Main application window
  - Welcome Screen (when no Round-Up open)
  - Workspace (when Round-Up open):
    - Left sidebar: Round-Up Explorer (8-step workflow)
    - Center: TabWidget with workflow tabs (Scan, Scan Results, Analysis, Review, Execution, Subtitles)

---

## UI Restructuring (Critical First Step)

### Main Window Restructure
**File:** `jelly_rancher_studio.py`

**Changes:**
1. Add top-level QTabWidget with two tabs:
   - **"JellyRancher" Tab:** Contains existing workspace (splitter with Round-Up Explorer + workflow tabs)
   - **"JellyBase" Tab:** Contains new JellyBase library management tool

2. Restructure `_create_main_layout()`:
   - Top-level tab widget wraps both JellyRancher workspace and JellyBase view
   - Welcome Screen still shows when no Round-Up is open (above top-level tabs)
   - Maintain all existing JellyRancher functionality

3. Remove Tools menu item for Jellyfin Cleanup (now accessible via JellyBase tab)

**Implementation Notes:**
- Welcome Screen should remain accessible (shown when no Round-Up is open)
- All existing JellyRancher workflow functionality must be preserved
- Top-level tabs should be clearly labeled and accessible

---

## Phase 1: Enhance Existing Validation (A)

### 1.1 Enhanced Validation Checks
**File:** `scripts/core/jellyfin_validator.py` (new module)

**Features:**
- **Metadata validation:**
  - Missing ProviderIds (TMDb, TVDb, IMDb)
  - Incomplete metadata (missing year, genre, description)
  - Invalid metadata formats

- **Quality checks:**
  - Resolution analysis (720p, 1080p, 4K)
  - Codec detection (H.264, HEVC, etc.)
  - Bitrate analysis
  - Container format validation

- **Subtitle coverage validation:**
  - Missing subtitle languages
  - Language code validation
  - External vs embedded subtitle detection

- **Duplicate content detection:**
  - Hash-based duplicate detection (BLAKE3)
  - Not just path-based (case sensitivity)
  - Content comparison for true duplicates

- **Orphan detection:**
  - Files on disk not in Jellyfin
  - Cross-reference with filesystem scans
  - Integration with JellyRancher's file scanner

**Implementation:**
- Reuse existing `FileScanner` for filesystem operations
- Use `JellyfinClient` for library queries
- Leverage existing BLAKE3 hashing from `TransactionManager`

### 1.2 Improved Reporting
**File:** `scripts/ui/jellybase_view.py` (will be created from cleanup_view)

**Features:**
- **Statistics dashboard:**
  - Total items (by type: Movie, Episode, Series)
  - Items by library
  - Validation status overview (valid/invalid/missing/duplicate counts)
  - Recent additions/changes
  - Quick actions panel

- **Export options:**
  - JSON export (full data)
  - CSV export (filtered results)
  - HTML report (formatted, printable)

- **Validation history/trends:**
  - Track validation runs over time
  - Trend analysis (improving/degrading library health)
  - Historical comparison

- **Severity levels:**
  - Critical (missing files, corruption)
  - Warning (missing metadata, low quality)
  - Info (minor issues, suggestions)

---

## Phase 2: Add New Features (B)

### 2.1 Item Management API Methods
**File:** `scripts/core/jellyfin_client.py`

**New Methods:**
- `add_item_by_path(path: str) -> bool`
  - Trigger scan of new path to add items
  - Uses `refresh_library_by_path()` or `Library/Media/Updated` endpoint
  - Returns success status

- `remove_from_collection(collection_id: str, item_ids: List[str]) -> bool`
  - Remove items from existing collection
  - Uses `DELETE /Collections/{id}/Items` endpoint
  - Batch operation support

- `update_item_metadata(item_id: str, metadata: Dict) -> bool`
  - Update item metadata (title, year, description, tags, etc.)
  - Uses `POST /Items/{id}` endpoint
  - Preserves existing metadata, only updates specified fields

- `get_item_statistics() -> Dict`
  - Get library statistics (counts, sizes, etc.)
  - Aggregates data from `get_all_items()`
  - Returns: total items, by type, by library, total size

- `search_items(query: str, filters: Dict) -> List[Dict]`
  - Advanced search with filters
  - Uses `GET /Search/Hints` or filters `get_all_items()` results
  - Filters: type, genre, year, library, quality, etc.

### 2.2 Collection Management Tools
**File:** `scripts/core/jellyfin_collections.py` (new module)

**Functions:**
- `create_collection_by_genre(genre: str) -> Optional[str]`
  - Auto-group items by genre
  - Finds all items with matching genre
  - Creates collection and adds items
  - Returns collection ID

- `create_collection_by_year(year: int) -> Optional[str]`
  - Group by release year
  - Filters items by `ProductionYear`
  - Creates collection

- `create_collection_by_series(series_name: str) -> Optional[str]`
  - Group TV series episodes
  - Finds all episodes in a series
  - Creates collection for series

- `merge_collections(collection_ids: List[str]) -> bool`
  - Merge multiple collections into one
  - Combines all items from source collections
  - Deletes source collections after merge

- `split_collection(collection_id: str, criteria: Dict) -> bool`
  - Split collection by criteria
  - Criteria: genre, year, series, custom filter
  - Creates new collections for each group

**Implementation Notes:**
- Use existing `JellyfinClient` methods
- Batch operations for performance
- Error handling for partial failures
- Logging for all operations

### 2.3 Batch Operations
**File:** `scripts/core/jellyfin_batch.py` (new module)

**Functions:**
- `batch_add_items(paths: List[str], progress_callback: Callable = None) -> Dict`
  - Batch add items (multiple paths)
  - Triggers library refresh for each path
  - Progress callback for UI updates
  - Returns: success count, failed paths

- `batch_remove_items(item_ids: List[str], dry_run: bool = True) -> Dict`
  - Batch remove items (with confirmation)
  - Dry-run mode by default
  - Preview before execution
  - Returns: items to delete, confirmation required

- `batch_update_metadata(item_ids: List[str], metadata_updates: Dict) -> Dict`
  - Batch update metadata (bulk ProviderId updates)
  - Applies same metadata to multiple items
  - Or applies different metadata per item
  - Returns: success count, failures

- `batch_collection_operations(operations: List[Dict]) -> Dict`
  - Batch collection operations
  - Operations: create, add items, remove items, delete
  - Transaction-like behavior (rollback on failure)
  - Returns: operation results

**Implementation Notes:**
- Use worker threads for long operations
- Progress reporting via signals/callbacks
- Comprehensive error handling
- Dry-run mode for safety

---

## Phase 3: Improve GUI (C)

### 3.1 JellyBase Main View
**File:** `scripts/ui/jellybase_view.py` (rename/expand `jellyfin_cleanup_view.py`)

**Tabbed Interface:**

#### Dashboard Tab
- **Library statistics:**
  - Total items (by type: Movie, Episode, Series)
  - Items by library (pie chart or list)
  - Total library size
  - Recent additions/changes (last 30 days)

- **Validation status overview:**
  - Health score (0-100)
  - Issue counts (critical/warning/info)
  - Quick status indicators

- **Quick actions panel:**
  - "Run Full Validation" button
  - "Refresh Library" button
  - "Add Items" button
  - "View Issues" button

#### Items Tab
- **Comprehensive item table:**
  - All metadata visible (title, year, genre, quality, library, path)
  - Sortable columns
  - Resizable columns
  - Color coding by status

- **Advanced filtering:**
  - Filter by genre, year, quality, library
  - Multi-select filters
  - Search with autocomplete
  - Saved filter presets

- **Multi-select for batch operations:**
  - Checkbox column
  - "Select All" / "Deselect All"
  - "Select Issues Only"
  - Batch action buttons

- **Inline editing:**
  - Edit metadata directly in table
  - Provider ID editing
  - Tag management
  - Save changes button

- **Search with autocomplete:**
  - Real-time search
  - Search by title, genre, year
  - Search history

#### Collections Tab
- **List all collections:**
  - Collection name, item count, type
  - Sortable table
  - Collection preview

- **Create new collection (with wizard):**
  - Step 1: Name and description
  - Step 2: Select items (from Items tab or search)
  - Step 3: Review and create

- **Edit collection:**
  - Add/remove items
  - Rename collection
  - Delete collection
  - Collection statistics

- **Auto-grouping tools:**
  - "Group by Genre" button
  - "Group by Year" button
  - "Group by Series" button
  - "Group by Franchise" button (custom logic)
  - Preview before creating

- **Collection statistics:**
  - Item count
  - Total size
  - Average quality
  - Genre distribution

#### Validation Tab
- **Enhanced validation results:**
  - Filter by issue type (missing, invalid, duplicate, metadata)
  - Severity levels (critical, warning, info)
  - Grouped by issue type
  - Detailed issue descriptions

- **Bulk fix actions:**
  - "Refresh Metadata" for selected items
  - "Remove Duplicates" with preview
  - "Fix Provider IDs" (bulk lookup)
  - "Remove Missing Items" (with confirmation)

- **Validation history:**
  - Previous validation runs
  - Trend graphs
  - Comparison with previous runs

#### Tools Tab
- **Add items:**
  - Path picker (folder selection)
  - "Scan Path" button
  - Progress indicator
  - Results display

- **Remove items:**
  - Select items from Items tab
  - Preview before deletion
  - Dry-run mode
  - Confirmation dialog

- **Refresh library:**
  - "Full Refresh" button
  - "Refresh by Path" (targeted)
  - Progress indicator
  - Status messages

- **Export/import operations:**
  - Export library data (JSON, CSV)
  - Import collection definitions
  - Backup/restore operations

### 3.2 Enhanced UI Features
- **Real-time updates:**
  - Polling every 30 seconds (configurable)
  - Manual refresh button
  - Status indicators

- **Progress indicators:**
  - Progress bars for long operations
  - Estimated time remaining
  - Cancel button for operations

- **Undo/redo:**
  - Operation history
  - Undo last operation
  - Redo support
  - History limit (last 10 operations)

- **Keyboard shortcuts:**
  - Ctrl+F: Search
  - Ctrl+A: Select all
  - Ctrl+D: Deselect all
  - Ctrl+R: Refresh
  - Delete: Remove selected items

- **Dark mode support:**
  - Already exists in JellyRancher
  - Ensure JellyBase follows theme

- **Responsive layout:**
  - Resizable panels
  - Collapsible sections
  - Window size adaptation

---

## Phase 4: Comprehensive JellyBase Tool (D)

### 4.1 Core Architecture
**File:** `scripts/core/jellybase_manager.py` (new module)

**JellyBaseManager Class:**
- **State management:**
  - Current library selection
  - Active filters
  - Selected items
  - Current view state

- **Operation queue:**
  - Queue batch operations
  - Progress tracking
  - Error handling
  - Operation cancellation

- **History/audit log:**
  - All operations logged
  - Timestamps
  - User actions
  - Results

- **Cache management:**
  - Cache library data
  - Invalidation on changes
  - Refresh strategies

**Methods:**
- `load_library_data() -> Dict`
- `apply_filters(filters: Dict) -> List[Dict]`
- `queue_operation(operation: Dict) -> str`
- `get_operation_status(operation_id: str) -> Dict`
- `get_history() -> List[Dict]`

### 4.2 Advanced Features

#### 4.2.1 Smart Grouping
**File:** `scripts/core/jellybase_grouping.py` (new module)

**Functions:**
- `group_by_genre(fuzzy: bool = True) -> List[Dict]`
  - Group by genre with fuzzy matching
  - Handles genre variations (e.g., "Sci-Fi" vs "Science Fiction")
  - Returns collection definitions

- `group_by_series() -> List[Dict]`
  - TV show detection
  - Groups episodes by series
  - Handles specials and movies

- `group_by_franchise() -> List[Dict]`
  - Franchise detection (Marvel, Star Wars, etc.)
  - Uses ProviderIds and metadata
  - Custom franchise definitions

- `group_by_director() -> List[Dict]`
  - Group movies by director
  - Uses metadata director field

- `group_by_actor() -> List[Dict]`
  - Group by actor (optional)
  - Uses metadata cast field

- `apply_custom_grouping_rules(rules: List[Dict]) -> List[Dict]`
  - User-defined grouping rules
  - Rule format: field, operator, value
  - Example: "year >= 2020 AND genre = 'Action'"

**Implementation Notes:**
- Use fuzzy string matching for genre variations
- Leverage ProviderIds for franchise detection
- Cache grouping results
- Preview before creating collections

#### 4.2.2 Metadata Enhancement
**File:** `scripts/core/jellybase_metadata.py` (new module)

**Functions:**
- `bulk_metadata_refresh(item_ids: List[str]) -> Dict`
  - Bulk metadata refresh
  - Triggers Jellyfin refresh for each item
  - Progress tracking
  - Returns: success count, failures

- `fix_missing_provider_ids(item_ids: List[str]) -> Dict`
  - Provider ID correction
  - Uses TMDb/TVDB APIs to find missing IDs
  - Updates Jellyfin items
  - Returns: fixed count

- `bulk_tag_management(item_ids: List[str], tags: List[str], operation: str) -> Dict`
  - Tag management (add/remove tags in bulk)
  - Operations: add, remove, replace
  - Returns: updated count

- `update_custom_metadata_fields(item_ids: List[str], fields: Dict) -> Dict`
  - Custom metadata fields
  - Updates user-defined fields
  - Returns: updated count

**Implementation Notes:**
- Integrate with existing TMDb/TVDB clients
- Rate limiting for API calls
- Batch operations for performance
- Error handling for API failures

#### 4.2.3 Library Analysis
**File:** `scripts/core/jellybase_analyzer.py` (new module)

**Functions:**
- `detect_content_duplicates() -> List[Dict]`
  - Duplicate detection (content-based, not just path)
  - Uses BLAKE3 hashing
  - Compares file hashes
  - Returns: duplicate groups

- `analyze_quality_distribution() -> Dict`
  - Quality analysis
  - Resolution distribution (720p, 1080p, 4K)
  - Codec usage
  - Bitrate analysis
  - Returns: statistics

- `analyze_coverage() -> Dict`
  - Coverage analysis
  - Missing metadata count
  - Missing subtitles count
  - Missing artwork count
  - Returns: coverage percentages

- `calculate_health_score() -> int`
  - Library health score (0-100)
  - Factors:
    - File validity (40%)
    - Metadata completeness (30%)
    - Subtitle coverage (20%)
    - Duplicate count (10%)
  - Returns: score (0-100)

**Implementation Notes:**
- Use existing file scanner for hash calculation
- Cache analysis results
- Incremental updates
- Performance optimization for large libraries

### 4.3 Integration Points
- **Round-Up workflow (optional):**
  - Export Round-Up data to JellyBase
  - Import JellyBase collections to Round-Up
  - Cross-reference Round-Up scans with Jellyfin library

- **Filesystem cross-reference:**
  - Use JellyRancher's file scanner
  - Compare Jellyfin library with filesystem
  - Identify orphans and missing items

---

## Implementation Strategy

### Step 1: UI Restructuring (Critical - Must Do First)
1. Restructure `jelly_rancher_studio.py` to add top-level tabs
2. Move existing workspace into "JellyRancher" tab
3. Create placeholder "JellyBase" tab with existing cleanup view
4. Test that all existing functionality still works
5. Remove Tools menu item for Jellyfin Cleanup

**Estimated Time:** 2-3 hours

### Step 2: Foundation (Phase 1 + 2.1)
1. Create `jellyfin_validator.py` with enhanced checks
2. Expand `jellyfin_client.py` with new API methods
3. Rename/expand cleanup view to JellyBase view
4. Update validation tab with enhanced features

**Estimated Time:** 8-10 hours

### Step 3: Core Features (Phase 2.2 + 2.3)
1. Create collection management module
2. Create batch operations module
3. Add to JellyBase GUI (Collections tab, Tools tab)
4. Implement auto-grouping features

**Estimated Time:** 10-12 hours

### Step 4: GUI Enhancement (Phase 3)
1. Expand JellyBase view with tabbed interface
2. Implement dashboard and statistics
3. Add all tabs (Items, Collections, Validation, Tools)
4. Implement advanced filtering and search

**Estimated Time:** 12-15 hours

### Step 5: Advanced Features (Phase 4)
1. Create JellyBase manager
2. Implement smart grouping
3. Add metadata enhancement tools
4. Add library analysis

**Estimated Time:** 15-20 hours

**Total Estimated Time:** 47-60 hours

---

## Files to Create/Modify

### New Files:
- `scripts/core/jellyfin_validator.py` - Enhanced validation logic (~600 lines)
- `scripts/core/jellyfin_collections.py` - Collection management tools (~400 lines)
- `scripts/core/jellyfin_batch.py` - Batch operations (~500 lines)
- `scripts/core/jellybase_manager.py` - Core manager (~400 lines)
- `scripts/core/jellybase_grouping.py` - Smart grouping (~500 lines)
- `scripts/core/jellybase_metadata.py` - Metadata enhancement (~400 lines)
- `scripts/core/jellybase_analyzer.py` - Library analysis (~600 lines)
- `scripts/ui/jellybase_view.py` - Main GUI (~1500 lines, rename from cleanup_view)

**Total New Code:** ~4,900 lines

### Modified Files:
- `jelly_rancher_studio.py` - **CRITICAL:** Restructure to top-level tabs (~100 lines changed)
- `scripts/core/jellyfin_client.py` - Add new API methods (~200 lines added)
- `validate_jellyfin_files.py` - Use new validator module (~50 lines changed)
- `remove_jellyfin_duplicates.py` - Integrate with JellyBase (~50 lines changed)

**Total Modified Code:** ~400 lines

### Test Files:
- `tests/test_jellyfin_validator.py` - Validation tests (~300 lines)
- `tests/test_jellyfin_collections.py` - Collection tests (~250 lines)
- `tests/test_jellyfin_batch.py` - Batch operation tests (~300 lines)
- `tests/test_jellybase_manager.py` - Manager tests (~200 lines)
- `tests/test_jellybase_grouping.py` - Grouping tests (~250 lines)
- `tests/test_jellybase_metadata.py` - Metadata tests (~200 lines)
- `tests/test_jellybase_analyzer.py` - Analyzer tests (~300 lines)
- `tests/test_jellybase_view.py` - GUI tests (~400 lines)
- `tests/test_main_window_restructure.py` - Test top-level tab structure (~150 lines)

**Total Test Code:** ~2,350 lines

---

## Testing Strategy

### Unit Tests
- Test all new modules independently
- Mock Jellyfin API responses
- Test error handling
- Test edge cases

### Integration Tests
- Test JellyBase with real Jellyfin server
- Test batch operations
- Test collection management
- Test validation workflows

### GUI Tests
- Test tab navigation
- Test filtering and search
- Test batch operations UI
- Test error handling in UI

### End-to-End Tests
- Complete workflow: validation → fix issues → create collections
- Large library performance (5000+ items)
- Error recovery scenarios

---

## Notes and Considerations

### API-Only Approach
- **No need for Jellyfin server/client repo code**
- REST API is comprehensive and sufficient
- All operations available via HTTP requests
- Well-documented endpoints

### Safety Features
- **Dry-run mode by default** for destructive operations
- **Confirmation dialogs** for batch operations
- **Comprehensive logging** for all operations
- **Undo/redo** support where possible

### Performance Considerations
- **Caching** library data to reduce API calls
- **Batch operations** for efficiency
- **Worker threads** for long operations
- **Progress indicators** for user feedback

### Code Quality
- Follow existing codebase patterns
- Comprehensive error handling
- Logging with `logger` (not `print`)
- Type hints and docstrings
- Test coverage for all new code

### Backward Compatibility
- Maintain existing cleanup tools as CLI scripts
- Preserve existing JellyRancher workflow
- No breaking changes to existing functionality

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Enhanced validation module created and tested
- ✅ Validation tab shows statistics dashboard
- ✅ Export options working (JSON, CSV, HTML)

### Phase 2 Complete When:
- ✅ All new API methods implemented and tested
- ✅ Collection management module functional
- ✅ Batch operations module functional
- ✅ Integration with GUI complete

### Phase 3 Complete When:
- ✅ JellyBase view has all 5 tabs (Dashboard, Items, Collections, Validation, Tools)
- ✅ All tabs functional with core features
- ✅ Advanced filtering and search working
- ✅ UI responsive and polished

### Phase 4 Complete When:
- ✅ JellyBase manager operational
- ✅ Smart grouping features working
- ✅ Metadata enhancement tools functional
- ✅ Library analysis and health scoring working

### Project Complete When:
- ✅ All tests passing (100% pass rate)
- ✅ Documentation updated
- ✅ Journal entries complete
- ✅ User can manage entire Jellyfin library through JellyBase

---

## Future Enhancements (Post-Phase 4)

### Potential Additions:
- **Webhook integration** - Real-time updates from Jellyfin
- **Scheduled tasks** - Automated validation, collection updates
- **User management** - Manage Jellyfin users and permissions
- **Playlist management** - Create and manage playlists
- **Statistics and analytics** - Advanced reporting and trends
- **Plugin system** - Extensible architecture for custom features

### Integration Opportunities:
- **Jellyseerr integration** - Media request management
- **Radarr/Sonarr integration** - Automated media acquisition
- **Trakt integration** - Watch history and recommendations

---

## Conclusion

JellyBase will transform JellyRancher from a media organization tool into a comprehensive Jellyfin library management platform. By leveraging the existing REST API and building on current validation tools, we can create a powerful, integrated solution that provides unique value through bulk operations, programmatic automation, and cross-reference with the filesystem.

The implementation is structured in phases to allow incremental development and testing, with the critical UI restructuring as the first step to ensure a solid foundation.

**Ready for implementation.**

