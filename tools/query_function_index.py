#!/usr/bin/env python3
"""Query and search the LLM function index."""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

class FunctionIndexQuery:
    """Query interface for the function index."""
    
    def __init__(self, index_file: str = "data/llm_function_index.json"):
        self.index_file = Path(index_file)
        if not self.index_file.exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")
        
        with open(self.index_file, 'r', encoding='utf-8') as f:
            self.index = json.load(f)
        
        self.functions = self.index.get('functions', {})
        self.index_by_name = self.index.get('index_by_name', {})
        self.metadata = self.index.get('metadata', {})
    
    def search_by_name(self, name: str, exact: bool = False) -> List[Dict[str, Any]]:
        """Search for functions by name."""
        results = []
        name_lower = name.lower()
        
        for func_name, occurrences in self.index_by_name.items():
            if exact:
                if func_name.lower() == name_lower:
                    for occ in occurrences:
                        file_path = occ['file_path']
                        line = occ['line']
                        # Get full function data
                        funcs = self.functions.get(file_path, [])
                        for func in funcs:
                            if func['name'] == func_name and func.get('line') == line:
                                results.append(func)
            else:
                if name_lower in func_name.lower():
                    for occ in occurrences:
                        file_path = occ['file_path']
                        line = occ['line']
                        funcs = self.functions.get(file_path, [])
                        for func in funcs:
                            if func['name'] == func_name and func.get('line') == line:
                                results.append(func)
        
        return results
    
    def search_by_description(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for functions by keyword in description."""
        results = []
        keyword_lower = keyword.lower()
        
        for file_path, funcs in self.functions.items():
            for func in funcs:
                description = func.get('description', '').lower()
                implementation = func.get('implementation', '').lower()
                if keyword_lower in description or keyword_lower in implementation:
                    results.append(func)
        
        return results
    
    def search_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all functions in a file."""
        # Try exact match first
        if file_path in self.functions:
            return self.functions[file_path]
        
        # Try partial match
        results = []
        file_path_lower = file_path.lower()
        for path, funcs in self.functions.items():
            if file_path_lower in path.lower():
                results.extend(funcs)
        
        return results
    
    def search_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Search for functions by capability/keyword."""
        results = []
        capability_lower = capability.lower()
        
        for file_path, funcs in self.functions.items():
            for func in funcs:
                # Search in description, implementation, notes
                text = ' '.join([
                    func.get('description', ''),
                    func.get('implementation', ''),
                    ' '.join(func.get('notes', []))
                ]).lower()
                
                if capability_lower in text:
                    results.append(func)
        
        return results
    
    def get_function_details(self, name: str, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific function."""
        if file_path:
            funcs = self.functions.get(file_path, [])
            for func in funcs:
                if func['name'] == name:
                    return func
        else:
            # Search all files
            for path, funcs in self.functions.items():
                for func in funcs:
                    if func['name'] == name:
                        return func
        
        return None
    
    def list_all_functions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all functions in the index."""
        results = []
        count = 0
        
        for file_path, funcs in self.functions.items():
            for func in funcs:
                results.append({
                    'name': func['name'],
                    'file_path': file_path,
                    'line': func.get('line'),
                    'description': func.get('description', '')[:100] + '...' if len(func.get('description', '')) > 100 else func.get('description', '')
                })
                count += 1
                if limit and count >= limit:
                    return results
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        return self.metadata.get('statistics', {})
    
    def print_function(self, func: Dict[str, Any], file_path: str = ""):
        """Pretty print a function."""
        print("=" * 80)
        print(f"Function: {func['name']}")
        if file_path:
            print(f"File: {file_path}")
        elif func.get('file_path'):
            print(f"File: {func['file_path']}")
        if func.get('line'):
            print(f"Line: {func['line']}")
        if func.get('class_name'):
            print(f"Class: {func['class_name']}")
        print()
        
        if func.get('description'):
            print("Description:")
            print(f"  {func['description']}")
            print()
        
        if func.get('implementation'):
            print("Implementation:")
            print(f"  {func['implementation'][:500]}{'...' if len(func['implementation']) > 500 else ''}")
            print()
        
        if func.get('inputs'):
            inputs = func['inputs']
            if inputs.get('parameters'):
                print("Parameters:")
                for param in inputs['parameters']:
                    req = "required" if param.get('required', False) else "optional"
                    param_type = param.get('type', 'Any')
                    print(f"  {param['name']}: {param_type} ({req})")
                    if param.get('description'):
                        print(f"    {param['description']}")
                print()
        
        if func.get('outputs'):
            outputs = func['outputs']
            if outputs.get('return_value'):
                ret = outputs['return_value']
                print("Returns:")
                print(f"  {ret.get('type', 'Any')}")
                if ret.get('description'):
                    print(f"    {ret['description']}")
                print()
        
        if func.get('usage_example'):
            print("Usage Example:")
            print(f"  {func['usage_example']}")
            print()
        
        if func.get('notes'):
            print("Notes:")
            for note in func['notes']:
                print(f"  - {note}")
            print()

def main():
    """CLI interface for querying the index."""
    parser = argparse.ArgumentParser(description='Query the LLM function index')
    parser.add_argument('--index', default='data/llm_function_index.json',
                       help='Path to index file')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search by name
    search_name = subparsers.add_parser('name', help='Search by function name')
    search_name.add_argument('name', help='Function name (supports partial match)')
    search_name.add_argument('--exact', action='store_true', help='Exact match only')
    search_name.add_argument('--details', action='store_true', help='Show full details')
    
    # Search by description
    search_desc = subparsers.add_parser('description', help='Search by description keyword')
    search_desc.add_argument('keyword', help='Keyword to search for')
    search_desc.add_argument('--details', action='store_true', help='Show full details')
    
    # Search by file
    search_file = subparsers.add_parser('file', help='List functions in a file')
    search_file.add_argument('file_path', help='File path (supports partial match)')
    search_file.add_argument('--details', action='store_true', help='Show full details')
    
    # Search by capability
    search_cap = subparsers.add_parser('capability', help='Search by capability/keyword')
    search_cap.add_argument('capability', help='Capability or keyword')
    search_cap.add_argument('--details', action='store_true', help='Show full details')
    
    # List all
    list_all = subparsers.add_parser('list', help='List all functions')
    list_all.add_argument('--limit', type=int, help='Limit number of results')
    
    # Statistics
    stats = subparsers.add_parser('stats', help='Show index statistics')
    
    # Get function details
    get_func = subparsers.add_parser('get', help='Get detailed info about a function')
    get_func.add_argument('name', help='Function name')
    get_func.add_argument('--file', help='File path (optional, for disambiguation)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        query = FunctionIndexQuery(args.index)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.command == 'name':
        results = query.search_by_name(args.name, exact=args.exact)
        print(f"Found {len(results)} function(s) matching '{args.name}':\n")
        for func in results:
            if args.details:
                query.print_function(func)
            else:
                file_path = func.get('file_path', 'unknown')
                line = func.get('line', '?')
                print(f"  {func['name']} in {file_path}:{line}")
                if func.get('description'):
                    desc = func['description'][:100] + '...' if len(func['description']) > 100 else func['description']
                    print(f"    {desc}")
                print()
    
    elif args.command == 'description':
        results = query.search_by_description(args.keyword)
        print(f"Found {len(results)} function(s) matching '{args.keyword}':\n")
        for func in results:
            if args.details:
                query.print_function(func)
            else:
                file_path = func.get('file_path', 'unknown')
                line = func.get('line', '?')
                print(f"  {func['name']} in {file_path}:{line}")
                if func.get('description'):
                    desc = func['description'][:100] + '...' if len(func['description']) > 100 else func['description']
                    print(f"    {desc}")
                print()
    
    elif args.command == 'file':
        results = query.search_by_file(args.file_path)
        print(f"Found {len(results)} function(s) in '{args.file_path}':\n")
        for func in results:
            if args.details:
                query.print_function(func, args.file_path)
            else:
                line = func.get('line', '?')
                print(f"  {func['name']} (line {line})")
                if func.get('description'):
                    desc = func['description'][:100] + '...' if len(func['description']) > 100 else func['description']
                    print(f"    {desc}")
                print()
    
    elif args.command == 'capability':
        results = query.search_by_capability(args.capability)
        print(f"Found {len(results)} function(s) matching capability '{args.capability}':\n")
        for func in results:
            if args.details:
                query.print_function(func)
            else:
                file_path = func.get('file_path', 'unknown')
                line = func.get('line', '?')
                print(f"  {func['name']} in {file_path}:{line}")
                if func.get('description'):
                    desc = func['description'][:100] + '...' if len(func['description']) > 100 else func['description']
                    print(f"    {desc}")
                print()
    
    elif args.command == 'list':
        results = query.list_all_functions(limit=args.limit)
        print(f"Total functions: {len(results)}\n")
        for func in results:
            file_path = func.get('file_path', 'unknown')
            line = func.get('line', '?')
            print(f"  {func['name']} in {file_path}:{line}")
    
    elif args.command == 'stats':
        stats = query.get_statistics()
        print("Index Statistics:")
        print(f"  Total functions: {stats.get('total_functions', 0)}")
        print(f"  Functions with description: {stats.get('functions_with_description', 0)}")
        print(f"  Functions with implementation: {stats.get('functions_with_implementation', 0)}")
        print(f"  Functions with parameters: {stats.get('functions_with_parameters', 0)}")
        print(f"  Functions with examples: {stats.get('functions_with_examples', 0)}")
        print(f"\n  Files indexed: {len(query.functions)}")
        print(f"  Unique function names: {len(query.index_by_name)}")
    
    elif args.command == 'get':
        func = query.get_function_details(args.name, args.file)
        if func:
            query.print_function(func, args.file or func.get('file_path', ''))
        else:
            print(f"Function '{args.name}' not found")
            if args.file:
                print(f"  (searched in {args.file})")
            else:
                print("  (searched in all files)")

if __name__ == "__main__":
    main()

