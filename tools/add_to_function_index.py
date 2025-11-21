#!/usr/bin/env python3
"""
Add/update function entry to function_index.json directly—no LLM/AST.

Usage:
.venv\Scripts\python.exe tools/add_to_function_index.py --json-entry '[{"name":"func","file_path":"scripts/core/file.py","line":123,"description":"Google docstring","inputs":{"parameters":[{"name":"p","type":"str","description":"Param","required":true}]},"outputs":{"return_value":{"type":"str","description":"Result"}},"notes":[], "usage_example":"", "class_name":null,"docstring_enhanced":true}]'

Batch OK (array). Merges/updates by file/line/name. Validates basic schema. Updates metadata.

MANDATORY per master-prompt II.2.1.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

INDEX_PATH = Path("function_index.json")

def load_index() -> Dict[str, Any]:
    if INDEX_PATH.exists():
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    print("Created new index.")
    return {"metadata": {"generated": "", "source": "manual", "total_functions": 0, "statistics": {"total_functions": 0, "functions_by_file": {}}}, "functions": {}}

def validate_entry(entry: Dict[str, Any]) -> bool:
    required = {"name", "file_path", "line", "description", "inputs", "outputs"}
    if not all(k in entry for k in required):
        print(f"Missing required: {required - set(entry)}", file=sys.stderr)
        return False
    if not isinstance(entry["inputs"]["parameters"], list):
        print("inputs.parameters must be list", file=sys.stderr)
        return False
    print("Valid entry.")
    return True

def add_or_update(index: Dict[str, Any], entries: List[Dict[str, Any]]) -> None:
    functions = index["functions"]
    updated = 0
    added = 0
    for entry in entries:
        if not validate_entry(entry):
            continue
        fp = entry["file_path"]
        if fp not in functions
