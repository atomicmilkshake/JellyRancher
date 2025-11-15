#!/usr/bin/env python3
from scripts.core.chroma_memory_backend import get_memory_backend

backend = get_memory_backend()

docs = [
    {
        "content": "OpenMemory Purge Complete: Removed OpenMemoryInterface from tools_backend.py (class, docstring, __main__ test); deleted test_openmemory.py; purged imports/methods from test_backends.py/quick_test.py; removed get_openmemory_config from config_loader.py; eliminated references from utils/media/ai/help/jellyfin_ui/master.py (deleted deepmemory scripts). Codebase clean, focused on ChromaDB semantic search.",
        "tags": ["purge", "openmemory", "cleanup", "tools"],
        "category": "documentation"
    },
    {
        "content": "Fixed Empty Search: Ingested 8 sample memories via ingest_samples.py using backend.add_memory with metadata (categories: project/action/backend/feature/tools/safety/memory/robustness; tags e.g., recent/gui/tmdb). Backend query 'recent work' returns 5 results with distances (1.73-1.86), categories/tags/content. Updated perform_memory_search with try/except for safe distance float, formatting fallbacks, Qt display error handling.",
        "tags": ["fix", "memory", "chromadb", "ingestion", "error-handling"],
        "category": "documentation"
    },
    {
        "content": "Project Assessment: Design modular (PyQt5 GUI/backends/utils separation, callbacks/audits/snapshots); functional (tabs operational, search returns categorized results, no crashes); strengths (safety/robustness/knowledge base); improvements (real APIs/full tests/async/UI polish). Demo: Search 'recent work' in Memory tab for action/memory results.",
        "tags": ["assessment", "design", "functionality", "improvements"],
        "category": "documentation"
    }
]

print("Documenting work in ChromaDB...")
added = []
for i, doc in enumerate(docs, 1):
    tags_str = ','.join(doc['tags'])
    metadata = {"category": doc['category'], "tags": tags_str, "source": "cline_ai"}
    memory_id = backend.add_memory(doc['content'], metadata=metadata)
    added.append(memory_id)
    print(f"Added [{i}/3]: {doc['category']} - {doc['content'][:50]}...")

print(f"\n✅ Documented work: {len(added)} entries added. Query 'purge work' or 'fix memory' in GUI.")
