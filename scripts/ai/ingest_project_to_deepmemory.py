"""
COMPLETE PROJECT INGESTION TO DEEPMEMORY

This script ingests EVERY Python script, documentation file, and project
artifact into DeepMemory/OpenMemory for complete project knowledge storage.

The agent will have complete knowledge of the entire codebase and all documentation.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import time

sys.path.insert(0, str(Path(__file__).parent / "_common"))

from deepmemory_integration import DeepMemoryIntegrator


class ProjectIngester:
    """
    Ingests entire project into DeepMemory for complete knowledge storage.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.memory = DeepMemoryIntegrator(user_id="jellyfin_project_knowledge")
        
        # File patterns to include
        self.include_patterns = [
            "*.py",       # Python scripts
            "*.md",       # Markdown documentation
            "*.txt",      # Text files
            "*.ps1",      # PowerShell scripts
            "*.yaml",     # Configuration
            "*.yml",      # Configuration
            "*.json",     # JSON data/config
            "*.sh",       # Shell scripts
        ]
        
        # Directories to exclude
        self.exclude_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "venv",
            ".venv",
            "node_modules",
            ".trash",
            "rollback",
            "snapshots",
            "audit-logs",
            "logs",
            "reports",
            "test_media",
            ".coverage",
        }
        
        # Files to exclude
        self.exclude_files = {
            ".gitignore",
            ".env",
            ".env.example",
            "coverage.xml",
        }
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed."""
        # Check if in excluded directory
        for parent in file_path.parents:
            if parent.name in self.exclude_dirs:
                return False
        
        # Check if excluded file
        if file_path.name in self.exclude_files:
            return False
        
        # Check if matches include patterns
        for pattern in self.include_patterns:
            if file_path.match(pattern):
                return True
        
        return False
    
    def categorize_file(self, file_path: Path) -> str:
        """Categorize file for appropriate memory sector."""
        relative_path = file_path.relative_to(self.project_root)
        path_str = str(relative_path).lower()
        
        # Core integration code
        if "deepmemory" in path_str or "openmemory" in path_str:
            return "core_integration"
        
        # Common utilities
        if "_common" in path_str:
            return "core_utilities"
        
        # Organization scripts
        if "organize" in path_str:
            return "organization_scripts"
        
        # Test files
        if "test" in path_str:
            return "test_suite"
        
        # Documentation
        if file_path.suffix == ".md":
            if "README" in file_path.name.upper():
                return "readme_docs"
            elif "GUIDE" in file_path.name.upper():
                return "guide_docs"
            elif "REPORT" in file_path.name.upper() or "SUMMARY" in file_path.name.upper():
                return "report_docs"
            else:
                return "general_docs"
        
        # Configuration
        if file_path.suffix in [".yaml", ".yml", ".json"]:
            return "configuration"
        
        # Scripts
        if file_path.suffix in [".ps1", ".sh"]:
            return "automation_scripts"
        
        # Python modules
        if file_path.suffix == ".py":
            if "main" in path_str or "backend" in path_str:
                return "backend_code"
            else:
                return "utility_code"
        
        return "misc_files"
    
    def read_file_safe(self, file_path: Path) -> Optional[str]:
        """Safely read file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"  ⚠️  Could not read {file_path.name}: {e}")
                return None
        except Exception as e:
            print(f"  ⚠️  Error reading {file_path.name}: {e}")
            return None
    
    def create_file_memory(self, file_path: Path, content: str, category: str):
        """Create a memory entry for a file."""
        relative_path = file_path.relative_to(self.project_root)
        
        # Get file stats
        lines = len(content.split('\n'))
        size_kb = len(content) / 1024
        
        # Create description
        description = f"""
FILE: {relative_path}
CATEGORY: {category}
SIZE: {size_kb:.1f} KB
LINES: {lines}
TYPE: {file_path.suffix}

CONTENT:
{content[:5000]}{"..." if len(content) > 5000 else ""}
        """.strip()
        
        # Determine sector based on category
        if category in ["core_integration", "core_utilities", "backend_code"]:
            sector = self.memory.SECTOR_PROCEDURAL
        elif category in ["readme_docs", "guide_docs"]:
            sector = self.memory.SECTOR_SEMANTIC
        elif category in ["test_suite"]:
            sector = self.memory.SECTOR_EPISODIC
        elif category in ["report_docs", "general_docs"]:
            sector = self.memory.SECTOR_REFLECTIVE
        else:
            sector = self.memory.SECTOR_SEMANTIC
        
        # Store in memory
        self.memory.add_memory(
            content=description,
            sector=sector,
            metadata={
                "file_path": str(relative_path),
                "category": category,
                "file_type": file_path.suffix,
                "file_size_kb": size_kb,
                "line_count": lines,
                "full_content": content if len(content) <= 10000 else content[:10000] + "...",
            }
        )
    
    def scan_and_ingest(self) -> Dict[str, int]:
        """Scan project and ingest all files."""
        print("=" * 70)
        print("🧠 COMPLETE PROJECT INGESTION TO DEEPMEMORY")
        print("=" * 70)
        print()
        
        # Initialize memory
        print("⚙️  Initializing DeepMemory connection...")
        if not self.memory.initialize():
            print("❌ Failed to connect to OpenMemory!")
            print("   Start server with: cd scripts && .\\start_openmemory.ps1")
            return {}
        
        print("✅ Connected to OpenMemory")
        print()
        
        # Scan for files
        print(f"📁 Scanning project: {self.project_root}")
        print()
        
        all_files: List[Path] = []
        for pattern in self.include_patterns:
            files = list(self.project_root.rglob(pattern))
            all_files.extend(files)
        
        # Filter files
        files_to_process = [f for f in all_files if self.should_process_file(f)]
        
        print(f"📊 Found {len(files_to_process)} files to ingest")
        print()
        
        # Categorize files
        categories: Dict[str, List[Path]] = {}
        for file_path in files_to_process:
            category = self.categorize_file(file_path)
            if category not in categories:
                categories[category] = []
            categories[category].append(file_path)
        
        # Display categories
        print("📋 File categories:")
        for category, files in sorted(categories.items()):
            print(f"   {category}: {len(files)} files")
        print()
        
        # Ingest files
        print("🔄 Ingesting files into DeepMemory...")
        print()
        
        ingested = 0
        failed = 0
        category_counts: Dict[str, int] = {}
        
        for category, files in sorted(categories.items()):
            print(f"📁 Processing {category} ({len(files)} files)...")
            
            for file_path in files:
                try:
                    # Read file
                    content = self.read_file_safe(file_path)
                    if content is None:
                        failed += 1
                        continue
                    
                    # Create memory
                    self.create_file_memory(file_path, content, category)
                    
                    relative_path = file_path.relative_to(self.project_root)
                    print(f"   ✅ {relative_path}")
                    
                    ingested += 1
                    category_counts[category] = category_counts.get(category, 0) + 1
                    
                    # Small delay to avoid overwhelming the server
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"   ❌ {file_path.name}: {e}")
                    failed += 1
            
            print()
        
        # Summary
        print("=" * 70)
        print("✅ INGESTION COMPLETE")
        print("=" * 70)
        print()
        print(f"📊 Summary:")
        print(f"   Total files processed: {ingested}")
        print(f"   Failed: {failed}")
        print()
        print("📂 By category:")
        for category, count in sorted(category_counts.items()):
            print(f"   {category}: {count} files")
        print()
        print("🧠 DeepMemory Status:")
        print("   All project knowledge now stored in OpenMemory")
        print("   Query with: python organize_with_memory.py --query 'your question'")
        print()
        
        return category_counts
    
    def create_project_index(self):
        """Create a comprehensive project index memory."""
        print("📝 Creating project index...")
        
        index_content = f"""
JELLYFIN MEDIA ORGANIZATION AGENT - PROJECT INDEX

This is a comprehensive media organization system with persistent memory
capabilities powered by OpenMemory.

KEY COMPONENTS:

1. CORE INTEGRATION
   - deepmemory_integration.py: OpenMemory integration with 4 memory sectors
   - immutable_audit.py: Hash-chained audit trail
   - credential_manager.py: Encrypted credential storage
   - snapshot_manager.py: Rollback capabilities
   - media_utils.py: Windows-specific file operations

2. ORGANIZATION SCRIPTS
   - organize_movies.py: Movie organization
   - organize_tv_shows.py: TV show organization
   - organize_anime.py: Anime organization
   - organize_with_memory.py: Memory-enhanced organization

3. MEMORY SECTORS
   - Episodic: Operation logs and events
   - Semantic: Patterns and facts
   - Procedural: Workflows and procedures
   - Reflective: User preferences and insights

4. TESTING & VALIDATION
   - test_deepmemory_integration.py: Memory integration tests
   - test_foundation.py: Core system tests
   - verify_audit_chain.py: Audit integrity verification

5. DOCUMENTATION
   - DEEPMEMORY_README.md: Quick start guide
   - DEEPMEMORY_INTEGRATION_GUIDE.md: Complete API reference
   - DEEPMEMORY_IMPLEMENTATION_SUMMARY.md: Technical architecture
   - master-prompt.md: Project guidelines

PROJECT LOCATION: V:\\Jellyfin Organizer

CAPABILITIES:
- Organize movies, TV shows, and anime
- Download subtitles from OpenSubtitles
- Maintain cryptographic audit trail
- Learn from past operations with DeepMemory
- Remember user preferences across sessions
- Provide context-aware recommendations
- Rollback operations via snapshots

TECHNOLOGY STACK:
- Python 3.14.0
- OpenMemory (Node.js)
- SQLite for persistence
- Cryptography for audit trail
- Windows-optimized file operations
        """
        
        self.memory.add_memory(
            content=index_content,
            sector=self.memory.SECTOR_SEMANTIC,
            metadata={
                "file_path": "PROJECT_INDEX",
                "category": "project_overview",
                "file_type": "index",
            }
        )
        
        print("✅ Project index created")
        print()


def main():
    """Main entry point."""
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Create ingester
    ingester = ProjectIngester(project_root)
    
    # Create project index first
    ingester.create_project_index()
    
    # Scan and ingest all files
    results = ingester.scan_and_ingest()
    
    if results:
        print("🎉 SUCCESS!")
        print()
        print("Your entire project is now in DeepMemory.")
        print("The agent has complete knowledge of all code and documentation.")
        print()
        print("Try querying:")
        print("  python organize_with_memory.py --query 'how does the audit trail work'")
        print("  python organize_with_memory.py --query 'list all organization scripts'")
        print("  python organize_with_memory.py --query 'explain deepmemory integration'")
    else:
        print("❌ Ingestion failed - check OpenMemory server status")
    
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
