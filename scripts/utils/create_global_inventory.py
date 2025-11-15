#!/usr/bin/env python3
"""
Global Media Inventory Scanner
Scans #MEDIA folders across multiple drives (L, M, Q, S, W)
Excludes Python virtual environments and project files
"""

import os
from pathlib import Path
from datetime import datetime

# Drives to scan
DRIVES = ['L:', 'M:', 'Q:', 'S:', 'W:']
MEDIA_FOLDER = '#MEDIA'

# Patterns to exclude
EXCLUDE_DIRS = {
    '.venv',
    'venv',
    '__pycache__',
    '.git',
    'node_modules',
    'Scripts',
    'Lib',
    'Include',
    'site-packages',
}

EXCLUDE_EXTENSIONS = {
    '.py',
    '.pyc',
    '.pyo',
    '.pyd',
    '.ps1',
    '.md',
    '.txt',
    '.log',
    '.json',
    '.xml',
    '.nfo',  # Jellyfin metadata
    '.jpg',
    '.png',
    '.jpeg',
    '.gif',
    '.bmp',
}

# File extensions we DO want to track (media files only, no subtitles)
MEDIA_EXTENSIONS = {
    '.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.webm',
    '.mpg', '.mpeg', '.m2ts', '.ts', '.vob', '.iso',
}

def should_exclude_dir(dir_name: str) -> bool:
    """Check if directory should be excluded"""
    # Exclude trickplay directories
    if 'trickplay' in dir_name.lower():
        return True
    return dir_name in EXCLUDE_DIRS or dir_name.startswith('.')

def should_include_file(file_path: Path) -> bool:
    """Check if file should be included in inventory"""
    ext = file_path.suffix.lower()
    
    # Include only media files (no subtitles, no trickplay)
    return ext in MEDIA_EXTENSIONS

def scan_media_folder(drive: str) -> list:
    """Scan a single drive's #MEDIA folder"""
    media_path = Path(drive) / MEDIA_FOLDER
    
    if not media_path.exists():
        print(f"  ⚠️  {media_path} does not exist")
        return []
    
    print(f"  📂 Scanning {media_path}...")
    
    inventory = []
    
    try:
        for root, dirs, files in os.walk(media_path):
            root_path = Path(root)
            
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude_dir(d)]
            
            # Check if we're in a virtual environment path
            if any(excluded in root_path.parts for excluded in EXCLUDE_DIRS):
                continue
            
            # Add media files only
            for file in files:
                file_path = root_path / file
                if should_include_file(file_path):
                    rel_path = file_path.relative_to(media_path.parent)
                    inventory.append(str(rel_path))
    
    except Exception as e:
        print(f"  ❌ Error scanning {media_path}: {e}")
    
    return inventory

def create_global_inventory():
    """Create global inventory across all drives"""
    print("=" * 80)
    print("GLOBAL MEDIA INVENTORY SCANNER")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_inventory = {}
    total_items = 0
    
    for drive in DRIVES:
        print(f"\n🔍 Scanning drive {drive}...")
        inventory = scan_media_folder(drive)
        
        if inventory:
            all_inventory[drive] = inventory
            print(f"  ✅ Found {len(inventory):,} items")
            total_items += len(inventory)
        else:
            print(f"  ℹ️  No media found or drive not accessible")
    
    print("\n" + "=" * 80)
    print(f"TOTAL ITEMS FOUND: {total_items:,}")
    print("=" * 80)
    
    # Write individual drive inventories
    output_dir = Path(__file__).parent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for drive, inventory in all_inventory.items():
        drive_letter = drive.replace(':', '')
        output_file = output_dir / f"{drive_letter}_MEDIA_inventory.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in sorted(inventory):
                f.write(f"{item}\n")
        
        print(f"\n📄 Wrote {drive} inventory to: {output_file.name}")
    
    # Write combined inventory
    combined_file = output_dir / f"GLOBAL_MEDIA_inventory_{timestamp}.txt"
    
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write(f"Global Media Inventory\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Items: {total_items:,}\n")
        f.write("=" * 80 + "\n\n")
        
        for drive in DRIVES:
            if drive in all_inventory:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"DRIVE: {drive}\n")
                f.write(f"Items: {len(all_inventory[drive]):,}\n")
                f.write(f"{'=' * 80}\n\n")
                
                for item in sorted(all_inventory[drive]):
                    f.write(f"{item}\n")
    
    print(f"\n📄 Wrote combined inventory to: {combined_file.name}")
    print(f"\n✅ Inventory complete!")
    print(f"⏱️  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    create_global_inventory()
