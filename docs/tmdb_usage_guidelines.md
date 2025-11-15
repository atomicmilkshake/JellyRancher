# TMDB API Usage Guidelines - Courteous Implementation

## Official TMDB Guidelines

### Rate Limiting
- **Legacy Limits**: 40 requests every 10 seconds (disabled since Dec 2019)
- **Current Limits**: ~40 requests per second upper bound to prevent bulk scraping
- **Key Requirement**: Respect 429 "Too Many Requests" responses
- **Recommendation**: Be courteous and avoid hammering their service

### Terms of Use
- **Cache Duration**: No longer than 6 months
- **Attribution**: Must give TMDB attribution for all content
- **Commercial Use**: Requires separate written agreement
- **Prohibited**: AI/ML training, excessive bandwidth, system degradation
- **Caching**: Allowed but must not exceed 6 months

## Our Courteous Implementation

### Rate Limiting Strategy
- **TMDB Backend**: 1 request per second (1000ms intervals)
- **Media Metadata Lookup**: 1 request per second (1000ms intervals)
- **Wikipedia Scraping**: 1 request every 11 seconds (existing implementation)
- **Error Handling**: Automatic backoff on 429 responses with exponential increase

### API Usage Patterns
- **Search**: 1 API call per search
- **Show Details**: 1 API call per show lookup
- **Cache Generation**: 1 + N calls (1 for show + 1 per season)
- **Metadata Lookup**: 1-2 calls per media item (TMDB + OMDb)

### Courteous Features
- **Automatic Rate Limiting**: Built into all API calls
- **429 Response Handling**: Detects and backs off appropriately
- **Progress Feedback**: Users see rate limiting in progress messages
- **Conservative Limits**: Well below TMDB's upper bounds
- **Error Recovery**: Graceful handling of API issues

### Usage Examples
- **Single Cache Generation**: ~10-15 seconds for a 10-season show
- **Bulk Metadata**: ~1 second per media item
- **Search Operations**: Near-instantaneous with rate limiting

### Compliance Status
✅ Rate limiting implemented
✅ 429 error handling
✅ Attribution requirements met
✅ Cache duration limits observed
✅ Non-commercial usage confirmed
✅ No AI/ML training usage

## Recommendations for Users

1. **Batch Processing**: Space out bulk operations to avoid rate limits
2. **Cache Reuse**: Generated caches are valid for months
3. **Error Handling**: If you see rate limit messages, wait and retry
4. **Attribution**: TMDB content properly attributed in UI
5. **Responsible Use**: Only generate caches for shows you actually need

This implementation ensures we stay well within TMDB's guidelines while providing
excellent functionality for media organization tasks.