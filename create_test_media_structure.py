#!/usr/bin/env python3
"""
Create Test Media Folder Structure

Generates a realistic test media folder structure for testing JellyRancher's
metadata lookup and reorganization capabilities.

Creates:
- Movies in various naming formats
- TV shows with seasons and episodes
- Multi-part episodes
- Mixed/messy folder structures
"""

from pathlib import Path
import os

def create_test_structure():
    """Create test media folder structure."""
    
    print("="*60)
    print("Creating Test Media Folder Structure")
    print("="*60)
    
    base_path = Path("test_media")
    
    # Remove existing test folder if it exists
    if base_path.exists():
        print(f"\nRemoving existing test folder: {base_path}")
        import shutil
        shutil.rmtree(base_path)
    
    # Create base directory
    base_path.mkdir(exist_ok=True)
    print(f"\n[OK] Created base directory: {base_path}")
    
    # =========================================================================
    # MOVIES - Various naming formats
    # =========================================================================
    
    movies = [
        # Standard formats
        "The Matrix (1999)/The Matrix (1999).mkv",
        "Inception (2010)/Inception (2010).mkv",
        "Interstellar (2014)/Interstellar (2014).mkv",
        
        # Messy formats that need reorganization
        "The.Shawshank.Redemption.1994.1080p.BluRay.x264.mkv",
        "Pulp Fiction [1994] (1080p).mp4",
        "the_dark_knight_2008.avi",
        "Fight Club (1999) - HD.mkv",
        
        # Movies with subtitles
        "The Godfather (1972)/The Godfather (1972).mkv",
        "The Godfather (1972)/The Godfather (1972).en.srt",
        "The Godfather (1972)/The Godfather (1972).en.forced.srt",
    ]
    
    print("\n[Creating Movies]")
    for movie_path in movies:
        full_path = base_path / "Movies" / movie_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch()
        print(f"  + {movie_path}")
    
    # =========================================================================
    # TV SHOWS - Well-organized
    # =========================================================================
    
    print("\n[Creating TV Shows - Well Organized]")
    
    # Breaking Bad - Complete structure
    print("  Breaking Bad (2008-2013):")
    for season in range(1, 6):  # 5 seasons
        season_path = base_path / "TV Shows" / "Breaking Bad (2008)" / f"Season {season:02d}"
        season_path.mkdir(parents=True, exist_ok=True)
        
        # Create a few episodes per season
        for ep in range(1, 4):  # 3 episodes per season for demo
            ep_file = season_path / f"Breaking Bad - S{season:02d}E{ep:02d} - Episode {ep}.mkv"
            ep_file.touch()
            print(f"    + S{season:02d}E{ep:02d}")
    
    # The Office - With subtitles
    print("  The Office (2005-2013):")
    for season in [1, 2]:  # Just 2 seasons for demo
        season_path = base_path / "TV Shows" / "The Office (US) (2005)" / f"Season {season:02d}"
        season_path.mkdir(parents=True, exist_ok=True)
        
        for ep in range(1, 3):  # 2 episodes per season
            ep_file = season_path / f"The Office - S{season:02d}E{ep:02d}.mkv"
            ep_file.touch()
            # Add subtitle
            sub_file = season_path / f"The Office - S{season:02d}E{ep:02d}.en.srt"
            sub_file.touch()
            print(f"    + S{season:02d}E{ep:02d} (with subs)")
    
    # =========================================================================
    # TV SHOWS - Messy/Needs Organization
    # =========================================================================
    
    print("\n[Creating TV Shows - Messy Format]")
    
    messy_tv = [
        # Flat structure (no seasons folder)
        "Stranger Things/stranger.things.s01e01.1080p.mkv",
        "Stranger Things/stranger.things.s01e02.1080p.mkv",
        "Stranger Things/stranger.things.s02e01.1080p.mkv",
        
        # Wrong naming format
        "Game.of.Thrones.S01E01.Winter.Is.Coming.mkv",
        "Game.of.Thrones.S01E02.The.Kingsroad.mkv",
        
        # Missing year
        "The Mandalorian/Season 1/Chapter 1 - The Mandalorian.mkv",
        "The Mandalorian/Season 1/Chapter 2 - The Child.mkv",
        
        # Multi-part episode (should trigger NFO generation)
        "Star Trek TNG/Season 01/Star Trek TNG - S01E01-E02 - Encounter at Farpoint Parts 1-2.mkv",
        "Star Trek TNG/Season 03/Star Trek TNG - S03E26-S04E01 - Best of Both Worlds Parts 1-2.mkv",
    ]
    
    for tv_path in messy_tv:
        full_path = base_path / "Unsorted TV" / tv_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch()
        print(f"  + {tv_path}")
    
    # =========================================================================
    # MIXED/UNSORTED - Challenging cases
    # =========================================================================
    
    print("\n[Creating Mixed/Unsorted Content]")
    
    mixed = [
        "random_video_1.mkv",
        "random_video_2.avi",
        "home_movie.mp4",
        "Documentary.About.Something.2020.mkv",
        "Some Folder/unknown_file.mkv",
    ]
    
    for mixed_path in mixed:
        full_path = base_path / "Unsorted" / mixed_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch()
        print(f"  + {mixed_path}")
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    print("\n" + "="*60)
    print("Test Media Structure Created Successfully!")
    print("="*60)
    
    # Count files
    total_video = len(list(base_path.rglob("*.mkv"))) + \
                  len(list(base_path.rglob("*.mp4"))) + \
                  len(list(base_path.rglob("*.avi")))
    total_subs = len(list(base_path.rglob("*.srt")))
    
    print(f"\nLocation: {base_path.absolute()}")
    print(f"Total video files: {total_video}")
    print(f"Total subtitle files: {total_subs}")
    print(f"\nFolder structure:")
    print(f"  - Movies/         : Well-organized and messy movies")
    print(f"  - TV Shows/       : Well-organized TV shows")
    print(f"  - Unsorted TV/    : TV shows needing reorganization")
    print(f"  - Unsorted/       : Mixed/unknown content")
    
    print(f"\nExpected Detections:")
    print(f"  Movies: ~7 (The Matrix, Inception, Interstellar, Shawshank, Pulp Fiction, Dark Knight, Fight Club, Godfather)")
    print(f"  TV Shows: ~5 (Breaking Bad, The Office, Stranger Things, Game of Thrones, The Mandalorian, Star Trek TNG)")
    print(f"  Multi-part episodes: ~2 (Star Trek TNG episodes)")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Run: python jelly_rancher_clean.py")
    print(f"2. Add folder: {base_path.absolute()}")
    print("3. Click 'Scan Selected Folders'")
    print("4. View hierarchical overview")
    print("5. Get LLM proposal")
    print("6. Build metadata database (Point 4)")
    print("="*60)


if __name__ == "__main__":
    try:
        create_test_structure()
    except Exception as e:
        print(f"\n[ERROR] Failed to create test structure: {e}")
        import traceback
        traceback.print_exc()



