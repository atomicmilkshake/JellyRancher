#!/usr/bin/env python3
"""
Ingest llm_function_index.json into ChromaDB for semantic search capabilities.

This script loads the function index and creates a ChromaDB collection with
embeddings for semantic search of functions by description, implementation,
and capabilities.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import chromadb


class FunctionIndexIngester:
    """Ingests function index into ChromaDB."""

    def __init__(
        self,
        index_file: str = "data/llm_function_index.json",
        chroma_dir: str = "chroma_db",
        collection_name: str = "function_index"
    ):
        """
        Initialize the ingester.

        Args:
            index_file: Path to the llm_function_index.json file
            chroma_dir: Directory to store ChromaDB data
            collection_name: Name of the ChromaDB collection
        """
        self.index_file = Path(index_file)
        self.chroma_dir = Path(chroma_dir)
        self.collection_name = collection_name

        if not self.index_file.exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=str(self.chroma_dir))

        print(f"ChromaDB initialized at: {self.chroma_dir}")

    def load_function_index(self) -> Dict[str, Any]:
        """Load the function index from JSON file."""
        print(f"Loading function index from: {self.index_file}")
        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        functions = index.get('functions', {})
        total_functions = sum(len(funcs) for funcs in functions.values())
        print(f"Loaded {total_functions} functions from {len(functions)} files")

        return index

    def prepare_documents(self, index: Dict[str, Any]) -> tuple[List[str], List[Dict], List[str]]:
        """
        Prepare documents for ChromaDB ingestion.

        Returns:
            tuple of (documents, metadatas, ids)
            - documents: List of text content for embedding
            - metadatas: List of metadata dicts for each function
            - ids: List of unique IDs for each function
        """
        documents = []
        metadatas = []
        ids = []

        functions = index.get('functions', {})

        for file_path, funcs in functions.items():
            for func in funcs:
                # Create unique ID: file_path:line_number:function_name
                func_id = f"{file_path}:{func.get('line', 0)}:{func['name']}"

                # Build searchable text from multiple fields
                text_parts = []

                # Function name (weighted heavily)
                text_parts.append(f"Function: {func['name']}")

                # Description (what it does)
                if func.get('description'):
                    text_parts.append(f"Description: {func['description']}")

                # Implementation (how it works)
                if func.get('implementation'):
                    text_parts.append(f"Implementation: {func['implementation']}")

                # Parameters
                inputs = func.get('inputs', {})
                if isinstance(inputs, dict) and inputs.get('parameters'):
                    params = inputs['parameters']
                    if isinstance(params, list):
                        param_texts = []
                        for p in params:
                            if isinstance(p, dict):
                                param_texts.append(f"{p.get('name', '')}:{p.get('type', 'Any')}")
                        if param_texts:
                            param_text = "Parameters: " + ", ".join(param_texts)
                            text_parts.append(param_text)

                # Return type
                outputs = func.get('outputs', {})
                if isinstance(outputs, dict) and outputs.get('return_value'):
                    ret = outputs['return_value']
                    if isinstance(ret, dict):
                        text_parts.append(f"Returns: {ret.get('type', 'Any')}")

                # Notes
                notes = func.get('notes')
                if isinstance(notes, list):
                    note_strings = [n for n in notes if isinstance(n, str)]
                    if note_strings:
                        notes_text = "Notes: " + " ".join(note_strings)
                        text_parts.append(notes_text)

                # Usage example
                if func.get('usage_example'):
                    text_parts.append(f"Example: {func['usage_example']}")

                # Combine all text
                document = "\n\n".join(text_parts)

                # Create metadata (for filtering and display)
                # Check if inputs has parameters
                has_params = False
                func_inputs = func.get('inputs', {})
                if isinstance(func_inputs, dict):
                    has_params = bool(func_inputs.get('parameters'))

                # Create short description
                desc = func.get('description', '')
                desc_short = desc[:200] + '...' if len(desc) > 200 else desc

                metadata = {
                    'name': func['name'],
                    'file_path': file_path,
                    'line': func.get('line', 0),
                    'class_name': func.get('class_name', ''),
                    'has_description': bool(desc),
                    'has_implementation': bool(func.get('implementation')),
                    'has_parameters': has_params,
                    'has_example': bool(func.get('usage_example')),
                    'description_short': desc_short,
                }

                documents.append(document)
                metadatas.append(metadata)
                ids.append(func_id)

        print(f"Prepared {len(documents)} documents for ingestion")
        return documents, metadatas, ids

    def ingest(self, reset: bool = False) -> None:
        """
        Ingest the function index into ChromaDB.

        Args:
            reset: If True, delete existing collection before ingesting
        """
        # Load index
        index = self.load_function_index()

        # Get or create collection
        if reset:
            print(f"Resetting collection: {self.collection_name}")
            try:
                self.client.delete_collection(name=self.collection_name)
            except Exception as e:
                print(f"Note: Could not delete collection (may not exist): {e}")

        print(f"Creating collection: {self.collection_name}")

        # Use sentence-transformers embedding function
        from chromadb.utils import embedding_functions
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=sentence_transformer_ef,
            metadata={"description": "Function index with semantic search capabilities"}
        )

        # Prepare documents
        documents, metadatas, ids = self.prepare_documents(index)

        # Ingest in batches (ChromaDB has limits)
        batch_size = 500
        total_batches = (len(documents) + batch_size - 1) // batch_size

        print(f"Ingesting {len(documents)} functions in {total_batches} batches...")

        for i in range(0, len(documents), batch_size):
            batch_num = i // batch_size + 1
            end_idx = min(i + batch_size, len(documents))

            batch_docs = documents[i:end_idx]
            batch_metas = metadatas[i:end_idx]
            batch_ids = ids[i:end_idx]

            print(f"  Batch {batch_num}/{total_batches}: {len(batch_docs)} functions")

            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )

        print(f"\n✅ Successfully ingested {len(documents)} functions into ChromaDB")
        print(f"Collection: {self.collection_name}")
        print(f"Database location: {self.chroma_dir}")

    def get_stats(self) -> None:
        """Print statistics about the ChromaDB collection."""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            count = collection.count()

            print(f"\n📊 ChromaDB Collection Stats:")
            print(f"  Collection: {self.collection_name}")
            print(f"  Total functions: {count}")
            print(f"  Database location: {self.chroma_dir}")

        except Exception as e:
            print(f"Error getting stats: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Ingest function index into ChromaDB for semantic search'
    )
    parser.add_argument(
        '--index',
        default='data/llm_function_index.json',
        help='Path to function index JSON file'
    )
    parser.add_argument(
        '--chroma-dir',
        default='chroma_db',
        help='Directory to store ChromaDB data'
    )
    parser.add_argument(
        '--collection',
        default='function_index',
        help='Name of ChromaDB collection'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset/delete existing collection before ingesting'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Only show statistics, do not ingest'
    )

    args = parser.parse_args()

    try:
        ingester = FunctionIndexIngester(
            index_file=args.index,
            chroma_dir=args.chroma_dir,
            collection_name=args.collection
        )

        if args.stats:
            ingester.get_stats()
        else:
            ingester.ingest(reset=args.reset)
            ingester.get_stats()

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
