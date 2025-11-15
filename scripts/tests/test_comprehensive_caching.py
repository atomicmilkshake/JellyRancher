#!/usr/bin/env python3
"""
Comprehensive TV show parsing test with caching enabled.
"""

from _common.tv_episode_cache import TVEpisodeCache
import time

# Test shows from the comprehensive test
test_shows = [
    'Breaking Bad', 'The Sopranos', 'The Wire', 'Mad Men', 'The Office (US)',
    'Parks and Recreation', 'Arrested Development', 'Curb Your Enthusiasm',
    'Seinfeld', 'Friends', 'Frasier', 'Cheers', 'The Big Bang Theory',
    'How I Met Your Mother', 'Modern Family', 'The Simpsons', 'Family Guy',
    'South Park', 'American Dad', 'King of the Hill', 'Rick and Morty',
    'BoJack Horseman', 'Archer', 'Futurama', 'Aqua Teen Hunger Force'
]

def main():
    cache = TVEpisodeCache()
    results = {}

    print(f'Testing {len(test_shows)} shows with caching enabled...')
    start_time = time.time()

    for i, show in enumerate(test_shows, 1):
        print(f'\n{i}/{len(test_shows)}: Testing {show}')
        try:
            result = cache.fetch_wikipedia_episodes(show)
            if result:
                season_count = len(result.get('seasons', {}))
                episode_count = sum(len(season.get('episodes', {})) for season in result.get('seasons', {}).values())
                results[show] = {'success': True, 'seasons': season_count, 'episodes': episode_count}
                print(f'  ✅ Success: {episode_count} episodes in {season_count} seasons')
            else:
                results[show] = {'success': False, 'error': 'No data returned'}
                print(f'  ❌ Failed: No data returned')
        except Exception as e:
            results[show] = {'success': False, 'error': str(e)}
            print(f'  ❌ Error: {e}')

    end_time = time.time()
    total_time = end_time - start_time

    # Calculate success rate
    successful = sum(1 for r in results.values() if r['success'])
    success_rate = successful / len(test_shows) * 100

    print(f'\n🎯 Test Results:')
    print(f'   Shows tested: {len(test_shows)}')
    print(f'   Successful: {successful}')
    print(f'   Success rate: {success_rate:.1f}%')
    print(f'   Total time: {total_time:.1f} seconds')
    print(f'   Average time per show: {total_time/len(test_shows):.1f} seconds')

    # Show failures
    failures = [(show, result) for show, result in results.items() if not result['success']]
    if failures:
        print(f'\n❌ Failed shows:')
        for show, result in failures:
            error_msg = result.get('error', 'Unknown error')
            print(f'   {show}: {error_msg}')

if __name__ == '__main__':
    main()