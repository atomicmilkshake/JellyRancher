#!/usr/bin/env python3
"""
Scan entire media library for multi-episode files (S01E01-E02, S01E01E02, etc.)
to identify all instances that may need NFO files
"""

import re
from pathlib import Path
from collections import defaultdict

# All media drives
MEDIA_ROOTS = [
    Path(r"E:\#MEDIA\TV Shows"),
    Path(r"M:\#MEDIA\TV Shows"),
    Path(r"Q:\#MEDIA\TV Shows"),
    Path(r"L:\#MEDIA\TV Shows"),
    Path(r"S:\#MEDIA\TV Shows"),
    Path(r"W:\#MEDIA\TV Shows"),
]

# Regex patterns for multi-episode files
MULTI_EP_PATTERNS = [
    r'[Ss](\d+)[Ee](\d+)-?[Ee](\d+)',      # S01E01-E02 or S01E01E02
    r'[Ss](\d+)[Ee](\d+)-(\d+)',           # S01E01-02
    r'[Ss](\d+)[Ee](\d+)\s*-\s*[Ee](\d+)', # S01E01 - E02
]

def find_multi_episode_files():
    """Scan all media drives for multi-episode files"""
    
    print("=" * 80)
    print("SCANNING FOR MULTI-EPISODE FILES")
    print("=" * 80)
    
    all_multi_ep_files = []
    by_show = defaultdict(list)
    
    for media_root in MEDIA_ROOTS:
        if not media_root.exists():
            print(f"\n⚠️  Skipping {media_root} (not found)")
            continue
        
        print(f"\n📂 Scanning: {media_root}")
        
        # Find all video files
        video_extensions = ['.mkv', '.mp4', '.avi', '.m4v', '.ts']
        
        for ext in video_extensions:
            for video_file in media_root.rglob(f"*{ext}"):
                filename = video_file.name
                
                # Check if filename matches multi-episode pattern
                for pattern in MULTI_EP_PATTERNS:
                    match = re.search(pattern, filename)
                    if match:
                        # Extract show name from path
                        show_name = video_file.parent.parent.name
                        season_num = match.group(1)
                        ep_start = match.group(2)
                        ep_end = match.group(3)
                        
                        # Check if NFO file exists
                        nfo_file = video_file.with_suffix('.nfo')
                        has_nfo = nfo_file.exists()
                        
                        file_info = {
                            'path': video_file,
                            'show': show_name,
                            'season': season_num,
                            'ep_start': ep_start,
                            'ep_end': ep_end,
                            'has_nfo': has_nfo,
                            'drive': video_file.drive
                        }
                        
                        all_multi_ep_files.append(file_info)
                        by_show[show_name].append(file_info)
                        break
    
    # Report findings
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    if not all_multi_ep_files:
        print("\n✅ No multi-episode files found!")
        return
    
    print(f"\n📊 Found {len(all_multi_ep_files)} multi-episode files across {len(by_show)} shows")
    
    # Group by show
    print("\n" + "-" * 80)
    print("BY SHOW:")
    print("-" * 80)
    
    for show_name in sorted(by_show.keys()):
        files = by_show[show_name]
        nfo_count = sum(1 for f in files if f['has_nfo'])
        
        print(f"\n📺 {show_name}")
        print(f"   Total multi-episode files: {len(files)}")
        print(f"   Files with NFO: {nfo_count}")
        print(f"   Files WITHOUT NFO: {len(files) - nfo_count}")
        
        for file_info in files:
            nfo_status = "✓ NFO" if file_info['has_nfo'] else "✗ NO NFO"
            print(f"   {nfo_status} | S{file_info['season']}E{file_info['ep_start']}-E{file_info['ep_end']} | {file_info['drive']} | {file_info['path'].name}")
    
    # Summary of files needing NFO
    files_needing_nfo = [f for f in all_multi_ep_files if not f['has_nfo']]
    
    if files_needing_nfo:
        print("\n" + "=" * 80)
        print(f"⚠️  {len(files_needing_nfo)} FILES NEED NFO FILES")
        print("=" * 80)
        
        for file_info in files_needing_nfo:
            print(f"\n{file_info['show']} - S{file_info['season']}E{file_info['ep_start']}-E{file_info['ep_end']}")
            print(f"  Path: {file_info['path']}")
    else:
        print("\n" + "=" * 80)
        print("✅ ALL MULTI-EPISODE FILES HAVE NFO FILES!")
        print("=" * 80)
    
    # Save detailed report
    report_file = Path("multi_episode_files_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("MULTI-EPISODE FILES REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total files: {len(all_multi_ep_files)}\n")
        f.write(f"Shows affected: {len(by_show)}\n")
        f.write(f"Files needing NFO: {len(files_needing_nfo)}\n\n")
        
        for show_name in sorted(by_show.keys()):
            f.write(f"\n{show_name}\n")
            f.write("-" * 80 + "\n")
            for file_info in by_show[show_name]:
                nfo_status = "HAS_NFO" if file_info['has_nfo'] else "NEEDS_NFO"
                f.write(f"{nfo_status} | {file_info['path']}\n")
    
    print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    find_multi_episode_files()
