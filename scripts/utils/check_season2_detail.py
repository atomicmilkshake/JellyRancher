#!/usr/bin/env python3
import json
from pathlib import Path

cache_file = Path('._state/tv_episode_cache/doc_martin_2004.json')
data = json.load(open(cache_file))

# Check all keys and fields for Season 2
print('Season 2 detailed structure:')
season2 = data['seasons']['2']
episodes = season2.get('episodes', {})

print(f'Episode keys: {list(episodes.keys())}')
print('\nFirst 3 episodes in detail:')
for i, key in enumerate(sorted(episodes.keys())[:3]):
    ep = episodes[key]
    print(f'\n  Cache key: {key}')
    print(f'    episode_number: {ep.get("episode_number")}')
    print(f'    canonical_title: {ep.get("canonical_title")}')
    print(f'    Fields: {list(ep.keys())}')
