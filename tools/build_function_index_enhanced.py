#!/usr/bin/env python3
"""
Build comprehensive function index for JellyRancher project with optional LLM docstring enhancement.

Features:
- Scans all Python files and extracts function signatures, docstrings, and metadata
- Optional: Auto-generates enhanced docstrings using Grok-4.1-Fast-Reasoning LLM
- Stores enhanced docstrings in function_index.json for TF-IDF search

Usage:
    .venv\\Scripts\\python.exe tools/build_function_index_enhanced.py                  # Normal build without enhancement
    .venv\\Scripts\\python.exe tools/build_function_index_enhanced.py --enhance        # Build with LLM docstring enhancement
    .venv\\Scripts\\python.exe tools/build_function_index_enhanced.py --enhance-new    # Only enhance new/modified functions
    .venv\\Scripts\\python.exe tools/build_function_index_enhanced.py --resume         # Resume enhancement from existing index

Note: Always use .venv Python for consistency.
"""

import ast
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
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

        # Load existing enhanced functions for resume capability
        self.existing_enhanced_functions = self._load_existing_enhanced_functions()

    def _initialize_poe_client(self):
        """Lazy initialization of Poe client for LLM docstring generation."""
        if self.poe_client is None and self.enhance_docstrings:
            try:
                from ravenmaven_client import PoeClient
                self.poe_client = PoeClient(default_model="Grok-4.1-Fast-Reasoning")
                logger.info("[OK] Poe client initialized for docstring enhancement")
            except Exception as e:
                logger.error(f"[ERROR] Failed to initialize Poe client: {e}")
                raise RuntimeError(f"Poe client initialization failed: {e}")

    def _load_existing_enhanced_functions(self):
        """Load existing enhanced functions from data/function_index.json"""
        enhanced_file = Path('data') / 'function_index.json'
        if enhanced_file.exists():
            try:
                with open(enhanced_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    enhanced_functions = []
                    functions_data = data.get('functions', {})
                    for file_path, funcs in functions_data.items():
                        for func in funcs:
                            if func.get('docstring_enhanced'):
                                enhanced_functions.append((file_path, func['name']))
                    # Convert to set of (file_path, function_name) tuples for fast lookup
                    return set(enhanced_functions)
            except Exception as e:
                logger.warning(f"Could not load existing enhanced functions: {e}")
        return set()

    def _needs_enhancement(self, func_info: Dict[str, Any], file_path: str) -> bool:
        """Determine if a function needs docstring enhancement."""
        # Check if already enhanced in previous runs
        func_key = (file_path, func_info['name'])
        if func_key in self.existing_enhanced_functions:
            return False

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

    def _generate_enhanced_docstrings_batch(self, func_batch: List[Tuple[Dict[str, Any], str]]) -> Dict[str, str]:
        """Generate enhanced docstrings for a batch of functions using LLM."""
        if not self.poe_client:
            raise RuntimeError("Poe client not initialized")

        # Build input array for all functions in batch
        functions_input = []
        for func_info, function_code in func_batch:
            function_input = {
                "function_name": func_info['name'],
                "file_path": func_info['file'],
                "line_number": func_info['line'],
                "function_code": function_code,
                "existing_docstring": func_info.get('docstring', ''),
                "module_context": func_info['file'].replace('/', '.').replace('\\', '.').replace('.py', '')
            }
            functions_input.append(function_input)

        prompt = f"""You are a Python documentation expert. Analyze these functions and generate comprehensive Google-style docstrings for each.

INPUT (JSON format):
{json.dumps(functions_input, indent=2)}

For EACH function, generate a detailed analysis and return enhanced_docstring in Google style format with Args, Returns, Raises sections.

Return ONLY a JSON array of objects with this structure (no markdown, no code fences):
[
  {{
    "function_name": "function1_name",
    "enhanced_docstring": "complete Google-style docstring for function1"
  }},
  {{
    "function_name": "function2_name", 
    "enhanced_docstring": "complete Google-style docstring for function2"
  }}
]

Each enhanced_docstring should be comprehensive with proper Args, Returns, Raises sections."""

        try:
            response = self.poe_client.send_message(prompt, model="Grok-4.1-Fast-Reasoning")

            if not response or not response.strip():
                raise ValueError(f"Empty response from LLM for batch of {len(func_batch)} functions")

            # Parse JSON response
            try:
                # Strip markdown code fences if present
                cleaned = response.strip()
                if cleaned.startswith('```'):
                    lines = cleaned.split('\n')
                    cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
                    if cleaned.startswith('json'):
                        cleaned = '\n'.join(cleaned.split('\n')[1:])
                
                results = json.loads(cleaned)
                if not isinstance(results, list):
                    raise ValueError(f"Expected JSON array, got {type(results)}")
                
                # Convert to dict keyed by function name
                enhanced_docstrings = {}
                for result in results:
                    if isinstance(result, dict) and 'function_name' in result and 'enhanced_docstring' in result:
                        func_name = result['function_name']
                        docstring = result['enhanced_docstring'].strip()
                        if docstring:
                            enhanced_docstrings[func_name] = docstring
                
                return enhanced_docstrings
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON response from LLM for batch: {e}")
                return {}
                
        except Exception as e:
            logger.warning(f"[LLM-BATCH-ERROR] Batch enhancement failed: {e}")
            return {}

    def _save_progress(self):
        """Save current progress to function_index.json for resume capability."""
        try:
            index_data = save_function_index(self.functions, "function_index.json", enhanced=self.enhance_docstrings)
            logger.info(f"[PROGRESS] Saved {index_data['metadata']['total_functions']} functions to function_index.json")
        except Exception as e:
            logger.warning(f"[SAVE-ERROR] Failed to save progress: {e}")

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
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=1,
            ) as progress:
                enhance_task = progress.add_task("🤖 Generating enhanced docstrings...", total=len(functions_to_enhance))

                successful_enhancements = 0
                for func_info in functions_to_enhance:
                    function_code = self._extract_function_code(file_path, func_info['name'], func_info['line'])

                    if not function_code:
                        progress.advance(enhance_task)
                        continue

                    enhanced_docstring = self._generate_enhanced_docstring(func_info, function_code)

                    if enhanced_docstring:
                        func_info['docstring'] = enhanced_docstring
                        func_info['docstring_enhanced'] = True
                        func_info['docstring_source'] = 'llm_grok_code_fast_1'
                        successful_enhancements += 1
                        
                        # Show preview only occasionally
                        if successful_enhancements % 25 == 0:  # Every 25 successful enhancements
                            preview = enhanced_docstring.split('\n')[0][:50] + "..." if len(enhanced_docstring.split('\n')[0]) > 50 else enhanced_docstring.split('\n')[0]
                            progress.update(enhance_task, description=f"✅ {successful_enhancements}/{len(functions_to_enhance)} enhanced - Latest: {preview}")

                    progress.advance(enhance_task)
        else:
            # Fallback to logger-based progress
            logger.info(f"[ENHANCE] {len(functions_to_enhance)} functions need enhancement in {file_key}")

            successful_enhancements = 0
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
                    successful_enhancements += 1
                    if successful_enhancements % 25 == 0:
                        logger.info(f"[OK] Enhanced {successful_enhancements}/{len(functions_to_enhance)} functions")
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

            return functions

        except Exception as e:
            logger.debug(f"[DEBUG] Failed to parse {file_path}: {e}")
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
        try:
            console = Console() if RICH_AVAILABLE else None
        except Exception:
            console = None

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

        # First pass: count total functions needing enhancement
        total_to_enhance = 0
        if self.enhance_docstrings:
            # Initialize Poe client for LLM enhancement
            self._initialize_poe_client()
            
            console.print("[yellow]🔢 Counting functions needing enhancement...[/yellow]") if console else print("Counting functions needing enhancement...")
            for file_path in python_files:
                try:
                    functions = self.extract_functions_from_file(file_path)
                    file_key = str(file_path.relative_to(project_root))
                    functions_to_enhance = [f for f in functions if self._needs_enhancement(f, file_key)]
                    total_to_enhance += len(functions_to_enhance)
                except:
                    pass
            console.print(f"[green]📊 Found {total_to_enhance} functions needing LLM enhancement[/green]\n") if console else print(f"Found {total_to_enhance} functions needing LLM enhancement\n")

        # Set up progress bar for file processing
        error_count = 0
        max_errors = 50

        if console:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=1,
            ) as progress:
                file_task = progress.add_task("🔍 Analyzing files...", total=len(python_files))
                enhance_task = progress.add_task("🤖 Enhancing docstrings...", total=total_to_enhance) if total_to_enhance > 0 else None

                enhanced_count = 0
                for file_path in sorted(python_files):
                    # Update file progress description occasionally
                    if self.total_files % 10 == 0 or self.total_files == 0:
                        progress.update(file_task, description=f"🔍 Analyzing files... ({self.total_files+1}/{len(python_files)})")

                    functions = self.extract_functions_from_file(file_path)

                    if functions:
                        file_key = str(file_path.relative_to(project_root))
                        self.functions[file_key] = functions
                        self.total_functions += len(functions)

                        # Handle enhancement for this file
                        if self.enhance_docstrings and enhance_task is not None:
                            functions_to_enhance = [f for f in functions if self._needs_enhancement(f, file_key)]
                            if functions_to_enhance:
                                progress.update(file_task, description=f"🔍 Analyzing: {file_path.relative_to(project_root).name} ({len(functions_to_enhance)} to enhance)")

                                # Process functions in batches of 6
                                batch_size = 6
                                for i in range(0, len(functions_to_enhance), batch_size):
                                    batch = functions_to_enhance[i:i + batch_size]
                                    
                                    # Extract code for all functions in batch
                                    batch_data = []
                                    for func_info in batch:
                                        function_code = self._extract_function_code(file_path, func_info['name'], func_info['line'])
                                        if function_code:
                                            batch_data.append((func_info, function_code))
                                    
                                    if batch_data:
                                        # Send batch to LLM
                                        enhanced_docstrings = self._generate_enhanced_docstrings_batch(batch_data)
                                        
                                        # Apply enhanced docstrings
                                        for func_info, _ in batch_data:
                                            func_name = func_info['name']
                                            if func_name in enhanced_docstrings:
                                                func_info['docstring'] = enhanced_docstrings[func_name]
                                                func_info['docstring_enhanced'] = True
                                                func_info['docstring_source'] = 'llm_grok_code_fast_1'
                                                enhanced_count += 1

                                                # Save progress every 10 successful enhancements
                                                if enhanced_count % 10 == 0:
                                                    self._save_progress()

                                                # Show preview very occasionally
                                                if enhanced_count % 50 == 0:
                                                    preview = enhanced_docstrings[func_name].split('\n')[0][:40] + "..." if len(enhanced_docstrings[func_name].split('\n')[0]) > 40 else enhanced_docstrings[func_name].split('\n')[0]
                                                    progress.update(enhance_task, description=f"✅ Enhanced {enhanced_count}/{total_to_enhance}: {preview}")
                                            else:
                                                logger.warning(f"[SKIP] No enhanced docstring returned for {func_name}")
                                    else:
                                        logger.warning(f"[SKIP] Could not extract code for any functions in batch")
                                    
                                    # Advance progress for each function in batch
                                    for _ in batch:
                                        progress.advance(enhance_task)

                        # Update file status occasionally
                        if self.total_files % 15 == 0:
                            status_parts = [f"✅ {self.total_files+1}/{len(python_files)} files"]
                            if enhanced_count > 0:
                                status_parts.append(f"{enhanced_count} enhanced")
                            progress.update(file_task, description=" | ".join(status_parts))
                    else:
                        error_count += 1
                        if error_count % 5 == 0:
                            progress.update(file_task, description=f"❌ {error_count} files failed ({self.total_files+1}/{len(python_files)})")

                    if error_count >= max_errors:
                        progress.update(file_task, description=f"🛑 STOPPED: Too many parsing errors ({error_count}/{max_errors})")
                        break

                    self.total_files += 1
                    progress.advance(file_task)
        else:
            # Fallback to basic progress
            enhanced_count = 0
            for file_path in sorted(python_files):
                print(f"Analyzing: {file_path.relative_to(project_root)}")

                functions = self.extract_functions_from_file(file_path)

                if functions:
                    file_key = str(file_path.relative_to(project_root))
                    self.functions[file_key] = functions
                    self.total_functions += len(functions)

                    # Handle enhancement
                    if self.enhance_docstrings:
                        functions_to_enhance = [f for f in functions if self._needs_enhancement(f, file_key)]
                        
                        # Process functions in batches of 6
                        batch_size = 6
                        for i in range(0, len(functions_to_enhance), batch_size):
                            batch = functions_to_enhance[i:i + batch_size]
                            
                            # Extract code for all functions in batch
                            batch_data = []
                            for func_info in batch:
                                function_code = self._extract_function_code(file_path, func_info['name'], func_info['line'])
                                if function_code:
                                    batch_data.append((func_info, function_code))
                            
                            if batch_data:
                                # Send batch to LLM
                                enhanced_docstrings = self._generate_enhanced_docstrings_batch(batch_data)
                                
                                # Apply enhanced docstrings
                                for func_info, _ in batch_data:
                                    func_name = func_info['name']
                                    if func_name in enhanced_docstrings:
                                        func_info['docstring'] = enhanced_docstrings[func_name]
                                        func_info['docstring_enhanced'] = True
                                        func_info['docstring_source'] = 'llm_grok_code_fast_1'
                                        enhanced_count += 1
                                        if enhanced_count % 25 == 0:
                                            print(f"Enhanced {enhanced_count} functions...")
                                    else:
                                        logger.warning(f"[SKIP] No enhanced docstring returned for {func_name}")
                            else:
                                logger.warning(f"[SKIP] Could not extract code for any functions in batch")

                    status_msg = f"  -> Found {len(functions)} functions"
                    if enhanced_count > 0:
                        status_msg += f" ({enhanced_count} enhanced so far)"
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
    """Save function index to JSON file in the format expected by query tool."""
    
    # Transform to the format expected by query_function_index_semantic.py
    transformed_functions = {}
    
    for file_path, funcs in functions.items():
        transformed_funcs = []
        for func in funcs:
            # Transform function info to expected format
            transformed_func = {
                'name': func['name'],
                'file_path': file_path,
                'line': func['line'],
                'description': func.get('docstring', 'No documentation available'),
                'implementation': '',  # Not extracted in current format
                'inputs': {
                    'parameters': [
                        {
                            'name': param['name'],
                            'type': param['type'],
                            'description': f"Parameter of type {param['type']}",
                            'required': param['name'] != 'self'  # Simple heuristic
                        }
                        for param in func.get('parameters', [])
                    ]
                },
                'outputs': {
                    'return_value': {
                        'type': func.get('return_type', 'Any'),
                        'description': f"Returns {func.get('return_type', 'Any')}"
                    }
                },
                'notes': [],
                'usage_example': '',
                'class_name': func.get('class')
            }
            
            # Add enhancement metadata
            if func.get('docstring_enhanced'):
                transformed_func['docstring_enhanced'] = True
                transformed_func['docstring_source'] = func.get('docstring_source', 'llm')
            
            transformed_funcs.append(transformed_func)
        
        transformed_functions[file_path] = transformed_funcs
    
    # Calculate statistics
    total_functions = sum(len(funcs) for funcs in transformed_functions.values())
    functions_with_description = sum(
        1 for funcs in transformed_functions.values()
        for f in funcs if f.get('description') and f['description'] != 'No documentation available'
    )
    
    functions_by_file = {file_path: len(funcs) for file_path, funcs in transformed_functions.items()}
    
    index_data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "source": "AST extraction with LLM enhancement" if enhanced else "AST extraction",
            "total_functions": total_functions,
            "statistics": {
                "total_functions": total_functions,
                "functions_with_description": functions_with_description,
                "functions_with_implementation": 0,  # Not tracked in current format
                "functions_by_file": functions_by_file
            }
        },
        "functions": transformed_functions
    }

    # Ensure data directory exists
    Path(output_file).parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Function index saved to {output_file}")
    if enhanced:
        enhanced_count = sum(
            1 for funcs in transformed_functions.values()
            for f in funcs if f.get('docstring_enhanced')
        )
        print(f"[OK] {enhanced_count} functions have LLM-enhanced docstrings")
    return index_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build function index with optional LLM docstring enhancement')
    parser.add_argument('--enhance', action='store_true',
                       help='Enable LLM docstring enhancement for all functions')
    parser.add_argument('--enhance-new', action='store_true',
                       help='Enable LLM docstring enhancement for new/modified functions only')
    parser.add_argument('--resume', action='store_true',
                       help='Resume enhancement from existing function_index.json (skip already enhanced functions)')

    args = parser.parse_args()

    # Build index
    enhance_mode = args.enhance or args.enhance_new or args.resume
    indexer = FunctionIndexer(
        enhance_docstrings=enhance_mode,
        enhance_new_only=args.enhance_new  # Only set enhance_new_only for --enhance-new, not --resume
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
            f"[cyan]📁 Files:[/cyan] {len(index_data['functions'])} files"
        ]

        if enhance_mode:
            enhanced_count = sum(
                1 for funcs in index_data['functions'].values()
                for f in funcs if f.get('docstring_enhanced')
            )
            completion_lines.append(f"[cyan]✨ Enhanced:[/cyan] {enhanced_count} functions with LLM docstrings")

        console.print(Panel.fit("\n".join(completion_lines), border_style="green", padding=(1, 2)))
    else:
        print("\n" + "=" * 80)
        print("Function Index Complete!")
        print("=" * 80)
        print(f"JSON Index: function_index.json")
        if enhance_mode:
            enhanced_count = sum(
                1 for funcs in index_data['functions'].values()
                for f in funcs if f.get('docstring_enhanced')
            )
            print(f"Enhanced: {enhanced_count} functions with LLM docstrings")
        print(f"Functions: {index_data['metadata']['total_functions']}")
        print(f"Files: {len(index_data['functions'])}")
        print("=" * 80)
