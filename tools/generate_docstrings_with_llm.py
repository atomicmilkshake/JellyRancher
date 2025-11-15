#!/usr/bin/env python3
"""
Generate Detailed Docstrings for All Functions Using LLM

Extracts function code from source files, chunks them into batches,
and submits to an LLM for detailed docstring generation.
"""

import ast
import sys
import json
import logging
import time
import warnings
import threading
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
# ThreadPoolExecutor removed - API calls are always sequential for Poe.com
from tenacity import retry, stop_after_attempt, wait_exponential

# Suppress SyntaxWarnings from invalid escape sequences in source files
warnings.filterwarnings('ignore', category=SyntaxWarning, module='ast')

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "ai"))

from ravenmaven_client import PoeClient

# RICH imports for beautiful progress indication
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class FunctionExtractor:
    """Extract full function code from source files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_function_code(self, file_path: str, function_name: str, line_number: int) -> Optional[str]:
        """
        Extract complete function code from source file.

        Args:
            file_path: Path to source file
            function_name: Name of function to extract
            line_number: Line number where function starts

        Returns:
            Complete function code as string, or None if extraction fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=SyntaxWarning)
                tree = ast.parse(content, filename=file_path)

            # Find the function node
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name and node.lineno == line_number:
                    # Extract the function code using ast.unparse
                    return ast.unparse(node)

            # Fallback: extract by line number if AST walk fails
            lines = content.split('\n')
            if line_number > 0 and line_number <= len(lines):
                # Find function end by indentation
                start_idx = line_number - 1
                indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

                end_idx = start_idx + 1
                while end_idx < len(lines):
                    line = lines[end_idx]
                    # Empty lines or comments are OK
                    if line.strip() == '' or line.strip().startswith('#'):
                        end_idx += 1
                        continue
                    # Check indentation
                    line_indent = len(line) - len(line.lstrip())
                    if line_indent <= indent and line.strip():
                        break
                    end_idx += 1

                return '\n'.join(lines[start_idx:end_idx])

            return None

        except Exception as e:
            self.logger.error(f"Failed to extract function {function_name} from {file_path}: {e}")
            return None


class DocstringGenerator:
    """Generate detailed docstrings using Poe API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize docstring generator.

        Args:
            api_key: Poe API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (defaults to Claude-Sonnet-4.5)
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize Poe client
        self.client = PoeClient(
            api_key=api_key,
            default_model=model or 'Grok-4-Fast-Reasoning',
            timeout=300,  # 5 minutes per batch
            logger=self.logger
        )

        self.extractor = FunctionExtractor()
        self.function_index = None
        self.enhanced_functions = []
        self.stats = {
            'total_functions': 0,
            'processed': 0,
            'failed': 0,
            'batches': 0
        }

    def load_function_index(self, index_path: str = 'function_index.json'):
        """Load existing function index."""
        self.logger.info(f"Loading function index from {index_path}...")

        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.function_index = data
        self.stats['total_functions'] = data['metadata']['total_functions']

        self.logger.info(f"Loaded {self.stats['total_functions']} functions from {data['metadata']['total_files']} files")

    def create_monolithic_file(self, output_path: str = 'data/FUNCTIONS_MONOLITH.py') -> str:
        """
        Create a monolithic Python file containing all functions with source comments.
        
        Args:
            output_path: Path where the monolithic file should be created
            
        Returns:
            Path to the created monolithic file
        """
        if not self.function_index:
            raise ValueError("Function index not loaded. Call load_function_index() first.")
        
        self.logger.info("Creating monolithic function file...")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("#" * 80 + "\n")
            f.write("# MONOLITHIC FUNCTION FILE - ALL FUNCTIONS FROM JELLYRANCHER\n")
            f.write("# Generated for LLM analysis\n")
            f.write(f"# Total Functions: {self.stats['total_functions']}\n")
            f.write(f"# Total Files: {self.function_index['metadata']['total_files']}\n")
            f.write("#" * 80 + "\n\n")
            
            functions_processed = 0
            
            # Process each file
            for file_path_str, functions in sorted(self.function_index['functions'].items()):
                file_path = Path(file_path_str)
                
                f.write(f"# {'='*76}\n")
                f.write(f"# SOURCE FILE: {file_path_str}\n")
                f.write(f"# {'='*76}\n\n")
                
                # Process each function in the file
                for func_info in functions:
                    # Write source comment before each function
                    f.write(f"# FUNCTION: {func_info['name']}\n")
                    f.write(f"# SOURCE: {file_path_str}:{func_info.get('line', 0)}\n")
                    if func_info.get('is_method') and func_info.get('class'):
                        f.write(f"# CLASS: {func_info['class']}\n")
                    f.write("#" + "-"*76 + "\n")
                    
                    # Extract and write the function code
                    func_code = self.extractor.extract_function_code(
                        file_path_str,
                        func_info['name'],
                        func_info.get('line', 0)
                    )
                    
                    if func_code:
                        f.write(func_code)
                        f.write("\n")
                    else:
                        f.write(f"# ERROR: Could not extract function {func_info['name']}\n\n")
                    
                    functions_processed += 1
                    if functions_processed % 100 == 0:
                        self.logger.info(f"Processed {functions_processed}/{self.stats['total_functions']} functions...")
            
            self.logger.info(f"Created monolithic file: {output_file} with {functions_processed} functions")
        
        return str(output_file)

    def repair_json(self, json_str: str) -> str:
        """
        Repair common JSON malformation issues from LLM responses.
        
        Handles:
        - Missing commas between object properties
        - Unescaped quotes in string values
        - Trailing commas
        - Other common JSON issues
        
        Args:
            json_str: Potentially malformed JSON string
            
        Returns:
            Repaired JSON string
        """
        # First, try to parse as-is
        try:
            json.loads(json_str)
            return json_str  # Already valid
        except json.JSONDecodeError:
            pass
        
        repaired = json_str
        
        # Fix 1: Remove trailing commas before closing brackets/braces
        repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
        
        # Fix 2: Add missing commas between object properties
        # Pattern: "key": value\n    "next_key" -> "key": value,\n    "next_key"
        # This handles cases like: "dependencies": [...]\n    "outputs": {...}
        repaired = re.sub(
            r'("(?:[^"\\]|\\.)*"\s*:\s*(?:\[[^\]]*\]|"[^"]*"|true|false|null|-?\d+\.?\d*)\s*)\n\s*(")',
            r'\1,\n    \2',
            repaired
        )
        
        # Fix 3: Add missing commas after closing brackets/braces before next property
        # Pattern: }\n    "key" -> },\n    "key"
        repaired = re.sub(
            r'([}\]])"',
            r'\1,"',
            repaired
        )
        # But remove comma if it's before closing bracket/brace
        repaired = re.sub(
            r',(\s*[}\]])',
            r'\1',
            repaired
        )
        
        # Fix 4: Escape unescaped quotes inside string values using state machine
        def fix_unescaped_quotes(text):
            """Fix unescaped quotes in JSON string values using a state machine."""
            result = []
            i = 0
            in_string = False
            escape_next = False
            
            while i < len(text):
                char = text[i]
                
                if escape_next:
                    # Next char is escaped, just copy it
                    result.append(char)
                    escape_next = False
                elif char == '\\':
                    # Escape sequence
                    result.append(char)
                    escape_next = True
                elif char == '"':
                    if in_string:
                        # We're inside a string - check if this is the end
                        # Look ahead to see what follows (more characters for better detection)
                        lookahead_start = i + 1
                        lookahead_end = min(i + 100, len(text))
                        lookahead = text[lookahead_start:lookahead_end]
                        lookahead_stripped = lookahead.strip()
                        
                        # More conservative: only treat as end if clearly a structural character
                        # Check for : (property separator), }, ] (object/array end), or ,\n" (next property)
                        is_end = (
                            lookahead_stripped.startswith(':') or
                            lookahead_stripped.startswith('}') or
                            lookahead_stripped.startswith(']') or
                            (lookahead_stripped.startswith(',') and ('\n' in lookahead[:10] or '"' in lookahead[:20])) or
                            (lookahead.startswith('\n') and ('":' in lookahead[:30] or '",' in lookahead[:30]))
                        )
                        
                        if is_end:
                            # End of string
                            in_string = False
                            result.append(char)
                        else:
                            # Unescaped quote in string content - escape it
                            result.append('\\"')
                    else:
                        # Start of string
                        in_string = True
                        result.append(char)
                else:
                    result.append(char)
                
                i += 1
            
            return ''.join(result)
        
        # Apply quote fixing
        repaired = fix_unescaped_quotes(repaired)
        
        # Try parsing again
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON repair attempt failed: {e}")
            return repaired  # Return what we have, let the caller handle the error

    def create_prompt_for_batch(self, functions: List[Dict[str, Any]]) -> str:
        """
        Create prompt for batch of functions using plain text format with delimiters.

        Args:
            functions: List of function dictionaries with code

        Returns:
            Formatted prompt for LLM with plain text input format
        """
        prompt_parts = [
            "You are a technical documentation expert analyzing Python functions from JellyRancher, a media organization application for Jellyfin media libraries.",
            "",
            "I will provide you with functions in a plain text format. You MUST analyze each function and respond with a JSON array in the EXACT format specified below.",
            "",
            "CRITICAL REQUIREMENTS:",
            "1. You MUST output ONLY valid JSON - no markdown, no code blocks, no explanatory text",
            "2. You MUST follow the exact output schema below - all required fields must be present",
            "3. The \"what_it_does\" field must be 2-4 paragraphs explaining WHAT the function does, WHY it exists, its purpose, business logic, and use cases",
            "4. The \"how_it_works\" field must be 2-4 paragraphs explaining HOW the function works - step-by-step algorithm, implementation details, data flow, and technical mechanics",
            "5. The \"inputs\" and \"outputs\" sections must be comprehensive with detailed descriptions",
            "",
            "=== FUNCTIONS TO ANALYZE ===",
            ""
        ]
        
        # Add each function in plain text format
        for idx, func in enumerate(functions, 1):
            prompt_parts.append(f"--- FUNCTION {idx}/{len(functions)} ---")
            prompt_parts.append(f"Name: {func['name']}")
            prompt_parts.append(f"File: {func['file']}")
            prompt_parts.append(f"Line: {func.get('line', 0)}")
            
            if func.get('imports'):
                prompt_parts.append(f"Imports: {', '.join(func['imports'])}")
            
            if func.get('docstring'):
                prompt_parts.append(f"Existing Docstring: {func['docstring']}")
            
            prompt_parts.append("")
            prompt_parts.append("Code:")
            prompt_parts.append(func['code'])
            prompt_parts.append("")
        
        # Add output format specification
        prompt_parts.extend([
            "=== OUTPUT FORMAT ===",
            "You MUST respond with a JSON array in this exact structure:",
            "[",
            "  {",
            "    \"function_name\": \"exact_function_name_from_input\",",
            "    \"file_path\": \"exact_file_path_from_input\",",
            "    \"what_it_does\": \"2-4 paragraphs: Detailed description of WHAT the function does - high-level purpose, business logic, use cases, and why it exists in the application context. Explain the function's role and importance.\",",
            "    \"how_it_works\": \"2-4 paragraphs: Detailed explanation of HOW the function works - step-by-step algorithm, implementation details, data flow, control flow, and technical mechanics. Explain the internal workings.\",",
            "    \"inputs\": {",
            "      \"parameters\": [",
            "        {",
            "          \"name\": \"param_name\",",
            "          \"type\": \"Python type hint or inferred type\",",
            "          \"description\": \"Detailed description of what this parameter represents and how it's used\",",
            "          \"required\": true,",
            "          \"default_value\": \"default if optional (omit if required)\",",
            "          \"constraints\": \"Any constraints, validations, or expected formats\"",
            "        }",
            "      ],",
            "      \"side_effects\": [\"List of external dependencies, file I/O, network calls, or state modifications\"],",
            "      \"dependencies\": [\"External dependencies (modules, classes, functions) this function relies on\"]",
            "    },",
            "    \"outputs\": {",
            "      \"return_value\": {",
            "        \"type\": \"Python type hint or inferred return type\",",
            "        \"description\": \"Detailed description of what is returned, its structure, format, and meaning\",",
            "        \"always\": true,",
            "        \"examples\": [\"Example return values with explanations\"]",
            "      },",
            "      \"exceptions\": [",
            "        {",
            "          \"exception_type\": \"ExceptionType\",",
            "          \"when\": \"Conditions that trigger this exception\",",
            "          \"why\": \"Reason this exception is raised\"",
            "        }",
            "      ],",
            "      \"side_effects\": [\"Any state changes, file modifications, or external effects\"]",
            "    },",
            "    \"enhanced_docstring\": \"Complete Google-style docstring combining all above information in standard Python docstring format (just the docstring text, no triple quotes)\",",
            "    \"usage_example\": \"Code example showing how to use this function\",",
            "    \"notes\": [\"Additional important notes, warnings, or best practices\"]",
            "  }",
            "]",
            "",
            "REMEMBER:",
            "- Return ONLY the JSON array - no markdown code blocks, no ```json```, no explanatory text",
            "- All required fields must be present for each function",
            "- \"what_it_does\" and \"how_it_works\" must be detailed 2-4 paragraph explanations",
            "- Parameters and return values must have comprehensive descriptions",
            "- The JSON must be valid and properly formatted",
            "- Maintain the exact order of functions as provided in input"
        ])
        
        return "\n".join(prompt_parts)

    def create_prompt_for_monolith_chunk(self, chunk_content: str, chunk_num: int, total_chunks: int) -> str:
        """
        Create prompt for a chunk of the monolithic file by loading from LLM_PROMPT.txt.
        
        Args:
            chunk_content: Content of the monolithic file chunk
            chunk_num: Current chunk number
            total_chunks: Total number of chunks
            
        Returns:
            Formatted prompt for LLM
        """
        # Load prompt template from file (relative to project root)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        prompt_file = project_root / 'data' / 'LLM_PROMPT.txt'
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Replace placeholders with actual values
        prompt = prompt_template.replace('{chunk_num}', str(chunk_num))
        prompt = prompt.replace('{total_chunks}', str(total_chunks))
        prompt = prompt.replace('{chunk_content}', chunk_content)
        
        return prompt

    def chunk_monolithic_file(self, monolith_path: str, target_chunks: int = 20) -> List[str]:
        """
        Chunk the monolithic file into target number of chunks, respecting function boundaries.
        
        Args:
            monolith_path: Path to the monolithic file
            target_chunks: Target number of chunks (default 15)
            
        Returns:
            List of chunk strings (each chunk contains complete functions only)
        """
        self.logger.info(f"Chunking monolithic file: {monolith_path} (target: {target_chunks} chunks)")
        
        with open(monolith_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First, split into functions (each function starts with # FUNCTION:)
        lines = content.split('\n')
        functions = []
        current_function = []
        
        for line in lines:
            if line.strip().startswith('# FUNCTION:'):
                # Start of new function - save previous if exists
                if current_function:
                    functions.append('\n'.join(current_function))
                current_function = [line]
            else:
                # Continue current function
                if current_function or line.strip():  # Include header lines before first function
                    current_function.append(line)
        
        # Add final function
        if current_function:
            functions.append('\n'.join(current_function))
        
        self.logger.info(f"Found {len(functions)} functions in monolithic file")
        
        # Calculate target chunk size (functions per chunk)
        if len(functions) == 0:
            return []
        
        functions_per_chunk = max(1, len(functions) // target_chunks)
        
        # Group functions into chunks
        chunks = []
        current_chunk = []
        
        for i, func in enumerate(functions):
            current_chunk.append(func)
            
            # Start new chunk if we've reached target size and there are more functions
            if len(current_chunk) >= functions_per_chunk and i < len(functions) - 1:
                # Check if we need to balance chunks (if remaining functions would create too many chunks)
                remaining_functions = len(functions) - i - 1
                remaining_chunks = target_chunks - len(chunks) - 1
                if remaining_chunks > 0 and remaining_functions / remaining_chunks < functions_per_chunk * 0.5:
                    # Too few functions left - keep adding to current chunk
                    continue
                
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        self.logger.info(f"Created {len(chunks)} chunks from monolithic file ({len(functions)} functions)")
        return chunks

    def chunk_functions(self, functions_by_file: Dict[str, List[Dict]], chunk_size: int = 225) -> List[List[Dict]]:
        """
        Chunk functions into batches for processing.

        Args:
            functions_by_file: Dictionary of functions organized by file
            chunk_size: Number of functions per chunk

        Returns:
            List of function batches
        """
        all_functions = []

        # Flatten all functions and extract code
        for file_path, functions in functions_by_file.items():
            for func in functions:
                # Extract actual function code
                code = self.extractor.extract_function_code(
                    file_path,
                    func['name'],
                    func['line']
                )

                if code:
                    func['code'] = code
                    func['file'] = file_path
                    
                    # Extract signature information and imports
                    try:
                        with warnings.catch_warnings():
                            warnings.filterwarnings('ignore', category=SyntaxWarning)
                            tree = ast.parse(code)
                        func_node = tree.body[0] if tree.body and isinstance(tree.body[0], ast.FunctionDef) else None
                        if func_node:
                            func['parameters'] = [arg.arg for arg in func_node.args.args]
                            func['return_type'] = ast.unparse(func_node.returns) if func_node.returns else "None"
                        else:
                            func['parameters'] = []
                            func['return_type'] = "None"
                        
                        # Extract imports from the function's module context
                        # Try to parse the full file to get imports
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            with warnings.catch_warnings():
                                warnings.filterwarnings('ignore', category=SyntaxWarning)
                                file_tree = ast.parse(file_content)
                            imports = []
                            for node in ast.walk(file_tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        imports.append(alias.name)
                                elif isinstance(node, ast.ImportFrom):
                                    module = node.module or ''
                                    for alias in node.names:
                                        imports.append(f"{module}.{alias.name}" if module else alias.name)
                            func['imports'] = list(set(imports))  # Remove duplicates
                        except Exception:
                            func['imports'] = []
                    except Exception as e:
                        self.logger.warning(f"Could not parse signature for {func['name']}: {e}")
                        func['parameters'] = []
                        func['return_type'] = "None"
                        func['imports'] = []
                        
                    all_functions.append(func)
                else:
                    self.logger.warning(f"Could not extract code for {func['name']} in {file_path}:{func['line']}")

        # Split into chunks
        chunks = []
        for i in range(0, len(all_functions), chunk_size):
            chunks.append(all_functions[i:i + chunk_size])

        self.logger.info(f"Created {len(chunks)} chunks from {len(all_functions)} functions (chunk_size={chunk_size})")
        return chunks

    def _send_with_retry(self, prompt: str, **kwargs):
        """
        Send message with retry logic for API reliability.
        
        Retries on:
        - RuntimeError (from PoeClient for HTTP errors like 502/500)
        - requests.exceptions.RequestException (network/HTTP errors)
        - Timeout errors
        
        Uses exponential backoff: 4s, 8s, 16s, up to 60s max.
        """
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=60),
            retry=(
                lambda exc: isinstance(exc, (RuntimeError,)) or
                (hasattr(exc, '__class__') and 'requests' in str(exc.__class__.__module__))
            )
        )
        def send():
            return self.client.send_message(prompt, **kwargs)

        return send()

    def process_monolith_chunk(self, chunk_content: str, chunk_num: int, total_chunks: int, progress_task=None) -> List[Dict[str, Any]]:
        """
        Process a chunk of the monolithic file through the LLM.
        
        Args:
            chunk_content: Content of the monolithic file chunk
            chunk_num: Current chunk number
            total_chunks: Total number of chunks
            progress_task: Optional RICH progress task for updates
            
        Returns:
            List of enhanced function dictionaries
        """
        console = Console() if RICH_AVAILABLE else None
        
        if console:
            console.print(f"[bold blue]Processing Monolith Chunk {chunk_num}/{total_chunks}[/bold blue]")
        else:
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"Processing Monolith Chunk {chunk_num}/{total_chunks}")
            self.logger.info(f"{'='*80}")
        
        # Create prompt for monolithic chunk
        prompt = self.create_prompt_for_monolith_chunk(chunk_content, chunk_num, total_chunks)
        
        # Log prompt stats
        prompt_chars = len(prompt)
        estimated_tokens = prompt_chars // 4
        
        if console:
            console.print(f"[dim]Prompt: {prompt_chars:,} chars (~{estimated_tokens:,} tokens)[/dim]")
        else:
            self.logger.info(f"Prompt size: {prompt_chars} chars (~{estimated_tokens} tokens)")
        
        try:
            # Send to LLM with retry and live elapsed time tracking
            if console:
                console.print("[yellow]Sending to LLM...[/yellow]")
            else:
                self.logger.info("Sending chunk to LLM...")
            
            # Track elapsed time during API request
            elapsed_time = [0.0]
            stop_timer = threading.Event()
            
            def update_elapsed_time():
                """Update progress with elapsed time while request is in progress."""
                start = time.perf_counter()
                while not stop_timer.is_set():
                    elapsed = time.perf_counter() - start
                    elapsed_time[0] = elapsed
                    elapsed_str = f"{elapsed:.1f}s" if elapsed < 60 else f"{elapsed/60:.1f}m"
                    
                    if progress_task:
                        progress_task.update(description=f"Processing chunk {chunk_num}/{total_chunks}... (elapsed: {elapsed_str})")
                    
                    elapsed_str_display = f"API request in progress... (elapsed: {elapsed_str})"
                    print(f"\r{elapsed_str_display}", end="", flush=True)
                    
                    time.sleep(0.5)
            
            timer_thread = threading.Thread(target=update_elapsed_time, daemon=True)
            timer_thread.start()
            
            try:
                response = self._send_with_retry(
                    prompt,
                    max_tokens=8000,  # More tokens for larger chunks
                    temperature=0.3
                )
            finally:
                stop_timer.set()
                timer_thread.join(timeout=1.0)
            
            final_elapsed = elapsed_time[0]
            elapsed_str = f"{final_elapsed:.1f}s" if final_elapsed < 60 else f"{final_elapsed/60:.1f}m"
            print("\r" + " " * 80 + "\r", end="", flush=True)
            self.logger.info(f"Request completed in {elapsed_str}")
            
            # Parse JSON response
            if console:
                console.print("[cyan]Parsing response...[/cyan]")
            else:
                self.logger.info("Parsing LLM response...")
            
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response[json_start:json_end]
            
            # Try to parse JSON, with repair if needed
            try:
                enhanced = json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parse error at position {e.pos}: {e.msg}. Attempting repair...")
                repaired_json = self.repair_json(json_str)
                try:
                    enhanced = json.loads(repaired_json)
                    self.logger.info("JSON repair successful")
                except json.JSONDecodeError as e2:
                    self.logger.error(f"JSON repair failed at position {e2.pos}: {e2.msg}")
                    raise ValueError(f"Failed to parse JSON even after repair: {e2.msg} at position {e2.pos}")
            
            if not isinstance(enhanced, list):
                raise ValueError("Expected JSON array in response")
            
            # Convert enhanced analysis to function dictionaries
            results = []
            for analysis in enhanced:
                func_dict = {
                    'name': analysis.get('function_name', ''),
                    'file': analysis.get('file_path', ''),
                    'enhanced_docstring': analysis.get('enhanced_docstring', ''),
                    'what_it_does': analysis.get('what_it_does', ''),
                    'how_it_works': analysis.get('how_it_works', ''),
                    'inputs_analysis': analysis.get('inputs', {}),
                    'outputs_analysis': analysis.get('outputs', {}),
                    'usage_example': analysis.get('usage_example', ''),
                    'notes': analysis.get('notes', []),
                    'docstring_generated': True,
                    'generation_timestamp': datetime.now().isoformat(),
                    'analysis_format': 'standardized_v1'
                }
                results.append(func_dict)
                self.stats['processed'] += 1
            
            if console:
                console.print(f"[green]Successfully processed {len(results)} functions[/green]")
            else:
                self.logger.info(f"Successfully processed {len(results)} functions in chunk {chunk_num}")
            
            if progress_task:
                progress_task.advance(1)
            
            return results
            
        except Exception as e:
            if console:
                console.print(f"[red]Failed to process chunk {chunk_num}: {e}[/red]")
            else:
                self.logger.error(f"Failed to process chunk {chunk_num}: {e}")
            self.stats['failed'] += 1  # Count chunk as failed, not individual functions
            
            if progress_task:
                progress_task.advance(1)
            
            return []

    def process_batch(self, batch: List[Dict[str, Any]], batch_num: int, total_batches: int, progress_task=None) -> List[Dict[str, Any]]:
        """
        Process a batch of functions through the LLM.

        Args:
            batch: List of function dictionaries
            batch_num: Current batch number
            total_batches: Total number of batches
            progress_task: Optional RICH progress task for updates

        Returns:
            List of enhanced function dictionaries
        """
        console = Console() if RICH_AVAILABLE else None
        
        if console:
            console.print(f"[bold blue]Processing Batch {batch_num}/{total_batches}[/bold blue] [dim]({len(batch)} functions)[/dim]")
        else:
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"Processing Batch {batch_num}/{total_batches} ({len(batch)} functions)")
            self.logger.info(f"{'='*80}")

        # Create prompt
        prompt = self.create_prompt_for_batch(batch)

        # Log prompt stats
        prompt_chars = len(prompt)
        estimated_tokens = prompt_chars // 4  # Rough estimate
        
        if console:
            console.print(f"[dim]Prompt: {prompt_chars:,} chars (~{estimated_tokens:,} tokens)[/dim]")
        else:
            self.logger.info(f"Prompt size: {prompt_chars} chars (~{estimated_tokens} tokens)")

        try:
            # Send to LLM with retry and live elapsed time tracking
            if console:
                console.print("[yellow]Sending to LLM...[/yellow]")
            else:
                self.logger.info("Sending batch to LLM...")
            
            # Track elapsed time during API request
            elapsed_time = [0.0]  # Use list to allow modification from nested function
            stop_timer = threading.Event()
            
            def update_elapsed_time():
                """Update progress with elapsed time while request is in progress."""
                start = time.perf_counter()
                while not stop_timer.is_set():
                    elapsed = time.perf_counter() - start
                    elapsed_time[0] = elapsed
                    elapsed_str = f"{elapsed:.1f}s" if elapsed < 60 else f"{elapsed/60:.1f}m"
                    
                    # Update progress bar if available
                    if progress_task:
                        progress_task.update(description=f"Processing batch {batch_num}/{total_batches}... (elapsed: {elapsed_str})")
                    
                    # Also print to console for visibility (update in place)
                    # Use sys.stdout for direct control, update every 0.5 seconds for smooth display
                    elapsed_str_display = f"API request in progress... (elapsed: {elapsed_str})"
                    print(f"\r{elapsed_str_display}", end="", flush=True)
                    
                    time.sleep(0.5)  # Update every 0.5 seconds
            
            # Start elapsed time updater
            timer_thread = threading.Thread(target=update_elapsed_time, daemon=True)
            timer_thread.start()
            
            try:
                response = self._send_with_retry(
                    prompt,
                    max_tokens=4000,  # Enough for detailed docstrings
                    temperature=0.3   # Lower temperature for consistent, factual output
                )
            finally:
                stop_timer.set()
                timer_thread.join(timeout=1.0)
            
            # Clear the in-place line and show final elapsed time
            final_elapsed = elapsed_time[0]
            elapsed_str = f"{final_elapsed:.1f}s" if final_elapsed < 60 else f"{final_elapsed/60:.1f}m"
            # Clear the progress line and print final result
            print("\r" + " " * 80 + "\r", end="", flush=True)  # Clear the line
            self.logger.info(f"Request completed in {elapsed_str}")

            # Parse JSON response
            if console:
                console.print("[cyan]Parsing response...[/cyan]")
            else:
                self.logger.info("Parsing LLM response...")

            # Extract JSON from response (in case LLM adds extra text)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")

            json_str = response[json_start:json_end]
            
            # Try to parse JSON, with repair if needed
            try:
                enhanced = json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parse error at position {e.pos}: {e.msg}. Attempting repair...")
                # Attempt to repair the JSON
                repaired_json = self.repair_json(json_str)
                try:
                    enhanced = json.loads(repaired_json)
                    self.logger.info("JSON repair successful")
                except json.JSONDecodeError as e2:
                    self.logger.error(f"JSON repair failed at position {e2.pos}: {e2.msg}")
                    # Try to extract what we can - find valid JSON objects
                    raise ValueError(f"Failed to parse JSON even after repair: {e2.msg} at position {e2.pos}")

            if not isinstance(enhanced, list):
                raise ValueError("Expected JSON array in response")

            # Validate response matches batch
            if len(enhanced) != len(batch):
                self.logger.warning(f"Response has {len(enhanced)} items but batch has {len(batch)} functions")

            # Merge enhanced analysis with original function data
            results = []
            for i, func in enumerate(batch):
                if i < len(enhanced):
                    analysis = enhanced[i]
                    
                    # Validate required fields in new format
                    required_fields = ['function_name', 'file_path', 'what_it_does', 'how_it_works', 
                                     'inputs', 'outputs', 'enhanced_docstring']
                    missing_fields = [field for field in required_fields if field not in analysis]
                    
                    if missing_fields:
                        self.logger.warning(f"Function {func['name']} missing required fields: {missing_fields}")
                        # Fallback to old format if available
                        func['enhanced_docstring'] = analysis.get('enhanced_docstring', func.get('docstring', ''))
                        func['docstring_generated'] = False
                    else:
                        # Store comprehensive analysis in new format
                        func['enhanced_docstring'] = analysis.get('enhanced_docstring', func.get('docstring', ''))
                        func['what_it_does'] = analysis.get('what_it_does', '')
                        func['how_it_works'] = analysis.get('how_it_works', '')
                        func['inputs_analysis'] = analysis.get('inputs', {})
                        func['outputs_analysis'] = analysis.get('outputs', {})
                        func['usage_example'] = analysis.get('usage_example', '')
                        func['notes'] = analysis.get('notes', [])
                        func['docstring_generated'] = True
                        func['generation_timestamp'] = datetime.now().isoformat()
                        func['analysis_format'] = 'standardized_v1'  # Mark as new format
                else:
                    func['enhanced_docstring'] = func.get('docstring', '')
                    func['docstring_generated'] = False

                results.append(func)
                self.stats['processed'] += 1

            if console:
                console.print(f"[green]Successfully processed {len(results)} functions[/green]")
            else:
                self.logger.info(f"Successfully processed {len(results)} functions in batch {batch_num}")
            
            if progress_task:
                progress_task.advance(1)
            
            return results

        except Exception as e:
            if console:
                console.print(f"[red]Failed to process batch {batch_num}: {e}[/red]")
            else:
                self.logger.error(f"Failed to process batch {batch_num}: {e}")
            self.stats['failed'] += len(batch)
            
            if progress_task:
                progress_task.advance(1)

            # Return batch with original docstrings
            for func in batch:
                func['enhanced_docstring'] = func.get('docstring', '')
                func['docstring_generated'] = False
                func['generation_error'] = str(e)

            return batch

    def process_all_functions(self, use_monolith: bool = True, target_chunks: int = 20, delay_seconds: float = 2.0):
        """
        Process all functions to generate enhanced docstrings using monolithic file approach.

        Note: API calls are always sequential to respect Poe.com rate limits.
        Local processing (file parsing, AST analysis) could be parallelized in the future.

        Args:
            use_monolith: If True, use monolithic file approach (default: True)
            target_chunks: Target number of chunks (default 15)
            delay_seconds: Delay between batches in seconds (default 2.0 to respect rate limits)
        """
        if not self.function_index:
            raise ValueError("Function index not loaded. Call load_function_index() first.")

        console = Console() if RICH_AVAILABLE else None

        if use_monolith:
            # Create monolithic file
            if console:
                console.print("[bold cyan]Creating monolithic function file...[/bold cyan]")
            monolith_path = self.create_monolithic_file()
            
            # Chunk the monolithic file (respecting function boundaries)
            if console:
                console.print(f"[bold cyan]Chunking monolithic file into {target_chunks} chunks...[/bold cyan]")
            chunks = self.chunk_monolithic_file(monolith_path, target_chunks=target_chunks)
            self.stats['batches'] = len(chunks)
        else:
            # Legacy approach: chunk by function count
            if console:
                console.print("[bold cyan]Chunking functions...[/bold cyan]")
            chunks = self.chunk_functions(self.function_index['functions'], chunk_size=225)
            self.stats['batches'] = len(chunks)

        # Create beautiful header
        if console:
            title = f"Generating Enhanced Docstrings\n{self.stats['total_functions']} functions in {len(chunks)} batches"
            console.print(Panel.fit(title, border_style="blue", padding=(1, 2)))
        else:
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"Starting Docstring Generation for {self.stats['total_functions']} Functions")
            self.logger.info(f"{'='*80}\n")

        # Process batches sequentially (API calls must be sequential for Poe.com)
        self.enhanced_functions = []

        if console and RICH_AVAILABLE:
            # Sequential processing with RICH progress bar
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
                batch_task = progress.add_task(
                    f"[cyan]Processing {len(chunks)} batches (0.0s elapsed)...",
                    total=len(chunks)
                )

                for i, chunk in enumerate(chunks, 1):
                    if use_monolith:
                        # Process monolithic chunk
                        results = self.process_monolith_chunk(chunk, i, len(chunks), progress_task=batch_task)
                    else:
                        # Process function batch
                        results = self.process_batch(chunk, i, len(chunks), progress_task=batch_task)
                    self.enhanced_functions.extend(results)
                    if i < len(chunks):  # No delay after last batch
                        progress.update(batch_task, description=f"[yellow]Waiting {delay_seconds}s before next batch...[/yellow]")
                        time.sleep(delay_seconds)
                        progress.update(batch_task, description=f"[cyan]Processing {len(chunks)} batches...[/cyan]")
        else:
            # Fallback to basic logging (still sequential)
            for i, chunk in enumerate(chunks, 1):
                if use_monolith:
                    results = self.process_monolith_chunk(chunk, i, len(chunks))
                else:
                    results = self.process_batch(chunk, i, len(chunks))
                self.enhanced_functions.extend(results)
                if i < len(chunks):  # No delay after last batch
                    self.logger.info(f"Waiting {delay_seconds} seconds before next batch to respect rate limits...")
                    time.sleep(delay_seconds)

        # Print statistics
        if console and RICH_AVAILABLE:
            success_rate = 100 * self.stats['processed'] / self.stats['total_functions'] if self.stats['total_functions'] > 0 else 0
            stats_text = f"""
[bold green]DOCSTRING GENERATION COMPLETE[/bold green]

[cyan]Total Functions:[/cyan] {self.stats['total_functions']}
[green]Processed:[/green] {self.stats['processed']}
[red]Failed:[/red] {self.stats['failed']}
[blue]Batches:[/blue] {self.stats['batches']}
[bold]Success Rate:[/bold] {success_rate:.1f}%
"""
            console.print(Panel(stats_text.strip(), border_style="green", title="Results"))
        else:
            self.logger.info(f"\n{'='*80}")
            self.logger.info("DOCSTRING GENERATION COMPLETE")
            self.logger.info(f"{'='*80}")
            self.logger.info(f"Total Functions: {self.stats['total_functions']}")
            self.logger.info(f"Processed: {self.stats['processed']}")
            self.logger.info(f"Failed: {self.stats['failed']}")
            self.logger.info(f"Batches: {self.stats['batches']}")
            self.logger.info(f"Success Rate: {100 * self.stats['processed'] / self.stats['total_functions']:.1f}%")
            self.logger.info(f"{'='*80}\n")

    def save_enhanced_index(self, output_file: str = 'enhanced_function_index.json'):
        """
        Save enhanced function index preserving comprehensive analysis format.

        Args:
            output_file: Path to output file
        """
        index_list = []
        for func in self.enhanced_functions:
            # Derive module from file path
            file_path = func.get('file', '')
            module = file_path.replace('/', '.').replace('\\', '.').rstrip('.py') if file_path else ''
            
            # Check if function has new standardized format
            if func.get('analysis_format') == 'standardized_v1':
                # Save comprehensive analysis
                item = {
                    "function_name": func['name'],
                    "module": module,
                    "source_file": func.get('file', ''),
                    "line_number": func.get('line', 0),
                    "docstring": func.get('enhanced_docstring', ''),
                    "what_it_does": func.get('what_it_does', ''),
                    "how_it_works": func.get('how_it_works', ''),
                    "inputs": func.get('inputs_analysis', {}),
                    "outputs": func.get('outputs_analysis', {}),
                    "usage_example": func.get('usage_example', ''),
                    "notes": func.get('notes', []),
                    "parameters": func.get('parameters', []),
                    "return_type": func.get('return_type', 'None'),
                    "tags": [],
                    "analysis_format": "standardized_v1",
                    "generation_timestamp": func.get('generation_timestamp', '')
                }
            else:
                # Fallback to legacy format for backward compatibility
                item = {
                    "function_name": func['name'],
                    "module": module,
                    "docstring": func.get('enhanced_docstring', ''),
                    "parameters": func.get('parameters', []),
                    "return_type": func.get('return_type', 'None'),
                    "tags": [],
                    "source_file": func.get('file', ''),
                    "line_number": func.get('line', 0),
                    "analysis_format": "legacy"
                }
            index_list.append(item)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index_list, f, indent=2, ensure_ascii=False)

        standardized_count = sum(1 for f in index_list if f.get('analysis_format') == 'standardized_v1')
        console = Console() if RICH_AVAILABLE else None
        
        if console:
            console.print(f"[green]Enhanced function index saved to[/green] [bold]{output_file}[/bold]")
            console.print(f"  [cyan]Total functions:[/cyan] {len(index_list)}")
            console.print(f"  [blue]Standardized format:[/blue] {standardized_count}")
            console.print(f"  [green]Docstrings generated:[/green] {sum(1 for f in index_list if f.get('docstring'))}")
        else:
            self.logger.info(f"Enhanced function index saved to {output_file}")
            self.logger.info(f"  Total functions: {len(index_list)}")
            self.logger.info(f"  Standardized format: {standardized_count}")
            self.logger.info(f"  Docstrings generated: {sum(1 for f in index_list if f.get('docstring'))}")

        return index_list


def main():
    """Main entry point with CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate detailed docstrings for all functions using LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate docstrings using monolithic file approach (default)
  python generate_docstrings_with_llm.py

  # Use different number of chunks
  python generate_docstrings_with_llm.py --target-chunks 20

  # Use legacy function-by-function approach
  python generate_docstrings_with_llm.py --no-monolith --chunk-size 100

  # Use specific model
  python generate_docstrings_with_llm.py --model Grok-4-Fast-Reasoning

  # Process only first 50 functions (for testing)
  python generate_docstrings_with_llm.py --limit 50
        """
    )

    parser.add_argument('--use-monolith', action='store_true', default=True, help='Use monolithic file approach (default: True)')
    parser.add_argument('--no-monolith', dest='use_monolith', action='store_false', help='Use legacy function-by-function approach')
    parser.add_argument('--target-chunks', type=int, default=20, help='Target number of chunks for monolithic file (default: 20)')
    parser.add_argument('--chunk-size', type=int, default=225, help='Number of functions per batch (legacy mode only, default: 225)')
    parser.add_argument('--model', default='Grok-4-Fast-Reasoning', help='Model to use (default: Grok-4-Fast-Reasoning)')
    parser.add_argument('--api-key', help='API key (default: OPENAI_API_KEY env var)')
    parser.add_argument('--limit', type=int, help='Limit processing to first N functions (for testing)')
    parser.add_argument('--output', default='enhanced_function_index_grok.json', help='Output file (default: enhanced_function_index_grok.json)')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between batches in seconds (default: 2.0)')

    args = parser.parse_args()

    # Initialize generator
    generator = DocstringGenerator(api_key=args.api_key, model=args.model)

    # Load function index
    generator.load_function_index()

    # Limit functions if requested
    if args.limit:
        # Limit to first N functions for testing
        limited_functions = {}
        count = 0
        for file_path, functions in generator.function_index['functions'].items():
            if count >= args.limit:
                break

            limited_functions[file_path] = []
            for func in functions:
                if count >= args.limit:
                    break
                limited_functions[file_path].append(func)
                count += 1

        generator.function_index['functions'] = limited_functions
        generator.stats['total_functions'] = count
        generator.logger.info(f"Limited to first {count} functions for testing")

    # Process all functions (API calls are always sequential for Poe.com)
    generator.process_all_functions(
        use_monolith=args.use_monolith,
        target_chunks=args.target_chunks,
        delay_seconds=args.delay
    )

    # Save enhanced index
    enhanced_index = generator.save_enhanced_index(output_file=args.output)

    # Final summary (only if RICH not available, otherwise already shown)
    if not RICH_AVAILABLE:
        print("\n" + "="*80)
        print("DOCSTRING GENERATION COMPLETE!")
        print("="*80)
        print(f"Enhanced index: {args.output}")
        print(f"Functions processed: {generator.stats['processed']}/{generator.stats['total_functions']}")
        print(f"Success rate: {100 * generator.stats['processed'] / generator.stats['total_functions']:.1f}%")
        print("="*80)


if __name__ == "__main__":
    main()
