"""
Beautiful, colorful pytest progress reporting with Rich library.

Provides the most granular progress indication with:
- Colorful progress bars
- Real-time test names
- Percentage, time elapsed, ETA
- Pass/Fail/Skip counts with colors
- Beautiful formatting
"""

import pytest
import time
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# Global state
_progress_state = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'start_time': None,
    'current_test': None,
    'progress': None,
    'live': None,
    'task_id': None,
}


def pytest_collection_modifyitems(config, items):
    """Called after test collection - initialize progress tracking."""
    _progress_state['total'] = len(items)
    _progress_state['start_time'] = time.time()
    
    # Only show rich progress if not in quiet mode
    if config.getoption('verbose', 0) >= 0 and not config.getoption('quiet', False):
        # Create Rich progress bar
        _progress_state['progress'] = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        )
        
        _progress_state['task_id'] = _progress_state['progress'].add_task(
            f"[cyan]Running {len(items)} tests",
            total=len(items)
        )
        
        _progress_state['live'] = Live(
            _progress_state['progress'],
            console=console,
            refresh_per_second=10
        )
        _progress_state['live'].start()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Called after each test - update progress with colors."""
    outcome = yield
    result = outcome.get_result()
    
    if result.when == "call":  # Only count on actual test execution
        _progress_state['current_test'] = f"{item.nodeid}"
        
        # Update counts
        if result.outcome == "passed":
            _progress_state['passed'] += 1
            status_color = "[green]✓"
            status_text = "PASSED"
        elif result.outcome == "failed":
            _progress_state['failed'] += 1
            status_color = "[red]✗"
            status_text = "FAILED"
        elif result.outcome == "skipped":
            _progress_state['skipped'] += 1
            status_color = "[yellow]⊘"
            status_text = "SKIPPED"
        else:
            status_color = "[white]?"
            status_text = result.outcome.upper()
        
        # Update progress bar
        if _progress_state['progress'] and _progress_state['task_id'] is not None:
            completed = _progress_state['passed'] + _progress_state['failed'] + _progress_state['skipped']
            
            # Create detailed description
            test_name = item.nodeid.split("::")[-1]  # Just the test function name
            description = (
                f"[cyan]{status_color} {status_text}[/] "
                f"[dim]{test_name}[/] | "
                f"[green]Pass: {_progress_state['passed']}[/] "
                f"[red]Fail: {_progress_state['failed']}[/] "
                f"[yellow]Skip: {_progress_state['skipped']}[/]"
            )
            
            _progress_state['progress'].update(
                _progress_state['task_id'],
                completed=completed,
                description=description
            )


def pytest_sessionfinish(session, exitstatus):
    """Called at end of test session - print beautiful summary."""
    if _progress_state['live']:
        _progress_state['live'].stop()
    
    if _progress_state['progress']:
        _progress_state['progress'].stop()
    
    # Create beautiful summary table
    elapsed = time.time() - _progress_state['start_time'] if _progress_state['start_time'] else 0
    
    table = Table(title="[bold cyan]Test Session Summary[/]", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")
    
    table.add_row("Total Tests", f"[white]{_progress_state['total']}[/]")
    table.add_row("[green]✓ Passed[/]", f"[green]{_progress_state['passed']}[/]")
    table.add_row("[red]✗ Failed[/]", f"[red]{_progress_state['failed']}[/]")
    table.add_row("[yellow]⊘ Skipped[/]", f"[yellow]{_progress_state['skipped']}[/]")
    table.add_row("Time Elapsed", f"[blue]{elapsed:.2f}s[/]")
    
    if _progress_state['total'] > 0:
        pass_rate = (_progress_state['passed'] / _progress_state['total']) * 100
        if pass_rate == 100:
            table.add_row("Pass Rate", f"[green]{pass_rate:.1f}%[/]")
        elif pass_rate >= 90:
            table.add_row("Pass Rate", f"[yellow]{pass_rate:.1f}%[/]")
        else:
            table.add_row("Pass Rate", f"[red]{pass_rate:.1f}%[/]")
    
    console.print()
    console.print(table)
    console.print()
