"""
Unified logging module for JellyRancher application.
Provides comprehensive, unified logging to a SINGLE master log file.
All modules log to the same master log with proper categorization.
"""

import logging
import logging.handlers
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
import subprocess
import platform

# Global master logger instance
_master_logger = None
_master_logger_lock = threading.Lock()

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