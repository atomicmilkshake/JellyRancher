# TMDB Episode Cache Generator

## Overview

The TMDB Episode Cache Generator is a feature that allows users to fetch complete episode metadata from The Movie Database (TMDB) and generate structured cache files for TV shows. This eliminates the need for manual episode title lookups and provides accurate, consistent naming.

## Features

- **Search TMDB**: Find TV shows by name, year, or direct TMDB ID
- **Preview Details**: View show information before generating cache
- **Progress Tracking**: Real-time progress updates during cache generation
- **Offline Usage**: Generated caches can be used without API access
- **JSON Format**: Standard, easy-to-parse cache file format

## Setup

### 1. Get a TMDB API Key

1. Visit [TMDB](https://www.themoviedb.org/)
2. Create a free account (if you don't have one)
3. Go to Settings → API
4. Request an API key (select "Developer" when asked)
5. Copy your API key (v3 auth)

### 2. Configure in JellyRancher

1. Open JellyRancher
2. Go to **Settings** tab
3. Find the **API Credentials** section
4. Paste your TMDB API key in the field
5. Click **Test** to verify it works
6. Click **Save Settings**

## Usage

### Generating a Cache

1. Go to **Tools** menu → **Generate TMDB Cache**
2. Enter the show name in the search field
3. (Optional) Enter the year to narrow results
4. Click **🔍 Search**
5. Select the correct show from the results list
6. Review the show details in the preview pane
7. Click **📥 Generate Cache**
8. Choose where to save the cache file
9. Wait for generation to complete

### Direct TMDB ID Lookup

If you know the exact TMDB ID:

1. Open the TMDB Cache Generator
2. Enter the TMDB ID in the **TMDB ID** field
3. The show will be looked up directly
4. Click **📥 Generate Cache**

### Using Generated Caches

Cache files are saved as JSON with the following structure:

```json
{
  "tmdb_id": 12345,
  "show_name": "Example Show",
  "first_air_date": "2020-01-01",
  "overview": "Show description...",
  "generated_date": "2025-11-08T22:38:00.123456",
  "seasons": {
    "1": {
      "season_number": 1,
      "episodes": {
        "1": {
          "episode_number": 1,
          "name": "Pilot",
          "air_date": "2020-01-01",
          "overview": "Episode description..."
        }
      }
    }
  }
}
```

These caches can be used by other tools in JellyRancher for:
- Episode title matching
- Metadata enrichment
- NFO file generation
- Automated organization

## Tips & Best Practices

### Searching

- **Be Specific**: Include the year if the show name is common
  - Example: "The Office 2005" vs "The Office"
- **Check Results**: Multiple shows may have similar names
- **Use TMDB ID**: For maximum accuracy, use the TMDB ID directly

### Cache Management

- **Organized Storage**: Keep caches in a dedicated folder
  - Example: `V:/Jellyfin/#MEDIA/caches/`
- **Naming Convention**: Use descriptive names
  - Good: `game_of_thrones_1399.json`
  - Bad: `cache.json`
- **Regular Updates**: Re-generate caches for ongoing series

### Troubleshooting

#### "No API key found"
- Go to Settings and configure your TMDB API key
- Click Test to verify it works

#### "TMDB API key is invalid"
- Check that you copied the entire key (no spaces)
- Ensure you're using the API Key (v3 auth), not API Read Access Token
- Verify your TMDB account is active

#### "No results found"
- Try different search terms
- Check spelling
- Try searching on TMDB website first to find the correct name
- Use the TMDB ID instead

#### "Failed to connect to TMDB"
- Check your internet connection
- TMDB may be temporarily down (check status.themoviedb.org)
- Try again in a few minutes

#### Cache generation is slow
- This is normal for shows with many seasons/episodes
- Progress bar shows current status
- Do not close the dialog while generating

## Technical Details

### API Rate Limits

TMDB has rate limits for API requests:
- Free tier: 50 requests per second
- JellyRancher respects these limits automatically

### Cache Format

Caches follow this structure:

**Root Level:**
- `tmdb_id`: Unique TMDB identifier
- `show_name`: Official show name
- `first_air_date`: Original air date
- `overview`: Show description
- `generated_date`: When cache was created
- `seasons`: Dictionary of season data

**Season Level:**
- `season_number`: Season number (0 = specials)
- `episodes`: Dictionary of episode data

**Episode Level:**
- `episode_number`: Episode number within season
- `name`: Episode title
- `air_date`: Original air date
- `overview`: Episode description

### File Locations

**Settings:**
- API key stored in: `scripts/core/config/settings.json`
- Key is stored in plain text (secure appropriately)

**Caches:**
- Saved wherever you choose during generation
- Recommended: Keep with media files or in dedicated cache directory

**Logs:**
- TMDB operations logged to: `logs/jelly_rancher_main.log`
- Check logs for detailed error information

## Development

### Backend Implementation

The TMDB backend is implemented in `scripts/core/tmdb_backend.py`:

```python
from tmdb_backend import TMDBBackend

# Initialize
tmdb = TMDBBackend()
tmdb.set_api_key("your_api_key")

# Search
results = tmdb.search_shows("Game of Thrones", year=2011)

# Get details
show = tmdb.get_show_details(1399)

# Generate cache
cache_path, cache_data = tmdb.generate_cache(
    tmdb_id=1399,
    output_path=Path("cache.json"),
    progress_callback=lambda msg, current, total: print(msg)
)
```

### Dialog Implementation

The UI dialog is in `scripts/core/dialogs/tmdb_cache_dialog.py`:

```python
from dialogs.tmdb_cache_dialog import TMDBCacheDialog

# Create and show
dialog = TMDBCacheDialog(parent)
if dialog.exec_():
    # Cache was generated successfully
    pass
```

### Testing

Run the integration test suite:

```bash
pytest scripts/tests/test_tmdb_integration.py -v
```

Run with coverage:

```bash
pytest scripts/tests/test_tmdb_integration.py --cov=scripts/core/tmdb_backend
```

### Adding Features

To extend the TMDB functionality:

1. **Backend**: Edit `scripts/core/tmdb_backend.py`
   - Add methods to `TMDBBackend` class
   - Follow existing patterns for error handling

2. **UI**: Edit `scripts/core/dialogs/tmdb_cache_dialog.py`
   - Add UI elements to dialog
   - Connect to backend methods

3. **Tests**: Update `scripts/tests/test_tmdb_integration.py`
   - Add tests for new functionality
   - Use mocks to avoid real API calls

## See Also

- [TMDB API Documentation](https://developers.themoviedb.org/3)
- [Episode Title Analyzer](episode_title_analyzer.md) (uses caches)
- [Settings Management](settings.md)

## Support

For issues with the TMDB Cache Generator:

1. Check the troubleshooting section above
2. Review logs in `logs/jelly_rancher_main.log`
3. Verify your API key is valid
4. Test your internet connection
5. Report bugs in the JellyRancher issue tracker

---

*Last Updated: November 8, 2025*  
*Version: 2.0.0*
