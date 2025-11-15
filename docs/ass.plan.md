<!-- 7bfef3a7-8e4a-40cf-b806-16b709069497 c7f9d63f-267f-4933-b023-9913850383f0 -->
## Assessment of Plan Points 1–4

### Goal

Explain, in plain language, what is actually implemented for points 1–4 from `docs/plan.md` in the current code (centered on `jelly_rancher_clean.py` and its collaborators), what is not implemented, and why those conclusions follow from the code.

### Point 1 – Scanning, MD5 baseline, Jellyfin, and other metadata

The application clearly implements multi-folder recursive scanning and persistent inventory storage. `JellyRancherClean` uses `MultiScanWorker` with `FileScanner.scan_folder(...)` to walk one or more selected folders recursively and build a list of `FileRecord` objects, each holding an absolute path, size, extension, parent folder, and scan timestamp. `InventoryRepository.add_file_records(...)` writes these records into SQLite, so there is an actual master file list with one row per file path. `MultiScanWorker` is designed to take a list of `Path` objects, iterate over them, and aggregate results; the GUI shows the first 500 files, which matches the “scan selected folder or multiple folders recursively and produce a file list” requirement.

Jellyfin cross-referencing is also clearly implemented. When a `JellyfinClient` is configured, `MultiScanWorker.run(...)` calls `self.jellyfin_client.get_all_items(...)` for movies and episodes, builds a map keyed by resolved filesystem paths, and walks all `FileRecord`s to fill in fields like `jellyfin_id`, `jellyfin_item_type`, `jellyfin_library_id`, `jellyfin_provider_ids`, and `jellyfin_matched`. This gives exactly the “already-imported media” and “Jellyfin IDs / provider IDs” enrichment described in point 1.

However, MD5 baseline hashing is not actually wired into the scan. `FileRecord` has an `md5_hash` field, and the `files` table in `InventoryRepository` has an `md5_hash` column, but `FileScanner._process_file(...)` never calls any MD5 function and always constructs `FileRecord` with `md5_hash=None`. MD5 hashing does exist elsewhere in the code (in `FileHasher` inside `transaction_manager.py`), but that is used for transaction logging during execution, not during the scan. Because MD5 is not computed or stored by the scanning pipeline, the “baseline for verification and duplicates” part of point 1 is not implemented at scan time.

The other “during scan” integrations in point 1 are also absent. A search of the Python code shows no references to AniList or AniDB, and there is no anime-specific metadata enrichment in the scanning workflow. Likewise, the scan is single-threaded: it iterates over extensions and files in ordinary Python loops; there is no pool of worker threads or asynchronous IO. So there is no parallelized hashing or parallel scan logic aimed at speeding up MD5 computation on large libraries.

From this, the conclusion is: the project **does** implement multi-folder recursive scanning, durable inventory storage, extension-based filtering, and optional Jellyfin cross-reference; it **does not yet** implement MD5 hashing as part of the scan, AniList/AniDB scraping during the scan, or parallelized hashing.

### Point 2 – Structural summary, duplicates, and Jellyfin/usage comparison

Point 2 asks for a structural summary of the library, including per-folder counts and the ability to talk about things like “178 videos in this folder,” plus optional duplicate grouping and Jellyfin/usage comparisons.

The structural summary portion is implemented. `FileScanner.get_folder_structure(...)` takes the list of `FileRecord`s from a scan and builds a dictionary keyed by folder path, where each folder entry tracks total size, file count, and per-extension counts and sizes. `JellyRancherClean.step_2_overview(...)` uses this structure and the enriched `self.scanned_files` to populate a `QTreeWidget` with columns for folder path, number of files, size in megabytes, a Jellyfin match count per folder, and a short description of the most common file types. This yields a real, navigable overview of the folder hierarchy with counts and sizes, which is exactly the kind of structural summarization point 2 describes.

The code also partially incorporates Jellyfin’s view of the library into the summary. Because file records can carry a `jellyfin_matched` flag, `step_2_overview` can count how many files in each folder are already known to Jellyfin and color the Jellyfin column green or yellow depending on whether all or only some files are matched.

What is missing is the MD5-driven and usage-driven enhancements described in the bullets. There is no code that groups files by identical MD5 hashes or reports “duplicates detected via MD5” in the overview; this is consistent with the fact that MD5 is never computed during scanning. There is also no code to query playback stats, sessions, or a playback-reporting plugin from Jellyfin; nothing in the Python code refers to watch counts, play duration, or similar metrics. Finally, there is no “before/after” comparison mode that would compare a post-reorg plan against Jellyfin’s current view; the overview is simply a snapshot with match counts.

Thus, point 2 is **implemented** in terms of a hierarchical folder summary with per-folder counts, sizes, and basic Jellyfin match counts, but the MD5-based duplicate grouping, playback-time analytics, and richer “before/after” analytics are **not yet implemented**.

### Point 3 – LLM reorganization proposal and detected media list

Point 3 asks for taking a summarized view of the folder structure, sending it to a reasoning LLM, and getting back both a list of detected movies/TV shows and a reorganization proposal.

This flow is implemented end to end. Once scanning and the folder structure are in place, `JellyRancherClean.step_3_llm_proposal(...)` spawns an `LLMAnalysisWorker`, passing it `folder_structure` and `scanned_files`. Inside that worker, `_build_structure_summary()` converts the internal folder structure into a model-ready summary: for each folder, it records path, file count, total size, file-type breakdown, and a deduplicated list of Jellyfin provider ID dictionaries for files that are matched in Jellyfin. This summary deliberately avoids enumerating every file name, keeping the LLM input at a structural level, as the high-level plan suggests.

The `LLMStructureAnalyzer` then takes this summary, builds a detailed prompt that explains Jellyfin naming conventions and structural expectations, and sends it to a reasoning model via `PoeClient`. The prompt explicitly instructs the LLM to respond with JSON containing a `detected_media` list (with `title`, `type`, `year_estimate`, `current_location`, `confidence`, and notes), a `reorganization_plan` object with folder changes and compliance issues, a `multi_part_episodes` list, and a `reasoning` string. The analyzer parses the LLM’s response back into a Python dict and returns it.

When the worker finishes, `JellyRancherClean._on_llm_finished(...)` stores the analysis in `self.llm_analysis`, extracts `self.detected_media` and `self.reorganization_plan`, and displays a textual summary in the GUI showing the detected media, a summary of the reorganization plan, any multi-part episodes, and the model’s reasoning. This matches the core of point 3: the folder structure is being fed to a reasoning LLM, and the result is a structured set of detected movies/TV shows plus a reorg proposal.

What is not implemented are the extra context and automation bullets under point 3. The structure summary that is passed to the LLM does not contain MD5 hashes or any notion of duplicate groups; it only has size, counts, and provider ID aggregates. There is also no integration with Trakt, Ani-Sync, or any other watch-history providers, and therefore no watched/unwatched or rating-driven prioritization in the prompt. Lastly, while the LLM is allowed to describe “API-driven actions,” the current code simply records and displays the plan; there is no pipeline that interprets those suggestions into concrete Jellyfin API calls.

So, for point 3: the application **does** implement the key LLM loop (structure in, detected media + reorg plan out) and surfaces it to the user, but the deeper context sources (MD5 duplicate info, Trakt-like history) and any direct API-automation based on the LLM’s output are **not implemented**.

### Point 4 – Canonical metadata database and multi-part episodes

Point 4 calls for taking the LLM-detected media list, querying external metadata sources to build a canonical database of movies and TV shows, and handling multi-part episodes so they can be represented correctly for Jellyfin.

This pipeline is implemented in two main pieces: `MetadataLookupWorker` in the GUI and `MediaMetadataLookup` in the media layer. After Step 3, `self.detected_media` holds the movies and TV shows that the LLM identified. When the user triggers Step 4, `step_4_metadata(...)` sets up a `MetadataLookupWorker` with that list and the `scanned_files`, and the worker instantiates a `MediaMetadataLookup` configured with TMDB and/or OMDb API keys. The worker loops over each detected item, dispatching to `lookup.lookup_movie(...)` or `lookup.lookup_tv_show(...)` as appropriate.

`MediaMetadataLookup` performs the actual external lookups. For movies, it either uses a Jellyfin-provided TMDB ID or searches TMDB (and optionally OMDb) by title and year to get canonical titles, years, overviews, IDs, and poster paths. For TV shows, it queries TMDB’s TV endpoints, retrieving overall show details plus season-by-season episode lists. As it builds season data, `_get_season_episodes(...)` marks episodes where the name suggests multiple parts (e.g., containing “part 1 / part 2” patterns) with `is_multi_part=True`.

Back in `MetadataLookupWorker`, the canonical database structure (`canonical_db`) collects all looked-up movies and shows, attaches the original LLM detection entries, and populates a `multi_part_episodes` list by scanning each show’s seasons for episodes flagged as `is_multi_part`. Each entry in this list includes the show title, season number, episode number, and a flag `needs_nfo=True`, directly acknowledging the need for special handling in Jellyfin for those episodes. The worker then logs a human-readable summary in the GUI (counts of movies, shows, multi-part episodes, and any lookup failures) and writes the full canonical database to a timestamped JSON file in `data/`.

What is missing are the downstream actions that the plan imagines. The code identifies which episodes are likely multi-part and labels them as needing NFOs, but it does not actually generate `.nfo` files or wire a path from these entries to a file-writing subsystem or Jellyfin API refresh requests. The plan’s mention of artwork from Fanart.tv and theme songs from Themerr is also not reflected in the code; metadata lookups expose poster paths from TMDB, but there is no dedicated artwork/theme download pipeline or plugin integration. Duplicate or “merge versions” handling at the canonical DB level is not present: there is no logic to collapse multiple files or records into unified movie/show entries beyond what TMDB/OMDb return. Finally, while Jellyfin provider IDs can be passed into the lookup functions, the mapping from `detected_media` items back to specific `FileRecord`s and specific Jellyfin items is intentionally simplistic in this version, as acknowledged in comments.

The resulting conclusion is that point 4 is **implemented** in its core: the system builds and persists a canonical metadata database of movies and TV shows using TMDB/OMDb, and it identifies multi-part episodes that need special handling. It **does not yet** implement NFO file generation, artwork/theme retrieval, robust duplicate/merge handling, or a full round-trip where the canonical DB directly drives Jellyfin updates.

### Summary of Where Points 1–4 Stand

- Point 1: Scanning, inventory, and Jellyfin cross-reference are implemented; MD5 baseline hashing during scan, AniList/AniDB integration, and parallel hashing are not.
- Point 2: Hierarchical folder summary with counts, sizes, and basic Jellyfin match counts is implemented; MD5-based duplicate grouping, playback/usage analytics, and “before/after” comparisons are not.
- Point 3: The core LLM loop (structure → detected media + reorg plan) is implemented and integrated into the GUI; richer context (MD5 duplicates, Trakt/Ani-Sync) and API-level automation of the LLM’s suggestions are not.
- Point 4: Building and saving a canonical metadata database with TMDB/OMDb and tagging multi-part episodes is implemented; NFO generation, artwork/theme integration, and advanced duplicate/merge handling are not.

These conclusions are all drawn directly from the observable code paths: where functions like `scan_folder`, `get_folder_structure`, `analyze_structure`, `lookup_movie`, and `lookup_tv_show` are invoked from the GUI, what fields they populate, and what external services and data they do (and do not) touch.

### To-dos

- [ ] Integrate MD5 hashing into the scanning/inventory pipeline so `FileRecord.md5_hash` and the SQLite `md5_hash` column are populated during or immediately after scans.
- [ ] Use stored MD5 hashes to detect and group duplicate files and surface them in the UI overview and/or a dedicated duplicates report.
- [ ] Extend `LLMStructureAnalyzer` prompt construction to include MD5-based duplicate info and (in the future) playback/Trakt-style data, so reorg proposals are more informed.
- [ ] From the canonical metadata DB, add NFO generation, artwork/theme acquisition hooks, and eventual execution wiring via `TransactionManager` and `ActionType.CREATE_NFO`.