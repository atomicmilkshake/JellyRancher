#!/usr/bin/env python3
"""
Create NFO file for Lost S06E01-E02 premiere
"""

from pathlib import Path

LOST_SEASON_06 = Path(r"E:\#MEDIA\TV Shows\Lost (2004)\Season 06")

# Multi-episode NFO content for Lost S06 premiere
NFO_CONTENT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<episodedetails>
    <title>LA X (1)</title>
    <showtitle>Lost</showtitle>
    <season>6</season>
    <episode>1</episode>
    <plot>The aftermath from Juliet's detonation of the hydrogen bomb is revealed.</plot>
    <aired>2010-02-02</aired>
    <uniqueid type="tvdb" default="true">339741</uniqueid>
    <uniqueid type="imdb">tt1466074</uniqueid>
</episodedetails>
<episodedetails>
    <title>LA X (2)</title>
    <showtitle>Lost</showtitle>
    <season>6</season>
    <episode>2</episode>
    <plot>The aftermath from Juliet's detonation of the hydrogen bomb is revealed.</plot>
    <aired>2010-02-02</aired>
    <uniqueid type="tvdb" default="true">339742</uniqueid>
    <uniqueid type="imdb">tt1466074</uniqueid>
</episodedetails>
'''

def create_nfo():
    """Create NFO file for the Lost S06 premiere"""
    
    print("=" * 80)
    print("CREATE LOST S06E01-E02 NFO FILE")
    print("=" * 80)
    
    if not LOST_SEASON_06.exists():
        print(f"❌ ERROR: Directory not found: {LOST_SEASON_06}")
        return
    
    # Find the premiere file
    premiere_files = list(LOST_SEASON_06.glob("*s06e01-e02*.mkv"))
    
    if not premiere_files:
        print("❌ ERROR: Could not find premiere file (s06e01-e02)")
        return
    
    premiere_file = premiere_files[0]
    print(f"\n✓ Found premiere file: {premiere_file.name}")
    
    # Create NFO file with same name as video file
    nfo_file = premiere_file.with_suffix('.nfo')
    
    print(f"\n📝 Creating NFO file: {nfo_file.name}")
    print("\nNFO Content:")
    print("-" * 80)
    print(NFO_CONTENT)
    print("-" * 80)
    
    # Write NFO file
    nfo_file.write_text(NFO_CONTENT, encoding='utf-8')
    
    print(f"\n✅ NFO file created successfully!")
    print(f"\n📋 Next steps:")
    print("   1. Refresh metadata for Lost in Jellyfin")
    print("   2. Check if episodes now show correctly numbered")

if __name__ == "__main__":
    create_nfo()
