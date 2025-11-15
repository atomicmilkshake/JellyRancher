#!/usr/bin/env python3
"""
Ingest llm_function_index.json and create embeddings for semantic search.

Uses sentence-transformers directly with FAISS for fast similarity search.
Python 3.14 compatible.
"""

import json
import sys
import pickle
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: .venv/Scripts/python.exe -m pip install sentence-transformers faiss-cpu")
    sys.exit(1)


class SemanticFunctionIndexer:
    """Creates semantic search index for functions."""

    def __init__(
        self,
        index_file: str = "data/llm_function_index.json",
        model_name: str = "all-MiniLM-L6-v2",
        output_dir: str = "data/semantic_index"
    ):
        """
        Initialize the indexer.

        Args:
            index_file: Path to llm_function_index.json
            model_name: Sentence transformer model to use
            output_dir: Directory to store the semantic index
        """
        self.index_file = Path(index_file)
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        if not self.index_file.exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")

        print(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

    def load_function_index(self) -> Dict[str, Any]:
        """Load the function index from JSON file."""
        print(f"\nLoading function index from: {self.index_file}")
        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        functions = index.get('functions', {})
        total_functions = sum(len(funcs) for funcs in functions.values())
        print(f"Loaded {total_functions} functions from {len(functions)} files")

        return index

    def prepare_documents(self, index: Dict[str, Any]) -> tuple[List[str], List[Dict], List[str]]:
        """
        Prepare documents for embedding.

        Returns:
            tuple of (texts, metadatas, ids)
        """
        texts = []
        metadatas = []
        ids = []

        functions = index.get('functions', {})

        for file_path, funcs in functions.items():
            for func in funcs:
                # Create unique ID
                func_id = f"{file_path}:{func.get('line', 0)}:{func['name']}"

                # Build searchable text
                text_parts = []

                # Function name (important for matching)
                text_parts.append(f"Function: {func['name']}")

                # Description
                if func.get('description'):
                    text_parts.append(func['description'])

                # Implementation
                if func.get('implementation'):
                    text_parts.append(func['implementation'])

                # Parameters
                if func.get('inputs', {}).get('parameters'):
                    params = func['inputs']['parameters']
                    param_text = "Parameters: " + ", ".join(
                        f"{p['name']}:{p.get('type', 'Any')}" for p in params
                    )
                    text_parts.append(param_text)

                # Return type
                if func.get('outputs', {}).get('return_value'):
                    ret = func['outputs']['return_value']
                    text_parts.append(f"Returns: {ret.get('type', 'Any')}")

                # Notes
                if func.get('notes'):
                    notes_text = " ".join(func['notes'])
                    text_parts.append(f"Notes: {notes_text}")

                # Combine all text
                text = "\n\n".join(text_parts)

                # Create metadata
                metadata = {
                    'id': func_id,
                    'name': func['name'],
                    'file_path': file_path,
                    'line': func.get('line', 0),
                    'class_name': func.get('class_name', ''),
                    'description_short': (func.get('description', '')[:200] + '...'
                                         if len(func.get('description', '')) > 200
                                         else func.get('description', '')),
                }

                texts.append(text)
                metadatas.append(metadata)
                ids.append(func_id)

        print(f"Prepared {len(texts)} documents for embedding")
        return texts, metadatas, ids

    def create_index(self) -> None:
        """Create and save the semantic index."""
        # Load function index
        index = self.load_function_index()

        # Prepare documents
        texts, metadatas, ids = self.prepare_documents(index)

        # Create embeddings
        print(f"\nGenerating embeddings (this may take a while)...")
        embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)
        print(f"Generated {len(embeddings)} embeddings")

        # Create FAISS index
        print("\nBuilding FAISS index...")
        dimension = embeddings.shape[1]
        faiss_index = faiss.IndexFlatL2(dimension)  # L2 distance (euclidean)
        faiss_index.add(embeddings.astype('float32'))
        print(f"FAISS index built with {faiss_index.ntotal} vectors")

        # Save everything
        print("\nSaving index files...")

        # Save FAISS index
        faiss_file = self.output_dir / "faiss.index"
        faiss.write_index(faiss_index, str(faiss_file))
        print(f"  Saved FAISS index: {faiss_file}")

        # Save metadatas and IDs
        metadata_file = self.output_dir / "metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump({'metadatas': metadatas, 'ids': ids}, f)
        print(f"  Saved metadata: {metadata_file}")

        # Save model name
        config_file = self.output_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump({
                'model_name': self.model_name,
                'dimension': dimension,
                'total_functions': len(ids)
            }, f, indent=2)
        print(f"  Saved config: {config_file}")

        print(f"\n✅ Successfully created semantic index for {len(ids)} functions")
        print(f"Index location: {self.output_dir}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Create semantic search index for function index'
    )
    parser.add_argument(
        '--index',
        default='data/llm_function_index.json',
        help='Path to function index JSON file'
    )
    parser.add_argument(
        '--model',
        default='all-MiniLM-L6-v2',
        help='Sentence transformer model name'
    )
    parser.add_argument(
        '--output',
        default='data/semantic_index',
        help='Output directory for semantic index'
    )

    args = parser.parse_args()

    try:
        indexer = SemanticFunctionIndexer(
            index_file=args.index,
            model_name=args.model,
            output_dir=args.output
        )
        indexer.create_index()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
