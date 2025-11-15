#!/usr/bin/env python3
"""
Quick test for The Simpsons parsing
"""

import sys
import os
from pathlib import Path

# Add the _common directory to the path
script_dir = Path(__file__).parent
common_dir = script_dir / "_common"
sys.path.insert(0, str(common_dir))

from tv_episode_cache import TVEpisodeCache

def test_simpsons():
    """Test parsing for The Simpsons."""
    print("Testing The Simpsons parsing...")

    cache = TVEpisodeCache()

    try:
        # Fetch episode data
        episode_data = cache.fetch_wikipedia_episodes("The Simpsons")

        if episode_data:
            total_episodes = sum(len(season['episodes']) for season in episode_data['seasons'].values())
            total_seasons = len(episode_data['seasons'])

            print(f"✅ SUCCESS: {total_episodes} episodes across {total_seasons} seasons")
        else:
            print("❌ FAILED: No episode data found")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_simpsons()