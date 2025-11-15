#!/usr/bin/env python3
"""Test TV filename parsing."""

import re

# Test parsing the problematic filename
filename = 'Star.Trek.Enterprise.S01E01E02.1080p.BluRay.x265-RARBG.mp4'
name = filename.rsplit('.', 1)[0]  # Remove extension

print(f'Testing filename: {filename}')
print(f'Name without extension: {name}')

# Combined episodes pattern
combined_match = re.search(r'S(\d{1,2})E(\d{1,2})(?:[-\s]?E(\d{1,2}))', name, re.IGNORECASE)
if combined_match:
    print(f'Combined match found:')
    print(f'  Season: {combined_match.group(1)}')
    print(f'  Episode start: {combined_match.group(2)}')
    print(f'  Episode end: {combined_match.group(3)}')
    print(f'  Match span: {combined_match.span()}')
    
    title_part = name[:combined_match.start()].strip()
    episode_title_part = name[combined_match.end():].strip()
    
    print(f'  Title part: "{title_part}"')
    print(f'  Episode title part: "{episode_title_part}"')
else:
    print('No combined match found')

# Test clean_episode_title function
def clean_episode_title(episode_title: str) -> str:
    """Clean episode title by removing technical tags and formatting."""
    if not episode_title:
        return episode_title
    
    # Split by dots to analyze segments
    segments = episode_title.split('.')
    cleaned_segments = []
    
    # Common technical keywords that indicate the start of technical tags
    technical_keywords = {
        '2160p', '1080p', '720p', '480p', '360p',  # resolutions
        '10bit', '8bit',  # bit depth
        'x264', 'x265', 'h264', 'h265', 'HEVC', 'AVC', 'XviD', 'DivX',  # codecs
        'WEB-DL', 'WEB', 'BluRay', 'BD', 'DVD', 'HDTV', 'SDTV', 'PDTV',  # sources
        'DDP', 'DD', 'AC3', 'DTS', 'AAC', 'FLAC', 'MP3',  # audio
        'RARBG', 'Vyndros', 'DSNP', 'NOGRP', 'ABC', 'CBS', 'NBC', 'FOX',  # groups
        'REPACK', 'PROPER', 'INTERNAL', 'LIMITED', 'EXTENDED', 'UNRATED',  # tags
        'REMUX', 'REMASTERED', 'DIRECTORS', 'CUT', 'MULTi', 'DUAL'  # other
    }
    
    # Go through segments and stop when we hit technical tags
    for segment in segments:
        segment_clean = segment.strip()
        if segment_clean in technical_keywords:
            break
        # Also check if segment contains numbers followed by common patterns
        if re.match(r'^\d+(?:p|bit)$', segment_clean):
            break
        if re.match(r'^(?:DD|DDP|AC3|DTS)\d+', segment_clean):
            break
        if re.match(r'^[A-Z]{2,8}(?:\-[A-Z]{2,8})*$', segment_clean):
            break
            
        cleaned_segments.append(segment_clean)
    
    # Join cleaned segments
    cleaned = ' '.join(cleaned_segments)
    
    # Final cleanup
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

cleaned = clean_episode_title(episode_title_part)
print(f'  Cleaned episode title: "{cleaned}"')