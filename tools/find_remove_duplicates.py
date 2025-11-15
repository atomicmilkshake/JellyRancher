#!/usr/bin/env python3
"""
Script to find and remove duplicate files and zero-byte files from all subfolders.
Duplicates are identified by identical file contents (CRC32 hash).
"""

import os
import hashlib
import sys
import zlib
from pathlib import Path
from collections import defaultdict
import concurrent.futures
import threading

def calculate_file_hash(filepath):
    """Calculate CRC32 hash of a file's contents."""
    try:
        with open(filepath, 'rb') as f:
            return zlib.crc32(f.read())
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def find_duplicate_files(root_dir):
    """Find duplicate files by content hash using multithreading."""
    hash_to_files = defaultdict(list)
    zero_byte_files = []
    files_to_hash = []

    # Directories to ignore
    ignore_dirs = {'__pycache__', '.venv', 'venv', 'env', '.env'}

    # First pass: collect all files and identify zero-byte files
    print("Scanning directories for files...")
    for filepath in Path(root_dir).rglob('*'):
        if filepath.is_file():
            # Skip files in ignored directories
            if any(part in ignore_dirs for part in filepath.parts):
                continue

            # Check for zero-byte files
            if filepath.stat().st_size == 0:
                zero_byte_files.append(filepath)
            else:
                files_to_hash.append(filepath)

    print(f"Found {len(zero_byte_files)} zero-byte files and {len(files_to_hash)} files to hash.")

    # Use multithreading to hash files
    print("Calculating file hashes using multithreading...")
    hash_results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as executor:
        # Submit all hashing tasks
        future_to_file = {executor.submit(calculate_file_hash, filepath): filepath for filepath in files_to_hash}

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                file_hash = future.result()
                if file_hash is not None:
                    hash_results[filepath] = file_hash
            except Exception as e:
                print(f"Error hashing {filepath}: {e}")

    # Group files by hash
    for filepath, file_hash in hash_results.items():
        hash_to_files[file_hash].append(filepath)

    # Find duplicates (files with same hash)
    duplicates = {hash_val: files for hash_val, files in hash_to_files.items() if len(files) > 1}

    return duplicates, zero_byte_files

def main():
    root_dir = 'V:\\JellyRancher'  # Use Windows path format

    print("Scanning for duplicate files and zero-byte files...")
    duplicates, zero_byte_files = find_duplicate_files(root_dir)

    total_removed = 0

    # Remove zero-byte files first
    if zero_byte_files:
        print(f"\nFound {len(zero_byte_files)} zero-byte files:")
        for file_path in zero_byte_files:
            print(f"  REMOVE: {file_path}")
            try:
                os.remove(file_path)
                print(f"    ✓ Removed zero-byte file: {file_path}")
                total_removed += 1
            except Exception as e:
                print(f"    ✗ Failed to remove {file_path}: {e}")

    # Remove duplicate files
    if duplicates:
        print(f"\nFound {len(duplicates)} groups of duplicate files:")
        for hash_val, files in duplicates.items():
            print(f"\nDuplicate group (CRC32: {hash_val:08x}):")
            # Sort by path to prefer keeping files in main directories
            sorted_files = sorted(files, key=lambda x: (len(x.parts), str(x)))

            # Keep the first file (shortest path), remove others
            keep_file = sorted_files[0]
            remove_files = sorted_files[1:]

            print(f"  KEEP: {keep_file}")
            for file_to_remove in remove_files:
                print(f"  REMOVE: {file_to_remove}")
                try:
                    os.remove(file_to_remove)
                    print(f"    ✓ Removed duplicate: {file_to_remove}")
                    total_removed += 1
                except Exception as e:
                    print(f"    ✗ Failed to remove {file_to_remove}: {e}")

    print(f"\nSummary: Removed {total_removed} files total ({len(zero_byte_files)} zero-byte + {sum(len(files)-1 for files in duplicates.values())} duplicates).")

if __name__ == "__main__":
    main()