#!/usr/bin/env python3
import json

for fname in ['batman_the_animated_series.json', 'batman_the_animated_series_1992.json']:
    print(f'\nChecking {fname}:')
    data = json.load(open(f'._state/tv_episode_cache/{fname}'))
    title = data.get('show_title')
    seasons = data.get('seasons',{})
    eps = sum(len(s.get('episodes',{})) for s in seasons.values())
    print(f'  Show: {title}')
    print(f'  Episodes: {eps}')
