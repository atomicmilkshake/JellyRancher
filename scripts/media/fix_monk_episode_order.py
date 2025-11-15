#!/usr/bin/env python3
"""
Fix Monk Episode Order
Compares current filenames with original torrent structure to identify mismatches
"""

import os
from pathlib import Path
import json

# Original torrent structure for Season 1
TORRENT_EPISODES = {
    1: "Mr. Monk Meets the Candidate",  # S01E01-E02 (combined)
    3: "Mr. Monk and the Psychic",
    4: "Mr. Monk Meets Dale the Whale",
    5: "Mr. Monk Goes to the Carnival",
    6: "Mr. Monk Goes to the Asylum",
    7: "Mr. Monk and the Billionaire Mugger",
    8: "Mr. Monk and the Other Woman",
    9: "Mr. Monk and the Marathon Man",
    10: "Mr. Monk Takes a Vacation",
    11: "Mr. Monk and the Earthquake",
    12: "Mr. Monk and the Red-Headed Stranger",
    13: "Mr. Monk and the Airplane"
}

# Current filenames on Q: drive
CURRENT_FILES = {
    1: "Mr Monk Meets the Candidate",  # S01E01-E02
    3: "Mr Monk and the Psychic",
    4: "Mr Monk Meets Dale the Whale",
    5: "Mr Monk Goes to the Carnival",
    6: "Mr Monk Goes to the Asylum",
    7: "Mr Monk and the Billionaire Mugger",
    8: "Mr Monk and the Other Woman",
    9: "Mr Monk and the Marathon Man",
    10: "Mr Monk Takes a Vacation",
    11: "Mr Monk and the Earthquake",
    12: "Mr Monk and the Red-Headed Stranger",
    13: "Mr Monk and the Airplane"
}

# User observations:
# - To watch "Mr Monk Goes to the Carnival" (should be E05), you select E06
# - To watch "Mr Monk Meets Dale the Whale" (should be E04), you select E05
# This suggests files are shifted forward by 1 starting at E04

def analyze_episode_order():
    """Analyze the episode order issue"""
    
    print("=" * 80)
    print("MONK SEASON 1 EPISODE ORDER ANALYSIS")
    print("=" * 80)
    
    print("\n📊 TORRENT STRUCTURE (Original):")
    print("-" * 80)
    for ep_num, title in TORRENT_EPISODES.items():
        if ep_num == 1:
            print(f"  S01E01-E02: {title}")
        else:
            print(f"  S01E{ep_num:02d}: {title}")
    
    print("\n📁 CURRENT FILES (Q: Drive):")
    print("-" * 80)
    for ep_num, title in CURRENT_FILES.items():
        if ep_num == 1:
            print(f"  S01E01-E02: {title}")
        else:
            print(f"  S01E{ep_num:02d}: {title}")
    
    print("\n🔍 USER OBSERVATIONS:")
    print("-" * 80)
    print("  • To watch 'Carnival' (E05), must select E06")
    print("  • To watch 'Dale the Whale' (E04), must select E05")
    print("  • This suggests files shifted forward by 1 starting at E04")
    
    print("\n💡 HYPOTHESIS:")
    print("-" * 80)
    print("  The FILENAMES are correct, but the VIDEO CONTENT is wrong.")
    print("  Each file from E04 onward contains the PREVIOUS episode's content.")
    
    print("\n🎯 PROPOSED FIX:")
    print("-" * 80)
    print("  We need to RENAME files to match their actual content:")
    print()
    
    # Generate rename mapping
    rename_map = []
    
    # E01-E02 is correct (combined episode)
    print("  ✓ S01E01-E02 - Mr Monk Meets the Candidate (CORRECT)")
    
    # E03 is correct
    print("  ✓ S01E03 - Mr Monk and the Psychic (CORRECT)")
    
    # Starting from E04, each file contains the previous episode
    # So the file named E04 actually contains E03's content
    # But wait - E03 is already correct...
    
    # Let me reconsider based on user observations:
    # User says: select E06 to watch Carnival (which should be E05)
    # This means: File E06 contains Carnival content
    # So: E06 file should be renamed to E05
    
    # User says: select E05 to watch Dale (which should be E04)
    # This means: File E05 contains Dale content
    # So: E05 file should be renamed to E04
    
    # This suggests files E04-E13 all need to shift BACK by 1
    
    print("\n  Files E04-E13 need to shift BACK by 1:")
    print()
    
    for current_num in range(4, 14):
        correct_num = current_num - 1
        current_title = CURRENT_FILES.get(current_num, "Unknown")
        
        rename_map.append({
            "current_filename": f"Monk (2002) - S01E{current_num:02d} - {current_title}.mkv",
            "new_filename": f"Monk (2002) - S01E{correct_num:02d} - {current_title}.mkv",
            "reason": f"File contains E{correct_num:02d} content but named E{current_num:02d}"
        })
        
        print(f"  S01E{current_num:02d} → S01E{correct_num:02d}: {current_title}")
    
    # But wait - what about the LAST episode?
    # If E13 shifts to E12, what's in the current E13 file?
    # It should contain E13 content but there's no E14 file...
    
    print("\n⚠️  WAIT - PROBLEM WITH THIS APPROACH:")
    print("-" * 80)
    print("  If we shift E04-E13 back by 1, we'd have:")
    print("  • E01-E02: Candidate (correct)")
    print("  • E03: Psychic (correct)")
    print("  • E03: Dale (DUPLICATE!)")
    print("  • E04: Carnival")
    print("  • ...")
    print("  • E12: Airplane")
    print("  • Missing E13!")
    
    print("\n🤔 LET ME RECONSIDER...")
    print("-" * 80)
    print("  User observation: 'Select E06 to watch Carnival'")
    print("  Carnival should be E05")
    print("  So file E06 contains Carnival (E05 content)")
    print()
    print("  This means files are shifted FORWARD by 1")
    print("  So we need to shift them BACK by 1")
    print()
    print("  But E01-E02 and E03 are correct...")
    print("  So the shift must start at E04")
    
    return rename_map

if __name__ == "__main__":
    analyze_episode_order()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Verify this analysis with actual video content")
    print("2. Create backup before renaming")
    print("3. Execute renames in correct order to avoid conflicts")
    print("=" * 80)
