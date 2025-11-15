#!/usr/bin/env python3
"""
Pre-cache Wikipedia episode data for TV shows in S:\#MEDIA

This script scans S:\#MEDIA, identifies all TV shows,
and pre-caches their Wikipedia episode data before running the organizer.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, '_common')

from tv_episode_cache import TVEpisodeCache
from media_utils import normalize_windows_path
from logger import ProjectLogger

def validate_episode_data(episode_data: dict, show_title: str) -> dict:
    """Validate episode data quality and completeness."""
    if not episode_data:
        return {
            'is_valid': False,
            'reason': 'No episode data',
            'details': 'Episode data is None or empty'
        }
    
    seasons = episode_data.get('seasons', {})
    if not seasons:
        return {
            'is_valid': False,
            'reason': 'No seasons found',
            'details': 'Episode data contains no season information'
        }
    
    total_episodes = sum(len(season.get('episodes', {})) for season in seasons.values())
    if total_episodes == 0:
        return {
            'is_valid': False,
            'reason': 'No episodes found',
            'details': 'All seasons contain zero episodes'
        }
    
    # Check for reasonable episode counts (most shows have at least 1 episode per season)
    empty_seasons = [s for s, data in seasons.items() if len(data.get('episodes', {})) == 0]
    if empty_seasons:
        return {
            'is_valid': False,
            'reason': 'Empty seasons detected',
            'details': f'Seasons {empty_seasons} have no episodes'
        }
    
    # Check for episode numbering consistency
    for season_num, season_data in seasons.items():
        episodes = season_data.get('episodes', {})
        if episodes:
            episode_nums = sorted([int(k) for k in episodes.keys()])
            expected_nums = list(range(1, len(episodes) + 1))
            if episode_nums != expected_nums:
                return {
                    'is_valid': False,
                    'reason': 'Inconsistent episode numbering',
                    'details': f'Season {season_num}: expected {expected_nums}, got {episode_nums}'
                }
    
    return {
        'is_valid': True,
        'reason': 'Valid episode data',
        'details': f'{len(seasons)} seasons, {total_episodes} total episodes'
    }

def extract_show_name_from_directory(dir_name: str) -> str:
    """Extract canonical show name from directory name with technical tags."""
    import re
    
    # Common patterns to clean up
    # Remove technical tags like (2160p, 1080p, WEB-DL, BluRay, etc.)
    patterns_to_remove = [
        r'\(\d{4}p[^)]*\)',  # (2160p HDR DSNP WEB-DL x265 HEVC 10bit DDP 5.1 Vyndros)
        r'\(\d{3,4}p[^)]*\)',  # (1080p WEB-DL x265 HEVC 10bit AAC 2.0 RCVR)
        r'S\d{1,2}[^)]*\)',  # Season patterns at end
        r'\.S\d{1,2}[^.]*',  # .S01.1080p.BluRay.x265-RARBG
        r'-\w+$',  # -RARBG, -Vyndros, etc.
        r'\s*\([^)]*RARBG[^)]*\)',  # (1080p BluRay x265-RARBG)
        r'\s*\([^)]*Vyndros[^)]*\)',  # (2160p HDR DSNP WEB-DL x265 HEVC 10bit DDP 5.1 Vyndros)
        r'\s*\([^)]*RCVR[^)]*\)',  # (1080p WEB-DL x265 HEVC 10bit AAC 2.0 RCVR)
    ]
    
    cleaned = dir_name
    
    # Apply cleanup patterns
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra spaces and dots
    cleaned = re.sub(r'[._]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    # Handle specific known cases
    if 'Star.Trek.Enterprise' in dir_name:
        return 'Star Trek Enterprise (2001)'
    elif 'Star Wars Andor' in dir_name:
        return 'Andor (2022)'
    elif 'Andor' in cleaned and '(2022)' in cleaned:
        return 'Andor (2022)'
    elif 'Baby Looney Tunes' in cleaned:
        return 'Baby Looney Tunes (2002)'
    elif 'That.70s.Show' in dir_name:
        return "That '70s Show (1998)"
    
    # For other cases, try to extract title and year
    # Look for pattern: Title (Year)
    year_match = re.search(r'\((\d{4})\)', cleaned)
    if year_match:
        title_part = cleaned[:year_match.start()].strip()
        year = year_match.group(1)
        return f"{title_part} ({year})"
    
    # If no year found, return cleaned version
    return cleaned

def get_show_titles_from_directory(media_root: str) -> list[str]:
    """Extract show titles from directory structure."""
    media_path = Path(media_root)
    show_titles = []

    # Check root level shows
    for item in media_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Skip common non-show directories
            if item.name.lower() not in ['movies', 'tv shows', 'backups', '.venv']:
                show_titles.append(item.name)

    # Check TV Shows subdirectory
    tv_shows_path = media_path / "TV Shows"
    if tv_shows_path.exists():
        for item in tv_shows_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                show_titles.append(item.name)

    return show_titles

def main():
    print("🔍 Pre-caching Wikipedia episode data for S:\\#MEDIA")
    print("=" * 60)

    # Initialize logger
    logger = ProjectLogger("pre_cache_shows_s")
    logger.info("Starting pre-cache operation for S:\\#MEDIA")

    # Target directory
    media_root = r"S:\#MEDIA"

    # Normalize path for Windows
    media_root_path = Path(media_root)
    media_root = str(normalize_windows_path(media_root_path))

    if not os.path.exists(media_root):
        error_msg = f"Media root directory not found: {media_root}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return

    print(f"📁 Scanning: {media_root}")
    logger.info(f"Scanning media root: {media_root}")

    # Get all show titles
    show_titles = get_show_titles_from_directory(media_root)
    print(f'📺 Found {len(show_titles)} TV shows to cache:')
    
    # Extract canonical names and create mapping
    canonical_titles = {}
    for dir_name in show_titles:
        canonical_name = extract_show_name_from_directory(dir_name)
        canonical_titles[dir_name] = canonical_name
        print(f'   • {dir_name}')
        print(f'     └─ Canonical: {canonical_name}')
    
    show_titles = list(canonical_titles.values())  # Use canonical names for caching

    # Initialize cache
    cache = TVEpisodeCache()

    # Cache each show
    successful = 0
    failed = 0

    for i, show_title in enumerate(show_titles, 1):
        print(f"\n{i}/{len(show_titles)}: Caching '{show_title}'...")
        logger.info(f"Processing show {i}/{len(show_titles)}: '{show_title}'")
        print(f"   Show ID: {cache.get_show_id(show_title)}")

        try:
            # Check if already cached
            existing_data = cache.get_cached_episode_data(show_title)
            if existing_data and cache.is_cache_valid(cache.get_show_id(show_title)):
                seasons = len(existing_data.get('seasons', {}))
                episodes = sum(len(season.get('episodes', {})) for season in existing_data.get('seasons', {}).values())
                print(f"   ✅ Already cached ({episodes} episodes across {seasons} seasons)")
                logger.info(f"Show '{show_title}' already cached: {episodes} episodes, {seasons} seasons")
                successful += 1
                continue

            # Fetch new data
            episode_data = cache.get_episode_data(show_title, force_refresh=True)

            if episode_data:
                # Validate data quality
                validation = validate_episode_data(episode_data, show_title)
                if validation['is_valid']:
                    seasons = len(episode_data.get('seasons', {}))
                    episodes = sum(len(season.get('episodes', {})) for season in episode_data.get('seasons', {}).values())
                    print(f"   ✅ Successfully cached ({episodes} episodes across {seasons} seasons)")
                    logger.info(f"Show '{show_title}' successfully cached: {episodes} episodes, {seasons} seasons")
                    successful += 1
                else:
                    print(f"   ❌ Validation failed: {validation['reason']}")
                    logger.error(f"Show '{show_title}' validation failed: {validation['reason']}")
                    failed += 1
            else:
                print(f"   ❌ No episode data found")
                logger.error(f"No episode data found for '{show_title}'")
                failed += 1

        except Exception as e:
            print(f"   ❌ Error caching '{show_title}': {e}")
            import traceback
            print(f"   📋 Full traceback:")
            traceback.print_exc()
            logger.error(f"Exception while caching '{show_title}': {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            failed += 1

    # Summary
    print(f"\n🎯 Pre-caching Complete!")
    print(f"   Shows processed: {len(show_titles)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Success rate: {(successful / len(show_titles) * 100):.1f}%")

    logger.info(f"Pre-caching complete: {successful} successful, {failed} failed, {(successful / len(show_titles) * 100):.1f}% success rate")

    if successful == len(show_titles):
        print("   ✅ All shows ready for organization!")
        logger.success("All shows successfully cached and ready for organization")
    else:
        print("   ⚠️  Some shows failed to cache - check logs for details")
        logger.warning(f"Some shows failed: {failed} failures detected")

if __name__ == '__main__':
    main()