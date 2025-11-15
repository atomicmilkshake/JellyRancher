#!/usr/bin/env python3
import json
from pathlib import Path

cache_file = Path('._state/tv_episode_cache/doc_martin_2004.json')
data = json.load(open(cache_file))

# Season 2, Episode 1-6 should be episodes 7-12 globally
print('Season 2 mapping (global episode numbering):')
season2 = data['seasons']['2']
episodes = season2.get('episodes', {})

for ep_num in ['7', '8', '9', '10', '11', '12']:
    if ep_num in episodes:
        title = episodes[ep_num].get('canonical_title', 'N/A')
        print(f'  Global Ep {ep_num}: {title}')

print('\nSeason 2 episode numbering:')
# Try to find the per-season numbering
for ep_key in sorted(episodes.keys()):
    ep = episodes[ep_key]
    print(f'  Key: {ep_key}')
    print(f'    episode_number: {ep.get("episode_number")}')
    print(f'    canonical_title: {ep.get("canonical_title")}')
    break
