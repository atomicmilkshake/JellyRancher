#!/usr/bin/env python3
"""
Performance Test for Optimized File Hashing

Demonstrates the performance improvements of the optimized hashing functions.
"""

import time
from pathlib import Path
from _common.media_utils import hash_file, hash_file_fast, hash_files_parallel

def test_hashing_performance():
    """Test hashing performance on sample files."""
    print("🔬 File Hashing Performance Test")
    print("=" * 40)

    # Find some test files
    test_files = []
    search_paths = [
        Path("Q:/#MEDIA/Movies"),
        Path("M:/#MEDIA/Movies"),
        Path("L:/#MEDIA/Movies"),
        Path("S:/#MEDIA"),
        Path("../test_real_media/Movies"),
        Path("../test_real_media/TV Shows"),
        Path("../scripts/test_media/movies"),
        Path("../scripts/test_media/TV Shows")
    ]

    for search_path in search_paths:
        if search_path.exists():
            # Find a few media files (recursive search)
            media_files = list(search_path.glob("**/*.mkv")) + list(search_path.glob("**/*.mp4"))
            test_files.extend(media_files[:2])  # Take 2 files per directory

    if not test_files:
        print("❌ No test files found")
        return

    print(f"📁 Found {len(test_files)} test files:")
    for f in test_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"   • {f.name}: {size_mb:.1f} MB")
    print()

    # Test 1: Original hashing
    print("🕐 Testing original hash_file()...")
    start_time = time.time()
    original_hashes = {}
    for file_path in test_files:
        hash_result = hash_file(file_path)
        original_hashes[file_path] = hash_result
    original_time = time.time() - start_time

    # Test 2: Optimized hashing
    print("🚀 Testing optimized hash_file_fast()...")
    start_time = time.time()
    fast_hashes = {}
    for file_path in test_files:
        hash_result = hash_file_fast(file_path)
        fast_hashes[file_path] = hash_result
    fast_time = time.time() - start_time

    # Test 3: Parallel hashing
    print("⚡ Testing parallel hash_files_parallel()...")
    start_time = time.time()
    parallel_hashes = hash_files_parallel(test_files, max_workers=4)
    parallel_time = time.time() - start_time

    # Results
    print("\n📊 PERFORMANCE RESULTS")
    print("=" * 40)
    print(f"Original hashing:  {original_time:.2f}s")
    print(f"Fast hashing:      {fast_time:.2f}s")
    print(f"Parallel hashing:  {parallel_time:.2f}s")
    print()

    # Verify results match
    print("🔍 VERIFICATION")
    print("=" * 40)
    all_match = True
    for file_path in test_files:
        orig = original_hashes[file_path]
        fast = fast_hashes[file_path]
        para = parallel_hashes[file_path]

        if orig == fast == para:
            print(f"✅ {file_path.name}: All hashes match")
        else:
            print(f"❌ {file_path.name}: Hash mismatch!")
            all_match = False

    if all_match:
        print("\n✅ All hashing methods produce identical results!")

    # Performance analysis
    speedup_fast = original_time / fast_time if fast_time > 0 else 1
    speedup_parallel = original_time / parallel_time if parallel_time > 0 else 1

    print("\n🎯 PERFORMANCE ANALYSIS")
    print("=" * 40)
    print(f"Fast hashing speedup: {speedup_fast:.1f}x")
    print(f"Parallel hashing speedup: {speedup_parallel:.1f}x")
    print(f"Time per file (original): {original_time/len(test_files):.2f}s")
    print(f"Time per file (fast): {fast_time/len(test_files):.2f}s")
    if len(test_files) > 1:
        print(f"Time per file (parallel): {parallel_time/len(test_files):.2f}s")
    print("\n💡 KEY OPTIMIZATIONS:")
    print("   • Memory mapping for large files (>50MB)")
    print("   • Larger chunk sizes (256KB vs 8KB)")
    print("   • Parallel processing for multiple files")
    print("   • Same-filesystem optimization (size-only verification)")

if __name__ == "__main__":
    test_hashing_performance()