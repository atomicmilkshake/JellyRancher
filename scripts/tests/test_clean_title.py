#!/usr/bin/env python3
"""Test the clean_episode_title function."""

import re

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
    
    return cleaned# Test cases
test_cases = [
    'One.Year.Later.2160p.10bit.DSNP.WEB-DL.DDP5.1.HEVC-Vyndros',
    'The.Eye.1080p.WEB-DL.DD5.1.H.264-RARBG',
    'Pilot.720p.HDTV.x264-ABC',
    'Episode.1.480p.DVDRip.XviD-SOMEGROUP',
    'That.70s.Show.S06E01.The.Seems.Assistance.1080p.BluRay.REMUX.AVC.DTS-HD.MA.5.1-NOGRP',
]

print('Testing clean_episode_title function:')
for test in test_cases:
    cleaned = clean_episode_title(test)
    print(f'  "{test}" -> "{cleaned}"')