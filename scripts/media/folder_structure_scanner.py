#!/usr/bin/env python3
"""
Folder Structure Scanner - Step 1 of JellyRancher Workflow

Scans selected folders recursively to:
1. Generate a bare file list with complete file paths
2. Summarize folder structure with video file counts
3. Provide hierarchical view of content without listing every file

Supports multiple video formats and provides Jellyfin-compliant analysis.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import json


# Common video file extensions
VIDEO_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv', '.ts', '.m2ts'
}


class FolderStructureScanner:
    """
    Scanner for generating file lists and structural summaries of media folders.
    """
    
    def __init__(self, root_folders: List[str]):
        """
        Initialize scanner with one or more root folders to scan.
        
        Args:
            root_folders: List of folder paths to scan recursively
        """
        self.root_folders = [Path(folder) for folder in root_folders]
        self.video_files = []
        self.all_files = []
        self.structure_summary = {}
        
    def scan_all(self) -> Tuple[List[str], Dict]:
        """
        Perform complete scan of all configured folders.
        
        Returns:
            Tuple of (video_file_list, structure_summary)
        """
        self.video_files = []
        self.all_files = []
        self.structure_summary = {}
        
        for root_folder in self.root_folders:
            if not root_folder.exists():
                print(f"Warning: Folder does not exist: {root_folder}")
                continue
                
            print(f"Scanning: {root_folder}")
            self._scan_folder(root_folder)
            
        return self.video_files, self.structure_summary
    
    def _scan_folder(self, folder_path: Path):
        """
        Recursively scan a single folder and collect file information.
        
        Args:
            folder_path: Path to folder to scan
        """
        try:
            # Walk the directory tree
            for root, dirs, files in os.walk(folder_path):
                root_path = Path(root)
                
                # Process all files in current directory
                for filename in files:
                    file_path = root_path / filename
                    file_ext = file_path.suffix.lower()
                    
                    # Add to all files list
                    self.all_files.append(str(file_path))
                    
                    # Add to video files if it's a video
                    if file_ext in VIDEO_EXTENSIONS:
                        self.video_files.append(str(file_path))
                        
        except PermissionError as e:
            print(f"Permission denied: {folder_path}")
        except Exception as e:
            print(f"Error scanning {folder_path}: {e}")
    
    def generate_structure_summary(self) -> Dict:
        """
        Generate a hierarchical summary of the scanned folders.
        
        Returns:
            Dictionary containing folder structure with video counts
        """
        summary = {}
        
        for root_folder in self.root_folders:
            if not root_folder.exists():
                continue
                
            folder_name = root_folder.name
            folder_data = self._analyze_folder_structure(root_folder)
            summary[str(root_folder)] = folder_data
            
        self.structure_summary = summary
        return summary
    
    def _analyze_folder_structure(self, folder_path: Path) -> Dict:
        """
        Analyze a single folder's structure and count video files.
        
        Args:
            folder_path: Path to analyze
            
        Returns:
            Dictionary with folder analysis
        """
        analysis = {
            'path': str(folder_path),
            'name': folder_path.name,
            'total_videos': 0,
            'direct_videos': 0,
            'subfolders': {},
            'type': 'unknown'
        }
        
        try:
            # Count direct video files in this folder
            direct_videos = []
            subdirs = []
            
            for item in folder_path.iterdir():
                if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS:
                    direct_videos.append(item.name)
                elif item.is_dir():
                    subdirs.append(item)
            
            analysis['direct_videos'] = len(direct_videos)
            analysis['total_videos'] = len(direct_videos)
            
            # Recursively analyze subfolders
            for subdir in subdirs:
                sub_analysis = self._analyze_folder_structure(subdir)
                analysis['subfolders'][subdir.name] = sub_analysis
                analysis['total_videos'] += sub_analysis['total_videos']
            
            # Determine folder type
            analysis['type'] = self._classify_folder(folder_path, analysis)
            
        except PermissionError:
            analysis['error'] = 'Permission denied'
        except Exception as e:
            analysis['error'] = str(e)
            
        return analysis
    
    def _classify_folder(self, folder_path: Path, analysis: Dict) -> str:
        """
        Classify a folder based on its structure and content.
        
        Args:
            folder_path: Path to classify
            analysis: Analysis dictionary for this folder
            
        Returns:
            Classification string (tv_show, movie_collection, season, mixed, etc.)
        """
        folder_name = folder_path.name.lower()
        subfolders = analysis['subfolders']
        
        # Check if it has season folders
        season_folders = [name for name in subfolders.keys() 
                         if 'season' in name.lower() or name.lower().startswith('s') and name[1:].isdigit()]
        
        if season_folders and len(season_folders) >= 2:
            return 'tv_show_with_seasons'
        
        # Check if this is a season folder
        if 'season' in folder_name or (folder_name.startswith('s') and folder_name[1:3].isdigit()):
            return 'season'
        
        # Check if it has many video files directly (likely a show without season folders)
        if analysis['direct_videos'] > 5:
            return 'tv_show_flat'
        
        # Check if it has few videos and no subfolders (likely individual movie folder)
        if analysis['direct_videos'] > 0 and len(subfolders) == 0:
            return 'movie'
        
        # Collection of movies or shows
        if len(subfolders) > 0 and analysis['total_videos'] > 0:
            return 'collection'
        
        return 'unknown'
    
    def save_file_list(self, output_path: str):
        """
        Save the complete file list to a text file.
        
        Args:
            output_path: Path where file list should be saved
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for file_path in self.video_files:
                f.write(f"{file_path}\n")
        
        print(f"File list saved: {output_file}")
        print(f"Total video files: {len(self.video_files)}")
    
    def save_structure_summary(self, output_path: str):
        """
        Save the structure summary to a JSON file.
        
        Args:
            output_path: Path where summary should be saved
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        summary_data = {
            'scan_date': datetime.now().isoformat(),
            'root_folders': [str(f) for f in self.root_folders],
            'total_video_files': len(self.video_files),
            'total_all_files': len(self.all_files),
            'structure': self.structure_summary
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"Structure summary saved: {output_file}")
    
    def print_structure_summary(self, max_depth: int = 3):
        """
        Print a human-readable structure summary to console.
        
        Args:
            max_depth: Maximum depth to display (prevents overwhelming output)
        """
        print("\n" + "="*80)
        print("FOLDER STRUCTURE SUMMARY")
        print("="*80)
        
        for root_path, analysis in self.structure_summary.items():
            self._print_folder_analysis(analysis, depth=0, max_depth=max_depth)
    
    def _print_folder_analysis(self, analysis: Dict, depth: int = 0, max_depth: int = 3):
        """
        Recursively print folder analysis with indentation.
        
        Args:
            analysis: Analysis dictionary to print
            depth: Current depth level
            max_depth: Maximum depth to display
        """
        if depth > max_depth:
            return
        
        indent = "  " * depth
        folder_name = analysis['name']
        folder_type = analysis['type']
        total_videos = analysis['total_videos']
        direct_videos = analysis['direct_videos']
        
        # Format the output based on folder type
        if folder_type == 'tv_show_with_seasons':
            season_count = len(analysis['subfolders'])
            print(f"{indent}📁 {folder_name} ({total_videos} videos across {season_count} seasons)")
            
            # Print season info
            for season_name, season_data in sorted(analysis['subfolders'].items()):
                season_videos = season_data['total_videos']
                print(f"{indent}  └─ {season_name}: {season_videos} videos")
                
        elif folder_type == 'tv_show_flat':
            print(f"{indent}📁 {folder_name} ({direct_videos} videos in this folder)")
            
        elif folder_type == 'movie':
            print(f"{indent}🎬 {folder_name} ({direct_videos} video{'s' if direct_videos != 1 else ''})")
            
        elif folder_type == 'collection':
            subfolder_count = len(analysis['subfolders'])
            print(f"{indent}📁 {folder_name} ({total_videos} videos, {subfolder_count} subfolders)")
            
            # Recursively print subfolders if within depth limit
            if depth < max_depth:
                for subfolder_name, subfolder_data in sorted(analysis['subfolders'].items()):
                    self._print_folder_analysis(subfolder_data, depth + 1, max_depth)
        else:
            if total_videos > 0:
                print(f"{indent}📁 {folder_name} ({total_videos} videos)")


def main():
    """
    Example usage of the folder structure scanner.
    """
    import sys
    
    # Check if folders were provided as arguments
    if len(sys.argv) > 1:
        folders_to_scan = sys.argv[1:]
    else:
        # Default test folders
        print("Usage: python folder_structure_scanner.py <folder1> [folder2] ...")
        print("\nNo folders specified. Using default example folders:")
        folders_to_scan = [
            r"V:\#MEDIA\TV Shows",
            r"V:\#MEDIA\Movies"
        ]
        print(f"  - {folders_to_scan[0]}")
        print(f"  - {folders_to_scan[1]}")
        print()
    
    # Create scanner
    scanner = FolderStructureScanner(folders_to_scan)
    
    # Perform scan
    print("Starting scan...\n")
    video_files, structure = scanner.scan_all()
    
    # Generate and print summary
    print("\nGenerating structure summary...")
    scanner.generate_structure_summary()
    scanner.print_structure_summary()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    file_list_path = f"data/scan_file_list_{timestamp}.txt"
    scanner.save_file_list(file_list_path)
    
    summary_path = f"data/scan_structure_{timestamp}.json"
    scanner.save_structure_summary(summary_path)
    
    print("\n" + "="*80)
    print(f"✅ Scan complete!")
    print(f"   Total video files found: {len(video_files)}")
    print(f"   File list: {file_list_path}")
    print(f"   Structure summary: {summary_path}")
    print("="*80)


if __name__ == "__main__":
    main()
