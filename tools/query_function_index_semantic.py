#!/usr/bin/env python3
"""
Semantic search for the LLM function index using TF-IDF similarity.

This is a lightweight semantic search implementation that doesn't require
heavy dependencies like ChromaDB, PyTorch, or sentence-transformers.
Uses sklearn's TF-IDF vectorizer for semantic similarity matching.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Error: scikit-learn is required but not installed.")
    print("Run: .venv/Scripts/python.exe -m pip install scikit-learn")
    sys.exit(1)


class SemanticFunctionSearch:
    """Semantic search interface for the function index using TF-IDF."""

    def __init__(self, index_file: str = "data/llm_function_index.json"):
        self.index_file = Path(index_file)
        if not self.index_file.exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")

        with open(self.index_file, 'r', encoding='utf-8') as f:
            self.index = json.load(f)

        self.functions = self.index.get('functions', {})
        self.metadata = self.index.get('metadata', {})

        # Prepare documents for search
        self._prepare_search_index()

    def _prepare_search_index(self) -> None:
        """Prepare TF-IDF index for semantic search."""
        print(f"Preparing search index...")

        self.function_list = []
        self.documents = []

        for file_path, funcs in self.functions.items():
            for func in funcs:
                # Skip if not a dict
                if not isinstance(func, dict):
                    continue

                # Build searchable text
                text_parts = []

                # Function name (repeated for importance)
                name = func.get('name', '')
                if not name:
                    continue
                text_parts.append(f"{name} {name} {name}")

                # Description
                desc = func.get('description', '')
                if desc:
                    text_parts.append(desc)

                # Implementation
                impl = func.get('implementation', '')
                if impl:
                    text_parts.append(impl)

                # Parameters
                inputs = func.get('inputs', {})
                if isinstance(inputs, dict):
                    params = inputs.get('parameters', [])
                    if isinstance(params, list):
                        param_texts = [
                            f"{p.get('name', '')} {p.get('type', '')} {p.get('description', '')}"
                            for p in params if isinstance(p, dict)
                        ]
                        text_parts.extend(param_texts)

                # Return type
                outputs = func.get('outputs', {})
                if isinstance(outputs, dict):
                    ret = outputs.get('return_value', {})
                    if isinstance(ret, dict):
                        text_parts.append(f"{ret.get('type', '')} {ret.get('description', '')}")

                # Notes
                notes = func.get('notes', [])
                if isinstance(notes, list):
                    text_parts.extend([n for n in notes if isinstance(n, str)])

                # Usage example
                example = func.get('usage_example', '')
                if example:
                    text_parts.append(example)

                document = " ".join(text_parts)

                self.function_list.append({
                    'name': name,
                    'file_path': file_path,
                    'line': func.get('line', 0),
                    'data': func
                })
                self.documents.append(document)

        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=1,
            max_df=0.8
        )

        # Fit and transform documents
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)

        print(f"* Indexed {len(self.function_list)} functions")
        print(f"* TF-IDF vocabulary size: {len(self.vectorizer.vocabulary_)}")

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using TF-IDF cosine similarity.

        Args:
            query: Search query
            top_k: Number of top results to return
            min_score: Minimum similarity score (0-1)

        Returns:
            List of matching functions with scores
        """
        # Transform query
        query_vec = self.vectorizer.transform([query])

        # Compute cosine similarity
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Filter by minimum score and build results
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score >= min_score:
                func_info = self.function_list[idx]
                results.append({
                    'function': func_info['data'],
                    'file_path': func_info['file_path'],
                    'line': func_info['line'],
                    'name': func_info['name'],
                    'score': float(score)
                })

        return results

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Convenience method for semantic search."""
        return self.semantic_search(query, top_k=top_k)

    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'total_functions': len(self.function_list),
            'total_files': len(self.functions),
            'vocabulary_size': len(self.vectorizer.vocabulary_),
            **self.metadata.get('statistics', {})
        }

    def print_result(self, result: Dict[str, Any], show_details: bool = False) -> None:
        """Pretty print a search result."""
        print("=" * 80)
        print(f"Score: {result['score']:.3f}")
        print(f"Function: {result['name']}")
        print(f"File: {result['file_path']}:{result['line']}")

        func = result['function']

        if func.get('class_name'):
            print(f"Class: {func['class_name']}")
        print()

        if func.get('description'):
            print("Description:")
            desc = func['description']
            if not show_details and len(desc) > 300:
                desc = desc[:300] + "..."
            print(f"  {desc}")
            print()

        if show_details:
            if func.get('implementation'):
                print("Implementation:")
                impl = func['implementation']
                if len(impl) > 500:
                    impl = impl[:500] + "..."
                print(f"  {impl}")
                print()

            if func.get('inputs', {}).get('parameters'):
                print("Parameters:")
                for param in func['inputs']['parameters']:
                    req = "required" if param.get('required', False) else "optional"
                    param_type = param.get('type', 'Any')
                    print(f"  {param['name']}: {param_type} ({req})")
                    if param.get('description'):
                        print(f"    {param['description']}")
                print()

            if func.get('outputs', {}).get('return_value'):
                ret = func['outputs']['return_value']
                print("Returns:")
                print(f"  {ret.get('type', 'Any')}")
                if ret.get('description'):
                    print(f"    {ret['description']}")
                print()


def _log_query_to_file(query: str, result_count: int, top_k: int) -> None:
    """
    Log function index query to audit file.
    
    Per master-prompt.md Section II.2, all function index queries must be logged
    to enforce the "Don't Reinvent the Wheel" rule. This creates an audit trail
    of all queries for review and enforcement purposes.
    
    Args:
        query: The search query string
        result_count: Number of results returned
        top_k: Maximum number of results requested
    """
    try:
        log_dir = Path('data')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'function_index_queries.log'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} | QUERY: {query} | RESULTS: {result_count} | TOP-K: {top_k}\n")
    except Exception as e:
        # Don't fail the query if logging fails
        print(f"Warning: Failed to log query: {e}", file=sys.stderr)


def main():
    """CLI interface for semantic search."""
    parser = argparse.ArgumentParser(
        description='Semantic search for function index'
    )
    parser.add_argument(
        '--index',
        default='data/llm_function_index.json',
        help='Path to index file'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Search command
    search_cmd = subparsers.add_parser('search', help='Semantic search')
    search_cmd.add_argument('query', help='Search query')
    search_cmd.add_argument('-k', '--top-k', type=int, default=10, help='Number of results')
    search_cmd.add_argument('--details', action='store_true', help='Show full details')

    # Stats command
    subparsers.add_parser('stats', help='Show index statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        searcher = SemanticFunctionSearch(args.index)

        if args.command == 'search':
            results = searcher.search(args.query, top_k=args.top_k)
            
            # Log query to audit file (per master-prompt.md II.2 enforcement)
            _log_query_to_file(args.query, len(results), args.top_k)

            if not results:
                print(f"No results found for: {args.query}")
                return

            print(f"\nFound {len(results)} results for: '{args.query}'\n")

            for result in results:
                searcher.print_result(result, show_details=args.details)

        elif args.command == 'stats':
            stats = searcher.get_statistics()
            print("Index Statistics:")
            print(f"  Total functions: {stats.get('total_functions', 0)}")
            print(f"  Total files: {stats.get('total_files', 0)}")
            print(f"  Vocabulary size: {stats.get('vocabulary_size', 0)}")
            print(f"  Functions with description: {stats.get('functions_with_description', 0)}")
            print(f"  Functions with implementation: {stats.get('functions_with_implementation', 0)}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
