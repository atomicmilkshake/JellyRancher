# JellyRancher: Vision & Competitive Analysis

**Document Created:** 2025-12-04
**Author:** Claude Code (understanding synthesized from JellyRancher Redux documents)

---

## The Problem JellyRancher Solves

You have a folder—probably called "Downloads" or "unsorted"—containing thousands of media files accumulated over years. The filenames are chaos:

```
YIFY.Breaking.Bad.S01.720p.HDTV.x264-DEMAND[ettv].mkv
rarbg.inception.2010.1080p.bluray.mkv
the.matrix.1999.dvdrip.xvid-group.avi
Game.of" "Thrones.S08E06.FINAL.WEB-DL.mkv
MovieName (2020) [1080p] [BluRay] [5.1].mkv
```

You want these organized for Jellyfin, which expects:

```
/Movies/Inception (2010)/Inception (2010).mkv
/TV Shows/Breaking Bad (2008)/Season 01/Breaking Bad S01E01.mkv
```

**The manual approach:** Open each file, figure out what it is, look up the year on IMDB, rename it, move it to the right folder. For 10,000 files, this takes weeks.

**The regex approach (FileBot):** Write patterns to match your specific chaos. Works well for consistent naming, breaks on edge cases, requires constant maintenance.

**The JellyRancher approach:** Use an LLM that can *read* messy filenames like a human would, propose reorganization, let you review and approve, then execute safely with full rollback capability.

---

## The Core Loop (MVP)

```
┌─────────────────────────────────────────────────────────┐
│                    THE CORE LOOP                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   SCAN  →  LLM  →  PREVIEW  →  EXECUTE  →  ROLLBACK   │
│     ↓       ↓         ↓           ↓           ↓        │
│   Files   Analyze   Review     Move with    Undo if    │
│   found   & parse   proposal   BLAKE3       wrong      │
│                                verify                   │
└─────────────────────────────────────────────────────────┘
```

This is the minimum viable loop that proves the concept works:

1. **Scan** - Recursively inventory a folder
2. **LLM** - Send structural summary to Claude/GPT, receive JSON proposal
3. **Preview** - Show before/after comparison, let user review
4. **Execute** - Copy files, verify with BLAKE3 hash, delete originals only after verification
5. **Rollback** - If anything went wrong, undo everything

---

## The Full 10-Step Workflow

Once the core loop is proven, the full vision expands to:

### Step 1: Select Folders
Add multiple source folders to a single project. Your Downloads folder, your "to sort" folder, that external drive.

### Step 2: Scan
Recursive file inventory with BLAKE3 hashing. Know exactly what you have.

### Step 3: Exclude
Checkbox dialog to exclude folders you don't want processed. Browser cache, temp files, partial downloads.

### Step 4: Categorize (Sorting Canvas)
**This is the secret weapon.** Drag-and-drop files/folders into category "buckets":
- Movies
- TV Shows
- Games
- Music
- Books
- Unsorted

Why? Because movies and TV shows need different LLM prompts. A TV show prompt knows about S01E01 patterns. A movie prompt focuses on year detection. Sorting first means better LLM results.

### Step 5: Diagnose
Find problems before they become problems:
- Zero-byte files (corrupted downloads)
- Duplicate files (same hash, different names)
- Orphaned subtitles (no matching video)

### Step 6: Configure LLM
Select which model to use (Claude-3.5-Sonnet, GPT-4, local LLM). Configure API keys. Set confidence thresholds.

### Step 7: Submit Per-Bucket
Each bucket gets its own specialized prompt:
- Movies bucket → Movie-specific Jellyfin naming rules
- TV Shows bucket → Series/season/episode patterns
- Games bucket → Different organization entirely

### Step 8: Review Proposal
Dual tree view: original structure on left, proposed structure on right. Color coding:
- Green: New destination
- Yellow: Moved
- Red: Unrecognized (needs attention)

Approve, reject, or modify individual items.

### Step 9: Canonical Database
The ground truth. When the LLM identifies "Breaking Bad," store that metadata from TMDB/TVDB:
- Official title: "Breaking Bad"
- Year: 2008
- TVDB ID: 81189

Now if the LLM later encounters another file from the same series, it references the canonical database instead of guessing again. Fix once, apply everywhere.

### Step 10: Execute
The moment of truth. For each approved move:
1. Calculate source BLAKE3 hash
2. Create destination directory
3. Copy file
4. Calculate destination BLAKE3 hash
5. Verify hashes match
6. Delete source only if verified
7. Log operation to transaction log

If power fails mid-operation? Resume from transaction log. Something went wrong? Full rollback from log.

---

## Post-Organization: Subtitle Handling

After files are organized:

### Subtitle Audit
Scan library for videos missing subtitles. Report coverage:
- 847 videos
- 623 have subtitles (73%)
- 224 missing subtitles

### Subtitle Acquisition
Fetch missing subtitles from OpenSubtitles or similar. Match to videos. Name correctly for Jellyfin:
```
Movie Name (2020).en.srt
Movie Name (2020).es.srt
```

---

## Key Architectural Concepts

### Round-Up (Project Session)
A saved project. You can work on your "Big Library Cleanup" over multiple sessions, save progress, close the application, come back next week, and resume exactly where you left off.

### Human Gates
Explicit approval steps. The LLM proposes, but YOU approve before anything moves. No automated destruction.

### Copy-Verify-Delete
Never move files. Copy, verify the copy matches (BLAKE3), then delete original. If verification fails, keep original, report error.

### Canonical Database
Ground truth that cascades. Fix "Stranger Things" metadata once → all 47 files referencing it update automatically.

---

## The Ultimate Success Test

> **"After running JellyRancher, the user never needs to manually fix metadata in Jellyfin."**

This is the goal. If you have to open Jellyfin and manually edit titles, years, or episode numbers, JellyRancher failed.

---

## Competitive Analysis: What Already Exists

### FileBot
The closest existing tool. Rule-based renaming using TVDB/TMDB lookups.

**Strengths:**
- Mature, well-tested
- Powerful regex engine
- Good TVDB/TMDB integration

**Limitations:**
- No LLM intelligence—can't "read" `YIFY.Breaking.Bad.S01.720p.x264-DEMAND[ettv]` without explicit patterns
- Requires user to configure regex for their specific filename chaos
- No sorting canvas (pre-categorization)
- No canonical database with bulk correction
- No human gates with visual before/after preview

### Sonarr/Radarr
Excellent for *new* content acquired through their pipeline.

**Strengths:**
- Automated downloading and organizing
- Great for ongoing library management
- Strong community

**Limitations:**
- Not designed for "here's my existing 10,000-file mess, please fix it"
- Works best with content acquired through its own pipeline
- Not a chaos-to-order tool

### tinyMediaManager
Metadata management and NFO generation.

**Strengths:**
- Good metadata editor
- NFO file generation
- Multiple provider support

**Limitations:**
- Rule-based, not LLM-powered
- Doesn't handle the initial chaos-to-order transformation
- Manual-heavy for large libraries

### Plex/Jellyfin Built-in Detection
Both try to auto-detect media from filenames.

**Strengths:**
- No extra tools needed
- Works well with properly named files

**Limitations:**
- Famously struggles with non-standard naming
- "Why is 'The Matrix' showing up as 'matrix.1999.dvdrip.xvid-group'?"

### Manual ChatGPT Approach
Ask ChatGPT: "What movie is `rarbg.inception.2010.1080p.bluray.mkv`?"

**Strengths:**
- Actually works
- LLM understands messy filenames

**Limitations:**
- Manual process: ask, read answer, rename file, repeat 10,000 times
- No automation
- No rollback
- No organization

---

## What Makes JellyRancher Different

| Feature | FileBot | Sonarr/Radarr | tinyMediaManager | JellyRancher |
|---------|---------|---------------|------------------|--------------|
| **LLM-powered identification** | No | No | No | **Yes** |
| **Sorting canvas (pre-categorization)** | No | No | No | **Yes** |
| **Human gates (approval workflow)** | Partial | No | Yes | **Yes** |
| **Canonical database (bulk correction)** | No | No | Partial | **Yes** |
| **Per-category LLM prompts** | N/A | N/A | N/A | **Yes** |
| **Copy-verify-delete safety** | Partial | Yes | No | **Yes** |
| **Full rollback capability** | No | Partial | No | **Yes** |
| **Designed for existing chaos** | Partial | No | Partial | **Yes** |

---

## The Short Answer

**Does anything in the real world already do all this?**

**No.**

There are pieces:
- FileBot does rule-based renaming very well
- Some people script custom solutions
- Various Python scripts exist for media organization

But the combination of:
- LLM-powered identification (reading filenames like a human)
- Sorting canvas with per-bucket prompts
- Human gates with visual before/after preview
- Canonical database with bulk correction cascade
- Copy-verify-delete with full rollback
- Round-Up persistence for multi-session projects

**That combination is novel.** JellyRancher automates what people currently do manually with ChatGPT + file explorer + lots of patience.

---

## Where JellyBase Fits In

JellyBase is a **complementary tool**, not part of the core JellyRancher workflow.

**JellyRancher:** Prepares files for Jellyfin (the chaos-to-order transformation)

**JellyBase:** Manages what's already in Jellyfin:
- Browse library contents
- Validate metadata health
- Manage collections
- Find duplicates and grouping issues

Think of it as:
- JellyRancher = The onboarding tool (getting files INTO Jellyfin properly)
- JellyBase = The maintenance tool (keeping Jellyfin healthy)

---

*Document generated by Claude Code from analysis of JellyRancher Redux documentation package.*
