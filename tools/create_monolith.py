#!/usr/bin/env python3
"""
Create a massive monolithic file containing ALL functions from the codebase.
Just for fun! This doesn't modify any existing code files.
"""

import json
import ast
from pathlib import Path
from typing import Dict, List, Any


def extract_function_code(file_path: Path, func_info: Dict[str, Any]) -> str:
    """Extract the complete function code from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the function in the AST to get exact boundaries
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))

        # Find the function node
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_info['name'] and node.lineno == func_info['line']:
                func_node = node
                break

        if not func_node:
            return f"# ERROR: Could not find function {func_info['name']} at line {func_info['line']}\n\n"

        # Get the function code lines
        start_line = func_node.lineno - 1  # Convert to 0-based indexing
        end_line = func_node.end_lineno

        # Include any decorators
        if func_node.decorator_list:
            # Find the first decorator line
            first_decorator = min(decorator.lineno for decorator in func_node.decorator_list) - 1
            start_line = min(start_line, first_decorator)

        # Extract the lines
        func_lines = lines[start_line:end_line]

        # Join and return
        return ''.join(func_lines) + '\n\n'

    except Exception as e:
        return f"# ERROR extracting {func_info['name']} from {file_path}: {e}\n\n"


def create_monolithic_file():
    """Create the massive monolithic function file."""
    print("Loading function index...")
    with open('function_index.json', 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    print(f"Found {index_data['metadata']['total_functions']} functions in {index_data['metadata']['total_files']} files")

    # Create the monolithic file
    output_file = 'ALL_FUNCTIONS_MONOLITH.py'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#" * 80 + "\n")
        f.write("# MASSIVE MONOLITHIC FUNCTION FILE\n")
        f.write("# Contains ALL functions from the JellyRancher codebase\n")
        f.write(f"# Generated: {index_data['metadata']['generated']}\n")
        f.write(f"# Total Functions: {index_data['metadata']['total_functions']}\n")
        f.write(f"# Total Files: {index_data['metadata']['total_files']}\n")
        f.write("# Just for fun! Don't actually use this file.\n")
        f.write("#" * 80 + "\n\n")

        functions_processed = 0

        # Process each file
        for file_path_str, functions in sorted(index_data['functions'].items()):
            file_path = Path(file_path_str)

            f.write(f"# {'='*60}\n")
            f.write(f"# FUNCTIONS FROM: {file_path_str}\n")
            f.write(f"# {'='*60}\n\n")

            # Process each function in the file
            for func_info in functions:
                f.write(f"# Function: {func_info['name']}\n")
                f.write(f"# Line: {func_info['line']}\n")
                if func_info['is_method'] and func_info['class']:
                    f.write(f"# Class: {func_info['class']}\n")
                f.write(f"# File: {file_path_str}\n")
                f.write("#" + "-"*40 + "\n")

                # Extract and write the function code
                func_code = extract_function_code(file_path, func_info)
                f.write(func_code)

                functions_processed += 1
                if functions_processed % 100 == 0:
                    print(f"Processed {functions_processed}/{index_data['metadata']['total_functions']} functions...")

        print(f"\nCompleted! Created {output_file} with {functions_processed} functions")

    return output_file


if __name__ == "__main__":
    create_monolithic_file()