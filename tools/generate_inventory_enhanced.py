#!/usr/bin/env python3
"""
Enhanced CODE-INVENTORY generator with detailed analysis of major scripts.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any
import ast

def count_complexity(content: str) -> int:
    """Estimate cyclomatic complexity by counting decision points."""
    complexity = 1  # Base complexity
    complexity += len(re.findall(r'\bif\b', content))
    complexity += len(re.findall(r'\bfor\b', content))
    complexity += len(re.findall(r'\bwhile\b', content))
    complexity += len(re.findall(r'\bexcept\b', content))
    complexity += len(re.findall(r'\belif\b', content))
    complexity += len(re.findall(r'\band\b', content))
    complexity += len(re.findall(r'\bor\b', content))
    return complexity

def get_detailed_analysis(file_path: Path) -> Dict[str, Any]:
    """Get detailed analysis for key files."""
    
    filename = file_path.name.lower()
    
    # Special analysis for key files
    detailed_info = {
        "ravenmaven_gui.py": {
            "summary": "Main GUI application for RavenMaven media reorganization tool. Provides batch processing interface with AI integration via Poe.com, structure preview, and safe execution with dry-run mode. Features customtkinter-based modern UI with progress tracking, logging, and cache management.",
            "major_components": [
                {"name": "RavenMavenGUI", "kind": "class", "description": "Main GUI application class"},
                {"name": "CacheManager", "kind": "class", "description": "Manages cached file lists and results"},
                {"name": "TextHandler", "kind": "class", "description": "Custom logging handler for tkinter"},
                {"name": "StreamToLogger", "kind": "class", "description": "Redirects stdout/stderr to logging"}
            ],
            "external": ["customtkinter", "tkinter", "PoeClient", "JellyfinSafeExecutor", "BatchQueueProcessor"],
            "inputs": [
                {"name": "source_directory", "type": "file", "description": "Directory to scan for media files"},
                {"name": "prompt_template", "type": "file", "description": "AI prompt template for batch processing"},
                {"name": "cached_lists", "type": "file", "description": "Previously saved scan results"}
            ],
            "outputs": [
                {"name": "reorganization_plan", "type": "file", "description": "JSON file with proposed file operations"},
                {"name": "execution_log", "type": "file", "description": "Log of executed operations"},
                {"name": "cache_files", "type": "file", "description": "Cached scan results and metadata"}
            ],
            "example_usage": "python ravenmaven_gui.py  # Launch GUI, scan directory, process with AI, preview structure, execute with dry-run",
            "suggested_tests": [
                "Test GUI initialization and component loading",
                "Test file scanning with various directory structures",
                "Test cache save/load functionality",
                "Test AI integration with mock responses",
                "Test safe execution with dry-run mode"
            ],
            "notable_features": [
                "Asynchronous batch processing with progress tracking",
                "Integrated AI analysis via Poe.com API",
                "Cache management for resuming interrupted sessions",
                "Safe file operations with atomic moves and verification",
                "Real-time logging with threadsafe text widget updates"
            ]
        },
        "ravenmaven_combined.py": {
            "summary": "Combined batch processing script for media reorganization using AI. Integrates file scanning, AI analysis via PoeClient, markdown table parsing, and safe execution. Supports chunked processing of large file lists and structure tree building for Jellyfin-compatible organization.",
            "major_components": [
                {"name": "ai_analysis", "kind": "function", "description": "Send files to AI for reorganization analysis"},
                {"name": "parse_markdown_table", "kind": "function", "description": "Parse AI response in markdown table format"},
                {"name": "execute_actions", "kind": "function", "description": "Execute file operations with dry-run support"},
                {"name": "build_structure_tree", "kind": "function", "description": "Build hierarchical view of proposed structure"}
            ],
            "example_usage": "python ravenmaven_combined.py --source /path/to/media --prompt template.txt --chunk-size 50 --dry-run",
            "notable_features": [
                "Chunked processing for large file lists (configurable chunk size)",
                "AI-powered reorganization suggestions",
                "Dry-run mode for safe testing",
                "Structure preview before execution",
                "Markdown table parsing from LLM responses"
            ]
        },
        "media_scanner.py": {
            "summary": "Media file scanner for RavenMaven. Scans directories, categorizes files as movies/TV shows/subtitles, and generates reorganization plans based on filename patterns. Uses regex patterns to extract show names, season/episode numbers, and movie titles.",
            "major_components": [
                {"name": "MediaFileScanner", "kind": "class", "description": "Main scanner class for media files"},
                {"name": "scan_files", "kind": "function", "description": "Recursively scan directory for media files"},
                {"name": "categorize_file", "kind": "function", "description": "Categorize file as movie, TV show, or subtitle"},
                {"name": "extract_tv_show_info", "kind": "function", "description": "Extract show name, season, episode from filename"}
            ],
            "example_usage": "scanner = MediaFileScanner('/path/to/media'); files = scanner.scan_files(); plan = scanner.generate_reorganization_plan(files)"
        },
        "llm_response_parser.py": {
            "summary": "LLM response parser for RavenMaven. Converts LLM text responses (OLD: NEW: format) into structured JSON for jellyfin_safe_executor. Handles cleanup of LLM output, extraction of file mappings, and batch processing of chunked responses.",
            "major_components": [
                {"name": "clean_llm_response", "kind": "function", "description": "Extract OLD: NEW mappings from LLM output"},
                {"name": "process_chunk_file", "kind": "function", "description": "Process and clean single chunk JSON file"}
            ],
            "example_usage": "python llm_response_parser.py  # Processes chunk1-9_processed.json files in lists/ directory"
        },
        "main.py": {
            "summary": "Main orchestrator for Jellyfin Media Organization Agent. Provides TUI interface using Rich for managing media folders across multiple volumes. Supports folder registration, JellyDive sessions, audit logs, and system status monitoring. Integrates immutable audit logging, credential management, and snapshot management.",
            "major_components": [
                {"name": "JellyfinOrganizer", "kind": "class", "description": "Main orchestrator class"},
                {"name": "show_main_menu", "kind": "function", "description": "Display Rich TUI main menu"},
                {"name": "register_new_folder", "kind": "function", "description": "Register new media folder for management"},
                {"name": "start_jellydive_session", "kind": "function", "description": "Initiate media organization session"}
            ],
            "external": ["rich", "immutable_audit", "credential_manager", "snapshot_manager", "media_utils"],
            "example_usage": "python main.py  # Launch TUI, register folders, start organization sessions"
        },
        "codecop_gui.py": {
            "summary": "CodeCop auditing wizard GUI. Modern tkinter-based interface for code auditing workflow. Orchestrates multi-step auditing process: install tools, collect signals, summarize files, consolidate reports, and police reports. Includes LLM model selection, progress tracking, and log management.",
            "major_components": [
                {"name": "CodeCopWizard", "kind": "class", "description": "Main GUI wizard class"},
                {"name": "install_tools", "kind": "function", "description": "Install required auditing tools"},
                {"name": "collect_signals", "kind": "function", "description": "Collect code signals for analysis"},
                {"name": "summarize_files", "kind": "function", "description": "Generate file summaries using LLM"},
                {"name": "consolidate_reports", "kind": "function", "description": "Consolidate audit reports"}
            ],
            "external": ["tkinter", "ttkbootstrap", "requests"],
            "example_usage": "python codecop_gui.py  # Launch wizard, select LLM model, run audit steps"
        },
        "jellyfin_safe_executor.py": {
            "summary": "Safe file operation executor for Jellyfin media organization. Implements atomic moves with hash verification, rollback capability, and detailed audit logging. Prevents data loss through pre-execution validation and supports dry-run mode for testing.",
            "major_components": [
                {"name": "JellyfinSafeExecutor", "kind": "class", "description": "Safe file operation executor"},
                {"name": "execute_action", "kind": "function", "description": "Execute single file operation with verification"},
                {"name": "rollback", "kind": "function", "description": "Rollback failed operations"}
            ],
            "notable_features": [
                "Atomic file operations with hash verification",
                "Automatic rollback on failure",
                "Comprehensive audit trail",
                "Dry-run mode for safety testing",
                "Duplicate detection and handling"
            ]
        },
        "media_utils.py": {
            "summary": "Media file utilities for Jellyfin Organizer. Provides cryptographic file hashing (SHA-256, CRC32), safe file moves with verification, Windows long path handling, and path validation. Supports concurrent hashing for performance and memory-mapped I/O for large files.",
            "major_components": [
                {"name": "hash_file", "kind": "function", "description": "Calculate SHA-256 hash of file"},
                {"name": "hash_file_crc32", "kind": "function", "description": "Calculate fast CRC32 checksum"},
                {"name": "safe_move", "kind": "function", "description": "Move file with hash verification"},
                {"name": "normalize_windows_path", "kind": "function", "description": "Handle Windows long path limitations"}
            ],
            "notable_features": [
                "Multiple hashing algorithms (SHA-256, CRC32)",
                "Memory-mapped I/O for large files",
                "Concurrent hashing with ThreadPoolExecutor",
                "Windows long path support (\\\\?\\)",
                "Atomic move operations with verification"
            ]
        }
    }
    
    return detailed_info.get(filename, None)

def analyze_python_file_enhanced(file_path: Path) -> Dict[str, Any]:
    """Enhanced Python file analysis with detailed metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        line_count = len(lines)
        
        # Get detailed analysis if available
        detailed = get_detailed_analysis(file_path)
        
        # Extract docstring
        docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if docstring_match:
            summary = docstring_match.group(1).strip()
            summary = ' '.join(summary.split()[:50])
        else:
            summary = "No description available"
        
        if detailed:
            summary = detailed["summary"]
        
        # Extract imports
        imports = []
        stdlib_modules = {'os', 'sys', 'json', 're', 'pathlib', 'typing', 'datetime', 
                         'collections', 'io', 'threading', 'logging', 'unittest', 
                         'argparse', 'subprocess', 'time', 'hashlib', 'shutil', 'mmap',
                         'binascii', 'concurrent', 'functools', 'itertools', 'math',
                         'random', 'string', 'textwrap', 'urllib', 'http', 'xml'}
        
        for line in lines[:150]:
            if line.strip().startswith(('import ', 'from ')):
                imports.append(line.strip())
        
        # Detect entry points
        entry_points = []
        if 'if __name__ == "__main__"' in content:
            entry_points.append('if __name__ == "__main__"')
        if re.search(r'@click\.command|@click\.group', content):
            entry_points.append('Click CLI command')
        if 'def main(' in content:
            entry_points.append('main() function')
        
        # Detect classes and functions
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        
        # Detect type hints
        type_hint_count = len(re.findall(r'->\s*[\w\[\],\s]+:', content))
        param_type_hints = len(re.findall(r':\s*[\w\[\],\s]+(?:\s*=|\s*\))', content))
        total_hints = type_hint_count + param_type_hints
        
        if total_hints > 20:
            type_hints = "complete"
        elif total_hints > 5:
            type_hints = "partial"
        else:
            type_hints = "none"
        
        # Detect async usage
        async_count = len(re.findall(r'\basync\s+(def|with|for)', content))
        await_count = len(re.findall(r'\bawait\b', content))
        if async_count + await_count > 10:
            async_usage = "extensive"
        elif async_count + await_count > 0:
            async_usage = "some"
        else:
            async_usage = "none"
        
        # Detect packaging references
        packaging_refs = []
        if Path(file_path.parent / "requirements.txt").exists():
            packaging_refs.append("requirements.txt")
        if Path(file_path.parent / "pyproject.toml").exists():
            packaging_refs.append("pyproject.toml")
        if Path(file_path.parent / "setup.py").exists():
            packaging_refs.append("setup.py")
        
        # Detect side effects
        side_effects = []
        if any(x in content for x in ['open(', 'write(', 'Path(', 'os.remove', 'shutil.']):
            side_effects.append("file IO")
        if any(x in content for x in ['requests.', 'urllib', 'http.client', 'socket']):
            side_effects.append("network")
        if any(x in content for x in ['sqlite3', 'psycopg2', 'pymongo', 'mysql']):
            side_effects.append("db writes")
        if any(x in content for x in ['subprocess.', 'os.system', 'os.popen']):
            side_effects.append("spawns subprocesses")
        if 'os.environ[' in content or 'os.putenv' in content:
            side_effects.append("modifies ENV")
        if not side_effects:
            side_effects.append("none")
        
        # External dependencies
        external = set()
        for imp in imports:
            match = re.match(r'(?:from\s+)?([\w.]+)', imp)
            if match:
                module = match.group(1).split('.')[0]
                if module not in stdlib_modules:
                    external.add(module)
        
        if detailed and "external" in detailed:
            external.update(detailed["external"])
        
        # Build major components
        major_components = []
        if detailed and "major_components" in detailed:
            major_components = detailed["major_components"]
        else:
            for cls in classes[:5]:
                major_components.append({
                    "name": cls,
                    "kind": "class",
                    "description": f"Class {cls}"
                })
            for func in functions[:5]:
                if not func.startswith('_'):
                    major_components.append({
                        "name": func,
                        "kind": "function",
                        "description": f"Function {func}"
                    })
        
        # Build inputs/outputs
        inputs = detailed.get("inputs", [
            {"name": "command_line_args", "type": "stdin", "description": "Command line arguments"}
        ]) if detailed else [
            {"name": "command_line_args", "type": "stdin", "description": "Command line arguments"}
        ]
        
        outputs = detailed.get("outputs", [
            {"name": "stdout", "type": "stdout", "description": "Standard output and logging"}
        ]) if detailed else [
            {"name": "stdout", "type": "stdout", "description": "Standard output and logging"}
        ]
        
        # Estimate complexity
        complexity = count_complexity(content)
        
        # Determine quality
        has_docstrings = len(re.findall(r'""".*?"""', content, re.DOTALL)) > len(classes) + len(functions[:10])
        has_tests = 'test_' in file_path.name or 'import unittest' in content or 'import pytest' in content
        
        if has_docstrings and type_hints != "none":
            readability = "excellent"
        elif has_docstrings or type_hints != "none":
            readability = "good"
        else:
            readability = "fair"
        
        comments_quality = "good" if content.count('#') > line_count / 20 else "some"
        test_coverage = "partial" if has_tests else "unknown"
        
        # Notable features
        notable_features = []
        if detailed and "notable_features" in detailed:
            notable_features = detailed["notable_features"]
        else:
            if 'try:' in content:
                notable_features.append("Error handling via try/except blocks")
            if 'logging.' in content:
                notable_features.append("Structured logging for debugging")
            if async_usage != "none":
                notable_features.append(f"Async/await concurrency model")
            if 'ThreadPoolExecutor' in content or 'multiprocessing' in content:
                notable_features.append("Concurrent execution with thread/process pools")
        
        example_usage = detailed.get("example_usage", f"python {file_path.name}") if detailed else f"python {file_path.name}"
        
        suggested_tests = detailed.get("suggested_tests", [
            "Unit test for main functions with mock data",
            "Integration test with sample inputs"
        ]) if detailed else [
            "Unit test for main functions with mock data",
            "Integration test with sample inputs"
        ]
        
        return {
            "file": str(file_path.relative_to(Path("v:/JellyRancher"))),
            "language": "Python",
            "module_or_path": str(file_path.stem),
            "summary": summary,
            "structure": {
                "major_components": major_components,
                "data_flow": "Standard Python module with classes and functions providing structured data flow from inputs through processing to outputs."
            },
            "python_details": {
                "imports": imports[:15],
                "entry_points": entry_points,
                "type_hints": type_hints,
                "async_usage": async_usage,
                "packaging_references": packaging_refs
            },
            "powershell_details": None,
            "inputs": inputs,
            "outputs": outputs,
            "side_effects": side_effects,
            "dependencies": {
                "internal": [],
                "external": sorted(list(external)),
                "system": ["python 3.8+", "Windows OS (for some path operations)"]
            },
            "behavior": {
                "notable_features": notable_features,
                "edge_cases_handled": []
            },
            "quality": {
                "readability": readability,
                "comments_quality": comments_quality,
                "test_coverage": test_coverage,
                "maintainability": f"{readability.capitalize()} - {'well-documented' if has_docstrings else 'needs more documentation'}",
                "autogenerated": False
            },
            "example_usage": example_usage,
            "suggested_tests": suggested_tests,
            "suggested_improvements": [
                "Add comprehensive docstrings to all public methods" if not has_docstrings else "Maintain documentation standards",
                "Implement unit tests for core functionality" if test_coverage == "unknown" else "Expand test coverage",
                "Add type hints for better IDE support" if type_hints == "none" else "Complete type hint coverage"
            ],
            "complexity_estimate": {
                "approx_lines": line_count,
                "approx_cyclomatic_complexity": complexity
            },
            "notes": f"Contains {len(classes)} classes and {len(functions)} functions. Complexity score: {complexity}.",
            "error": None
        }
    
    except Exception as e:
        return {
            "file": str(file_path.relative_to(Path("v:/JellyRancher"))),
            "language": "Python",
            "module_or_path": None,
            "summary": None,
            "structure": None,
            "python_details": None,
            "powershell_details": None,
            "inputs": None,
            "outputs": None,
            "side_effects": None,
            "dependencies": None,
            "behavior": None,
            "quality": None,
            "example_usage": None,
            "suggested_tests": None,
            "suggested_improvements": None,
            "complexity_estimate": None,
            "notes": None,
            "error": str(e)
        }

def analyze_powershell_file_enhanced(file_path: Path) -> Dict[str, Any]:
    """Enhanced PowerShell file analysis."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        line_count = len(lines)
        
        # Extract comments for summary
        comments = [line.lstrip('#').strip() for line in lines[:30] if line.strip().startswith('#')]
        summary = ' '.join(comments[:10]) if comments else "PowerShell script"
        
        # Detect param block
        has_param = bool(re.search(r'param\s*\(', content, re.IGNORECASE))
        
        # Extract parameters
        param_names = re.findall(r'\[\w+\]\s*\$(\w+)', content)
        
        # Detect admin requirement
        requires_admin = bool(re.search(r'#\s*requires\s+-runasadministrator', content, re.IGNORECASE))
        if not requires_admin:
            requires_admin = any(x in content.lower() for x in ['requireadministrator', '-verb runas'])
        
        # Detect modules
        modules = re.findall(r'Import-Module\s+["\']?(\w+)["\']?', content, re.IGNORECASE)
        modules += re.findall(r'#Requires\s+-Modules\s+(\w+)', content, re.IGNORECASE)
        
        # Detect functions
        functions = re.findall(r'function\s+(\w+)', content, re.IGNORECASE)
        
        # Side effects
        side_effects = []
        if any(x in content for x in ['Set-Content', 'Out-File', 'New-Item', 'Remove-Item', 'Copy-Item', 'Move-Item']):
            side_effects.append("file IO")
        if 'Invoke-WebRequest' in content or 'Invoke-RestMethod' in content or 'curl' in content:
            side_effects.append("network")
        if 'Start-Process' in content or 'Invoke-Expression' in content:
            side_effects.append("spawns subprocesses")
        if '$env:' in content:
            side_effects.append("modifies ENV")
        if not side_effects:
            side_effects.append("none")
        
        # Build major components
        major_components = []
        if functions:
            for func in functions[:5]:
                major_components.append({
                    "name": func,
                    "kind": "function",
                    "description": f"PowerShell function {func}"
                })
        else:
            major_components.append({
                "name": "Main script",
                "kind": "script",
                "description": "Sequential PowerShell commands"
            })
        
        # Build inputs
        inputs = []
        if param_names:
            for param in param_names:
                inputs.append({
                    "name": param,
                    "type": "string",
                    "description": f"Parameter ${param}"
                })
        else:
            inputs.append({
                "name": "parameters",
                "type": "string",
                "description": "Optional PowerShell parameters"
            })
        
        # Estimate complexity
        complexity = count_complexity(content)
        
        # Determine quality
        has_help = bool(re.search(r'<#.*?#>', content, re.DOTALL))
        comments_quality = "good" if len(comments) > 5 else "some"
        
        return {
            "file": str(file_path.relative_to(Path("v:/JellyRancher"))),
            "language": "PowerShell",
            "module_or_path": None,
            "summary": summary,
            "structure": {
                "major_components": major_components,
                "data_flow": "Sequential PowerShell command execution with parameter handling and error checking."
            },
            "python_details": None,
            "powershell_details": {
                "param_block": "true" if has_param else "false",
                "requires_admin": "true" if requires_admin else "unknown",
                "modules_required": list(set(modules))
            },
            "inputs": inputs,
            "outputs": [
                {
                    "name": "stdout",
                    "type": "stdout",
                    "description": "PowerShell output and status messages"
                }
            ],
            "side_effects": side_effects,
            "dependencies": {
                "internal": [],
                "external": list(set(modules)),
                "system": ["PowerShell 5.1+", "Windows OS"]
            },
            "behavior": {
                "notable_features": [
                    "PowerShell parameter validation" if has_param else "Simple script execution",
                    "Error handling with try/catch" if 'try' in content.lower() else "Basic error handling"
                ],
                "edge_cases_handled": []
            },
            "quality": {
                "readability": "good" if has_help or len(comments) > 5 else "fair",
                "comments_quality": comments_quality,
                "test_coverage": "unknown",
                "maintainability": "Good - standard PowerShell patterns with parameter blocks" if has_param else "Fair - simple script structure",
                "autogenerated": False
            },
            "example_usage": f".\\{file_path.name}" + (f" -Parameter1 value1" if param_names else ""),
            "suggested_tests": [
                "Test with various parameter combinations" if has_param else "Test basic script execution",
                "Validate error handling and edge cases"
            ],
            "suggested_improvements": [
                "Add comment-based help (<# #>)" if not has_help else "Maintain documentation",
                "Implement comprehensive error handling with try/catch",
                "Add parameter validation attributes"
            ],
            "complexity_estimate": {
                "approx_lines": line_count,
                "approx_cyclomatic_complexity": complexity
            },
            "notes": f"PowerShell script with {len(functions)} functions. Requires admin: {requires_admin}.",
            "error": None
        }
    
    except Exception as e:
        return {
            "file": str(file_path.relative_to(Path("v:/JellyRancher"))),
            "language": "PowerShell",
            "error": str(e)
        }

def main():
    """Generate enhanced inventory."""
    base_path = Path("v:/JellyRancher")
    
    # Find all files
    python_files = []
    powershell_files = []
    
    for root, dirs, files in os.walk(base_path):
        # Skip virtual environments
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', 'env', '__pycache__', 'node_modules', '.git']]
        
        for file in files:
            file_path = Path(root) / file
            if file.endswith('.py') and '__pycache__' not in str(file_path):
                python_files.append(file_path)
            elif file.endswith('.ps1'):
                powershell_files.append(file_path)
    
    print(f"Found {len(python_files)} Python files and {len(powershell_files)} PowerShell files")
    
    # Prioritize files
    priority_names = ['main', 'gui', 'client', 'executor', 'scanner', 'parser', 'utils', 'manager', 
                     'backend', 'organizer', 'combined', 'batch', 'media', 'jellyfin']
    
    priority_files = []
    other_files = []
    
    for pf in python_files:
        if any(name in pf.name.lower() for name in priority_names) and 'test_' not in pf.name:
            priority_files.append(pf)
        elif 'test_' not in pf.name and 'archive' not in str(pf):
            other_files.append(pf)
    
    # Analyze files
    inventory = []
    
    # Priority files first (top 50)
    for pf in priority_files[:50]:
        print(f"Analyzing {pf.name}...")
        result = analyze_python_file_enhanced(pf)
        inventory.append(result)
    
    # Other important files (next 50)
    for pf in other_files[:50]:
        print(f"Analyzing {pf.name}...")
        result = analyze_python_file_enhanced(pf)
        inventory.append(result)
    
    # All PowerShell files
    for psf in powershell_files:
        print(f"Analyzing {psf.name}...")
        result = analyze_powershell_file_enhanced(psf)
        inventory.append(result)
    
    # Generate output
    output = {"files": inventory}
    
    output_file = base_path / "CODE-INVENTORY.MD"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Enhanced inventory generated: {output_file}")
    print(f"Total files analyzed: {len(inventory)}")
    print(f"Python files: {sum(1 for f in inventory if f.get('language') == 'Python')}")
    print(f"PowerShell files: {sum(1 for f in inventory if f.get('language') == 'PowerShell')}")

if __name__ == "__main__":
    main()
