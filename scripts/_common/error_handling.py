"""
Shared error handling utilities for JellyRancher.

Provides decorators and utilities for consistent error handling across the application.
"""

import functools
import logging
import traceback
from typing import Callable, Any, Optional, Type, Tuple
from PyQt6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)


def safe_slot(show_error: bool = True, default_return: Any = None, halt_on_error: bool = True):
    """
    Decorator for Qt slots that provides comprehensive error handling.
    
    Args:
        show_error: Whether to show a message box on error (default True)
        default_return: Value to return on error (default None)
        halt_on_error: Whether to re-raise exception to trigger global handler (default True)
    
    Usage:
        @safe_slot()
        def on_button_clicked(self):
            # risky operation - will HALT app on error
            
        @safe_slot(halt_on_error=False)
        def on_timer_tick(self):
            # non-critical - won't halt app
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Get the class name for better logging
                class_name = self.__class__.__name__ if hasattr(self, '__class__') else 'Unknown'
                func_name = func.__name__
                
                # Log the full traceback
                logger.error(
                    f"Error in {class_name}.{func_name}: {e}",
                    exc_info=True
                )
                
                # Show error status if requested (non-modal - Phase 48-E-6)
                if show_error:
                    parent = self if isinstance(self, QWidget) else None
                    if parent and hasattr(parent, '_set_status'):
                        parent._set_status(f"Operation Failed in {class_name}.{func_name}: {e}", level='error')
                    elif parent and hasattr(parent, 'status_label'):
                        parent.status_label.setText(f"❌ Operation Failed: {e}")
                        parent.status_label.setStyleSheet("color: red;")
                    # Log to console as fallback
                    logger.error(f"Operation Failed in {class_name}.{func_name}: {e}", exc_info=True)
                
                # Re-raise to trigger global exception handler (HALT)
                if halt_on_error:
                    raise
                
                return default_return
        return wrapper
    return decorator


def safe_worker(halt_on_error: bool = True):
    """
    Decorator for QThread worker run() methods.
    Catches exceptions, emits error signal, and optionally halts app.
    
    Args:
        halt_on_error: Whether to re-raise to halt app (default True)
    
    Usage:
        class MyWorker(QThread):
            error = pyqtSignal(str)
            
            @safe_worker()
            def run(self):
                # worker code - will HALT app on error
                
            @safe_worker(halt_on_error=False)
            def run(self):
                # worker code - will emit error but continue
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                import traceback
                error_msg = f"{type(e).__name__}: {str(e)}"
                full_tb = traceback.format_exc()
                
                # Log with full traceback (will also appear in console via LoggingStream)
                logger.error(
                    f"🛑 WORKER ERROR in {self.__class__.__name__}:\n{full_tb}"
                )
                
                # Emit error signal if available
                if hasattr(self, 'error') and callable(getattr(self.error, 'emit', None)):
                    self.error.emit(error_msg)
                
                # Re-raise to halt application
                if halt_on_error:
                    raise
        return wrapper
    return decorator


def log_exceptions(
    logger_instance: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    reraise: bool = True
):
    """
    Decorator that logs exceptions with full traceback.
    
    Args:
        logger_instance: Logger to use (defaults to module logger)
        level: Logging level for the error
        reraise: Whether to re-raise the exception after logging
    
    Usage:
        @log_exceptions()
        def risky_operation():
            pass
            
        @log_exceptions(reraise=False)
        def optional_operation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger_instance or logger
                log.log(
                    level,
                    f"Exception in {func.__qualname__}: {e}",
                    exc_info=True
                )
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


def handle_db_error(func: Callable) -> Callable:
    """
    Decorator specifically for database operations.
    Handles SQLite errors with specific messaging.
    
    Usage:
        @handle_db_error
        def save_to_database(self, data):
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            
            # Categorize database errors
            if 'sqlite' in error_type.lower() or 'database' in str(e).lower():
                logger.error(f"Database error in {func.__qualname__}: {e}", exc_info=True)
                raise DatabaseError(f"Database operation failed: {e}") from e
            elif 'permission' in str(e).lower() or 'access' in str(e).lower():
                logger.error(f"Permission error in {func.__qualname__}: {e}", exc_info=True)
                raise PermissionError(f"Access denied: {e}") from e
            else:
                logger.error(f"Error in {func.__qualname__}: {e}", exc_info=True)
                raise
    return wrapper


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class AnalysisError(Exception):
    """Custom exception for analysis-related errors."""
    pass


class ScanError(Exception):
    """Custom exception for scan-related errors."""
    pass


def format_error_for_user(error: Exception) -> str:
    """
    Format an exception into a user-friendly message.
    
    Args:
        error: The exception to format
        
    Returns:
        User-friendly error message string
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Simplify common error types
    if 'FileNotFoundError' in error_type:
        return f"File not found: {error_msg}"
    elif 'PermissionError' in error_type:
        return f"Permission denied: {error_msg}"
    elif 'ConnectionError' in error_type or 'Timeout' in error_type:
        return f"Network error: {error_msg}"
    elif 'ValueError' in error_type:
        return f"Invalid value: {error_msg}"
    elif 'DatabaseError' in error_type:
        return f"Database error: {error_msg}"
    else:
        return f"{error_type}: {error_msg}"


def show_error_dialog(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None
):
    """
    Show a standardized error dialog with optional details.
    
    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Main error message
        details: Optional detailed error information
    """
    # Non-modal error display (Phase 48-E-6: Modal banishment)
    # Show in parent's status bar if available, otherwise log
    if parent and hasattr(parent, '_set_status'):
        full_message = f"{message}" + (f"\n{details}" if details else "")
        parent._set_status(full_message, level='error')
    elif parent and hasattr(parent, 'status_label'):
        parent.status_label.setText(f"❌ {message}")
        parent.status_label.setStyleSheet("color: red;")
    else:
        # Fallback: log to console
        logger.critical(f"{title}: {message}" + (f"\n{details}" if details else ""))


def log_function_entry_exit(
    enabled: bool = True,
    log_args: bool = True,
    log_return: bool = True,
    logger_instance: Optional[logging.Logger] = None
):
    """
    Decorator that logs function entry and exit with key variables.
    
    Logs function entry with parameters and exit with return value.
    Uses DEBUG level for entry/exit, ERROR for exceptions.
    Designed to be lightweight with minimal overhead.
    
    Args:
        enabled: Whether to enable logging for this function (default True)
        log_args: Whether to log function arguments (default True)
        log_return: Whether to log return value (default True)
        logger_instance: Logger to use (defaults to module logger)
    
    Usage:
        @log_function_entry_exit()
        def my_function(self, param1, param2):
            return result
            
        @log_function_entry_exit(enabled=False)
        def performance_critical_function(self):
            # No logging overhead
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not enabled:
                return func(*args, **kwargs)
            
            log = logger_instance or logger
            
            # Get function qualname for logging
            func_name = func.__qualname__ if hasattr(func, '__qualname__') else func.__name__
            
            # Log function entry
            if log_args:
                # Format arguments (key variables only - skip 'self' for methods)
                arg_strs = []
                if args:
                    # Skip 'self' for instance methods
                    start_idx = 1 if args and hasattr(args[0], '__class__') and args[0].__class__.__name__ in str(type(args[0])) else 0
                    for i, arg in enumerate(args[start_idx:], start=start_idx):
                        # Truncate long arguments
                        arg_repr = repr(arg)
                        if len(arg_repr) > 100:
                            arg_repr = arg_repr[:97] + "..."
                        arg_strs.append(arg_repr)
                
                # Format keyword arguments
                kwarg_strs = []
                for key, value in kwargs.items():
                    value_repr = repr(value)
                    if len(value_repr) > 100:
                        value_repr = value_repr[:97] + "..."
                    kwarg_strs.append(f"{key}={value_repr}")
                
                all_args = ", ".join(arg_strs + kwarg_strs)
                log.debug(f"[ENTRY] {func_name}({all_args})")
            else:
                log.debug(f"[ENTRY] {func_name}()")
            
            # Execute function and log exit/exception
            try:
                result = func(*args, **kwargs)
                
                # Log function exit
                if log_return:
                    result_repr = repr(result)
                    if len(result_repr) > 200:
                        result_repr = result_repr[:197] + "..."
                    log.debug(f"[EXIT] {func_name} -> {result_repr}")
                else:
                    log.debug(f"[EXIT] {func_name}")
                
                return result
                
            except Exception as e:
                # Log exception with full traceback
                log.error(
                    f"[EXCEPTION] {func_name}: {type(e).__name__}: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def ensure_logging(module_name: str) -> logging.Logger:
    """
    Ensure a module has proper logging configured.
    Returns a logger instance for the module.
    
    Args:
        module_name: Name of the module (typically __name__)
        
    Returns:
        Configured logger instance
    """
    log = logging.getLogger(module_name)
    
    # Ensure we're connected to the master logger
    if not log.handlers and not log.parent:
        # Connect to root logger which should be MasterLogger
        log.parent = logging.getLogger('jelly_rancher_master')
    
    return log

