#!/usr/bin/env python3
"""
Create zero-byte file structure in VHDX disk image.

Scans F:\\OneDrive\\DOWNLOADS and V:\\ recursively, creates zero-byte copies
in a mountable VHDX image. Image is unmounted after creation to prevent
Everything from indexing it.

Usage:
    python tools/create_zero_byte_vhdx.py --output "F:\\zero_byte_structure.vhdx" --size-gb 10
"""

import subprocess
import logging
import argparse
import sys
import time
import os
from pathlib import Path
from typing import List, Optional, Set, Tuple
import shutil

# Set console encoding to UTF-8 on Windows to handle Unicode
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

# Setup Rich console
console = Console()

# Setup logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='[%X]',
    handlers=[
        RichHandler(console=console, rich_tracebacks=True),
        logging.FileHandler('create_zero_byte_vhdx.log')
    ]
)
logger = logging.getLogger(__name__)


def run_powershell(command: str, capture_output: bool = True) -> Tuple[bool, str]:
    """
    Run a PowerShell command and return success status and output.
    
    IMPORTANT: Always use pwsh.exe (PowerShell 7+), NOT powershell.exe (legacy 5.1).
    
    Args:
        command: PowerShell command to execute
        capture_output: Whether to capture stdout/stderr
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        # ALWAYS use pwsh.exe (PowerShell 7+), NOT the legacy powershell.exe
        result = subprocess.run(
            ['pwsh.exe', '-NoProfile', '-Command', command],
            capture_output=capture_output,
            text=True,
            timeout=300,  # 5 minute timeout
            shell=False  # Never use shell=True - causes issues when already in pwsh
        )
        output = result.stdout.strip() if capture_output else ""
        if result.returncode != 0:
            error = result.stderr.strip() if capture_output else ""
            logger.error(f"PowerShell command failed: {command}\nError: {error}")
            return False, error
        return True, output
    except subprocess.TimeoutExpired:
        logger.error(f"PowerShell command timed out: {command}")
        return False, "Command timed out"
    except Exception as e:
        logger.error(f"Failed to run PowerShell command: {e}")
        return False, str(e)


def create_vhdx_image(vhdx_path: Path, size_gb: int) -> bool:
    """
    Create a dynamic VHDX disk image.
    
    Args:
        vhdx_path: Path where VHDX file will be created
        size_gb: Maximum size in GB (dynamic, grows as needed)
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Creating VHDX image: {vhdx_path} ({size_gb}GB dynamic)")
    
    # Ensure parent directory exists
    vhdx_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Delete existing VHDX if present
    if vhdx_path.exists():
        logger.warning(f"VHDX already exists, deleting: {vhdx_path}")
        try:
            # Try to unmount first if mounted
            unmount_vhdx(vhdx_path)
            vhdx_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete existing VHDX: {e}")
            return False
    
    size_bytes = size_gb * 1024 * 1024 * 1024
    command = f'New-VHD -Path "{vhdx_path}" -SizeBytes {size_bytes} -Dynamic'
    
    success, output = run_powershell(command)
    if success:
        logger.info(f"VHDX created successfully: {vhdx_path}")
        return True
    else:
        logger.error(f"Failed to create VHDX: {output}")
        return False


def mount_and_initialize_vhdx(vhdx_path: Path) -> Optional[str]:
    """
    Mount a VHDX disk image, initialize it, and return its drive letter.
    
    For a NEW VHDX, the flow is:
    1. Mount VHDX (attaches as raw disk with no partitions)
    2. Initialize disk (create GPT partition table)
    3. Create partition (gets a drive letter)
    4. Format as NTFS
    
    Args:
        vhdx_path: Path to VHDX file
        
    Returns:
        Drive letter (e.g., "E:") or None if failed
    """
    logger.info(f"Mounting VHDX: {vhdx_path}")
    
    # Mount the VHDX
    mount_cmd = f'Mount-VHD -Path "{vhdx_path}"'
    success, output = run_powershell(mount_cmd)
    if not success:
        logger.error(f"Failed to mount VHDX: {output}")
        return None
    
    # Wait a moment for mount to complete
    time.sleep(2)
    
    # Get the disk number for the mounted VHDX
    get_disk_cmd = f'''
    $diskImage = Get-DiskImage -ImagePath "{vhdx_path}"
    $disk = $diskImage | Get-Disk
    $disk.Number
    '''
    
    success, output = run_powershell(get_disk_cmd)
    if not success or not output.strip():
        logger.error(f"Failed to get disk number: {output}")
        return None
    
    disk_number = output.strip()
    logger.info(f"VHDX attached as disk {disk_number}")
    
    # Check if disk is already initialized
    check_cmd = f'(Get-Disk -Number {disk_number}).PartitionStyle'
    success, partition_style = run_powershell(check_cmd)
    
    if success and partition_style.strip() == "RAW":
        # Initialize the disk
        logger.info("Initializing RAW disk with GPT partition table...")
        init_cmd = f'Initialize-Disk -Number {disk_number} -PartitionStyle GPT -PassThru | Out-Null'
        success, output = run_powershell(init_cmd)
        if not success:
            logger.error(f"Failed to initialize disk: {output}")
            return None
    
    # Create partition with drive letter and format
    logger.info("Creating partition and formatting as NTFS...")
    partition_cmd = f'''
    $partition = New-Partition -DiskNumber {disk_number} -UseMaximumSize -AssignDriveLetter
    Format-Volume -Partition $partition -FileSystem NTFS -NewFileSystemLabel "ZeroByteStructure" -Confirm:$false | Out-Null
    $partition.DriveLetter
    '''
    
    success, output = run_powershell(partition_cmd)
    if success and output.strip():
        drive_letter = output.strip() + ":"
        logger.info(f"Disk initialized, formatted, and mounted at: {drive_letter}")
        return drive_letter
    else:
        logger.error(f"Failed to create partition: {output}")
        return None


def mount_vhdx(vhdx_path: Path) -> Optional[str]:
    """
    Mount a VHDX disk image and return its drive letter.
    Wrapper for backwards compatibility - now calls mount_and_initialize_vhdx.
    """
    return mount_and_initialize_vhdx(vhdx_path)


def initialize_vhdx_disk(drive_letter: str) -> bool:
    """
    Initialize disk - now a no-op since mount_and_initialize_vhdx handles everything.
    Kept for backwards compatibility.
    """
    logger.info(f"Disk already initialized (handled during mount)")
    return True


def unmount_vhdx(vhdx_path: Path) -> bool:
    """
    Unmount a VHDX disk image.
    
    Args:
        vhdx_path: Path to VHDX file
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Unmounting VHDX: {vhdx_path}")
    
    command = f'Dismount-VHD -Path "{vhdx_path}"'
    success, output = run_powershell(command)
    
    if success:
        logger.info("VHDX unmounted successfully")
        return True
    else:
        logger.warning(f"Unmount warning: {output}")
        return False


def scan_all_files(
    source: Path, 
    exclude_paths: Optional[Set[Path]] = None,
    progress: Optional[Progress] = None,
    task_id: Optional[int] = None
) -> List[Path]:
    """
    Recursively scan all files in a directory.
    
    Supports Windows long paths by using \\\\?\\ prefix when needed.
    
    Args:
        source: Root directory to scan
        exclude_paths: Optional set of paths to exclude
        progress: Optional Rich Progress object for progress bar
        task_id: Optional task ID for progress bar
        
    Returns:
        List of Path objects for all files found
    """
    console.print(f"[cyan]Scanning:[/cyan] {source}")
    files = []
    exclude_paths = exclude_paths or set()
    
    # Convert to long path format for Windows if needed
    try:
        long_path_source = Path(str(source).encode('utf-8').decode('utf-8'))
        if sys.platform == 'win32' and len(str(source)) > 260:
            # Use long path prefix
            long_path_source = Path(f"\\\\?\\{source.resolve()}")
    except Exception:
        long_path_source = source
    
    try:
        for item in long_path_source.rglob('*'):
            try:
                # Skip if in exclude list
                if any(excluded in item.parts for excluded in exclude_paths):
                    continue
                
                # Check if file (skip on error)
                try:
                    if item.is_file():
                        files.append(item)
                        
                        # Update progress bar if available
                        if progress and task_id is not None:
                            progress.update(task_id, completed=len(files))
                except (PermissionError, OSError):
                    # Skip inaccessible files silently
                    continue
                        
            except (PermissionError, OSError, UnicodeEncodeError) as e:
                # Skip inaccessible files silently
                continue
            except Exception as e:
                # Log unexpected errors but continue
                logger.debug(f"Skipping item due to error: {e}")
                continue
                
    except Exception as e:
        logger.warning(f"Error during scan of {source}: {e} (continuing with files found so far)")
    
    console.print(f"[green][OK][/green] Scan complete: [bold]{len(files):,}[/bold] files found")
    return files


def create_zero_byte_structure(
    drive_letter: str,
    files: List[Path],
    source_root: Path,
    target_root: str,
    stats: dict,
    progress: Optional[Progress] = None,
    task_id: Optional[int] = None
) -> None:
    """
    Create zero-byte file structure in VHDX.
    
    Args:
        drive_letter: Drive letter of mounted VHDX (e.g., "E:")
        files: List of source file paths
        source_root: Root directory of source (for calculating relative paths)
        target_root: Target directory name in VHDX (e.g., "OneDrive_DOWNLOADS")
        stats: Dictionary to update with statistics
        progress: Optional Rich Progress object for progress bar
        task_id: Optional task ID for progress bar
    """
    console.print(f"[cyan]Creating zero-byte structure:[/cyan] {len(files):,} files -> {drive_letter}\\{target_root}")
    
    target_base = Path(f"{drive_letter}\\{target_root}")
    try:
        target_base.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        console.print(f"[red][FAIL][/red] Failed to create target base directory {target_base}: {e}")
        return
    
    created_files = 0
    created_dirs = 0
    errors = 0
    
    for i, source_file in enumerate(files):
        try:
            # Calculate relative path from source root
            try:
                relative_path = source_file.relative_to(source_root)
            except ValueError:
                # File not under source_root, use full path structure
                # Replace drive letter and colons with underscores
                path_parts = source_file.parts
                if len(path_parts) > 1 and path_parts[0].endswith(':'):
                    # Remove drive letter, keep rest
                    relative_path = Path(*path_parts[1:])
                else:
                    relative_path = Path(*path_parts)
            
            # Create target path
            target_file = target_base / relative_path
            
            # Create parent directories (skip on error)
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                if not target_file.parent.exists():
                    created_dirs += 1
            except Exception as e:
                logger.debug(f"Failed to create directory {target_file.parent}: {e}")
                errors += 1
                continue
            
            # Create zero-byte file (skip on error)
            try:
                target_file.touch()
                created_files += 1
            except Exception as e:
                logger.debug(f"Failed to create file {target_file}: {e}")
                errors += 1
                continue
            
            # Update progress bar if available
            if progress and task_id is not None:
                progress.update(task_id, completed=i + 1)
                
        except (PermissionError, OSError, ValueError, UnicodeEncodeError) as e:
            errors += 1
            if errors <= 10:  # Log first 10 errors, then only debug
                logger.warning(f"Failed to create {source_file}: {e}")
            else:
                logger.debug(f"Failed to create {source_file}: {e}")
            continue
        except Exception as e:
            errors += 1
            logger.warning(f"Unexpected error creating {source_file}: {e}")
            continue
    
    stats['files_created'] += created_files
    stats['dirs_created'] += created_dirs
    stats['errors'] += errors
    
    console.print(
        f"[green][OK][/green] Structure created: [bold]{created_files:,}[/bold] files, "
        f"[bold]{created_dirs:,}[/bold] dirs, [yellow]{errors:,}[/yellow] errors"
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create zero-byte file structure in VHDX disk image'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Path to output VHDX file (e.g., F:\\zero_byte_structure.vhdx)'
    )
    parser.add_argument(
        '--size-gb',
        type=int,
        default=10,
        help='VHDX maximum size in GB (default: 10, dynamic so grows as needed)'
    )
    parser.add_argument(
        '--exclude',
        type=Path,
        nargs='*',
        help='Paths to exclude from scanning'
    )
    
    args = parser.parse_args()
    
    # Validate output path
    if args.output.suffix.lower() != '.vhdx':
        logger.error("Output file must have .vhdx extension")
        return 1
    
    # Check available disk space (rough estimate)
    output_drive = args.output.drive
    if output_drive:
        import shutil
        free_space_gb = shutil.disk_usage(args.output.parent).free / (1024**3)
        if free_space_gb < args.size_gb:
            logger.warning(
                f"Available space ({free_space_gb:.1f}GB) is less than VHDX size ({args.size_gb}GB). "
                "VHDX is dynamic, so this may still work."
            )
    
    # Prepare exclude paths
    exclude_paths = set(args.exclude) if args.exclude else set()
    
    # Statistics
    stats = {
        'files_created': 0,
        'dirs_created': 0,
        'errors': 0
    }
    
    # Display header
    console.print(Panel.fit(
        "[bold cyan]Zero-Byte File Structure VHDX Creator[/bold cyan]\n\n"
        f"Output: [yellow]{args.output}[/yellow]\n"
        f"Size: [yellow]{args.size_gb}GB[/yellow] (dynamic)",
        border_style="cyan"
    ))
    
    try:
        # Step 1: Create VHDX
        console.print("\n[bold cyan]Step 1:[/bold cyan] Creating VHDX image")
        with console.status("[cyan]Creating VHDX...", spinner="dots"):
            if not create_vhdx_image(args.output, args.size_gb):
                console.print("[red][FAIL][/red] Failed to create VHDX image")
                return 1
        console.print("[green][OK][/green] VHDX created successfully")
        
        # Step 2: Mount VHDX
        console.print("\n[bold cyan]Step 2:[/bold cyan] Mounting VHDX")
        with console.status("[cyan]Mounting VHDX...", spinner="dots"):
            drive_letter = mount_vhdx(args.output)
            if not drive_letter:
                console.print("[red][FAIL][/red] Failed to mount VHDX")
                # Unmount first before cleanup
                unmount_vhdx(args.output)
                time.sleep(1)
                # Now try to clean up
                try:
                    if args.output.exists():
                        args.output.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete failed VHDX: {e}")
                return 1
        console.print(f"[green][OK][/green] VHDX mounted at [bold]{drive_letter}[/bold]")
        
        # Step 3: Initialize disk
        console.print("\n[bold cyan]Step 3:[/bold cyan] Initializing disk")
        with console.status("[cyan]Initializing and formatting disk...", spinner="dots"):
            if not initialize_vhdx_disk(drive_letter):
                console.print("[red][FAIL][/red] Failed to initialize disk")
                unmount_vhdx(args.output)
                return 1
        console.print("[green][OK][/green] Disk initialized and formatted")
        
        # Step 4: Scan sources
        console.print("\n[bold cyan]Step 4:[/bold cyan] Scanning source directories")
        
        onedrive_path = Path("F:\\OneDrive\\DOWNLOADS")
        v_drive_path = Path("V:\\")
        
        onedrive_files = []
        v_drive_files = []
        
        # Use Rich Progress for scanning
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            # Scan F:\OneDrive\DOWNLOADS
            if onedrive_path.exists():
                task1 = progress.add_task(f"[cyan]Scanning {onedrive_path.name}...", total=None)
                try:
                    onedrive_files = scan_all_files(onedrive_path, exclude_paths, progress, task1)
                    if task1 is not None:
                        progress.update(task1, total=len(onedrive_files), completed=len(onedrive_files))
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Error scanning {onedrive_path}: {e} (skipping)")
                    onedrive_files = []
            else:
                console.print(f"[yellow]⚠[/yellow] Source not found: {onedrive_path}")
            
            # Scan V:\
            if v_drive_path.exists():
                task2 = progress.add_task(f"[cyan]Scanning {v_drive_path}...", total=None)
                try:
                    v_drive_files = scan_all_files(v_drive_path, exclude_paths, progress, task2)
                    if task2 is not None:
                        progress.update(task2, total=len(v_drive_files), completed=len(v_drive_files))
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Error scanning {v_drive_path}: {e} (skipping)")
                    v_drive_files = []
            else:
                console.print(f"[yellow]⚠[/yellow] Source not found: {v_drive_path}")
        
        total_files = len(onedrive_files) + len(v_drive_files)
        console.print(f"\n[bold]Total files to process:[/bold] [cyan]{total_files:,}[/cyan]")
        
        # Step 5: Create zero-byte structures
        console.print("\n[bold cyan]Step 5:[/bold cyan] Creating zero-byte file structures")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console
        ) as progress:
            if onedrive_files:
                task1 = progress.add_task(
                    "[cyan]Creating OneDrive structure...",
                    total=len(onedrive_files)
                )
                try:
                    create_zero_byte_structure(
                        drive_letter,
                        onedrive_files,
                        onedrive_path,
                        "OneDrive_DOWNLOADS",
                        stats,
                        progress,
                        task1
                    )
                except Exception as e:
                    console.print(f"[red][FAIL][/red] Error creating OneDrive structure: {e} (continuing)")
            
            if v_drive_files:
                task2 = progress.add_task(
                    "[cyan]Creating V_Drive structure...",
                    total=len(v_drive_files)
                )
                try:
                    create_zero_byte_structure(
                        drive_letter,
                        v_drive_files,
                        v_drive_path,
                        "V_Drive",
                        stats,
                        progress,
                        task2
                    )
                except Exception as e:
                    console.print(f"[red][FAIL][/red] Error creating V_Drive structure: {e} (continuing)")
        
        # Step 6: Unmount VHDX
        console.print("\n[bold cyan]Step 6:[/bold cyan] Unmounting VHDX")
        with console.status("[cyan]Unmounting VHDX...", spinner="dots"):
            unmount_vhdx(args.output)
        console.print("[green][OK][/green] VHDX unmounted")
        
        # Final report
        console.print("\n")
        table = Table(title="[bold green][OK] COMPLETE - Final Statistics[/bold green]", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        
        table.add_row("VHDX Location", str(args.output))
        table.add_row("Files Created", f"{stats['files_created']:,}")
        table.add_row("Directories Created", f"{stats['dirs_created']:,}")
        table.add_row("Errors", f"[yellow]{stats['errors']:,}[/yellow]")
        table.add_row("VHDX Size", f"{args.size_gb}GB (dynamic)")
        
        console.print(table)
        console.print("\n[bold green]VHDX is unmounted. Everything will not index it.[/bold green]")
        console.print(f"[dim]To mount manually:[/dim] [cyan]Mount-VHD -Path \"{args.output}\"[/cyan]")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        # Try to clean up
        try:
            unmount_vhdx(args.output)
        except:
            pass
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        # Try to clean up
        try:
            unmount_vhdx(args.output)
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())

