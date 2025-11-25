# JellyRancher Testing Guide - Point 4 Implementation

This guide helps you test the newly implemented **Point 4: Canonical Metadata Database** functionality.

## Quick Start

### Option 1: Automated Setup (Recommended)

```powershell
# Run the setup script (sets API key and launches app)
.\setup_and_run.ps1
```

### Option 2: Manual Setup

```powershell
# 1. Set TMDB API key
$env:TMDB_API_KEY = "a71ed25dc11e509b52067f0c10df1af4"

# 2. Activate virtual environment
.venv\Scripts\Activate.ps1

# 3. Run application
python jelly_rancher_clean.py
```

## Test Media Folder

A test media folder has been created at: `test_media/`

**Contents:**
- **41 video files** (movies and TV episodes)
- **6 subtitle files**
- **7 movies** in various naming formats
- **6 TV shows** (well-organized and messy)
- **2 multi-part episodes** (for NFO testing)

**Structure:**
```
test_media/
├── Movies/
│   ├── The Matrix (1999)/
│   ├── Inception (2010)/
│   ├── Interstellar (2014)/
│   ├── The Godfather (1972)/ (with subtitles)
│   └── Various messy formats...
├── TV Shows/
│   ├── Breaking Bad (2008)/ (5 seasons, organized)
│   └── The Office (US) (2005)/ (2 seasons with subs)
├── Unsorted TV/
│   ├── Stranger Things/ (flat structure)
│   ├── Game of Thrones files (no folders)
│   ├── The Mandalorian/ (missing year)
│   └── Star Trek TNG/ (multi-part episodes!)
└── Unsorted/
    └── Random/unknown files
```

## Testing Workflow

### Step 1: Scan Folders (Points 1-2)

1. Launch JellyRancher: `python jelly_rancher_clean.py`
2. Go to **Tab 1: "1-2. Scan & Overview"**
3. Click **"Add Folder"**
4. Select the `test_media` folder
5. Click **"Scan Selected Folders"**
6. Wait for scan to complete (should be fast - 41 files)

**Expected Results:**
- Progress bar shows scanning progress
- File list displays (first 500 files)
- Hierarchical overview tree appears automatically
- Status shows total files and size

### Step 2: LLM Analysis (Point 3)

1. Go to **Tab 2: "3-4. LLM & Metadata"**
2. Click **"Get LLM Proposal"**
3. If no API key, enter your Poe.com API key when prompted
4. Wait 30-60 seconds for LLM analysis

**Expected Results:**
- LLM detects ~7 movies
- LLM detects ~6 TV shows
- Reorganization proposal appears
- Multi-part episodes flagged (Star Trek TNG)
- Results saved to `data/llm_analysis_TIMESTAMP.json`

### Step 3: Metadata Lookup (Point 4) ⭐ NEW!

1. Still in **Tab 2: "3-4. LLM & Metadata"**
2. Click **"Build Metadata DB"**
3. TMDB API key should already be set
4. Watch progress bar and status messages

**Expected Results:**
- Progress updates for each movie/TV show
- Rate limiting visible (1 request per second)
- Movies display with correct years and TMDB IDs
- TV shows show season/episode counts
- Multi-part episodes detected and listed
- Canonical database saved to `data/canonical_metadata_TIMESTAMP.json`

**Example Output:**
```
[1/13] Querying movie: The Matrix (1999)...
[2/13] Querying movie: Inception (2010)...
[3/13] Querying tv_show: Breaking Bad (2008)...
...

============================================================
✅ METADATA LOOKUP COMPLETE
============================================================

📽️  Movies: 7
   • The Matrix (1999) [TMDB: 603]
   • Inception (2010) [TMDB: 27205]
   • Interstellar (2014) [TMDB: 157336]
   ...

📺 TV Shows: 6
   • Breaking Bad (2008) - 5 seasons, 62 episodes [TMDB: 1396]
   • The Office (2005) - 9 seasons, 201 episodes [TMDB: 2316]
   ...

⚠️  Multi-Part Episodes: 2
   (These will require NFO files for proper Jellyfin recognition)
   • Star Trek TNG - S01E01 - Encounter at Farpoint
   • Star Trek TNG - S03E26 - Best of Both Worlds

💾 Canonical database saved to: data/canonical_metadata_20231113_235959.json
```

## Verification Checklist

### ✅ Structural Tests
- [x] All imports work without errors
- [x] MediaMetadataLookup initializes correctly
- [x] Cache directory created (`data/metadata_cache/`)
- [x] JSON serialization works
- [x] No Unicode logging errors

### ✅ Point 4 Functionality
- [ ] TMDB API key detected or prompted
- [ ] Background worker prevents GUI freezing
- [ ] Progress bar updates in real-time
- [ ] Rate limiting visible (1 req/sec)
- [ ] Movie metadata retrieved (title, year, TMDB ID)
- [ ] TV show metadata retrieved (seasons, episodes)
- [ ] Multi-part episodes detected
- [ ] Lookup failures displayed
- [ ] Results saved to timestamped JSON
- [ ] No crashes or errors

## Expected API Behavior

**TMDB API Calls:**
- **Movies**: 1 API call per movie (search + details)
- **TV Shows**: 1 + N calls (1 for show + 1 per season)
- **Rate Limiting**: 1 request per second (courteous)
- **Caching**: Subsequent lookups use cache

**For 7 movies + 6 TV shows:**
- ~7 calls for movies
- ~30-40 calls for TV shows (depending on seasons)
- **Total time**: ~45-60 seconds with rate limiting

## Troubleshooting

### Issue: No API key error

**Solution:**
```powershell
# Set manually
$env:TMDB_API_KEY = "a71ed25dc11e509b52067f0c10df1af4"

# Or use the setup script
.\setup_and_run.ps1
```

### Issue: "No detected media" warning

**Solution:**
- Complete Step 2 (LLM Analysis) first
- Metadata lookup requires detected media from LLM

### Issue: Lookup failures

**Possible causes:**
- Internet connection issues
- TMDB API temporarily unavailable
- Incorrect movie/show titles from LLM
- Rate limiting (429 errors)

**Solution:**
- Check internet connection
- Wait a few minutes and retry
- Check `data/logs/jellyrancher.log` for details

### Issue: Slow progress

**This is normal!**
- Rate limiting: 1 request per second
- 13 items = ~60 seconds total
- Large libraries will take longer
- Caching speeds up subsequent runs

## Files Generated

After testing, you should see:

```
data/
├── canonical_metadata_YYYYMMDD_HHMMSS.json  # Canonical database
├── llm_analysis_YYYYMMDD_HHMMSS.json        # LLM proposal
├── metadata_cache/                           # Cached API responses
│   ├── movie_The_Matrix_1999.json
│   ├── tv_Breaking_Bad_2008.json
│   └── ...
├── logs/
│   └── jellyrancher.log                        # Application log
└── inventory.db                              # SQLite scan inventory
```

## Next Steps After Testing

Once Point 4 is verified:

1. **Point 5**: Generate editable action table
   - Combine LLM proposal + canonical metadata
   - Create file operation plan
   - Display in color-coded table

2. **Point 6-7**: Execute operations
   - Transaction logging
   - MD5 verification
   - Subtitle handling
   - NFO generation for multi-part episodes

3. **Point 8-9**: Subtitle management
   - Coverage evaluation
   - Download missing subtitles

## Known Limitations

1. **LLM Analysis (Point 3)** requires Poe.com API key
2. **Metadata lookup** requires TMDB API key (provided)
3. **Test media** uses empty files (no actual video content)
4. **Multi-part detection** relies on episode name patterns

## API Credentials

**TMDB API Key:** `a71ed25dc11e509b52067f0c10df1af4`
- Free tier: 40 requests per 10 seconds
- Our implementation: 1 request per second (courteous)
- Get your own: https://www.themoviedb.org/settings/api

**API Read Access Token:** (not currently used)
```
eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhNzFlZDI1ZGMxMWU1MDliNTIwNjdmMGMxMGRmMWFmNCIsIm5iZiI6MTc2Mjg4OTc2NC4wMDcsInN1YiI6IjY5MTM5MDI0NjAwZGIxNjUyYmQyNjM1NSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.wHizl2Jf-LgGAq0czRufHTKKmF4mMDuwCNUd3RddlM0
```

## Questions?

Check the documentation:
- `docs/plan.md` - Full 9-point workflow specification
- `docs/ARCHITECTURE.md` - Architecture and library choices
- `agent-journal.md` - Implementation history (Phase 19)
- `docs/tmdb_usage_guidelines.md` - TMDB API best practices

---

**Happy Testing! 🎬📺**



