#!/usr/bin/env python3
"""
JellyRancher Root Directory Cleanup Script
Identifies and helps clean up temporary files, backups, and artifacts
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

def analyze_cleanup_candidates():
    """Analyze files that could be cleaned up"""
    root = Path(".")

    candidates = {
        "temporary_files": [],
        "backup_files": [],
        "test_artifacts": [],
        "log_files": [],
        "cache_directories": []
    }

    # Temporary files (temp_*.py)
    for file in root.glob("temp_*.py"):
        candidates["temporary_files"].append(file)

    # Backup files
    backup_patterns = ["*.bak", "*.backup", "*backup*"]
    for pattern in backup_patterns:
        for file in root.glob(pattern):
            candidates["backup_files"].append(file)

    # Test artifacts
    test_files = ["coverage.xml", ".coverage"]
    for file in test_files:
        if (root / file).exists():
            candidates["test_artifacts"].append(root / file)

    # Cache directories
    cache_dirs = [".pytest_cache", "__pycache__", "htmlcov"]
    for dir_name in cache_dirs:
        if (root / dir_name).exists():
            candidates["cache_directories"].append(root / dir_name)

    # Log files
    for file in root.glob("*.log"):
        candidates["log_files"].append(file)

    return candidates

def get_file_info(filepath):
    """Get file information"""
    stat = filepath.stat()
    return {
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "size_mb": round(stat.st_size / (1024 * 1024), 2)
    }

def calculate_cleanup_size(candidates):
    """Calculate total size of files to be cleaned up"""
    total_size = 0

    for category, files in candidates.items():
        for file in files:
            if file.is_file():
                total_size += file.stat().st_size
            elif file.is_dir():
                total_size += sum(f.stat().st_size for f in file.rglob("*") if f.is_file())

    return total_size

def print_cleanup_report(candidates):
    """Print detailed cleanup report"""
    print("🧹 JELLYRANCHER ROOT DIRECTORY CLEANUP ANALYSIS")
    print("=" * 60)

    total_files = sum(len(files) for files in candidates.values())
    total_size = calculate_cleanup_size(candidates)

    print(f"📊 Total cleanup candidates: {total_files} items")
    print(f"💾 Estimated space savings: {total_size / (1024*1024):.2f} MB")
    print()

    for category, files in candidates.items():
        if files:
            print(f"📁 {category.replace('_', ' ').title()}: {len(files)} items")
            for file in files:
                info = get_file_info(file) if file.is_file() else {"size_mb": "DIR", "modified": "N/A"}
                print(f"   🗑️  {file.name} ({info['size_mb']} MB, modified: {info['modified']})")
            print()

def perform_safe_cleanup(candidates):
    """Perform safe cleanup of identified files"""
    print("🧹 PERFORMING SAFE CLEANUP...")
    print("=" * 60)

    # Files that are always safe to delete
    safe_patterns = [
        "temp_*.py",      # Temporary development files
        "*.bak",          # Backup files
        "*.backup",       # More backup files
        "coverage.xml",   # Test coverage
        ".coverage",      # Coverage data
        "*.log",          # Log files
    ]

    # Directories that are always safe to delete
    safe_dirs = [
        "__pycache__",    # Python bytecode cache
        ".pytest_cache",  # Pytest cache
        "htmlcov",        # HTML coverage reports
    ]

    deleted_count = 0
    saved_space = 0

    # Clean safe files
    for pattern in safe_patterns:
        for file in Path(".").glob(pattern):
            if file.exists():
                size = file.stat().st_size
                try:
                    file.unlink()
                    print(f"✅ Deleted: {file.name}")
                    deleted_count += 1
                    saved_space += size
                except Exception as e:
                    print(f"❌ Failed to delete {file.name}: {e}")

    # Clean safe directories
    for dir_name in safe_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"✅ Deleted directory: {dir_name}/")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete directory {dir_name}: {e}")

    # Handle sensitive files separately
    sensitive_files = []
    for file in candidates["backup_files"]:
        if "credentials" in file.name.lower() or "backup" in file.name.lower():
            sensitive_files.append(file)

    if sensitive_files:
        print("\n⚠️  SENSITIVE FILES DETECTED:")
        for file in sensitive_files:
            print(f"   📁 {file.name} - REVIEW BEFORE DELETING")
            print("      This file may contain credentials or sensitive data")
        print("\n💡 Move these to backups/ directory instead of deleting")

    print(f"\n📊 Cleanup Summary:")
    print(f"   Files deleted: {deleted_count}")
    print(f"   Space saved: {saved_space / (1024*1024):.2f} MB")
    if sensitive_files:
        print(f"   Sensitive files to review: {len(sensitive_files)}")

def main():
    """Main cleanup analysis function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        # Perform actual cleanup
        candidates = analyze_cleanup_candidates()
        perform_safe_cleanup(candidates)
    else:
        # Just analyze
        print("Analyzing root directory for cleanup opportunities...\n")
        candidates = analyze_cleanup_candidates()
        print_cleanup_report(candidates)

        print("💡 RECOMMENDATIONS:")
        print("✅ SAFE TO DELETE:")
        print("   • temp_*.py files (temporary development scripts)")
        print("   • *.bak and *.backup files (old backups)")
        print("   • coverage.xml and .coverage (test artifacts)")
        print("   • __pycache__/ and .pytest_cache/ (Python cache)")
        print("   • htmlcov/ (HTML coverage reports)")
        print("   • *.log files (build logs)")
        print()
        print("⚠️  REVIEW BEFORE DELETING:")
        print("   • *backup* files (may contain credentials or important data)")
        print("   • Check if any temp files contain important code")
        print()
        print("🚀 TO CLEAN UP: Run 'python cleanup.py --clean'")
        print("   Or manually delete the files listed above")

if __name__ == "__main__":
    main()