#!/usr/bin/env python3
"""
LLM Response Parser for RavenMaven
Converts LLM text responses into proper JSON format for jellyfin_safe_executor.py
"""

import json
import re
import os
from pathlib import Path

def clean_llm_response(response_text):
    """
    Clean up the LLM response text to extract just the OLD: NEW mappings
    """
    # Find the start of the actual mappings (after any introductory text)
    lines = response_text.split('\n')
    cleaned_lines = []

    # Skip introductory text and find the first OLD: line
    found_first_old = False
    for line in lines:
        line = line.strip()
        if line.startswith('OLD:'):
            found_first_old = True
        if found_first_old:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def process_chunk_file(chunk_json_path, output_path):
    """
    Process a single chunk JSON file and clean up the response text
    """
    try:
        with open(chunk_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list) and len(data) > 0:
            item = data[0]
            if 'response' in item:
                # Clean up the response text
                cleaned_response = clean_llm_response(item['response'])

                # Create cleaned data structure
                cleaned_data = [{
                    'success': item.get('success', True),
                    'response': cleaned_response,
                    'prompt': item.get('prompt', ''),
                    'model': item.get('model', ''),
                    'file_count': item.get('file_count', 0),
                    'timestamp': item.get('timestamp', ''),
                    'mappings': []  # Will be populated by the executor
                }]

                # Save cleaned data
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

                print(f"✅ Cleaned response for {chunk_json_path}")
                return True

    except Exception as e:
        print(f"❌ Error processing {chunk_json_path}: {e}")

    return False

def main():
    """
    Main function to process all chunk files
    """
    lists_dir = Path("V:/RavenMaven/lists")

    print("🎯 Starting LLM Response Cleaner...")

    for chunk_num in range(1, 10):
        chunk_file = lists_dir / f"chunk{chunk_num}_processed.json"
        output_file = lists_dir / f"chunk{chunk_num}_cleaned.json"

        if chunk_file.exists():
            success = process_chunk_file(chunk_file, output_file)
            if success:
                print(f"  ✅ chunk{chunk_num}_cleaned.json")
        else:
            print(f"⚠️  Chunk file not found: {chunk_file}")

    print("🎉 Response cleaning complete!")

if __name__ == "__main__":
    main()