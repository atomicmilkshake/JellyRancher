# OpenMemory Journal (Dev/Agent Notes)

This documents how to use OpenMemory as a semantic development journal for Jellyfin Organizer (and other projects), while keeping the ImmutableAuditLog as the source of truth.

## Prereqs

- OpenMemory backend running locally (see `config.json -> openmemory.url`).
- Python dependency:
  - `pip install requests`
- Optional: Ollama with `nomic-embed-text` pulled, if your OpenMemory backend uses Ollama for embeddings.

## Config

`_common/config_loader.py` reads `config.json` at the project root. Ensure it has:

```json
{
  "openmemory": {
    "backend_dir": "C:/path/to/OpenMemory",
    "url": "http://localhost:8080"
  }
}
```

## Publish a journal entry

- From the scripts folder:

```powershell
# Direct text
python .\journal_service.py --category decision --project "Jellyfin Organizer" --tag workflow --tag planning "Planning JMO integration: services layer, dual-write audit->journal, AI assist on ambiguous renames."

# From stdin (multi-line)
Get-Content .\some_notes.txt | python .\journal_service.py --category summary --tag weekly
```

Fields you can add:
- `--category` observation|decision|plan|action|error|rollback|summary
- `--project` to scope across multiple projects
- `--session-id` to tie a sequence of actions/notes together
- `--tag` repeatable tag flags
- `--media-ref` repeatable media paths/ids (useful for per-file queries)
- `--audit-ref` link back to an audit record id

The service performs a best-effort redaction for secrets before indexing.

## Why two layers?

- ImmutableAuditLog: exact, append-only, rollbackable truth of operations.
- OpenMemory journal: short, human-readable summaries and rationale for semantic search.

Search in your OpenMemory UI/API to recall "why", then follow the `audit_ref` to verify the exact details.

## Health check

If the backend isn't responding:

```powershell
# Expect [OK] if reachable
python .\journal_service.py "health check" --category observation
```

If it fails, verify your `openmemory.url` and that the service is running.
