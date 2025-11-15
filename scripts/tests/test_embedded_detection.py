#!/usr/bin/env python3
"""
Quick test of embedded subtitle detection on a few sample files
"""
import json
import subprocess
from pathlib import Path

def has_embedded_subtitles(video_path: Path, languages=['en', 'eng']) -> bool:
    """Check if video file has embedded subtitle streams."""
    try:
        lang_codes = set()
        for lang in languages:
            lang_codes.add(lang.lower())
            if lang == 'en':
                lang_codes.update(['eng', 'en', 'english'])
            elif lang == 'eng':
                lang_codes.update(['en', 'eng', 'english'])
        
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 's',
                str(video_path)
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return False
        
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        
        for stream in streams:
            tags = stream.get('tags', {})
            stream_lang = tags.get('language', '').lower()
            
            if stream_lang in lang_codes:
                return True
        
        return False
        
    except Exception:
        return False


def test_sample_files():
    """Test embedded detection on a few sample files."""
    import os
    media_root = Path(r'M:\#MEDIA')
    
    # Find first 5 video files
    test_files = []
    for root, dirs, files in os.walk(media_root):
        for file in files:
            filepath = Path(root) / file
            if filepath.suffix.lower() in ['.mkv', '.mp4', '.avi', '.m4v']:
                test_files.append(filepath)
                if len(test_files) >= 5:
                    break
        if len(test_files) >= 5:
            break
    
    print("=" * 70)
    print("EMBEDDED SUBTITLE DETECTION TEST")
    print("=" * 70)
    print()
    
    for i, filepath in enumerate(test_files, 1):
        print(f"{i}. {filepath.name}")
        has_embedded = has_embedded_subtitles(filepath)
        
        # Also check for external subs
        has_external = any(
            filepath.with_suffix(f'.{lang}{ext}').exists()
            for lang in ['en', 'eng']
            for ext in ['.srt', '.sub', '.ass', '.ssa', '.vtt']
        ) or filepath.with_suffix('.srt').exists()
        
        print(f"   Embedded: {'✅ YES' if has_embedded else '❌ NO'}")
        print(f"   External: {'✅ YES' if has_external else '❌ NO'}")
        print()


if __name__ == '__main__':
    test_sample_files()
