# Analysis Tab Improvement Plan

**Date:** 2025-11-22
**Status:** Planning Phase

---

## Decision Point 1: Heuristic Enhancement Scope

### Why This Matters

The current `regex_structure_analyzer.py` is a **standalone implementation** that doesn't leverage 2,400+ lines of battle-tested parsing code already in the codebase. The question is: how do we unify this without creating a maintenance nightmare?

### Option A: Integrate Existing Backend Code (Adapter Pattern)

**What it means:** Create a `HeuristicAnalyzer` class that delegates to existing backends:
```python
class HeuristicAnalyzer:
    def __init__(self):
        self.movie_backend = MovieNameBackend()
        self.episode_backend = EpisodeTitleBackend()
        self.folder_scanner = FolderStructureScanner()

    def analyze(self, files, folders):
        # Use folder_scanner to classify each folder
        # Use movie_backend for movie folders
        # Use episode_backend for TV folders
```

**Advantages:**
- Fastest to implement (days, not weeks)
- Preserves existing tested code
- Clear separation of concerns
- Each backend can evolve independently

**Disadvantages:**
- Three different coding styles/patterns to maintain
- Potential inconsistencies in confidence scoring
- Some duplication (each backend has its own codec patterns)
- Doesn't address the gaps (anime, pre-1978, editions)

**Verdict:** Safe but doesn't achieve "maximum kickass-ness"

---

### Option B: Add Wikipedia/TMDB Canonical Verification Layer

**What it means:** After regex parsing, verify against canonical sources:
```python
def analyze(self, files):
    parsed = self._regex_parse(files)  # Fast, offline
    verified = self._verify_canonical(parsed)  # Network calls
    return verified
```

**Advantages:**
- Catches regex mistakes ("Br Ba" → "Breaking Bad")
- Provides authoritative metadata (air dates, episode counts)
- Wikipedia parser already exists and is sophisticated
- TMDB integration already exists

**Disadvantages:**
- Network dependency (slower, can fail)
- Rate limiting concerns (Wikipedia: 11 sec delay)
- Doesn't fix the regex weaknesses—just patches over them
- Could mask underlying parsing bugs

**Verdict:** Valuable addition but shouldn't replace fixing the core heuristics

---

### Option C: Full Consolidation (The "Right Way")

**What it means:** Extract the best patterns from all modules into a unified, well-architected analyzer.

**Why context window is a concern:**
- `tv_episode_cache.py`: 1,456 lines
- `movie_name_backend.py`: ~400 lines
- `episode_title_backend.py`: ~300 lines
- `folder_structure_scanner.py`: ~250 lines
- `regex_structure_analyzer.py`: ~450 lines
- Total: **~2,850 lines** to understand, extract from, and consolidate

Cannot hold all of this in context simultaneously. A careless consolidation would lose edge cases.

**The Careful Approach:**
1. **Phase 1: Pattern Audit** - Document every regex pattern across all modules in a single reference file
2. **Phase 2: Gap Analysis** - Identify what's missing (anime, editions, pre-1978)
3. **Phase 3: Architecture Design** - Design the unified class structure BEFORE coding
4. **Phase 4: Incremental Build** - Build one component at a time with tests
5. **Phase 5: Deprecate Old** - Mark old modules as deprecated, redirect imports

**Advantages:**
- Single source of truth for media parsing
- Consistent confidence scoring
- Easier to extend (one place to add anime patterns)
- Maximum kickass-ness

**Disadvantages:**
- Highest effort (1-2 weeks of careful work)
- Risk of regression if done carelessly
- Requires comprehensive test suite

**Recommendation for Option C:**
Don't do it all at once. Create a **new** `scripts/media/unified_media_parser.py` that:
1. Starts with the best architecture (folder-aware, multi-strategy)
2. Imports and wraps existing backends initially
3. Gradually inlines/improves the patterns over multiple phases
4. Each phase is a testable, committable unit

---

### Option D: Hybrid Approach (Recommended)

**Phase 1 (This Session):**
- Create `UnifiedMediaParser` class with clean interface
- Wrap existing backends (adapter pattern)
- Add folder classification as first-class citizen
- Add the missing patterns (anime, editions, pre-1978 years)

**Phase 2 (Future Session):**
- Add optional canonical verification layer (Wikipedia/TMDB)
- Cache verification results in Round-Up database

**Phase 3 (Future Session):**
- Gradually inline the best patterns from backends
- Deprecate redundant modules

**Advantages:**
- Immediate improvement without risk
- Each phase is independently valuable
- Maintains test coverage throughout
- Achieves maximum kickass-ness over time

---

## Decision Point 2: Prompt Format for LLM

### Why This Matters

Current JSON format for a 5,000-file scan could be **50,000+ tokens**. At $0.003/1K tokens (Claude), that's $0.15 per analysis. At $0.01/1K (GPT-4), that's $0.50. Token efficiency directly impacts cost and context window usage.

### Option A: Tree Format

```
📁 Movies/
├── Inception (2010)/
│   ├── Inception (2010).mkv [2.1 GB] [1080p] [x264]
│   └── Inception (2010).en.srt
├── The Matrix (1999)/
│   └── The.Matrix.1999.BluRay.1080p.x264.mkv [4.2 GB]
📁 TV Shows/
├── Breaking Bad/
│   ├── Season 01/
│   │   ├── S01E01 - Pilot.mkv [1.1 GB]
```

**Advantages:**
- ~60% fewer tokens than JSON
- Mirrors how humans think about folder structure
- LLMs understand tree format well (trained on `tree` command output)
- Metadata inline where relevant

**Disadvantages:**
- Less structured for LLM parsing of response
- Custom parsing logic needed
- Some metadata harder to represent (MD5 hashes, timestamps)

**Token Comparison (hypothetical 100 files):**
- JSON with indent=2: ~8,000 tokens
- Tree format: ~3,000 tokens
- **Savings: 62%**

---

### Option B: Compact Single-Line Paths

```
M|Inception (2010)/Inception (2010).mkv|2.1GB|1080p|x264|abc123
M|The Matrix (1999)/The.Matrix.1999.BluRay.mkv|4.2GB|1080p|x264|def456
T|Breaking Bad/Season 01/S01E01 - Pilot.mkv|1.1GB|1080p|x265|ghi789
```

**Advantages:**
- Most token-efficient (~70% savings)
- Easy to parse programmatically
- Every file on one line = easy to reference in response

**Disadvantages:**
- Loses visual hierarchy (folder nesting not obvious)
- Harder for LLM to "see" folder structure patterns
- Less human-readable in preview

---

### Option C: Minified JSON

```json
{"Movies":{"Inception (2010)":{"files":[{"n":"Inception (2010).mkv","s":2100,"q":"1080p"}]}}}
```

**Advantages:**
- Still structured/parseable
- ~40% token savings
- Familiar format for LLM

**Disadvantages:**
- Less savings than tree format
- Harder to read in preview
- Nested structure still verbose

---

### Recommended: Hybrid Tree + Structured Suffix

```
=== FOLDER STRUCTURE ===
📁 Movies/
├── Inception (2010)/
│   ├── Inception (2010).mkv [2.1 GB, 1080p, x264]
│   └── Inception (2010).en.srt
├── [ISSUE] The.Matrix.1999.BluRay/ ← folder name doesn't match Jellyfin format
│   └── The.Matrix.1999.BluRay.1080p.x264.mkv [4.2 GB]

=== DETECTED ISSUES (3) ===
1. The.Matrix.1999.BluRay/ - Folder naming non-compliant
2. Orphan subtitle: random.en.srt (no matching video)
3. Duplicate: Movie.mkv has 2 copies (MD5 match)

=== STATISTICS ===
Total: 127 files, 45.2 GB
Movies: 23 folders, TV: 8 shows (104 episodes)
```

**Why this is maximum kickass:**
- Tree for visual structure (LLM gets the "shape")
- Pre-analyzed issues highlighted (LLM focuses on problems)
- Statistics summary (context without file-by-file details)
- Token-efficient but information-rich

---

## Decision Point 3: Prompt Preview Dialog

### Why This Matters

The prompt preview is currently a read-only `QTextEdit` showing raw prompt text. If we're optimizing the prompt format, users need to understand what they're sending.

### Option A: Just Show New Format Properly

**What it means:** Update the preview to render the tree format nicely (monospace font, proper indentation).

**Effort:** Low (1-2 hours)
**Value:** Moderate

---

### Option B: Add Editing Capability

**What it means:** Make the prompt editable so users can:
- Remove files they don't want analyzed
- Add context ("This is anime, use absolute episode numbering")
- Fix obvious mistakes before sending

**Advantages:**
- Power user feature
- Reduces wasted API calls
- Aligns with "user control at every step" philosophy

**Disadvantages:**
- Risk of users breaking prompt structure
- Need validation before send
- More complex UI

**Effort:** Medium (4-6 hours)
**Value:** High for power users

---

### Option C: Show Token Count Estimate

**What it means:** Display estimated token count and cost:
```
Prompt: 4,521 tokens (~$0.014 with Claude Sonnet)
Expected response: ~2,000 tokens (~$0.030)
Total estimated cost: $0.044
```

**Advantages:**
- Cost transparency
- Helps users decide if filtering is worth it
- Educational (users learn what costs money)

**Disadvantages:**
- Token counting is approximate
- Need to maintain pricing info
- Might scare users away from LLM mode

**Effort:** Low-Medium (2-3 hours)
**Value:** High for cost-conscious users

---

### Option D: All of the Above + Diff View

**What it means:** Full-featured prompt preview:
1. Tree-formatted, syntax-highlighted view
2. Editable with structure validation
3. Token count + cost estimate
4. **Diff view** showing what changed from last analysis

**Effort:** High (8-10 hours)
**Value:** Maximum kickass-ness

---

## Summary: Recommended Plan

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| **Heuristics** | Option D (Hybrid) | Immediate improvement via adapter pattern, future consolidation path |
| **Prompt Format** | Hybrid Tree + Issues | Token-efficient, LLM-friendly, highlights problems |
| **Prompt Preview** | Option D (Full-featured) | Worth the investment for power users |

**Plus the easy win:**
- Rename "LLM Analysis" → "Analysis" across all ~15 locations

---

## Pre-Existing Code Assets

### Function Index Query Results

| Module | Lines | Capabilities |
|--------|-------|--------------|
| `movie_name_backend.py` | ~400 | Title truncation detection, folder-to-title similarity scoring |
| `episode_title_backend.py` | ~300 | Multi-pattern Jellyfin episode parsing, technical tag removal |
| `folder_structure_scanner.py` | ~250 | Folder classification (tv_show_with_seasons, movie, collection) |
| `tv_episode_cache.py` | **1,456** | Wikipedia parsing with 5 strategies, canonical title verification, fuzzy matching |

### Current Regex Analyzer Weaknesses

- No anime patterns (`[01]`, `- 01 -`, absolute numbering)
- Year regex misses pre-1978 films
- No "Director's Cut" / "Remastered" / "Extended" detection
- Title extraction is just "what's left" after pattern removal
- Ignores folder context entirely (folder name often IS the title)
- No canonical verification against Wikipedia/TMDB
