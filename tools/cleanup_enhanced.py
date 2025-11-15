# cleanup_enhanced.py
"""
Enhanced JellyRancher Project Cleanup Script
Analyzes and categorizes all files for intelligent cleanup decisions
"""

import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re

class ProjectCleaner:
    def __init__(self, root_path):
        self.root = Path(root_path)
        self.analysis = {
            'keep': defaultdict(list),
            'archive': defaultdict(list),
            'delete': defaultdict(list),
            'review': defaultdict(list)
        }
        
        # Define patterns for categorization
        self.patterns = {
            'core_scripts': [
                r'scripts/core/.*\.py$',
                r'scripts/media/.*\.py$',
                r'scripts/ai/.*\.py$',
                r'scripts/_common/.*\.py$'
            ],
            'config': [
                r'config\.json$',
                r'settings\.json$',
                r'requirements.*\.txt$',
                r'pytest\.ini$',
                r'\.gitignore$'
            ],
            'documentation_current': [
                r'USER_GUIDE\.md$',
                r'ARCHITECTURE_REFERENCE\.md$',
                r'docs/.*\.md$',
                r'README\.md$'
            ],
            'documentation_archived': [
                r'archive/documentation.*\.md$',
                r'.*SUMMARY\.md$',
                r'.*ANALYSIS\.md$'
            ],
            'logs': [
                r'logs/.*\.log$',
                r'.*\.jsonl$'
            ],
            'cache': [
                r'chroma_db/.*',
                r'.*_cache\.json$',
                r'\.pytest_cache/.*'
            ],
            'snapshots': [
                r'snapshots/.*\.json$',
                r'\._state/snapshots/.*\.json$'
            ],
            'llm_io': [
                r'LLM_io_log/.*\.json$'
            ],
            'temp': [
                r'temp/.*',
                r'tmp.*/.*',
                r'.*\.bak$',
                r'.*\.backup$'
            ],
            'duplicates': [
                r'.*_backup_.*',
                r'.*_fixed.*\.json$',
                r'.*_processed.*\.json$'
            ],
            'legacy': [
                r'Jellyfin Organizer/.*',
                r'code_cop/.*',
                r'RavenMaven/.*'
            ]
        }
    
    def analyze_file(self, filepath):
        """Categorize a single file"""
        rel_path = filepath.relative_to(self.root)
        str_path = str(rel_path).replace('\\', '/')
        
        # Check each pattern category
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, str_path):
                    return category
        
        return 'review'
    
    def get_file_info(self, filepath):
        """Get metadata about a file"""
        stat = filepath.stat()
        return {
            'path': str(filepath.relative_to(self.root)),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
        }
    
    def scan_project(self):
        """Scan entire project and categorize files"""
        print("🔍 Scanning project...")
        
        for filepath in self.root.rglob('*'):
            if filepath.is_file():
                category = self.analyze_file(filepath)
                info = self.get_file_info(filepath)
                
                # Decide action based on category
                if category in ['core_scripts', 'config', 'documentation_current']:
                    self.analysis['keep'][category].append(info)
                elif category in ['documentation_archived', 'legacy']:
                    self.analysis['archive'][category].append(info)
                elif category in ['temp', 'duplicates']:
                    self.analysis['delete'][category].append(info)
                elif category in ['logs', 'llm_io']:
                    # Keep recent logs, delete old ones
                    if info['age_days'] > 30:
                        self.analysis['delete'][category].append(info)
                    else:
                        self.analysis['keep'][category].append(info)
                elif category == 'snapshots':
                    # Keep last 5 snapshots per directory
                    self.analysis['review'][category].append(info)
                else:
                    self.analysis['review'][category].append(info)
    
    def calculate_stats(self):
        """Calculate statistics for each category"""
        stats = {}
        for action, categories in self.analysis.items():
            stats[action] = {}
            for category, files in categories.items():
                total_size = sum(f['size'] for f in files)
                stats[action][category] = {
                    'count': len(files),
                    'size_mb': round(total_size / (1024 * 1024), 2),
                    'size_gb': round(total_size / (1024 * 1024 * 1024), 3)
                }
        return stats
    
    def generate_report(self):
        """Generate comprehensive cleanup report"""
        stats = self.calculate_stats()
        
        report = []
        report.append("=" * 80)
        report.append("JELLYRANCHER PROJECT CLEANUP ANALYSIS")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        for action in ['keep', 'archive', 'delete', 'review']:
            total_files = sum(s['count'] for s in stats.get(action, {}).values())
            total_size = sum(s['size_mb'] for s in stats.get(action, {}).values())
            report.append(f"{action.upper():12} : {total_files:5} files ({total_size:,.2f} MB)")
        report.append("")
        
        # Detailed breakdown
        for action in ['delete', 'archive', 'review', 'keep']:
            if action not in stats:
                continue
                
            report.append("")
            report.append("=" * 80)
            report.append(f"ACTION: {action.upper()}")
            report.append("=" * 80)
            
            for category, stat in sorted(stats[action].items()):
                report.append("")
                report.append(f"Category: {category}")
                report.append(f"  Files: {stat['count']}")
                report.append(f"  Size:  {stat['size_mb']:.2f} MB ({stat['size_gb']:.3f} GB)")
                
                # Show sample files
                files = self.analysis[action][category][:5]
                if files:
                    report.append("  Sample files:")
                    for f in files:
                        report.append(f"    - {f['path']}")
                    if len(self.analysis[action][category]) > 5:
                        report.append(f"    ... and {len(self.analysis[action][category]) - 5} more")
        
        return "\n".join(report)
    
    def generate_deletion_script(self):
        """Generate PowerShell script for safe deletion"""
        script_lines = [
            "# JellyRancher Cleanup Script",
            f"# Generated: {datetime.now().isoformat()}",
            "# Review this script before running!",
            "",
            "$ErrorActionPreference = 'Stop'",
            "$DeletedCount = 0",
            "$FailedCount = 0",
            "",
            "Write-Host '🧹 Starting JellyRancher Cleanup...' -ForegroundColor Cyan",
            ""
        ]
        
        # Group deletions by category
        for category, files in self.analysis['delete'].items():
            script_lines.append(f"# Deleting {category} ({len(files)} files)")
            script_lines.append("")
            
            for file_info in files:
                filepath = str(self.root / file_info['path'])
                script_lines.append(f"try {{")
                script_lines.append(f"    Remove-Item -Path '{filepath}' -Force -ErrorAction Stop")
                script_lines.append(f"    $DeletedCount++")
                script_lines.append(f"    Write-Host '✓ Deleted: {file_info['path']}' -ForegroundColor Green")
                script_lines.append(f"}} catch {{")
                script_lines.append(f"    $FailedCount++")
                script_lines.append(f"    Write-Host '✗ Failed: {file_info['path']}' -ForegroundColor Red")
                script_lines.append(f"}}")
                script_lines.append("")
        
        script_lines.extend([
            "Write-Host ''",
            "Write-Host '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' -ForegroundColor Cyan",
            "Write-Host 'Cleanup Summary:' -ForegroundColor Cyan",
            "Write-Host \"Deleted: $DeletedCount files\" -ForegroundColor Green",
            "Write-Host \"Failed:  $FailedCount files\" -ForegroundColor Red",
            "Write-Host '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' -ForegroundColor Cyan"
        ])
        
        return "\n".join(script_lines)
    
    def generate_archive_plan(self):
        """Generate plan for archiving files"""
        plan = {
            'timestamp': datetime.now().isoformat(),
            'archives': {}
        }
        
        for category, files in self.analysis['archive'].items():
            archive_name = f"archive_{category}_{datetime.now().strftime('%Y%m%d')}.zip"
            plan['archives'][archive_name] = {
                'category': category,
                'file_count': len(files),
                'files': [f['path'] for f in files]
            }
        
        return plan
    
    def save_results(self, output_dir):
        """Save all analysis results"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save report
        report_file = output_path / f'cleanup_report_{timestamp}.txt'
        report_file.write_text(self.generate_report(), encoding='utf-8')
        print(f"📄 Report saved: {report_file}")
        
        # Save deletion script
        script_file = output_path / f'cleanup_delete_{timestamp}.ps1'
        script_file.write_text(self.generate_deletion_script(), encoding='utf-8')
        print(f"🔧 Deletion script saved: {script_file}")
        
        # Save archive plan
        archive_plan = self.generate_archive_plan()
        archive_file = output_path / f'cleanup_archive_plan_{timestamp}.json'
        archive_file.write_text(json.dumps(archive_plan, indent=2), encoding='utf-8')
        print(f"📦 Archive plan saved: {archive_file}")
        
        # Save raw analysis
        analysis_file = output_path / f'cleanup_analysis_{timestamp}.json'
        analysis_file.write_text(json.dumps(self.analysis, indent=2), encoding='utf-8')
        print(f"📊 Raw analysis saved: {analysis_file}")


def main():
    print("🚀 JellyRancher Enhanced Cleanup Tool")
    print("=" * 80)
    
    # Adjust this path to your project root
    project_root = Path(r'V:\JellyRancher')
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        return
    
    cleaner = ProjectCleaner(project_root)
    
    print(f"📁 Analyzing: {project_root}")
    cleaner.scan_project()
    
    print("💾 Generating reports...")
    cleaner.save_results(project_root / 'cleanup_reports')
    
    print("")
    print("✅ Analysis complete!")
    print("")
    print("Next steps:")
    print("1. Review cleanup_report_*.txt for full analysis")
    print("2. Review cleanup_delete_*.ps1 before running")
    print("3. Review cleanup_archive_plan_*.json for archiving")
    print("")
    print("⚠️  IMPORTANT: Always review before running deletion script!")


if __name__ == '__main__':
    main()