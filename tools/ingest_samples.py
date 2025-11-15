#!/usr/bin/env python3
from scripts.core.chroma_memory_backend import get_memory_backend

# Sample project memories for testing semantic search
samples = [
    {
        "content": "JellyRancher is a unified media organization platform for Jellyfin libraries. Key features: movie/TV/anime organization, subtitle management, batch processing with RavenMaven, code analysis via CodeCop, analytics reporting, and semantic memory search using ChromaDB.",
        "tags": ["overview", "architecture", "features"],
        "category": "project"
    },
    {
        "content": "Recent work: Integrated PyQt5 GUI with tabs for Organization, Subtitles, Batch Processing, Code Analysis, Analytics, Memory, and Settings. Added TMDB cache generation dialog for TV episodes and movie/episode name analyzers.",
        "tags": ["recent", "gui", "tmdb", "analysis"],
        "category": "action"
    },
    {
        "content": "Media organization uses MediaOrganizer backend to scan folders, propose moves, and execute with dry-run/snapshot safety. Supports movies, TV shows, anime with integrity verification.",
        "tags": ["media", "organization", "safety"],
        "category": "backend"
    },
    {
        "content": "Subtitle management downloads from OpenSubtitles/Subscene/Podnapisi with coverage detection. Live mode writes .srt files; integrates with media paths from config.",
        "tags": ["subtitles", "download", "providers"],
        "category": "feature"
    },
    {
        "content": "Batch processing via RavenMavenInterface simulates AI-powered folder reorganization. Code analysis with CodeCopInterface checks complexity/docs/style. AnalyticsBackend generates reports on operations/audit.",
        "tags": ["batch", "codecop", "analytics"],
        "category": "tools"
    },
    {
        "content": "ImmutableAuditLog ensures all operations are traceable with hash-chained entries. SnapshotManager creates rollback points before changes. SettingsManager handles paths, APIs (TMDB key), preferences.",
        "tags": ["audit", "snapshots", "settings"],
        "category": "safety"
    },
    {
        "content": "ChromaDB semantic search in Memory tab queries project knowledge. Suggestions provide tips like recent blockers or architecture decisions. Journal actions auto-add to memory.",
        "tags": ["chromadb", "search", "suggestions"],
        "category": "memory"
    },
    {
        "content": "Error handling: Threading prevents UI freezes; progress callbacks update bars/logs. Config validation ensures paths exist; fallbacks for missing embeddings use text matching.",
        "tags": ["errors", "threading", "progress"],
        "category": "robustness"
    }
]

print("Ingesting sample memories to ChromaDB...")
backend = get_memory_backend()
added = []
for i, sample in enumerate(samples, 1):
    tags_str = ','.join(sample['tags'])
    metadata = {"category": sample['category'], "tags": tags_str}
    memory_id = backend.add_memory(sample['content'], metadata=metadata)
    added.append(memory_id)
    print(f"Added [{i}/8]: {sample['category']} - {sample['content'][:50]}...")

print(f"\n✅ Ingested {len(added)} sample memories. IDs: {added}")
print("Now try searching 'recent work' or 'media organization' in the GUI Memory tab.")
