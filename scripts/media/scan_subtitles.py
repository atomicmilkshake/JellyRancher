#!/usr/bin/env python3
"""
Subtitle Scanner
Scans video files for embedded and external subtitles.
Generates comprehensive subtitle coverage report.
"""

import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import sys

class SubtitleScanner:
    def __init__(self, drives: List[str] = None):
        """
        Initialize subtitle scanner.
        
        Args:
            drives: List of drive letters to scan (e.g., ['L', 'M', 'Q', 'S', 'W'])
        """
        self.drives = drives or ['L', 'M', 'Q', 'S', 'W']
        self.video_extensions = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.mpg', '.mpeg'}
        self.subtitle_extensions = {'.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt'}
        
        self.results = {
            'videos_with_embedded': [],
            'videos_without_embedded': [],
            'external_subtitles': [],
            'orphaned_subtitles': [],
            'summary': {}
        }
        
    def check_ffprobe_available(self) -> bool:
        """Check if ffprobe is available."""
        try:
            subprocess.run(['ffprobe', '-version'], 
                         capture_output=True, 
                         check=True,
                         timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_embedded_subtitles(self, video_path: Path) -> List[Dict]:
        """
        Extract embedded subtitle information from video file using ffprobe.
        
        Returns:
            List of subtitle track dictionaries with language, codec, etc.
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 's',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True,
                                  timeout=30)
            
            if result.returncode != 0:
                return []
            
            data = json.loads(result.stdout)
            subtitles = []
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'subtitle':
                    subtitle_info = {
                        'index': stream.get('index'),
                        'codec': stream.get('codec_name', 'unknown'),
                        'language': stream.get('tags', {}).get('language', 'und'),
                        'title': stream.get('tags', {}).get('title', ''),
                        'forced': stream.get('disposition', {}).get('forced', 0) == 1,
                        'default': stream.get('disposition', {}).get('default', 0) == 1
                    }
                    subtitles.append(subtitle_info)
            
            return subtitles
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"   ⚠️  Error scanning {video_path.name}: {e}")
            return []
    
    def find_external_subtitles(self, video_path: Path) -> List[Path]:
        """Find external subtitle files matching the video file."""
        video_stem = video_path.stem
        video_dir = video_path.parent
        
        external_subs = []
        
        # Look for subtitle files with same base name
        for sub_ext in self.subtitle_extensions:
            # Exact match
            exact_match = video_dir / f"{video_stem}{sub_ext}"
            if exact_match.exists():
                external_subs.append(exact_match)
            
            # Language variants (e.g., video.en.srt, video.eng.srt)
            for sub_file in video_dir.glob(f"{video_stem}.*{sub_ext}"):
                if sub_file not in external_subs:
                    external_subs.append(sub_file)
        
        return external_subs
    
    def scan_directory(self, directory: Path, drive_letter: str) -> Dict:
        """Scan a directory for videos and subtitles."""
        print(f"\n📂 Scanning {directory}...")
        
        stats = {
            'total_videos': 0,
            'videos_with_embedded': 0,
            'videos_without_embedded': 0,
            'total_embedded_tracks': 0,
            'external_subtitle_files': 0,
            'videos_with_external': 0
        }
        
        # Find all video files
        video_files = []
        for ext in self.video_extensions:
            video_files.extend(directory.rglob(f"*{ext}"))
        
        stats['total_videos'] = len(video_files)
        print(f"   Found {len(video_files)} video files")
        
        # Track which external subs are matched
        matched_external_subs = set()
        
        # Scan each video
        for i, video_path in enumerate(video_files, 1):
            if i % 50 == 0:
                print(f"   Progress: {i}/{len(video_files)} videos scanned...")
            
            # Get embedded subtitles
            embedded_subs = self.get_embedded_subtitles(video_path)
            
            # Get external subtitles
            external_subs = self.find_external_subtitles(video_path)
            
            # Update stats
            if embedded_subs:
                stats['videos_with_embedded'] += 1
                stats['total_embedded_tracks'] += len(embedded_subs)
            else:
                stats['videos_without_embedded'] += 1
            
            if external_subs:
                stats['videos_with_external'] += 1
                stats['external_subtitle_files'] += len(external_subs)
                matched_external_subs.update(external_subs)
            
            # Store results
            video_info = {
                'drive': drive_letter,
                'path': str(video_path.relative_to(directory.parent)),
                'size_mb': video_path.stat().st_size / (1024 * 1024),
                'embedded_subtitles': embedded_subs,
                'external_subtitles': [str(s.relative_to(directory.parent)) for s in external_subs],
                'has_subtitles': bool(embedded_subs or external_subs)
            }
            
            if embedded_subs:
                self.results['videos_with_embedded'].append(video_info)
            else:
                self.results['videos_without_embedded'].append(video_info)
            
            for ext_sub in external_subs:
                self.results['external_subtitles'].append({
                    'drive': drive_letter,
                    'path': str(ext_sub.relative_to(directory.parent)),
                    'video': str(video_path.relative_to(directory.parent))
                })
        
        # Find orphaned subtitle files (not matched to any video)
        all_subtitle_files = []
        for ext in self.subtitle_extensions:
            all_subtitle_files.extend(directory.rglob(f"*{ext}"))
        
        orphaned = [s for s in all_subtitle_files if s not in matched_external_subs]
        for orphan in orphaned:
            self.results['orphaned_subtitles'].append({
                'drive': drive_letter,
                'path': str(orphan.relative_to(directory.parent))
            })
        
        print(f"   ✅ Scan complete:")
        print(f"      - Videos with embedded subs: {stats['videos_with_embedded']}")
        print(f"      - Videos without embedded subs: {stats['videos_without_embedded']}")
        print(f"      - External subtitle files: {stats['external_subtitle_files']}")
        print(f"      - Orphaned subtitle files: {len(orphaned)}")
        
        return stats
    
    def scan_all_drives(self):
        """Scan all configured drives."""
        print("=" * 70)
        print("SUBTITLE SCANNER")
        print("=" * 70)
        
        # Check for ffprobe
        if not self.check_ffprobe_available():
            print("\n⚠️  WARNING: ffprobe not found!")
            print("   Embedded subtitle detection will be skipped.")
            print("   Install ffmpeg to enable full subtitle scanning.")
            print("   Only external subtitle files will be detected.\n")
        
        total_stats = defaultdict(int)
        
        for drive in self.drives:
            media_dir = Path(f"{drive}:/#MEDIA")
            
            if not media_dir.exists():
                print(f"\n⚠️  Skipping {drive}: - directory not found")
                continue
            
            drive_stats = self.scan_directory(media_dir, drive)
            
            # Aggregate stats
            for key, value in drive_stats.items():
                total_stats[key] += value
        
        # Store summary
        self.results['summary'] = dict(total_stats)
        
        print("\n" + "=" * 70)
        print("SCAN COMPLETE")
        print("=" * 70)
        print(f"\n📊 Overall Summary:")
        print(f"   - Total videos scanned: {total_stats['total_videos']:,}")
        print(f"   - Videos with embedded subtitles: {total_stats['videos_with_embedded']:,}")
        print(f"   - Videos without embedded subtitles: {total_stats['videos_without_embedded']:,}")
        print(f"   - Total embedded subtitle tracks: {total_stats['total_embedded_tracks']:,}")
        print(f"   - External subtitle files: {total_stats['external_subtitle_files']:,}")
        print(f"   - Orphaned subtitle files: {len(self.results['orphaned_subtitles']):,}")
        
        # Calculate coverage
        if total_stats['total_videos'] > 0:
            coverage = (total_stats['videos_with_embedded'] + total_stats['videos_with_external']) / total_stats['total_videos'] * 100
            print(f"\n   📈 Subtitle Coverage: {coverage:.1f}%")
    
    def generate_report(self, output_path: str = "scripts/reports/subtitle_scan.json"):
        """Generate comprehensive subtitle report."""
        print(f"\n📝 Generating report...")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Report saved to {output_path}")
        
        # Generate markdown report
        self._generate_markdown_report(output_path.with_suffix('.md'))
        
        return self.results
    
    def _generate_markdown_report(self, output_path: Path):
        """Generate human-readable markdown report."""
        md_lines = [
            "# Subtitle Scan Report",
            f"\nGenerated: {Path(__file__).name}",
            "\n## Summary\n",
            f"- **Total videos scanned**: {self.results['summary'].get('total_videos', 0):,}",
            f"- **Videos with embedded subtitles**: {self.results['summary'].get('videos_with_embedded', 0):,}",
            f"- **Videos without embedded subtitles**: {self.results['summary'].get('videos_without_embedded', 0):,}",
            f"- **Total embedded subtitle tracks**: {self.results['summary'].get('total_embedded_tracks', 0):,}",
            f"- **External subtitle files**: {self.results['summary'].get('external_subtitle_files', 0):,}",
            f"- **Orphaned subtitle files**: {len(self.results['orphaned_subtitles']):,}",
        ]
        
        # Calculate coverage
        total = self.results['summary'].get('total_videos', 0)
        if total > 0:
            with_subs = self.results['summary'].get('videos_with_embedded', 0) + self.results['summary'].get('videos_with_external', 0)
            coverage = with_subs / total * 100
            md_lines.append(f"- **Subtitle Coverage**: {coverage:.1f}%")
        
        md_lines.append("\n## Videos Without Subtitles\n")
        
        no_subs = [v for v in self.results['videos_without_embedded'] 
                   if not v.get('external_subtitles')]
        
        if no_subs:
            md_lines.append(f"**Count**: {len(no_subs)}\n")
            md_lines.append("First 20 files:")
            for video in no_subs[:20]:
                md_lines.append(f"- `{video['path']}`")
            if len(no_subs) > 20:
                md_lines.append(f"- ... and {len(no_subs) - 20} more")
        else:
            md_lines.append("✅ All videos have subtitles!")
        
        md_lines.append("\n## Orphaned Subtitle Files\n")
        
        if self.results['orphaned_subtitles']:
            md_lines.append(f"**Count**: {len(self.results['orphaned_subtitles'])}\n")
            md_lines.append("First 20 files:")
            for sub in self.results['orphaned_subtitles'][:20]:
                md_lines.append(f"- `{sub['path']}`")
            if len(self.results['orphaned_subtitles']) > 20:
                md_lines.append(f"- ... and {len(self.results['orphaned_subtitles']) - 20} more")
        else:
            md_lines.append("✅ No orphaned subtitle files found!")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        
        print(f"✅ Markdown report saved to {output_path}")


def main():
    # Scan all drives
    scanner = SubtitleScanner(drives=['L', 'M', 'Q', 'S', 'W'])
    scanner.scan_all_drives()
    scanner.generate_report()


if __name__ == '__main__':
    main()
