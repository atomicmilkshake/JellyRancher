#!/usr/bin/env python3
r"""
Update JSON plans to use new E:\#MEDIA paths instead of E:\Movies and E:\TV Shows
"""
import json
import os
from pathlib import Path

def update_json_paths(json_file_path):
    r"""Update paths in JSON file to use E:\#MEDIA"""
    print(f"Updating {json_file_path}...")

    # Read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Update the response field
    if isinstance(data, list) and len(data) > 0 and 'response' in data[0]:
        response = data[0]['response']

        # Replace paths
        response = response.replace('E:\\\\Movies\\\\', 'E:\\\\#MEDIA\\\\Movies\\\\')
        response = response.replace('E:\\\\TV Shows\\\\', 'E:\\\\#MEDIA\\\\TV Shows\\\\')

        data[0]['response'] = response

        # Write back
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Updated {json_file_path}")
    else:
        print(f"⚠️ Skipping {json_file_path} - unexpected format")

def main():
    lists_dir = Path(r"V:\RavenMaven\lists")

    # Process all cleaned JSON files
    for json_file in lists_dir.glob("*_cleaned.json"):
        update_json_paths(json_file)

    print("\n🎯 All JSON files updated to use E:\\#MEDIA paths!")

if __name__ == "__main__":
    main()