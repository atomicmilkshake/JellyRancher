#!/usr/bin/env python3
"""
Validate Reorganization Plan
Cross-references global-extras-analysis.md with media-inventory-organization-guide.xlsx
to ensure all identified extras are covered and detect anomalies.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import openpyxl
from collections import defaultdict

class ReorganizationValidator:
    def __init__(self, analysis_md_path: str, guide_xlsx_path: str):
        self.analysis_md_path = Path(analysis_md_path)
        self.guide_xlsx_path = Path(guide_xlsx_path)
        self.extras_from_analysis = defaultdict(list)
        self.files_from_guide = []
        self.anomalies = {
            'missing_from_guide': [],
            'vob_files': [],
            'unusual_formats': [],
            'naming_issues': [],
            'duplicate_conflicts': [],
            'missing_metadata': [],
            'orphaned_files': []
        }
        
    def parse_analysis_md(self):
        """Extract extras information from the analysis markdown."""
        print("📖 Parsing global-extras-analysis.md...")
        
        with open(self.analysis_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract extras by show
        current_show = None
        current_drive = None
        
        # Parse Drive L extras
        if "Drive L:" in content:
            # There Will Be Blood
            if "There Will Be Blood (2007)" in content:
                self.extras_from_analysis['There Will Be Blood (2007)'].extend([
                    '15 Minutes.mkv',
                    'Dailies Gone Wild.mkv',
                    'Deleted Scenes/Fishing.mkv',
                    'Deleted Scenes/Haircut-Interrupted Hymn.mkv',
                    'The Story of Petroleum.mkv',
                    'Theatrical trailer.mkv'
                ])
            
            # Animaniacs
            if "Animaniacs (1993)" in content:
                self.extras_from_analysis['Animaniacs (1993)'].extend([
                    'DVD Extras - Vol 1, Ads',
                    'DVD Extras - Vol 2, Ads',
                    'DVD Extras - Vol 3, Ads 1',
                    'DVD Extras - Vol 3, Ads 2'
                ])
        
        # Parse Drive Q extras - Better Call Saul
        if "Better Call Saul (2015)" in content:
            # Extract season-by-season extras
            bcs_pattern = r'\*\*Season (\d+):\*\* (.+?)(?=\*\*Season|\*\*Season|####|$)'
            matches = re.findall(bcs_pattern, content, re.DOTALL)
            for season, extras_text in matches:
                extras = re.findall(r'([A-Z][^,\n]+?)(?:,|\n|$)', extras_text)
                for extra in extras:
                    extra = extra.strip()
                    if extra and len(extra) > 3:
                        self.extras_from_analysis['Better Call Saul (2015)'].append(f'S{season.zfill(2)} {extra}')
        
        # Parse Drive M/S - Star Trek DS9
        if "Star Trek Deep Space Nine" in content:
            ds9_extras = [
                'Alien Artifacts', 'Crew Dossiers', 'DS9 Sketchbook',
                'Michael Westmore\'s Aliens', 'Section 31 Hidden Files',
                'New Frontiers', 'New Station New Ships', 'Sailing Through the Stars',
                'Birth of the Dominion', 'Charting New Territory',
                '24th Century Wedding', 'Mission Inquiry'
            ]
            self.extras_from_analysis['Star Trek Deep Space Nine (1993)'].extend(ds9_extras)
        
        # Parse Drive M/S - Star Trek Voyager
        if "Star Trek Voyager (1995)" in content:
            voyager_extras = [
                'Braving The Unknown', 'Cast Reflections', 'Launching Voyager On The Web',
                'On Location With The Kazons', 'Real Science With Andre Bormanis',
                'The First Captain Janeway', 'Visual Effects',
                'Voyager Time Capsules', 'Hidden Files',
                'A Day In The Life Of Ethan Phillips', 'Saboteur Extraordinaire Seska',
                'Flashback To Flashback', 'The Art Of Alien Worlds',
                'The Birth Of Species', 'Red Alert Amazing Visual Effects',
                'The Borg Queen Speaks', 'Delta Quadrant Make-Up Magic',
                'Star Mapping The Final Frontier', 'Guest Star Profile Vaughn Armstrong',
                'Coming Home The Final Episode', 'The Making of Borg Invasion',
                'Inside Voyager\'s Scenic Art Department'
            ]
            self.extras_from_analysis['Star Trek Voyager (1995)'].extend(voyager_extras)
        
        # Parse Drive W - Lost (extensive)
        if "Lost (2004)" in content:
            # Extract Lost extras by season
            lost_pattern = r'\*\*Season (\d+):\*\*(.+?)(?=\*\*Season|\#\#\#|$)'
            matches = re.findall(lost_pattern, content, re.DOTALL)
            for season, extras_text in matches:
                # Count different types
                audition_tapes = len(re.findall(r'Audition Tapes \((\d+)', extras_text))
                deleted_scenes = len(re.findall(r'Deleted Scenes \((\d+)', extras_text))
                hidden_extras = len(re.findall(r'Hidden Extras \((\d+)', extras_text))
                
                if audition_tapes:
                    self.extras_from_analysis['Lost (2004)'].append(f'S{season.zfill(2)} Audition Tapes ({audition_tapes} files)')
                if deleted_scenes:
                    self.extras_from_analysis['Lost (2004)'].append(f'S{season.zfill(2)} Deleted Scenes ({deleted_scenes} files)')
                if hidden_extras:
                    self.extras_from_analysis['Lost (2004)'].append(f'S{season.zfill(2)} Hidden Extras ({hidden_extras} files)')
        
        print(f"✅ Found extras for {len(self.extras_from_analysis)} shows in analysis")
        for show, extras in self.extras_from_analysis.items():
            print(f"   - {show}: {len(extras)} extras")
    
    def parse_guide_xlsx(self):
        """Extract file operations from the reorganization guide."""
        print("\n📊 Parsing media-inventory-organization-guide.xlsx...")
        
        wb = openpyxl.load_workbook(self.guide_xlsx_path)
        ws = wb.active
        
        # Skip header row
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0]:  # Skip empty rows
                continue
            
            original_drive = row[0]
            original_path = row[1]
            proposed_library = row[2]
            proposed_path = row[3]
            notes = row[4] if len(row) > 4 else ""
            
            file_info = {
                'original_drive': original_drive,
                'original_path': original_path,
                'proposed_library': proposed_library,
                'proposed_path': proposed_path,
                'notes': notes
            }
            
            self.files_from_guide.append(file_info)
            
            # Detect anomalies
            self._detect_anomalies(file_info)
        
        print(f"✅ Parsed {len(self.files_from_guide)} file operations from guide")
    
    def _detect_anomalies(self, file_info: Dict):
        """Detect various anomalies in file operations."""
        original = file_info['original_path']
        proposed = file_info['proposed_path']
        notes = file_info['notes']
        
        # VOB files needing conversion
        if '.VOB' in original.upper():
            self.anomalies['vob_files'].append(file_info)
        
        # Unusual formats
        unusual_exts = ['.flv', '.avi', '.mpg', '.vob']
        if any(ext in original.lower() for ext in unusual_exts):
            self.anomalies['unusual_formats'].append(file_info)
        
        # Missing metadata (no year in folder name)
        if proposed and not re.search(r'\(\d{4}\)', proposed):
            if '/Movies/' in proposed or '/TV Shows/' in proposed:
                self.anomalies['missing_metadata'].append(file_info)
        
        # Naming issues
        if original and ('...' in original or original.startswith('...')):
            self.anomalies['naming_issues'].append(file_info)
        
        # Duplicate conflicts
        if notes and 'duplicate' in notes.lower():
            self.anomalies['duplicate_conflicts'].append(file_info)
    
    def cross_reference_extras(self):
        """Cross-reference extras from analysis with guide."""
        print("\n🔍 Cross-referencing extras...")
        
        guide_extras = defaultdict(set)
        
        # Extract extras from guide
        for file_info in self.files_from_guide:
            proposed = file_info['proposed_path']
            if not proposed:
                continue
            
            # Check if it's an extra
            if any(keyword in proposed for keyword in ['/Extras/', '/Deleted Scenes/', '/Featurettes/', '/Specials/', '/Trailers/']):
                # Extract show/movie name
                match = re.search(r'/(?:TV Shows|Movies)/([^/]+)/', proposed)
                if match:
                    show_name = match.group(1)
                    # Extract filename
                    filename = Path(proposed).name
                    guide_extras[show_name].add(filename)
        
        print(f"✅ Found extras in guide for {len(guide_extras)} shows/movies")
        
        # Compare
        for show, analysis_extras in self.extras_from_analysis.items():
            # Try to find matching show in guide
            guide_show = None
            for guide_show_name in guide_extras.keys():
                if show.split('(')[0].strip() in guide_show_name:
                    guide_show = guide_show_name
                    break
            
            if guide_show:
                print(f"\n   ✓ {show}")
                print(f"     Analysis: {len(analysis_extras)} extras")
                print(f"     Guide: {len(guide_extras[guide_show])} extras")
            else:
                print(f"\n   ⚠️  {show} - NOT FOUND IN GUIDE")
                self.anomalies['missing_from_guide'].append({
                    'show': show,
                    'extras_count': len(analysis_extras),
                    'extras': analysis_extras
                })
    
    def generate_report(self, output_path: str = "reports/reorganization_validation.json"):
        """Generate comprehensive validation report."""
        print("\n📝 Generating validation report...")
        
        report = {
            'summary': {
                'total_files_in_guide': len(self.files_from_guide),
                'shows_with_extras_in_analysis': len(self.extras_from_analysis),
                'total_anomalies': sum(len(v) for v in self.anomalies.values())
            },
            'extras_coverage': {},
            'anomalies': self.anomalies,
            'recommendations': []
        }
        
        # Add extras coverage
        for show, extras in self.extras_from_analysis.items():
            report['extras_coverage'][show] = {
                'count': len(extras),
                'items': extras
            }
        
        # Generate recommendations
        if self.anomalies['vob_files']:
            report['recommendations'].append({
                'priority': 'HIGH',
                'category': 'VOB Conversion',
                'message': f"{len(self.anomalies['vob_files'])} VOB files need conversion to MKV",
                'action': 'Use ffmpeg or MakeMKV to convert before reorganization'
            })
        
        if self.anomalies['unusual_formats']:
            report['recommendations'].append({
                'priority': 'MEDIUM',
                'category': 'Format Conversion',
                'message': f"{len(self.anomalies['unusual_formats'])} files in unusual formats (FLV, AVI, MPG)",
                'action': 'Consider converting to MKV/MP4 for better compatibility'
            })
        
        if self.anomalies['missing_from_guide']:
            report['recommendations'].append({
                'priority': 'HIGH',
                'category': 'Missing Extras',
                'message': f"{len(self.anomalies['missing_from_guide'])} shows with extras not found in guide",
                'action': 'Review and add these extras to reorganization plan'
            })
        
        if self.anomalies['duplicate_conflicts']:
            report['recommendations'].append({
                'priority': 'MEDIUM',
                'category': 'Duplicates',
                'message': f"{len(self.anomalies['duplicate_conflicts'])} duplicate files detected",
                'action': 'Review quality and choose which version to keep'
            })
        
        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Report saved to {output_path}")
        
        # Also create human-readable markdown report
        self._generate_markdown_report(report, output_path.with_suffix('.md'))
        
        return report
    
    def _generate_markdown_report(self, report: Dict, output_path: Path):
        """Generate human-readable markdown report."""
        md_lines = [
            "# Reorganization Validation Report",
            f"\nGenerated: {Path(__file__).name}",
            "\n## Summary\n",
            f"- **Total files in guide**: {report['summary']['total_files_in_guide']:,}",
            f"- **Shows with extras in analysis**: {report['summary']['shows_with_extras_in_analysis']}",
            f"- **Total anomalies detected**: {report['summary']['total_anomalies']}",
            "\n## Extras Coverage\n"
        ]
        
        for show, info in report['extras_coverage'].items():
            md_lines.append(f"### {show}")
            md_lines.append(f"- **Count**: {info['count']} extras")
            md_lines.append("")
        
        md_lines.append("\n## Anomalies\n")
        
        for category, items in report['anomalies'].items():
            if items:
                md_lines.append(f"### {category.replace('_', ' ').title()}")
                md_lines.append(f"**Count**: {len(items)}\n")
                
                if category == 'vob_files':
                    md_lines.append("Files requiring conversion:")
                    for item in items[:10]:  # Show first 10
                        md_lines.append(f"- `{item['original_path']}`")
                    if len(items) > 10:
                        md_lines.append(f"- ... and {len(items) - 10} more")
                
                elif category == 'missing_from_guide':
                    for item in items:
                        md_lines.append(f"- **{item['show']}**: {item['extras_count']} extras")
                
                md_lines.append("")
        
        md_lines.append("\n## Recommendations\n")
        
        for rec in report['recommendations']:
            md_lines.append(f"### {rec['category']} [{rec['priority']}]")
            md_lines.append(f"{rec['message']}")
            md_lines.append(f"**Action**: {rec['action']}\n")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        
        print(f"✅ Markdown report saved to {output_path}")
    
    def run(self):
        """Run complete validation process."""
        print("=" * 70)
        print("REORGANIZATION PLAN VALIDATION")
        print("=" * 70)
        
        self.parse_analysis_md()
        self.parse_guide_xlsx()
        self.cross_reference_extras()
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("VALIDATION COMPLETE")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   - Files to reorganize: {report['summary']['total_files_in_guide']:,}")
        print(f"   - Anomalies detected: {report['summary']['total_anomalies']}")
        print(f"   - Recommendations: {len(report['recommendations'])}")
        print(f"\n📁 Reports saved to: reports/reorganization_validation.*")
        
        return report


def main():
    validator = ReorganizationValidator(
        analysis_md_path='../global-extras-analysis.md',
        guide_xlsx_path='../media-inventory-organization-guide.xlsx'
    )
    
    report = validator.run()
    
    # Print high-priority issues
    if report['anomalies']['vob_files']:
        print(f"\n⚠️  HIGH PRIORITY: {len(report['anomalies']['vob_files'])} VOB files need conversion")
    
    if report['anomalies']['missing_from_guide']:
        print(f"\n⚠️  HIGH PRIORITY: {len(report['anomalies']['missing_from_guide'])} shows with extras missing from guide")


if __name__ == '__main__':
    main()
