#!/usr/bin/env python3
"""
Build comprehensive function index for JellyRancher project with optional LLM docstring enhancement.

Features:
- Scans all Python files and extracts function signatures, docstrings, and metadata
- Optional: Auto-generates enhanced docstrings using Grok-Code-Fast-1 LLM
- Stores enhanced docstrings in function_index.json for TF-IDF search

Usage:
    .venv\Scripts\python.exe tools/build_function_index_enhanced.py                  # Normal build without enhancement
    .venv\Scripts\python.exe tools/build_function_index_enhanced.py --enhance        # Build with LLM docstring enhancement
    .venv\Scripts\python.exe tools/build_function_index_enhanced.py --enhance-new    # Only enhance new/modified functions

Note: Always use .venv Python for consistency.
"""

import ast
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add scripts to path for PoeClient import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ai"))

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
    """Extract function information from Python files with optional LLM enhancement."""

    def __init__(self, enhance_docstrings=False, enhance_new_only=False):
        self.functions = {}
        self.total_files = 0
        self.total_functions = 0
        self.enhance_docstrings = enhance_docstrings
        self.enhance_new_only = enhance_new_only
        self.poe_client = None

        # Load existing index if enhancing new only
        self.existing_index = {}
        if enhance_new_only and Path('function_index.json').exists():
            with open('function_index.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.existing_index = data.get('functions', {})

    def _initialize_poe_client(self):
        """Lazy initialization of Poe client for LLM docstring generation."""
        if self.poe_client is None and self.enhance_docstrings:
            try:
                from ravenmaven_client import PoeClient
                self.poe_client = PoeClient()
                logger.info("[OK] Poe client initialized for docstring enhancement")
            except Exception as e:
                logger.error(f"[ERROR] Failed to initialize Poe client: {e}")
                logger.warning("[WARNING] Continuing without docstring enhancement")
                self.enhance_docstrings = False

    def _needs_enhancement(self, func_info: Dict[str, Any], file_path: str) -> bool:
        """Determine if a function needs docstring enhancement."""
        docstring = func_info.get('docstring', '')

        # Check if already enhanced
        if func_info.get('docstring_enhanced'):
            return False

        # Check if it's a new/modified function (for enhance_new_only mode)
        if self.enhance_new_only:
            existing_funcs = self.existing_index.get(file_path, [])
            existing_func = next(
                (f for f in existing_funcs if f['name'] == func_info['name'] and f['line'] == func_info['line']),
                None
            )
            if existing_func and existing_func.get('docstring_enhanced'):
                # Already enhanced, copy over the enhanced docstring
                func_info['docstring'] = existing_func['docstring']
                func_info['docstring_enhanced'] = True
                func_info['docstring_source'] = existing_func.get('docstring_source', 'llm')
                return False

        # Needs enhancement if docstring is missing or minimal
        if not docstring or docstring == "No documentation available":
            return True
        if len(docstring.strip()) < 20:  # Very short docstring
            return True
        if not any(keyword in docstring.lower() for keyword in ['args:', 'returns:', 'raises:', 'parameters:']):
            # Doesn't have structured documentation
            return True

        return False

    def _extract_function_code(self, file_path: Path, function_name: str, line_number: int) -> Optional[str]:
        """Extract complete function code from source file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            # Find the function node
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name and node.lineno == line_number:
                    return ast.unparse(node)

            return None

        except Exception as e:
            logger.error(f"Failed to extract {function_name} from {file_path}: {e}")
            return None

    def _generate_enhanced_docstring(self, func_info: Dict[str, Any], function_code: str) -> Optional[str]:
        """Generate enhanced docstring using LLM with JSON schema format."""
        if not self.poe_client:
            return None

        # Build input using function_analysis_schema.json format
        function_input = {
            "function_name": func_info['name'],
            "file_path": func_info['file'],
            "line_number": func_info['line'],
            "function_code": function_code,
            "existing_docstring": func_info.get('docstring', ''),
            "module_context": func_info['file'].replace('/', '.').replace('\\', '.').replace('.py', '')
        }

        prompt = f"""You are a Python documentation expert. Analyze this function and generate a comprehensive Google-style docstring.

INPUT (JSON format):
{json.dumps([function_input], indent=2)}

Generate a detailed analysis following this structure:
1. what_it_does: Explain WHY the function exists and WHAT problem it solves (2-4 paragraphs)
2. how_it_works: Explain HOW it works - algorithm, data flow, implementation details (2-4 paragraphs)  
3. inputs: All parameters with types, descriptions, constraints
4. outputs: Return value, exceptions, side effects
5. enhanced_docstring: Complete Google-style docstring in standard Python format
6. usage_example: Code example showing how to use it

Return ONLY a JSON object with this structure (no markdown, no code fences):
{{
  "function_name": "{func_info['name']}",
  "enhanced_docstring": "your complete Google-style docstring here"
}}

The enhanced_docstring should include Args, Returns, Raises sections in Google style format."""

        try:
            response = self.poe_client.send_message(prompt, model="Grok-Code-Fast-1")

            if response and response.strip():
                # Parse JSON response
                try:
                    # Strip markdown code fences if present
                    cleaned = response.strip()
                    if cleaned.startswith('```'):
                        lines = cleaned.split('\n')
                        cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
                        if cleaned.startswith('json'):
                            cleaned = '\n'.join(cleaned.split('\n')[1:])
                    
                    result = json.loads(cleaned)
                    return result.get('enhanced_docstring', '').strip()
                except json.JSONDecodeError:
                    # Fallback: try to extract docstring from text
                    logger.warning(f"JSON parse failed for {func_info['name']}, using text extraction")
                    return response.strip()

        except Exception as e:
            logger.error(f"Failed to generate docstring for {func_info['name']}: {e}")

        return None

    def _enhance_function_docstrings(self, functions: List[Dict[str, Any]], file_path: Path):
        """Enhance docstrings for functions that need it."""
        if not self.enhance_docstrings:
            return

        self._initialize_poe_client()
        if not self.poe_client:
            return

        file_key = str(file_path.relative_to(Path.cwd()))
        functions_to_enhance = [f for f in functions if self._needs_enhancement(f, file_key)]

        if not functions_to_enhance:
            return

        # Use RICH progress bar for enhancement if available
        if RICH_AVAILABLE:
            console = Console()
            console.print(f"[bold blue]✨ Enhancing {len(functions_to_enhance)} functions in {Path(file_key).name}[/bold blue]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=2,
            ) as progress:
                enhance_task = progress.add_task("🤖 Generating docstrings...", total=len(functions_to_enhance))

                for func_info in functions_to_enhance:
                    progress.update(enhance_task, description=f"🤖 Enhancing: {func_info['name']}")
                    function_code = self._extract_function_code(file_path, func_info['name'], func_info['line'])

                    if not function_code:
                        progress.update(enhance_task, description=f"⚠️  Skipped: {func_info['name']} (code extraction failed)")
                        progress.advance(enhance_task)
                        continue

                    enhanced_docstring = self._generate_enhanced_docstring(func_info, function_code)

                    if enhanced_docstring:
                        func_info['docstring'] = enhanced_docstring
                        func_info['docstring_enhanced'] = True
                        func_info['docstring_source'] = 'llm_grok_code_fast_1'
                        progress.update(enhance_task, description=f"✅ Enhanced: {func_info['name']}")
                    else:
                        progress.update(enhance_task, description=f"❌ Failed: {func_info['name']}")

                    progress.advance(enhance_task)
        else:
            # Fallback to logger-based progress
            logger.info(f"[ENHANCE] {len(functions_to_enhance)} functions need enhancement in {file_key}")

            for func_info in functions_to_enhance:
                function_code = self._extract_function_code(file_path, func_info['name'], func_info['line'])

                if not function_code:
                    logger.warning(f"[SKIP] Could not extract code for {func_info['name']}")
                    continue

                logger.info(f"[ENHANCE] Generating docstring for {func_info['name']}...")
                enhanced_docstring = self._generate_enhanced_docstring(func_info, function_code)

                if enhanced_docstring:
                    func_info['docstring'] = enhanced_docstring
                    func_info['docstring_enhanced'] = True
                    func_info['docstring_source'] = 'llm_grok_code_fast_1'
                    logger.info(f"[OK] Enhanced {func_info['name']}")
                else:
                    logger.warning(f"[SKIP] Failed to enhance {func_info['name']}")

    def extract_functions_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all functions from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self.extract_function_info(node, file_path)
                    functions.append(func_info)

            # Enhance docstrings if enabled
            if self.enhance_docstrings and functions:
                self._enhance_function_docstrings(functions, file_path)

            return functions

        except Exception as e:
            logger.error(f"[ERROR] Failed to parse {file_path}: {e}")
            return []

    def extract_function_info(self, node: ast.FunctionDef, file_path: Path) -> Dict[str, Any]:
        """Extract detailed information about a function."""
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
        """Recursively scan directory for Python files."""
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
        """Build complete function index."""
        # Initialize RICH console if available
        console = Console() if RICH_AVAILABLE else None

        if console:
            # Create beautiful header
            title = "🔍 Building JellyRancher Function Index"
            if self.enhance_docstrings:
                mode = "ENHANCED (New Functions Only)" if self.enhance_new_only else "ENHANCED (All Functions)"
                title += f"\n✨ Mode: {mode}"

            console.print(Panel.fit(title, border_style="blue", padding=(1, 2)))
        else:
            # Fallback to basic output
            print("=" * 80)
            print("Building JellyRancher Function Index")
            if self.enhance_docstrings:
                mode = "ENHANCED (New Functions Only)" if self.enhance_new_only else "ENHANCED (All Functions)"
                print(f"Mode: {mode}")
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
        max_errors = 50

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
                        enhanced_count = sum(1 for f in functions if f.get('docstring_enhanced'))

                        status_msg = f"✅ {file_path.relative_to(project_root).name}: {len(functions)} functions"
                        if enhanced_count > 0:
                            status_msg += f" ({enhanced_count} enhanced)"

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
                    enhanced_count = sum(1 for f in functions if f.get('docstring_enhanced'))

                    status_msg = f"  -> Found {len(functions)} functions"
                    if enhanced_count > 0:
                        status_msg += f" ({enhanced_count} enhanced)"

                    print(status_msg)
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


def save_function_index(functions: Dict[str, List[Dict]], output_file: str, enhanced: bool = False):
    """Save function index to JSON file."""
    total_enhanced = sum(
        1 for funcs in functions.values()
        for f in funcs if f.get('docstring_enhanced')
    )

    index_data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_files": len(functions),
            "total_functions": sum(len(funcs) for funcs in functions.values()),
            "enhanced_count": total_enhanced if enhanced else 0,
            "enhancement_source": "Grok-Code-Fast-1" if enhanced and total_enhanced > 0 else None
        },
        "functions": functions
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Function index saved to {output_file}")
    if total_enhanced > 0:
        print(f"[OK] {total_enhanced} functions have LLM-enhanced docstrings")
    return index_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build function index with optional LLM docstring enhancement')
    parser.add_argument('--enhance', action='store_true',
                       help='Enable LLM docstring enhancement for all functions')
    parser.add_argument('--enhance-new', action='store_true',
                       help='Enable LLM docstring enhancement for new/modified functions only')

    args = parser.parse_args()

    # Build index
    enhance_mode = args.enhance or args.enhance_new
    indexer = FunctionIndexer(
        enhance_docstrings=enhance_mode,
        enhance_new_only=args.enhance_new
    )
    success = indexer.build_index()

    if not success:
        logger.error("[ABORTED] Function indexing failed due to too many errors")
        print("\n❌ Indexing aborted due to excessive errors. Check the log file for details.")
        sys.exit(1)

    functions = indexer.functions

    # Save to JSON
    index_data = save_function_index(functions, "function_index.json", enhanced=enhance_mode)

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

        if enhance_mode:
            completion_lines.append(f"[cyan]✨ Enhanced:[/cyan] {index_data['metadata']['enhanced_count']} functions with LLM docstrings")

        console.print(Panel.fit("\n".join(completion_lines), border_style="green", padding=(1, 2)))
    else:
        print("\n" + "=" * 80)
        print("Function Index Complete!")
        print("=" * 80)
        print(f"JSON Index: function_index.json")
        if enhance_mode:
            print(f"Enhanced: {index_data['metadata']['enhanced_count']} functions with LLM docstrings")
        print(f"Functions: {index_data['metadata']['total_functions']}")
        print(f"Files: {index_data['metadata']['total_files']}")
        print("=" * 80)
