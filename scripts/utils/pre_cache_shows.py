#!/usr/bin/env python3
"""
Pre-cache Wikipedia episode data for all TV shows in M:\#MEDIA

This script scans the target directory, identifies all TV shows,
and pre-caches their Wikipedia episode data before running the organizer.
This ensures all episode information is available locally for fast access
during the organization process.
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

def get_show_titles_from_directory(media_root: str) -> list[str]:
    """Extract show titles from directory structure."""
    media_path = Path(media_root)
    show_titles = []

    # Check root level shows
    for item in media_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Skip common non-show directories
            if item.name.lower() not in ['movies', 'tv shows', 'backups', '.venv']:
                # Clean the show title from folder name
                clean_title = clean_show_title_from_folder(item.name)
                if clean_title and clean_title not in show_titles:
                    show_titles.append(clean_title)

    # Check TV Shows subdirectory
    tv_shows_path = media_path / "TV Shows"
    if tv_shows_path.exists():
        for item in tv_shows_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                show_titles.append(item.name)

    return show_titles

def clean_show_title_from_folder(folder_name: str) -> str:
    """Extract clean show title from season folder name."""
    import re
    
    # Patterns for season folders
    # Examples: "Lost (2004) Season 1 S01 + Extras..."
    #           "That.70s.Show.S01-S08.COMPLETE.SERIES..."
    #           "The Mandalorian (2019) Season 3 S03 + Extras..."
    
    # Try to match "Show Name (Year)" pattern
    year_match = re.search(r'^(.+?)\s*\((\d{4})\)', folder_name)
    if year_match:
        title = year_match.group(1).strip()
        year = year_match.group(2)
        # Clean title: replace dots/underscores with spaces
        title = re.sub(r'[._]', ' ', title)
        return f"{title} ({year})"
    
    # Fallback: extract before "Season" or "S01"
    season_match = re.search(r'^(.+?)\s*(?:Season|S\d+)', folder_name, re.IGNORECASE)
    if season_match:
        title = season_match.group(1).strip()
        # Clean title
        title = re.sub(r'[._]', ' ', title)
        return title
    
    # Last resort: use whole name cleaned
    title = re.sub(r'[._]', ' ', folder_name)
    return title

def main():
    print("🔍 Pre-caching Wikipedia episode data for M:\\#MEDIA")
    print("=" * 60)

    # Initialize logger
    logger = ProjectLogger("pre_cache_shows")
    logger.info("Starting pre-cache operation for M:\\#MEDIA")

    # Target directory
    media_root = r"W:\#MEDIA"

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
    print(f"📺 Found {len(show_titles)} TV shows to cache:")
    for title in show_titles:
        print(f"   • {title}")

    # For debugging, only process first few shows
    debug_mode = False  # Set to False to process all shows
    if debug_mode:
        show_titles = show_titles[:3]  # Only first 3 shows
        print(f"🐛 DEBUG MODE: Only processing first {len(show_titles)} shows")

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

            # Fetch and cache with detailed logging and validation
            print(f"   🔍 Starting Wikipedia fetch for '{show_title}'...")
            logger.info(f"Fetching Wikipedia data for '{show_title}'")
            episode_data = cache.get_episode_data(show_title, force_refresh=True)  # Force refresh to use enhanced parsing
            
            if episode_data:
                # Validate the episode data
                validation_result = validate_episode_data(episode_data, show_title)
                if not validation_result['is_valid']:
                    print(f"   ⚠️  Episode data validation failed: {validation_result['reason']}")
                    print(f"   📋 Validation details: {validation_result['details']}")
                    logger.error(f"Validation failed for '{show_title}': {validation_result['reason']} - {validation_result['details']}")
                    failed += 1
                    # Stop on first failure for debugging
                    print(f"❌ STOPPED: Validation failed for '{show_title}'. Check logs and debug parsing algorithm.")
                    logger.error(f"STOPPED processing due to validation failure for '{show_title}'")
                    break
                
                seasons = len(episode_data.get('seasons', {}))
                episodes = sum(len(season.get('episodes', {})) for season in episode_data.get('seasons', {}).values())
                print(f"   ✅ Successfully cached and validated {episodes} episodes across {seasons} seasons")
                logger.success(f"Cached '{show_title}': {episodes} episodes, {seasons} seasons")
                successful += 1
            else:
                print(f"   ❌ Failed to fetch episode data from Wikipedia")
                logger.error(f"Failed to fetch Wikipedia data for '{show_title}'")
                failed += 1
                # Stop on first failure for debugging
                print(f"❌ STOPPED: Fetch failed for '{show_title}'. Check logs and debug parsing algorithm.")
                logger.error(f"STOPPED processing due to fetch failure for '{show_title}'")
                break

        except Exception as e:
            print(f"   ❌ Error caching '{show_title}': {e}")
            import traceback
            print(f"   📋 Full traceback:")
            traceback.print_exc()
            logger.error(f"Exception while caching '{show_title}': {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            failed += 1
            # Stop on first failure for debugging
            print(f"❌ STOPPED: Exception for '{show_title}'. Check logs and debug parsing algorithm.")
            logger.error(f"STOPPED processing due to exception for '{show_title}'")
            break

        # Pause between shows for debugging
        if i < len(show_titles):
            input(f"   ⏸️  Press Enter to continue to next show ({i+1}/{len(show_titles)})...")

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