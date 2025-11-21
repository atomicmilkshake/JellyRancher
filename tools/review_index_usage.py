#!/usr/bin/env python3
"""
Review Function Index Usage - Query Statistics and Audit Tool

Provides statistics and analysis of function index query usage to enforce
the "Don't Reinvent the Wheel" rule per master-prompt.md Section II.2.

Usage:
    .venv\Scripts\python.exe tools/review_index_usage.py [--days N] [--summary]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict, Tuple


def parse_log_file(log_file: Path) -> List[Dict]:
    """
    Parse function index query log file.
    
    Args:
        log_file: Path to function_index_queries.log
        
    Returns:
        List of parsed query entries
    """
    queries = []
    
    if not log_file.exists():
        return queries
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse format: "YYYY-MM-DD HH:MM:SS | QUERY: ... | RESULTS: N | TOP-K: N"
                parts = line.split(' | ')
                if len(parts) < 4:
                    continue
                
                try:
                    timestamp_str = parts[0]
                    query = parts[1].replace('QUERY: ', '')
                    results = int(parts[2].replace('RESULTS: ', ''))
                    top_k = int(parts[3].replace('TOP-K: ', ''))
                    
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    queries.append({
                        'timestamp': timestamp,
                        'query': query,
                        'results': results,
                        'top_k': top_k
                    })
                except (ValueError, IndexError) as e:
                    # Skip malformed lines
                    continue
    except Exception as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
    
    return queries


def filter_by_days(queries: List[Dict], days: int) -> List[Dict]:
    """Filter queries to last N days."""
    if days <= 0:
        return queries
    
    cutoff = datetime.now() - timedelta(days=days)
    return [q for q in queries if q['timestamp'] >= cutoff]


def generate_statistics(queries: List[Dict]) -> Dict:
    """
    Generate statistics from query log.
    
    Returns:
        Dictionary with statistics
    """
    if not queries:
        return {
            'total_queries': 0,
            'date_range': None,
            'avg_results': 0,
            'total_results': 0,
            'unique_queries': 0,
            'most_common_queries': [],
            'queries_by_day': {}
        }
    
    timestamps = [q['timestamp'] for q in queries]
    results = [q['results'] for q in queries]
    query_texts = [q['query'] for q in queries]
    
    # Date range
    min_date = min(timestamps)
    max_date = max(timestamps)
    
    # Most common queries
    query_counter = Counter(query_texts)
    most_common = query_counter.most_common(10)
    
    # Queries by day
    queries_by_day = Counter([q['timestamp'].date() for q in queries])
    
    return {
        'total_queries': len(queries),
        'date_range': (min_date, max_date),
        'avg_results': sum(results) / len(results) if results else 0,
        'total_results': sum(results),
        'unique_queries': len(set(query_texts)),
        'most_common_queries': most_common,
        'queries_by_day': dict(queries_by_day)
    }


def print_summary(stats: Dict) -> None:
    """Print summary statistics."""
    print("=" * 80)
    print("FUNCTION INDEX QUERY STATISTICS")
    print("=" * 80)
    print()
    
    if stats['total_queries'] == 0:
        print("No queries found in log file.")
        print("This may indicate:")
        print("  - Function index is not being used (violates master-prompt.md II.2)")
        print("  - Log file is empty or missing")
        print("  - Queries are being made outside the standard tool")
        return
    
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Unique Queries: {stats['unique_queries']}")
    print(f"Average Results per Query: {stats['avg_results']:.1f}")
    print(f"Total Results Returned: {stats['total_results']}")
    print()
    
    if stats['date_range']:
        min_date, max_date = stats['date_range']
        print(f"Date Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        print()
    
    if stats['most_common_queries']:
        print("Most Common Queries:")
        for query, count in stats['most_common_queries'][:5]:
            print(f"  [{count}x] {query}")
        print()
    
    if stats['queries_by_day']:
        print("Queries by Day (last 7 days):")
        sorted_days = sorted(stats['queries_by_day'].items(), reverse=True)[:7]
        for day, count in sorted_days:
            print(f"  {day}: {count} queries")
        print()


def print_detailed(queries: List[Dict], limit: int = 50) -> None:
    """Print detailed query log."""
    print("=" * 80)
    print("DETAILED QUERY LOG")
    print("=" * 80)
    print()
    
    if not queries:
        print("No queries found.")
        return
    
    # Sort by timestamp (newest first)
    sorted_queries = sorted(queries, key=lambda x: x['timestamp'], reverse=True)
    
    for i, query in enumerate(sorted_queries[:limit], 1):
        timestamp = query['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{i}. [{timestamp}]")
        print(f"   Query: {query['query']}")
        print(f"   Results: {query['results']} (requested top-{query['top_k']})")
        print()
    
    if len(sorted_queries) > limit:
        print(f"... and {len(sorted_queries) - limit} more queries")
        print()


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description='Review function index query usage statistics'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=0,
        help='Filter to last N days (0 = all time)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary statistics only'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Limit detailed output to N queries (default: 50)'
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        default=Path('data/function_index_queries.log'),
        help='Path to query log file'
    )
    
    args = parser.parse_args()
    
    # Parse log file
    queries = parse_log_file(args.log_file)
    
    # Filter by days if specified
    if args.days > 0:
        queries = filter_by_days(queries, args.days)
        print(f"Filtered to last {args.days} days\n")
    
    # Generate statistics
    stats = generate_statistics(queries)
    
    # Print output
    print_summary(stats)
    
    if not args.summary:
        print_detailed(queries, limit=args.limit)


if __name__ == "__main__":
    main()

