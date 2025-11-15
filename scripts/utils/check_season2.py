#!/usr/bin/env python3
import json
from pathlib import Path

cache_file = Path('._state/tv_episode_cache/doc_martin_2004.json')
data = json.load(open(cache_file))

# Check S02E01 specifically
print('Season 2 structure:')
season2 = data['seasons']['2']
episodes = season2.get('episodes', {})
print(f'  Episode keys: {list(episodes.keys())}')

for ep_key in sorted(episodes.keys())[:3]:
    ep = episodes[ep_key]
    title = ep.get('canonical_title')
    print(f'  Episode {ep_key}: {title}')
