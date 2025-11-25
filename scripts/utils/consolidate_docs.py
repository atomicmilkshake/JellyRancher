#!/usr/bin/env python3
"""
Documentation Consolidation & Compression Script

Consolidates and compresses all project documentation into a single
chronologically-organized Markdown document.

Phases:
1. Documentation Collection - Scan and move docs to docs/ folder
2. Document Compression - Compress via Grok-4.1-Fast-Reasoning API
3. Consolidation - Merge into single chronological markdown file

Usage:
    python consolidate_docs.py [--dry-run] [--skip-compress] [--output FILE]
"""

import os
import sys
import json
import zlib
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.ravenmaven_client import PoeClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Configuration
# ==============================================================================

# Documentation file extensions to include
DOC_EXTENSIONS = {
    '.md', '.txt', '.rst', '.adoc', '.html', '.htm',
    '.pdf', '.docx', '.doc', '.odt', '.rtf',
    '.tex', '.wiki', '.org', '.asciidoc'
}

# Code file extensions to exclude
CODE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.go', '.rb', '.php', '.rs', '.swift', '.kt', '.kts', '.scala', '.clj',
    '.cs', '.fs', '.vb', '.lua', '.pl', '.pm', '.r', '.R', '.jl',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
    '.sql', '.graphql', '.json', '.yaml', '.yml', '.toml', '.xml',
    '.css', '.scss', '.sass', '.less', '.styl',
    '.vue', '.svelte', '.elm', '.dart', '.ex', '.exs', '.erl', '.hrl',
    '.asm', '.s', '.m', '.mm', '.f', '.f90', '.f95', '.for',
    '.coffee', '.litcoffee', '.iced', '.cson',
    '.qss'  # Qt stylesheets
}

# Files to explicitly exclude
EXCLUDED_FILES = {
    'master-prompt.md',
    'agent-journal.md'
}

# Directories to exclude from scanning
EXCLUDED_DIRS = {
    # Version control
    '.git', '.svn', '.hg', '.bzr',
    # Python caches
    '__pycache__', '.pytest_cache', '.mypy_cache',
    # Package managers / virtual environments
    'node_modules', 'venv', 'env', '.env', '.venv',
    'site-packages', 'Lib', 'lib64', 'lib',
    # IDE / editor
    '.cache', '.idea', '.vscode',
    # Build outputs
    'build', 'dist', 'target', 'out',
    # Project-specific exclusions
    'LLM_io_log', 'audit-logs', 'logs',
    'htmlcov',  # Coverage reports
    'archive',  # Archived/deprecated code
    'backups',  # Backup files
    # Package metadata directories
    'colorama', 'certifi', 'charset_normalizer', 'idna',
    'pip', 'setuptools', 'wheel', 'pkg_resources',
    # Test data that shouldn't be consolidated
    'test_lists', 'temp_file_lists', 'gui_captures',
    'data', 'metadata_cache', 'subtitle_coverage', 'subtitle_downloads',
    'test_output', 'cleanup_reports', 'reports'
}

# Compression prompt for the LLM
COMPRESSION_PROMPT = """Compress this document as losslessly as possible. Preserve all key information, technical details, and meaning while reducing length. Maintain clarity and readability.

Important guidelines:
- Keep all technical specifications, API details, configuration options
- Preserve code examples and command-line instructions
- Maintain structural hierarchy (headings, lists)
- Remove redundant explanations and verbose phrasing
- Keep critical warnings and important notes
- Condense examples while keeping their essence

Document to compress:

{content}"""

# Default model for compression
DEFAULT_MODEL = "grok-3-fast"


# ==============================================================================
# Phase 1: Documentation Collection
# ==============================================================================

def compute_file_hash(filepath: Path) -> str:
    """Compute CRC32 hash of file contents for deduplication."""
    crc = 0
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            crc = zlib.crc32(chunk, crc)
    return format(crc & 0xFFFFFFFF, '08x')


def get_file_timestamp(filepath: Path) -> datetime:
    """Get file modification timestamp."""
    return datetime.fromtimestamp(filepath.stat().st_mtime)


def is_documentation_file(filepath: Path) -> bool:
    """Check if file is a documentation file based on extension."""
    return filepath.suffix.lower() in DOC_EXTENSIONS


def is_code_file(filepath: Path) -> bool:
    """Check if file is a code file based on extension."""
    return filepath.suffix.lower() in CODE_EXTENSIONS


def should_exclude(filepath: Path, project_root: Path) -> Tuple[bool, str]:
    """
    Check if file should be excluded.
    Returns (should_exclude, reason).
    """
    # Check excluded filenames
    if filepath.name in EXCLUDED_FILES:
        return True, f"Excluded file: {filepath.name}"

    # Check if in excluded directory
    rel_parts = filepath.relative_to(project_root).parts
    for part in rel_parts[:-1]:  # Exclude filename from check
        if part in EXCLUDED_DIRS:
            return True, f"In excluded directory: {part}"

    # Check if code file
    if is_code_file(filepath):
        return True, f"Code file: {filepath.suffix}"

    return False, ""


def scan_documentation(project_root: Path) -> List[Dict]:
    """
    Scan project directory for documentation files.

    Returns list of dicts with file info:
    {
        'path': Path,
        'relative_path': str,
        'name': str,
        'extension': str,
        'timestamp': datetime,
        'hash': str,
        'size': int
    }
    """
    logger.info(f"Scanning for documentation in: {project_root}")

    doc_files = []
    seen_hashes: Dict[str, Path] = {}
    duplicates = []

    for filepath in project_root.rglob('*'):
        if not filepath.is_file():
            continue

        # Check exclusions
        exclude, reason = should_exclude(filepath, project_root)
        if exclude:
            logger.debug(f"Skipping: {filepath} - {reason}")
            continue

        # Check if documentation file
        if not is_documentation_file(filepath):
            continue

        # Compute hash for deduplication
        try:
            file_hash = compute_file_hash(filepath)
        except Exception as e:
            logger.warning(f"Could not hash {filepath}: {e}")
            continue

        # Check for duplicates
        if file_hash in seen_hashes:
            duplicates.append({
                'duplicate': filepath,
                'original': seen_hashes[file_hash]
            })
            logger.info(f"Duplicate found: {filepath.name} == {seen_hashes[file_hash].name}")
            continue

        seen_hashes[file_hash] = filepath

        # Collect file info
        try:
            doc_files.append({
                'path': filepath,
                'relative_path': str(filepath.relative_to(project_root)),
                'name': filepath.name,
                'extension': filepath.suffix,
                'timestamp': get_file_timestamp(filepath),
                'hash': file_hash,
                'size': filepath.stat().st_size
            })
        except Exception as e:
            logger.warning(f"Error processing {filepath}: {e}")

    logger.info(f"Found {len(doc_files)} documentation files, {len(duplicates)} duplicates")
    return doc_files


def move_to_docs_folder(
    doc_files: List[Dict],
    project_root: Path,
    dry_run: bool = False
) -> List[Dict]:
    """
    Move all documentation files to docs/ folder.
    Preserves relative path structure within docs/.

    Returns updated list with new paths.
    """
    docs_folder = project_root / 'docs'

    if not dry_run:
        docs_folder.mkdir(parents=True, exist_ok=True)

    updated_files = []

    for doc in doc_files:
        source_path = doc['path']

        # Skip if already in docs folder
        try:
            source_path.relative_to(docs_folder)
            logger.debug(f"Already in docs/: {source_path}")
            updated_files.append(doc)
            continue
        except ValueError:
            pass  # Not in docs folder, proceed to move

        # Determine destination path
        # Flatten structure: docs/original_filename
        dest_path = docs_folder / source_path.name

        # Handle name conflicts
        if dest_path.exists() and dest_path != source_path:
            # Add parent folder name to avoid collision
            parent_name = source_path.parent.name
            new_name = f"{parent_name}_{source_path.name}"
            dest_path = docs_folder / new_name

            # If still conflicts, add hash
            if dest_path.exists():
                hash_prefix = doc['hash'][:8]
                new_name = f"{hash_prefix}_{source_path.name}"
                dest_path = docs_folder / new_name

        if dry_run:
            logger.info(f"[DRY-RUN] Would move: {source_path} -> {dest_path}")
        else:
            try:
                shutil.move(str(source_path), str(dest_path))
                logger.info(f"Moved: {source_path.name} -> docs/{dest_path.name}")
            except Exception as e:
                logger.error(f"Failed to move {source_path}: {e}")
                continue

        # Update record with new path
        updated_doc = doc.copy()
        updated_doc['original_path'] = doc['path']
        updated_doc['path'] = dest_path
        updated_doc['relative_path'] = str(dest_path.relative_to(project_root))
        updated_files.append(updated_doc)

    return updated_files


# ==============================================================================
# Phase 2: Document Compression
# ==============================================================================

def read_document_content(filepath: Path) -> Optional[str]:
    """
    Read document content. Supports text-based formats.
    Returns None for binary formats that can't be processed.
    """
    binary_extensions = {'.pdf', '.docx', '.doc', '.odt', '.rtf'}

    if filepath.suffix.lower() in binary_extensions:
        logger.warning(f"Binary format not supported for compression: {filepath.name}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Could not read {filepath}: {e}")
            return None
    except Exception as e:
        logger.error(f"Could not read {filepath}: {e}")
        return None


def compress_document(
    client: PoeClient,
    content: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8000
) -> Optional[str]:
    """
    Compress document content using LLM.
    Returns compressed content or None on failure.
    """
    if not content or len(content.strip()) < 100:
        # Too short to compress meaningfully
        return content

    prompt = COMPRESSION_PROMPT.format(content=content)

    try:
        response = client.send_message(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=0.3  # Lower temperature for more consistent output
        )
        return response
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        return None


def compress_all_documents(
    doc_files: List[Dict],
    client: PoeClient,
    model: str = DEFAULT_MODEL,
    skip_compress: bool = False
) -> List[Dict]:
    """
    Compress all documents using LLM API.

    Returns list with 'compressed_content' added to each dict.
    """
    results = []
    total = len(doc_files)

    for idx, doc in enumerate(doc_files, 1):
        filepath = doc['path']
        logger.info(f"[{idx}/{total}] Processing: {filepath.name}")

        # Read content
        content = read_document_content(filepath)

        if content is None:
            doc['compressed_content'] = None
            doc['compression_status'] = 'unsupported_format'
            results.append(doc)
            continue

        doc['original_content'] = content
        doc['original_length'] = len(content)

        if skip_compress:
            doc['compressed_content'] = content
            doc['compression_status'] = 'skipped'
            doc['compressed_length'] = len(content)
        else:
            # Compress via API
            compressed = compress_document(client, content, model)

            if compressed:
                doc['compressed_content'] = compressed
                doc['compression_status'] = 'success'
                doc['compressed_length'] = len(compressed)

                ratio = len(compressed) / len(content) * 100
                logger.info(f"  Compressed: {len(content)} -> {len(compressed)} chars ({ratio:.1f}%)")
            else:
                # Fall back to original on compression failure
                doc['compressed_content'] = content
                doc['compression_status'] = 'failed'
                doc['compressed_length'] = len(content)
                logger.warning(f"  Compression failed, using original")

        results.append(doc)

    return results


# ==============================================================================
# Phase 3: Consolidation
# ==============================================================================

def generate_consolidated_markdown(
    doc_files: List[Dict],
    project_root: Path,
    output_path: Path
) -> None:
    """
    Generate consolidated markdown file with all compressed documentation.
    Documents are sorted chronologically (oldest first).
    """
    # Sort by timestamp (oldest first)
    sorted_docs = sorted(doc_files, key=lambda x: x['timestamp'])

    lines = []
    lines.append("# Consolidated Project Documentation")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    lines.append(f"*Total Documents: {len(sorted_docs)}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for idx, doc in enumerate(sorted_docs, 1):
        anchor = doc['name'].lower().replace(' ', '-').replace('.', '')
        lines.append(f"{idx}. [{doc['relative_path']}](#{anchor})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Document sections
    for doc in sorted_docs:
        content = doc.get('compressed_content')

        if content is None:
            content = f"*[Binary file - {doc['extension']} format not supported for text extraction]*"

        # Section header
        lines.append(f"# {doc['relative_path']}")
        lines.append("")

        # Metadata
        lines.append(f"**Original Date:** {doc['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        if 'original_length' in doc and 'compressed_length' in doc:
            orig = doc['original_length']
            comp = doc['compressed_length']
            ratio = comp / orig * 100 if orig > 0 else 100
            lines.append(f"**Compression:** {orig:,} -> {comp:,} chars ({ratio:.1f}%)")
            lines.append("")

        lines.append(f"**Status:** {doc.get('compression_status', 'unknown')}")
        lines.append("")

        # Content
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    # Write output
    output_content = '\n'.join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_content)

    logger.info(f"Consolidated documentation written to: {output_path}")
    logger.info(f"Total size: {len(output_content):,} characters")


def save_metadata(doc_files: List[Dict], output_path: Path) -> None:
    """Save processing metadata to JSON for reference."""
    metadata = []

    for doc in doc_files:
        entry = {
            'name': doc['name'],
            'relative_path': doc['relative_path'],
            'original_path': str(doc.get('original_path', doc['path'])),
            'timestamp': doc['timestamp'].isoformat(),
            'hash': doc['hash'],
            'size': doc['size'],
            'compression_status': doc.get('compression_status', 'unknown'),
            'original_length': doc.get('original_length'),
            'compressed_length': doc.get('compressed_length')
        }
        metadata.append(entry)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Metadata saved to: {output_path}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Consolidate and compress project documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Full run with compression
    python consolidate_docs.py

    # Dry run to see what would be collected
    python consolidate_docs.py --dry-run

    # Skip compression (just collect and consolidate)
    python consolidate_docs.py --skip-compress

    # Use specific model for compression
    python consolidate_docs.py --model grok-3-fast

    # Custom output file
    python consolidate_docs.py --output my-docs.md
        """
    )

    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview operations without making changes'
    )
    parser.add_argument(
        '--skip-compress', action='store_true',
        help='Skip LLM compression phase (collect and consolidate only)'
    )
    parser.add_argument(
        '--skip-move', action='store_true',
        help='Skip moving files to docs/ folder'
    )
    parser.add_argument(
        '--model', default=DEFAULT_MODEL,
        help=f'LLM model for compression (default: {DEFAULT_MODEL})'
    )
    parser.add_argument(
        '--output', '-o', default='consolidated-docs.md',
        help='Output file path (default: consolidated-docs.md)'
    )
    parser.add_argument(
        '--project-root', '-p', type=Path,
        help='Project root directory (default: auto-detect)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine project root
    if args.project_root:
        project_root = args.project_root.resolve()
    else:
        # Auto-detect: go up from script location until we find .git or common markers
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / '.git').exists() or (current / 'launch_gui.py').exists():
                project_root = current
                break
            current = current.parent
        else:
            project_root = Path.cwd()

    logger.info(f"Project root: {project_root}")

    # Phase 1: Documentation Collection
    logger.info("=" * 60)
    logger.info("PHASE 1: Documentation Collection")
    logger.info("=" * 60)

    doc_files = scan_documentation(project_root)

    if not doc_files:
        logger.error("No documentation files found!")
        return 1

    # Move to docs folder (unless skipped)
    if not args.skip_move:
        doc_files = move_to_docs_folder(doc_files, project_root, dry_run=args.dry_run)

    if args.dry_run:
        logger.info("\n[DRY-RUN] Would process the following files:")
        for doc in sorted(doc_files, key=lambda x: x['timestamp']):
            logger.info(f"  - {doc['relative_path']} ({doc['timestamp'].strftime('%Y-%m-%d')})")
        return 0

    # Phase 2: Document Compression
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 2: Document Compression")
    logger.info("=" * 60)

    if args.skip_compress:
        logger.info("Compression skipped (--skip-compress)")
        # Still need to read content
        for doc in doc_files:
            content = read_document_content(doc['path'])
            doc['compressed_content'] = content
            doc['original_content'] = content
            doc['original_length'] = len(content) if content else 0
            doc['compressed_length'] = len(content) if content else 0
            doc['compression_status'] = 'skipped'
    else:
        # Initialize Poe client
        try:
            client = PoeClient(
                timeout=1800,  # 30 minute timeout for large documents
                logger=logger
            )
            logger.info(f"Using model: {args.model}")
        except ValueError as e:
            logger.error(f"Failed to initialize API client: {e}")
            logger.error("Set OPENAI_API_KEY environment variable or provide --api-key")
            return 1

        doc_files = compress_all_documents(
            doc_files, client, model=args.model
        )

    # Phase 3: Consolidation
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 3: Consolidation")
    logger.info("=" * 60)

    output_path = project_root / args.output
    generate_consolidated_markdown(doc_files, project_root, output_path)

    # Save metadata
    metadata_path = output_path.with_suffix('.meta.json')
    save_metadata(doc_files, metadata_path)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("COMPLETE")
    logger.info("=" * 60)

    total_original = sum(d.get('original_length', 0) or 0 for d in doc_files)
    total_compressed = sum(d.get('compressed_length', 0) or 0 for d in doc_files)

    logger.info(f"Documents processed: {len(doc_files)}")
    logger.info(f"Original total: {total_original:,} characters")
    logger.info(f"Compressed total: {total_compressed:,} characters")

    if total_original > 0:
        ratio = total_compressed / total_original * 100
        logger.info(f"Overall compression: {ratio:.1f}%")

    logger.info(f"Output: {output_path}")
    logger.info(f"Metadata: {metadata_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
