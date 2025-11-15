#!/usr/bin/env python3
"""
Diagnose Monk Episode Mismatch

This script helps identify which Monk episode files have content that doesn't match their filenames.
It will extract metadata from the video files to help determine the actual episode content.
"""

import subprocess
import json
from pathlib import Path
import re

def get_video_metadata(video_path: Path) -> dict:
    """Extract metadata from video file using ffprobe."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except Exception as e:
        print(f"Error reading metadata from {video_path.name}: {e}")
        return {}

def extract_episode_from_filename(filename: str) -> dict:
    """Extract season and episode number from filename."""
    match = re.search(r'S(\d+)E(\d+)', filename, re.IGNORECASE)
    if match:
        return {
            'season': int(match.group(1)),
            'episode': int(match.group(2))
        }
    return {}

def extract_title_from_filename(filename: str) -> str:
    """Extract episode title from filename."""
    # Pattern: "Monk (2002) - S01E04 - Mr Monk Meets Dale the Whale.mkv"
    match = re.search(r'S\d+E\d+ - (.+?)\.(?:mkv|mp4|avi)', filename, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def analyze_monk_episodes():
    """Analyze all Monk episodes and report potential mismatches."""
    monk_dir = Path(r"Q:\#MEDIA\TV Shows\Monk (2002)")
    
    if not monk_dir.exists():
        print(f"❌ Monk directory not found: {monk_dir}")
        return
    
    print("=" * 80)
    print("MONK EPISODE DIAGNOSTIC REPORT")
    print("=" * 80)
    print()
    print("This report shows all Monk episodes with their filenames and metadata.")
    print("Look for discrepancies between filename and actual content.")
    print()
    
    # Process each season
    for season_dir in sorted(monk_dir.glob("Season *")):
        if not season_dir.is_dir():
            continue
        
        season_match = re.search(r'Season (\d+)', season_dir.name)
        if not season_match:
            continue
        
        season_num = int(season_match.group(1))
        print(f"\n{'=' * 80}")
        print(f"SEASON {season_num:02d}")
        print(f"{'=' * 80}\n")
        
        # Get all video files
        video_files = []
        for ext in ['*.mkv', '*.mp4', '*.avi']:
            video_files.extend(season_dir.glob(ext))
        
        video_files = sorted(video_files)
        
        for video_file in video_files:
            # Extract info from filename
            ep_info = extract_episode_from_filename(video_file.name)
            title_from_filename = extract_title_from_filename(video_file.name)
            
            if not ep_info:
                continue
            
            print(f"File: {video_file.name}")
            print(f"  Season: {ep_info['season']:02d}, Episode: {ep_info['episode']:02d}")
            print(f"  Title from filename: {title_from_filename}")
            
            # Get video metadata
            metadata = get_video_metadata(video_file)
            
            if metadata:
                # Check for title in metadata
                format_info = metadata.get('format', {})
                tags = format_info.get('tags', {})
                
                # Look for title in various tag fields
                metadata_title = (
                    tags.get('title') or 
                    tags.get('TITLE') or 
                    tags.get('Title') or
                    tags.get('episode_id') or
                    tags.get('EPISODE_ID')
                )
                
                if metadata_title:
                    print(f"  Title from metadata: {metadata_title}")
                    
                    # Check if titles match
                    if metadata_title.lower() != title_from_filename.lower():
                        print(f"  ⚠️  WARNING: Title mismatch detected!")
                else:
                    print(f"  No title found in video metadata")
                
                # Show file size and duration
                duration = format_info.get('duration', 'unknown')
                size_mb = int(format_info.get('size', 0)) / (1024 * 1024)
                print(f"  Duration: {duration}s, Size: {size_mb:.1f} MB")
            else:
                print(f"  ⚠️  Could not read video metadata")
            
            print()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("1. Review the warnings above for title mismatches")
    print("2. Watch the flagged episodes to verify actual content")
    print("3. If content doesn't match filename, files need to be renamed")
    print("4. Consider creating a mapping file to track corrections needed")
    print()
    print("IMPORTANT: The issue you reported (S01E05 showing S01E04 content)")
    print("suggests the video files themselves are in the wrong order.")
    print("This requires manual verification by watching the episodes.")
    print()

if __name__ == '__main__':
    analyze_monk_episodes()
