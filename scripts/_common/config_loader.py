"""
Configuration Loader for Jellyfin Organizer
Provides centralized access to all configuration settings from config.json
"""

import json
from pathlib import Path
from typing import Dict, List, Any

import logging
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Gets the project root directory (assumed to be parent of 'scripts')."""
    return Path(__file__).parent.parent.parent.resolve()


def load_config() -> Dict[str, Any]:
    """
    Loads the central config.json file from the project root.

    Returns:
        Dictionary containing all configuration settings

    Raises:
        FileNotFoundError: If config.json cannot be found
        json.JSONDecodeError: If config.json is malformed
    """
    config_path = get_project_root() / 'config.json'
    if not config_path.exists():
        raise FileNotFoundError(
            f"Could not find config.json at project root: {config_path}\n"
            f"Please create config.json in the project root directory."
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def get_project_path(config_key: str) -> Path:
    """
    Gets a path from the config relative to the project root.

    Args:
        config_key: Key from the 'project_paths' section of config.json
                   Valid keys: tv_cache, reports, audit_logs, operation_logs,
                               ravenmaven_root, ravenmaven_lists

    Returns:
        Resolved Path object for the requested configuration key

    Raises:
        KeyError: If config_key is not found in configuration
    """
    config = load_config()
    root = get_project_root()

    # Special cases: paths relative to the 'scripts' directory
    if config_key == 'tv_cache':
        scripts_root = root / 'scripts'
        return scripts_root / config['project_paths']['tv_cache']

    if config_key == 'reports':
        scripts_root = root / 'scripts'
        return scripts_root / config['project_paths']['reports']

    if config_key == 'audit_logs':
        # audit-logs is at the project root
        return root / config['project_paths']['audit_logs']

    if config_key == 'operation_logs':
        # logs is at the project root
        return root / config['project_paths']['operation_logs']

    # External paths (like ravenmaven) - use as absolute paths
    if config_key in ['ravenmaven_root', 'ravenmaven_lists']:
        return Path(config['project_paths'][config_key])

    # Default behavior for other paths
    return root / config['project_paths'].get(config_key, config_key)


def get_media_paths(media_type: str) -> List[Path]:
    """
    Gets all media paths for a specific media type.

    Args:
        media_type: Type of media ('movies' or 'tv_shows')

    Returns:
        List of Path objects for the requested media type

    Raises:
        KeyError: If media_type is not found in configuration
    """
    config = load_config()
    paths = config['media_paths'][media_type]
    return [Path(p) for p in paths]


def get_executor_path(executor_name: str) -> Path:
    """
    Gets the path to an executor script.

    Args:
        executor_name: Name of the executor ('safe_executor', 'batch_processor', 'prompt_file')

    Returns:
        Path object for the requested executor

    Raises:
        KeyError: If executor_name is not found in configuration
    """
    config = load_config()
    return Path(config['executor_paths'][executor_name])


def get_openmemory_config() -> Dict[str, str]:
    """
    Gets OpenMemory configuration settings.

    Returns:
        Dictionary with 'backend_dir' and 'url' keys
    """
    config = load_config()
    return config['openmemory']


# Convenience functions for common paths
def get_tv_cache_dir() -> Path:
    """Get the TV episode cache directory."""
    return get_project_path('tv_cache')


def get_reports_dir() -> Path:
    """Get the reports directory."""
    return get_project_path('reports')


def get_audit_logs_dir() -> Path:
    """Get the audit logs directory."""
    return get_project_path('audit_logs')


if __name__ == "__main__":
    # Test the configuration loader
    import sys
    # Set console to UTF-8 for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    logger.info("Configuration Loader Test")
    logger.info("=" * 60)

    try:
        config = load_config()
        logger.info("[OK] Configuration loaded successfully")
        logger.info(f"\nProject Root: {get_project_root()}")
        logger.info(f"\nTV Cache Dir: {get_tv_cache_dir()}")
        logger.info(f"Reports Dir: {get_reports_dir()}")
        logger.info(f"Audit Logs Dir: {get_audit_logs_dir()}")

        logger.info("\nMovie Paths:")
        for path in get_media_paths('movies'):
            logger.info(f"  - {path}")

        logger.info("\nTV Show Paths:")
        for path in get_media_paths('tv_shows'):
            logger.info(f"  - {path}")

        logger.info("\nExecutor Paths:")
        logger.info(f"  - Safe Executor: {get_executor_path('safe_executor')}")
        logger.info(f"  - Batch Processor: {get_executor_path('batch_processor')}")

        logger.info("\nOpenMemory Config:")
        om_config = get_openmemory_config()
        logger.info(f"  - Backend Dir: {om_config['backend_dir']}")
        logger.info(f"  - URL: {om_config['url']}")

        logger.info("\n[OK] All configuration tests passed!")

    except Exception as e:
        logger.info(f"\n[ERROR] Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
