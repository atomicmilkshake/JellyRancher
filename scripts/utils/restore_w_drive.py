"""
Restore all W: drive files that were archived during cleanup.
"""

import os
import shutil
import json
from pathlib import Path

def restore_w_drive_files():
    """Restore all W: drive files from the archives."""
    
    # Load the cleanup report
    with open('scripts/media_cleanup_report.json', 'r') as f:
        report = json.load(f)
    
    print("=" * 80)
    print("RESTORING W: DRIVE FILES")
    print("=" * 80)
    
    restored_scripts = []
    restored_docs = []
    errors = []
    
    # Restore scripts from W: drive
    scripts_archive = Path(report['scripts_archive_location'])
    w_scripts_folder = scripts_archive / 'W'
    
    if w_scripts_folder.exists():
        print(f"\nRestoring scripts from: {w_scripts_folder}")
        for root, dirs, files in os.walk(w_scripts_folder):
            for file in files:
                src = os.path.join(root, file)
                # Reconstruct original path
                rel_path = os.path.relpath(src, w_scripts_folder)
                dest = f"W:{os.sep}{rel_path}"
                
                try:
                    # Create destination directory if needed
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)
                    restored_scripts.append(dest)
                    print(f"  ✓ Restored: {dest}")
                except Exception as e:
                    error_msg = f"Failed to restore {dest}: {e}"
                    errors.append(error_msg)
                    print(f"  ✗ {error_msg}")
    
    # Restore documentation from W: drive
    docs_archive = Path(report['docs_archive_location'])
    w_docs_folder = docs_archive / 'W'
    
    if w_docs_folder.exists():
        print(f"\nRestoring documentation from: {w_docs_folder}")
        for root, dirs, files in os.walk(w_docs_folder):
            for file in files:
                src = os.path.join(root, file)
                # Reconstruct original path
                rel_path = os.path.relpath(src, w_docs_folder)
                dest = f"W:{os.sep}{rel_path}"
                
                try:
                    # Create destination directory if needed
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)
                    restored_docs.append(dest)
                    print(f"  ✓ Restored: {dest}")
                except Exception as e:
                    error_msg = f"Failed to restore {dest}: {e}"
                    errors.append(error_msg)
                    print(f"  ✗ {error_msg}")
    
    # Summary
    print("\n" + "=" * 80)
    print("RESTORATION SUMMARY")
    print("=" * 80)
    print(f"Scripts restored: {len(restored_scripts)}")
    print(f"Documentation restored: {len(restored_docs)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ ALL W: DRIVE FILES RESTORED SUCCESSFULLY")
    
    return restored_scripts, restored_docs, errors

if __name__ == '__main__':
    restore_w_drive_files()
