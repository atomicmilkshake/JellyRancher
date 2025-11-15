"""
Session-Based Credential Cache

Provides in-memory caching of decrypted credentials for the duration of a session.
Eliminates repeated password prompts while maintaining security.
"""

import os
import atexit
import json
from typing import Dict, Optional
from pathlib import Path
import tempfile


class CredentialCache:
    """
    Singleton credential cache for session-based password management.
    
    Uses temporary file for cross-process session persistence.
    """

    _instance: Optional['CredentialCache'] = None
    _cache: Dict[str, str] = {}
    _session_file: Optional[Path] = None
    _password_file: Optional[Path] = None

    def __new__(cls) -> 'CredentialCache':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_session()
            atexit.register(cls._save_session)
        return cls._instance

    @classmethod
    def _get_password_file(cls) -> Path:
        """Get the password cache file path."""
        if cls._password_file is None:
            # Use system temp directory for password file
            temp_dir = Path(tempfile.gettempdir())
            cls._password_file = temp_dir / "jellyfin_org_password.tmp"
        return cls._password_file

    @classmethod
    def _save_password(cls, password: str) -> None:
        """Save master password to temporary encrypted file."""
        try:
            # Simple obfuscation (not true encryption for temp file)
            import base64
            obfuscated = base64.b64encode(password.encode()).decode()
            cls._get_password_file().write_text(obfuscated)
        except Exception:
            pass  # Ignore errors for temp file

    @classmethod
    def _load_password(cls) -> Optional[str]:
        """Load master password from temporary file."""
        try:
            password_file = cls._get_password_file()
            if password_file.exists():
                import base64
                obfuscated = password_file.read_text()
                return base64.b64decode(obfuscated).decode()
        except Exception:
            pass  # Ignore errors for temp file
        return None

    @classmethod
    def _clear_password_file(cls) -> None:
        """Clear the password cache file."""
        try:
            password_file = cls._get_password_file()
            if password_file.exists():
                password_file.unlink()
        except Exception:
            pass

    @classmethod
    def _get_session_file(cls) -> Path:
        """Get the session file path."""
        if cls._session_file is None:
            # Use system temp directory for session file
            temp_dir = Path(tempfile.gettempdir())
            cls._session_file = temp_dir / "jellyfin_org_session_cache.json"
        return cls._session_file

    @classmethod
    def _load_session(cls) -> None:
        """Load cached credentials from session file."""
        session_file = cls._get_session_file()
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    cls._cache.update(session_data.get('credentials', {}))
                    # Don't load master password from file for security
                print(f"🔄 Session loaded: {len(cls._cache)} cached credentials")
            except Exception as e:
                print(f"⚠️  Could not load session: {e}")
                cls._cache = {}

    @classmethod
    def _save_session(cls) -> None:
        """Save current credentials to session file."""
        session_file = cls._get_session_file()
        try:
            session_data = {
                'credentials': cls._cache.copy(),
                # Don't save master password for security
            }
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
        except Exception as e:
            print(f"⚠️  Could not save session: {e}")

    @classmethod
    def _clear_session(cls) -> None:
        """Clear the session file."""
        session_file = cls._get_session_file()
        if session_file.exists():
            try:
                session_file.unlink()
            except:
                pass

    @classmethod
    def get_credential(cls, key: str) -> Optional[str]:
        """
        Get a credential from cache, initializing if necessary.

        Args:
            key: Credential key (e.g., 'opensubtitles_username')

        Returns:
            Credential value or None if not found
        """
        if not cls._cache:
            try:
                cls._initialize_cache()
            except Exception:
                # If initialization fails, cache remains empty
                return None

        return cls._cache.get(key)

    @classmethod
    def set_credential(cls, key: str, value: str) -> None:
        """
        Store a credential in both cache and encrypted storage.

        Args:
            key: Credential key
            value: Credential value
        """
        if not cls._credential_manager:
            cls._initialize_cache()

        if cls._credential_manager:
            cls._credential_manager.set_credential(key, value)
            cls._cache[key] = value

    @classmethod
    def list_credentials(cls) -> list:
        """
        List all available credential keys.

        Returns:
            List of credential keys
        """
        if not cls._cache:
            cls._initialize_cache()

        return list(cls._cache.keys())

    @classmethod
    def _initialize_cache(cls) -> None:
        """
        Initialize the credential cache by loading from encrypted storage.
        """
        try:
            # Import here to avoid circular imports
            try:
                from .credential_manager import CredentialManager
            except ImportError:
                from credential_manager import CredentialManager

            # Try to load cached password first
            cached_password = cls._load_password()
            
            if cached_password:
                print("🔑 Using cached master password...")
                # Create credential manager with cached password
                cls._credential_manager = CredentialManager(password=cached_password)
            else:
                # No cached password, will prompt user
                cls._credential_manager = CredentialManager()
                # Cache the password for future use
                if hasattr(cls._credential_manager, 'password'):
                    cls._save_password(cls._credential_manager.password)

            # Load all credentials into cache
            encrypted_creds = cls._credential_manager._load_credentials()
            cls._cache.update(encrypted_creds)

            # Save session immediately after loading
            cls._save_session()

            print(f"🔓 Credential cache initialized ({len(cls._cache)} credentials loaded)")

        except Exception as e:
            print(f"❌ Failed to initialize credential cache: {e}")
            cls._cache = {}
            raise

    @classmethod
    def _clear_cache(cls) -> None:
        """
        Clear all cached credentials.
        Called automatically on application exit.
        """
        cls._cache.clear()
        cls._clear_session()
        print("🔒 Credential cache cleared")

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if the credential cache has been initialized.

        Returns:
            True if cache is ready, False otherwise
        """
        return bool(cls._cache)

    @classmethod
    def get_session_status(cls) -> Dict[str, any]:
        """
        Get current session status.

        Returns:
            Dictionary with cache status information
        """
        return {
            'cache_initialized': cls.is_initialized(),
            'credentials_cached': len(cls._cache),
            'session_file_exists': cls._get_session_file().exists()
        }


# Convenience functions for easy access
def get_credential(key: str) -> Optional[str]:
    """Get a credential from the session cache."""
    return CredentialCache.get_credential(key)

def set_credential(key: str, value: str) -> None:
    """Store a credential in the session cache and encrypted storage."""
    CredentialCache.set_credential(key, value)

def list_credentials() -> list:
    """List all available credential keys."""
    return CredentialCache.list_credentials()

def get_cache_status() -> Dict[str, any]:
    """Get current credential cache status."""
    return CredentialCache.get_session_status()