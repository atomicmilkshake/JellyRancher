# Workflow Step 1: Folder Scanning & Structure Analysis

## Overview

The first step in the JellyRancher workflow allows you to scan one or multiple folders recursively to:
1. Generate a complete list of all video files with full paths
2. Analyze and summarize folder structure
3. Identify folder types (TV shows with seasons, movies, etc.)
4. Export results for further processing

## How to Use

### Via GUI (jelly_rancher_main.py)

1. **Launch the application:**
   ```bash
   python jelly_rancher_main.py
   ```

2. **Navigate to the Workflow tab** (first tab with 🚀 icon)

3. **Add folders to scan:**
   - Click "➕ Add Folder"
   - Select the folder you want to scan
   - Repeat for multiple folders

4. **Configure options:**
   - **Structure Summary Depth**: How many folder levels to display (1-10)
   - **Save complete file list**: Check to save all video file paths to a text file
   - **Save structure summary**: Check to save JSON with detailed structure analysis

5. **Start the scan:**
   - Click "🔍 Start Scan"
   - Watch the progress bar
   - View results in the Structure Summary panel

6. **Export results:**
   - Results are auto-saved if options are checked
   - Click "💾 Export Results" to manually export
   - Files saved to `data/` folder with timestamps

### Via Python Module

```python
from folder_structure_scanner import FolderStructureScanner

# Create scanner with one or more folders
scanner = FolderStructureScanner([
    r"V:\#MEDIA\TV Shows",
    r"V:\#MEDIA\Movies"
])

# Perform scan
video_files, structure = scanner.scan_all()

# Generate and display structure summary
scanner.generate_structure_summary()
scanner.print_structure_summary(max_depth=3)

# Save results
scanner.save_file_list("data/video_files.txt")
scanner.save_structure_summary("data/structure.json")

print(f"Found {len(video_files)} video files")
```

### Via Command Line

```bash
python scripts/media/folder_structure_scanner.py "V:\#MEDIA\TV Shows" "V:\#MEDIA\Movies"
```

## Output Format

### File List (Text)
One complete file path per line:
```
V:\#MEDIA\TV Shows\Star Trek TNG\Season 01\Episode 01.mkv
V:\#MEDIA\TV Shows\Star Trek TNG\Season 01\Episode 02.mkv
...
```

### Structure Summary (JSON)
```json
{
  "scan_date": "2025-11-08T19:27:30.701776",
  "root_folders": ["V:\\#MEDIA\\TV Shows"],
  "total_video_files": 234,
  "total_all_files": 240,
  "structure": {
    "V:\\#MEDIA\\TV Shows\\Star Trek TNG": {
      "path": "V:\\#MEDIA\\TV Shows\\Star Trek TNG",
      "name": "Star Trek TNG",
      "total_videos": 176,
      "direct_videos": 0,
      "type": "tv_show_with_seasons",
      "subfolders": {
        "Season 01": {
          "total_videos": 26,
          "type": "season"
        },
        ...
      }
    }
  }
}
```

### Console Display
```
================================================================================
FOLDER STRUCTURE SUMMARY
================================================================================

📁 Star Trek The Next Generation (176 videos across 7 seasons)
  └─ Season 01: 26 videos
  └─ Season 02: 26 videos
  └─ Season 03: 26 videos
  └─ Season 04: 26 videos
  └─ Season 05: 26 videos
  └─ Season 06: 26 videos
  └─ Season 07: 20 videos

📁 The Office (50 videos in this folder)

📁 Movies (5 videos, 5 subfolders)
  🎬 The Matrix (1999) (1 video)
  🎬 Inception (2010) (1 video)
  🎬 Pulp Fiction (1994) (1 video)
  🎬 The Dark Knight (2008) (1 video)
  🎬 Forrest Gump (1994) (1 video)
```

## Folder Type Classification

The scanner automatically classifies folders:

- **tv_show_with_seasons**: TV show with Season 01, Season 02, etc. folders
- **tv_show_flat**: TV show episodes directly in the folder
- **movie**: Individual movie folder (1-2 video files)
- **collection**: Folder containing multiple subfolders
- **season**: A season folder within a TV show
- **unknown**: Could not determine type

## Supported Video Formats

`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.mpg`, `.mpeg`, `.3gp`, `.ogv`, `.ts`, `.m2ts`

## Use Cases

1. **Inventory**: Know exactly what media files you have
2. **Planning**: Understand folder structure before reorganization
3. **Analysis**: Identify which folders are Jellyfin-ready
4. **Documentation**: Generate reports on media library contents
5. **Validation**: Verify expected files exist
6. **Integration**: Feed file list to Step 2 for reorganization planning

## Tips

- **Large Libraries**: Use depth limit (2-3) to avoid overwhelming output
- **Multiple Sources**: Add all source folders before scanning for combined report
- **Filtering**: Results include only video files, ignoring other content
- **Performance**: Scanning is fast; most time spent on disk I/O
- **Safety**: Read-only operation, no files are modified

## Next Steps

After scanning, use the file list and structure summary for:
- Step 2: Propose Jellyfin-compliant reorganization
- Manual review and verification
- Import into other tools
- Archive/backup planning

## Troubleshooting

**Problem**: Folder shows 0 videos but you know it has content
- Check folder permissions
- Verify file extensions are in supported list
- Check console for error messages

**Problem**: Structure summary truncated
- Increase the "Structure Summary Depth" setting
- Check the JSON file for complete structure

**Problem**: Scan takes too long
- Reduce number of folders in single scan
- Check for network drives (slower than local)
- Verify no symbolic link loops

## Example Workflow

```bash
# 1. Scan your media library
python scripts/media/folder_structure_scanner.py "E:\Media\Unsorted"

# 2. Review the structure summary
cat data/scan_structure_*.json

# 3. Check video count
wc -l data/scan_file_list_*.txt

# 4. Ready for Step 2!
```
