"""
Enhanced Media Organization with DeepMemory Integration

Extends the base media organization functionality with persistent memory,
allowing the agent to learn from past operations and user preferences.

Usage:
    python organize_with_memory.py --media-root "V:/Jellyfin Organizer/Movies" --type movies
    python organize_with_memory.py --media-root "V:/Jellyfin Organizer/TV Shows" --type tv
    python organize_with_memory.py --query "How have I organized anime files?"
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime

# Add _common to path
sys.path.insert(0, str(Path(__file__).parent / "_common"))

from deepmemory_integration import DeepMemoryIntegrator
from immutable_audit import ImmutableAuditLog
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MemoryEnhancedOrganizer:
    """
    Media organizer with persistent memory capabilities.
    
    Combines the existing audit trail with DeepMemory for:
    - Context retention across sessions
    - Learning from past operations
    - Retrieving similar past cases
    - Storing user preferences and corrections
    """
    
    def __init__(
        self,
        media_root: Path,
        media_type: str = "movies",
        use_memory: bool = True
    ):
        """
        Initialize memory-enhanced organizer.
        
        Args:
            media_root: Root directory for media files
            media_type: Type of media (movies, tv, anime)
            use_memory: Enable DeepMemory integration
        """
        self.media_root = Path(media_root)
        self.media_type = media_type
        self.use_memory = use_memory
        
        # Initialize audit log (existing system)
        self.audit = ImmutableAuditLog()
        self.audit.initialize()
        
        # Initialize DeepMemory integration
        self.memory: Optional[DeepMemoryIntegrator] = None
        if use_memory:
            self.memory = DeepMemoryIntegrator(
                user_id=f"jellyfin_agent_{media_type}"
            )
            if self.memory.initialize():
                logger.info("✅ DeepMemory integration active")
                self._load_context()
            else:
                logger.warning("⚠️  DeepMemory unavailable, continuing without persistent memory")
                self.memory = None
    
    def _load_context(self):
        """Load initial context from past operations."""
        if not self.memory:
            return
        
        # Get agent summary for session context
        summary = self.memory.get_agent_summary()
        if summary:
            logger.info(f"📝 Loaded agent context: {len(summary)} chars")
        
        # Get recent similar operations
        recent = self.memory.get_similar_operations(
            f"organizing {self.media_type}",
            k=5
        )
        if recent:
            logger.info(f"📚 Found {len(recent)} similar past operations")
    
    def organize_file(
        self,
        source_path: Path,
        destination_path: Path,
        metadata: Dict
    ) -> bool:
        """
        Organize a media file with memory logging.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            metadata: File metadata (title, year, etc.)
            
        Returns:
            True if successful
        """
        try:
            # Check for similar past operations
            if self.memory:
                similar = self.memory.get_similar_operations(
                    f"organize {metadata.get('title', source_path.name)}",
                    k=3
                )
                if similar:
                    logger.info(f"💡 Found {len(similar)} similar past operations")
                    for op in similar[:2]:
                        logger.debug(f"   - {op.get('content', '')[:60]}...")
            
            # Perform the actual organization (placeholder)
            # In production, this would call safe_move, hash verification, etc.
            logger.info(f"📁 Would organize: {source_path.name}")
            logger.info(f"   → {destination_path}")
            
            # Log to audit trail (existing system)
            self.audit.log_event("organize", {
                "source": str(source_path),
                "destination": str(destination_path),
                "media_type": self.media_type,
                **metadata
            }, actor="organize_with_memory.py")
            
            # Log to DeepMemory (new system)
            if self.memory:
                self.memory.log_operation(
                    operation_type=f"organize_{self.media_type}",
                    description=f"Organized '{metadata.get('title', source_path.name)}' to standardized structure",
                    metadata={
                        "source": str(source_path),
                        "destination": str(destination_path),
                        "media_type": self.media_type,
                        **metadata
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to organize {source_path}: {e}")
            return False
    
    def store_pattern(self, pattern_type: str, description: str, examples: List[str]):
        """
        Store a learned pattern to semantic memory.
        
        Args:
            pattern_type: Type of pattern (naming, structure, etc.)
            description: Pattern description
            examples: Example cases
        """
        if self.memory:
            self.memory.store_media_pattern(
                pattern_type=pattern_type,
                description=description,
                examples=examples
            )
            logger.info(f"📝 Stored pattern: {pattern_type}")
    
    def store_user_preference(self, insight: str, context: str):
        """
        Store user preference or correction to reflective memory.
        
        Args:
            insight: The preference learned
            context: Context in which it was learned
        """
        if self.memory:
            self.memory.store_reflection(
                insight=insight,
                context=context,
                learned_from="user interaction"
            )
            logger.info(f"💡 Stored preference: {insight[:50]}...")
    
    def query_memory(self, query: str, k: int = 5) -> List[Dict]:
        """
        Query past operations and knowledge.
        
        Args:
            query: Natural language query
            k: Number of results
            
        Returns:
            List of relevant memories
        """
        if not self.memory:
            logger.warning("DeepMemory not available")
            return []
        
        results = self.memory.query_memory(query, k=k)
        return results
    
    def get_recommendations(self, file_name: str) -> List[str]:
        """
        Get recommendations based on similar past operations.
        
        Args:
            file_name: File being organized
            
        Returns:
            List of recommendation strings
        """
        if not self.memory:
            return []
        
        # Get similar operations
        similar = self.memory.get_similar_operations(
            f"organize {file_name}",
            k=3
        )
        
        recommendations = []
        for op in similar:
            content = op.get('content', '')
            metadata = op.get('metadata', {})
            if metadata.get('destination'):
                recommendations.append(
                    f"Similar to: {content[:50]}... → {Path(metadata['destination']).name}"
                )
        
        return recommendations


def main():
    """Main entry point for memory-enhanced organization."""
    parser = argparse.ArgumentParser(
        description="Organize media with persistent memory learning"
    )
    parser.add_argument(
        "--media-root",
        type=Path,
        help="Root directory for media files"
    )
    parser.add_argument(
        "--type",
        choices=["movies", "tv", "anime"],
        default="movies",
        help="Type of media to organize"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query past operations and knowledge"
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable DeepMemory integration"
    )
    
    args = parser.parse_args()
    
    # Query mode
    if args.query:
        print("🔍 Querying DeepMemory...\n")
        memory = DeepMemoryIntegrator()
        if not memory.initialize():
            print("❌ OpenMemory server not running")
            print("   Start with: python start_openmemory.ps1")
            return 1
        
        results = memory.query_memory(args.query, k=10)
        print(f"Found {len(results)} relevant memories:\n")
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            sector = metadata.get('sector', 'unknown')
            timestamp = metadata.get('timestamp', 'N/A')
            
            print(f"{i}. [{sector.upper()}] {content[:80]}...")
            print(f"   Time: {timestamp}")
            print()
        
        return 0
    
    # Organization mode
    if not args.media_root:
        parser.print_help()
        return 1
    
    print("=" * 60)
    print("🧠 Memory-Enhanced Media Organization")
    print("=" * 60)
    print(f"Media Root: {args.media_root}")
    print(f"Media Type: {args.type}")
    print(f"Memory: {'Enabled' if not args.no_memory else 'Disabled'}")
    print("=" * 60)
    print()
    
    organizer = MemoryEnhancedOrganizer(
        media_root=args.media_root,
        media_type=args.type,
        use_memory=not args.no_memory
    )
    
    # Example: Demonstrate memory-enhanced organization
    print("💡 Example: Organizing a test file with memory context...\n")
    
    test_file = args.media_root / "The Matrix.mkv"
    dest_file = args.media_root / "The Matrix (1999)" / "The Matrix (1999).mkv"
    
    # Get recommendations based on past operations
    recommendations = organizer.get_recommendations("The Matrix.mkv")
    if recommendations:
        print("📚 Recommendations from past operations:")
        for rec in recommendations:
            print(f"   - {rec}")
        print()
    
    # Organize the file
    success = organizer.organize_file(
        source_path=test_file,
        destination_path=dest_file,
        metadata={
            "title": "The Matrix",
            "year": 1999,
            "media_type": "movie"
        }
    )
    
    if success:
        print("✅ Organization logged to both audit trail and DeepMemory")
        
        # Store learned pattern
        organizer.store_pattern(
            pattern_type="movie_structure",
            description="Movies organized as: {Title} ({Year})/{Title} ({Year}).{ext}",
            examples=["The Matrix (1999)/The Matrix (1999).mkv"]
        )
        print("✅ Pattern stored to semantic memory")
    
    print("\n" + "=" * 60)
    print("💡 Query your memories with:")
    print(f"   python organize_with_memory.py --query 'Matrix organization'")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
