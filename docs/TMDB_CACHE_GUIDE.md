# TMDB Cache Builder Guide

## Overview

The TMDB Cache Builder is your gateway to comprehensive TV show metadata from The Movie Database (TMDB). This powerful tool generates detailed episode caches that enable accurate episode title analysis and fixing throughout your media library.

## Why Use TMDB Caches?

- **Accurate Episode Data**: Official episode titles, air dates, and season information
- **Bulk Processing**: Analyze entire TV show collections automatically
- **Offline Capability**: Generated caches work without internet connection
- **Consistency**: Standardized naming across your entire library
- **Time Saving**: Eliminates manual episode title research

## Quick Start

### 1. Set Up Your TMDB API Key

1. Visit [themoviedb.org](https://www.themoviedb.org/)
2. Create a free account
3. Go to **Settings** → **API**
4. Request a **Developer API Key**
5. Copy your **v3 API Key**

### 2. Configure in JellyRancher

1. Launch JellyRancher
2. Navigate to **Settings** tab
3. Locate **TMDB API Key** field
4. Paste your API key
5. Click **Test Key** to verify
6. **Save Settings**

### 3. Generate Your First Cache

1. Go to **Tools** → **Generate TMDB Cache**
2. Search for a show (e.g., "Breaking Bad")
3. Select the correct show from results
4. Click **Generate Cache**
5. Choose save location (recommended: `data/tmdb_caches/`)

## Step-by-Step Guide

### Finding Your Show

The search is flexible and forgiving:

- **Show Name**: "The Office", "Breaking Bad", "Stranger Things"
- **With Year**: Add year for better accuracy (e.g., "The Office 2005")
- **Alternative Titles**: TMDB knows international titles
- **Direct ID**: If you know the TMDB ID, enter it directly

### Understanding Results

When you search, you'll see:
- **Show Title**: Official name
- **Year Range**: First and last air dates
- **Overview**: Brief description
- **Poster**: Visual confirmation
- **TMDB Rating**: Community score

### Cache Generation Process

1. **Preparation**: Tool fetches show details from TMDB
2. **Episode Fetching**: Downloads all episode data for every season
3. **Data Processing**: Formats data into JellyRancher's cache structure
4. **File Creation**: Saves as JSON file for future use

**Progress Indicators:**
- Current season being processed
- Episodes fetched per season
- Overall completion percentage
- Estimated time remaining

## Cache File Details

Generated caches contain:

```json
{
  "show_info": {
    "name": "Breaking Bad",
    "tmdb_id": 1396,
    "total_seasons": 5,
    "total_episodes": 62
  },
  "episodes": {
    "S01E01": {
      "title": "Pilot",
      "air_date": "2008-01-20",
      "overview": "Walter White learns he has terminal lung cancer..."
    }
  }
}
```

## Integration with Episode Tools

Once generated, caches automatically work with:

- **Episode Title Analysis**: Compares your files against official titles
- **Batch Fixing**: Renames entire collections to match TMDB data
- **Confidence Scoring**: Rates how well your titles match official names
- **Missing Episode Detection**: Identifies gaps in your collection

## Best Practices

### Organization
- Store caches in `data/tmdb_caches/` folder
- Name files descriptively: `breaking_bad_1396.json`
- Keep caches organized by genre or alphabetically

### Maintenance
- Regenerate caches when new seasons air
- Update for shows with title changes
- Archive old caches before regenerating

### Troubleshooting

**"API Key Invalid"**
- Double-check your API key in Settings
- Ensure no extra spaces or characters
- Test the key in Settings tab

**"Show Not Found"**
- Try alternative spellings
- Include the year for disambiguation
- Check for international title variations

**"Generation Failed"**
- Check internet connection
- TMDB API might be temporarily down
- Try again in a few minutes

## Advanced Features

### Direct TMDB ID Usage
If you know the exact TMDB ID:
1. Enter the numeric ID directly in the search field
2. No need to search - goes straight to generation
3. Useful for scripts or bulk processing

### Batch Cache Generation
For multiple shows:
1. Generate caches one at a time
2. Store in organized folders
3. Use episode analysis tools across collections

### Cache File Inspection
You can open cache files in any text editor to:
- Verify episode data
- Check for missing information
- Understand the data structure
- Debug analysis issues

## Integration Examples

### With Episode Title Management
1. Generate TMDB cache for "The Office"
2. Run episode analysis on your Office files
3. Tool automatically matches your files to TMDB data
4. Get suggestions for title corrections

### With Media Organization
1. Use caches during bulk renaming
2. Ensure consistent episode titles across collections
3. Maintain professional naming standards
4. Prepare for media server integration

## Support and Resources

- **In-App Help**: Press F1 or go to Help → Contents
- **Settings Validation**: Test your TMDB key in Settings tab
- **Log Files**: Check `logs/` for detailed error information
- **Community**: Search existing issues for common problems

---

**Pro Tip**: Start with popular shows to get familiar with the workflow, then expand to your entire collection. The time investment in cache generation pays off exponentially in accurate, consistent media organization.