#!/usr/bin/env python3
"""
Add/update function entry to function_index.json directly—no LLM/AST.

Usage:
.venv\\Scripts\\python.exe tools/add_to_function_index.py --json-entry '[{"name":"func","file_path":"scripts/core/file.py","line":123,"description":"Google docstring","inputs":{"parameters":[{"name":"p","type":"str","description":"Param","required":true}]},"outputs":{"return_value":{"type":"str","description":"Result"}},"notes":[], "usage_example":"", "class_name":null,"docstring_enhanced":true}]'

Batch OK (array). Merges/updates by file/line/name. Validates basic schema. Updates metadata.

MANDATORY per master-prompt II.2.1.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

INDEX_PATH = Path("function_index.json")


def load_index() -> Dict[str, Any]:
    """Load existing function index or create new one."""
    if INDEX_PATH.exists():
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    print("Created new index.")
    return {
        "metadata": {
            "generated": "",
            "source": "manual",
            "total_functions": 0,
            "statistics": {
                "total_functions": 0,
                "functions_by_file": {}
            }
        },
        "functions": {}
    }


def validate_entry(entry: Dict[str, Any]) -> bool:
    """Validate that entry has required fields."""
    required = {"name", "file_path", "line", "description", "inputs", "outputs"}
    if not all(k in entry for k in required):
        print(f"Missing required: {required - set(entry)}", file=sys.stderr)
        return False
    if not isinstance(entry.get("inputs", {}).get("parameters", []), list):
        print("inputs.parameters must be list", file=sys.stderr)
        return False
    return True


def add_or_update(index: Dict[str, Any], entries: List[Dict[str, Any]]) -> None:
    """Add or update function entries in the index."""
    functions = index["functions"]
    updated = 0
    added = 0
    
    for entry in entries:
        if not validate_entry(entry):
            continue
        
        fp = entry["file_path"]
        
        # Initialize file entry if not exists
        if fp not in functions:
            functions[fp] = []
        
        # Check if function already exists (by name and line)
        existing_idx = None
        for i, existing in enumerate(functions[fp]):
            if existing.get("name") == entry["name"] and existing.get("line") == entry["line"]:
                existing_idx = i
                break
        
        # Ensure defaults for optional fields
        entry.setdefault("notes", [])
        entry.setdefault("usage_example", "")
        entry.setdefault("class_name", None)
        entry.setdefault("docstring_enhanced", True)
        
        if existing_idx is not None:
            # Update existing entry
            functions[fp][existing_idx] = entry
            updated += 1
            print(f"Updated: {entry['name']} in {fp}")
        else:
            # Add new entry
            functions[fp].append(entry)
            added += 1
            print(f"Added: {entry['name']} in {fp}")
    
    # Update metadata
    total = sum(len(funcs) for funcs in functions.values())
    index["metadata"]["total_functions"] = total
    index["metadata"]["statistics"]["total_functions"] = total
    index["metadata"]["statistics"]["functions_by_file"] = {
        fp: len(funcs) for fp, funcs in functions.items()
    }
    index["metadata"]["last_updated"] = datetime.now().isoformat()
    
    print(f"\nSummary: {added} added, {updated} updated. Total functions: {total}")


def save_index(index: Dict[str, Any]) -> None:
    """Save index to file."""
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    print(f"Saved to {INDEX_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Add/update function index entries")
    parser.add_argument(
        "--json-entry",
        help="JSON array of function entries to add/update"
    )
    parser.add_argument(
        "--from-file",
        help="Path to JSON file containing function entries"
    )
    args = parser.parse_args()
    
    if not args.json_entry and not args.from_file:
        print("Error: Must provide --json-entry or --from-file", file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.from_file:
            with open(args.from_file, 'r', encoding='utf-8') as f:
                entries = json.load(f)
        else:
            entries = json.loads(args.json_entry)
        
        if not isinstance(entries, list):
            entries = [entries]
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {args.from_file}", file=sys.stderr)
        sys.exit(1)
    
    index = load_index()
    add_or_update(index, entries)
    save_index(index)


if __name__ == "__main__":
    main()
