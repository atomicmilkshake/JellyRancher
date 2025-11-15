#!/usr/bin/env python3
"""
Build comprehensive GUI control index for JellyRancher project.

Maps every GUI control (buttons, inputs, etc.) to their connected functions.
Prevents stub implementations by enforcing function accountability.

This index MUST be maintained in synchronicity with the function index.
"""

import ast
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts" / "core"))

from chroma_memory_backend import ChromaMemoryBackend


class GUIControlIndexer:
    """Extract GUI control to function mappings from PyQt5 code."""

    # PyQt5 control types to track
    CONTROL_TYPES = [
        'QPushButton', 'QLineEdit', 'QComboBox', 'QCheckBox',
        'QRadioButton', 'QSpinBox', 'QDoubleSpinBox', 'QTextEdit',
        'QPlainTextEdit', 'QTableWidget', 'QListWidget', 'QTreeWidget',
        'QSlider', 'QDial', 'QDateEdit', 'QTimeEdit', 'QDateTimeEdit',
        'QAction', 'QToolButton', 'QGroupBox', 'QTabWidget'
    ]

    # Signal/slot connection patterns
    SIGNAL_PATTERNS = [
        r'\.clicked\.connect\((.*?)\)',
        r'\.textChanged\.connect\((.*?)\)',
        r'\.currentIndexChanged\.connect\((.*?)\)',
        r'\.stateChanged\.connect\((.*?)\)',
        r'\.toggled\.connect\((.*?)\)',
        r'\.valueChanged\.connect\((.*?)\)',
        r'\.editingFinished\.connect\((.*?)\)',
        r'\.returnPressed\.connect\((.*?)\)',
        r'\.triggered\.connect\((.*?)\)',
        r'\.activated\.connect\((.*?)\)',
        r'\.itemClicked\.connect\((.*?)\)',
        r'\.itemDoubleClicked\.connect\((.*?)\)',
        r'\.currentChanged\.connect\((.*?)\)',
    ]

    def __init__(self):
        self.controls = {}
        self.total_files = 0
        self.total_controls = 0
        self.unconnected_controls = []

    def extract_controls_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract all GUI controls and their connections from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST for structure
            tree = ast.parse(content, filename=str(file_path))
            controls = []

            # Find control instantiations
            control_instances = self._find_control_instances(content, file_path)

            # Find connections
            connections = self._find_connections(content, file_path)

            # Match controls to their connections
            matched_controls = self._match_controls_to_connections(
                control_instances, connections, content, file_path
            )

            return matched_controls

        except Exception as e:
            print(f"[ERROR] Failed to parse {file_path}: {e}")
            return []

    def _find_control_instances(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Find all GUI control instantiations."""
        controls = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            for control_type in self.CONTROL_TYPES:
                # Pattern: variable = ControlType(...)
                # Escape the control type to avoid regex issues
                escaped_type = re.escape(control_type)
                pattern = rf'(\w+)\s*=\s*{escaped_type}\s*\('
                try:
                    matches = re.finditer(pattern, line)
                except re.error:
                    continue

                for match in matches:
                    var_name = match.group(1)

                    # Extract text/label if present
                    label = self._extract_label(line)

                    # Extract tooltip if present
                    tooltip = self._extract_tooltip(content, var_name)

                    controls.append({
                        'variable': var_name,
                        'type': control_type,
                        'label': label,
                        'tooltip': tooltip,
                        'line': line_num,
                        'file': str(file_path.relative_to(Path.cwd())),
                        'connected_function': None,
                        'is_stub': False
                    })

        return controls

    def _extract_label(self, line: str) -> Optional[str]:
        """Extract button/control label from line."""
        # Look for string literals in quotes
        try:
            # Double quotes
            match = re.search(r'"([^"]+)"', line)
            if match:
                return match.group(1)

            # Single quotes
            match = re.search(r"'([^']+)'", line)
            if match:
                return match.group(1)
        except re.error:
            pass

        return None

    def _extract_tooltip(self, content: str, var_name: str) -> Optional[str]:
        """Extract tooltip for a control variable."""
        # Look for setToolTip calls
        # Escape var_name to avoid regex issues with special characters
        escaped_var = re.escape(var_name)
        pattern = rf'{escaped_var}\.setToolTip\(["\']([^"\']+)["\']\)'
        try:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        except re.error:
            # Regex pattern error - skip this tooltip
            pass
        return None

    def _find_connections(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Find all signal/slot connections."""
        connections = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            for pattern in self.SIGNAL_PATTERNS:
                try:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        function_name = match.group(1).strip()

                        # Extract variable name (before the signal)
                        var_match = re.search(r'(\w+)\.\w+\.connect', line)
                        if var_match:
                            var_name = var_match.group(1)

                            connections.append({
                                'variable': var_name,
                                'function': function_name,
                                'line': line_num,
                                'signal': match.group(0)
                            })
                except re.error:
                    # Skip lines that cause regex errors
                    continue

        return connections

    def _match_controls_to_connections(
        self,
        controls: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        content: str,
        file_path: Path
    ) -> List[Dict[str, Any]]:
        """Match controls to their connected functions."""
        matched = []

        for control in controls:
            # Find matching connection
            connection = next(
                (c for c in connections if c['variable'] == control['variable']),
                None
            )

            if connection:
                control['connected_function'] = connection['function']
                control['signal'] = connection['signal']
                control['connection_line'] = connection['line']

                # Check if function is a stub
                control['is_stub'] = self._is_stub_function(
                    content, connection['function']
                )
            else:
                # Control has no connection - potential issue
                control['connected_function'] = None
                control['is_stub'] = False
                self.unconnected_controls.append(control)

            matched.append(control)

        return matched

    def _is_stub_function(self, content: str, function_name: str) -> bool:
        """Check if a function is a stub implementation."""
        # Remove 'self.' prefix if present
        func_name = function_name.replace('self.', '')

        # Escape function name to avoid regex issues
        escaped_func = re.escape(func_name)

        # Look for function definition
        func_pattern = rf'def {escaped_func}\s*\([^)]*\):'
        try:
            match = re.search(func_pattern, content)

            if match:
                # Get the function body (next few lines)
                start_pos = match.end()
                func_body = content[start_pos:start_pos+500]

                # Check for stub indicators using word boundaries
                # This prevents matching "pass" in "password", etc.
                stub_patterns = [
                    r'\bpass\b',  # Python pass keyword (word boundary)
                    r'\bNotImplementedError\b',
                    r'\bTODO\b',
                    r'\bSTUB\b',
                    r'raise\s+NotImplemented',
                    r'#\s*stub\b',
                    r'#\s*TODO\b',
                    r'#\s*placeholder\b'
                ]

                for pattern in stub_patterns:
                    if re.search(pattern, func_body, re.IGNORECASE):
                        return True
        except re.error:
            # If regex fails, assume not a stub
            pass

        return False

    def scan_gui_files(self) -> List[Path]:
        """Find all GUI-related Python files."""
        gui_patterns = [
            'scripts/core/*.py',
            'scripts/core/dialogs/*.py',
            'scripts/tools/*/gui*.py',
            'scripts/tools/*/*/*gui*.py',
        ]

        gui_files = []
        project_root = Path.cwd()

        for pattern in gui_patterns:
            for file_path in project_root.glob(pattern):
                if file_path.is_file():
                    gui_files.append(file_path)

        return sorted(set(gui_files))

    def build_index(self):
        """Build complete GUI control index."""
        print("=" * 80)
        print("Building JellyRancher GUI Control Index")
        print("=" * 80)
        print()

        # Scan for GUI files
        gui_files = self.scan_gui_files()
        print(f"Found {len(gui_files)} GUI files to analyze")
        print()

        # Extract controls from each file
        for file_path in gui_files:
            print(f"Analyzing: {file_path.relative_to(Path.cwd())}")
            controls = self.extract_controls_from_file(file_path)

            if controls:
                file_key = str(file_path.relative_to(Path.cwd()))
                self.controls[file_key] = controls
                self.total_controls += len(controls)

                # Count stubs and unconnected
                stubs = [c for c in controls if c['is_stub']]
                unconnected = [c for c in controls if c['connected_function'] is None]

                print(f"  -> Found {len(controls)} controls")
                if stubs:
                    print(f"     WARNING: {len(stubs)} stub implementations detected!")
                if unconnected:
                    print(f"     WARNING: {len(unconnected)} unconnected controls!")

            self.total_files += 1

        print()
        print("=" * 80)
        print(f"Index Complete: {self.total_controls} controls in {self.total_files} files")

        # Report issues
        total_stubs = sum(
            len([c for c in controls if c['is_stub']])
            for controls in self.controls.values()
        )
        total_unconnected = len(self.unconnected_controls)

        if total_stubs > 0:
            print(f"WARNING: {total_stubs} STUB IMPLEMENTATIONS FOUND!")
        if total_unconnected > 0:
            print(f"WARNING: {total_unconnected} UNCONNECTED CONTROLS FOUND!")

        print("=" * 80)

        return self.controls


def save_gui_control_index(controls: Dict[str, List[Dict]], output_file: str):
    """Save GUI control index to JSON file."""
    # Calculate statistics
    total_controls = sum(len(ctrls) for ctrls in controls.values())
    total_stubs = sum(
        len([c for c in ctrls if c['is_stub']])
        for ctrls in controls.values()
    )
    total_unconnected = sum(
        len([c for c in ctrls if c['connected_function'] is None])
        for ctrls in controls.values()
    )
    total_connected = total_controls - total_unconnected

    index_data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_files": len(controls),
            "total_controls": total_controls,
            "total_connected": total_connected,
            "total_unconnected": total_unconnected,
            "total_stubs": total_stubs,
            "health_status": "FAIL" if (total_stubs > 0 or total_unconnected > 0) else "PASS"
        },
        "controls": controls
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] GUI control index saved to {output_file}")

    # Print health report
    print("\n" + "=" * 80)
    print("GUI CONTROL HEALTH REPORT")
    print("=" * 80)
    print(f"Total Controls: {total_controls}")
    print(f"Connected: {total_connected} ({100*total_connected/total_controls:.1f}%)")
    print(f"Unconnected: {total_unconnected}")
    print(f"Stub Implementations: {total_stubs}")
    print(f"Health Status: {index_data['metadata']['health_status']}")
    print("=" * 80)

    return index_data


def store_in_chromadb(index_data: Dict):
    """Store GUI control index in ChromaDB."""
    mem = ChromaMemoryBackend('./chroma_db')

    # Create comprehensive documentation
    doc_content = f"""# JellyRancher GUI Control Index
Generated: {index_data['metadata']['generated']}
Total Files: {index_data['metadata']['total_files']}
Total Controls: {index_data['metadata']['total_controls']}
Connected Controls: {index_data['metadata']['total_connected']}
Unconnected Controls: {index_data['metadata']['total_unconnected']}
Stub Implementations: {index_data['metadata']['total_stubs']}
Health Status: {index_data['metadata']['health_status']}

## Complete GUI Control Mapping

This index maps every GUI control to its connected function.
It prevents stub implementations by enforcing function accountability.

"""

    # Organize by file
    for file_path, controls in sorted(index_data['controls'].items()):
        doc_content += f"\n### File: {file_path}\n\n"

        for ctrl in controls:
            doc_content += f"#### {ctrl['type']}: `{ctrl['variable']}`\n\n"
            doc_content += f"**Location**: Line {ctrl['line']}\n\n"

            if ctrl['label']:
                doc_content += f"**Label**: \"{ctrl['label']}\"\n\n"

            if ctrl['tooltip']:
                doc_content += f"**Tooltip**: \"{ctrl['tooltip']}\"\n\n"

            if ctrl['connected_function']:
                doc_content += f"**Connected Function**: `{ctrl['connected_function']}`\n\n"
                doc_content += f"**Connection Line**: {ctrl['connection_line']}\n\n"

                if ctrl['is_stub']:
                    doc_content += "**WARNING**: This is a STUB implementation!\n\n"
            else:
                doc_content += "**WARNING**: NO FUNCTION CONNECTED!\n\n"

            doc_content += "---\n\n"

    # Store master index in ChromaDB
    memory_id = mem.add_memory(
        content=doc_content,
        user_id='gui_control_indexer',
        metadata={
            'type': 'gui_control_index',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_files': index_data['metadata']['total_files'],
            'total_controls': index_data['metadata']['total_controls'],
            'total_stubs': index_data['metadata']['total_stubs'],
            'health_status': index_data['metadata']['health_status'],
            'tags': 'gui_control_index,gui,controls,accountability',
            'generated': index_data['metadata']['generated']
        }
    )

    print(f"\n[OK] GUI control index stored in ChromaDB")
    print(f"[OK] Memory ID: {memory_id}")

    # Store individual control entries
    controls_stored = 0
    for file_path, controls in index_data['controls'].items():
        for ctrl in controls:
            ctrl_content = f"""# GUI Control: {ctrl['variable']}

Type: {ctrl['type']}
File: {file_path}
Line: {ctrl['line']}
Label: {ctrl['label'] or 'N/A'}
Tooltip: {ctrl['tooltip'] or 'N/A'}

## Connection
Connected Function: {ctrl['connected_function'] or 'NONE - UNCONNECTED!'}
{"Connection Line: " + str(ctrl.get('connection_line', '')) if ctrl['connected_function'] else ''}

## Status
{"WARNING: STUB IMPLEMENTATION DETECTED!" if ctrl['is_stub'] else ''}
{"WARNING: NO FUNCTION CONNECTED!" if not ctrl['connected_function'] else ''}
{"OK: Properly connected" if ctrl['connected_function'] and not ctrl['is_stub'] else ''}
"""

            mem.add_memory(
                content=ctrl_content,
                user_id='gui_control_indexer',
                metadata={
                    'type': 'gui_control',
                    'control_type': ctrl['type'],
                    'variable': ctrl['variable'],
                    'file': file_path,
                    'line': str(ctrl['line']),
                    'connected_function': ctrl['connected_function'] or 'none',
                    'is_stub': str(ctrl['is_stub']),
                    'has_connection': str(bool(ctrl['connected_function'])),
                    'tags': f"gui,control,{ctrl['type']},{file_path.split('/')[0] if '/' in file_path else 'root'}"
                }
            )
            controls_stored += 1

    print(f"[OK] {controls_stored} individual control entries stored in ChromaDB")

    stats = mem.get_memory_stats()
    print(f"[INFO] Total memories in ChromaDB: {stats['total_memories']}")


if __name__ == "__main__":
    # Build index
    indexer = GUIControlIndexer()
    controls = indexer.build_index()

    # Save to JSON
    index_data = save_gui_control_index(controls, "gui_control_index.json")

    # Store in ChromaDB
    print("\nStoring in ChromaDB...")
    store_in_chromadb(index_data)

    print("\n" + "=" * 80)
    print("GUI Control Index Complete!")
    print("=" * 80)
    print(f"JSON Index: gui_control_index.json")
    print(f"ChromaDB: Searchable via semantic queries")
    print("\nExample queries:")
    print('  mem.query_memory("button connect function", limit=5)')
    print('  mem.query_memory("unconnected controls stub", limit=10)')
    print("=" * 80)
