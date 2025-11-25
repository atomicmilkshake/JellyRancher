import os
import zipfile
import datetime
import glob

def is_excluded(path):
    """Check if a file should be excluded from core backup."""
    exclude_patterns = [
        '.git',
        '.claude',
        'test_media',
        'gui_captures',
        'CTemp',
        'scripts/_archived',
        'scripts/_common',  # Contains some utils but can be regenerated if core scripts are there
        '__pycache__',
        '*.pyc',
        'venv',
        '.venv',
        'node_modules',
        'backups',
        'tools/ravenmaven',  # Subproject, large and archived
    ]
    path_lower = path.lower()
    return any(ex in path_lower for ex in exclude_patterns)

def create_core_backup():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    zip_path = os.path.join(backup_dir, f"core_backup_{timestamp}.zip")
    
    print(f"Creating CORE backup: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add README at root
        readme_content = f"""CORE Backup Script Output
========================

This is a minimal "CORE" backup containing ONLY the VERY IMPORTANT files essential for project recovery and core functionality.

Included:
- All Python source files (.py) from root, scripts/, tools/, tests/
- Key configuration files: pytest.ini, requirements.txt files
- Critical JSON data: function_index*.json, gui_runtime_state.json
- Essential documentation: root *.md files (plans, prompts, consolidated docs)

EXCLUDED (to keep backup small):
- Git repo (.git/)
- Test media (test_media/ - large sample data)
- Captures and temps (gui_captures/, C:\Temp/)
- Archived code (scripts/_archived/)
- Subprojects and tools outputs (tools/ravenmaven/, backups/)
- Cache, pyc, venvs, etc.

Backup created: {datetime.datetime.now().isoformat()}
Total files included: (logged below)

Files added:
"""
        zf.writestr("README.txt", readme_content)
        
        # Collect and add core files
        core_patterns = [
            "**/*.py",
            "**/requirements.txt",
            "**/*.json",  # But will filter to only important
            "pytest.ini",
            "*.md",  # Root docs
            "scripts/**/*.md",  # Scripts docs if any
        ]
        
        added_count = 0
        added_files = []
        
        for pattern in core_patterns:
            for filepath in glob.glob(pattern, recursive=True):
                if not os.path.isfile(filepath):
                    continue
                
                # Specific include for key JSONs
                if filepath.endswith('.json'):
                    if not any(key in filepath for key in ['function_index', 'gui_runtime_state']):
                        continue
                
                if is_excluded(filepath):
                    continue
                
                arcname = os.path.relpath(filepath, os.getcwd())
                zf.write(filepath, arcname)
                added_files.append(arcname)
                added_count += 1
        
        # Append list to README (but since already written, print here)
        print(f"Added {added_count} files:")
        for f in sorted(added_files):
            print(f"  {f}")
        print(f"\nBackup complete: {zip_path}")
        print(f"Size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    create_core_backup()