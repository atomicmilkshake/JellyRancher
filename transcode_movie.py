#!/usr/bin/env python3
"""
Transcode Movie - Convert video to 1080p HEVC MP4 with AAC audio

Usage:
    python transcode_movie.py "movie search term" [--output-dir OUTPUT_DIR]
    python transcode_movie.py "barbie mermaid" --output-dir "L:\\#MEDIA\\Movies\\Barbie in A Mermaid Tale (2010)"
"""

import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).parent))

from scripts.core.jellyfin_client import JellyfinClient
from scripts.core.jellyfin_config import JellyfinConfigManager


def find_video_file(source_path: Path) -> tuple[Optional[Path], bool]:
    """
    Find the actual video file in a path (handles DVD folders, etc.)
    
    Args:
        source_path: Path from Jellyfin (may be folder or file)
    
    Returns:
        Tuple of (Path to video file or DVD root directory, is_dvd_structure)
        For DVD structures, returns the root DVD directory (parent of VIDEO_TS)
        For regular files, returns the video file path
    """
    if source_path.is_file():
        # Check if it's a video file
        video_extensions = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', 
                           '.webm', '.mpg', '.mpeg', '.ts', '.vob', '.mpeg2'}
        if source_path.suffix.lower() in video_extensions:
            return source_path, False
    
    # If it's a directory, search for video files
    if source_path.is_dir():
        # Check for DVD structure (VIDEO_TS folder with IFO files)
        video_ts_dir = source_path / 'VIDEO_TS'
        if video_ts_dir.exists():
            # Check if there are IFO files (confirms DVD structure)
            ifo_files = list(video_ts_dir.glob('VTS_*_0.IFO'))
            if ifo_files:
                print(f"Found DVD structure at: {source_path}")
                # Return the root DVD directory (HandBrakeCLI can read from here)
                return source_path, True
        
        # Look for regular video files
        video_extensions = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', 
                           '.webm', '.mpg', '.mpeg', '.ts', '.vob', '.mpeg2'}
        for pattern in ['*.mkv', '*.mp4', '*.avi', '*.m4v', '*.mov', '*.mpg', '*.mpeg']:
            matches = list(source_path.rglob(pattern))
            if matches:
                return matches[0], False
    
    return None, False


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_handbrake() -> bool:
    """Check if HandBrakeCLI is available."""
    try:
        # Try HandBrakeCLI first (Windows)
        result = subprocess.run(
            ['HandBrakeCLI', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try lowercase variant (Linux/Mac)
        result = subprocess.run(
            ['handbrakecli', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def transcode_dvd_with_handbrake(
    dvd_path: Path,
    output_file: Path,
    target_resolution: str = "1080p",
    crf: int = 23,
    preset: str = "medium"
) -> bool:
    """
    Transcode DVD to HEVC (H.265) MP4 with AAC audio using HandBrakeCLI.
    
    Args:
        dvd_path: Root DVD directory (contains VIDEO_TS folder)
        output_file: Output MP4 file path
        target_resolution: Target resolution (720p, 1080p, 2160p)
        crf: Quality setting (RF 18-28, equivalent to CRF, 23 is default)
        preset: Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    
    Returns:
        True if successful, False otherwise
    """
    # Resolution mapping
    resolution_map = {
        "720p": (1280, 720),
        "1080p": (1920, 1080),
        "2160p": (3840, 2160)
    }
    
    width, height = resolution_map.get(target_resolution.lower(), (1920, 1080))
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Build HandBrakeCLI command
    # Try HandBrakeCLI first (Windows), then handbrakecli (Linux/Mac)
    cmd = None
    for cmd_name in ['HandBrakeCLI', 'handbrakecli']:
        try:
            result = subprocess.run(
                [cmd_name, '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                cmd = [cmd_name]
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    if cmd is None:
        print("[ERROR] HandBrakeCLI not found. Please install HandBrake.")
        return False
    
    cmd.extend([
        '-i', str(dvd_path),           # Input DVD directory
        '-o', str(output_file),        # Output file
        '--title', '0',                # Auto-select largest title
        '--encoder', 'x265',           # HEVC video codec
        '--quality', f'RF={crf}',      # Quality (RF 18-28, similar to CRF)
        '--encoder-preset', preset,    # Encoding speed/quality tradeoff
        '--width', str(width),         # Target width
        '--height', str(height),       # Target height
        '--audio', '1',                # First audio track
        '--aencoder', 'aac',           # AAC audio codec
        '--ab', '192',                 # Audio bitrate (192kbps)
        '--format', 'mp4'              # MP4 container
    ])
    
    print(f"\nTranscoding command:")
    print(f"  Input:  {dvd_path}")
    print(f"  Output: {output_file}")
    print(f"  Resolution: {target_resolution} ({width}x{height})")
    print(f"  Quality: RF {crf} (preset: {preset})")
    print(f"\nRunning HandBrakeCLI (this may take a while)...\n")
    
    try:
        # Run HandBrakeCLI with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n[SUCCESS] Transcoding completed successfully!")
            print(f"  Output file: {output_file}")
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"  Output size: {size_mb:.2f} MB")
            return True
        else:
            print(f"\n[ERROR] Transcoding failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error during transcoding: {e}")
        return False


def transcode_to_hevc(
    input_file: Path,
    output_file: Path,
    target_resolution: str = "1080p",
    crf: int = 23,
    preset: str = "medium"
) -> bool:
    """
    Transcode video to HEVC (H.265) MP4 with AAC audio using ffmpeg.
    
    Args:
        input_file: Source video file
        output_file: Output MP4 file path
        target_resolution: Target resolution (720p, 1080p, 2160p)
        crf: Constant Rate Factor (18-28, lower = higher quality, 23 is default)
        preset: Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    
    Returns:
        True if successful, False otherwise
    """
    # Resolution mapping
    resolution_map = {
        "720p": "1280:720",
        "1080p": "1920:1080",
        "2160p": "3840:2160"
    }
    
    scale = resolution_map.get(target_resolution.lower(), "1920:1080")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Build ffmpeg command
    # Video: HEVC (libx265), scale to target resolution, maintain aspect ratio
    # Audio: AAC, 192kbps, stereo (or keep original channels if 2ch)
    # Container: MP4
    cmd = ['ffmpeg', '-i', str(input_file)]
    
    cmd.extend([
        '-c:v', 'libx265',           # HEVC video codec
        '-preset', preset,           # Encoding speed/quality tradeoff
        '-crf', str(crf),            # Quality (18-28, 23 is default)
        '-vf', f'scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2',  # Scale and pad to maintain aspect
        '-c:a', 'aac',               # AAC audio codec
        '-b:a', '192k',              # Audio bitrate
        '-ac', '2',                  # Stereo (2 channels)
        '-movflags', '+faststart',   # Web-optimized (fast start)
        '-y',                        # Overwrite output file
        str(output_file)
    ])
    
    print(f"\nTranscoding command:")
    print(f"  Input:  {input_file}")
    print(f"  Output: {output_file}")
    print(f"  Resolution: {target_resolution}")
    print(f"  Quality: CRF {crf} (preset: {preset})")
    print(f"\nRunning ffmpeg (this may take a while)...\n")
    
    try:
        # Run ffmpeg with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n[SUCCESS] Transcoding completed successfully!")
            print(f"  Output file: {output_file}")
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"  Output size: {size_mb:.2f} MB")
            return True
        else:
            print(f"\n[ERROR] Transcoding failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error during transcoding: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Transcode movie from Jellyfin library to 1080p HEVC MP4',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python transcode_movie.py "barbie mermaid"
  python transcode_movie.py "star wars" --resolution 720p --crf 20
  python transcode_movie.py "matrix" --output-dir "D:\\Transcoded"
        """
    )
    parser.add_argument(
        'search_term',
        help='Movie search term (case-insensitive)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory (default: same directory as source)'
    )
    parser.add_argument(
        '--resolution',
        choices=['720p', '1080p', '2160p'],
        default='1080p',
        help='Target resolution (default: 1080p)'
    )
    parser.add_argument(
        '--crf',
        type=int,
        default=23,
        choices=range(18, 29),
        metavar='18-28',
        help='Quality setting: 18 (highest quality, larger file) to 28 (lower quality, smaller file). Default: 23'
    )
    parser.add_argument(
        '--preset',
        choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
        default='medium',
        help='Encoding speed preset (default: medium)'
    )
    
    args = parser.parse_args()
    
    # Check tool availability (will check specific tool based on file type)
    # We'll check ffmpeg and HandBrakeCLI as needed
    
    # Query Jellyfin for movie
    config = JellyfinConfigManager()
    client = JellyfinClient(
        server_url=config.get_server_url(),
        api_key=config.get_api_key()
    )
    
    print("Testing Jellyfin connection...")
    if not client.test_connection():
        print("[ERROR] Jellyfin connection failed!")
        sys.exit(1)
    
    print("Connected successfully\n")
    
    # Search for movie
    print(f"Searching for: '{args.search_term}'...")
    items = client.get_all_items(
        item_types=['Movie'],
        fields=['Name', 'Path', 'MediaSources', 'Id', 'ProductionYear']
    )
    
    search_lower = args.search_term.lower()
    matches = [
        item for item in items
        if search_lower in item.get('Name', '').lower()
    ]
    
    if not matches:
        print(f"No movies found matching '{args.search_term}'")
        sys.exit(1)
    
    if len(matches) > 1:
        print(f"\nFound {len(matches)} matches:")
        for i, movie in enumerate(matches):
            print(f"  {i+1}. {movie['Name']} ({movie.get('ProductionYear', 'N/A')})")
        print(f"\nUsing first match: {matches[0]['Name']}\n")
    
    movie = matches[0]
    source_path = Path(movie['Path'])
    
    print(f"Movie: {movie['Name']}")
    print(f"Source path: {source_path}")
    
    # Find actual video file
    video_file, is_dvd = find_video_file(source_path)
    if not video_file:
        print(f"[ERROR] Could not find video file in: {source_path}")
        sys.exit(1)
    
    print(f"Video file: {video_file}")
    if is_dvd:
        print("DVD structure detected - will use HandBrakeCLI for transcoding")
        # Check HandBrakeCLI availability for DVD
        if not check_handbrake():
            print("[ERROR] HandBrakeCLI not found in PATH")
            print("HandBrakeCLI is required for DVD transcoding.")
            print("Install HandBrake using one of these methods:")
            print("  winget install HandBrake")
            print("  choco install handbrake")
            sys.exit(1)
    else:
        # Check ffmpeg availability for regular files
        if not check_ffmpeg():
            print("[ERROR] ffmpeg not found in PATH")
            print("Please install ffmpeg and ensure it's in your system PATH")
            sys.exit(1)
    
    # Determine output path
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Use same directory as source, or parent if source is a file
        if source_path.is_file():
            output_dir = source_path.parent
        else:
            output_dir = source_path.parent
    
    # Generate output filename
    movie_name = movie['Name']
    year = movie.get('ProductionYear', '')
    if year:
        output_filename = f"{movie_name} ({year}).mp4"
    else:
        output_filename = f"{movie_name}.mp4"
    
    # Clean filename (remove invalid characters)
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        output_filename = output_filename.replace(char, '_')
    
    output_file = output_dir / output_filename
    
    # Check if output already exists
    if output_file.exists():
        response = input(f"\nOutput file already exists: {output_file}\nOverwrite? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    # Transcode
    if is_dvd:
        success = transcode_dvd_with_handbrake(
            video_file,  # This is the DVD root directory for DVDs
            output_file,
            target_resolution=args.resolution,
            crf=args.crf,
            preset=args.preset
        )
    else:
        success = transcode_to_hevc(
            video_file,
            output_file,
            target_resolution=args.resolution,
            crf=args.crf,
            preset=args.preset
        )
    
    if success:
        print(f"\n[SUCCESS] Transcoded movie saved to:")
        print(f"  {output_file}")
        sys.exit(0)
    else:
        print(f"\n[ERROR] Transcoding failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

