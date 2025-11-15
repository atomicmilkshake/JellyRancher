"""
Execute cleanup of media folders:
1. Delete Python virtual environments
2. Archive loose scripts and documentation to "early development files"
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def load_scan_results():
    """Load the scan results."""
    with open('scripts/media_cleanup_scan.json', 'r') as f:
        return json.load(f)

def delete_virtual_environments(venvs):
    """Delete all virtual environment folders."""
    print("\n" + "=" * 80)
    print("DELETING VIRTUAL ENVIRONMENTS")
    print("=" * 80)
    
    deleted = []
    errors = []
    
    for venv_path in venvs:
        try:
            if os.path.exists(venv_path):
                print(f"Deleting: {venv_path}")
                shutil.rmtree(venv_path)
                deleted.append(venv_path)
                print(f"  ✓ Deleted successfully")
            else:
                print(f"  ⚠ Path not found: {venv_path}")
        except Exception as e:
            error_msg = f"Failed to delete {venv_path}: {e}"
            errors.append(error_msg)
            print(f"  ✗ {error_msg}")
    
    return deleted, errors

def archive_files(files, archive_type):
    """Archive files to early development files folder."""
    print("\n" + "=" * 80)
    print(f"ARCHIVING {archive_type.upper()}")
    print("=" * 80)
    
    # Create archive folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_base = Path("early development files")
    archive_folder = archive_base / f"media_cleanup_{archive_type}_{timestamp}"
    archive_folder.mkdir(parents=True, exist_ok=True)
    
    archived = []
    errors = []
    
    for file_path in files:
        try:
            if os.path.exists(file_path):
                # Create relative path structure in archive
                # Extract drive letter and relative path
                if ':' in file_path:
                    drive, rel_path = file_path.split(':', 1)
                    # Clean up the path
                    rel_path = rel_path.lstrip('\\').lstrip('/')
                    
                    # Create destination path
                    dest_folder = archive_folder / drive / os.path.dirname(rel_path)
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    
                    dest_file = dest_folder / os.path.basename(file_path)
                    
                    print(f"Archiving: {file_path}")
                    print(f"       to: {dest_file}")
                    
                    shutil.copy2(file_path, dest_file)
                    archived.append(file_path)
                    print(f"  ✓ Archived successfully")
                    
                    # Delete original after successful archive
                    os.remove(file_path)
                    print(f"  ✓ Original deleted")
                else:
                    print(f"  ⚠ Skipping (no drive letter): {file_path}")
            else:
                print(f"  ⚠ File not found: {file_path}")
        except Exception as e:
            error_msg = f"Failed to archive {file_path}: {e}"
            errors.append(error_msg)
            print(f"  ✗ {error_msg}")
    
    return archived, errors, str(archive_folder)

def main():
    print("=" * 80)
    print("MEDIA FOLDER CLEANUP EXECUTION")
    print("=" * 80)
    
    # Load scan results
    results = load_scan_results()
    
    # Delete virtual environments
    deleted_venvs, venv_errors = delete_virtual_environments(results['virtual_environments'])
    
    # Archive scripts
    archived_scripts, script_errors, scripts_archive = archive_files(
        results['loose_scripts'], 
        'scripts'
    )
    
    # Archive documentation
    archived_docs, doc_errors, docs_archive = archive_files(
        results['loose_documentation'], 
        'documentation'
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Virtual environments deleted: {len(deleted_venvs)}/{len(results['virtual_environments'])}")
    print(f"Scripts archived: {len(archived_scripts)}/{len(results['loose_scripts'])}")
    print(f"Documentation archived: {len(archived_docs)}/{len(results['loose_documentation'])}")
    print(f"\nTotal errors: {len(venv_errors) + len(script_errors) + len(doc_errors)}")
    
    if scripts_archive:
        print(f"\nScripts archived to: {scripts_archive}")
    if docs_archive:
        print(f"Documentation archived to: {docs_archive}")
    
    # Save cleanup report
    report = {
        'timestamp': datetime.now().isoformat(),
        'deleted_venvs': deleted_venvs,
        'archived_scripts': archived_scripts,
        'archived_docs': archived_docs,
        'scripts_archive_location': scripts_archive if archived_scripts else None,
        'docs_archive_location': docs_archive if archived_docs else None,
        'errors': {
            'venv_errors': venv_errors,
            'script_errors': script_errors,
            'doc_errors': doc_errors
        }
    }
    
    report_file = 'scripts/media_cleanup_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nCleanup report saved to: {report_file}")
    
    if venv_errors or script_errors or doc_errors:
        print("\n⚠ ERRORS OCCURRED - Check report for details")
    else:
        print("\n✓ CLEANUP COMPLETED SUCCESSFULLY")

if __name__ == '__main__':
    main()
