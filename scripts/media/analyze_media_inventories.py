"""
Analyze media inventories to identify extras, featurettes, and organizational issues.
"""
import re
from pathlib import Path
from collections import defaultdict
import json

def analyze_inventory_file(inventory_path):
    """Analyze a single inventory file for extras and organizational patterns."""
    
    with open(inventory_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    results = {
        'total_files': len(lines),
        'video_files': [],
        'potential_extras': [],
        'organizational_issues': [],
        'file_types': defaultdict(int),
        'folder_structure': defaultdict(list)
    }
    
    # Common video extensions
    video_exts = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.flv', '.webm'}
    
    # Patterns that might indicate extras/featurettes
    extra_patterns = [
        r'(?i)\b(extra|extras|featurette|featurettes)\b',
        r'(?i)\b(behind.the.scenes?|bts)\b',
        r'(?i)\b(deleted.scenes?)\b',
        r'(?i)\b(making.of)\b',
        r'(?i)\b(bonus)\b',
        r'(?i)\b(interview|interviews)\b',
        r'(?i)\b(commentary)\b',
        r'(?i)\b(blooper|bloopers|gag.reel)\b',
        r'(?i)\b(trailer|trailers)\b',
        r'(?i)\b(documentary|documentaries)\b',
        r'(?i)\b(special.features?)\b',
    ]
    
    for line in lines:
        path = Path(line)
        ext = path.suffix.lower()
        
        # Count file types
        results['file_types'][ext] += 1
        
        # Track video files
        if ext in video_exts:
            results['video_files'].append(str(path))
            
            # Check for potential extras
            for pattern in extra_patterns:
                if re.search(pattern, str(path)):
                    results['potential_extras'].append({
                        'path': str(path),
                        'pattern_matched': pattern
                    })
                    break
        
        # Track folder structure
        if len(path.parts) > 1:
            parent = str(path.parent)
            results['folder_structure'][parent].append(path.name)
    
    return results

def generate_report(all_results):
    """Generate a comprehensive report from all inventory analyses."""
    
    report = {
        'summary': {
            'total_drives_scanned': len(all_results),
            'total_video_files': 0,
            'total_potential_extras': 0,
        },
        'by_drive': {},
        'recommendations': []
    }
    
    for drive_name, results in all_results.items():
        report['summary']['total_video_files'] += len(results['video_files'])
        report['summary']['total_potential_extras'] += len(results['potential_extras'])
        
        report['by_drive'][drive_name] = {
            'total_files': results['total_files'],
            'video_files_count': len(results['video_files']),
            'potential_extras_count': len(results['potential_extras']),
            'file_types': dict(results['file_types']),
            'potential_extras': results['potential_extras']
        }
    
    # Generate recommendations
    if report['summary']['total_potential_extras'] > 0:
        report['recommendations'].append(
            f"Found {report['summary']['total_potential_extras']} potential extras/featurettes that may need organization"
        )
    
    return report

def main():
    """Main analysis function."""
    
    inventory_files = {
        'M_Movies': Path('scripts/Movies_inventory.txt'),
        'M_TV_Shows': Path('scripts/TV_Shows_inventory.txt'),
        'L_MEDIA': Path('scripts/L_MEDIA_inventory.txt'),
        'Q_MEDIA': Path('scripts/Q_MEDIA_inventory.txt')
    }
    
    all_results = {}
    
    for name, inv_path in inventory_files.items():
        if inv_path.exists():
            print(f"Analyzing {name}...")
            all_results[name] = analyze_inventory_file(inv_path)
        else:
            print(f"Warning: {inv_path} not found, skipping...")
    
    # Generate report
    report = generate_report(all_results)
    
    # Save report
    output_path = Path('scripts/media_inventory_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nAnalysis complete! Report saved to: {output_path}")
    print(f"\nSummary:")
    print(f"  Total video files: {report['summary']['total_video_files']}")
    print(f"  Potential extras found: {report['summary']['total_potential_extras']}")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

if __name__ == '__main__':
    main()
