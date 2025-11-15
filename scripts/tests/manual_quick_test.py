#!/usr/bin/env python3
"""
Quick test for a few shows
"""

import sys
import os
from pathlib import Path

# Add the _common directory to the path
script_dir = Path(__file__).parent
common_dir = script_dir / "_common"
sys.path.insert(0, str(common_dir))

from tv_episode_cache import TVEpisodeCache

def test_show(show_name: str):
    """Test parsing for a single show."""
    print(f"\n🎬 Testing: {show_name}")

    cache = TVEpisodeCache()

    try:
        # Fetch episode data
        episode_data = cache.fetch_wikipedia_episodes(show_name)

        if episode_data:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            print(f"✅ SUCCESS: {total_episodes} episodes")
        else:
            print("❌ FAILED: No episode data found")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    # Test a few key shows
    test_show("Stranger Things")
    test_show("The Mandalorian")
    test_show("Severance")