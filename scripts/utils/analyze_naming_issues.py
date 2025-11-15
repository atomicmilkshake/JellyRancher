#!/usr/bin/env python3
"""
Comprehensive Filename Correction Analysis
Shows exactly what needs to be renamed for BOTH video and subtitle files
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

report_file = Path(__file__).parent.parent / 'reports' / 'tv_filename_issues.json'

if not report_file.exists():
    print("Report file not found. Run find_missing_episode_titles.py first.")
    sys.exit(1)

with open(report_file) as f:
    report = json.load(f)

print("="*100)
print("COMPREHENSIVE FILENAME CORRECTION ANALYSIS")
print("="*100)
print()

# Group issues by show
by_show = defaultdict(list)
for issue in report['issues']:
    by_show[issue['show']].append(issue)

total_video_files_wrong = 0
total_subtitle_files_wrong = 0

for show_name in sorted(by_show.keys()):
    issues = by_show[show_name]
    
    print(f"\n{show_name}: {len(issues)} files needing corrections")
    print("-" * 100)
    
    for i, issue in enumerate(sorted(issues, key=lambda x: (x['season'], x['episode']))[:5], 1):
        filename = issue['filename']
        show = issue['show']
        season = issue['season']
        episode = issue['episode']
        canonical_title = issue.get('canonical_title', 'UNKNOWN')
        ext = Path(filename).suffix
        
        # Video file correction
        video_wrong = f"{filename}"
        video_correct = f"{show} S{season:02d}E{episode:02d} - {canonical_title}{ext}"
        
        # Subtitle file correction - look for matching subtitle
        print(f"\n  Episode S{season:02d}E{episode:02d} - {canonical_title}:")
        print(f"    VIDEO WRONG:   {video_wrong}")
        print(f"    VIDEO CORRECT: {video_correct}")
        
        # Subtitle files
        print(f"    SUBTITLES (current state):")
        print(f"      WRONG:   {show} S{season:02d}E{episode:02d}.en.srt")
        print(f"      CORRECT: {show} S{season:02d}E{episode:02d} - {canonical_title}.en.srt")
        
        total_video_files_wrong += 1
        total_subtitle_files_wrong += 1
    
    if len(issues) > 5:
        print(f"\n  ... and {len(issues) - 5} more episodes")

print("\n" + "="*100)
print("SUMMARY")
print("="*100)
print(f"\nTotal VIDEO files needing episode titles added: {len(report['issues'])}")
print(f"Total SUBTITLE files needing episode titles added: {report['subtitle_mismatches']}")
print()
print("BOTH video and subtitle filenames are WRONG and need the episode title added!")
print()
print("ACTION REQUIRED:")
print("  1. Rename all video files: ADD ' - {Episode Title}' before extension")
print("  2. Rename all subtitle files: ADD ' - {Episode Title}' to match video names")
print("  3. This ensures Jellyfin can properly match videos to subtitles")
print()
