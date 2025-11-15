#!/usr/bin/env python3
"""
Build comprehensive help index for JellyRancher project.

Links GUI controls to their help tooltips derived from function docstrings.
Ensures every control has proper help documentation.

This index MUST be maintained in synchronicity with:
- gui_control_index.json
- function_index.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts" / "core"))

from chroma_memory_backend import ChromaMemoryBackend


class HelpIndexBuilder:
    """Build help index from GUI controls and function docstrings."""

    def __init__(self):
        self.help_index = {}
        self.missing_help = []
        self.missing_tooltips = []

    def load_indexes(self):
        """Load existing indexes."""
        # Load GUI control index
        with open('gui_control_index.json', 'r', encoding='utf-8') as f:
            self.gui_index = json.load(f)

        # Load function index
        with open('function_index.json', 'r', encoding='utf-8') as f:
            self.function_index = json.load(f)

        print(f"[OK] Loaded GUI control index: {self.gui_index['metadata']['total_controls']} controls")
        print(f"[OK] Loaded function index: {self.function_index['metadata']['total_functions']} functions")

    def find_function_docstring(self, function_name: str, file_path: str) -> Optional[str]:
        """Find docstring for a function."""
        # Remove 'self.' prefix if present
        func_name = function_name.replace('self.', '').replace('lambda:', '').strip()

        # Skip lambdas
        if 'lambda' in func_name:
            return None

        # Search function index
        for file, functions in self.function_index['functions'].items():
            # Prefer same file, but search all files
            for func in functions:
                if func['name'] == func_name:
                    docstring = func.get('docstring', 'No documentation available')
                    if docstring and docstring != 'No documentation available':
                        return docstring

        return None

    def build_index(self):
        """Build complete help index."""
        print("\n" + "=" * 80)
        print("Building JellyRancher Help Index")
        print("=" * 80)
        print()

        # Load existing indexes
        self.load_indexes()
        print()

        # Process each GUI file
        for file_path, controls in self.gui_index['controls'].items():
            print(f"Processing: {file_path}")

            file_help = []

            for ctrl in controls:
                help_entry = {
                    'control_variable': ctrl['variable'],
                    'control_type': ctrl['type'],
                    'control_label': ctrl['label'],
                    'line': ctrl['line'],
                    'current_tooltip': ctrl['tooltip'],
                    'connected_function': ctrl['connected_function'],
                    'function_docstring': None,
                    'suggested_tooltip': None,
                    'has_help': False,
                    'needs_update': False
                }

                # Find function docstring
                if ctrl['connected_function']:
                    docstring = self.find_function_docstring(
                        ctrl['connected_function'],
                        file_path
                    )

                    if docstring:
                        help_entry['function_docstring'] = docstring
                        help_entry['has_help'] = True

                        # Generate suggested tooltip from docstring
                        # Take first line or first sentence
                        first_line = docstring.split('\n')[0].strip()
                        if len(first_line) > 100:
                            first_line = first_line[:97] + '...'

                        help_entry['suggested_tooltip'] = first_line

                        # Check if tooltip needs update
                        if not ctrl['tooltip'] or ctrl['tooltip'] != first_line:
                            help_entry['needs_update'] = True
                            self.missing_tooltips.append(help_entry)
                    else:
                        # Function has no docstring
                        self.missing_help.append(help_entry)
                else:
                    # Control has no function
                    self.missing_help.append(help_entry)

                file_help.append(help_entry)

            self.help_index[file_path] = file_help

            # Report status
            total = len(file_help)
            with_help = len([h for h in file_help if h['has_help']])
            needs_update = len([h for h in file_help if h['needs_update']])

            print(f"  -> {total} controls: {with_help} have help, {needs_update} need tooltip updates")

        # Summary
        total_controls = sum(len(helps) for helps in self.help_index.values())
        total_with_help = sum(
            len([h for h in helps if h['has_help']])
            for helps in self.help_index.values()
        )
        total_missing = len(self.missing_help)
        total_need_update = len(self.missing_tooltips)

        print()
        print("=" * 80)
        print(f"Help Index Complete: {total_controls} controls processed")
        print(f"  With Help: {total_with_help} ({100*total_with_help/total_controls:.1f}%)")
        print(f"  Missing Help: {total_missing}")
        print(f"  Need Tooltip Update: {total_need_update}")
        print("=" * 80)

        return self.help_index

    def generate_missing_help_report(self) -> str:
        """Generate report of controls missing help."""
        report = "# Controls Missing Help Documentation\n\n"

        if not self.missing_help:
            report += "OK: All controls have help documentation!\n"
            return report

        report += f"Found {len(self.missing_help)} controls missing help:\n\n"

        for entry in self.missing_help:
            report += f"## {entry['control_type']}: {entry['control_variable']}\n"
            report += f"- Label: {entry['control_label'] or 'N/A'}\n"
            report += f"- File: {entry.get('file', 'unknown')}\n"
            report += f"- Connected Function: {entry['connected_function'] or 'NONE'}\n"
            report += f"- Action Required: "

            if not entry['connected_function']:
                report += "Connect to a function\n"
            else:
                report += "Add docstring to function\n"

            report += "\n"

        return report

    def generate_tooltip_update_report(self) -> str:
        """Generate report of controls needing tooltip updates."""
        report = "# Controls Needing Tooltip Updates\n\n"

        if not self.missing_tooltips:
            report += "OK: All tooltips are up-to-date!\n"
            return report

        report += f"Found {len(self.missing_tooltips)} controls needing tooltip updates:\n\n"

        for entry in self.missing_tooltips:
            report += f"## {entry['control_type']}: {entry['control_variable']}\n"
            report += f"- Label: {entry['control_label'] or 'N/A'}\n"
            report += f"- Current Tooltip: {entry['current_tooltip'] or 'NONE'}\n"
            report += f"- Suggested Tooltip: {entry['suggested_tooltip']}\n"
            report += f"- From Function: {entry['connected_function']}\n"
            report += "\n"

        return report


def save_help_index(help_index: Dict[str, List[Dict]], output_file: str):
    """Save help index to JSON file."""
    # Calculate statistics
    total_controls = sum(len(helps) for helps in help_index.values())
    total_with_help = sum(
        len([h for h in helps if h['has_help']])
        for helps in help_index.values()
    )
    total_missing = total_controls - total_with_help
    total_need_update = sum(
        len([h for h in helps if h['needs_update']])
        for helps in help_index.values()
    )

    index_data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_files": len(help_index),
            "total_controls": total_controls,
            "total_with_help": total_with_help,
            "total_missing_help": total_missing,
            "total_need_tooltip_update": total_need_update,
            "help_coverage": f"{100*total_with_help/total_controls:.1f}%",
            "health_status": "PASS" if total_missing == 0 else "FAIL"
        },
        "help_entries": help_index
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Help index saved to {output_file}")

    # Print health report
    print("\n" + "=" * 80)
    print("HELP SYSTEM HEALTH REPORT")
    print("=" * 80)
    print(f"Total Controls: {total_controls}")
    print(f"With Help: {total_with_help} ({index_data['metadata']['help_coverage']})")
    print(f"Missing Help: {total_missing}")
    print(f"Need Tooltip Update: {total_need_update}")
    print(f"Health Status: {index_data['metadata']['health_status']}")
    print("=" * 80)

    return index_data


def store_in_chromadb(index_data: Dict, builder: HelpIndexBuilder):
    """Store help index in ChromaDB."""
    mem = ChromaMemoryBackend('./chroma_db')

    # Create comprehensive documentation
    doc_content = f"""# JellyRancher Help Index
Generated: {index_data['metadata']['generated']}
Total Files: {index_data['metadata']['total_files']}
Total Controls: {index_data['metadata']['total_controls']}
With Help: {index_data['metadata']['total_with_help']}
Missing Help: {index_data['metadata']['total_missing_help']}
Need Tooltip Update: {index_data['metadata']['total_need_tooltip_update']}
Help Coverage: {index_data['metadata']['help_coverage']}
Health Status: {index_data['metadata']['health_status']}

## Complete Help System Mapping

This index maps GUI controls to their help documentation.
It ensures every control has a tooltip derived from function docstrings.

### Integration

The help index is integrated with:
- **GUI Control Index**: Maps controls to functions
- **Function Index**: Provides function docstrings
- **Help Tooltips**: Displayed on mouse hover

When user hovers over a control, they see the help tooltip derived from
the connected function's docstring.

"""

    # Add reports
    doc_content += "\n---\n\n"
    doc_content += builder.generate_missing_help_report()
    doc_content += "\n---\n\n"
    doc_content += builder.generate_tooltip_update_report()

    # Store master index in ChromaDB
    memory_id = mem.add_memory(
        content=doc_content,
        user_id='help_indexer',
        metadata={
            'type': 'help_index',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_files': index_data['metadata']['total_files'],
            'total_controls': index_data['metadata']['total_controls'],
            'help_coverage': index_data['metadata']['help_coverage'],
            'health_status': index_data['metadata']['health_status'],
            'tags': 'help_index,help,tooltips,documentation',
            'generated': index_data['metadata']['generated']
        }
    )

    print(f"\n[OK] Help index stored in ChromaDB")
    print(f"[OK] Memory ID: {memory_id}")

    # Store individual help entries
    entries_stored = 0
    for file_path, helps in index_data['help_entries'].items():
        for help_entry in helps:
            help_content = f"""# Help Entry: {help_entry['control_variable']}

Control Type: {help_entry['control_type']}
Control Label: {help_entry['control_label'] or 'N/A'}
File: {file_path}
Line: {help_entry['line']}

## Current State
Current Tooltip: {help_entry['current_tooltip'] or 'NONE'}
Connected Function: {help_entry['connected_function'] or 'NONE'}

## Documentation
Function Docstring: {help_entry['function_docstring'] or 'NONE'}
Suggested Tooltip: {help_entry['suggested_tooltip'] or 'NONE'}

## Status
Has Help: {help_entry['has_help']}
{"OK: Help documentation complete" if help_entry['has_help'] else "WARNING: Missing help documentation"}
{"WARNING: Tooltip needs update" if help_entry['needs_update'] else ""}
"""

            mem.add_memory(
                content=help_content,
                user_id='help_indexer',
                metadata={
                    'type': 'help_entry',
                    'control_type': help_entry['control_type'],
                    'variable': help_entry['control_variable'],
                    'file': file_path,
                    'has_help': str(help_entry['has_help']),
                    'needs_update': str(help_entry['needs_update']),
                    'tags': f"help,tooltip,{help_entry['control_type']},{file_path.split('/')[0] if '/' in file_path else 'root'}"
                }
            )
            entries_stored += 1

    print(f"[OK] {entries_stored} individual help entries stored in ChromaDB")

    stats = mem.get_memory_stats()
    print(f"[INFO] Total memories in ChromaDB: {stats['total_memories']}")


if __name__ == "__main__":
    # Build index
    builder = HelpIndexBuilder()
    help_index = builder.build_index()

    # Save to JSON
    index_data = save_help_index(help_index, "help_index.json")

    # Store in ChromaDB
    print("\nStoring in ChromaDB...")
    store_in_chromadb(index_data, builder)

    # Generate reports
    print("\nGenerating reports...")
    missing_report = builder.generate_missing_help_report()
    tooltip_report = builder.generate_tooltip_update_report()

    with open("help_missing_report.txt", "w", encoding="utf-8") as f:
        f.write(missing_report)
    print("[OK] Missing help report saved to help_missing_report.txt")

    with open("help_tooltip_report.txt", "w", encoding="utf-8") as f:
        f.write(tooltip_report)
    print("[OK] Tooltip update report saved to help_tooltip_report.txt")

    print("\n" + "=" * 80)
    print("Help Index Complete!")
    print("=" * 80)
    print(f"JSON Index: help_index.json")
    print(f"ChromaDB: Searchable via semantic queries")
    print(f"Reports: help_missing_report.txt, help_tooltip_report.txt")
    print("\nExample queries:")
    print('  mem.query_memory("control help tooltip", limit=5)')
    print('  mem.query_memory("missing help documentation", limit=10)')
    print("=" * 80)
