# Movie Name Management Guide

## Overview

Movie Name Management is your quality assurance tool for movie collections. This intelligent analyzer scans your movie library, identifies naming inconsistencies, and provides automated fixing capabilities to ensure professional, Jellyfin-compatible movie organization.

## What It Solves

- **Codec Tag Cleanup**: Removes technical tags from visible titles
- **Title Truncation**: Fixes shortened or abbreviated movie names
- **Folder Structure**: Ensures proper movie folder organization
- **Missing Years**: Adds release years for better metadata matching
- **Consistency**: Standardizes naming across your entire collection

## Quick Start

### 1. Access the Tool

1. Launch JellyRancher
2. Navigate to **Movie Analysis** tab
3. Click **Select Movies Folder**
4. Choose your Movies directory
5. Click **Analyze Movies**

### 2. Review Results

1. Browse the analysis results table
2. Check issue types and severity levels
3. Review suggested fixes
4. Select items to fix

### 3. Apply Fixes

1. Use **Fix Selected Issues** for individual fixes
2. Use **Fix All Issues** for bulk operations
3. Always preview in dry-run mode first

## Understanding Issues

### 🔧 Codec Tags in Titles
**Problem**: Technical information mixed with movie titles
```
Before: Inception (2010) H.265 1080p BluRay.mkv
After:  Inception (2010).mkv
```

**Why it matters**: Codec info belongs in file properties, not titles

**Auto-fixable**: ✅ Yes, tool removes common codec tags

### ✂️ Truncated Titles
**Problem**: Movie names shortened or abbreviated
```
Before: Cloutie Ru (2003).mkv
After:  Cloutie Rural (2003).mkv
```

**Why it matters**: Makes movies hard to find and identify

**Auto-fixable**: ❌ No, requires manual research and correction

### 📁 Folder Structure Issues
**Problem**: Movies not in proper individual folders
```
Before: Movies/Inception (2010).mkv
After:  Movies/Inception (2010)/Inception (2010).mkv
```

**Why it matters**: Jellyfin needs folders for metadata and artwork

**Auto-fixable**: ✅ Yes, tool creates proper folder structure

### 📅 Missing Years
**Problem**: Release years not included in filenames
```
Before: Inception.mkv
After:  Inception (2010).mkv
```

**Why it matters**: Essential for metadata matching and organization

**Auto-fixable**: ❌ No, requires manual year lookup

## Interface Guide

### Main Controls

- **Select Movies Folder**: Choose your Movies root directory
- **Analyze Movies**: Start comprehensive analysis
- **Fix Selected Issues**: Apply fixes to checked items only
- **Fix All Issues**: Bulk fix all detected problems
- **Export Results**: Save analysis report as JSON

### Results Display

Each movie shows:
- **Current Path**: Existing file location and name
- **Issues Detected**: List of problems found
- **Suggested Fix**: Recommended changes
- **Severity**: How critical the issue is
- **Status**: Current state (Pending/Fixed/Error)

### Severity Levels

- 🔴 **High**: Critical issues affecting functionality
- 🟡 **Medium**: Important for organization and appearance
- 🟢 **Low**: Minor improvements, optional fixes

## Analysis Process

### What It Checks

1. **File Structure**: Verifies proper movie folder organization
2. **Naming Patterns**: Validates title formatting and completeness
3. **Codec Detection**: Identifies unwanted technical tags
4. **Year Validation**: Checks for release year inclusion
5. **Consistency**: Ensures uniform naming across collection

### Processing Speed

- **Small Library** (< 100 movies): Instant analysis
- **Medium Library** (100-1000): Few seconds
- **Large Library** (> 1000): May take several minutes
- **Progress Bar**: Shows current file being analyzed

## Fixing Strategies

### Safe Bulk Operations

For high-confidence fixes:
1. Run analysis on entire collection
2. Filter by issue type (codec tags, folder structure)
3. Use "Fix All Issues" for automated processing
4. Review results and celebrate clean library

### Manual Corrections

For truncated titles and missing years:
1. Analyze collection to identify issues
2. Research correct titles and years online
3. Use individual fixing for precise control
4. Apply changes one movie at a time

### Dry Run Mode

Always preview before applying:
1. Check "Dry Run" option
2. Run fixes to see what would change
3. Review proposed changes carefully
4. Uncheck dry run to apply actual changes

## Best Practices

### Organization
- Keep Movies in dedicated folder
- Use consistent naming: `Movie Title (Year).extension`
- Avoid special characters in filenames
- Maintain folder structure for each movie

### Maintenance
- Run analysis after adding new movies
- Fix issues promptly to prevent accumulation
- Use automated fixes for routine cleanup
- Manual review for complex cases

### Quality Control
- Preview all changes before applying
- Backup important collections before bulk operations
- Test fixes on small batches first
- Verify results in your media player

## Common Scenarios

### New Movie Import
1. Add movies to your Movies folder
2. Run Movie Name Analysis
3. Fix any detected issues
4. Import into Jellyfin with clean names

### Library Cleanup
1. Analyze entire existing collection
2. Prioritize high-severity issues
3. Apply automated fixes first
4. Handle manual corrections separately

### Pre-Server Migration
1. Analyze collection thoroughly
2. Fix all folder structure issues
3. Ensure consistent naming
4. Verify in media server before migration

## Troubleshooting

### "No Movies Found"
- Check folder selection points to Movies root
- Ensure movies are in individual folders
- Verify file extensions are video formats

### "Permission Errors"
- Ensure write access to Movies folder
- Close any open media files
- Check antivirus exclusions

### "Analysis Takes Too Long"
- Reduce scope to subfolder for testing
- Close other applications using disk
- Consider batch processing in smaller chunks

## Integration Benefits

### With Jellyfin
- Better metadata matching with correct titles
- Proper poster and artwork display
- Cleaner library browsing experience
- Improved search and filtering

### With Subtitles
- More accurate subtitle matching
- Better subtitle organization
- Cleaner subtitle file naming

### With Organization Tools
- Consistent naming for bulk operations
- Reliable duplicate detection
- Better analytics and reporting

## Performance Optimization

- **SSD Storage**: Faster analysis on solid state drives
- **Folder Depth**: Shallow folder structures analyze quicker
- **File Count**: Large numbers of files may need batch processing
- **Network Drives**: Local storage preferred for speed

## Examples

### Complete Makeover

**Before Analysis:**
```
Movies/
├── Inception.H.265.1080p.mkv
├── Dark Knight (2008) x264 BluRay.mp4
├── Cloutie Ru (2003).avi
└── Movie Title.mkv
```

**After Fixes:**
```
Movies/
├── Inception (2010)/
│   └── Inception (2010).mkv
├── The Dark Knight (2008)/
│   └── The Dark Knight (2008).mp4
├── Cloutie Rural (2003)/
│   └── Cloutie Rural (2003).avi
└── Movie Title (2021)/
    └── Movie Title (2021).mkv
```

### Issue Breakdown
```
✓ Fixed: Codec tags removed from 2 files
✓ Fixed: Folder structure corrected for 3 files
⚠ Manual: Title truncation needs research for 1 file
⚠ Manual: Missing year needs lookup for 1 file
```

## Support and Resources

- **In-App Help**: Detailed help system with examples
- **Settings Tab**: Configure analysis preferences
- **Log Files**: Check `logs/` for operation details
- **Export Feature**: Save reports for sharing or tracking

---

**Pro Tip**: Run Movie Name Analysis monthly to maintain library quality. The tool gets smarter with use, learning from your corrections and preferences for better future suggestions.