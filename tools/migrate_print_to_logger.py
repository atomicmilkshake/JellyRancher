"""
Automated print() → logger migration script.

Phase 48-B: Migrates print statements to proper logging calls per Commandment 12.

Usage:
    python tools/migrate_print_to_logger.py --dry-run    # Preview changes
    python tools/migrate_print_to_logger.py              # Apply changes
    python tools/migrate_print_to_logger.py --report     # Just count prints

Handles:
- Pattern-based replacement (error/warn/debug/info classification)
- Automatic logger setup injection if missing
- Preserves f-strings and formatting
- Skips _archived/ directory
- Reports changes made
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass, field


@dataclass
class MigrationResult:
    """Result of migrating a single file."""
    filepath: Path
    original_prints: int = 0
    migrated_prints: int = 0
    logger_added: bool = False
    changes: List[Tuple[int, str, str]] = field(default_factory=list)  # (line_num, before, after)


# Pattern classifications: (regex_pattern, logger_level, cleanup_pattern)
# cleanup_pattern removes the prefix when converting to logger
PATTERNS = [
    # Error patterns → logger.error()
    (r'print\(f?"?\[FAIL\]\s*', 'error', r'\[FAIL\]\s*'),
    (r'print\(f?"?\[ERROR\]\s*', 'error', r'\[ERROR\]\s*'),
    (r'print\(f?"?Error:\s*', 'error', r'Error:\s*'),
    (r'print\(f?"?ERROR:\s*', 'error', r'ERROR:\s*'),
    (r'print\(f?"?❌\s*', 'error', r'❌\s*'),
    (r'print\(f?"?✗\s*', 'error', r'✗\s*'),
    (r'print\(f?"?Failed', 'error', None),

    # Warning patterns → logger.warning()
    (r'print\(f?"?\[WARN\]\s*', 'warning', r'\[WARN\]\s*'),
    (r'print\(f?"?\[WARNING\]\s*', 'warning', r'\[WARNING\]\s*'),
    (r'print\(f?"?Warning:\s*', 'warning', r'Warning:\s*'),
    (r'print\(f?"?⚠️\s*', 'warning', r'⚠️\s*'),
    (r'print\(f?"?⚠\s*', 'warning', r'⚠\s*'),

    # Debug patterns → logger.debug()
    (r'print\(f?"?DEBUG:\s*', 'debug', r'DEBUG:\s*'),
    (r'print\(f?"?\[DEBUG\]\s*', 'debug', r'\[DEBUG\]\s*'),
    (r'print\(f?"?WORKER DEBUG:\s*', 'debug', r'WORKER DEBUG:\s*'),

    # Success/Info patterns → logger.info()
    (r'print\(f?"?\[OK\]\s*', 'info', r'\[OK\]\s*'),
    (r'print\(f?"?\[INFO\]\s*', 'info', r'\[INFO\]\s*'),
    (r'print\(f?"?✓\s*', 'info', r'✓\s*'),
    (r'print\(f?"?✔\s*', 'info', r'✔\s*'),
    (r'print\(f?"?Successfully\s*', 'info', r'Successfully\s*'),
    (r'print\(f?"?Running\s*', 'info', None),
    (r'print\(f?"?Starting\s*', 'info', None),
    (r'print\(f?"?Completed\s*', 'info', None),
    (r'print\(f?"?Processing\s*', 'info', None),
]

# Logger setup to inject if missing
LOGGER_SETUP = """import logging
logger = logging.getLogger(__name__)
"""

LOGGER_SETUP_MINIMAL = "logger = logging.getLogger(__name__)"


def count_prints_in_file(filepath: Path) -> int:
    """Count print() calls in a file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        # Match print( but not things like blueprint( or sprint(
        matches = re.findall(r'(?<![a-zA-Z_])print\s*\(', content)
        return len(matches)
    except Exception:
        return 0


def classify_print(line: str) -> Tuple[str, str]:
    """
    Classify a print statement and return (level, cleaned_content).
    Returns ('unknown', line) if no pattern matches.
    """
    for pattern, level, cleanup in PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            if cleanup:
                # Remove the prefix pattern from the string content
                cleaned = re.sub(cleanup, '', line, count=1, flags=re.IGNORECASE)
                return (level, cleaned)
            return (level, line)
    return ('unknown', line)


def convert_print_to_logger(line: str, level: str) -> str:
    """Convert a print() call to logger.level() call."""
    # Extract the content inside print()
    # Handle: print(f"..."), print("..."), print(f'...'), print('...')

    # First, replace 'print(' with 'logger.level('
    # This is a simple approach that works for most cases

    # Match print with optional whitespace
    match = re.match(r'^(\s*)print\s*\(', line)
    if not match:
        return line

    indent = match.group(1)
    rest = line[len(match.group(0)):]

    # The rest should be the content ending with )
    # Handle potential trailing comment
    new_line = f"{indent}logger.{level}({rest}"

    return new_line


def has_logger_setup(content: str) -> bool:
    """Check if file already has logger setup."""
    return 'logger = logging.getLogger' in content or 'logger=logging.getLogger' in content


def has_logging_import(content: str) -> bool:
    """Check if file imports logging."""
    return 'import logging' in content


def find_import_section_end(lines: List[str]) -> int:
    """Find the line number after the import section."""
    last_import = 0
    in_multiline_import = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track multiline imports (from x import (\n...\n))
        if '(' in stripped and 'import' in stripped and ')' not in stripped:
            in_multiline_import = True
        if in_multiline_import:
            if ')' in stripped:
                in_multiline_import = False
                last_import = i
            continue

        # Regular imports
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import = i
        # Skip docstrings and comments at top
        elif stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        elif stripped.startswith('#'):
            continue
        elif stripped == '':
            continue
        elif last_import > 0:
            # We've passed the import section
            break

    return last_import + 1


def inject_logger_setup(content: str) -> str:
    """Inject logger setup after imports."""
    lines = content.split('\n')
    insert_pos = find_import_section_end(lines)

    if has_logging_import(content):
        # Just add the logger line
        lines.insert(insert_pos, '')
        lines.insert(insert_pos + 1, LOGGER_SETUP_MINIMAL)
    else:
        # Add both import and logger
        lines.insert(insert_pos, '')
        lines.insert(insert_pos + 1, LOGGER_SETUP.strip())

    return '\n'.join(lines)


def should_skip_print_line(line: str) -> bool:
    """Check if this print line should be skipped (not migrated)."""
    stripped = line.strip()

    # Skip comments
    if stripped.startswith('#'):
        return True

    # Skip Rich console.print - these are for UI formatting
    if 'console.print' in line:
        return True

    # Skip if it's in a lambda (common pattern for callbacks)
    if 'lambda' in line and 'print' in line:
        return True

    # Skip table formatting prints (decorative)
    if re.search(r'print\s*\(\s*["\'][-=*]{10,}', line):
        return True

    return False


def migrate_file(filepath: Path, dry_run: bool = True) -> MigrationResult:
    """Migrate print statements in a single file."""
    result = MigrationResult(filepath=filepath)

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return result

    original_content = content
    lines = content.split('\n')
    new_lines = []

    for line_num, line in enumerate(lines, 1):
        # Check if line has a print statement (not in comment, not part of word)
        if re.search(r'(?<![a-zA-Z_])print\s*\(', line):
            # Check if we should skip this line
            if should_skip_print_line(line):
                new_lines.append(line)
                continue

            result.original_prints += 1

            # Classify and potentially convert
            level, _ = classify_print(line)

            if level != 'unknown':
                new_line = convert_print_to_logger(line, level)
                result.migrated_prints += 1
                result.changes.append((line_num, line.strip(), new_line.strip()))
                new_lines.append(new_line)
            else:
                # Unclassified print - convert to logger.info by default
                new_line = convert_print_to_logger(line, 'info')
                result.migrated_prints += 1
                result.changes.append((line_num, line.strip(), new_line.strip()))
                new_lines.append(new_line)
        else:
            new_lines.append(line)

    new_content = '\n'.join(new_lines)

    # If we made changes and file doesn't have logger, inject it
    if result.migrated_prints > 0 and not has_logger_setup(new_content):
        new_content = inject_logger_setup(new_content)
        result.logger_added = True

    # Write if not dry run and content changed
    if not dry_run and new_content != original_content:
        filepath.write_text(new_content, encoding='utf-8')

    return result


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    path_str = str(filepath)

    # Skip archived code
    if '_archived' in path_str:
        return True

    # Skip test files (they may have intentional prints)
    if '/tests/' in path_str or '\\tests\\' in path_str:
        return True

    # Skip this script
    if 'migrate_print_to_logger' in path_str:
        return True

    return False


def generate_report(scripts_dir: Path) -> Dict[str, int]:
    """Generate report of print statements by file."""
    report = {}

    for py_file in scripts_dir.rglob('*.py'):
        if should_skip_file(py_file):
            continue

        count = count_prints_in_file(py_file)
        if count > 0:
            relative_path = py_file.relative_to(scripts_dir.parent)
            report[str(relative_path)] = count

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Migrate print() to logger calls')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without writing')
    parser.add_argument('--report', action='store_true',
                        help='Just count and report print statements')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed changes')
    parser.add_argument('--path', type=Path, default=Path('scripts'),
                        help='Directory to scan (default: scripts)')

    args = parser.parse_args()

    scripts_dir = args.path
    if not scripts_dir.exists():
        print(f"Error: Directory {scripts_dir} does not exist")
        sys.exit(1)

    if args.report:
        print("\n=== Print Statement Report ===\n")
        report = generate_report(scripts_dir)

        # Sort by count descending
        sorted_report = sorted(report.items(), key=lambda x: x[1], reverse=True)

        total = 0
        for filepath, count in sorted_report:
            print(f"  {count:4d}  {filepath}")
            total += count

        print(f"\n  Total: {total} print statements in {len(report)} files")
        return

    print(f"\n=== Print to Logger Migration {'(DRY RUN)' if args.dry_run else ''} ===\n")

    results = []
    for py_file in scripts_dir.rglob('*.py'):
        if should_skip_file(py_file):
            continue

        result = migrate_file(py_file, dry_run=args.dry_run)
        if result.original_prints > 0:
            results.append(result)

    # Summary
    total_original = sum(r.original_prints for r in results)
    total_migrated = sum(r.migrated_prints for r in results)
    total_logger_added = sum(1 for r in results if r.logger_added)

    print(f"Files processed: {len(results)}")
    print(f"Print statements found: {total_original}")
    print(f"Print statements migrated: {total_migrated}")
    print(f"Logger setups added: {total_logger_added}")

    if args.verbose or args.dry_run:
        print("\n=== Changes by File ===\n")
        for result in results:
            if result.changes:
                rel_path = result.filepath.relative_to(scripts_dir.parent)
                print(f"\n{rel_path}:")
                for line_num, before, after in result.changes[:5]:  # Show first 5
                    # Handle unicode safely for Windows console
                    before_safe = before[:60].encode('ascii', 'replace').decode('ascii')
                    after_safe = after[:60].encode('ascii', 'replace').decode('ascii')
                    print(f"  L{line_num}: {before_safe}...")
                    print(f"      -> {after_safe}...")
                if len(result.changes) > 5:
                    print(f"  ... and {len(result.changes) - 5} more")

    if args.dry_run:
        print("\n(Dry run - no files were modified)")
    else:
        print(f"\nMigration complete. {len(results)} files modified.")


if __name__ == '__main__':
    main()
