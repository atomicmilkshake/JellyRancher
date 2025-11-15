#!/usr/bin/env python3
"""
RavenMaven Batch Processor
Processes media file lists in batch mode for rapid cleanup
"""

import sys
import os
import json
import argparse
from datetime import datetime
from ravenmaven_client import PoeClient

def load_prompt_file(prompt_path):
    """Load prompt from file."""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading prompt file: {e}")
        return None

def load_file_list(input_path):
    """Load file list from text file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading file list: {e}")
        return None

def save_results(results, output_path):
    """Save processing results to JSON."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_path}")
    except Exception as e:
        print(f"Error saving results: {e}")

def process_batch(file_list, prompt, model="Claude-Sonnet-4.5"):
    """Process a batch of files through LLM."""
    # Format the file list for the prompt
    filepaths_text = "\n".join(file_list)
    full_prompt = prompt.replace("{filepaths}", filepaths_text)

    # Initialize client
    client = PoeClient()

    try:
        print(f"Processing {len(file_list)} files with {model}...")
        response = client.send_message(full_prompt, model=model)

        # Parse the response (assuming OLD: NEW format)
        lines = response.strip().split('\n')
        mappings = []

        for line in lines:
            if line.startswith('OLD: ') and 'NEW: ' in line:
                parts = line.split('NEW: ', 1)
                old_path = parts[0].replace('OLD: ', '').strip()
                new_path = parts[1].strip()
                mappings.append({"old": old_path, "new": new_path})

        result = {
            "success": True,
            "response": response,
            "prompt": full_prompt,
            "model": model,
            "file_count": len(file_list),
            "mappings": mappings,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "prompt": full_prompt,
            "model": model,
            "file_count": len(file_list),
            "timestamp": datetime.now().isoformat()
        }

    return result

def main():
    parser = argparse.ArgumentParser(description='RavenMaven Batch Processor')
    parser.add_argument('--input', required=True, help='Input file list (.txt)')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--prompt-file', required=True, help='Prompt template file')
    parser.add_argument('--model', default='Claude-Sonnet-4.5', help='LLM model to use')

    args = parser.parse_args()

    # Load inputs
    prompt = load_prompt_file(args.prompt_file)
    if not prompt:
        sys.exit(1)

    file_list = load_file_list(args.input)
    if not file_list:
        sys.exit(1)

    # Process batch
    result = process_batch(file_list, prompt, args.model)

    # Save results
    save_results(result, args.output)

    if result["success"]:
        print(f"✅ Successfully processed {len(file_list)} files")
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == '__main__':
    main()