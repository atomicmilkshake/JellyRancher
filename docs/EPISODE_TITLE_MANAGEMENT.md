# Episode Title Management Guide

## Overview

The Episode Title Management feature helps you analyze and fix TV show episode filenames in your Jellyfin library. It compares your filenames against canonical episode titles from TMDB, identifies issues, and provides tools to safely rename files.

**Key Features:**
- Analyze entire TV show folders
- Compare episode titles with TMDB cache
- Identify naming issues (missing titles, incorrect titles, etc.)
- Preview fixes in dry-run mode
- Apply fixes with full audit logging
- Color-coded confidence levels
- Export results to JSON

## Prerequisites

1. **TMDB Cache**: Generate a TMDB cache file for your TV show first
   - Go to **Tools → Generate TMDB Cache**
   - Search for your show and generate the cache
   - See [TMDB_CACHE_GENERATOR.md](TMDB_CACHE_GENERATOR.md) for details

2. **Organized Structure**: Show folder should follow Jellyfin structure:
   ```
   Show Name/
   ├── Season 01/
   │   ├── Show Name - S01E01 - Episode Title.mkv
   │   ├── Show Name - S01E02 - Episode Title.mkv
   │   └── ...
   └── Season 02/
       └── ...
   ```

## Supported Filename Patterns

The analyzer recognizes three Jellyfin filename patterns:

1. **Standard Pattern**: `S01E01 - Episode Title.mkv`
2. **Show Prefix**: `Show Name S01E01 Episode Title.mkv`
3. **Full Pattern**: `Show Name - S01E01 - Episode Title.mkv`

## Using the Episode Analyzer

### Step 1: Open the Analyzer

1. Launch Jelly Rancher
2. Go to **Tools → 🔍 Analyze Episode Titles**
3. The Episode Analysis dialog opens

### Step 2: Select Show Folder

1. Click **Browse** next to "Show Folder"
2. Navigate to your TV show's root folder
3. Select the folder (e.g., `V:\TV Shows\Doctor Who`)

### Step 3: Select TMDB Cache

1. Click **Browse** next to "TMDB Cache File"
2. Navigate to your generated cache file
3. Select the JSON file (e.g., `doctor_who_cache.json`)

### Step 4: Run Analysis

1. Click **🔍 Analyze Show**
2. Wait for analysis to complete (progress bar shows status)
3. Results appear in the table

### Understanding Results

#### Results Table Columns

- **File**: Episode filename
- **Season**: Season number (S01, S02, etc.)
- **Episode**: Episode number (E01, E02, etc.)
- **Current Title**: Title extracted from filename
- **TMDB Title**: Canonical title from TMDB cache
- **Confidence**: Match confidence (High/Medium/Low/Very Low)
- **Issue Type**: Type of naming issue detected

#### Confidence Levels (Color-Coded)

- **High (Green)**: 90-100% match - filename is correct
- **Medium (Yellow)**: 70-89% match - minor differences
- **Low (Orange)**: 50-69% match - significant differences
- **Very Low (Red)**: <50% match - major issues

#### Issue Types

- **missing_title**: Episode number present but no title
- **incorrect_title**: Title doesn't match TMDB
- **technical_tags**: Title has codec/quality tags (x264, 1080p, etc.)
- **perfect_match**: No issues detected

#### Episode Details Pane

Click any row to see detailed information:
- Full file path
- Current vs. canonical title comparison
- Similarity score
- Recommended action
- Any warnings or notes

### Filtering Results

**Show All Episodes**: Toggle checkbox to show/hide episodes without issues
- Unchecked (default): Only shows episodes needing fixes
- Checked: Shows all episodes including perfect matches

## Fixing Episode Titles

### Dry Run (Preview Mode)

**Always preview fixes first!**

1. After analyzing, click **🔧 Fix Issues (Dry Run)**
2. Confirm the operation
3. Review the preview results:
   - Shows what would be renamed
   - Old filename → New filename
   - Success/failure for each operation
4. No files are actually renamed

### Applying Fixes

**Only use after reviewing dry-run results!**

1. Click **✅ Apply Fixes**
2. Read the warning dialog carefully
3. Confirm to proceed
4. Wait for operation to complete
5. Review results summary
6. Analysis automatically re-runs to show updated state

### Fix Results Dialog

Shows operation summary:
- **Total**: Number of episodes processed
- **Successful**: Files successfully renamed
- **Failed**: Files that couldn't be renamed (with error messages)

Click "Show Details" to see the full JSON results including:
- Old and new filenames for each operation
- Error messages for failures
- Audit log references

## Safety Features

### Validation Checks

Before renaming, the system validates:
- Source file exists
- Target filename doesn't already exist
- Directory is writable
- Filename is valid for the filesystem
- Filename length is within limits (200 chars display, 255 OS limit)

### Invalid Characters

Automatically removes invalid filename characters:
- Windows: `< > : " / \ | ? *`
- Unix: Null byte
- Control characters (0x00-0x1F)

### Audit Logging

All rename operations are logged to:
- ChromaDB knowledge base
- Immutable audit log (if configured)

Logs include:
- Old and new filenames
- Timestamp
- Operation result (success/failure)
- Error messages (if any)

### What Gets Preserved

When renaming files:
- ✅ Season/Episode pattern (S01E01)
- ✅ File extension (.mkv, .mp4, etc.)
- ✅ Show name (if present in original)
- ✅ Directory structure (files stay in same folder)
- ❌ Technical tags removed (x264, 1080p, HEVC, etc.)
- ❌ Release group tags removed ([RARBG], etc.)

## Workflows

### Workflow 1: Quick Check

Use when you want to verify if your library is properly named:

1. Open analyzer
2. Select show folder and TMDB cache
3. Click Analyze
4. Review confidence levels
5. Export results if needed

### Workflow 2: Fix Single Show

Use when you know one show has naming issues:

1. Generate TMDB cache for the show
2. Open analyzer
3. Select show folder and cache
4. Click Analyze
5. Review episodes with issues
6. Click Fix Issues (Dry Run)
7. Review preview results
8. Click Apply Fixes if satisfied
9. Verify results after auto re-analysis

### Workflow 3: Batch Analysis

Use when checking multiple shows:

1. Generate TMDB caches for all shows
2. For each show:
   - Open analyzer (or use same window)
   - Select show folder and cache
   - Click Analyze
   - Export results to JSON
3. Review all exported JSON files
4. Go back and fix shows with issues

## Troubleshooting

### "No episodes need fixing"

**Cause**: All episodes either have perfect matches or the analyzer couldn't identify issues.

**Solutions**:
- Check "Show all episodes" to see all results
- Verify TMDB cache matches the show
- Check if files follow supported patterns

### Analysis finds 0 episodes

**Cause**: No video files found or files don't match expected patterns.

**Solutions**:
- Verify show folder contains Season subfolders
- Check that files have S##E## pattern
- Supported extensions: .mkv, .mp4, .avi, .m4v, .ts

### Fix operation fails

**Common causes**:
- File is open in another program (media player, Jellyfin)
- Insufficient permissions
- Target filename already exists
- Network drive issues

**Solutions**:
- Close all programs using the files
- Run Jelly Rancher as administrator
- Check file permissions
- For network drives, copy to local first

### TMDB cache doesn't match show

**Cause**: Wrong show selected during cache generation.

**Solutions**:
- Regenerate TMDB cache
- Use search to find exact show
- Check TMDB ID in cache file
- Verify year/version matches your show

### Low confidence on correct titles

**Cause**: Similarity algorithm may not handle special characters or formatting differences well.

**Solutions**:
- Review the specific episodes manually
- Check episode details pane for exact comparison
- Use dry-run to preview suggested changes
- Some episodes may need manual review

## Best Practices

### Before You Start

1. **Backup your library** - Always have a backup before batch renaming
2. **Test with one show** - Use a small show (10-20 episodes) first
3. **Use dry-run** - Always preview changes before applying
4. **Generate accurate caches** - Verify TMDB show selection is correct

### During Operation

1. **Review each section** - Check all episodes flagged with issues
2. **Check confidence levels** - Pay attention to low confidence matches
3. **Read warnings** - Don't ignore validation warnings
4. **Use export** - Save results before making changes

### After Fixes

1. **Verify in Jellyfin** - Refresh metadata and check display
2. **Check audit logs** - Review what was changed
3. **Test playback** - Make sure files still work
4. **Update TMDB cache** - If you fixed many episodes, consider regenerating cache

## Technical Details

### Pattern Matching

The analyzer uses three-stage matching:

1. **Extract**: Parse filename to extract episode info
2. **Clean**: Remove technical tags and normalize
3. **Compare**: Use SequenceMatcher for fuzzy matching

### Similarity Scoring

- **Algorithm**: Python's difflib.SequenceMatcher
- **Range**: 0.0 (no match) to 1.0 (perfect match)
- **Thresholds**:
  - ≥0.90: High confidence
  - 0.70-0.89: Medium confidence  
  - 0.50-0.69: Low confidence
  - <0.50: Very low confidence

### Recommendations

Based on analysis, the system recommends:

- **perfect**: No changes needed
- **use_cleaned**: Use title with technical tags removed
- **use_canonical**: Use TMDB title
- **review_manual**: Human review required (low confidence)

### Performance

- **Analysis Speed**: ~100-200 episodes/second
- **Fix Speed**: ~10-50 files/second (varies by disk)
- **Memory Usage**: Minimal (<100MB for typical shows)

## FAQ

**Q: Will this work with multi-episode files?**
A: No, the analyzer expects one episode per file. Multi-episode files (S01E01-E02) may not be recognized correctly.

**Q: Can I undo renames?**
A: Not directly. The audit log shows what was changed. You'd need to manually rename back or restore from backup.

**Q: Does this update Jellyfin metadata?**
A: No, this only renames files. You'll need to refresh metadata in Jellyfin after renaming.

**Q: Can I customize the filename pattern?**
A: Currently no. The system uses Jellyfin's standard pattern: `Show - S##E## - Title.ext`

**Q: What about special episodes (S00E##)?**
A: Special episodes are supported if they're in the TMDB cache and follow the S##E## pattern.

**Q: Does it work with anime?**
A: Yes, but TMDB may not have accurate data for all anime. Consider using TVDB-based caches instead (future feature).

## Related Documentation

- [TMDB Cache Generator Guide](TMDB_CACHE_GENERATOR.md) - Generate TMDB caches
- [Architecture Documentation](../docs/) - Technical details
- [Jelly Rancher Main Guide](../JELLY_RANCHER_README.md) - Overview of all features

## Support

For issues or questions:
1. Check audit logs in `audit-logs/` directory
2. Check application logs in `logs/` directory
3. Review ChromaDB entries for operation history
4. Export analysis results to JSON for detailed review

---

*Last Updated: November 8, 2025*
*Version: 2.0 (Integration Phase 2)*
