#!/usr/bin/env python3
r"""
Episode Title Analysis Script

Analyzes episode titles in organized TV shows against canonical data.
Identifies titles that need cleaning or correction.

Usage:
    python analyze_episode_titles.py [media_root]

Example:
    python analyze_episode_titles.py "M:\#MEDIA"
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
sys.path.insert(0, '_common')

from media_utils import clean_episode_title, compare_episode_titles
from tv_episode_cache import TVEpisodeCache
from immutable_audit import ImmutableAuditLog
from config_loader import load_config, get_reports_dir

def extract_episode_info(filename: str, show_title: str) -> Optional[Dict[str, Any]]:
    """
    Extract episode information from a Jellyfin-formatted filename.
    
    Handles multiple Jellyfin naming patterns:
    - "S01E01 - Episode Title.ext"
    - "Show Title S01E01.ext" 
    - "Show Title - S01E01 - Episode Title.ext"
    """
    import re
    
    # Remove extension
    name_without_ext = filename.rsplit('.', 1)[0]
    
    # Pattern 1: "S01E01 - Episode Title" (most common Jellyfin format)
    pattern1 = r'^S(\d+)E(\d+(?:-E\d+)?)\s*-\s*(.+)$'
    match1 = re.match(pattern1, name_without_ext, re.IGNORECASE)
    
    if match1:
        season = int(match1.group(1))
        episode = match1.group(2)
        title = match1.group(3).strip()
        return {
            'show_title': show_title,
            'season': season,
            'episode': episode,
            'episode_title': title
        }
    
    # Pattern 2: "Show Title S01E01 [optional title]" (some shows)
    pattern2 = r'^(.+?)\s+S(\d+)E(\d+(?:-E\d+)?)(?:\s+(.+))?$'
    match2 = re.match(pattern2, name_without_ext, re.IGNORECASE)
    
    if match2:
        parsed_show = match2.group(1).strip()
        season = int(match2.group(2))
        episode = match2.group(3)
        title_part = match2.group(4).strip() if match2.group(4) else ""
        
        # Check if show title matches (basic check)
        show_base = show_title.lower().split(' (')[0]  # Remove year
        if show_base not in parsed_show.lower():
            return None
            
        # Use title part if available, otherwise generic
        episode_title = title_part if title_part else f"Episode {episode}"
            
        return {
            'show_title': parsed_show,
            'season': season,
            'episode': episode,
            'episode_title': episode_title
        }
    
    # Pattern 3: "Show Title - S01E01 - Episode Title" (full format)
    pattern3 = r'^(.+?)\s*-\s*S(\d+)E(\d+(?:-E\d+)?)\s*-\s*(.+)$'
    match3 = re.match(pattern3, name_without_ext, re.IGNORECASE)
    
    if match3:
        parsed_show = match3.group(1).strip()
        season = int(match3.group(2))
        episode = match3.group(3)
        title = match3.group(4).strip()
        
        # Check if show title matches (basic check)
        show_base = show_title.lower().split(' (')[0]  # Remove year
        if show_base not in parsed_show.lower():
            return None
            
        return {
            'show_title': parsed_show,
            'season': season,
            'episode': episode,
            'episode_title': title
        }
    
    return None

def analyze_tv_shows(tv_show_paths: List[str]) -> Dict[str, Any]:
    """
    Analyze all TV shows in the configured paths for episode title issues.
    """
    episode_cache = TVEpisodeCache()
    results = {
        'total_shows': 0,
        'total_episodes': 0,
        'issues_found': 0,
        'shows': {}
    }

    # Get all show directories from all configured paths
    show_dirs = []
    for tv_root_str in tv_show_paths:
        tv_root = Path(tv_root_str)
        if not tv_root.exists():
            print(f"[SKIP] TV Shows directory not found: {tv_root}")
            continue

        show_dirs.extend([d for d in tv_root.iterdir() if d.is_dir()])

    results['total_shows'] = len(show_dirs)

    print(f"[INFO] Analyzing {len(show_dirs)} TV shows...")

    for show_dir in sorted(show_dirs):
        show_title = show_dir.name
        print(f"🔍 Analyzing: {show_title}")
        
        show_results = {
            'episodes': 0,
            'issues': [],
            'canonical_available': False
        }
        
        # Check if we have canonical data
        canonical_data = episode_cache.get_cached_episode_data(show_title)
        if canonical_data:
            show_results['canonical_available'] = True
        
        # Find all video files in this show
        video_extensions = ['*.mkv', '*.mp4', '*.avi']
        episode_files = []
        for ext in video_extensions:
            episode_files.extend(show_dir.rglob(ext))
        
        show_results['episodes'] = len(episode_files)
        results['total_episodes'] += len(episode_files)
        
        # Analyze each episode
        for episode_file in episode_files:
            # Get relative path for cleaner output
            try:
                rel_path = episode_file.relative_to(show_dir.parent)
            except:
                rel_path = episode_file
            
            # Extract episode info from filename
            episode_info = extract_episode_info(episode_file.name, show_title)
            if not episode_info:
                show_results['issues'].append({
                    'file': str(rel_path),
                    'type': 'parse_error',
                    'message': 'Could not parse episode information from filename'
                })
                continue
            
            current_title = episode_info['episode_title']
            season = episode_info['season']
            episode = episode_info['episode']
            
            # Get canonical title if available
            canonical_title = None
            if canonical_data and str(season) in canonical_data.get('seasons', {}):
                season_data = canonical_data['seasons'][str(season)]
                # Handle episode ranges like "1-2"
                if '-' in str(episode):
                    # For combined episodes, check first episode
                    first_ep = str(episode).split('-')[0]
                    if first_ep in season_data.get('episodes', {}):
                        canonical_title = season_data['episodes'][first_ep].get('canonical_title')
                elif str(episode) in season_data.get('episodes', {}):
                    canonical_title = season_data['episodes'][str(episode)].get('canonical_title')
            
            # Special handling for anthology series where year is meaningful
            if show_title == "Looney Tunes (1930)":
                # For Looney Tunes, year information is valuable content metadata
                # Skip title cleaning for this anthology series
                pass
            elif canonical_title:
                comparison = compare_episode_titles(current_title, canonical_title)
                
                if comparison['needs_rename']:
                    show_results['issues'].append({
                        'file': str(rel_path),
                        'type': 'title_mismatch',
                        'current_title': current_title,
                        'cleaned_title': comparison['cleaned_title'],
                        'canonical_title': canonical_title,
                        'recommendation': comparison['recommendation'],
                        'confidence': comparison['confidence']
                    })
            else:
                # No canonical data - just check if cleaning would help
                cleaned = clean_episode_title(current_title)
                if cleaned != current_title:
                    show_results['issues'].append({
                        'file': str(rel_path),
                        'type': 'technical_tags',
                        'current_title': current_title,
                        'cleaned_title': cleaned,
                        'canonical_title': None,
                        'recommendation': 'use_cleaned',
                        'confidence': 'medium'
                    })
        
        if show_results['issues']:
            results['issues_found'] += len(show_results['issues'])
            results['shows'][show_title] = show_results
            print(f"   ⚠️  Found {len(show_results['issues'])} issues")
        else:
            print(f"   ✅ No issues found")
    
    return results

def main():
    print("[INFO] Episode Title Analysis")
    print("=" * 40)

    # Load configuration
    config = load_config()
    tv_show_paths = config['media_paths']['tv_shows']

    print(f"[INFO] Analyzing TV shows in {len(tv_show_paths)} configured paths")

    # Run analysis
    results = analyze_tv_shows(tv_show_paths)
    
    # Display summary
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 40)
    print(f"Total shows analyzed: {results['total_shows']}")
    print(f"Total episodes found: {results['total_episodes']}")
    print(f"Issues found: {results['issues_found']}")
    
    if results['issues_found'] > 0:
        print(f"\n🔧 RECOMMENDED FIXES:")
        print("-" * 40)
        
        for show_title, show_data in results['shows'].items():
            if show_data['issues']:
                print(f"\n📺 {show_title} ({len(show_data['issues'])} issues):")
                
                for issue in show_data['issues'][:5]:  # Show first 5 per show
                    print(f"  📄 {issue['file']}")
                    
                    if issue['type'] == 'parse_error':
                        print(f"     Issue: {issue['message']}")
                    else:
                        print(f"     Current: \"{issue.get('current_title', 'N/A')}\"")
                        
                        if issue.get('canonical_title'):
                            print(f"     Canonical: \"{issue['canonical_title']}\"")
                        
                        if issue.get('cleaned_title') and issue['cleaned_title'] != issue.get('current_title'):
                            print(f"     Cleaned: \"{issue['cleaned_title']}\"")
                        
                        print(f"     Recommendation: {issue.get('recommendation', 'unknown')} ({issue.get('confidence', 'unknown')})")
                    
                    print()
                
                if len(show_data['issues']) > 5:
                    print(f"  ... and {len(show_data['issues']) - 5} more issues")
    
    # Save detailed results
    output_file = get_reports_dir() / 'episode_title_analysis.json'
    output_file.parent.mkdir(exist_ok=True, parents=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Detailed results saved to: {output_file}")

    if results['issues_found'] > 0:
        print(f"\n[INFO] Next step: Run episode title fixes on a test show first")
        print(f"   python fix_episode_titles.py \"Test Show Name\"")
    else:
        print(f"\n[OK] All episode titles look good!")

if __name__ == "__main__":
    main()