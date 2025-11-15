agent-journal.md is the sole source of truth for this project. Upon starting each session, check if agent-journal.md exists in the project root. If it exists, read it completely and prove ingestion by stating the last phase number, what was accomplished in that phase, and the current project status. If it doesn't exist, acknowledge this is a new project and create agent-journal.md with Phase 1.

All work, decisions, code changes, and progress must be documented in agent-journal.md. Do not create additional documentation files, summaries, reference cards, or any other documentation. agent-journal.md is the only documentation file.

When agent-journal.md **exceeds 1200 lines**, IMMEDIATELY create a backup and compress it. Do not ask permission. This is mandatory automatic maintenance. Steps:
1. Create backup: /backups/agent-journal_YYYY-MM-DD_HHMMSS.md (ISO 8601 format)
2. Compress losslessly: condense verbose entries, preserve ALL phase numbers, key decisions, accomplishments, essential context
3. **CRITICAL:** Preserve every obstacle encountered and the breakthrough that overcame it (prevents reinventing the wheel)
4. Add journal entry (Phase N) documenting compression with backup filename reference
5. Continue with compressed journal

Note: If current line count > 1200, the journal has EXCEEDED the threshold and needs compression NOW, not "soon" or "approaching."

Each journal entry should include date/time, phase number, changes made, decisions, and next steps. When obstacles are encountered, document both the obstacle and the breakthrough solution prominently.

Always use the virtual environment () for running python scripts or snippets.  Do not run python scripts or commands outside the virtual environment. Activate the virtual environment immediately upon reading this: .venv\Scripts\Activate.ps1

Before implementing new functionality, you must query the LLM-enhanced function index (data/llm_function_index.json) using tools/query_function_index_semantic.py to check for already-available functionality. This prevents reinventing the wheel and ensures we leverage existing, well-documented code. Use semantic search with natural language queries describing the desired functionality (e.g., "find TMDB metadata for movies" or "organize TV episodes using TVDB").

For time entries in journal: Always get the current time by running: python -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))" and use the output for the time field. Never use placeholders for time.

Git workflow is mandatory for this project. After completing each significant phase or set of related changes:
1. Stage changes: git add .
2. Commit with descriptive message following conventional commits format (e.g., "feat: add X", "fix: resolve Y", "docs: update Z")
3. Push to GitHub: git push origin master
4. Document git commits in journal entries when appropriate

GitHub repository: https://github.com/atomicmilkshake/JellyRancher
GitHub CLI location: "C:\Program Files\GitHub CLI\gh.exe"

Philosophically, don't halfass things just because you're in a hurry or have a sycophantic personality disorder.  Always ASK and never ASSUME before making important design decisions.  I don't like shortcuts unless I specify otherwise.