#!/usr/bin/env python3
"""
Merge enhanced docstrings into main function_index.json.
"""

import json
from datetime import datetime

def main():
    # Load both indexes
    with open('function_index.json', 'r', encoding='utf-8') as f:
        original = json.load(f)

    with open('enhanced_function_index_grok.json', 'r', encoding='utf-8') as f:
        enhanced = json.load(f)

    # Merge enhanced docstrings
    updates = 0
    for file_path, functions in original['functions'].items():
        enhanced_funcs = enhanced['functions'].get(file_path, [])

        for func in functions:
            # Find matching enhanced function
            enhanced_func = next(
                (ef for ef in enhanced_funcs if ef['name'] == func['name'] and ef['line'] == func['line']),
                None
            )

            if enhanced_func and enhanced_func.get('docstring_generated'):
                func['docstring'] = enhanced_func['enhanced_docstring']
                func['docstring_enhanced'] = True
                func['docstring_source'] = 'llm_grok'
                updates += 1

    # Update metadata
    original['metadata']['last_enhanced'] = datetime.now().isoformat()
    original['metadata']['enhanced_count'] = updates
    original['metadata']['enhancement_source'] = 'Grok-4-Fast-Reasoning'

    # Save merged index
    with open('function_index.json', 'w', encoding='utf-8') as f:
        json.dump(original, f, indent=2, ensure_ascii=False)

    print(f"[OK] Merged {updates} enhanced docstrings into function_index.json")

if __name__ == "__main__":
    main()
