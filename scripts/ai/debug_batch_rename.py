#!/usr/bin/env python3
"""Debug which files the batch rename script finds"""

import re
from pathlib import Path
from collections import defaultdict

DRIVES_TO_SCAN = ['M:', 'L:', 'Q:', 'S:', 'W:', 'E:']

# Episode pattern (without title)
EPISODE_PATTERN = re.compile(
    r'^(.+?)\s+S(\d{2})E(\d{2})(?:-E(\d{2}))?$',
    re.IGNORECASE
)

def parse_episode_filename(filename: str):
    """Parse episode filename WITHOUT title."""
    name_no_ext = Path(filename).stem
    
    match = EPISODE_PATTERN.match(name_no_ext)
    if match:
        show_name = match.group(1).strip()
        season = int(match.group(2))
        episode = int(match.group(3))
        episode_end = int(match.group(4)) if match.group(4) else None
        
        return {
            'show_name': show_name,
            'season': season,
            'episode': episode,
            'episode_end': episode_end,
            'filename': filename
        }
    return None

def find_files_needing_rename(drive: str):
    """Find all TV files missing episode titles."""
    files_to_rename = []
    
    for tv_root in [f"{drive}/#MEDIA/TV Shows", f"{drive}\\#MEDIA\\TV Shows"]:
        tv_path = Path(tv_root)
        if not tv_path.exists():
            continue
        
        for show_dir in tv_path.iterdir():
            if not show_dir.is_dir() or show_dir.name.startswith('.'):
                continue
            
            if show_dir.name in ['Blu-Prints', 'Deleted Scenes', 'Featurettes']:
                continue
            
            for item in show_dir.rglob('*'):
                if not item.is_file():
                    continue
                
                # Video files
                if item.suffix.lower() in ['.mkv', '.mp4', '.avi', '.mov', '.flv', '.m4v']:
                    parsed = parse_episode_filename(item.name)
                    if parsed:
                        parsed['full_path'] = str(item)
                        parsed['drive'] = drive
                        parsed['file_type'] = 'video'
                        parsed['ext'] = item.suffix
                        files_to_rename.append(parsed)
    
    return files_to_rename

# Scan for files
files_to_rename = []

for drive in DRIVES_TO_SCAN:
    try:
        print(f"Scanning {drive}...")
        files = find_files_needing_rename(drive)
        files_to_rename.extend(files)
    except Exception as e:
        print(f"  Error: {e}")

# Analyze
by_show = defaultdict(list)
for file_info in files_to_rename:
    show = file_info['show_name']
    by_show[show].append(file_info)

print(f"\nFound {len(files_to_rename)} total files")
print("\nBy show:")
for show, files in sorted(by_show.items(), key=lambda x: -len(x[1])):
    print(f"  {show}: {len(files)} files")
    for f in files[:2]:
        print(f"    - {f['filename']}")
