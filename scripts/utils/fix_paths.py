#!/usr/bin/env python3
r"""
Fix Windows paths in reorganization plan.

The original plan has malformed paths like E:/MOVIES\file (mix of forward/back slashes).
This script corrects them to proper Windows paths like E:\MOVIES\file.
"""

import json
import sys
from pathlib import Path

def fix_windows_paths(plan_file: str) -> None:
    """Fix malformed Windows paths in reorganization plan."""

    # Read the plan
    with open(plan_file, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    fixed_count = 0

    # Fix paths in each result
    for result in plan:
        if 'response' in result and 'OLD:' in result['response']:
            lines = result['response'].split('\n')
            fixed_lines = []

            for line in lines:
                if line.startswith('OLD: ') or line.startswith('NEW: '):
                    # Fix the malformed path E:/MOVIES\ -> E:\MOVIES\
                    if 'E:/MOVIES\\' in line:
                        line = line.replace('E:/MOVIES\\', 'E:\\MOVIES\\')
                        fixed_count += 1
                    # Fix destination paths too
                    if 'E:/MUSIC\\' in line:
                        line = line.replace('E:/MUSIC\\', 'E:\\MUSIC\\')
                        fixed_count += 1
                    if 'E:/TV Shows\\' in line:
                        line = line.replace('E:/TV Shows\\', 'E:\\TV Shows\\')
                        fixed_count += 1
                    if 'E:/Movies\\' in line:
                        line = line.replace('E:/Movies\\', 'E:\\Movies\\')
                        fixed_count += 1

                fixed_lines.append(line)

            result['response'] = '\n'.join(fixed_lines)

    # Write back the fixed plan
    output_file = plan_file.replace('.json', '_fixed2.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"Fixed {fixed_count} malformed paths")
    print(f"Fixed plan saved to: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python fix_paths.py <plan_file>")
        sys.exit(1)

    fix_windows_paths(sys.argv[1])