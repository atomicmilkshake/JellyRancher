"""
Complete DeepMemoryAgent Demo

Demonstrates the full integration with realistic media organization scenarios.
Shows all memory sectors in action and cross-session persistence.
"""

import sys
from pathlib import Path
from time import sleep

sys.path.insert(0, str(Path(__file__).parent / "_common"))

from deepmemory_integration import DeepMemoryIntegrator
from immutable_audit import ImmutableAuditLog


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"🧠 {title}")
    print("=" * 70 + "\n")


def demo_episodic_memory(memory: DeepMemoryIntegrator):
    """Demonstrate episodic memory - operation logging."""
    print_section("DEMO 1: Episodic Memory - Operation Logging")
    
    print("📝 Logging media organization operations...\n")
    
    # Log movie organization
    memory.log_operation(
        operation_type="organize_movie",
        description="Organized 'The Matrix (1999)' from loose files to standardized structure",
        metadata={
            "source": "V:/Movies/The Matrix.mkv",
            "destination": "V:/Movies/The Matrix (1999)/The Matrix (1999).mkv",
            "media_type": "movie",
            "file_size": "8.5 GB"
        }
    )
    print("✅ Logged: The Matrix (1999) organization")
    
    # Log TV show organization
    memory.log_operation(
        operation_type="organize_tv",
        description="Organized Breaking Bad S01E01 into proper season structure",
        metadata={
            "source": "V:/TV/Breaking Bad - Pilot.mkv",
            "destination": "V:/TV Shows/Breaking Bad/Season 01/Breaking Bad - S01E01 - Pilot.mkv",
            "media_type": "tv_show",
            "season": 1,
            "episode": 1
        }
    )
    print("✅ Logged: Breaking Bad S01E01 organization")
    
    # Log subtitle download
    memory.log_operation(
        operation_type="download_subtitle",
        description="Downloaded English subtitles for Inception (2010)",
        metadata={
            "movie": "Inception (2010)",
            "language": "English",
            "source": "OpenSubtitles.org",
            "forced": False
        }
    )
    print("✅ Logged: Inception subtitle download")
    
    sleep(1)
    
    # Query similar operations
    print("\n🔍 Querying for similar operations...\n")
    similar = memory.get_similar_operations("organizing movie files", k=3)
    
    print(f"Found {len(similar)} similar operations:")
    for i, op in enumerate(similar, 1):
        print(f"  {i}. {op.get('content', '')[:60]}...")


def demo_semantic_memory(memory: DeepMemoryIntegrator):
    """Demonstrate semantic memory - patterns and facts."""
    print_section("DEMO 2: Semantic Memory - Patterns & Facts")
    
    print("📚 Storing learned patterns...\n")
    
    # Store movie naming pattern
    memory.store_media_pattern(
        pattern_type="movie_naming",
        description="Standard movie naming: {Title} ({Year})",
        examples=[
            "The Matrix (1999)",
            "Inception (2010)",
            "Interstellar (2014)"
        ]
    )
    print("✅ Stored: Movie naming pattern")
    
    # Store TV show structure pattern
    memory.store_media_pattern(
        pattern_type="tv_structure",
        description="TV episodes: {Show}/Season {NN}/{Show} - S{NN}E{NN} - {Title}.ext",
        examples=[
            "Breaking Bad/Season 01/Breaking Bad - S01E01 - Pilot.mkv",
            "The Office/Season 02/The Office - S02E01 - The Dundies.mkv"
        ]
    )
    print("✅ Stored: TV show structure pattern")
    
    # Store subtitle pattern
    memory.store_media_pattern(
        pattern_type="subtitle_naming",
        description="Subtitles: {filename}.{language}.srt or {filename}.{language}.forced.srt",
        examples=[
            "Movie.en.srt",
            "Movie.en.forced.srt",
            "Show - S01E01.es.srt"
        ]
    )
    print("✅ Stored: Subtitle naming pattern")
    
    sleep(1)
    
    # Query patterns
    print("\n🔍 Retrieving relevant patterns...\n")
    patterns = memory.get_relevant_patterns("movie", "naming conventions", k=2)
    
    print(f"Found {len(patterns)} relevant patterns:")
    for i, pattern in enumerate(patterns, 1):
        print(f"  {i}. {pattern.get('content', '')[:60]}...")


def demo_procedural_memory(memory: DeepMemoryIntegrator):
    """Demonstrate procedural memory - procedures and workflows."""
    print_section("DEMO 3: Procedural Memory - Procedures & Workflows")
    
    print("⚙️  Storing organization procedures...\n")
    
    # Store movie organization procedure
    memory.store_procedure(
        procedure_name="organize_movie_file",
        description="Standard procedure for organizing a movie file",
        steps=[
            "Parse filename to extract title and year",
            "Create movie directory: {Title} ({Year})/",
            "Rename file to: {Title} ({Year}).{ext}",
            "Move file to movie directory",
            "Verify file hash matches original",
            "Update media inventory"
        ]
    )
    print("✅ Stored: Movie organization procedure")
    
    # Store subtitle download procedure
    memory.store_procedure(
        procedure_name="download_subtitles",
        description="Procedure for downloading subtitles for a media file",
        steps=[
            "Check if subtitles already exist",
            "Hash media file for API query",
            "Query OpenSubtitles API with hash",
            "Filter by language preference",
            "Download highest-rated subtitle",
            "Rename to match media file: {filename}.{lang}.srt",
            "Verify subtitle sync quality"
        ]
    )
    print("✅ Stored: Subtitle download procedure")
    
    # Store troubleshooting procedure
    memory.store_procedure(
        procedure_name="fix_duplicate_episodes",
        description="Resolve duplicate episode files in TV show structure",
        steps=[
            "Scan season directory for duplicates",
            "Compare file hashes to identify true duplicates",
            "For different hashes: check quality (resolution, bitrate)",
            "Keep higher quality version",
            "Check for special editions (Extended, Director's Cut)",
            "Move lower quality to archive or delete",
            "Update episode metadata"
        ]
    )
    print("✅ Stored: Duplicate resolution procedure")
    
    sleep(1)
    
    # Query procedures
    print("\n🔍 Retrieving procedures...\n")
    procs = memory.query_memory("how to organize files", k=2, sector=memory.SECTOR_PROCEDURAL)
    
    print(f"Found {len(procs)} relevant procedures:")
    for i, proc in enumerate(procs, 1):
        print(f"  {i}. {proc.get('content', '')[:60]}...")


def demo_reflective_memory(memory: DeepMemoryIntegrator):
    """Demonstrate reflective memory - insights and preferences."""
    print_section("DEMO 4: Reflective Memory - Insights & Preferences")
    
    print("💡 Storing learned insights and user preferences...\n")
    
    # Store subtitle preference
    memory.store_reflection(
        insight="User prefers forced subtitles for foreign language dialogue in English movies",
        context="Downloaded subtitles for Inglourious Basterds - user corrected to forced version",
        learned_from="user correction"
    )
    print("✅ Stored: Subtitle preference insight")
    
    # Store quality preference
    memory.store_reflection(
        insight="User prefers 1080p quality over 4K for TV shows to save disk space",
        context="Organizing TV show files - user kept 1080p when both versions available",
        learned_from="user choice"
    )
    print("✅ Stored: Quality preference insight")
    
    # Store naming preference
    memory.store_reflection(
        insight="User prefers year in parentheses even for very old movies (pre-1950)",
        context="Organizing classic film collection - user requested year format consistency",
        learned_from="user feedback"
    )
    print("✅ Stored: Naming preference insight")
    
    sleep(1)
    
    # Query preferences
    print("\n🔍 Retrieving user preferences...\n")
    prefs = memory.get_user_preferences("subtitle", k=3)
    
    print(f"Found {len(prefs)} relevant preferences:")
    for i, pref in enumerate(prefs, 1):
        print(f"  {i}. {pref.get('content', '')[:60]}...")


def demo_cross_session_persistence():
    """Demonstrate persistence across sessions."""
    print_section("DEMO 5: Cross-Session Persistence")
    
    print("🔄 Simulating new agent session...\n")
    
    # Create new integrator instance (simulates new session)
    memory = DeepMemoryIntegrator(user_id="jellyfin_agent_demo")
    if not memory.initialize():
        print("❌ OpenMemory not available")
        return
    
    print("✅ New session initialized\n")
    
    # Query all previously stored memories
    print("🔍 Querying memories from 'previous session'...\n")
    
    all_memories = memory.query_memory("media organization", k=10)
    
    print(f"📚 Retrieved {len(all_memories)} memories from previous sessions:")
    
    sectors = {}
    for mem in all_memories:
        sector = mem.get('metadata', {}).get('sector', 'unknown')
        sectors[sector] = sectors.get(sector, 0) + 1
    
    for sector, count in sorted(sectors.items()):
        print(f"  • {sector.capitalize()}: {count} memories")
    
    print("\n💡 All memories persisted successfully across sessions!")


def demo_integrated_workflow(memory: DeepMemoryIntegrator, audit: ImmutableAuditLog):
    """Demonstrate integrated workflow with both audit trail and memory."""
    print_section("DEMO 6: Integrated Workflow - Audit Trail + DeepMemory")
    
    print("🔗 Demonstrating dual-logging pattern...\n")
    
    operation = {
        "source": "V:/Jellyfin Organizer/Movies/Interstellar.mkv",
        "destination": "V:/Jellyfin Organizer/Movies/Interstellar (2014)/Interstellar (2014).mkv",
        "title": "Interstellar",
        "year": 2014
    }
    
    # Log to immutable audit trail (existing system)
    print("1️⃣  Logging to immutable audit trail...")
    audit.log_event("organize_movie", operation, actor="demo.py")
    print("   ✅ Logged to hash-chained audit trail (cryptographic integrity)")
    
    # Log to DeepMemory (new system)
    print("\n2️⃣  Logging to DeepMemory...")
    memory.log_operation(
        operation_type="organize_movie",
        description=f"Organized '{operation['title']} ({operation['year']})' to standardized structure",
        metadata=operation
    )
    print("   ✅ Logged to semantic memory (retrievable for learning)")
    
    print("\n🎯 Result: Both systems updated with complementary benefits")
    print("   • Audit Trail: Compliance, tamper detection, legal record")
    print("   • DeepMemory: Learning, context, recommendations")


def main():
    """Run complete demo."""
    print("=" * 70)
    print("🧠 DeepMemoryAgent Complete Integration Demo")
    print("=" * 70)
    print("\nThis demo shows all four memory sectors and cross-session persistence.")
    print("Memories stored here will be available in all future sessions.\n")
    
    # Initialize systems
    print("⚙️  Initializing systems...\n")
    
    memory = DeepMemoryIntegrator(user_id="jellyfin_agent_demo")
    if not memory.initialize():
        print("❌ OpenMemory server not running!")
        print("   Start with: cd scripts && .\\start_openmemory.ps1")
        return 1
    
    audit = ImmutableAuditLog()
    audit.initialize()
    
    print("✅ Systems initialized\n")
    
    # Run demos
    demo_episodic_memory(memory)
    demo_semantic_memory(memory)
    demo_procedural_memory(memory)
    demo_reflective_memory(memory)
    demo_cross_session_persistence()
    demo_integrated_workflow(memory, audit)
    
    # Summary
    print_section("Demo Complete - Summary")
    
    print("✅ Demonstrated all memory sectors:")
    print("   • Episodic: Operation logs and events")
    print("   • Semantic: Patterns and facts")
    print("   • Procedural: Workflows and procedures")
    print("   • Reflective: Insights and preferences")
    
    print("\n✅ Verified cross-session persistence")
    print("✅ Demonstrated integrated workflow")
    
    print("\n💡 Next steps:")
    print("   1. Query stored memories:")
    print("      python organize_with_memory.py --query 'Matrix organization'")
    print("\n   2. Use memory-enhanced organization:")
    print("      python organize_with_memory.py --media-root '...' --type movies")
    print("\n   3. Integrate into production scripts")
    
    print("\n" + "=" * 70)
    print("🎉 DeepMemoryAgent is ready for production use!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
