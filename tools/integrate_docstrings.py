#!/usr/bin/env python3
"""
Integrate enhanced docstrings back into Python source files.

Reads enhanced_function_index_grok.json and updates source files
with LLM-generated docstrings.
"""

import json
import ast
import sys
from pathlib import Path
from typing import Dict, List

def update_function_docstring(file_path: str, function_name: str, line_number: int, new_docstring: str) -> bool:
    """
    Update a function's docstring in source file.

    Args:
        file_path: Path to source file
        function_name: Name of function to update
        line_number: Line where function starts
        new_docstring: New docstring text

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find function definition
        func_line_idx = line_number - 1
        if func_line_idx >= len(lines):
            return False

        # Check if there's already a docstring
        next_line_idx = func_line_idx + 1
        indent = len(lines[func_line_idx]) - len(lines[func_line_idx].lstrip())

        # Look for existing docstring
        docstring_start = None
        docstring_end = None

        if next_line_idx < len(lines):
            next_line = lines[next_line_idx].strip()
            if next_line.startswith('"""') or next_line.startswith("'''"):
                # Has docstring
                docstring_start = next_line_idx
                quote = '"""' if next_line.startswith('"""') else "'''"

                # Find end
                if next_line.count(quote) >= 2:
                    # Single line docstring
                    docstring_end = next_line_idx
                else:
                    # Multi-line docstring
                    for i in range(next_line_idx + 1, len(lines)):
                        if quote in lines[i]:
                            docstring_end = i
                            break

        # Format new docstring
        docstring_indent = ' ' * (indent + 4)
        formatted_docstring = f'{docstring_indent}"""\n'
        for line in new_docstring.split('\n'):
            if line.strip():
                formatted_docstring += f'{docstring_indent}{line}\n'
            else:
                formatted_docstring += '\n'
        formatted_docstring += f'{docstring_indent}"""\n'

        # Replace or insert docstring
        if docstring_start is not None and docstring_end is not None:
            # Replace existing
            lines[docstring_start:docstring_end+1] = [formatted_docstring]
        else:
            # Insert new
            lines.insert(next_line_idx, formatted_docstring)

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return True

    except Exception as e:
        print(f"Error updating {function_name} in {file_path}: {e}")
        return False

def main():
    # Load enhanced index
    with open('enhanced_function_index_grok.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = 0
    updated = 0
    failed = 0

    for file_path, functions in data['functions'].items():
        for func in functions:
            if not func.get('docstring_generated'):
                continue

            total += 1
            success = update_function_docstring(
                file_path,
                func['name'],
                func['line'],
                func['enhanced_docstring']
            )

            if success:
                updated += 1
                print(f"[OK] Updated {func['name']} in {file_path}")
            else:
                failed += 1
                print(f"[FAIL] Failed {func['name']} in {file_path}")

    print(f"\n{'='*70}")
    print(f"INTEGRATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total: {total}")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {100*updated/total:.1f}%")

if __name__ == "__main__":
    main()
