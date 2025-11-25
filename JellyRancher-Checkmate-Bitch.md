### **Jellyfin Media Organizer: The Right Polish**

---

## **What This Application Does**

Transforms chaotic media libraries into Jellyfin-ready structures through scanning, intelligent reorganization, metadata enrichment, and subtitle management—with mandatory human approval before any destructive operations.

---

## **The 8-Step Workflow**

### **Step 1: Recursive File Scan**
Scan selected folders recursively to produce a complete file inventory. Compute MD5 hashes during the scan for integrity verification and duplicate detection. Filter by media file extensions (video and subtitle formats). Log any access errors for user review.

**Why MD5:** Enables duplicate detection across renames, verifies move operations didn't corrupt files, and provides rollback capability.

---

### **Step 2: Structural Summary**
Condense the file inventory into a hierarchical summary that preserves folder structure without listing individual filenames. Group files by directory, count videos per folder, detect season patterns, and calculate aggregate statistics.

**Why This Matters:** LLMs can't process 10,000 filenames efficiently. "178 videos in 7 season folders" gives structural context without exceeding token limits.

---

### **Step 3: LLM Proposal & Title Detection**
Submit the structural summary to a reasoning LLM for two outputs:
1. Proposed reorganization following Jellyfin naming conventions
2. List of detected TV shows and movies for metadata lookup

**Design Decision:** Use rule-based detection (regex for S01E05 patterns) for obvious cases. Use LLM as a fallback oracle for ambiguous situations. Validate all LLM output—don't blindly trust it.

**Critical Flag:** Multi-part episodes presented as single files (e.g., "Encounter at Farpoint" containing episodes 1 and 2).

---

### **Step 4: Canonical Database Construction**
Query authoritative metadata sources (TMDb for movies/TV, AniDB for anime) to build a ground truth database for all detected titles. Store correct years, season structures, episode titles, and episode numbers.

**Multi-Part Episode Handling:** When the LLM flags combined episodes in a single file, create separate database entries for each episode but link them together. Generate NFO files to inform Jellyfin about the multi-part structure so episode numbering stays correct.

**Conflict Resolution:** When metadata sources disagree with detected files (e.g., TMDb says 26 episodes but only 24 files exist), flag for user review in Step 5.

---

### **Step 5: Review Table Generation**
Present an editable table showing current paths, proposed paths, detected metadata matches, and suggested actions for each file. 

**Available Actions:**
- `move` - Rename and relocate
- `delete` - Remove (for duplicates or junk)
- `merge` - Combine separate files that should be treated as one
- `do_nothing` - Keep as-is
- `review` - Flag for manual inspection

**User Control:** Full editing capability. Sort, filter, bulk operations. User must explicitly approve before execution begins.

---

### **Step 6: Execution with Verification**
Execute the approved plan using safe operations: copy (don't move), verify with MD5, then delete source only if verification passes. Related subtitle files must move with their video files and follow Jellyfin naming conventions.

**Safety Measures:**
- Dry-run mode to preview operations
- MD5 verification before and after
- Copy-verify-delete (never rename in place)
- Comprehensive operation logging
- Resume capability for interrupted operations
- Rollback capability if needed

**Subtitle Naming:** Follow Jellyfin standard (e.g., `Movie.en.srt`, `Show - S01E01.en.forced.srt`).

---

### **Step 7: Subtitle Coverage Audit**
After reorganization is complete, evaluate which files have subtitles (external or embedded) and which don't. Use media analysis tools to check for embedded subtitle streams. Validate that detected subtitles have identifiable languages and usable formats.

**Output:** Categorized lists showing files with complete coverage, files with problematic subtitles (unknown language, image-based only), and files with no subtitles at all.

---

### **Step 8: Subtitle Acquisition**
Fetch missing subtitles from external sources (OpenSubtitles, Subscene, Addic7ed). Use hash-based matching when possible, falling back to metadata or filename matching. Respect user's language preferences.

**Post-Download:** Verify subtitle files are valid, save using Jellyfin naming conventions, and update the database.

---

## **Guiding Principles**

**Human Authority:**
- Steps 3→4: User approves LLM-detected titles before metadata queries
- Step 5→6: User reviews and finalizes plan before execution
- No automatic execution without explicit user initiation

**Safety First:**
- All operations are logged
- All moves are verified
- Rollback is always possible
- Dry-run mode is mandatory before first execution

**Separation of Concerns:**
- Organization (Steps 1-6) is independent from subtitle handling (Steps 7-8)
- Users can organize first, handle subtitles later (or never)
- Each step builds on the previous—no skipping

---

## **What This Plan Deliberately Excludes (For Now)**

**Not in MVP:**
- Real-time file monitoring / plugin mode
- Integration with *arr suite (Sonarr, Radarr)
- Scrobbling services (Trakt, Ani-Sync)
- Analytics dashboards
- Theme song downloads
- Automated scheduling

**Rationale:** Ship a working core first. These are extensions, not foundations. Build them after the 8-step workflow is proven.

---

## **Success Looks Like**

1. User scans their chaotic 10,000-file library in minutes
2. LLM proposes sensible reorganization following Jellyfin conventions
3. User reviews and adjusts the plan in an intuitive interface
4. Execution completes without data loss or corruption
5. Jellyfin recognizes all media immediately, including multi-part episodes
6. Subtitles are properly associated and selectable

**The Ultimate Test:** After running this tool, the user never needs to manually fix metadata in Jellyfin.