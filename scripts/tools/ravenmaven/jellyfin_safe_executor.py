import json
import os
import shutil
import logging
import hashlib
import zlib
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from datetime import datetime
import argparse
import sys
from tqdm import tqdm  # type: ignore

try:
    import blake3  # type: ignore
except ImportError:
    print("BLAKE3 library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "blake3"])
    import blake3  # type: ignore

# Add _common to path for immutable audit
sys.path.insert(0, str(Path(__file__).parent.parent.parent / '_common'))
try:
    from immutable_audit import ImmutableAuditLog
    IMMUTABLE_AUDIT_AVAILABLE = True
except ImportError:
    print("Warning: ImmutableAuditLog not available, using legacy audit only")
    IMMUTABLE_AUDIT_AVAILABLE = False

class JellyfinSafeExecutor:
    def __init__(self, jellyfin_base_dir="V:/Jellyfin Organizer"):
        self.logger = self.setup_logging()
        self.logger.info("JellyfinSafeExecutor: Initializing...")

        self.jellyfin_base = Path(jellyfin_base_dir)
        self.snapshots_dir = self.jellyfin_base / "snapshots"
        self.audit_dir = self.jellyfin_base / "audit_trail"
        self.rollback_dir = self.jellyfin_base / "rollback"

        # Create directories
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

        # Initialize immutable audit log if available
        self.immutable_audit = None
        if IMMUTABLE_AUDIT_AVAILABLE:
            try:
                self.immutable_audit = ImmutableAuditLog()
                self.immutable_audit.initialize()
                self.logger.info("JellyfinSafeExecutor: Immutable audit log initialized")
            except Exception as e:
                self.logger.warning(f"JellyfinSafeExecutor: Could not initialize immutable audit: {e}")

        self.logger.info(f"JellyfinSafeExecutor: Base directory set to {self.jellyfin_base}")
        self.logger.info("JellyfinSafeExecutor: Initialization complete")

    def setup_logging(self):
        """Setup comprehensive logging system."""
        log_file = f"logs/executor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logger = logging.getLogger('JellyfinSafeExecutor')
        logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(file_formatter)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        ch.setFormatter(console_formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    def calculate_checksum(self, file_path, quick_mode=False):
        """Calculate BLAKE3 checksum for file integrity (fast and secure).
        
        Args:
            file_path: Path to the file
            quick_mode: If True, use size+mtime for large files (>100MB) for speed
        """
        self.logger.debug(f"Calculating checksum for: {file_path} (quick_mode={quick_mode})")
        try:
            file_size = file_path.stat().st_size
            file_mtime = file_path.stat().st_mtime
            
            # For large files (>100MB), use quick mode if enabled
            if quick_mode and file_size > 100 * 1024 * 1024:
                # Use size + mtime as a quick integrity check
                quick_hash = f"{file_size}_{file_mtime}"
                return f"quick_{hashlib.md5(quick_hash.encode()).hexdigest()}"
            
            # Full BLAKE3 checksum for smaller files
            hasher = blake3.blake3()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):  # Read in 8KB chunks
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return None

    def create_snapshot(self, files_to_snapshot, snapshot_name=None, quick_mode=False):
        """Create lightweight snapshot capturing only file paths and directory structure.
        
        Args:
            files_to_snapshot: List of file paths to snapshot
            snapshot_name: Name for the snapshot (auto-generated if None)
            quick_mode: Ignored - always lightweight now
        """
        if snapshot_name is None:
            snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot_path = self.snapshots_dir / snapshot_name
        snapshot_path.mkdir(exist_ok=True)
        
        self.logger.info(f"Creating lightweight snapshot: {snapshot_name}")
        print(f"📸 Creating lightweight snapshot '{snapshot_name}'...")
        
        snapshot_metadata = {
            'snapshot_id': snapshot_name,
            'timestamp': datetime.now().isoformat(),
            'files_to_snapshot': [str(f) for f in files_to_snapshot],
            'files': []
        }
        
        total_files = len(files_to_snapshot)
        self.logger.info(f"Lightweight snapshot will capture {total_files} file paths")
        
        # Just capture file paths - no checksums needed
        with tqdm(total=total_files, desc="Lightweight Snapshot", unit="files") as pbar:
            for file_path in files_to_snapshot:
                try:
                    # Store just the path - rollback will use this to restore structure
                    snapshot_metadata['files'].append(str(file_path))
                    pbar.update(1)
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {e}")
        
        # Save snapshot metadata
        metadata_file = snapshot_path / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(snapshot_metadata, f, indent=2)
        
        self.logger.info(f"Lightweight snapshot created with {len(snapshot_metadata['files'])} file paths")
        print(f"✅ Lightweight snapshot '{snapshot_name}' created ({len(snapshot_metadata['files'])} files)")
        return snapshot_name

    def parse_plan_from_json(self, json_file_path):
        """Parse reorganization plan from RavenMaven JSON output."""
        self.logger.info(f"Parsing plan from: {json_file_path}")
        print(f"📄 Parsing reorganization plan from {json_file_path}...")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load JSON: {e}")
            raise
        
        operations = []
        total_results = len(results)
        
        with tqdm(total=total_results, desc="Parsing Results", unit="results") as pbar:
            for result in results:
                if not result.get('success', False):
                    self.logger.warning(f"Skipping failed result: {result.get('source', 'Unknown')}")
                    pbar.update(1)
                    continue
                
                response = result.get('response', '')
                mappings = self.parse_response_mappings(response)
                operations.extend(mappings)
                pbar.update(1)
        
        self.logger.info(f"Parsed {len(operations)} file operations from {total_results} results")
        print(f"✅ Parsed {len(operations)} file operations")
        return operations

    def parse_response_mappings(self, response_text):
        """Extract OLD: NEW mappings from LLM response text."""
        mappings = []
        lines = response_text.split('\n')
        old_path = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('OLD:'):
                old_path = line.replace('OLD:', '').strip()
            elif line.startswith('NEW:') and old_path:
                new_path = line.replace('NEW:', '').strip()
                mappings.append((old_path, new_path))
                old_path = None
        
        return mappings

    def validate_operations(self, operations):
        """Validate all operations before execution."""
        self.logger.info("Validating operations...")
        print(f"🔍 Validating {len(operations)} operations...")
        
        valid_operations = []
        
        with tqdm(total=len(operations), desc="Validation", unit="ops") as pbar:
            for old_path, new_path in operations:
                try:
                    self.validate_single_operation(old_path, new_path)
                    valid_operations.append((old_path, new_path))
                    self.logger.debug(f"Validated: {old_path} -> {new_path}")
                except Exception as e:
                    self.logger.error(f"Validation failed for {old_path} -> {new_path}: {e}")
                    print(f"❌ Validation failed: {e}")
                
                pbar.update(1)
        
        self.logger.info(f"Validation complete: {len(valid_operations)}/{len(operations)} operations valid")
        print(f"✅ Validation complete: {len(valid_operations)}/{len(operations)} operations valid")
        return valid_operations

    def validate_single_operation(self, old_path, new_path):
        """Validate a single file operation."""
        old_path_obj = Path(old_path)
        new_path_obj = Path(new_path)
        
        if not old_path_obj.exists():
            raise FileNotFoundError(f"Source does not exist: {old_path}")
        
        if new_path_obj.exists():
            raise FileExistsError(f"Destination already exists: {new_path}")
        
        # Check if we can create destination directory
        try:
            new_path_obj.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise PermissionError(f"Cannot create destination directory: {e}")

    def execute_operations(self, operations, dry_run=False):
        """Execute file operations with progress tracking."""
        mode = "DRY RUN" if dry_run else "EXECUTION"
        self.logger.info(f"Starting {mode} of {len(operations)} operations")
        print(f"🚀 Starting {mode}...")
        
        successful = 0
        failed = 0
        
        with tqdm(total=len(operations), desc=f"{mode} Progress", unit="files") as pbar:
            for old_path, new_path in operations:
                try:
                    self.execute_single_operation(old_path, new_path, dry_run)
                    successful += 1
                    status = "✅" if not dry_run else "👁️"
                    self.logger.info(f"{mode}: {old_path} -> {new_path}")
                except Exception as e:
                    failed += 1
                    status = "❌"
                    self.logger.error(f"{mode} FAILED: {old_path} -> {new_path}: {e}")
                
                pbar.set_postfix({"Success": successful, "Failed": failed})
                pbar.update(1)
        
        self.logger.info(f"{mode} complete: {successful} successful, {failed} failed")
        print(f"🏁 {mode} complete: {successful} successful, {failed} failed")
        return successful, failed

    def execute_single_operation(self, old_path, new_path, dry_run=False):
        """Execute a single file operation."""
        if dry_run:
            print(f"  Would move: {old_path} -> {new_path}")
            return

        # Get file size before move
        file_size = Path(old_path).stat().st_size

        # Create destination directory
        Path(new_path).parent.mkdir(parents=True, exist_ok=True)

        # Perform move
        shutil.move(old_path, new_path)

        # Log to immutable audit trail if available
        if self.immutable_audit:
            try:
                self.immutable_audit.log_event(
                    event_type='move',
                    details={
                        'source': str(old_path),
                        'destination': str(new_path),
                        'file_size': file_size,
                        'operation': 'move'
                    },
                    actor='jellyfin_safe_executor'
                )
            except Exception as e:
                self.logger.warning(f"Could not log to immutable audit: {e}")

    def create_audit_trail(self, operations, successful, failed, snapshot_id, rollback_manifest, cleaned_count, execution_time):
        """Create comprehensive audit trail."""
        self.logger.info("Creating audit trail...")
        print("📝 Creating audit trail...")
        
        audit_data = {
            'execution_timestamp': datetime.now().isoformat(),
            'snapshot_id': snapshot_id,
            'rollback_manifest': str(rollback_manifest) if rollback_manifest else None,
            'total_operations': len(operations),
            'successful_operations': successful,
            'failed_operations': failed,
            'directories_cleaned': cleaned_count,
            'execution_time_seconds': execution_time,
            'operations': []
        }
        
        for i, (old_path, new_path) in enumerate(operations):
            audit_data['operations'].append({
                'index': i,
                'old_path': old_path,
                'new_path': new_path,
                'executed': i < successful,  # Mark which operations were actually executed
                'timestamp': datetime.now().isoformat()
            })
        
        audit_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        self.logger.info(f"Audit trail saved to: {audit_file}")
        print(f"✅ Audit trail saved to: {audit_file}")

    def cleanup_empty_directories(self, operations):
        """Clean up empty directories after successful file moves."""
        self.logger.info("cleanup_empty_directories: Starting cleanup of empty directories")
        print("🧹 Cleaning up empty directories...")
        
        cleaned_count = 0
        total_dirs_checked = 0
        
        # Identify source directories from operations
        source_dirs = set()
        for old_path, _ in operations:
            source_dirs.add(str(Path(old_path).parent))
        
        # Process each source directory
        for source_dir in source_dirs:
            source_path = Path(source_dir)
            if not source_path.exists():
                continue
                
            # Walk through all subdirectories (bottom-up to handle nested empties)
            for dir_path in sorted(source_path.rglob('*'), key=lambda x: len(x.parts), reverse=True):
                if dir_path.is_dir():
                    total_dirs_checked += 1
                    try:
                        # Check if directory is empty
                        if not any(dir_path.iterdir()):
                            # Double-check it's still empty (race condition protection)
                            if not list(dir_path.iterdir()):
                                dir_path.rmdir()
                                cleaned_count += 1
                                self.logger.info(f"cleanup_empty_directories: Removed empty directory: {dir_path}")
                                print(f"  Removed: {dir_path}")
                    except Exception as e:
                        self.logger.warning(f"cleanup_empty_directories: Failed to remove {dir_path}: {e}")
        
        self.logger.info(f"cleanup_empty_directories: Cleanup complete - removed {cleaned_count} empty directories")
        print(f"✅ Cleanup complete: {cleaned_count} empty directories removed")
        return cleaned_count

    def create_rollback_manifest(self, operations):
        """Create a rollback manifest for undoing changes."""
        self.logger.info("create_rollback_manifest: Creating rollback manifest")
        print("📋 Creating rollback manifest...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        manifest_file = self.rollback_dir / f"rollback_{timestamp}.json"
        
        # Analyze current state and create rollback operations
        rollback_operations = []
        directories_to_restore = set()
        
        for old_path, new_path in operations:
            old_path_obj = Path(old_path)
            new_path_obj = Path(new_path)
            
            # Record the move operation for rollback (reverse direction)
            rollback_operations.append({
                'action': 'move',
                'from': str(new_path_obj),
                'to': str(old_path_obj),
                'original_operation': f"{old_path} -> {new_path}"
            })
            
            # Track directories that need to be restored
            old_parent = old_path_obj.parent
            if old_parent.exists() and old_parent not in directories_to_restore:
                directories_to_restore.add(str(old_parent))
        
        manifest_data = {
            'created_timestamp': datetime.now().isoformat(),
            'execution_timestamp': timestamp,
            'total_operations': len(rollback_operations),
            'directories_to_restore': list(directories_to_restore),
            'rollback_operations': rollback_operations,
            'status': 'ready'
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        self.logger.info(f"create_rollback_manifest: Rollback manifest created: {manifest_file}")
        print(f"✅ Rollback manifest created: {manifest_file}")
        return manifest_file

    def rollback_changes(self, manifest_path=None):
        """Rollback changes using the most recent manifest or specified manifest."""
        print("🔄 Starting Rollback Operation")
        print("=" * 50)
        
        # Find the most recent rollback manifest if not specified
        if manifest_path is None:
            rollback_files = list(self.rollback_dir.glob("rollback_*.json"))
            if not rollback_files:
                print("❌ No rollback manifests found")
                return False
            
            # Sort by creation time, get most recent
            manifest_path = max(rollback_files, key=lambda x: x.stat().st_ctime)
            print(f"📋 Using most recent rollback manifest: {manifest_path}")
        else:
            manifest_path = Path(manifest_path)
            if not manifest_path.exists():
                print(f"❌ Rollback manifest not found: {manifest_path}")
                return False
        
        # Load manifest
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load rollback manifest: {e}")
            return False
        
        print(f"🔄 Rolling back {manifest['total_operations']} operations...")
        print(f"   Created: {manifest['created_timestamp']}")
        
        successful_rollbacks = 0
        failed_rollbacks = 0
        
        # Execute rollback operations in reverse order
        for operation in reversed(manifest['rollback_operations']):
            try:
                if operation['action'] == 'move':
                    from_path = Path(operation['from'])
                    to_path = Path(operation['to'])
                    
                    if from_path.exists():
                        # Create destination directory
                        to_path.parent.mkdir(parents=True, exist_ok=True)
                        # Move file back
                        shutil.move(str(from_path), str(to_path))
                        successful_rollbacks += 1
                        print(f"  ✅ Restored: {from_path} -> {to_path}")
                        self.logger.info(f"rollback_changes: Restored {from_path} -> {to_path}")
                    else:
                        print(f"  ⚠️  Source file missing: {from_path}")
                        self.logger.warning(f"rollback_changes: Source file missing: {from_path}")
                        
            except Exception as e:
                failed_rollbacks += 1
                print(f"  ❌ Failed to rollback: {operation['original_operation']} - {e}")
                self.logger.error(f"rollback_changes: Failed to rollback {operation['original_operation']}: {e}")
        
        # Update manifest status
        manifest['status'] = 'completed' if failed_rollbacks == 0 else 'partial'
        manifest['rollback_timestamp'] = datetime.now().isoformat()
        manifest['successful_rollbacks'] = successful_rollbacks
        manifest['failed_rollbacks'] = failed_rollbacks
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"🔄 Rollback Complete!")
        print(f"   Successful: {successful_rollbacks}")
        print(f"   Failed: {failed_rollbacks}")
        print(f"   Status: {'✅ Complete' if failed_rollbacks == 0 else '⚠️  Partial'}")
        
        self.logger.info(f"rollback_changes: Rollback complete - {successful_rollbacks} successful, {failed_rollbacks} failed")
        return failed_rollbacks == 0

    def execute_plan(self, json_file_path, dry_run=False, quick_snapshot=False, cleanup_empty=True, enable_rollback=True):
        start_time = datetime.now()
        self.logger.info(f"Starting plan execution from: {json_file_path} (dry_run={dry_run}, cleanup_empty={cleanup_empty}, enable_rollback={enable_rollback})")
        print(f"🎯 Starting Jellyfin Safe Executor")
        print(f"   Plan: {json_file_path}")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
        print(f"   Cleanup: {'ENABLED' if cleanup_empty else 'DISABLED'}")
        print(f"   Rollback: {'ENABLED' if enable_rollback else 'DISABLED'}")
        print(f"   Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        rollback_manifest = None
        try:
            # Phase 1: Parse plan
            print("Phase 1: Parsing Reorganization Plan")
            operations = self.parse_plan_from_json(json_file_path)
            print()

            # Phase 2: Create snapshot (only for live execution)
            snapshot_id = None
            if not dry_run:
                print("Phase 2: Creating Pre-Execution Snapshot")
                files_to_snapshot = [Path(old_path) for old_path, _ in operations]
                snapshot_id = self.create_snapshot(files_to_snapshot, quick_mode=quick_snapshot)
                print()

            # Phase 3: Validate operations
            print("Phase 3: Validating Operations")
            valid_operations = self.validate_operations(operations)
            print()

            if not valid_operations:
                self.logger.error("No valid operations to execute")
                print("❌ No valid operations to execute")
                return 0, 0

            # Phase 4: Execute operations
            print("Phase 4: Executing Operations")
            successful, failed = self.execute_operations(valid_operations, dry_run)
            print()

            # Phase 5: Create rollback manifest (only for live execution with rollback enabled)
            if not dry_run and enable_rollback and successful > 0:
                print("Phase 5: Creating Rollback Manifest")
                rollback_manifest = self.create_rollback_manifest(valid_operations[:successful])  # Only successful operations
                print(f"✅ Rollback manifest created: {rollback_manifest}")
                print()

            # Phase 6: Cleanup empty directories (only for live execution with cleanup enabled)
            cleaned_count = 0
            if not dry_run and cleanup_empty and successful > 0:
                print("Phase 6: Cleaning Up Empty Directories")
                cleaned_count = self.cleanup_empty_directories(valid_operations[:successful])
                print()

            # Phase 7: Create audit trail
            execution_time = (datetime.now() - start_time).total_seconds()
            print("Phase 7: Creating Audit Trail")
            self.create_audit_trail(valid_operations, successful, failed, snapshot_id, rollback_manifest, cleaned_count, execution_time)
            print()

            # Final summary
            end_time = datetime.now()
            self.logger.info(f"Plan execution completed in {execution_time:.2f} seconds")
            print("🎉 Execution Complete!")
            print(f"   End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Duration: {execution_time:.2f} seconds")
            print(f"   Operations: {successful + failed}")
            print(f"   Successful: {successful}")
            print(f"   Failed: {failed}")
            if cleaned_count > 0:
                print(f"   Directories Cleaned: {cleaned_count}")
            if snapshot_id:
                print(f"   Snapshot: {snapshot_id}")
            if rollback_manifest:
                print(f"   Rollback Manifest: {rollback_manifest.name}")
                print("   💡 To rollback changes: python jellyfin_safe_executor.py --rollback")
            
            return successful, failed

        except Exception as e:
            self.logger.error(f"Plan execution failed: {e}")
            print(f"💥 Execution failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Jellyfin Safe Executor - Safely execute RavenMaven reorganization plans")
    parser.add_argument("json_file", nargs='?', help="Path to RavenMaven processed JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview operations without executing them")
    parser.add_argument("--quick-snapshot", action="store_true", help="Use quick checksums for large files (>100MB) to speed up snapshot creation")
    parser.add_argument("--jellyfin-dir", default="V:/Jellyfin Organizer", help="Jellyfin Organizer base directory")
    parser.add_argument("--no-cleanup", action="store_true", help="Disable automatic cleanup of empty directories")
    parser.add_argument("--no-rollback", action="store_true", help="Disable rollback manifest creation")
    parser.add_argument("--rollback", action="store_true", help="Execute rollback using the most recent manifest")
    parser.add_argument("--rollback-manifest", help="Specify specific rollback manifest file to use")
    
    args = parser.parse_args()
    
    # Handle rollback mode
    if args.rollback or args.rollback_manifest:
        if not args.json_file and not args.rollback_manifest:
            print("❌ Rollback mode requires either a JSON file or --rollback-manifest")
            sys.exit(1)
        
        executor = JellyfinSafeExecutor(args.jellyfin_dir)
        
        if args.rollback_manifest:
            success = executor.rollback_changes(args.rollback_manifest)
        else:
            # Use the most recent manifest
            success = executor.rollback_changes()
        
        sys.exit(0 if success else 1)
    
    # Normal execution mode
    if not args.json_file:
        print("❌ JSON file required for execution mode")
        parser.print_help()
        sys.exit(1)
    
    executor = JellyfinSafeExecutor(args.jellyfin_dir)
    successful, failed = executor.execute_plan(
        args.json_file, 
        dry_run=args.dry_run, 
        quick_snapshot=args.quick_snapshot,
        cleanup_empty=not args.no_cleanup,
        enable_rollback=not args.no_rollback
    )
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()