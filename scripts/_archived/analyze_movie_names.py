#!/usr/bin/env python3
"""
Analyze and report movie naming issues in media library

Identifies:
1. Truncated movie titles (e.g., "Cloutie Ru" instead of full title)
2. Codec tags in filenames (e.g., "H 265")
3. Movies not in proper folder structure
4. Other naming inconsistencies
"""

import sys
from pathlib import Path
import re
import json

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / '_common'))
from config_loader import load_config, get_reports_dir

def analyze_movie_names(movie_paths: list):
    """Analyze all movie files for naming issues."""

    issues = {
        'truncated_titles': [],
        'codec_in_name': [],
        'not_in_folder': [],
        'missing_year': [],
        'other_issues': []
    }

    # Get all movie files from all configured paths
    movie_files = []
    for movies_path in movie_paths:
        movies_dir = Path(movies_path)
        if not movies_dir.exists():
            print(f"[SKIP] Movies directory not found: {movies_dir}")
            continue

        for ext in ['.mkv', '.mp4', '.avi', '.m4v']:
            movie_files.extend(movies_dir.rglob(f'*{ext}'))

    print(f"[INFO] Found {len(movie_files)} movie files")
    print("\n" + "=" * 70)
    print("ANALYZING MOVIE NAMES")
    print("=" * 70 + "\n")

    for movie_file in sorted(movie_files):
        # Get relative path from the immediate parent of the Movies folder
        try:
            relative_path = movie_file.relative_to(movie_file.parents[2])
        except:
            relative_path = movie_file
        filename = movie_file.stem
        parent_folder = movie_file.parent.name
        
        # Check 1: Codec tags in filename
        codec_patterns = [r'H\.?265', r'H\.?264', r'HEVC', r'x264', r'x265', r'AVC']
        for pattern in codec_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                issues['codec_in_name'].append({
                    'path': str(relative_path),
                    'filename': filename,
                    'issue': f'Contains codec tag: {pattern}',
                    'parent_folder': parent_folder
                })
                break
        
        # Check 2: Truncated titles (suspiciously short or incomplete words)
        # Look for words that end abruptly (less than 3 chars before year)
        truncated_pattern = r'\b\w{1,2}\s+\d{4}'
        if re.search(truncated_pattern, filename):
            issues['truncated_titles'].append({
                'path': str(relative_path),
                'filename': filename,
                'issue': 'Possibly truncated title',
                'parent_folder': parent_folder
            })
        
        # Check 3: Not in proper folder structure (file directly in Movies/)
        # Check if parent folder name matches the movie filename pattern
        if parent_folder.lower() in ['movies', '#media']:
            issues['not_in_folder'].append({
                'path': str(relative_path),
                'filename': filename,
                'issue': 'Not in dedicated movie folder',
                'parent_folder': parent_folder
            })
        
        # Check 4: Missing year in filename
        if not re.search(r'\(\d{4}\)', filename):
            issues['missing_year'].append({
                'path': str(relative_path),
                'filename': filename,
                'issue': 'Missing year in filename',
                'parent_folder': parent_folder
            })
    
    # Print results
    total_issues = sum(len(v) for v in issues.values())
    
    if total_issues == 0:
        print("✅ No naming issues found!")
        return issues
    
    print(f"⚠️  Found {total_issues} naming issues:\n")
    
    # Truncated titles
    if issues['truncated_titles']:
        print(f"🔴 TRUNCATED TITLES ({len(issues['truncated_titles'])} files)")
        print("-" * 70)
        for item in issues['truncated_titles']:
            print(f"  📁 {item['path']}")
            print(f"     Issue: {item['issue']}")
            print()
    
    # Codec tags
    if issues['codec_in_name']:
        print(f"🟡 CODEC TAGS IN FILENAME ({len(issues['codec_in_name'])} files)")
        print("-" * 70)
        for item in issues['codec_in_name']:
            print(f"  📁 {item['path']}")
            print(f"     Issue: {item['issue']}")
            print()
    
    # Not in folder
    if issues['not_in_folder']:
        print(f"🟠 NOT IN DEDICATED FOLDER ({len(issues['not_in_folder'])} files)")
        print("-" * 70)
        for item in issues['not_in_folder']:
            print(f"  📁 {item['path']}")
            print(f"     Issue: {item['issue']}")
            print()
    
    # Missing year
    if issues['missing_year']:
        print(f"🔵 MISSING YEAR ({len(issues['missing_year'])} files)")
        print("-" * 70)
        for item in issues['missing_year']:
            print(f"  📁 {item['path']}")
            print(f"     Issue: {item['issue']}")
            print()
    
    # Save to JSON
    output_file = get_reports_dir() / 'movie_naming_issues.json'
    output_file.parent.mkdir(exist_ok=True, parents=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(issues, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print(f"[INFO] Full report saved to: {output_file}")
    print("=" * 70)

    return issues


def suggest_fixes(issues: dict):
    """Suggest fixes for identified issues."""
    
    print("\n" + "=" * 70)
    print("SUGGESTED FIXES")
    print("=" * 70 + "\n")
    
    if issues['truncated_titles']:
        print("🔴 TRUNCATED TITLES - Manual Review Required")
        print("-" * 70)
        print("These files appear to have truncated titles and need manual correction:")
        print()
        for item in issues['truncated_titles']:
            print(f"  Current: {item['filename']}")
            print(f"  Path: {item['path']}")
            print(f"  → Needs: Full movie title research and rename")
            print()
    
    if issues['codec_in_name']:
        print("🟡 CODEC TAGS - Can be automatically removed")
        print("-" * 70)
        print("These files have codec tags that should be removed:")
        print()
        for item in issues['codec_in_name']:
            # Suggest cleaned name
            cleaned = item['filename']
            for pattern in [r'H\.?265', r'H\.?264', r'HEVC', r'x264', r'x265', r'AVC']:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            print(f"  Current: {item['filename']}")
            print(f"  Suggested: {cleaned}")
            print(f"  Path: {item['path']}")
            print()


if __name__ == '__main__':
    config = load_config()
    movie_paths = config['media_paths']['movies']

    print(f"[INFO] Analyzing movies in {len(movie_paths)} configured paths")

    issues = analyze_movie_names(movie_paths)

    if any(issues.values()):
        suggest_fixes(issues)
