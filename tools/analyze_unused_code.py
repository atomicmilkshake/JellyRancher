#!/usr/bin/env python3
"""
Analyze unused code in the JellyRancher project.
Identifies unused Python modules and evaluates their potential value.
"""

import os
import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from datetime import datetime

class CodeAnalyzer:
    def __init__(self, workspace_root: str):
        self.workspace = Path(workspace_root)
        self.all_files: List[Path] = []
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.exported_functions: Dict[str, List[str]] = {}
        self.main_scripts: List[Path] = []
        self.file_info: Dict[str, Dict] = {}
        
    def scan_files(self):
        """Scan all Python files in the workspace."""
        print(f"Scanning {self.workspace}...")
        
        for py_file in self.workspace.rglob("*.py"):
            if '__pycache__' in str(py_file) or '.venv' in str(py_file):
                continue
                
            rel_path = py_file.relative_to(self.workspace)
            self.all_files.append(py_file)
            
            # Analyze the file
            self._analyze_file(py_file, rel_path)
            
        print(f"Found {len(self.all_files)} Python files")
        
    def _analyze_file(self, file_path: Path, rel_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Basic file info
            lines = content.split('\n')
            self.file_info[str(rel_path)] = {
                'path': str(rel_path),
                'size': file_path.stat().st_size,
                'lines': len(lines),
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'has_main': '__name__ == "__main__"' in content or '__name__ == \'__main__\'' in content,
                'imports': [],
                'functions': [],
                'classes': []
            }
            
            # Parse AST
            try:
                tree = ast.parse(content)
                
                # Find imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name.split('.')[0]
                            self.imports[module_name].add(str(rel_path))
                            self.file_info[str(rel_path)]['imports'].append(alias.name)
                            
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module.split('.')[0]
                            self.imports[module_name].add(str(rel_path))
                            self.file_info[str(rel_path)]['imports'].append(node.module)
                            
                    elif isinstance(node, ast.FunctionDef):
                        if node.col_offset == 0:  # Top-level function
                            self.file_info[str(rel_path)]['functions'].append(node.name)
                            
                    elif isinstance(node, ast.ClassDef):
                        if node.col_offset == 0:  # Top-level class
                            self.file_info[str(rel_path)]['classes'].append(node.name)
                            
            except SyntaxError:
                self.file_info[str(rel_path)]['parse_error'] = True
                
            # Check if it's a main script
            if self.file_info[str(rel_path)]['has_main']:
                self.main_scripts.append(file_path)
                
        except Exception as e:
            print(f"Error analyzing {rel_path}: {e}")
            
    def find_unused_files(self) -> Dict[str, List[Dict]]:
        """Find files that are likely unused."""
        
        # Build module name to file path mapping
        file_to_module = {}
        for file_path in self.all_files:
            rel_path = file_path.relative_to(self.workspace)
            module_name = str(rel_path).replace('\\', '.').replace('/', '.').replace('.py', '')
            file_to_module[module_name] = str(rel_path)
            
            # Also check just the filename (common import pattern)
            filename = file_path.stem
            if filename not in file_to_module or len(module_name) < len(file_to_module[filename]):
                file_to_module[filename] = str(rel_path)
        
        # Categorize files
        unused = {
            'standalone_utils': [],  # Utility scripts run independently
            'orphaned_modules': [],  # Modules never imported
            'test_files': [],  # Test/debugging files
            'duplicate_locations': [],  # Files that exist in multiple places
            'cache_scripts': [],  # TV show cache builders
            'one_time_tools': []  # Scripts for specific one-time tasks
        }
        
        for rel_path, info in self.file_info.items():
            path_lower = rel_path.lower()
            
            # Skip main entry points and backends
            if any(x in rel_path for x in ['jelly_rancher_main.py', '_backend.py', '_common', 'gui_main.py']):
                continue
                
            # Categorize
            is_imported = False
            module_basename = Path(rel_path).stem
            
            # Check if this module is imported
            for imported_module in self.imports.keys():
                if module_basename in imported_module or any(module_basename in imp for imp in self.imports[imported_module]):
                    is_imported = True
                    break
                    
            # Test files
            if 'test_' in path_lower or path_lower.startswith('tests'):
                unused['test_files'].append(info)
                
            # Cache building scripts
            elif 'cache_' in path_lower and 'scripts/utils/' in rel_path:
                unused['cache_scripts'].append(info)
                
            # One-time utility scripts
            elif any(x in path_lower for x in ['fix_', 'correct_', 'cleanup_', 'validate_', 'analyze_', 'check_', 'build_', 'create_']):
                unused['one_time_tools'].append(info)
                
            # Standalone scripts with main
            elif info.get('has_main') and not is_imported:
                if 'scripts/utils/' in rel_path or 'scripts/tools/' in rel_path:
                    unused['standalone_utils'].append(info)
                    
            # Orphaned modules (no main, never imported)
            elif not info.get('has_main') and not is_imported:
                unused['orphaned_modules'].append(info)
                
        return unused
        
    def evaluate_value(self, file_info: Dict) -> Dict[str, any]:
        """Evaluate the potential value of unused code."""
        path = file_info['path']
        value_score = 0
        reasons = []
        
        # Size/complexity indicators
        if file_info['lines'] > 200:
            value_score += 2
            reasons.append(f"Substantial code ({file_info['lines']} lines)")
            
        # Has well-defined classes
        if len(file_info.get('classes', [])) > 0:
            value_score += 2
            reasons.append(f"Contains classes: {', '.join(file_info['classes'][:3])}")
            
        # Has multiple functions
        if len(file_info.get('functions', [])) > 5:
            value_score += 1
            reasons.append(f"Multiple functions ({len(file_info['functions'])})")
            
        # Recently modified
        try:
            mod_date = datetime.fromisoformat(file_info['modified'])
            days_old = (datetime.now() - mod_date).days
            if days_old < 90:
                value_score += 2
                reasons.append(f"Recently modified ({days_old} days ago)")
            elif days_old < 180:
                value_score += 1
        except:
            pass
            
        # Check for valuable patterns in filename
        valuable_keywords = ['organizer', 'workflow', 'processor', 'analyzer', 'manager', 'backend', 'interface']
        if any(kw in path.lower() for kw in valuable_keywords):
            value_score += 1
            reasons.append("Valuable naming pattern")
            
        # Has imports indicating integration
        if len(file_info.get('imports', [])) > 10:
            value_score += 1
            reasons.append(f"Well-integrated ({len(file_info['imports'])} imports)")
            
        return {
            'score': value_score,
            'reasons': reasons,
            'recommendation': self._get_recommendation(value_score)
        }
        
    def _get_recommendation(self, score: int) -> str:
        if score >= 6:
            return "HIGH VALUE - Review for integration"
        elif score >= 4:
            return "MODERATE VALUE - Consider keeping"
        elif score >= 2:
            return "LOW VALUE - Candidate for archival"
        else:
            return "MINIMAL VALUE - Safe to remove"
            
    def generate_report(self, output_file: str = "unused_code_analysis.json"):
        """Generate comprehensive analysis report."""
        unused = self.find_unused_files()
        
        report = {
            'analysis_date': datetime.now().isoformat(),
            'total_files': len(self.all_files),
            'main_scripts': [str(p.relative_to(self.workspace)) for p in self.main_scripts],
            'summary': {
                'standalone_utils': len(unused['standalone_utils']),
                'orphaned_modules': len(unused['orphaned_modules']),
                'test_files': len(unused['test_files']),
                'cache_scripts': len(unused['cache_scripts']),
                'one_time_tools': len(unused['one_time_tools'])
            },
            'high_value_unused': [],
            'categories': {}
        }
        
        # Evaluate each category
        for category, files in unused.items():
            report['categories'][category] = []
            
            for file_info in files:
                evaluation = self.evaluate_value(file_info)
                entry = {
                    **file_info,
                    'value_assessment': evaluation
                }
                report['categories'][category].append(entry)
                
                # Track high-value items
                if evaluation['score'] >= 4:
                    report['high_value_unused'].append({
                        'path': file_info['path'],
                        'category': category,
                        'score': evaluation['score'],
                        'reasons': evaluation['reasons']
                    })
                    
        # Sort high-value items by score
        report['high_value_unused'].sort(key=lambda x: x['score'], reverse=True)
        
        # Save report
        output_path = self.workspace / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nReport saved to: {output_path}")
        return report
        
    def print_summary(self, report: Dict):
        """Print a human-readable summary."""
        print("\n" + "="*80)
        print("UNUSED CODE ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"\nTotal Python files analyzed: {report['total_files']}")
        print(f"Main/Entry point scripts: {len(report['main_scripts'])}")
        
        print("\n### UNUSED CODE CATEGORIES ###")
        for category, count in report['summary'].items():
            print(f"  {category.replace('_', ' ').title()}: {count}")
            
        print(f"\n### HIGH-VALUE UNUSED CODE ({len(report['high_value_unused'])} files) ###")
        for item in report['high_value_unused'][:20]:
            print(f"\n  [{item['score']}] {item['path']}")
            print(f"      Category: {item['category']}")
            for reason in item['reasons']:
                print(f"      - {reason}")
                
        print("\n" + "="*80)


def main():
    analyzer = CodeAnalyzer("V:/JellyRancher")
    analyzer.scan_files()
    report = analyzer.generate_report()
    analyzer.print_summary(report)
    
    print("\nFull details saved to: unused_code_analysis.json")
    print("\nRecommendations:")
    print("  1. Review HIGH VALUE items for potential integration")
    print("  2. Archive MODERATE VALUE items for future reference")
    print("  3. Document and remove LOW/MINIMAL VALUE items")
    

if __name__ == "__main__":
    main()
