#!/usr/bin/env python3
"""
Build comprehensive function index for JellyRancher project.

Features:
- Scans all Python files and extracts function signatures, docstrings, and metadata
- Stores in function_index.json for TF-IDF semantic search
- Simple, dependency-free, fast

Usage:
    .venv\Scripts\python.exe tools/build_function_index_simple.py

Note: Always use .venv Python for consistency.
"""

import ast
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# RICH imports for progress indication
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("[WARNING] RICH not available - using basic progress indication")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build_function_index.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FunctionIndexer:
    """Extract function information from Python files."""

    def __init__(self):
        self.functions = {}
        self.total_files = 0
        self.total_functions = 0

    def extract_functions_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all functions from a Python file.
        
        Args:
            file_path: Path to Python file to analyze
            
        Returns:
            List of function metadata dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self.extract_function_info(node, file_path)
                    functions.append(func_info)

            return functions

        except Exception as e:
            logger.error(f"[ERROR] Failed to parse {file_path}: {e}")
            return []

    def extract_function_info(self, node: ast.FunctionDef, file_path: Path) -> Dict[str, Any]:
        """Extract detailed information about a function.
        
        Args:
            node: AST FunctionDef node
            file_path: Source file path
            
        Returns:
            Function metadata dictionary
        """
        # Get function name
        func_name = node.name

        # Get docstring
        docstring = ast.get_docstring(node) or "No documentation available"

        # Get parameters
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            # Try to get type annotation
            arg_type = "Any"
            if arg.annotation:
                arg_type = ast.unparse(arg.annotation)
            args.append({"name": arg_name, "type": arg_type})

        # Get return type
        return_type = "Any"
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Determine if it's a class method
        is_method = False
        parent_class = None
        for parent_node in ast.walk(ast.parse(open(file_path, 'r', encoding='utf-8').read())):
            if isinstance(parent_node, ast.ClassDef):
                for item in parent_node.body:
                    if item == node or (isinstance(item, ast.FunctionDef) and item.name == func_name):
                        is_method = True
                        parent_class = parent_node.name
                        break

        return {
            "name": func_name,
            "file": str(file_path.relative_to(Path.cwd())),
            "line": node.lineno,
            "docstring": docstring,
            "parameters": args,
            "return_type": return_type,
            "is_method": is_method,
            "class": parent_class if is_method else None
        }

    def scan_directory(self, directory: Path, exclude_dirs=None):
        """Recursively scan directory for Python files.
        
        Args:
            directory: Root directory to scan
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            List of Python file paths
        """
        if exclude_dirs is None:
            exclude_dirs = {'.venv', '__pycache__', 'archive', '.git', 'chroma_db', 'backups', 
                          'Jellyfin Organizer', 'RavenMaven', 'code_cop'}

        python_files = []
        for item in directory.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in exclude_dirs):
                continue
            # Skip monolith files
            if 'MONOLITH' in item.name.upper():
                continue
            python_files.append(item)

        return python_files

    def build_index(self):
        """Build complete function index.
        
        Returns:
            True if successful, False if too many errors
        """
        # Initialize RICH console if available
        console = Console() if RICH_AVAILABLE else None

        if console:
            console.print(Panel.fit(
                "🔍 Building JellyRancher Function Index", 
                border_style="blue", 
                padding=(1, 2)
            ))
        else:
            print("=" * 80)
            print("Building JellyRancher Function Index")
            print("=" * 80)
            print()

        # Scan for Python files
        project_root = Path.cwd()
        python_files = self.scan_directory(project_root)

        if console:
            console.print(f"[bold green]📁 Found {len(python_files)} Python files to analyze[/bold green]\n")
        else:
            print(f"Found {len(python_files)} Python files to analyze")
            print()

        # Set up progress bar for file processing
        error_count = 0
        max_errors = 50  # Allow parsing errors for large codebase

        if console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=10,
            ) as progress:
                file_task = progress.add_task("🔍 Analyzing files...", total=len(python_files))

                for file_path in sorted(python_files):
                    progress.update(file_task, description=f"🔍 Analyzing: {file_path.relative_to(project_root).name}")

                    functions = self.extract_functions_from_file(file_path)

                    if functions:
                        file_key = str(file_path.relative_to(project_root))
                        self.functions[file_key] = functions
                        self.total_functions += len(functions)

                        status_msg = f"✅ {file_path.relative_to(project_root).name}: {len(functions)} functions"
                        progress.update(file_task, description=status_msg)
                    else:
                        error_count += 1
                        progress.update(file_task, description=f"❌ {file_path.relative_to(project_root).name}: Parse failed ({error_count}/{max_errors})")

                    if error_count >= max_errors:
                        progress.update(file_task, description=f"🛑 STOPPED: Too many parsing errors ({error_count}/{max_errors})")
                        break

                    self.total_files += 1
                    progress.advance(file_task)
        else:
            # Fallback to basic progress
            for file_path in sorted(python_files):
                print(f"Analyzing: {file_path.relative_to(project_root)}")

                functions = self.extract_functions_from_file(file_path)

                if functions:
                    file_key = str(file_path.relative_to(project_root))
                    self.functions[file_key] = functions
                    self.total_functions += len(functions)
                    print(f"  -> Found {len(functions)} functions")
                else:
                    error_count += 1
                    print(f"  -> Parse failed ({error_count}/{max_errors})")

                if error_count >= max_errors:
                    print(f"STOPPED: Too many parsing errors ({error_count}/{max_errors})")
                    break

                self.total_files += 1

        # Check if we stopped due to errors
        if error_count >= max_errors:
            logger.error(f"[STOPPED] Processing halted due to {error_count} parsing errors")
            return False

        return True


def save_function_index(functions: Dict[str, List[Dict]], output_file: str):
    """Save function index to JSON file.
    
    Args:
        functions: Dictionary mapping file paths to function lists
        output_file: Path to save JSON file
        
    Returns:
        Index metadata dictionary
    """
    index_data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_files": len(functions),
            "total_functions": sum(len(funcs) for funcs in functions.values())
        },
        "functions": functions
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Function index saved to {output_file}")
    return index_data


if __name__ == "__main__":
    # Build index
    indexer = FunctionIndexer()
    success = indexer.build_index()

    if not success:
        logger.error("[ABORTED] Function indexing failed due to too many errors")
        print("\n❌ Indexing aborted due to excessive errors. Check the log file for details.")
        sys.exit(1)

    functions = indexer.functions

    # Save to JSON
    index_data = save_function_index(functions, "function_index.json")

    # Print completion
    if RICH_AVAILABLE:
        console = Console()
        completion_lines = [
            "[bold green]🎉 Function Index Complete![/bold green]",
            "",
            f"[cyan]📄 JSON Index:[/cyan] function_index.json",
            f"[cyan]📊 Functions:[/cyan] {index_data['metadata']['total_functions']} functions",
            f"[cyan]📁 Files:[/cyan] {index_data['metadata']['total_files']} files"
        ]
        console.print(Panel.fit("\n".join(completion_lines), border_style="green", padding=(1, 2)))
    else:
        print("\n" + "=" * 80)
        print("Function Index Complete!")
        print("=" * 80)
        print(f"JSON Index: function_index.json")
        print(f"Functions: {index_data['metadata']['total_functions']}")
        print(f"Files: {index_data['metadata']['total_files']}")
        print("=" * 80)
