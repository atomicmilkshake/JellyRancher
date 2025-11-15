#!/usr/bin/env python3
"""Test episode title lookup"""

import sys
import json
from pathlib import Path

STATE_DIR = Path('._state/tv_episode_cache')

def find_cache_file(show_name: str):
    show_normalized = show_name.lower().replace(' ', '_').replace(':', '').replace('&', 'and').replace('(', '').replace(')', '')
    
    variations = [
        show_normalized + '.json',
        show_normalized + '_2004.json',
        show_normalized + '_2008.json',
    ]
    
    for variation in variations:
        cache_file = STATE_DIR / variation
        if cache_file.exists():
            return cache_file
    return None

def load_episode_cache(show_name: str):
    cache_file = find_cache_file(show_name)
    if cache_file:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def get_episode_title(show_name: str, season: int, episode: int, cache):
    if not cache:
        return None
    
    try:
        seasons = cache.get('seasons', {})
        season_data = seasons.get(str(season), {})
        episodes = season_data.get('episodes', {})
        episode_data = episodes.get(str(episode), {})
        title = episode_data.get('canonical_title')
        return title if title else None
    except (KeyError, TypeError):
        return None

# Test with Doc Martin
print("Testing Doc Martin...")
cache = load_episode_cache("Doc Martin")
print(f"Cache loaded: {cache is not None}")

if cache:
    # Try S02E01
    title = get_episode_title("Doc Martin", 2, 1, cache)
    print(f"S02E01: {title}")
    
    # Try S01E01
    title = get_episode_title("Doc Martin", 1, 1, cache)
    print(f"S01E01: {title}")
    
    # Try S10E01 (maybe doesn't exist)
    title = get_episode_title("Doc Martin", 10, 1, cache)
    print(f"S10E01: {title}")
