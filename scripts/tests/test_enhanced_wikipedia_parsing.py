#!/usr/bin/env python3
"""
Enhanced Wikipedia TV Show Parsing Test
Tests the improved parsing logic on 10 diverse TV shows to validate robustness.
"""

import sys
import os
from pathlib import Path

# Add the _common directory to the path
script_dir = Path(__file__).parent
common_dir = script_dir / "_common"
sys.path.insert(0, str(common_dir))

from tv_episode_cache import TVEpisodeCache

def test_show_parsing(show_name: str, expected_min_episodes: int = 1) -> bool:
    """Test parsing for a single show."""
    print(f"\n🎬 Testing: {show_name}")
    print("=" * (12 + len(show_name)))

    cache = TVEpisodeCache()

    try:
        # Fetch episode data
        episode_data = cache.fetch_wikipedia_episodes(show_name)

        if episode_data:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            total_seasons = len(episode_data['seasons'])

            print(f"✅ SUCCESS: {total_episodes} episodes across {total_seasons} seasons")

            # Show season breakdown
            for season_num in sorted(episode_data['seasons'].keys(), key=int):
                season = episode_data['seasons'][season_num]
                episode_count = len(season['episodes'])
                print(f"   Season {season_num}: {episode_count} episodes")

            # Check if we meet minimum expectations
            if total_episodes >= expected_min_episodes:
                print(f"✅ PASSED: Met minimum episode requirement ({expected_min_episodes})")
                return True
            else:
                print(f"❌ FAILED: Only {total_episodes} episodes, expected at least {expected_min_episodes}")
                return False
        else:
            print("❌ FAILED: No episode data found")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Test enhanced parsing on diverse TV shows."""
    print("🧪 Enhanced Wikipedia TV Show Parsing Test")
    print("Testing improved parsing logic on 10 real TV shows")
    print("=" * 70)

    # Test shows - use only real shows from the actual media library
    test_shows = [
        ("The Middle", 215),  # 9 seasons, 215 episodes
        ("Monk", 125),  # 8 seasons, 125 episodes
        ("Star Trek: Deep Space Nine", 176),  # 7 seasons, 176 episodes
        ("Better Call Saul", 63),  # 6 seasons, 63 episodes
        ("Columbo", 69),  # 10 seasons, 69 episodes
        ("Breaking Bad", 62),  # 5 seasons, 62 episodes (related to Better Call Saul)
        ("Ted Lasso", 34),  # 3 seasons, 34 episodes
        ("Succession", 39),  # 4 seasons, 39 episodes
        ("The Crown", 60),  # 6 seasons, 60 episodes
        ("The Mandalorian", 24),  # 3 seasons, 24 episodes
    ]

    results = []

    for show_name, min_episodes in test_shows:
        success = test_show_parsing(show_name, min_episodes)
        results.append((show_name, success))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    successful = sum(1 for _, success in results if success)
    total = len(results)

    print(f"Total Shows Tested: {total}")
    print(f"Successful Parsing: {successful}")
    print(".1f")

    if successful >= 8:  # 80% success rate on 10 shows
        print("🎉 OVERALL: PASSED - Enhanced parsing is robust!")
    else:
        print("⚠️  OVERALL: NEEDS IMPROVEMENT - Parsing success rate too low")

    # Show detailed results
    print("\n📋 Detailed Results:")
    for show_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {show_name}")

if __name__ == "__main__":
    main()