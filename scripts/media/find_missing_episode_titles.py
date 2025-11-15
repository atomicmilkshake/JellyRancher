#!/usr/bin/env python3
"""
TV Show Filename Validation - CRITICAL: Episode Titles Must Be Present

Scans all TV show files and identifies those MISSING episode titles in filenames.
Episode titles are MANDATORY - files like "Breaking Bad S01E01.mkv" are WRONG.
Correct format: "Breaking Bad S01E01 - Pilot.mkv"

This script also identifies subtitle mismatches where .srt files don't match
video filenames due to missing episode titles.
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / '_common'))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

# Drives to scan
DRIVES_TO_SCAN = ['M:', 'L:', 'Q:', 'S:', 'W:', 'E:']

# Cache directory
TV_SHOWS_CACHE_DIR = Path(__file__).parent / '_common' / 'tv_episode_cache'

# Pattern: Show Name S##E## with optional episode title
# MUST have episode title to be correct
EPISODE_PATTERN = re.compile(
    r'^(.+?)\s+S(\d{2})E(\d{2})(?:-E(\d{2}))?(?:\s+-\s+(.+?))?$',
    re.IGNORECASE
)


def load_episode_cache(show_name: str) -> Optional[Dict]:
    """Load episode cache for a show."""
    cache_name = show_name.lower().replace(' ', '_').replace(':', '')
    cache_file = TV_SHOWS_CACHE_DIR / f"{cache_name}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def parse_episode_filename(filename: str) -> Optional[Dict]:
    """Parse episode filename and check for episode title presence."""
    name_no_ext = Path(filename).stem
    
    match = EPISODE_PATTERN.match(name_no_ext)
    if match:
        show_name = match.group(1).strip()
        season = int(match.group(2))
        episode = int(match.group(3))
        episode_end = int(match.group(4)) if match.group(4) else None
        episode_title = match.group(5).strip() if match.group(5) else None
        
        return {
            'show_name': show_name,
            'season': season,
            'episode': episode,
            'episode_end': episode_end,
            'title': episode_title,
            'filename': filename,
            'has_title': episode_title is not None
        }
    return None


def get_canonical_title(show_name: str, season: int, episode: int, cache: Optional[Dict]) -> Optional[str]:
    """Get canonical episode title from cache."""
    if not cache:
        return None
    
    episodes = cache.get('episodes', [])
    for ep in episodes:
        if ep.get('season') == season and ep.get('episode') == episode:
            return ep.get('title')
    
    return None


def scan_tv_shows(drive: str) -> List[Dict]:
    """Scan for all TV show files."""
    files = []
    
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
                
                if item.suffix.lower() not in ['.mkv', '.mp4', '.avi', '.mov', '.flv', '.m4v']:
                    continue
                
                parsed = parse_episode_filename(item.name)
                if parsed:
                    parsed['full_path'] = str(item)
                    parsed['drive'] = drive
                    parsed['show_dir'] = show_dir.name
                    parsed['ext'] = item.suffix
                    files.append(parsed)
    
    return files


def find_subtitle_for_video(video_file: Path) -> Optional[Path]:
    """Find corresponding subtitle file for a video."""
    video_stem = video_file.stem
    video_dir = video_file.parent
    
    # Look for .srt files with same stem or .{lang}.srt
    for srt_file in video_dir.glob(f"{video_stem}*.srt"):
        if srt_file.is_file():
            return srt_file
    
    return None


def main():
    console.print("[bold cyan]TV SHOW FILENAME VALIDATION - EPISODE TITLES REQUIRED")
    console.print("[bold cyan]Scanning all drives for missing episode titles...\n")
    
    all_files = []
    all_issues = []
    subtitle_mismatches = []
    
    # Scan all drives
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Scanning drives...", total=None)
        
        for drive in DRIVES_TO_SCAN:
            try:
                progress.update(task, description=f"Scanning {drive}...")
                files = scan_tv_shows(drive)
                all_files.extend(files)
            except Exception as e:
                console.print(f"[yellow]Warning: {drive}: {e}")
    
    console.print(f"\n[cyan]Found {len(all_files)} TV show files")
    
    # Validate each file
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Validating filenames...", total=len(all_files))
        
        for file_info in all_files:
            # CRITICAL: Episode title must be present
            if not file_info['has_title']:
                cache = load_episode_cache(file_info['show_name'])
                canonical_title = get_canonical_title(
                    file_info['show_name'],
                    file_info['season'],
                    file_info['episode'],
                    cache
                )
                
                all_issues.append({
                    'drive': file_info['drive'],
                    'show': file_info['show_name'],
                    'filename': file_info['filename'],
                    'path': file_info['full_path'],
                    'season': file_info['season'],
                    'episode': file_info['episode'],
                    'problem': 'Missing episode title',
                    'canonical_title': canonical_title,
                    'correct_name': f"{file_info['show_name']} S{file_info['season']:02d}E{file_info['episode']:02d} - {canonical_title}{file_info['ext']}" if canonical_title else None,
                    'severity': 'CRITICAL'
                })
            
            # Check for subtitle mismatch
            video_path = Path(file_info['full_path'])
            srt_file = find_subtitle_for_video(video_path)
            if srt_file and not file_info['has_title']:
                subtitle_mismatches.append({
                    'drive': file_info['drive'],
                    'video': file_info['filename'],
                    'subtitle': srt_file.name,
                    'issue': 'Subtitle filename may not match video (due to missing title in video)'
                })
            
            progress.advance(task)
    
    # Generate report
    console.print("\n" + "="*90)
    console.print("[bold cyan]VALIDATION REPORT - EPISODE TITLE REQUIREMENTS")
    console.print("="*90 + "\n")
    
    if not all_issues:
        console.print("[bold green]OK: All TV show files have correct filenames with episode titles!")
        console.print(f"   Total files checked: {len(all_files)}")
        console.print("   Issues found: 0\n")
    else:
        console.print(f"[bold red]CRITICAL: {len(all_issues)} files have WRONG naming (missing episode titles)\n")
        
        # Group by show
        by_show = defaultdict(list)
        for issue in all_issues:
            by_show[issue['show']].append(issue)
        
        # Display issues
        console.print("[bold red]FILES REQUIRING CORRECTION:\n")
        
        for show_name in sorted(by_show.keys()):
            issues = by_show[show_name]
            console.print(f"[bold yellow]{show_name}: {len(issues)} files")
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Season", style="cyan", width=8)
            table.add_column("Episode", style="cyan", width=8)
            table.add_column("Current (WRONG)", style="red", width=50)
            table.add_column("Correct Format", style="green", width=50)
            
            for issue in sorted(issues, key=lambda x: (x['season'], x['episode']))[:15]:
                table.add_row(
                    f"S{issue['season']:02d}",
                    f"E{issue['episode']:02d}",
                    issue['filename'][:48],
                    (issue['correct_name'][:48] if issue['correct_name'] else "N/A")
                )
            
            if len(issues) > 15:
                console.print(f"... and {len(issues) - 15} more")
            
            console.print(table)
            console.print()
    
    # Subtitle mismatch report
    if subtitle_mismatches:
        console.print("\n[bold yellow]SUBTITLE MISMATCH WARNINGS:\n")
        console.print(f"[yellow]{len(subtitle_mismatches)} subtitle files may have naming mismatches:")
        
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Drive", style="cyan")
        table.add_column("Video File", style="white", width=50)
        table.add_column("Subtitle File", style="white", width=50)
        
        for match in subtitle_mismatches[:20]:
            table.add_row(
                match['drive'],
                match['video'][:48],
                match['subtitle'][:48]
            )
        
        console.print(table)
        if len(subtitle_mismatches) > 20:
            console.print(f"\n[yellow]... and {len(subtitle_mismatches) - 20} more")
    
    # Summary
    console.print("\n" + "="*90)
    summary_stats = {
        'total_files': len(all_files),
        'files_with_issues': len(all_issues),
        'subtitle_mismatches': len(subtitle_mismatches),
        'needs_renaming': len(all_issues)
    }
    
    console.print(f"\n[bold]SUMMARY:")
    console.print(f"  Total files scanned: {summary_stats['total_files']}")
    console.print(f"  Files missing episode titles: {summary_stats['files_with_issues']}")
    console.print(f"  Potential subtitle mismatches: {summary_stats['subtitle_mismatches']}")
    
    # Save report
    report_file = Path(__file__).parent.parent / 'reports' / 'tv_filename_issues.json'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_files_scanned': summary_stats['total_files'],
            'critical_issues': len(all_issues),
            'subtitle_mismatches': len(subtitle_mismatches),
            'issues': all_issues,
            'subtitle_mismatches': subtitle_mismatches,
            'drives_scanned': DRIVES_TO_SCAN
        }, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[cyan]Detailed report saved to: {report_file}")
    
    return len(all_issues)


if __name__ == '__main__':
    try:
        issues_found = main()
        sys.exit(0 if issues_found == 0 else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
