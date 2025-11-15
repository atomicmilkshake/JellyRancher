#!/usr/bin/env python3
r"""
Update JSON plans to use corrected E:\#MEDIA source paths
"""
import json
import os
from pathlib import Path

def update_json_source_paths(json_file_path):
    """Update OLD: paths in JSON file to reflect moved folders"""
    print(f"Updating source paths in {json_file_path}...")

    # Read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Update the response field
    if isinstance(data, list) and len(data) > 0 and 'response' in data[0]:
        response = data[0]['response']

        # Replace OLD: paths to use E:\#MEDIA\MOVIES instead of E:\MOVIES
        response = response.replace('OLD: E:\\MOVIES\\', 'OLD: E:\\#MEDIA\\MOVIES\\')

        data[0]['response'] = response

        # Write back
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Updated source paths in {json_file_path}")
    else:
        print(f"⚠️ Skipping {json_file_path} - unexpected format")

def main():
    lists_dir = Path(r"V:\RavenMaven\lists")

    # Process all cleaned and processed JSON files
    for json_file in lists_dir.glob("*_cleaned.json"):
        update_json_source_paths(json_file)
    
    for json_file in lists_dir.glob("*_processed.json"):
        update_json_source_paths(json_file)

    print("\n🎯 All JSON files updated with corrected E:\\#MEDIA source paths!")

if __name__ == "__main__":
    main()