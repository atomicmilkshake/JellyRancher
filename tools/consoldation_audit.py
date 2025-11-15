#!/usr/bin/env python3
"""
One-Shot Consolidation Audit

Runs everything. No switches. Just answers.

Generates a comprehensive report showing:
1. What code exists where (duplicates, unique copies)
2. What capabilities you have (function inventory)
3. What's safe to delete vs. what's the "live" version
4. A simple action plan

Run this. Read the report. Then you know what's real.
"""

import hashlib
import json
import ast
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Where to look
SCAN_ROOTS = [
    Path("V:/JellyRancher/scripts"),
    Path("V:/JellyRancher/backups/scripts_backup_20251110"),
    Path("V:/JellyRancher/Jellyfin Organizer/scripts"),
    Path("V:/JellyRancher/RavenMaven"),
]

# What to ignore
SKIP = {"__pycache__", ".pyc", ".git", ".venv", "node_modules"}

# Output
REPORT_FILE = Path("V:/JellyRancher/CONSOLIDATION_REPORT.json")
READABLE_FILE = Path("V:/JellyRancher/CONSOLIDATION_REPORT.txt")


def semantic_hash(filepath):
    """Hash file content, ignoring whitespace/comments."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = []
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    lines.append(stripped)
            content = '\n'.join(lines)
            return hashlib.md5(content.encode()).hexdigest()
    except:
        return None


def extract_capabilities(filepath):
    """Extract all function and class names from a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        functions = [node.name for node in ast.walk(tree) 
                     if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) 
                   if isinstance(node, ast.ClassDef)]
        
        return {"functions": functions, "classes": classes}
    except:
        return {"functions": [], "classes": []}


def scan_directory(root):
    """Find all Python files in a directory."""
    files = []
    for path in Path(root).rglob("*.py"):
        if any(skip in str(path) for skip in SKIP):
            continue
        files.append(path)
    return files


def main():
    print("🔍 Scanning your codebase...")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Data structures
    file_registry = defaultdict(list)  # hash -> [paths with same content]
    capability_index = {}  # filepath -> {functions, classes}
    directory_stats = defaultdict(lambda: {"files": 0, "size": 0})
    
    # Scan all roots
    all_files = []
    for root in SCAN_ROOTS:
        if not root.exists():
            print(f"⚠️  Skipping non-existent: {root}")
            continue
        
        print(f"📂 Scanning: {root}")
        files = scan_directory(root)
        all_files.extend([(root, f) for f in files])
        print(f"   Found {len(files)} Python files")
    
    print(f"\n📊 Total files to analyze: {len(all_files)}\n")
    
    # Analyze each file
    for idx, (root, filepath) in enumerate(all_files, 1):
        print(f"   [{idx}/{len(all_files)}] {filepath.name}", end='\r')
        
        # Hash for duplicate detection
        file_hash = semantic_hash(filepath)
        if file_hash:
            file_registry[file_hash].append(str(filepath))
        
        # Extract capabilities
        caps = extract_capabilities(filepath)
        if caps["functions"] or caps["classes"]:
            capability_index[str(filepath)] = caps
        
        # Directory stats
        dir_key = str(root)
        directory_stats[dir_key]["files"] += 1
        directory_stats[dir_key]["size"] += filepath.stat().st_size
    
    print("\n\n✅ Analysis complete!\n")
    
    # ========================================================================
    # Generate Report
    # ========================================================================
    
    duplicates = {h: paths for h, paths in file_registry.items() if len(paths) > 1}
    unique_files = {h: paths[0] for h, paths in file_registry.items() if len(paths) == 1}
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_files": len(all_files),
            "unique_files": len(unique_files),
            "duplicate_groups": len(duplicates),
            "total_duplicates": sum(len(paths) - 1 for paths in duplicates.values()),
        },
        "directory_stats": dict(directory_stats),
        "duplicates": duplicates,
        "capabilities": capability_index,
    }
    
    # Save JSON
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"💾 Saved: {REPORT_FILE}")
    
    # ========================================================================
    # Generate Human-Readable Report
    # ========================================================================
    
    with open(READABLE_FILE, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CONSOLIDATION AUDIT REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Summary
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Python files found: {report['summary']['total_files']}\n")
        f.write(f"Unique files: {report['summary']['unique_files']}\n")
        f.write(f"Duplicate groups: {report['summary']['duplicate_groups']}\n")
        f.write(f"Wasted copies: {report['summary']['total_duplicates']}\n\n")
        
        # Directory breakdown
        f.write("DIRECTORY BREAKDOWN\n")
        f.write("-" * 80 + "\n")
        for dir_path, stats in directory_stats.items():
            size_mb = stats['size'] / (1024 * 1024)
            f.write(f"{dir_path}\n")
            f.write(f"  Files: {stats['files']}\n")
            f.write(f"  Size: {size_mb:.2f} MB\n\n")
        
        # Duplicates (the money shot)
        f.write("\nDUPLICATE FILES (THESE ARE IDENTICAL)\n")
        f.write("=" * 80 + "\n")
        for file_hash, paths in duplicates.items():
            # Pick the most recently modified as "canonical"
            paths_with_mtime = [(p, Path(p).stat().st_mtime) for p in paths]
            paths_with_mtime.sort(key=lambda x: x[1], reverse=True)
            
            canonical = paths_with_mtime[0][0]
            copies = [p for p, _ in paths_with_mtime[1:]]
            
            f.write(f"\n{Path(canonical).name}\n")
            f.write(f"  KEEP THIS ONE (newest): {canonical}\n")
            f.write(f"  DELETE THESE COPIES:\n")
            for copy in copies:
                f.write(f"    - {copy}\n")
        
        # Unique capabilities
        f.write("\n\nUNIQUE CAPABILITIES INVENTORY\n")
        f.write("=" * 80 + "\n")
        
        # Group by filename
        by_filename = defaultdict(list)
        for filepath, caps in capability_index.items():
            filename = Path(filepath).name
            by_filename[filename].append((filepath, caps))
        
        for filename in sorted(by_filename.keys()):
            entries = by_filename[filename]
            if len(entries) == 1:
                # Unique file
                filepath, caps = entries[0]
                f.write(f"\n{filename}\n")
                f.write(f"  Location: {filepath}\n")
                if caps["classes"]:
                    f.write(f"  Classes: {', '.join(caps['classes'][:5])}\n")
                if caps["functions"]:
                    f.write(f"  Functions: {', '.join(caps['functions'][:10])}\n")
            else:
                # Multiple versions exist
                f.write(f"\n{filename} (WARNING: {len(entries)} versions exist)\n")
                for filepath, caps in entries:
                    f.write(f"  - {filepath}\n")
                    f.write(f"    Functions: {len(caps['functions'])}, Classes: {len(caps['classes'])}\n")
        
        # Action plan
        f.write("\n\nRECOMMENDED ACTION PLAN\n")
        f.write("=" * 80 + "\n")
        f.write("1. Review the DUPLICATE FILES section above\n")
        f.write("2. The 'KEEP THIS ONE' entries are the newest versions\n")
        f.write("3. The 'DELETE THESE COPIES' are safe to remove\n")
        f.write("4. Check the 'UNIQUE CAPABILITIES INVENTORY' for code you need\n")
        f.write("5. Create your backup ZIP before deleting anything\n")
        f.write("6. Use the 'KEEP THIS ONE' paths to build your clean V:/JellyRancher_v2\n")
        f.write("\nEstimated cleanup savings:\n")
        
        total_waste = sum(
            sum(Path(p).stat().st_size for p in paths[1:])
            for paths in duplicates.values()
        )
        f.write(f"  You can reclaim ~{total_waste / (1024*1024):.1f} MB by removing duplicates\n")
    
    print(f"📄 Saved: {READABLE_FILE}\n")
    print("=" * 80)
    print("✅ DONE")
    print("=" * 80)
    print(f"\nRead this file now: {READABLE_FILE}")
    print("\nIt tells you:")
    print("  • Which files are duplicates")
    print("  • Which version to keep (newest)")
    print("  • What capabilities exist where")
    print("  • How much space you're wasting")
    print("\nAfter reading it, you'll know exactly what's safe to delete.")
    print("=" * 80)


if __name__ == "__main__":
    main()