#!/usr/bin/env python3
"""
Generate Enhanced Docstrings Using Existing Batch Processing System

Leverages the existing RavenMaven batch processing infrastructure:
- PoeClient for LLM API calls
- Dynamic chunking based on token limits
- Progress tracking and error handling
- Results caching

Simple workflow:
1. Load function index
2. Extract actual function code from source files
3. Create batches with custom docstring generation prompt
4. Process through PoeClient
5. Parse JSON responses and update function index
6. Store in ChromaDB
"""

import sys
import json
import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts" / "core"))
sys.path.insert(0, str(Path(__file__).parent / "scripts" / "ai"))

from ravenmaven_client import PoeClient
from chroma_memory_backend import ChromaMemoryBackend


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_function_code(file_path: str, function_name: str, line_number: int) -> Optional[str]:
    """
    Extract complete function code from source file.

    Args:
        file_path: Path to source file
        function_name: Name of function to extract
        line_number: Line number where function starts

    Returns:
        Complete function code as string, or None if extraction fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=file_path)

        # Find the function node
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name and node.lineno == line_number:
                return ast.unparse(node)

        # Fallback: extract by line number
        lines = content.split('\n')
        if line_number > 0 and line_number <= len(lines):
            start_idx = line_number - 1
            indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

            end_idx = start_idx + 1
            while end_idx < len(lines):
                line = lines[end_idx]
                if line.strip() == '' or line.strip().startswith('#'):
                    end_idx += 1
                    continue
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= indent and line.strip():
                    break
                end_idx += 1

            return '\n'.join(lines[start_idx:end_idx])

        return None

    except Exception as e:
        logger.error(f"Failed to extract {function_name} from {file_path}: {e}")
        return None


def create_docstring_prompt(functions: List[Dict[str, Any]]) -> str:
    """
    Create prompt for generating docstrings for a batch of functions.

    Args:
        functions: List of function dictionaries with code

    Returns:
        Formatted prompt for LLM
    """
    prompt = """You are a Python documentation expert. Analyze the following functions from the JellyRancher media organization application and write comprehensive docstrings.

**Requirements:**
- Use Google-style docstring format
- Explain WHAT the function does, WHY it exists, and HOW it works
- Document all parameters with types and descriptions
- Document return values
- Note any exceptions, side effects, or important behaviors
- Be detailed but concise

**Output Format:**
Return a JSON array with one object per function:
```json
[
  {
    "function_name": "exact_function_name",
    "file": "path/to/file.py",
    "docstring": "Complete docstring text here (without triple quotes)"
  }
]
```

**Functions to Document:**

"""

    for idx, func in enumerate(functions, 1):
        prompt += f"\n{'='*70}\n"
        prompt += f"FUNCTION {idx}/{len(functions)}\n"
        prompt += f"{'='*70}\n"
        prompt += f"File: {func['file']}\n"
        prompt += f"Name: {func['name']}\n"
        prompt += f"Current Docstring: {func.get('docstring', 'None')}\n\n"
        prompt += f"COMPLETE CODE:\n```python\n{func['code']}\n```\n"

    prompt += f"\n{'='*70}\n"
    prompt += "Return ONLY the JSON array. Ensure valid JSON with proper escaping.\n"

    return prompt


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
    return len(text) // 4


def chunk_functions(functions: List[Dict[str, Any]], max_functions_per_chunk: int = 15) -> List[List[Dict]]:
    """
    Chunk functions into smaller batches for reliable API processing.

    Args:
        functions: List of function dictionaries with code
        max_functions_per_chunk: Maximum functions per batch (default: 15 for reliability)

    Returns:
        List of function batches
    """
    # Simple chunking by function count for reliability
    chunks = []
    for i in range(0, len(functions), max_functions_per_chunk):
        chunk = functions[i:i + max_functions_per_chunk]
        chunk_tokens = sum(estimate_tokens(f"{f['name']}\n{f['file']}\n{f.get('code', '')}") for f in chunk)
        chunks.append(chunk)
        logger.info(f"Created chunk {len(chunks)} with {len(chunk)} functions (~{chunk_tokens} tokens)")

    return chunks


def process_batch(client: PoeClient, batch: List[Dict], batch_num: int, total_batches: int) -> List[Dict]:
    """
    Process a batch of functions through LLM.

    Args:
        client: PoeClient instance
        batch: List of function dictionaries
        batch_num: Current batch number
        total_batches: Total number of batches

    Returns:
        List of functions with enhanced docstrings
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Processing Batch {batch_num}/{total_batches} ({len(batch)} functions)")
    logger.info(f"{'='*70}")

    # Create prompt
    prompt = create_docstring_prompt(batch)
    prompt_tokens = estimate_tokens(prompt)
    logger.info(f"Prompt size: ~{prompt_tokens} tokens")

    try:
        # Send to LLM
        logger.info("Sending to LLM...")
        response = client.send_message(
            prompt,
            max_tokens=8000,  # Enough for detailed docstrings
            temperature=0.3   # Lower temperature for consistent output
        )

        # Parse JSON response
        logger.info("Parsing response...")
        json_start = response.find('[')
        json_end = response.rfind(']') + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON array found in response")

        json_str = response[json_start:json_end]
        enhanced = json.loads(json_str)

        # Merge enhanced docstrings with original function data
        results = []
        for i, func in enumerate(batch):
            if i < len(enhanced):
                func['enhanced_docstring'] = enhanced[i].get('docstring', func.get('docstring', ''))
                func['docstring_generated'] = True
                func['generation_timestamp'] = datetime.now().isoformat()
            else:
                func['enhanced_docstring'] = func.get('docstring', '')
                func['docstring_generated'] = False

            results.append(func)

        logger.info(f"✓ Successfully processed {len(results)} functions")
        return results

    except Exception as e:
        logger.error(f"✗ Failed to process batch {batch_num}: {e}")

        # Return batch with original docstrings
        for func in batch:
            func['enhanced_docstring'] = func.get('docstring', '')
            func['docstring_generated'] = False
            func['generation_error'] = str(e)

        return batch


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate enhanced docstrings using existing batch processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with first 10 functions
  python generate_docstrings_batch.py --limit 10

  # Process all functions
  python generate_docstrings_batch.py

  # Use specific model
  python generate_docstrings_batch.py --model GPT-4o

  # Skip ChromaDB storage
  python generate_docstrings_batch.py --no-chromadb
        """
    )

    parser.add_argument('--limit', type=int, help='Limit to first N functions (for testing)')
    parser.add_argument('--model', default='Claude-Sonnet-4.5', help='Model to use')
    parser.add_argument('--output', default='enhanced_function_index.json', help='Output file')
    parser.add_argument('--no-chromadb', action='store_true', help='Skip ChromaDB storage')

    args = parser.parse_args()

    # Initialize PoeClient
    logger.info("Initializing PoeClient...")
    client = PoeClient(default_model=args.model, timeout=1800)

    # Load function index
    logger.info("Loading function index...")
    with open('function_index.json', 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    total_functions = index_data['metadata']['total_functions']
    logger.info(f"Loaded {total_functions} functions from {index_data['metadata']['total_files']} files")

    # Extract function code
    logger.info("Extracting function code...")
    all_functions = []

    for file_path, functions in index_data['functions'].items():
        for func in functions:
            code = extract_function_code(file_path, func['name'], func['line'])

            if code:
                func['code'] = code
                func['file'] = file_path
                all_functions.append(func)

                # Limit if requested
                if args.limit and len(all_functions) >= args.limit:
                    break

        if args.limit and len(all_functions) >= args.limit:
            break

    logger.info(f"Extracted code for {len(all_functions)} functions")

    # Create chunks
    logger.info("Creating batches...")
    chunks = chunk_functions(all_functions)
    logger.info(f"Created {len(chunks)} batches")

    # Process batches
    logger.info(f"\n{'='*70}")
    logger.info(f"STARTING BATCH PROCESSING")
    logger.info(f"{'='*70}\n")

    enhanced_functions = []
    stats = {'processed': 0, 'failed': 0}

    for i, chunk in enumerate(chunks, 1):
        results = process_batch(client, chunk, i, len(chunks))
        enhanced_functions.extend(results)

        # Update stats
        stats['processed'] += sum(1 for f in results if f.get('docstring_generated', False))
        stats['failed'] += sum(1 for f in results if not f.get('docstring_generated', False))

    # Save results
    logger.info(f"\n{'='*70}")
    logger.info("Saving results...")

    # Organize by file
    functions_by_file = {}
    for func in enhanced_functions:
        file_path = func['file']
        if file_path not in functions_by_file:
            functions_by_file[file_path] = []
        functions_by_file[file_path].append(func)

    enhanced_index = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_files": len(functions_by_file),
            "total_functions": len(enhanced_functions),
            "docstrings_generated": stats['processed'],
            "docstrings_failed": stats['failed'],
            "model": args.model,
            "source": "Batch processing with PoeClient"
        },
        "functions": functions_by_file
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(enhanced_index, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Saved to {args.output}")

    # Store in ChromaDB
    if not args.no_chromadb:
        logger.info("Storing in ChromaDB...")
        mem = ChromaMemoryBackend('./chroma_db')

        # Store master document
        doc_content = f"""# Enhanced Function Index (LLM-Generated Docstrings)
Generated: {enhanced_index['metadata']['generated']}
Model: {enhanced_index['metadata']['model']}
Total Functions: {enhanced_index['metadata']['total_functions']}
Docstrings Generated: {enhanced_index['metadata']['docstrings_generated']}
Failed: {enhanced_index['metadata']['docstrings_failed']}

This index contains LLM-generated comprehensive docstrings for JellyRancher functions.
"""

        memory_id = mem.add_memory(
            content=doc_content,
            user_id='docstring_generator',
            metadata={
                'type': 'enhanced_function_index',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_functions': enhanced_index['metadata']['total_functions'],
                'docstrings_generated': enhanced_index['metadata']['docstrings_generated'],
                'model': args.model,
                'tags': 'enhanced_docstrings,llm_generated,function_index'
            }
        )

        logger.info(f"✓ Stored in ChromaDB (ID: {memory_id})")

        # Store individual functions
        functions_stored = 0
        for file_path, functions in functions_by_file.items():
            for func in functions:
                if not func.get('docstring_generated', False):
                    continue

                func_content = f"""# Function: {func['name']}

File: {file_path}
Line: {func['line']}

## Enhanced Documentation
{func.get('enhanced_docstring', 'No documentation')}
"""

                mem.add_memory(
                    content=func_content,
                    user_id='docstring_generator',
                    metadata={
                        'type': 'enhanced_function',
                        'function_name': func['name'],
                        'file': file_path,
                        'tags': f"enhanced_docstring,{func['name']}"
                    }
                )
                functions_stored += 1

        logger.info(f"✓ Stored {functions_stored} individual functions in ChromaDB")

    # Final summary
    print(f"\n{'='*70}")
    print("DOCSTRING GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total Functions: {len(enhanced_functions)}")
    print(f"Docstrings Generated: {stats['processed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {100 * stats['processed'] / len(enhanced_functions):.1f}%")
    print(f"Output: {args.output}")
    if not args.no_chromadb:
        print(f"ChromaDB: Enhanced docstrings stored")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
