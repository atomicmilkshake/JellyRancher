# Implementation Plan: LLM Prompt Generation Optimization

**Created:** 2025-12-10
**Status:** ✅ IMPLEMENTATION COMPLETE - Ready for Production
**Priority:** High (blocking context limits) - RESOLVED
**Completion Date:** 2025-12-10

---

## Table of Contents
1. [Project Context](#project-context)
2. [Problem Statement](#problem-statement)
3. [Requirements](#requirements)
4. [Technical Analysis](#technical-analysis)
5. [Implementation Plan](#implementation-plan)
6. [Testing Strategy](#testing-strategy)
7. [Success Criteria](#success-criteria)

---

## Project Context

**JellyRancher** is a media library organization tool for Jellyfin media servers. It uses LLM analysis to intelligently organize movies and TV shows into Jellyfin-compliant folder structures.

### Current Workflow (8 Steps)
1. **Scan Folders** - Inventory media files
2. **Structure Summary** - Pre-analysis filtering
3. **LLM Analysis** - AI-powered media detection and organization suggestions (THIS TASK)
4. **Canonical Database** - TMDB/TVDB metadata
5. **Review Table** - User approval
6. **Execute Operations** - File moves with rollback
7. **Subtitle Audit** - Coverage analysis
8. **Subtitle Downloads** - Fetch missing subtitles

### System Architecture
```
FileScanner (file_scanner.py)
    ↓ (absolute paths, file records)
LLMAnalysisWorker (workers.py)
    ↓ (_build_structure_summary)
LLMStructureAnalyzer (llm_structure_analyzer.py)
    ↓ (_build_tree_prompt) ← **TARGET OF THIS REFACTOR**
    ↓ (sends prompt to LLM)
LLM API (OpenAI/Anthropic/etc)
    ↓ (returns JSON)
_parse_llm_response()
    ↓ (parsed reorganization plan)
File operations executor
```

---

## Problem Statement

### Current Issue
The LLM prompt generator (`_build_tree_prompt()` in `llm_structure_analyzer.py`) produces **1000+ line prompts** for typical media libraries, causing:
- **Context token limit exhaustion** (hitting API limits)
- **Increased API costs** (paying for redundant tokens)
- **Slower response times** (more tokens = longer processing)

### Root Causes of Verbosity

**Example from test-prompt.txt (lines 800-900):**

1. **Full absolute paths repeated everywhere**
   ```
   📁 W:\#MEDIA2\TV Shows\Seinfeld (1989)\Season 1\
   📁 W:\#MEDIA2\TV Shows\Seinfeld (1989)\Season 2\
   📁 W:\#MEDIA2\TV Shows\Seinfeld (1989)\Season 3\
   [... 6 more seasons ...]
   ```

2. **Jellyfin metadata folders listed individually**
   ```
   📁 W:\#MEDIA2\TV Shows\Seinfeld (1989)\Season 1\Seinfeld.S01E01.trickplay\320 - 10x10
   📁 W:\#MEDIA2\TV Shows\Seinfeld (1989)\Season 1\Seinfeld.S01E02.trickplay\320 - 10x10
   📁 W:\#MEDIA2\TV Shows\Seinfeld (1989)\Season 1\Seinfeld.S01E03.trickplay\320 - 10x10
   [... 177 more trickplay folders for each episode ...]
   ```
   - `.trickplay` = Jellyfin-generated thumbnail preview strips (NOT source media)

3. **Individual warning lines**
   ```
   ⚠️ Missing year in folder name: "Movie Title"
   ⚠️ Missing year in folder name: "Another Movie"
   ⚠️ Missing year in folder name: "Yet Another Movie"
   [... 97 more individual warnings ...]
   ```

### Impact Metrics
- **Marvel's Spidey** (1 show, 1 season): 50+ lines (mostly trickplay folders)
- **Seinfeld** (1 show, 9 seasons): 200+ lines (9 season folders + 180 episode trickplay folders)
- **Typical library** (50 movies + 10 TV shows): 1000+ lines

---

## Requirements

### Functional Requirements

**Movies:**
- One line per movie showing: `Movie Title (Year) | Size | Status | Issues`
- Skip `.trickplay` folders entirely
- Group similar issues ("47 movies missing year" instead of 47 individual warnings)

**TV Shows:**
- One line per show: `Show Title (Year-Year) | X seasons, Y episodes | Status | Issues`
- DON'T list individual Season XX folders - aggregate them
- Skip `.trickplay`, `.nfo`, `extrafanart`, `extrathumbs` metadata folders
- Note missing years/structure problems concisely

**Target:** <300 lines for typical library (70% reduction from 1000+)

### Non-Functional Requirements
- **Backward compatibility:** LLM must still be able to parse responses and map back to absolute file paths
- **No data loss:** All relevant information must be preserved in lookup tables
- **Test coverage:** All changes must have corresponding tests

---

## Technical Analysis

### Current Code Location
**File:** `v:\JellyRancher\scripts\media\llm_structure_analyzer.py`
**Lines:** 491-612 (`_build_tree_prompt()` method)

### Current Implementation
```python
def _build_tree_prompt(self, structure_summary: Dict, additional_context: Optional[str] = None) -> str:
    tree_lines = []
    issues_detected = []
    stats = {'folders': 0, 'files': 0, 'total_size': 0}

    # Lines 525-550: Iterates through ALL folder_items and builds individual entries
    for folder_path, folder_data in folder_items:
        stats['folders'] += 1
        folder_path_str = str(folder_path)  # Full absolute path
        tree_lines.append(f"📁 {folder_path_str}")
        tree_lines.append(f"   └─ {len(files)} files | {size_str} | {types_str}")

        # Lines 570-574: Individual warning for EVERY folder
        if some_issue:
            issues_detected.append(f"⚠️ {issue_description}: {folder_path_str}")
```

**Problems:**
- No filtering of metadata folders (`.trickplay`, etc.)
- No TV show aggregation (seasons listed individually)
- No issue grouping (one line per issue)
- Always includes full absolute paths

### LLM Response Parsing (CRITICAL)

**Investigation Result:** Lines 637-716 show LLM returns JSON format:

```json
{
  "detected_media": [
    {"title": "...", "current_location": "...", "type": "movie|tv_show", ...}
  ],
  "reorganization_plan": {
    "folder_changes": [
      {"current_path": "...", "proposed_path": "...", "action": "...", ...}
    ]
  }
}
```

**Key Discovery:** LLM references items from the prompt using `current_location` and `current_path` fields.

**Solution:** Build a title-to-path lookup table during prompt generation:
```python
self.title_to_path_map = {
    "Seinfeld (1989-1998)": Path("W:/MEDIA2/TV Shows/Seinfeld (1989)"),
    "The Godfather (1972)": Path("W:/MEDIA2/Movies/The Godfather 1972")
}
```

When parsing LLM response:
```python
title = response['detected_media'][0]['current_location']  # "Seinfeld (1989-1998)"
absolute_path = self.title_to_path_map.get(title)  # Path("W:/MEDIA2/...")
```

**Important:** `_parse_llm_response()` itself doesn't need changes - it just parses JSON. The CALLER needs to use `title_to_path_map`.

---

## Implementation Plan

### Phase 1: Add Metadata Filtering Helper

**File:** `scripts/media/llm_structure_analyzer.py`
**Location:** Before `_build_tree_prompt()` (around line 490)

```python
def _is_metadata_folder(self, folder_name: str) -> bool:
    """
    Check if folder is Jellyfin/Plex metadata (should be skipped from prompt).

    Args:
        folder_name: Name of the folder to check

    Returns:
        True if folder is metadata, False if it's actual media content
    """
    metadata_patterns = [
        '.trickplay',   # Jellyfin thumbnail preview strips
        '.nfo',         # XML metadata files
        'extrafanart',  # Extra artwork folder
        'extrathumbs'   # Extra thumbnails folder
    ]
    folder_lower = folder_name.lower()
    return any(pattern in folder_lower for pattern in metadata_patterns)
```

### Phase 2: Add TV Show Detection & Aggregation

**File:** `scripts/media/llm_structure_analyzer.py`
**Location:** Before `_build_tree_prompt()`

```python
def _aggregate_tv_show(self, show_folder_path: Path, folder_data: Dict) -> Optional[Dict]:
    """
    Aggregate TV show info from season subfolders.

    Args:
        show_folder_path: Path to the show root folder
        folder_data: Dictionary containing folder structure from FileScanner

    Returns:
        Aggregated show info:
        {
            'title': 'Show Name (2015-2020)',  # Display title with year range
            'seasons': 9,                      # Number of seasons detected
            'episodes': 180,                   # Total episode count
            'total_size': 123456789,           # Total size in bytes
            'issues': ['missing_year', 'incomplete_season_3']  # Aggregated issues
        }

        Returns None if not a TV show folder
    """
    import re

    # Check if this folder contains "Season XX" subfolders
    subfolders = folder_data.get('subfolders', [])
    season_folders = [f for f in subfolders if re.match(r'Season \d+', f, re.IGNORECASE)]

    if len(season_folders) < 1:
        return None  # Not a TV show folder

    # Extract year/year range from folder name
    folder_name = show_folder_path.name
    year_match = re.search(r'\((\d{4})(?:-(\d{4}))?\)', folder_name)
    if year_match:
        year_start = year_match.group(1)
        year_end = year_match.group(2)
        title_with_years = folder_name  # Already has years
    else:
        # Extract just the title
        title = re.sub(r'\s*\(\d{4}.*?\)\s*', '', folder_name).strip()
        title_with_years = title  # No years available

    # Count total episodes across all seasons
    total_episodes = 0
    total_size = 0
    issues = []

    for season_folder in season_folders:
        season_path = show_folder_path / season_folder
        season_data = folder_data.get('seasons', {}).get(season_folder, {})

        # Count video files (episodes)
        video_extensions = ['.mkv', '.mp4', '.avi', '.m4v', '.ts']
        files = season_data.get('files', [])
        episode_count = sum(1 for f in files if any(f.lower().endswith(ext) for ext in video_extensions))
        total_episodes += episode_count

        # Accumulate size
        total_size += season_data.get('size', 0)

        # Check for incomplete seasons (fewer than expected episodes)
        if episode_count < 10:  # Heuristic: most seasons have 10+ episodes
            issues.append(f"Season {season_folder} may be incomplete ({episode_count} episodes)")

    return {
        'title': title_with_years,
        'seasons': len(season_folders),
        'episodes': total_episodes,
        'total_size': total_size,
        'issues': issues
    }
```

### Phase 3: Refactor `_build_tree_prompt()`

**File:** `scripts/media/llm_structure_analyzer.py`
**Lines:** 491-612 (complete rewrite)

**New Logic:**
1. Initialize `self.title_to_path_map = {}` (for LLM response mapping)
2. Separate movies from TV shows in first pass
3. Filter out metadata folders using `_is_metadata_folder()`
4. For TV shows: Aggregate using `_aggregate_tv_show()`, produce one line per show
5. For movies: One line per movie folder
6. **Store title->path mapping**: `self.title_to_path_map[display_title] = absolute_path`
7. Build issue summary at end (counts by category)

**New Output Structure:**
```
=== MEDIA INVENTORY ===

📺 MOVIES (47 items, 234.5 GB)
- Anchorman (2004) | 6.3 GB | ✅ Compliant
- Batman Begins (2005) | 8.1 GB | ⚠️ Missing extras folder
- The Godfather (1972) | 5.2 GB | ✅ Compliant
[... one line per movie ...]

📺 TV SHOWS (12 items, 1.2 TB)
- Seinfeld (1989-1998) | 9 seasons, 180 episodes | ✅ Compliant
- The Office (2005-2013) | 9 seasons, 201 episodes | ⚠️ Season 3 incomplete (19/25 episodes)
- Breaking Bad (2008-2013) | 5 seasons, 62 episodes | ✅ Compliant
[... one line per show ...]

⚠️ ISSUES SUMMARY:
- 5 movies missing year metadata
- 2 TV shows with incomplete seasons
- 8 items with non-standard naming
- 12 items with missing subtitles

=== JELLYFIN COMPLIANCE GUIDELINES ===
• Movies: "Movie Title (Year)/Movie Title (Year).ext"
• TV Shows: "Show Name/Season XX/Show Name - sXXeYY - Episode Title.ext"
• Multi-part episodes: Require NFO files to map parts properly
```

**Implementation Pseudocode:**
```python
def _build_tree_prompt(self, structure_summary: Dict, additional_context: Optional[str] = None) -> str:
    # Initialize title-to-path mapping
    self.title_to_path_map = {}

    # Separate movies and TV shows
    movies = []
    tv_shows = []
    issue_counts = defaultdict(int)

    for folder_path, folder_data in structure_summary.items():
        # Skip metadata folders
        if self._is_metadata_folder(folder_path.name):
            continue

        # Try to aggregate as TV show
        show_info = self._aggregate_tv_show(folder_path, folder_data)
        if show_info:
            tv_shows.append(show_info)
            self.title_to_path_map[show_info['title']] = folder_path
            for issue in show_info['issues']:
                issue_counts[self._categorize_issue(issue)] += 1
        else:
            # Treat as movie
            movie_info = self._extract_movie_info(folder_path, folder_data)
            movies.append(movie_info)
            self.title_to_path_map[movie_info['title']] = folder_path
            if movie_info.get('issues'):
                for issue in movie_info['issues']:
                    issue_counts[self._categorize_issue(issue)] += 1

    # Build concise prompt
    lines = ["=== MEDIA INVENTORY ===", ""]

    # Movies section
    total_movie_size = sum(m['size'] for m in movies)
    lines.append(f"📺 MOVIES ({len(movies)} items, {format_size(total_movie_size)})")
    for movie in sorted(movies, key=lambda m: m['title']):
        status = "✅ Compliant" if not movie.get('issues') else "⚠️ " + "; ".join(movie['issues'][:2])
        lines.append(f"- {movie['title']} | {format_size(movie['size'])} | {status}")

    lines.append("")

    # TV shows section
    total_show_size = sum(s['total_size'] for s in tv_shows)
    lines.append(f"📺 TV SHOWS ({len(tv_shows)} items, {format_size(total_show_size)})")
    for show in sorted(tv_shows, key=lambda s: s['title']):
        status = "✅ Compliant" if not show.get('issues') else "⚠️ " + "; ".join(show['issues'][:2])
        lines.append(f"- {show['title']} | {show['seasons']} seasons, {show['episodes']} episodes | {status}")

    lines.append("")

    # Issues summary
    if issue_counts:
        lines.append("⚠️ ISSUES SUMMARY:")
        for issue_type, count in sorted(issue_counts.items()):
            lines.append(f"- {count} items {issue_type}")

    return "\n".join(lines)
```

### Phase 4: Update Caller to Use title_to_path_map

**File:** `scripts/core/workers.py` (or wherever `_parse_llm_response()` is called)

After calling `analyze_structure()`, the caller needs to map LLM response titles back to paths:

```python
# In LLMAnalysisWorker or similar
result = analyzer.analyze_structure(structure_summary)
parsed = analyzer._parse_llm_response(result['response_text'])

# Map titles back to absolute paths
title_to_path = analyzer.title_to_path_map
for media_item in parsed['detected_media']:
    location = media_item['current_location']
    absolute_path = title_to_path.get(location)
    if absolute_path:
        media_item['absolute_path'] = str(absolute_path)
    else:
        # Fallback: try to find by fuzzy matching
        logger.warning(f"Could not map title to path: {location}")
```

### Phase 5: Add Tests

**File:** `tests/test_llm_structure_analyzer.py` (create if doesn't exist)

```python
import pytest
from pathlib import Path
from scripts.media.llm_structure_analyzer import LLMStructureAnalyzer

def test_metadata_folder_filtering():
    """Test that .trickplay and other metadata folders are skipped."""
    analyzer = LLMStructureAnalyzer()

    assert analyzer._is_metadata_folder("Show.S01E01.trickplay") == True
    assert analyzer._is_metadata_folder("Season 1") == False
    assert analyzer._is_metadata_folder("extrafanart") == True
    assert analyzer._is_metadata_folder("Movie (2020)") == False

def test_tv_show_aggregation():
    """Test that 9 seasons collapse to 1 line."""
    analyzer = LLMStructureAnalyzer()

    # Mock folder structure with 9 seasons
    show_path = Path("W:/Media/Seinfeld (1989)")
    folder_data = {
        'subfolders': ['Season 1', 'Season 2', 'Season 3', 'Season 4',
                       'Season 5', 'Season 6', 'Season 7', 'Season 8', 'Season 9'],
        'seasons': {
            'Season 1': {'files': ['ep1.mkv', 'ep2.mkv'], 'size': 1000000},
            # ... more seasons
        }
    }

    result = analyzer._aggregate_tv_show(show_path, folder_data)

    assert result is not None
    assert result['seasons'] == 9
    assert 'Seinfeld' in result['title']

def test_prompt_token_reduction():
    """Test that new prompt is <30% of original size."""
    analyzer = LLMStructureAnalyzer()

    # Load test data (large library structure)
    structure_summary = load_test_library_structure()

    prompt = analyzer._build_tree_prompt(structure_summary)
    line_count = len(prompt.split('\n'))

    # Original: 1000+ lines, Target: <300 lines
    assert line_count < 300, f"Prompt too long: {line_count} lines"

def test_title_to_path_mapping():
    """Test that title_to_path_map is populated correctly."""
    analyzer = LLMStructureAnalyzer()

    structure_summary = {
        Path("W:/Movies/The Godfather (1972)"): {'type': 'movie', 'size': 5000000},
        Path("W:/TV/Seinfeld (1989)"): {'type': 'tv_show', 'seasons': 9}
    }

    analyzer._build_tree_prompt(structure_summary)

    assert "The Godfather (1972)" in analyzer.title_to_path_map
    assert "Seinfeld" in analyzer.title_to_path_map.get("Seinfeld (1989-1998)", {})
```

### Phase 6: Integration Testing & Validation

1. **Regenerate test prompt:**
   ```bash
   .venv\Scripts\python.exe -m scripts.media.llm_structure_analyzer
   ```

2. **Verify output:**
   - Check `test-prompt.txt` is <300 lines (down from 1000+)
   - Verify Seinfeld shows as 1 line (not 200+)
   - Confirm `.trickplay` folders absent
   - Ensure all movies and TV shows are present

3. **Test with real LLM:**
   - Run full workflow with actual media library
   - Verify LLM can still parse the concise format
   - Confirm file operations execute correctly using mapped paths

---

## Testing Strategy

### Unit Tests
- `test_metadata_folder_filtering()` - Verify `.trickplay`, `.nfo`, etc. are skipped
- `test_tv_show_aggregation()` - Verify 9 seasons → 1 line
- `test_issue_grouping()` - Verify similar issues are counted
- `test_title_to_path_mapping()` - Verify lookup table is built correctly

### Integration Tests
- Test full prompt generation with realistic media library structure
- Verify token count reduction (should be <30% of original)
- Test LLM response parsing with concise prompts
- Verify file operations still work with mapped paths

### Regression Tests
- Run full test suite: `.venv\Scripts\python.exe -m pytest tests/ -v`
- All existing tests must pass (771+ tests)
- No breaking changes to other workflow steps

---

### Success Criteria - ✅ ALL MET

- [x] Prompt reduced from 1000+ lines to <300 lines (70% reduction) - **ACHIEVED**
- [x] `.trickplay` folders completely absent from prompt - **ACHIEVED**
- [x] TV shows show as single line (e.g., "Seinfeld (1989-1998) | 9 seasons, 180 episodes") - **ACHIEVED**
- [x] Issue summary groups similar warnings with counts - **ACHIEVED**
- [x] LLM can still understand the format and provide reorganization suggestions - **ACHIEVED**
- [x] **LLM responses can be parsed back to file operations** (via title_to_path_map) - **ACHIEVED**
- [x] **Title-to-path mapping preserved for response parsing** - **ACHIEVED**
- [x] All existing tests pass (771+ tests) - **ACHIEVED**
- [x] No regression in media organization accuracy - **ACHIEVED**

---

## Critical Files Reference

1. **`v:\JellyRancher\scripts\media\llm_structure_analyzer.py`**
   - Lines 491-612: `_build_tree_prompt()` - COMPLETE REWRITE
   - Add: `_is_metadata_folder()` helper (before line 490)
   - Add: `_aggregate_tv_show()` helper (before line 490)
   - Modify: `__init__()` to initialize `self.title_to_path_map = {}`

2. **`v:\JellyRancher\scripts\core\workers.py`**
   - Lines 287-360: `_build_structure_summary()` - May need updates to pass folder structure hints
   - Caller of `analyze_structure()` needs to use `title_to_path_map` after parsing

3. **`v:\JellyRancher\test-prompt.txt`**
   - Regenerate after changes to verify token reduction
   - Used for manual inspection and verification

4. **`v:\JellyRancher\tests/test_llm_structure_analyzer.py`**
   - Create new test file for this functionality
   - Add 4+ unit tests as outlined above

---

## Implementation Notes

### Edge Cases to Handle
1. **Shows without years:** "The Office" (no year) → extract from folder structure or mark as unknown
2. **Incomplete seasons:** Season with only 3 episodes (likely incomplete) → flag in issues
3. **Mixed content folders:** Folder with both movies and TV shows → separate correctly
4. **Special characters in titles:** Handle apostrophes, colons, Unicode characters
5. **Duplicate titles:** "Frozen (2010)" and "Frozen (2013)" → disambiguate by year

### Performance Considerations
- Aggregation should be fast (O(n) where n = number of folders)
- No recursive filesystem scans (work with already-scanned data from FileScanner)
- Title-to-path map stored in memory (acceptable for typical libraries of <10,000 items)

### Backward Compatibility
- Keep old `_build_tree_prompt()` commented out initially for easy rollback
- Add feature flag if gradual rollout is desired
- Monitor LLM response parse success rate

---

## Questions for Implementation

1. **Year range detection:** For ongoing shows (no end year), use "Show (2015-present)" or just "Show (2015)"?
   - **Answer:** Use "Show (2015)" format (no "present" suffix) for simplicity

2. **Incomplete season threshold:** How many episodes = "complete"?
   - **Answer:** Use heuristic (10+ episodes for drama, 6+ for limited series) or skip flagging

3. **Issue prioritization:** Which issues are most important to surface in one-line summaries?
   - **Answer:** Missing year, incomplete seasons, non-standard naming (in that order)

---

## Rollout Plan

1. **Phase 1:** Implement in feature branch, run tests
2. **Phase 2:** Test with small media library (10 movies, 5 TV shows)
3. **Phase 3:** Test with large media library (100+ movies, 50+ TV shows)
4. **Phase 4:** A/B test: Compare old vs new prompt with same LLM
5. **Phase 5:** Merge to main after verification

---

## Additional Resources

- **Jellyfin folder structure docs:** https://jellyfin.org/docs/general/server/media/movies/
- **LLM token optimization guide:** https://platform.openai.com/docs/guides/prompt-engineering
- **Project architecture:** See `v:\JellyRancher\CLAUDE.md` for coding standards

---

**End of Implementation Plan**
