# Application Proposal for Jellyfin Media Organizer

## Core Requirements

1. **Scan a selected folder or multiple folders recursively to obtain a bare file list, with each row in the file being a single, complete file path.**
   - During the scan, compute and store MD5 hashes for each file (alongside paths) in the output (e.g., as a CSV/JSON column) to serve as a baseline for verification and duplicates.
   - Before or during the scan, optionally query Jellyfin's API for existing item paths and metadata to cross-reference against local files, identifying already-imported media and enriching the list with Jellyfin IDs or tags (e.g., via GET /Items?Recursive=true&IncludeItemTypes=Movie,Episode&Fields=Path).
   - Incorporate metadata scraping from plugins like AniList or AniDB (for anime-specific libraries) during the scan to enrich the list with preliminary tags or IDs.
   - Filter by media types (videos, subs, etc.); make hashing parallelized for speed on large libraries.

2. **Summarize the structure, so if a folder happens to be called Star Trek The Next Generation, we see (178 videos in this folder), or we see 7 season folders, with the number of video files in each of those folders.**
   - Enhance duplicate detection by grouping files with matching MD5 hashes in the summary (e.g., "178 videos: 5 duplicates detected via MD5"). Include breakdowns by file type, size, or total.
   - Incorporate Jellyfin's view of the library (via API) into the summary for a "before/after" comparison, e.g., "178 videos: 50 already in Jellyfin (matched via paths/hashes)". Flag potential overlaps or gaps (e.g., via GET /Views or GET /UserViews).
   - Pull in playback stats from the Playback Reporting plugin to include usage insights in the summary (e.g., "178 videos: 50 watched, total playtime 200 hours").
   - Generate visual representations like text-based trees.
   - The goal here is to capture enough of the folder structure for reorganization to be possible, without flooding the context of the LLM in the next step with filenames, when that is essentially too much information (reorganizaiton can be proposed without knowing every single freaking file)

3. **Submit the folder structure to a very smart, reasoning LLM for proposed reorganization for preparation for Jellyfin. Also obtain from the LLM a list of detected movies and tv shows.**
   - Feed API-queried Jellyfin data (e.g., current items, collections) and MD5-based dupes into the LLM prompt as context to generate informed proposals (e.g., "Align with existing Jellyfin structure: [API snapshot]").
   - Include data from Trakt or Ani-Sync plugins in the prompt for watched/scrobble history, enabling proposals like "Prioritize unwatched seasons" or "Group by user ratings."
   - LLM can suggest API-driven actions, like adding to collections.

4. **Use the LLM-detected list of movies and TV shows to query correct movie years, correct tv show names and years, and correct season structure and episode titles and episode numbers to build a canonical database of the detected movies and TV shows. Be able to handle multi-part episodes presented in feature length, such as the pilot to Star Trek The Next Generation (where episodes 1 and 2 are Encounter at Farpoint parts 1 and 2, respectively). That way episode numbering is not out of whack in Jellyfin. I believe this situation requires an NFO file to inform Jellyfin about the multi-part episode.**
   - Cross-verify the canonical DB against Jellyfin's metadata via API queries, pulling in existing ProviderIds (e.g., TMDb IDs) for consistency (e.g., via GET /Items/{itemId}?Fields=ProviderIds).
   - For multi-part episodes, generate NFOs and test via API refresh on samples.
   - Extend queries to include artwork from Fanart.tv plugin (posters, backdrops) and theme songs from Themerr plugin, storing them in the DB.
   - For duplicates, integrate Merge Versions plugin logic to auto-group repeated movies during DB build.

5. **Using the canonical database, and the LLM-generated reorganization proposal, extrapolate the proposed reorganization and file renaming to produce an editable table for user review, with actions suggested for each row. Actions would be delete, move, do nothing, review further, etc.**
   - Add MD5 columns (current and proposed) and suggest actions based on hashes, e.g., "Delete: MD5 duplicate."
   - Include columns for Jellyfin status (e.g., "Already in library: Yes/No, via API match") and suggested API actions (e.g., "Refresh after move").
   - Add columns for artwork previews (from Fanart) and theme song suggestions (from Themerr). Suggest actions like "Add to box set" via TMDb Box Sets plugin.
   - Make the table interactive, sortable, with bulk edits.

6. **Execute the revised, finalized organization plan. Subtitle files related to video files must "come along" with the video file, and be properly named according to Jellyfin documentation.**
   - During execution, verify each move/rename with MD5: Hash source before, perform action (copy-then-rename), hash destination after; mismatch triggers rollback and log.
   - After operations, trigger targeted API refreshes for affected items/libraries (e.g., POST /Items/{itemId}/Refresh or POST /Libraries/{libraryId}/Refresh) and auto-create/populate collections (e.g., POST /Collections/{collectionId}/Items).
   - During execution, auto-download and embed artwork/themes using Fanart/Themerr, and create collections/box sets with TMDb Box Sets.
   - For subtitles, leverage Subtitle Extract plugin to handle embedded ones automatically post-move.
   - Generate a change journal logging paths, actions, MD5s, and API results.

7. **Evaluate subtitle coverage. Find out which episodes of tv shows and which movies already have correct external subtitles or correct embedded subtitles (can be checked using ffprobe). Produce a list of tv episodes and movies that do not have subtitles at all.**
   - Supplement ffprobe with API queries for media streams to get server-side validation (e.g., GET /Items/{itemId}?Fields=MediaStreams).
   - Use MD5 to compare subs; include "API-Validated" status in the report.
   - Use WizdomSubs or similar language-specific plugins as fallbacks if standard sources lack coverage.
   - Integrate with Kodi Sync Queue for real-time sync evaluation if using Kodi clients.

8. **Obtain subtitles for tv episodes and movies that don't have them.**
   - After adding subs, trigger API refreshes to confirm detection (e.g., POST /Items/{itemId}/Refresh).
   - Verify new subs with MD5; use API to check if they're now listed in streams.
   - Beyond Open Subtitles, add support for Bazarr for automated searching across providers, with language preferences.

## Overarching Enhancements
- **Safety and Versioning**: Mandate dry-runs, backups, and change journals. Pair MD5 with Git/LFS for optional versioning; expand with tools like Restic or Duplicati for automated library backups post-execution.
- **Feedback and Iteration Loop**: Post-reorg, schedule periodic API queries for playback stats (e.g., GET /Sessions) to assess structure. Feed to LLM for refinements; integrate Playback Reporting for analytics.
- **Automation with *Arr Suite (Sonarr, Radarr, Lidarr)**: Hand off to these for ongoing monitoring/downloads/renaming after reorg; query for missing content to feed back to LLM.
- **Request and Discovery Tools (Jellyseerr/Overseerr)**: Suggest "missing episodes" based on canonical DB, then queue via Jellyseerr for post-download re-scans.
- **Scrobbling and Sync (Trakt, Ani-Sync)**: Auto-sync watched status during execution; use for personalized LLM proposals.
- **Theme and UI Enhancements (Jellyfin-Enhanced, Themerr)**: Add theme song downloads and client tweaks for immersive libraries.
- **Advanced Reporting and Analytics**: Generate post-reorg dashboards from Reports/Playback Reporting plugins (e.g., "Top genres by watch time").
- **Plugin-Style Extension**: Offer mode to install as Jellyfin plugin for real-time hooks (e.g., auto-reorg on new files).
- **Configurability and UX**: Add toggles for features (e.g., hashing mode: MD5/CRC32; API integration); support GUI/CLI; ensure cross-platform compatibility.
- **Performance and Scalability**: Multi-threading for scans/hashing; chunking for large libraries; local processing for privacy.
