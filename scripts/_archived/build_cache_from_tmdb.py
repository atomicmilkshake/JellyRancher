#!/usr/bin/env python3
"""
TMDB Episode Cache Builder
Dynamically creates episode cache files from The Movie Database (TMDB) API.

This script fetches TV show data from TMDB and generates cache files compatible
with the batch_rename_episode_titles.py script.

Usage:
    python build_cache_from_tmdb.py --show "Planet Earth" --year 2006
    python build_cache_from_tmdb.py --show "Breaking Bad" --year 2008 --tmdb-id 1396

Requirements:
    pip install tmdbv3api

Setup:
    1. Get a free API key from https://www.themoviedb.org/settings/api
    2. Set the TMDB_API_KEY environment variable or pass it via --api-key
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Optional

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / '_common'))
from config_loader import get_tv_cache_dir

try:
    from tmdbv3api import TMDb, TV
except ImportError:
    print("[ERROR] tmdbv3api library not found")
    print("Install it with: pip install tmdbv3api")
    sys.exit(1)


def sanitize_title(title: str) -> str:
    """
    Sanitize episode title to remove illegal characters.
    Matches the sanitization in batch_rename_episode_titles.py
    """
    illegal_chars = {
        '<': '(less than)',
        '>': '(greater than)',
        ':': ' -',
        '"': "'",
        '/': ' or ',
        '\\': ' or ',
        '|': '-',
        '?': '',
        '*': 'x',
    }

    sanitized = title
    for illegal, replacement in illegal_chars.items():
        sanitized = sanitized.replace(illegal, replacement)

    # Clean up multiple spaces
    while '  ' in sanitized:
        sanitized = sanitized.replace('  ', ' ')

    return sanitized.strip()


def search_show(tmdb: TMDb, tv: TV, show_name: str, year: Optional[int] = None) -> Optional[Dict]:
    """
    Search for a TV show on TMDB.

    Args:
        tmdb: TMDB API instance
        tv: TV API instance
        show_name: Name of the show to search for
        year: Optional year to filter results

    Returns:
        Show data dictionary, or None if not found
    """
    print(f"[INFO] Searching TMDB for '{show_name}' (year: {year or 'any'})...")

    search_results = tv.search(show_name)

    if not search_results:
        print(f"[ERROR] No results found for '{show_name}'")
        return None

    # Filter by year if provided
    if year:
        filtered = [s for s in search_results if s.first_air_date and str(year) in s.first_air_date]
        if filtered:
            search_results = filtered

    # Show top results
    print(f"\n[INFO] Found {len(search_results)} results:")
    for i, show in enumerate(search_results[:5], 1):
        air_date = show.first_air_date if hasattr(show, 'first_air_date') else 'Unknown'
        print(f"  {i}. {show.name} ({air_date}) [ID: {show.id}]")

    if len(search_results) > 5:
        print(f"  ... and {len(search_results) - 5} more")

    # Return the first result (best match)
    return search_results[0]


def build_cache_from_tmdb(
    api_key: str,
    show_name: str,
    year: Optional[int] = None,
    tmdb_id: Optional[int] = None,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Build episode cache from TMDB data.

    Args:
        api_key: TMDB API key
        show_name: Name of the TV show
        year: Optional year to help identify the show
        tmdb_id: Optional TMDB ID if known
        output_path: Optional custom output path

    Returns:
        Cache data dictionary
    """
    # Initialize TMDB API
    tmdb = TMDb()
    tmdb.api_key = api_key
    tv = TV()

    # Search for show or get by ID
    if tmdb_id:
        print(f"[INFO] Fetching show with TMDB ID: {tmdb_id}...")
        show = tv.details(tmdb_id)
    else:
        show = search_show(tmdb, tv, show_name, year)
        if not show:
            raise ValueError(f"Could not find show: {show_name}")

    print(f"\n[OK] Found: {show.name} ({show.first_air_date})")
    print(f"    TMDB ID: {show.id}")
    print(f"    Seasons: {show.number_of_seasons}")
    print(f"    Episodes: {show.number_of_episodes}")

    # Build cache structure
    cache = {
        'show_name': show.name,
        'tmdb_id': show.id,
        'first_air_date': show.first_air_date,
        'overview': show.overview if hasattr(show, 'overview') else '',
        'seasons': {}
    }

    # Fetch all seasons and episodes
    print(f"\n[INFO] Fetching episode data...")

    for season_num in range(1, show.number_of_seasons + 1):
        try:
            season = tv.season(show.id, season_num)

            if not hasattr(season, 'episodes') or not season.episodes:
                print(f"  [SKIP] Season {season_num}: No episodes found")
                continue

            cache['seasons'][str(season_num)] = {
                'season_number': season_num,
                'name': season.name if hasattr(season, 'name') else f"Season {season_num}",
                'air_date': season.air_date if hasattr(season, 'air_date') else None,
                'episodes': {}
            }

            for episode in season.episodes:
                episode_num = episode.episode_number
                title = episode.name if hasattr(episode, 'name') else f"Episode {episode_num}"

                # Sanitize title for filesystem compatibility
                canonical_title = sanitize_title(title)

                cache['seasons'][str(season_num)]['episodes'][str(episode_num)] = {
                    'episode_number': episode_num,
                    'canonical_title': canonical_title,
                    'original_title': title,
                    'air_date': episode.air_date if hasattr(episode, 'air_date') else None,
                    'overview': episode.overview if hasattr(episode, 'overview') else ''
                }

            print(f"  [OK] Season {season_num}: {len(season.episodes)} episodes")

        except Exception as e:
            print(f"  [ERROR] Season {season_num}: {e}")
            continue

    # Save cache to file
    if output_path is None:
        cache_dir = get_tv_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        show_name_normalized = show.name.lower()
        show_name_normalized = show_name_normalized.replace(' ', '_').replace(':', '').replace('&', 'and')
        show_name_normalized = show_name_normalized.replace('(', '').replace(')', '')

        if year:
            filename = f"{show_name_normalized}_{year}.json"
        else:
            filename = f"{show_name_normalized}.json"

        output_path = cache_dir / filename

    # Write cache file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Cache saved to: {output_path}")
    print(f"[INFO] Total seasons: {len(cache['seasons'])}")

    total_episodes = sum(len(s['episodes']) for s in cache['seasons'].values())
    print(f"[INFO] Total episodes: {total_episodes}")

    return cache


def main():
    parser = argparse.ArgumentParser(
        description="Build episode cache from TMDB API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_cache_from_tmdb.py --show "Planet Earth" --year 2006
  python build_cache_from_tmdb.py --show "Breaking Bad" --year 2008
  python build_cache_from_tmdb.py --tmdb-id 1396 --show "Breaking Bad"

Environment Variables:
  TMDB_API_KEY    Your TMDB API key (get one from https://www.themoviedb.org/settings/api)
        """
    )

    parser.add_argument('--show', required=True, help='TV show name')
    parser.add_argument('--year', type=int, help='Year the show first aired')
    parser.add_argument('--tmdb-id', type=int, help='TMDB ID if known')
    parser.add_argument('--api-key', help='TMDB API key (or set TMDB_API_KEY env var)')
    parser.add_argument('--output', help='Custom output path for cache file')

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key
    if not api_key:
        import os
        api_key = os.environ.get('TMDB_API_KEY')

    if not api_key:
        print("[ERROR] TMDB API key not provided")
        print("Either pass --api-key or set the TMDB_API_KEY environment variable")
        print("Get a free API key from: https://www.themoviedb.org/settings/api")
        sys.exit(1)

    output_path = Path(args.output) if args.output else None

    try:
        build_cache_from_tmdb(
            api_key=api_key,
            show_name=args.show,
            year=args.year,
            tmdb_id=args.tmdb_id,
            output_path=output_path
        )
    except KeyboardInterrupt:
        print("\n[INFO] Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
