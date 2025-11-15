"""
Scan media folders for Python virtual environments and loose scripts/documentation.
Identifies items to delete and archive.
"""

import os
from pathlib import Path
import json

# Media drive paths
MEDIA_DRIVES = ['L:', 'M:', 'Q:', 'S:', 'W:']

# Virtual environment folder names
VENV_NAMES = {'venv', '.venv', 'env', '.env', 'virtualenv', '__pycache__', '.pytest_cache', '.tox'}

# Script and documentation extensions
SCRIPT_EXTENSIONS = {'.py', '.ps1', '.sh', '.bat', '.cmd'}
DOC_EXTENSIONS = {'.md', '.txt', '.rst', '.pdf', '.docx', '.doc'}

def scan_media_folders():
    """Scan all media drives for virtual environments and loose files."""
    
    results = {
        'virtual_environments': [],
        'loose_scripts': [],
        'loose_documentation': [],
        'errors': []
    }
    
    for drive in MEDIA_DRIVES:
        if not os.path.exists(drive):
            results['errors'].append(f"Drive {drive} not accessible")
            continue
            
        print(f"\nScanning {drive}...")
        
        try:
            for root, dirs, files in os.walk(drive):
                # Check for virtual environment folders
                for dir_name in dirs[:]:  # Use slice to allow modification during iteration
                    if dir_name in VENV_NAMES:
                        venv_path = os.path.join(root, dir_name)
                        results['virtual_environments'].append(venv_path)
                        print(f"  Found venv: {venv_path}")
                        # Don't descend into venv folders
                        dirs.remove(dir_name)
                
                # Check for loose scripts and documentation in root of media folders
                # Only check top-level and show folders, not deep in season folders
                depth = root.replace(drive, '').count(os.sep)
                if depth <= 2:  # Drive root, show folder, or season folder
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        ext = os.path.splitext(file_name)[1].lower()
                        
                        if ext in SCRIPT_EXTENSIONS:
                            results['loose_scripts'].append(file_path)
                            print(f"  Found script: {file_path}")
                        elif ext in DOC_EXTENSIONS:
                            results['loose_documentation'].append(file_path)
                            print(f"  Found doc: {file_path}")
                            
        except PermissionError as e:
            results['errors'].append(f"Permission denied: {e}")
        except Exception as e:
            results['errors'].append(f"Error scanning {drive}: {e}")
    
    return results

def main():
    print("=" * 80)
    print("MEDIA FOLDER CLEANUP SCAN")
    print("=" * 80)
    
    results = scan_media_folders()
    
    # Save results
    output_file = 'scripts/media_cleanup_scan.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SCAN SUMMARY")
    print("=" * 80)
    print(f"Virtual environments found: {len(results['virtual_environments'])}")
    print(f"Loose scripts found: {len(results['loose_scripts'])}")
    print(f"Loose documentation found: {len(results['loose_documentation'])}")
    print(f"Errors encountered: {len(results['errors'])}")
    print(f"\nResults saved to: {output_file}")
    
    if results['virtual_environments']:
        print("\nVirtual Environments to Delete:")
        for venv in results['virtual_environments']:
            print(f"  - {venv}")
    
    if results['loose_scripts']:
        print("\nLoose Scripts to Archive:")
        for script in results['loose_scripts'][:10]:  # Show first 10
            print(f"  - {script}")
        if len(results['loose_scripts']) > 10:
            print(f"  ... and {len(results['loose_scripts']) - 10} more")
    
    if results['loose_documentation']:
        print("\nLoose Documentation to Archive:")
        for doc in results['loose_documentation'][:10]:  # Show first 10
            print(f"  - {doc}")
        if len(results['loose_documentation']) > 10:
            print(f"  ... and {len(results['loose_documentation']) - 10} more")

if __name__ == '__main__':
    main()
