#!/usr/bin/env python3
"""Build Doc Martin episode mapping from cache"""

import json
from pathlib import Path
from collections import defaultdict

cache_file = Path('._state/tv_episode_cache/doc_martin_2004.json')
data = json.load(open(cache_file))

# Build a season->episode->title mapping
mapping = {}
global_counter = 0

for season_key in sorted(data['seasons'].keys()):
    season_data = data['seasons'][season_key]
    episodes = season_data.get('episodes', {})
    
    season_num = int(season_key)
    mapping[season_num] = {}
    
    for global_ep_key in sorted(episodes.keys()):
        episode_data = episodes[global_ep_key]
        title = episode_data.get('canonical_title', 'Unknown')
        
        # Figure out per-season episode number
        # by tracking what episode number this episode thinks it is
        ep_num = episode_data.get('episode_number')
        
        if ep_num:
            # Store by the actual episode number within season
            mapping[season_num][ep_num] = title

# Print the mapping
for season in sorted(mapping.keys()):
    print(f'Season {season}:')
    for ep_num in sorted(mapping[season].keys())[:5]:
        title = mapping[season][ep_num]
        print(f'  S{season:02d}E{ep_num:02d}: {title}')
    if len(mapping[season]) > 5:
        print(f'  ... and {len(mapping[season]) - 5} more')

# Save the mapping
with open('doc_martin_mapping.json', 'w') as f:
    # Convert keys to strings for JSON
    json_mapping = {}
    for season, episodes in mapping.items():
        json_mapping[str(season)] = {str(k): v for k, v in episodes.items()}
    json.dump(json_mapping, f, indent=2)

print(f'\nMapping saved to doc_martin_mapping.json')
