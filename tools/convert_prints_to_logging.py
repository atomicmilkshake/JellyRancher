#!/usr/bin/env python3
"""
Convert print() statements to logger calls throughout the codebase.

This script:
1. Scans Python files for print() statements
2. Converts them to logger.info() or logger.error() (for stderr)
3. Ensures each file has proper logger import/setup

Usage:
    python tools/convert_prints_to_logging.py --dry-run    # Preview changes
    python tools/convert_prints_to_logging.py              # Apply changes
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict


# Directories to process
SCAN_DIRS = [
    "scripts/core",
    "scripts/media", 
    "scripts/utils",
    "scripts/_common",
    "scripts/ui",
    "scripts/ai",
    "scripts/database",
]

# Files to skip (already have proper logging or are special)
SKIP_FILES = {
    "logger.py",  # The logger module itself
    "__init__.py",
    "conftest.py",
}

# Logger import line to add if missing
LOGGER_IMPORT = "import logging"
LOGGER_SETUP = "logger = logging.getLogger(__name__)"


def find_print_statements(content: str) -> List[Tuple[int, str, str]]:
    """
    Find all print() statements in file content.
    
    Returns:
        List of (line_number, original_line, replacement_line)
    """
    results = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Skip comments and strings
        if stripped.startswith('#'):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
            
        # Match print() patterns
        # Pattern 1: print(f"..." or print("...")
        match = re.match(r'^(\s*)print\s*\((.*)\)\s*$', line)
        if match:
            indent = match.group(1)
            args = match.group(2)
            
            # Determine log level based on content
            if 'file=sys.stderr' in args or 'file=__import__' in args:
                # stderr prints become logger.error
                # Remove the file= argument
                clean_args = re.sub(r',?\s*file\s*=\s*[^,)]+', '', args).strip()
                if clean_args.endswith(','):
                    clean_args = clean_args[:-1]
                replacement = f"{indent}logger.error({clean_args})"
            elif 'error' in args.lower() or 'fail' in args.lower() or 'exception' in args.lower():
                replacement = f"{indent}logger.error({args})"
            elif 'warning' in args.lower() or 'warn' in args.lower():
                replacement = f"{indent}logger.warning({args})"
            elif 'debug' in args.lower():
                replacement = f"{indent}logger.debug({args})"
            else:
                replacement = f"{indent}logger.info({args})"
            
            results.append((i, line, replacement))
    
    return results


def has_logger_import(content: str) -> bool:
    """Check if file already imports logging."""
    return bool(re.search(r'^import logging\b', content, re.MULTILINE))


def has_logger_setup(content: str) -> bool:
    """Check if file already has logger = logging.getLogger()."""
    return bool(re.search(r'^logger\s*=\s*logging\.getLogger\(', content, re.MULTILINE))


def add_logger_setup(content: str) -> str:
    """Add logger import and setup to file content."""
    lines = content.split('\n')
    new_lines = []
    
    # Find the right place to insert imports (after existing imports)
    import_section_end = 0
    in_docstring = False
    docstring_char = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track docstrings
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_char = stripped[:3]
                if stripped.count(docstring_char) == 1:
                    in_docstring = True
                continue
        else:
            if docstring_char in stripped:
                in_docstring = False
            continue
        
        # Track import section
        if stripped.startswith('import ') or stripped.startswith('from '):
            import_section_end = i + 1
        elif stripped and not stripped.startswith('#') and import_section_end > 0:
            # First non-import, non-comment line after imports
            break
    
    # Insert logger setup
    needs_import = not has_logger_import(content)
    needs_setup = not has_logger_setup(content)
    
    if needs_import or needs_setup:
        for i, line in enumerate(lines):
            new_lines.append(line)
            if i == import_section_end - 1:
                if needs_import:
                    new_lines.append(LOGGER_IMPORT)
                if needs_setup:
                    new_lines.append("")
                    new_lines.append(LOGGER_SETUP)
        
        # Handle case where import_section_end is 0
        if import_section_end == 0:
            new_lines = [LOGGER_IMPORT, "", LOGGER_SETUP, ""] + lines
        
        return '\n'.join(new_lines)
    
    return content


def process_file(filepath: Path, dry_run: bool = True) -> Dict:
    """
    Process a single file, converting print() to logger calls.
    
    Returns:
        Dict with 'prints_found', 'prints_converted', 'logger_added'
    """
    result = {
        'filepath': str(filepath),
        'prints_found': 0,
        'prints_converted': 0,
        'logger_added': False,
        'changes': []
    }
    
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        result['error'] = str(e)
        return result
    
    # Find print statements
    prints = find_print_statements(content)
    result['prints_found'] = len(prints)
    
    if not prints:
        return result
    
    # Store changes for preview
    for line_num, original, replacement in prints:
        result['changes'].append({
            'line': line_num,
            'original': original.strip(),
            'replacement': replacement.strip()
        })
    
    if dry_run:
        return result
    
    # Apply changes
    lines = content.split('\n')
    for line_num, original, replacement in reversed(prints):  # Reverse to preserve line numbers
        lines[line_num - 1] = replacement
    
    new_content = '\n'.join(lines)
    
    # Add logger setup if needed
    if not has_logger_import(new_content) or not has_logger_setup(new_content):
        new_content = add_logger_setup(new_content)
        result['logger_added'] = True
    
    # Write back
    filepath.write_text(new_content, encoding='utf-8')
    result['prints_converted'] = len(prints)
    
    return result


def main():
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    if dry_run:
        print("=" * 70)
        print("DRY RUN - No changes will be made")
        print("=" * 70)
    else:
        print("=" * 70)
        print("CONVERTING print() TO logger calls")
        print("=" * 70)
    
    project_root = Path(__file__).parent.parent
    
    total_files = 0
    total_prints = 0
    total_converted = 0
    files_with_prints = []
    
    for scan_dir in SCAN_DIRS:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue
        
        for py_file in dir_path.rglob("*.py"):
            if py_file.name in SKIP_FILES:
                continue
            
            total_files += 1
            result = process_file(py_file, dry_run=dry_run)
            
            if result.get('error'):
                print(f"  ERROR: {py_file}: {result['error']}")
                continue
            
            if result['prints_found'] > 0:
                files_with_prints.append(result)
                total_prints += result['prints_found']
                total_converted += result.get('prints_converted', 0)
                
                if verbose or dry_run:
                    print(f"\n{py_file.relative_to(project_root)}: {result['prints_found']} print() statements")
                    for change in result['changes'][:5]:  # Show first 5
                        print(f"  Line {change['line']}:")
                        print(f"    - {change['original']}")
                        print(f"    + {change['replacement']}")
                    if len(result['changes']) > 5:
                        print(f"  ... and {len(result['changes']) - 5} more")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files scanned: {total_files}")
    print(f"Files with print(): {len(files_with_prints)}")
    print(f"Total print() statements: {total_prints}")
    
    if dry_run:
        print(f"\nTo apply changes, run without --dry-run flag")
    else:
        print(f"Converted: {total_converted}")
    
    # List files with most prints
    if files_with_prints:
        print("\nTop files by print() count:")
        for result in sorted(files_with_prints, key=lambda x: x['prints_found'], reverse=True)[:10]:
            filepath = Path(result['filepath']).relative_to(project_root)
            print(f"  {result['prints_found']:3d}  {filepath}")


if __name__ == "__main__":
    main()

