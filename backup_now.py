#!/usr/bin/env python3
"""Quick backup script with verbose output."""

import sys
import os
import zipfile
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(r"v:\JellyRancher")
DRIVE_ROOT = Path(r"v:\")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_NAME = f"JellyRancher_backup_{TIMESTAMP}.zip"
BACKUP_PATH = DRIVE_ROOT / BACKUP_NAME

# Exclude patterns
EXCLUDE_DIRS = {'venv', '.venv', '__pycache__', '.git', 'logs', 'data', 'roundups', 'backups', 
                'gui_captures', 'archive', 'deprecated', 'old', 'node_modules', '.pytest_cache',
                'htmlcov', '.tox', '.cache', 'build', 'dist', '.idea', '.vscode'}

EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.log', '.db', '.sqlite', '.sqlite3', 
                      '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v',
                      '.srt', '.sub', '.idx', '.ass', '.ssa', '.nfo'}

log_file = PROJECT_ROOT / "backup_output.log"
with open(log_file, 'w') as log:
    log.write(f"BACKUP SCRIPT STARTING\n")
    log.write(f"Project: {PROJECT_ROOT}\n")
    log.write(f"Backup: {BACKUP_PATH}\n")
    log.write(f"Timestamp: {TIMESTAMP}\n\n")
    log.flush()

print(f"BACKUP SCRIPT STARTING")
print(f"Project: {PROJECT_ROOT}")
print(f"Backup: {BACKUP_PATH}")
print(f"Timestamp: {TIMESTAMP}")
print()

if not PROJECT_ROOT.exists():
    with open(log_file, 'a') as log:
        log.write(f"ERROR: Project root does not exist: {PROJECT_ROOT}\n")
    print(f"ERROR: Project root does not exist: {PROJECT_ROOT}")
    sys.exit(1)

file_count = 0
total_size = 0
errors = []

try:
    with zipfile.ZipFile(BACKUP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        print("Walking directory tree...")
        
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip excluded extensions
                if file_path.suffix.lower() in EXCLUDE_EXTENSIONS:
                    continue
                
                # Skip hidden files
                if file.startswith('.'):
                    continue
                
                try:
                    rel_path = file_path.relative_to(PROJECT_ROOT)
                    zipf.write(file_path, rel_path)
                    
                    file_count += 1
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    if file_count % 100 == 0:
                        print(f"  Added {file_count} files... ({total_size / 1024 / 1024:.1f} MB)")
                
                except Exception as e:
                    errors.append(f"{file_path}: {e}")
                    if len(errors) < 10:  # Only show first 10 errors
                        print(f"  Warning: {file_path}: {e}")
        
        print(f"\nCompleted adding files to archive...")
    
    # Get backup size
    if BACKUP_PATH.exists():
        backup_size = BACKUP_PATH.stat().st_size
        print()
        print("=" * 60)
        print("BACKUP COMPLETE")
        print("=" * 60)
        print(f"Backup location: {BACKUP_PATH}")
        print(f"Files included: {file_count:,}")
        print(f"Original size: {total_size / 1024 / 1024:.2f} MB")
        print(f"Compressed size: {backup_size / 1024 / 1024:.2f} MB")
        if total_size > 0:
            print(f"Compression ratio: {(1 - backup_size / total_size) * 100:.1f}%")
        if errors:
            print(f"Errors encountered: {len(errors)}")
        print("=" * 60)
        with open(log_file, 'a') as log:
            log.write(f"\n✓ SUCCESS: Backup created at {BACKUP_PATH}\n")
        print(f"\n✓ SUCCESS: Backup created at {BACKUP_PATH}")
    else:
        with open(log_file, 'a') as log:
            log.write(f"\n✗ ERROR: Backup file was not created!\n")
        print(f"\n✗ ERROR: Backup file was not created!")
        sys.exit(1)

except Exception as e:
    print(f"\n✗ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


















