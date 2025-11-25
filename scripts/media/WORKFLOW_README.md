# Jellyfin Media Organization Workflow

Complete automated workflow for preparing media libraries for Jellyfin, with intelligent LLM-based analysis and accurate metadata lookup.

## Overview

This workflow implements Steps 3 and 4 of the JellyRancher media organization system:

**Step 3:** LLM Structure Analysis
- Submits folder structure to reasoning LLM (Grok-4.1-Fast-Reasoning or similar)
- Proposes Jellyfin-compliant reorganization
- Detects and classifies movies vs TV shows
- Identifies multi-part episodes requiring special handling

**Step 4:** Metadata Lookup & NFO Generation
- Queries TMDB/OMDb APIs for accurate metadata
- Builds canonical database with correct titles, years, and episode information
- Generates NFO files for multi-part episodes (e.g., Star Trek TNG "Encounter at Farpoint")
- Handles complex episode numbering scenarios

## Components

### 1. `llm_structure_analyzer.py`
Analyzes folder structures using LLM reasoning via Poe.com API.

**Features:**
- Dynamic model selection (Grok-4.1-Fast-Reasoning, GPT-4, etc.)
- Comprehensive prompt engineering for media analysis
- JSON response parsing with error handling
- Detailed reasoning capture

**Usage:**
```bash
python llm_structure_analyzer.py data/scan_structure_20241108_120000.json
```

### 2. `media_metadata_lookup.py`
Looks up accurate metadata from external APIs.

**Features:**
- TMDB integration for comprehensive movie/TV data
- OMDb fallback for additional coverage
- Episode-level details including multi-part detection
- Intelligent caching to minimize API calls
- Rate limiting for API compliance

**Usage:**
```bash
# Set API keys first
export TMDB_API_KEY="your_tmdb_key"
export OMDB_API_KEY="your_omdb_key"

python media_metadata_lookup.py data/llm_analysis_20241108_120000.json
```

**Getting API Keys:**
- TMDB: https://www.themoviedb.org/settings/api (free)
- OMDb: http://www.omdbapi.com/apikey.aspx (free tier available)

### 3. `nfo_generator.py`
Generates Jellyfin/Kodi-compatible NFO files.

**Features:**
- Multi-part episode NFO generation
- Movie and TV show NFO support
- Proper XML formatting
- Dry-run mode for safe testing

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
Complete workflow orchestrator.

**Features:**
- End-to-end automation
- Comprehensive logging
- Dry-run mode (default)
- Progress tracking
- Error handling and recovery

**Usage:**
```bash
# Dry run (safe, no changes):
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" "V:\#MEDIA\Movies"

# With custom model:
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --model gpt-4o-reasoning

# Execute actual changes:
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --execute

# With additional context:
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --context "Focus on anime collections"
```

## Complete Workflow Example

```bash
# 1. Set up environment
export OPENAI_API_KEY="your_poe_api_key"  # For LLM analysis
export TMDB_API_KEY="your_tmdb_key"        # For metadata lookup
export OMDB_API_KEY="your_omdb_key"        # Optional fallback

# 2. Run complete workflow (dry-run)
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" "V:\#MEDIA\Movies"

# 3. Review outputs in data/workflow_output/:
#    - workflow_complete_TIMESTAMP.json (all results)
#    - reorganization_plan_TIMESTAMP.json (action plan)
#    - canonical_metadata_TIMESTAMP.json (verified metadata)
#    - llm_analysis_TIMESTAMP.json (LLM recommendations)
#    - nfo_files/ (generated NFO files)

# 4. If satisfied, execute:
python jellyfin_workflow.py "V:\#MEDIA\TV Shows" --execute
```

## Output Files

### `workflow_complete_TIMESTAMP.json`
Complete results from all workflow steps.

### `reorganization_plan_TIMESTAMP.json`
Detailed plan for reorganizing media:
- Folder renaming recommendations
- File movement instructions
- NFO file placement
- Jellyfin compliance issues

### `canonical_metadata_TIMESTAMP.json`
Verified metadata database:
- Complete movie information (title, year, IDs)
- TV show details (seasons, episodes, air dates)
- Multi-part episode detection
- Source attribution (TMDB/OMDb)

### `llm_analysis_TIMESTAMP.json`
LLM reasoning and recommendations:
- Detected media with confidence scores
- Structural analysis
- Multi-part episode identification
- Reorganization reasoning

### `nfo_files/`
Generated NFO files organized by show/season.

## Multi-Part Episode Handling

The workflow automatically detects and handles multi-part episodes:

**Detection:**
- Episode titles with "Part 1/2" or "Part I/II"
- LLM reasoning based on episode patterns
- TMDB episode metadata analysis

**NFO Generation:**
- Creates proper multi-part NFO files
- Maps multiple episode numbers to single file
- Preserves correct episode order in Jellyfin

**Example:** Star Trek TNG Season 1
```
Encounter at Farpoint (Episodes 1-2) stored as single file
→ Generates: Star Trek The Next Generation - s01e01.nfo
   Containing: <multipart><part>1</part><part>2</part></multipart>
```

## Requirements

### Python Packages
```bash
pip install requests
```

### API Keys (Environment Variables)
- `OPENAI_API_KEY` - Poe.com API key (required for LLM analysis)
- `TMDB_API_KEY` - TMDB API key (recommended for best results)
- `OMDB_API_KEY` - OMDb API key (optional fallback)

### Directory Structure
```
scripts/media/
├── folder_structure_scanner.py  (Steps 1-2)
├── llm_structure_analyzer.py    (Step 3)
├── media_metadata_lookup.py     (Step 4a)
├── nfo_generator.py              (Step 4b)
└── jellyfin_workflow.py          (Orchestrator)

scripts/ai/
└── ravenmaven_client.py          (Poe API client)
```

## Workflow Steps in Detail

### Step 1-2: Scan & Summarize (Already Implemented)
- Recursively scan folders for video files
- Generate hierarchical structure summary
- Classify folders (TV shows, movies, seasons)
- Count video files per folder/season

### Step 3: LLM Analysis (New)
**Input:** Folder structure summary
**Process:**
1. Build comprehensive analysis prompt
2. Submit to reasoning LLM via Poe API
3. Parse JSON response
4. Extract detected media and reorganization recommendations

**Output:**
- List of detected movies and TV shows
- Confidence scores for each detection
- Proposed folder structure changes
- Multi-part episode identifications

### Step 4a: Metadata Lookup (New)
**Input:** Detected media list from LLM
**Process:**
1. Query TMDB for each movie/TV show
2. Retrieve detailed episode information
3. Detect multi-part episodes from metadata
4. Cache results to minimize API calls

**Output:**
- Canonical metadata database
- Complete season/episode details
- Accurate titles and years
- Multi-part episode flags

### Step 4b: NFO Generation (New)
**Input:** Canonical metadata + multi-part episodes
**Process:**
1. For each multi-part episode, generate NFO
2. Map multiple episode numbers to single file
3. Include proper TMDB/IMDB IDs
4. Format as Jellyfin-compatible XML

**Output:**
- NFO files in appropriate folder structure
- Ready for Jellyfin scanning

## Logging and Debugging

### Workflow Log
Complete log saved to: `data/workflow_output/workflow_TIMESTAMP.log`

### LLM I/O Logs
Detailed API transactions: `LLM_io_log/llm_transaction_TIMESTAMP.json`

Includes:
- Full request/response
- Prompt and model used
- Token usage
- Timing information
- Error details

### Dry Run Mode
Default mode - no actual file changes:
- NFO files are not written (but content is generated)
- Folder moves are planned but not executed
- Safe for testing and validation

Use `--execute` flag to apply changes.

## Troubleshooting

### "Import ravenmaven_client could not be resolved"
The import path is resolved at runtime. Ensure `scripts/ai/ravenmaven_client.py` exists.

### "No metadata found for show: X"
- Check TMDB_API_KEY is set correctly
- Verify show title spelling
- Check TMDB has the show in their database
- Review LLM detection accuracy

### "API request failed: 403 Forbidden"
- Verify API key is valid
- Check API key permissions
- Ensure not rate-limited

### Multi-part episodes not detected
- Review LLM analysis output
- Check TMDB episode data
- Manually add to multi_part_episodes list if needed

## Future Enhancements

- [ ] TVDB API integration for additional TV data
- [ ] Automatic file renaming and moving
- [ ] Jellyfin API integration for direct library updates
- [ ] GUI for workflow control
- [ ] Batch processing for large libraries
- [ ] Custom rule engine for special cases

## Related Documentation

- [JELLY_RANCHER_README.md](../../JELLY_RANCHER_README.md) - Main project documentation
- [bootstrap.md](../../bootstrap.md) - Development setup guide
- [folder_structure_scanner.py](folder_structure_scanner.py) - Steps 1-2 implementation

## License

Part of the JellyRancher project.
