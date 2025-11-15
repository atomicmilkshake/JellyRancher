# Episode Title Management Guide

## Overview

Episode Title Management is your intelligent assistant for maintaining perfect TV show episode naming. This powerful tool analyzes your episode files, compares them against official TMDB data, and provides automated fixing capabilities to ensure your media library follows professional naming standards.

## What It Does

- **Smart Analysis**: Automatically detects episode numbering and titles
- **TMDB Integration**: Cross-references with official episode data
- **Issue Detection**: Identifies missing, incorrect, or malformed titles
- **Safe Fixing**: Preview and apply changes with full rollback capability
- **Batch Processing**: Handle entire TV show collections at once
- **Confidence Scoring**: Rates how well your files match official data

## Quick Start

### 1. Prepare Your TMDB Cache

Before analyzing episodes, you need TMDB data:

1. Go to **Tools** → **Generate TMDB Cache**
2. Search for your TV show
3. Generate and save the cache file
4. Remember the cache file location

### 2. Analyze Your Episodes

1. Navigate to **Episode Analysis** tab
2. Click **Select Show Folder**
3. Choose your TV show directory
4. Select the TMDB cache file
5. Click **Analyze Episodes**

### 3. Review and Fix

1. Review the analysis results
2. Check confidence levels and issues
3. Preview proposed fixes
4. Apply changes safely

## Understanding the Interface

### Main Controls

- **Select Show Folder**: Choose your TV show directory
- **Select TMDB Cache**: Link to official episode data
- **Analyze Episodes**: Start the analysis process
- **Fix Selected Issues**: Apply fixes to checked items
- **Export Results**: Save analysis as JSON report

### Results Table

Each episode shows:
- **Current Name**: Your existing filename
- **Suggested Name**: Recommended correction
- **Confidence**: How certain the analysis is (High/Medium/Low)
- **Issues**: Specific problems detected
- **Status**: Current state of the file

### Color Coding

- 🟢 **Green**: Perfect match with TMDB data
- 🟡 **Yellow**: Minor issues, suggestions available
- 🔴 **Red**: Significant problems requiring attention

## Common Issues and Solutions

### Missing Episode Titles
**Problem**: Files named `Show S01E01.mkv` instead of `Show S01E01 - Episode Title.mkv`

**Solution**: The tool automatically suggests adding official titles from TMDB

### Incorrect Titles
**Problem**: Wrong or unofficial episode titles

**Solution**: Tool compares against TMDB and suggests corrections

### Codec Tags in Titles
**Problem**: Files like `Show S01E01 [1080p].mkv`

**Solution**: Tool detects and suggests removing codec tags from episode titles

### Inconsistent Formatting
**Problem**: Mixed naming patterns across episodes

**Solution**: Tool standardizes all episodes to consistent Jellyfin format

## Supported File Formats

The analyzer works with:
- **MKV, MP4, AVI**: All common video formats
- **Multiple episodes**: Handles multi-episode files
- **Special episodes**: Supports specials and non-standard episodes
- **International shows**: Works with non-English episode titles

## Advanced Features

### Dry Run Mode
- Preview all changes before applying
- See exactly what will be renamed
- No risk of data loss

### Selective Fixing
- Fix individual episodes
- Skip episodes you want to keep as-is
- Apply fixes in batches

### Confidence Filtering
- Focus on high-confidence fixes first
- Review medium-confidence suggestions
- Manually handle low-confidence cases

### Export and Reporting
- Save analysis results as JSON
- Share reports with others
- Track changes over time
- Audit trail for all operations

## Best Practices

### Organization
- Keep TMDB caches organized by show
- Process one show at a time for best results
- Backup your files before bulk operations

### Quality Control
- Always review high-confidence suggestions
- Test fixes on small batches first
- Use dry-run mode extensively

### Maintenance
- Re-analyze shows after TMDB updates
- Check for new episodes regularly
- Update caches when new seasons release

## Troubleshooting

### "No Episodes Found"
- Check that your folder structure matches Jellyfin standards
- Ensure files have proper S01E01 style numbering
- Verify the TMDB cache covers the correct show

### "Low Confidence Scores"
- TMDB cache might be outdated
- Episode numbering might not match TMDB
- Special episodes may need manual handling

### "Permission Denied"
- Ensure write access to the show folder
- Close any media players using the files
- Check antivirus software interference

## Integration with Other Tools

### Media Organization
- Use after initial media import
- Prepare files for media server integration
- Ensure consistent naming across collections

### Subtitle Management
- Clean episode titles before subtitle download
- Better subtitle matching with correct titles
- Improved subtitle organization

### Analytics and Reporting
- Generate reports on naming quality
- Track library consistency over time
- Identify shows needing attention

## Performance Tips

- **Large Collections**: Process one show at a time
- **Network Drives**: Ensure stable connection during analysis
- **File Count**: Tool handles thousands of episodes efficiently
- **Memory Usage**: Monitor system resources for very large libraries

## Examples

### Before and After

**Before:**
```
TheOffice.S01E01.mkv
TheOffice.S01E02.Diversity.Day.mkv
TheOffice.S01E03.Health.Care.[720p].mkv
```

**After:**
```
The Office - S01E01 - Pilot.mkv
The Office - S01E02 - Diversity Day.mkv
The Office - S01E03 - Health Care.mkv
```

### Analysis Results
```
✓ S01E01: Perfect match - "Pilot"
✓ S01E02: Title corrected - "Diversity Day"
⚠ S01E03: Codec tag removed - "[720p]" stripped
```

## Support Resources

- **In-App Help**: Comprehensive help system built-in
- **Tooltips**: Hover over interface elements for guidance
- **Log Files**: Check `logs/` for detailed operation logs
- **Settings**: Configure analysis preferences in Settings tab

---

**Pro Tip**: Start with a small, well-organized show to learn the workflow, then tackle larger collections. The analysis gets smarter with each use, learning from your preferences and corrections.