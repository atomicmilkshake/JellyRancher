#!/usr/bin/env python3
"""Build correct Doc Martin mapping: season/episode -> title"""

import json
from pathlib import Path

cache_file = Path('._state/tv_episode_cache/doc_martin_2004.json')
data = json.load(open(cache_file))

# Build mapping: {season: {episode_per_season: title}}
mapping = {}

for season_key in sorted(data['seasons'].keys()):
    season_data = data['seasons'][season_key]
    episodes_in_season = season_data.get('episodes', {})
    
    season_num = int(season_key)
    mapping[season_num] = {}
    
    # For each episode in this season
    per_season_ep_num = 1
    for global_ep_key in sorted(episodes_in_season.keys(), key=lambda x: int(x)):
        episode_data = episodes_in_season[global_ep_key]
        title = episode_data.get('canonical_title', 'Unknown')
        
        # Store using per-season numbering
        mapping[season_num][per_season_ep_num] = title
        per_season_ep_num += 1

# Print to verify
for season in sorted(mapping.keys()):
    print(f'Season {season}:')
    for ep_num in sorted(mapping[season].keys())[:3]:
        title = mapping[season][ep_num]
        print(f'  S{season:02d}E{ep_num:02d}: {title}')
    if len(mapping[season]) > 3:
        print(f'  ... and {len(mapping[season]) - 3} more')

# Save with string keys for JSON
with open('doc_martin_correct_mapping.json', 'w') as f:
    json_mapping = {}
    for season, episodes in mapping.items():
        json_mapping[str(season)] = {str(k): v for k, v in episodes.items()}
    json.dump(json_mapping, f, indent=2)

print(f'\nCorrect mapping saved to doc_martin_correct_mapping.json')
