#!/usr/bin/env python3
"""
Flatten Python dependencies for jelly_rancher_studio.py
Copies all Python dependencies to a flat directory structure.
"""

import ast
import shutil
from pathlib import Path
from typing import Set, List

def get_script_imports(filepath: Path) -> Set[str]:
    """Extract all 'scripts.*' imports from a Python file."""
    imports = set()
    try:
        tree = ast.parse(filepath.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('scripts'):
                    imports.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('scripts'):
                        imports.add(alias.name)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return imports

def import_to_path(import_name: str) -> Path:
    """Convert import name to file path."""
    # scripts.core.roundup_manager -> scripts/core/roundup_manager.py
    parts = import_name.split('.')
    if len(parts) > 1:
        return Path('/'.join(parts[:-1])) / f"{parts[-1]}.py"
    return Path(f"{import_name}.py")

def collect_all_dependencies(start_file: Path, root: Path) -> Set[Path]:
    """Recursively collect all Python dependencies."""
    seen = set()
    to_process = {start_file}
    all_files = set()
    
    while to_process:
        current = to_process.pop()
        if current in seen:
            continue
        seen.add(current)
        
        if not current.exists():
            continue
            
        all_files.add(current)
        
        # Get imports from this file
        imports = get_script_imports(current)
        for imp in imports:
            dep_path = root / import_to_path(imp)
            if dep_path.exists() and dep_path not in seen:
                to_process.add(dep_path)
    
    return all_files

def flatten_name(filepath: Path, root: Path) -> str:
    """Convert path to flattened name."""
    # scripts/core/roundup_manager.py -> scripts_core_roundup_manager.py
    rel = filepath.relative_to(root)
    parts = list(rel.parts)
    if parts[-1].endswith('.py'):
        parts[-1] = parts[-1][:-3]  # Remove .py
    return '_'.join(parts) + '.py'

def main():
    root = Path(__file__).parent.parent
    main_script = root / "jelly_rancher_studio.py"
    output_dir = Path("V:/bullshit")
    
    print(f"Collecting dependencies for {main_script}...")
    all_files = collect_all_dependencies(main_script, root)
    
    print(f"Found {len(all_files)} Python files")
    print(f"Copying to {output_dir}...")
    
    output_dir.mkdir(exist_ok=True)
    
    for filepath in sorted(all_files):
        flat_name = flatten_name(filepath, root)
        dest = output_dir / flat_name
        print(f"  {filepath.name} -> {flat_name}")
        shutil.copy2(filepath, dest)
    
    print(f"\nDone! Copied {len(all_files)} files to {output_dir}")

if __name__ == "__main__":
    main()

