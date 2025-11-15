# Movie Name Management Guide

## Overview

The Movie Name Management feature helps you analyze and fix movie filenames in your Jellyfin library. It identifies common naming issues like codec tags, truncated titles, and improper folder structure, then provides tools to safely fix them.

**Key Features:**
- Analyze entire Movies folder
- Detect 4 types of naming issues
- Color-coded severity levels
- Preview fixes in dry-run mode
- Apply fixes with full audit logging
- Export results to JSON

## Issue Types Detected

### 1. Codec Tags in Filenames
**Examples:**
- `Movie Title (2020) H.265.mkv`
- `Action Film (2019) x264 1080p BluRay.mp4`
- `Drama Title (2018) HEVC 10bit HDR.mkv`

**Why it's an issue:** Codec information belongs in file metadata, not the filename. Jellyfin displays this separately.

**Fix:** Automatically removes codec tags, quality markers, and release tags.

### 2. Truncated Titles
**Examples:**
- `Cloutie Ru (2003).mkv` (should be "Cloutie Rural")
- `Doc Mar (2001).mkv` (should be "Doc Martin")

**Why it's an issue:** Truncated titles make movies hard to find and look unprofessional in Jellyfin.

**Fix:** Requires manual title lookup and correction (TMDB/IMDB).

### 3. Improper Folder Structure
**Examples:**
- File directly in Movies folder: `Movies/Movie Title (2020).mkv`
- Folder name doesn't match: `Movies/RandomFolder/Movie Title (2020).mkv`

**Why it's an issue:** Jellyfin expects each movie in its own folder for proper metadata, artwork, and extras.

**Fix:** Automatically creates proper folder: `Movies/Movie Title (2020)/Movie Title (2020).mkv`

### 4. Missing Year
**Examples:**
- `Movie Title.mkv` (no year)
- `Action Film x264.mp4` (no year)

**Why it's an issue:** Year is essential for Jellyfin to distinguish between remakes, identify correct metadata, and organize collections.

**Fix:** Requires manual year lookup (TMDB/IMDB).

## Using the Movie Analyzer

### Step 1: Open the Analyzer

1. Launch Jelly Rancher
2. Go to **Tools → 🎬 Analyze Movie Names**
3. The Movie Analysis dialog opens

### Step 2: Select Movies Folder

1. Click **Browse** next to "Movies Folder"
2. Navigate to your Movies folder (e.g., `V:\Movies` or `M:\#MEDIA\Movies`)
3. Select the folder

### Step 3: Run Analysis

1. Click **🔍 Analyze Movies**
2. Wait for analysis to complete (progress bar shows status)
3. Results appear in the table

### Understanding Results

#### Results Table Columns

- **File**: Movie filename
- **Title**: Extracted movie title
- **Year**: Release year (or "(missing)" if not found)
- **Folder**: Parent folder name
- **Issues**: Number of issues detected
- **Severity**: Highest severity level (High/Medium/Low/None)
- **Auto-Fixable**: Whether issues can be automatically fixed

#### Severity Levels (Color-Coded)

- **High (Red)**: Critical issues - truncated titles, missing year
- **Medium (Orange)**: Moderate issues - codec tags, folder mismatch
- **Low (Yellow)**: Minor issues - file directly in Movies folder
- **None (Green)**: No issues detected

#### Movie Details Pane

Click any row to see detailed information:
- Full file path
- Extracted title and year
- Cleaned filename (codec tags removed)
- List of all issues with descriptions
- Suggested fixes with auto/manual indicators
- Specific actions for each fix

### Filtering Results

**Show All Movies**: Toggle checkbox to show/hide movies without issues
- Unchecked (default): Only shows movies with issues
- Checked: Shows all movies including perfect ones

## Fixing Movie Names

### Automatic Fixes

These can be applied with one click:
- **Codec tag removal**: Strips all technical tags
- **Folder structure creation**: Moves movie to proper folder

### Manual Fixes

These require user input:
- **Truncated titles**: Need correct full title
- **Missing years**: Need release year from TMDB/IMDB

### Dry Run (Preview Mode)

**Always preview fixes first!**

1. After analyzing, click **🔧 Fix Issues (Dry Run)**
2. Review the confirmation dialog showing:
   - Number of movies to process
   - Fix types that will be applied
3. Confirm to see preview
4. Review results:
   - Shows what would be renamed/moved
   - Old path → New path
   - Success/skip/error for each operation
5. No files are actually modified

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
- **Total**: Number of movies processed
- **Successful**: Files successfully fixed
- **Skipped**: Files that didn't need changes
- **Failed**: Files that couldn't be fixed (with error messages)

Click "Show Details" to see the full JSON results.

## Safety Features

### Validation Checks

Before renaming/moving, the system validates:
- Source file exists
- Target path doesn't already exist
- Directory is writable
- Filename is valid for the filesystem
- Filename length is within limits (200 chars display, 255 OS limit)

### Invalid Characters

Automatically removes invalid filename characters:
- Windows: `< > : " / \ | ? *`
- Control characters (0x00-0x1F)

### Audit Logging

All operations are logged to:
- ChromaDB knowledge base
- Immutable audit log (if configured)

Logs include:
- Old and new paths
- Timestamp
- Operation type (rename/move)
- Operation result (success/failure)
- Error messages (if any)

### What Gets Preserved

When fixing files:
- ✅ Movie title
- ✅ Release year (if present)
- ✅ File extension (.mkv, .mp4, etc.)
- ❌ Codec tags removed
- ❌ Quality markers removed (1080p, 4K, etc.)
- ❌ Release tags removed ([RARBG], {YIFY}, etc.)

### What Gets Created

For folder structure fixes:
- ✅ New folder: `Movie Title (Year)/`
- ✅ Moved file: `Movie Title (Year)/Movie Title (Year).ext`
- ✅ Old empty folder removed (if safe)

## Workflows

### Workflow 1: Quick Cleanup

Use when you want to remove codec tags from filenames:

1. Open analyzer
2. Select Movies folder
3. Click Analyze
4. Review movies with "codec_in_name" issues
5. Click Fix Issues (Dry Run)
6. Verify preview results
7. Click Apply Fixes
8. Done!

### Workflow 2: Folder Structure Fix

Use when movies are loose in Movies folder:

1. Open analyzer
2. Select Movies folder
3. Click Analyze
4. Review movies with "not_in_folder" issues
5. Click Fix Issues (Dry Run)
6. Verify proper folder structure will be created
7. Click Apply Fixes
8. Jellyfin will now properly identify movies

### Workflow 3: Complete Library Audit

Use when setting up or cleaning entire library:

1. Open analyzer
2. Select Movies folder
3. Click Analyze
4. Check "Show all movies" to see everything
5. Export results to JSON for records
6. Filter by severity:
   - Fix high-severity issues manually first
   - Apply automatic fixes for medium/low issues
7. Re-analyze to verify all fixed

## Troubleshooting

### "No movies need fixing"

**Cause**: All movies are properly named.

**Solutions**:
- Check "Show all movies" to see all results
- Verify you selected correct Movies folder
- Check if folder contains video files

### Analysis finds 0 movies

**Cause**: No video files found in folder.

**Solutions**:
- Verify folder contains .mkv, .mp4, .avi, .m4v, or .ts files
- Check subfolder structure
- Ensure you selected the root Movies folder

### Fix operation fails

**Common causes**:
- File is open in another program (media player, Jellyfin)
- Insufficient permissions
- Target path already exists
- Network drive issues
- Disk full

**Solutions**:
- Close all programs using the files
- Stop Jellyfin service temporarily
- Run Jelly Rancher as administrator
- Check disk space
- For network drives, copy to local first

### "Target already exists" error

**Cause**: Another movie with same title and year exists.

**Solutions**:
- Check for duplicate movies
- Manually rename one movie to distinguish (add edition, quality, etc.)
- Remove duplicate if it's an extra copy

### Folder name doesn't match after fix

**Cause**: Analyzer extracted title differently than expected.

**Solutions**:
- This is usually fine - Jellyfin uses metadata, not folder names
- Manually rename folder if desired
- Check if extracted title is more accurate

## Best Practices

### Before You Start

1. **Backup your library** - Always have a backup before batch operations
2. **Stop Jellyfin** - Prevents file lock issues
3. **Test with small batch** - Try 5-10 movies first
4. **Use dry-run** - Always preview changes before applying

### During Operation

1. **Review each issue type** - Understand what will be fixed
2. **Check severity levels** - Focus on high-severity issues first
3. **Read warnings** - Don't ignore validation warnings
4. **Use export** - Save results before making changes

### After Fixes

1. **Verify in file system** - Check a few files manually
2. **Restart Jellyfin** - Refresh metadata library
3. **Check playback** - Make sure files still work
4. **Review audit logs** - Confirm what was changed

### Manual Fixes

For truncated titles and missing years:
1. Look up movie on TMDB or IMDB
2. Get exact title and year
3. Manually rename file: `Movie Title (Year).ext`
4. Create folder if needed: `Movies/Movie Title (Year)/`
5. Move file into folder
6. Re-run analysis to confirm fixed

## Technical Details

### Issue Detection Algorithms

**Codec Tags:**
- Pattern matching for 13 common codec/quality tags
- Case-insensitive regex matching
- Removes bracketed/braced tags

**Truncated Titles:**
- Detects 1-2 character words before year
- Filters out common short words (a, an, in, etc.)
- Flags multiple suspicious short words

**Folder Structure:**
- Checks if parent folder is "Movies" or "#MEDIA"
- Uses fuzzy matching (SequenceMatcher) for folder vs title
- Threshold: <50% similarity triggers warning

**Missing Year:**
- Looks for (YYYY) pattern in filename
- Year range: 1900-2099

### Pattern Matching

Codec/quality tags detected:
```
H.265, H.264, HEVC, x264, x265, AVC
10bit, 8bit, HDR, DV, WEB-DL, BluRay
1080p, 720p, 2160p, 4K
AAC, DTS, DD5.1, Atmos
```

Release tags removed:
```
[RARBG], {YIFY}, [YTS], etc.
Anything in brackets or braces
```

### Performance

- **Analysis Speed**: ~50-100 movies/second
- **Fix Speed**: ~5-20 files/second (varies by operation)
- **Memory Usage**: Minimal (<50MB for typical libraries)

### File Operations

**Codec Tag Removal:**
```
Old: Movie Title (2020) H.265 1080p.mkv
New: Movie Title (2020).mkv
```

**Folder Creation:**
```
Old: Movies/Movie Title (2020).mkv
New: Movies/Movie Title (2020)/Movie Title (2020).mkv
```

## FAQ

**Q: Will this work with movies in subfolders?**
A: Yes, the analyzer recursively scans all subfolders.

**Q: Can I undo renames?**
A: Not directly. Check audit logs for what changed. Best practice: backup first.

**Q: Does this update Jellyfin metadata?**
A: No, this only renames files/folders. Refresh metadata in Jellyfin after fixing.

**Q: What about special characters in titles?**
A: Special characters are preserved but invalid filesystem characters are removed.

**Q: Can I customize what codec tags to remove?**
A: Currently no. The system removes 13 common patterns. Future versions may allow customization.

**Q: Does it work with 4K/HDR movies?**
A: Yes, but it removes "4K" and "HDR" from filenames (they belong in metadata).

**Q: What about multi-file movies (CD1/CD2)?**
A: Each file is analyzed separately. Manual handling recommended for multi-file movies.

**Q: Can I fix specific issues only?**
A: Yes, the fixer automatically detects which fix types are needed per movie.

**Q: What about movies with multiple editions?**
A: Add edition info manually: `Movie Title (2020) - Director's Cut.mkv`

**Q: Does it handle 3D movies?**
A: Yes, but it may remove "3D" tag. Add it back manually if needed for identification.

## Codec Tags Reference

### Video Codecs
- **H.264 / AVC**: Common codec, widely supported
- **H.265 / HEVC**: Newer codec, better compression
- **x264 / x265**: Software encoder names

### Quality Markers
- **1080p**: 1920x1080 resolution (Full HD)
- **720p**: 1280x720 resolution (HD)
- **2160p / 4K**: 3840x2160 resolution (Ultra HD)
- **HDR**: High Dynamic Range
- **10bit**: Color depth (vs 8bit)

### Source Markers
- **BluRay**: Blu-ray disc source
- **WEB-DL**: Downloaded from web service
- **WEBRip**: Ripped from streaming service

### Audio Codecs
- **AAC**: Advanced Audio Coding
- **DTS**: Digital Theater Systems
- **DD5.1**: Dolby Digital 5.1
- **Atmos**: Dolby Atmos

**Note:** All these belong in file metadata, not the filename. Jellyfin displays them separately.

## Related Documentation

- [TMDB Cache Generator Guide](TMDB_CACHE_GENERATOR.md) - For TV shows
- [Episode Title Management](EPISODE_TITLE_MANAGEMENT.md) - For TV episodes
- [Architecture Documentation](../docs/) - Technical details
- [Jelly Rancher Main Guide](../JELLY_RANCHER_README.md) - Overview of all features

## Support

For issues or questions:
1. Check audit logs in `audit-logs/` directory
2. Check application logs in `logs/` directory
3. Review ChromaDB entries for operation history
4. Export analysis results to JSON for detailed review

## Examples

### Example 1: Clean Filename
```
Before: Movies/Inception (2010) H.265 1080p BluRay x264.mkv
After:  Movies/Inception (2010)/Inception (2010).mkv
```

### Example 2: Truncated Title
```
Before: Movies/Doc Mar (2003).mkv
Manual: Look up on TMDB → "Doc Martin and the Legend of the Cloutie Well"
After:  Movies/Doc Martin and the Legend of the Cloutie Well (2003)/
        Doc Martin and the Legend of the Cloutie Well (2003).mkv
```

### Example 3: Multiple Issues
```
Before: Movies/Action Film x264 1080p.mkv
Issues: Codec tags, missing year, not in folder
Manual: Look up year → 2018
After:  Movies/Action Film (2018)/Action Film (2018).mkv
```

---

*Last Updated: November 8, 2025*
*Version: 2.0 (Integration Phase 3)*
