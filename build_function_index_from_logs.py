#!/usr/bin/env python3
"""Build comprehensive function/capabilities index from LLM io logs."""

import json
import glob
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional

class FunctionIndexBuilder:
    """Builds a comprehensive function index from LLM io logs."""
    
    def __init__(self, log_dir: str = "LLM_io_log", output_file: str = "data/llm_function_index.json"):
        self.log_dir = Path(log_dir)
        self.output_file = Path(output_file)
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            'files_processed': 0,
            'files_with_functions': 0,
            'total_functions_found': 0,
            'unique_functions': 0,
            'duplicates_merged': 0,
            'errors': []
        }
    
    def extract_complete_json_object(self, text: str, start_pos: int) -> Optional[Dict[str, Any]]:
        """Extract a complete JSON object starting at start_pos by finding matching braces."""
        if start_pos >= len(text) or text[start_pos] != '{':
            return None
        
        brace_count = 0
        in_string = False
        escape_next = False
        end_pos = start_pos
        
        for i in range(start_pos, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
        
        if brace_count == 0 and end_pos > start_pos:
            try:
                obj_str = text[start_pos:end_pos]
                return json.loads(obj_str)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def extract_functions_from_log(self, log_file: Path) -> List[Dict[str, Any]]:
        """Extract function data from a single log file."""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            final_response = data.get('final_response', {})
            text = final_response.get('text', '')
            
            if not text:
                return []
            
            functions = []
            text_stripped = text.strip()
            
            # Strategy 1: Try to parse as complete JSON array
            if text_stripped.startswith('['):
                try:
                    functions = json.loads(text_stripped)
                    if isinstance(functions, list):
                        return functions
                except json.JSONDecodeError:
                    # Try to find JSON array boundaries more carefully
                    # Look for [ at start, find matching ]
                    bracket_count = 0
                    array_start = text_stripped.find('[')
                    if array_start >= 0:
                        in_string = False
                        escape_next = False
                        for i in range(array_start, len(text_stripped)):
                            char = text_stripped[i]
                            if escape_next:
                                escape_next = False
                                continue
                            if char == '\\':
                                escape_next = True
                                continue
                            if char == '"' and not escape_next:
                                in_string = not in_string
                                continue
                            if not in_string:
                                if char == '[':
                                    bracket_count += 1
                                elif char == ']':
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        try:
                                            array_text = text_stripped[array_start:i+1]
                                            functions = json.loads(array_text)
                                            if isinstance(functions, list):
                                                return functions
                                        except:
                                            pass
                                        break
            
            # Strategy 2: Find all function_name occurrences and extract complete objects
            # Find all positions where "function_name" appears
            func_name_pattern = r'"function_name"\s*:\s*"([^"]+)"'
            matches = list(re.finditer(func_name_pattern, text_stripped))
            
            if matches:
                # For each match, find the start of the object (previous {)
                for match in matches:
                    # Search backwards from match start to find opening brace
                    start_pos = match.start()
                    obj_start = -1
                    
                    # Find the opening brace of this object
                    for i in range(start_pos, -1, -1):
                        if text_stripped[i] == '{':
                            # Check if this is the start of our object
                            # (not inside a string, not part of another object)
                            obj_start = i
                            break
                    
                    if obj_start >= 0:
                        func_obj = self.extract_complete_json_object(text_stripped, obj_start)
                        if func_obj and 'function_name' in func_obj:
                            # Avoid duplicates
                            func_name = func_obj['function_name']
                            if not any(f.get('function_name') == func_name and 
                                     f.get('file_path') == func_obj.get('file_path') 
                                     for f in functions):
                                functions.append(func_obj)
            
            return functions if isinstance(functions, list) else []
            
        except Exception as e:
            self.stats['errors'].append(f"{log_file.name}: {str(e)}")
            return []
    
    def normalize_file_path(self, file_path: str) -> tuple[str, Optional[int]]:
        """Normalize file path and extract line number."""
        if not file_path:
            return "", None
        
        # Handle Windows paths
        path = file_path.replace('\\', '/')
        
        # Extract line number if present (format: "path:line")
        line_match = re.search(r':(\d+)$', path)
        line_num = None
        if line_match:
            line_num = int(line_match.group(1))
            path = path[:line_match.start()]
        
        # Normalize to relative path
        if path.startswith('scripts/'):
            pass  # Already relative
        elif '/' in path or '\\' in path:
            # Try to make relative
            parts = path.replace('\\', '/').split('/')
            if 'scripts' in parts:
                idx = parts.index('scripts')
                path = '/'.join(parts[idx:])
        
        return path, line_num
    
    def normalize_function(self, func: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """Normalize a function entry."""
        normalized = {
            'name': func.get('function_name', ''),
            'file_path': '',
            'line': None,
            'description': func.get('what_it_does', ''),
            'implementation': func.get('how_it_works', ''),
            'docstring': func.get('enhanced_docstring', ''),
            'usage_example': func.get('usage_example', ''),
            'notes': func.get('notes', []),
            'inputs': func.get('inputs', {}),
            'outputs': func.get('outputs', {}),
            'class_name': func.get('class_name'),
            'is_method': func.get('is_method', False),
            'sources': [source_file],
            'last_updated': datetime.now().isoformat()
        }
        
        # Normalize file path
        file_path = func.get('file_path', '')
        normalized['file_path'], normalized['line'] = self.normalize_file_path(file_path)
        
        # Ensure notes is a list
        if not isinstance(normalized['notes'], list):
            normalized['notes'] = [normalized['notes']] if normalized['notes'] else []
        
        return normalized
    
    def merge_functions(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two function entries, preferring more complete data."""
        merged = existing.copy()
        
        # Merge sources
        if new['sources']:
            merged['sources'].extend(new['sources'])
            merged['sources'] = list(set(merged['sources']))  # Remove duplicates
        
        # Prefer non-empty fields
        for key in ['description', 'implementation', 'docstring', 'usage_example']:
            if new.get(key) and (not merged.get(key) or len(str(new[key])) > len(str(merged.get(key, '')))):
                merged[key] = new[key]
        
        # Merge notes
        if new.get('notes'):
            merged['notes'] = list(set((merged.get('notes', []) + new.get('notes', []))))
        
        # Merge inputs/outputs if more complete
        if new.get('inputs') and isinstance(new['inputs'], dict):
            if not merged.get('inputs') or len(str(new['inputs'])) > len(str(merged.get('inputs', {}))):
                merged['inputs'] = new['inputs']
        
        if new.get('outputs') and isinstance(new['outputs'], dict):
            if not merged.get('outputs') or len(str(new['outputs'])) > len(str(merged.get('outputs', {}))):
                merged['outputs'] = new['outputs']
        
        # Update timestamp
        merged['last_updated'] = datetime.now().isoformat()
        
        return merged
    
    def build_index(self):
        """Build the function index from all log files."""
        print("Building function index from LLM io logs...")
        print("=" * 80)
        
        log_files = sorted(
            self.log_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True  # Process newest first
        )
        
        print(f"Found {len(log_files)} log files to process\n")
        
        for log_file in log_files:
            self.stats['files_processed'] += 1
            functions = self.extract_functions_from_log(log_file)
            
            if functions:
                self.stats['files_with_functions'] += 1
                self.stats['total_functions_found'] += len(functions)
                
                for func in functions:
                    func_name = func.get('function_name', '')
                    if not func_name:
                        continue
                    
                    normalized = self.normalize_function(func, log_file.name)
                    
                    # Create unique key: function_name + file_path
                    key = f"{func_name}::{normalized['file_path']}"
                    
                    if key in self.functions:
                        # Merge with existing
                        self.functions[key] = self.merge_functions(
                            self.functions[key],
                            normalized
                        )
                        self.stats['duplicates_merged'] += 1
                    else:
                        self.functions[key] = normalized
        
        self.stats['unique_functions'] = len(self.functions)
        
        print(f"\nProcessing complete!")
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  Files with functions: {self.stats['files_with_functions']}")
        print(f"  Total functions found: {self.stats['total_functions_found']}")
        print(f"  Unique functions: {self.stats['unique_functions']}")
        print(f"  Duplicates merged: {self.stats['duplicates_merged']}")
        if self.stats['errors']:
            print(f"  Errors: {len(self.stats['errors'])}")
    
    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the index."""
        stats = {
            'total_functions': len(self.functions),
            'functions_by_file': defaultdict(int),
            'functions_with_description': 0,
            'functions_with_implementation': 0,
            'functions_with_parameters': 0,
            'functions_with_examples': 0,
            'field_coverage': defaultdict(int)
        }
        
        for func in self.functions.values():
            # Count by file
            if func['file_path']:
                stats['functions_by_file'][func['file_path']] += 1
            
            # Count field coverage
            if func.get('description'):
                stats['functions_with_description'] += 1
            if func.get('implementation'):
                stats['functions_with_implementation'] += 1
            if func.get('inputs') and func['inputs'].get('parameters'):
                stats['functions_with_parameters'] += 1
            if func.get('usage_example'):
                stats['functions_with_examples'] += 1
            
            # Count all fields
            for key in func.keys():
                if func.get(key):
                    stats['field_coverage'][key] += 1
        
        return stats
    
    def save_index(self):
        """Save the index to file."""
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare output structure
        output = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'source': 'LLM io logs',
                'total_functions': len(self.functions),
                'statistics': self.generate_statistics(),
                'build_stats': self.stats
            },
            'functions': {}
        }
        
        # Organize functions by file for easier navigation
        for key, func in self.functions.items():
            file_path = func['file_path'] or 'unknown'
            if file_path not in output['functions']:
                output['functions'][file_path] = []
            
            # Create a clean entry
            entry = {
                'name': func['name'],
                'line': func['line'],
                'description': func.get('description', ''),
                'implementation': func.get('implementation', ''),
                'docstring': func.get('docstring', ''),
                'usage_example': func.get('usage_example', ''),
                'notes': func.get('notes', []),
                'inputs': func.get('inputs', {}),
                'outputs': func.get('outputs', {}),
                'class_name': func.get('class_name'),
                'is_method': func.get('is_method', False),
                'sources': func.get('sources', [])
            }
            
            output['functions'][file_path].append(entry)
        
        # Also create a flat index by function name for quick lookup
        output['index_by_name'] = {}
        for key, func in self.functions.items():
            name = func['name']
            if name not in output['index_by_name']:
                output['index_by_name'][name] = []
            output['index_by_name'][name].append({
                'file_path': func['file_path'],
                'line': func['line'],
                'key': key
            })
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\nIndex saved to: {self.output_file}")
        print(f"  Total functions indexed: {len(self.functions)}")
        
        # Print statistics
        stats = output['metadata']['statistics']
        print(f"\nIndex Statistics:")
        print(f"  Functions with description: {stats['functions_with_description']}")
        print(f"  Functions with implementation: {stats['functions_with_implementation']}")
        print(f"  Functions with parameters: {stats['functions_with_parameters']}")
        print(f"  Functions with examples: {stats['functions_with_examples']}")
        
        print(f"\nTop 10 files by function count:")
        sorted_files = sorted(
            stats['functions_by_file'].items(),
            key=lambda x: -x[1]
        )[:10]
        for file_path, count in sorted_files:
            print(f"  {file_path}: {count} functions")

def main():
    """Main entry point."""
    builder = FunctionIndexBuilder()
    builder.build_index()
    builder.save_index()
    
    print("\n" + "=" * 80)
    print("Function index build complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()

