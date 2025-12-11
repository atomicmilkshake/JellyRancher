#!/usr/bin/env python3
"""
Create a dated, compressed backup of the JellyRancher codebase.

Creates a zip file in the drive root (v:\) excluding:
- venv/.venv
- __pycache__
- .git
- logs/
- data/
- roundups/
- backups/
- And other patterns from .gitignore
"""

import sys
import os
import zipfile
from pathlib import Path
from datetime import datetime
import fnmatch

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DRIVE_ROOT = Path(PROJECT_ROOT.drive + "\\")

# Backup filename with timestamp
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_NAME = f"JellyRancher_backup_{TIMESTAMP}.zip"
BACKUP_PATH = DRIVE_ROOT / BACKUP_NAME

# Patterns to exclude (from .gitignore)
EXCLUDE_PATTERNS = [
    # Python
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    "build/",
    "dist/",
    "*.egg-info",
    "*.egg",
    
    # Virtual environments
    "venv/",
    ".venv/",
    "ENV/",
    "env/",
    ".env",
    
    # IDE
    ".vscode/",
    ".idea/",
    "*.iml",
    "*.sublime-*",
    "*.swp",
    "*.swo",
    
    # OS
    ".DS_Store",
    "Thumbs.db",
    "Desktop.ini",
    "$RECYCLE.BIN/",
    
    # Project specific
    "*.roundup/",
    "roundups/",
    "data/",
    "logs/",
    "backups/",
    "pre_rename_archive/",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.log",
    "temp/",
    "tmp/",
    "*.tmp",
    "analysis_results/",
    "scan_results/",
    "jellyfin_cache/",
    ".llm_cache/",
    "anthropic_cache/",
    "LLM_io_log/",
    
    # Media files
    "*.mkv",
    "*.mp4",
    "*.avi",
    "*.mov",
    "*.wmv",
    "*.flv",
    "*.webm",
    "*.m4v",
    "*.srt",
    "*.sub",
    "*.idx",
    "*.ass",
    "*.ssa",
    "*.nfo",
    
    # Build
    "build/",
    "dist/",
    "*.exe",
    "*.app",
    
    # Archive
    "archive/",
    "deprecated/",
    "old/",
    
    # Git
    ".git/",
    ".gitignore",
    
    # Coverage
    ".coverage",
    "htmlcov/",
    ".pytest_cache/",
    ".tox/",
    ".cache/",
    
    # Node
    "node_modules/",
    
    # GUI captures (can be large)
    "gui_captures/",
]

def should_exclude(file_path: Path, project_root: Path) -> bool:
    """Check if a file should be excluded from backup."""
    # Get relative path from project root
    try:
        rel_path = file_path.relative_to(project_root)
    except ValueError:
        # File is outside project root, exclude
        return True
    
    rel_str = str(rel_path).replace("\\", "/")
    
    # Check against exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            pattern_dir = pattern.rstrip("/")
            if rel_str.startswith(pattern_dir + "/") or rel_str == pattern_dir:
                return True
        # Handle wildcard patterns
        elif "*" in pattern:
            if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True
        # Exact match
        else:
            if rel_str == pattern or rel_str.startswith(pattern + "/"):
                return True
    
    # Exclude hidden files/directories (except .gitignore which we want)
    if rel_path.name.startswith(".") and rel_path.name != ".gitignore":
        return True
    
    return False

def create_backup():
    """Create the backup zip file."""
    print(f"Creating backup: {BACKUP_PATH}", flush=True)
    print(f"Source: {PROJECT_ROOT}", flush=True)
    print(f"Excluding: venv, .venv, logs, data, roundups, backups, and other patterns from .gitignore", flush=True)
    print(flush=True)
    
    file_count = 0
    total_size = 0
    
    with zipfile.ZipFile(BACKUP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        # Walk through project directory
        for root, dirs, files in os.walk(PROJECT_ROOT):
            root_path = Path(root)
            
            # Filter out excluded directories before descending
            dirs[:] = [d for d in dirs if not should_exclude(root_path / d, PROJECT_ROOT)]
            
            for file in files:
                file_path = root_path / file
                
                # Skip excluded files
                if should_exclude(file_path, PROJECT_ROOT):
                    continue
                
                try:
                    # Get relative path for archive
                    arcname = file_path.relative_to(PROJECT_ROOT)
                    
                    # Add to zip
                    zipf.write(file_path, arcname)
                    
                    file_count += 1
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    if file_count % 100 == 0:
                        print(f"  Added {file_count} files... ({total_size / 1024 / 1024:.1f} MB)", flush=True)
                
                except Exception as e:
                    print(f"  Warning: Could not add {file_path}: {e}", flush=True)
                    continue
    
    # Get final backup size
    backup_size = BACKUP_PATH.stat().st_size
    
    print(flush=True)
    print("=" * 60, flush=True)
    print("BACKUP COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"Backup location: {BACKUP_PATH}", flush=True)
    print(f"Files included: {file_count:,}", flush=True)
    print(f"Original size: {total_size / 1024 / 1024:.2f} MB", flush=True)
    print(f"Compressed size: {backup_size / 1024 / 1024:.2f} MB", flush=True)
    if total_size > 0:
        print(f"Compression ratio: {(1 - backup_size / total_size) * 100:.1f}%", flush=True)
    print("=" * 60, flush=True)
    
    return BACKUP_PATH

if __name__ == "__main__":
    status_file = PROJECT_ROOT / "backup_status.txt"
    try:
        with open(status_file, 'w') as f:
            f.write(f"Starting backup at {datetime.now()}\n")
            f.write(f"Target: {BACKUP_PATH}\n")
            f.flush()
        
        backup_path = create_backup()
        
        with open(status_file, 'a') as f:
            f.write(f"\n✓ Backup created successfully: {backup_path}\n")
            f.write(f"File exists: {backup_path.exists()}\n")
            if backup_path.exists():
                f.write(f"File size: {backup_path.stat().st_size / 1024 / 1024:.2f} MB\n")
        
        print(f"\n✓ Backup created successfully: {backup_path}")
        sys.exit(0)
    except Exception as e:
        with open(status_file, 'a') as f:
            f.write(f"\n✗ Backup failed: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        print(f"\n✗ Backup failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)



















