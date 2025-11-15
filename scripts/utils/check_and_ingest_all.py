"""
Check DeepMemory state and ingest entire project if needed.
Then archive all redundant documentation.
"""

import sys
from pathlib import Path
import json
import time
from datetime import datetime
import zipfile

sys.path.insert(0, str(Path(__file__).parent / "_common"))

try:
    from openmemory import OpenMemory
except ImportError as e:
    print(f"ERROR: {e}")
    print("Install dependencies: pip install openmemory-py")
    sys.exit(1)


def check_memory_status():
    """Check if project has been ingested."""
    print("\n" + "="*60)
    print("CHECKING DEEPMEMORY STATUS")
    print("="*60 + "\n")
    
    try:
        client = OpenMemory(base_url="http://localhost:8080")
        
        # Test search for project knowledge
        result = client.search(
            "project architecture",
            user_id="jellyfin_project_knowledge",
            limit=10
        )
        
        print(f"Found {len(result)} memory entries for 'project architecture'")
        
        if result:
            print("\nSample memories:")
            for i, r in enumerate(result[:5], 1):
                source = r.get("metadata", {}).get("source", "unknown")
                print(f"  {i}. {source}")
            return len(result)
        else:
            print("No project memories found - needs ingestion")
            return 0
            
    except Exception as e:
        print(f"ERROR checking memory: {e}")
        return -1


def ingest_project():
    """Ingest entire project into DeepMemory."""
    print("\n" + "="*60)
    print("INGESTING PROJECT TO DEEPMEMORY")
    print("="*60 + "\n")
    
    project_root = Path(__file__).parent.parent
    client = OpenMemory(base_url="http://localhost:8080")
    
    # File patterns to include
    include_patterns = [
        "*.py",
        "*.md",
        "*.txt",
        "*.ps1",
        "*.yaml",
        "*.yml",
        "*.json",
        "*.sh",
    ]
    
    # Directories to exclude
    exclude_dirs = {
        ".git", "__pycache__", ".pytest_cache", "venv", ".venv",
        "node_modules", ".trash", "rollback", "snapshots", "audit-logs",
        "logs", "reports", "test_media", ".coverage", "OpenMemory"
    }
    
    files_to_ingest = []
    
    print("Scanning project files...")
    for pattern in include_patterns:
        for file_path in project_root.rglob(pattern):
            # Skip excluded directories
            if any(excl in file_path.parts for excl in exclude_dirs):
                continue
            # Skip this script
            if file_path.name == "check_and_ingest_all.py":
                continue
            files_to_ingest.append(file_path)
    
    print(f"\nFound {len(files_to_ingest)} files to ingest\n")
    
    ingested_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in files_to_ingest:
        try:
            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = file_path.read_text(encoding='latin-1')
            
            # Skip very large files
            if len(content) > 500000:
                print(f"  SKIP (too large): {file_path.name}")
                skipped_count += 1
                continue
            
            # Skip empty files
            if len(content.strip()) == 0:
                skipped_count += 1
                continue
            
            relative_path = file_path.relative_to(project_root)
            
            # Create memory entry
            memory_data = {
                "content": content[:100000],  # Limit to 100KB per file
                "source": str(relative_path),
                "file_type": file_path.suffix,
                "category": categorize_file(file_path),
                "ingestion_date": datetime.now().isoformat()
            }
            
            client.add(
                content=f"File: {relative_path}\n\n{content[:100000]}",
                metadata=memory_data,
                user_id="jellyfin_project_knowledge"
            )
            
            ingested_count += 1
            if ingested_count % 10 == 0:
                print(f"  Ingested {ingested_count} files...")
                
        except Exception as e:
            print(f"  ERROR {file_path.name}: {e}")
            error_count += 1
    
    print(f"\n" + "="*60)
    print(f"INGESTION COMPLETE")
    print(f"  Ingested: {ingested_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print("="*60 + "\n")
    
    return ingested_count


def categorize_file(file_path: Path) -> str:
    """Categorize file for metadata."""
    path_str = str(file_path).lower()
    
    if "deepmemory" in path_str or "openmemory" in path_str:
        return "memory_system"
    elif "_common" in path_str:
        return "core_utilities"
    elif "organize" in path_str:
        return "organization_scripts"
    elif "test" in path_str:
        return "tests"
    elif file_path.suffix == ".md":
        return "documentation"
    elif file_path.suffix in [".yaml", ".yml", ".json"]:
        return "configuration"
    elif file_path.suffix in [".ps1", ".sh"]:
        return "automation"
    elif file_path.suffix == ".py":
        return "python_code"
    else:
        return "other"


def archive_documentation():
    """Archive all redundant markdown documentation to a zip file."""
    print("\n" + "="*60)
    print("ARCHIVING REDUNDANT DOCUMENTATION")
    print("="*60 + "\n")
    
    project_root = Path(__file__).parent.parent
    archive_dir = project_root / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = archive_dir / f"documentation_archive_{timestamp}.zip"
    
    # Files to keep (not archive)
    keep_files = {
        "README.md",  # Will create new one
        "master-prompt.md",  # Keep single source of truth
        ".github/copilot-instructions.md"
    }
    
    # Find all markdown and txt files to archive
    files_to_archive = []
    for ext in ["*.md", "*.txt"]:
        for file_path in project_root.glob(ext):
            relative_path = file_path.relative_to(project_root)
            if str(relative_path) not in keep_files:
                files_to_archive.append(file_path)
    
    print(f"Found {len(files_to_archive)} files to archive\n")
    
    # Create zip archive
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_archive:
            relative_path = file_path.relative_to(project_root)
            zipf.write(file_path, relative_path)
            print(f"  + {relative_path}")
    
    # Delete archived files
    for file_path in files_to_archive:
        file_path.unlink()
        print(f"  - Deleted {file_path.name}")
    
    print(f"\n" + "="*60)
    print(f"ARCHIVE COMPLETE")
    print(f"  Archived: {len(files_to_archive)} files")
    print(f"  Location: {archive_path}")
    print(f"  Size: {archive_path.stat().st_size / 1024:.1f} KB")
    print("="*60 + "\n")
    
    return archive_path


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("DEEPMEMORY PROJECT SETUP & DOCUMENTATION CLEANUP")
    print("="*70)
    
    # Step 1: Check current memory status
    memory_count = check_memory_status()
    
    # Step 2: Ingest if needed (or if user wants full re-ingestion)
    if memory_count < 10:
        print("\nMemory system needs ingestion. Starting...")
        time.sleep(2)
        ingest_project()
    else:
        response = input(f"\nMemory has {memory_count} entries. Re-ingest? (y/N): ")
        if response.lower() == 'y':
            ingest_project()
        else:
            print("Skipping ingestion...")
    
    # Step 3: Archive redundant documentation
    response = input("\nArchive redundant documentation files? (Y/n): ")
    if response.lower() != 'n':
        archive_path = archive_documentation()
        print(f"\nAll redundant docs archived to:\n  {archive_path}")
    else:
        print("Skipping documentation cleanup...")
    
    print("\n" + "="*70)
    print("SETUP COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Use master-prompt.md as your single bootstrap file")
    print("  2. Query DeepMemory for context: client.search('topic', user_id='jellyfin_project_knowledge')")
    print("  3. All project knowledge is now in persistent memory")
    print("\n")


if __name__ == "__main__":
    main()
