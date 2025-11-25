"""
Unified logging module for JellyRancher application.
Provides comprehensive, unified logging to a SINGLE master log file.
All modules log to the same master log with proper categorization.

Includes stdout/stderr capture so ALL console output goes to the log.
"""

import logging
import logging.handlers
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO
import subprocess
import platform

# Global master logger instance
_master_logger = None
_master_logger_lock = threading.Lock()


class LoggingStream:
    """
    A stream wrapper that sends writes to both a logger and the original stream.
    This ensures all print() statements are captured in the log file.
    """
    
    def __init__(self, logger: logging.Logger, level: int, original_stream: TextIO, prefix: str = ""):
        """
        Initialize the logging stream.
        
        Args:
            logger: Logger to write to
            level: Logging level (INFO for stdout, WARNING for stderr)
            original_stream: Original sys.stdout or sys.stderr
            prefix: Optional prefix for log messages (e.g., "[STDOUT]")
        """
        self.logger = logger
        self.level = level
        self.original_stream = original_stream
        self.prefix = prefix
        self._buffer = ""
    
    def write(self, message: str):
        """Write message to both logger and original stream."""
        # Always write to original stream for console visibility
        if self.original_stream:
            self.original_stream.write(message)
        
        # Buffer and log complete lines
        if message:
            self._buffer += message
            while '\n' in self._buffer:
                line, self._buffer = self._buffer.split('\n', 1)
                if line.strip():  # Don't log empty lines
                    log_msg = f"{self.prefix}{line}" if self.prefix else line
                    self.logger.log(self.level, log_msg)
    
    def flush(self):
        """Flush the stream."""
        if self.original_stream:
            self.original_stream.flush()
        # Flush any remaining buffer content
        if self._buffer.strip():
            log_msg = f"{self.prefix}{self._buffer}" if self.prefix else self._buffer
            self.logger.log(self.level, log_msg)
            self._buffer = ""
    
    def isatty(self):
        """Check if stream is a TTY."""
        return self.original_stream.isatty() if self.original_stream else False
    
    def fileno(self):
        """Return file descriptor."""
        return self.original_stream.fileno() if self.original_stream else -1

class MasterLogger:
    """
    Singleton master logger that manages a single application-wide log file.
    All modules log to this unified log with proper categorization.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the master logger with unified configuration."""
        # Create master log directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # Master log filename with date
        date_str = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"jelly_rancher_master_{date_str}.log"

        # Setup master logger
        self.logger = logging.getLogger('jelly_rancher_master')
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Rotating file handler (10MB per file, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Detailed file format with module categorization
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler with colored output for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '[%(levelname)s] [%(module)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info("JellyRancher Master Logger Initialized")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info("=" * 80)

    def get_child_logger(self, module_name: str) -> logging.Logger:
        """
        Get a child logger for a specific module.
        All child loggers inherit the master logger's handlers.

        Args:
            module_name: Name of the module/component

        Returns:
            Logger instance configured for the module
        """
        child_logger = self.logger.getChild(module_name)
        return child_logger

    def get_log_path(self) -> Path:
        """Return path to master log file."""
        return self.log_file

    def open_log(self):
        """Open master log file in system default editor/viewer."""
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', str(self.log_file)])
            elif platform.system() == 'Windows':
                os.startfile(str(self.log_file))
            else:  # Linux
                subprocess.Popen(['xdg-open', str(self.log_file)])
        except Exception as e:
            self.logger.warning(f"Could not open master log: {e}")
    
    def capture_stdout_stderr(self):
        """
        Redirect stdout and stderr to the logger.
        All print() statements will now appear in the log file.
        
        This should be called once during application startup.
        """
        # Create a child logger for captured output
        capture_logger = self.get_child_logger("console")
        
        # Store original streams
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        
        # Replace with logging streams
        sys.stdout = LoggingStream(
            capture_logger, 
            logging.INFO, 
            self._original_stdout,
            "[PRINT] "
        )
        sys.stderr = LoggingStream(
            capture_logger, 
            logging.WARNING, 
            self._original_stderr,
            "[STDERR] "
        )
        
        self.logger.info("Console output capture enabled - all print() statements will appear in log")
    
    def restore_stdout_stderr(self):
        """Restore original stdout and stderr."""
        if hasattr(self, '_original_stdout') and self._original_stdout:
            sys.stdout = self._original_stdout
        if hasattr(self, '_original_stderr') and self._original_stderr:
            sys.stderr = self._original_stderr
        self.logger.info("Console output capture disabled")

class ProjectLogger:
    """
    Backward-compatible logger interface that uses the unified MasterLogger.
    Each module gets its own child logger that writes to the master log.
    """

    def __init__(self, script_name: str, auto_open: bool = False):
        """
        Initialize project-compliant logger using unified master log.

        Args:
            script_name: Name of calling script/module (e.g., 'tmdb_backend')
            auto_open: Whether to auto-open master log in default editor (default: False)
        """
        self.script_name = script_name

        # Get master logger instance
        self.master_logger = MasterLogger()

        # Get child logger for this module
        self.logger = self.master_logger.get_child_logger(script_name)

        # Auto-open master log if requested (only once per session)
        if auto_open:
            self.master_logger.open_log()

    def info(self, msg: str):
        self.logger.info(msg)

    def success(self, msg: str):
        self.logger.info(f"[SUCCESS] {msg}")

    def error(self, msg: str):
        self.logger.error(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def dryrun(self, msg: str):
        self.logger.info(f"[DRYRUN] {msg}")

    def critical(self, msg: str):
        self.logger.critical(msg)

    def get_log_path(self) -> Path:
        """Return path to master log file."""
        return self.master_logger.get_log_path()

    def open_log(self):
        """Open master log file in system default editor/viewer."""
        self.master_logger.open_log()