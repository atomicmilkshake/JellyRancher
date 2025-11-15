#!/usr/bin/env python3
"""
Comprehensive TV Show Filename Validation Across All Drives

Scans all drives (M:, L:, Q:, S:, W:, E:) for TV show files and validates
filenames against canonical episode data from cached sources.

Features:
- Scans all drives for TV shows
- Compares against cached episode data
- Identifies naming issues (wrong titles, numbering, episode titles)
- Generates detailed report
- Uses rich progress bars and tables
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
from rich.text import Text

console = Console()

# Known TV show locations and their canonical caches
TV_SHOWS_CACHE_DIR = Path(__file__).parent / '_common' / 'tv_episode_cache'

# Drives to scan
DRIVES_TO_SCAN = ['M:', 'L:', 'Q:', 'S:', 'W:', 'E:']

# TV show folder patterns
TV_FOLDER_PATTERN = re.compile(
    r'^(.+?)\s+S(\d{2})E(\d{2})(?:-E(\d{2}))?(?:\s+-\s+(.+?))?$',
    re.IGNORECASE
)


def load_episode_cache(show_name: str) -> Optional[Dict]:
    """Load episode cache for a show if it exists."""
    # Normalize show name for cache lookup
    cache_name = show_name.lower().replace(' ', '_').replace(':', '')
    cache_file = TV_SHOWS_CACHE_DIR / f"{cache_name}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load cache for {show_name}: {e}")
            return None
    return None


def parse_episode_filename(filename: str) -> Optional[Dict]:
    """Parse TV episode filename to extract show name, season, episode, and title."""
    # Remove extension
    name_no_ext = Path(filename).stem
    
    match = TV_FOLDER_PATTERN.match(name_no_ext)
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
            'filename': filename
        }
    return None


def validate_episode_title(show_name: str, season: int, episode: int, 
                          provided_title: Optional[str], cache: Optional[Dict]) -> Tuple[bool, str]:
    """Validate episode title against cache."""
    if not cache:
        return True, "No cache available"
    
    episodes = cache.get('episodes', [])
    
    # Find matching episode
    for ep in episodes:
        if ep.get('season') == season and ep.get('episode') == episode:
            cached_title = ep.get('title', '')
            
            if not provided_title:
                return False, f"Missing title (should be '{cached_title}')"
            
            # Normalize for comparison
            provided_normalized = provided_title.lower().strip()
            cached_normalized = cached_title.lower().strip()
            
            if provided_normalized == cached_normalized:
                return True, "Match"
            else:
                return False, f"Should be '{cached_title}' (got '{provided_title}')"
    
    return False, f"Episode not found in cache (S{season:02d}E{episode:02d})"


def scan_drive_for_tv_shows(drive: str) -> List[Dict]:
    """Scan a drive for TV show files."""
    tv_shows = []
    
    # Try both slash formats
    for tv_root in [f"{drive}/#MEDIA/TV Shows", f"{drive}\\#MEDIA\\TV Shows"]:
        tv_path = Path(tv_root)
        if not tv_path.exists():
            continue
        
        # Iterate through show directories
        for show_item in tv_path.iterdir():
            if not show_item.is_dir():
                continue
            
            # Skip special folders
            if show_item.name.startswith('.') or show_item.name in ['Blu-Prints', 'Deleted Scenes', 'Featurettes']:
                continue
            
            show_name = show_item.name
            
            # Look for video files directly or in season subdirectories
            for item in show_item.rglob('*'):
                if not item.is_file():
                    continue
                
                # Check for video extensions
                if item.suffix.lower() not in ['.mkv', '.mp4', '.avi', '.mov', '.flv', '.m4v']:
                    continue
                
                parsed = parse_episode_filename(item.name)
                if parsed:
                    parsed['full_path'] = str(item)
                    parsed['drive'] = drive
                    parsed['show_dir'] = show_name
                    tv_shows.append(parsed)
    
    return tv_shows


def main():
    console.print("[bold cyan]TV SHOW FILENAME VALIDATION - SCANNING ALL DRIVES")
    console.print("[bold cyan]Checking naming against canonical episode data...\n")
    
    # Scan all drives
    all_shows_by_drive = defaultdict(list)
    all_issues = []
    total_files_scanned = 0
    
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
                tv_shows = scan_drive_for_tv_shows(drive)
                all_shows_by_drive[drive] = tv_shows
                total_files_scanned += len(tv_shows)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not scan {drive}: {e}")
    
    console.print(f"\n✓ Found {total_files_scanned} TV show files across all drives\n")
    
    # Validate against caches
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Validating filenames...", total=total_files_scanned)
        
        for drive, shows in all_shows_by_drive.items():
            for show in shows:
                show_name = show['show_name']
                cache = load_episode_cache(show_name)
                
                # Validate title
                title_valid, title_msg = validate_episode_title(
                    show_name, show['season'], show['episode'], 
                    show['title'], cache
                )
                
                if not title_valid:
                    all_issues.append({
                        'drive': drive,
                        'filename': show['filename'],
                        'path': show['full_path'],
                        'show': show_name,
                        'season': show['season'],
                        'episode': show['episode'],
                        'issue': title_msg,
                        'severity': 'high' if 'Missing title' in title_msg else 'medium'
                    })
                
                progress.advance(task)
    
    # Generate report
    console.print("\n" + "="*80)
    console.print("[bold cyan]VALIDATION REPORT")
    console.print("="*80 + "\n")
    
    if not all_issues:
        console.print("[bold green]OK: All TV show filenames are correctly formatted!")
        console.print(f"   Total files checked: {total_files_scanned}")
        console.print("   Issues found: 0\n")
    else:
        console.print(f"[bold yellow]WARNING: {len(all_issues)} files need attention\n")
        
        # Group by severity
        high_severity = [i for i in all_issues if i['severity'] == 'high']
        medium_severity = [i for i in all_issues if i['severity'] == 'medium']
        
        if high_severity:
            console.print(f"[bold red]HIGH PRIORITY ({len(high_severity)} files):")
            table = Table(show_header=True, header_style="bold red")
            table.add_column("Drive", style="cyan")
            table.add_column("Show", style="yellow")
            table.add_column("File", style="white")
            table.add_column("Issue", style="red")
            
            for issue in high_severity[:20]:  # Show first 20
                table.add_row(
                    issue['drive'],
                    issue['show'],
                    issue['filename'],
                    issue['issue']
                )
            
            console.print(table)
            if len(high_severity) > 20:
                console.print(f"\n[yellow]... and {len(high_severity) - 20} more high priority issues")
            console.print()
        
        if medium_severity:
            console.print(f"[bold yellow]MEDIUM PRIORITY ({len(medium_severity)} files):")
            table = Table(show_header=True, header_style="bold yellow")
            table.add_column("Drive", style="cyan")
            table.add_column("Show", style="yellow")
            table.add_column("File", style="white")
            table.add_column("Issue", style="yellow")
            
            for issue in medium_severity[:20]:  # Show first 20
                table.add_row(
                    issue['drive'],
                    issue['show'],
                    issue['filename'],
                    issue['issue']
                )
            
            console.print(table)
            if len(medium_severity) > 20:
                console.print(f"\n[yellow]... and {len(medium_severity) - 20} more medium priority issues")
            console.print()
    
    # Summary panel
    summary_text = f"""
Drive Summary:
"""
    for drive in DRIVES_TO_SCAN:
        count = len(all_shows_by_drive.get(drive, []))
        if count > 0:
            issues = len([i for i in all_issues if i['drive'] == drive])
            status = f"[green]OK[/green]" if issues == 0 else f"[yellow]ISSUES[/yellow]"
            summary_text += f"\n  {status} {drive}: {count} files, {issues} issues"
    
    console.print(Panel(summary_text, title="[bold]Summary", expand=False))
    
    # Save detailed report
    report_file = Path(__file__).parent.parent / 'reports' / 'tv_filename_validation.json'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_files_scanned': total_files_scanned,
            'total_issues': len(all_issues),
            'high_priority': len([i for i in all_issues if i['severity'] == 'high']),
            'medium_priority': len([i for i in all_issues if i['severity'] == 'medium']),
            'issues': all_issues,
            'drives_scanned': DRIVES_TO_SCAN
        }, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[cyan]Detailed report saved to: {report_file}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
