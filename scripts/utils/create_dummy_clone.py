#!/usr/bin/env python3
r"""
Create a dummy clone of Q:\#MEDIA with zero-byte decoy files for testing.
This preserves the directory structure and file names but creates empty files
instead of copying large media content.
"""

import os
import shutil
from pathlib import Path

def create_dummy_clone(source_root: str, dest_root: str):
    r"""
    Create a dummy clone with zero-byte files.

    Args:
        source_root: Source directory (Q:\#MEDIA)
        dest_root: Destination directory
    """
    source_path = Path(source_root)
    dest_path = Path(dest_root)

    print(f"Creating dummy clone from {source_path} to {dest_path}")

    # Walk through all files and directories
    for root, dirs, files in os.walk(source_path):
        # Calculate relative path
        rel_path = Path(root).relative_to(source_path)
        current_dest = dest_path / rel_path

        # Create directory if it doesn't exist
        current_dest.mkdir(parents=True, exist_ok=True)

        for file in files:
            source_file = Path(root) / file
            dest_file = current_dest / file

            # Get file size
            try:
                size = source_file.stat().st_size
            except OSError:
                print(f"Warning: Could not get size for {source_file}")
                size = 0

            # If file is small (< 1MB), copy it
            if size < 1024 * 1024:  # 1MB threshold
                try:
                    shutil.copy2(source_file, dest_file)
                    print(f"Copied: {rel_path / file} ({size} bytes)")
                except Exception as e:
                    print(f"Error copying {source_file}: {e}")
                    # Create zero-byte file as fallback
                    dest_file.touch()
            else:
                # Create zero-byte decoy
                dest_file.touch()
                print(f"Created decoy: {rel_path / file} (was {size} bytes, now 0)")

if __name__ == "__main__":
    source = r"Q:\#MEDIA"
    dest = r"V:\Jellyfin Organizer\test_real_media"

    # Create destination root
    Path(dest).mkdir(parents=True, exist_ok=True)

    create_dummy_clone(source, dest)
    print("Dummy clone creation complete!")