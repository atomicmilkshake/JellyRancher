"""
Encrypted Credential Management System

Securely stores subtitle service credentials using Fernet (symmetric encryption).
Master password is prompted at runtime or optionally read from environment variable.

Features:
- Fernet encryption (AES-128 in CBC mode)
- PBKDF2 key derivation from master password
- Credential storage in binary encrypted file
- No plaintext credentials in memory after encryption

Usage:
    from _common.credential_manager import CredentialManager
    
    # Initialize (prompts for master password, or reads from JELLYFIN_ORG_PASSWORD env var)
    creds = CredentialManager()
    
    # Store subtitle service credentials (first time)
    creds.set_credential("opensubtitles_username", "your_username")
    creds.set_credential("opensubtitles_password", "your_password")
    
    # Retrieve credentials
    username = creds.get_credential("opensubtitles_username")
    password = creds.get_credential("opensubtitles_password")
    
    # List stored credentials
    keys = creds.list_credentials()
"""

import os
import json
import base64
import getpass
from pathlib import Path
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialManager:
    """
    Manages encrypted storage of subtitle service credentials.
    
    Uses Fernet encryption with PBKDF2 key derivation from a master password.
    Credentials are stored in a binary encrypted file (._state/credentials.enc).
    """
    
    ENV_VAR_NAME = "JELLYFIN_ORG_PASSWORD"
    DEFAULT_CRED_FILE = Path("._state/credentials.enc")
    SALT_FILE = Path("._state/credentials.salt")
    
    def __init__(self, 
                 password: Optional[str] = None,
                 credential_file: Optional[Path] = None):
        """
        Initialize credential manager.
        
        Args:
            password: Master password (if None, prompts user or reads from env var)
            credential_file: Path to encrypted credential file (default: ._state/credentials.enc)
        """
        self.credential_file = credential_file or self.DEFAULT_CRED_FILE
        self.salt_file = self.SALT_FILE
        
        # Get master password
        if password is None:
            password = self._get_master_password()
        
        self.password = password
        self._ensure_state_directory()
        self._initialize_encryption()
    
    def _get_master_password(self) -> str:
        """
        Retrieve master password from environment variable (optional) or prompt user.
        
        Returns:
            Master password string
        """
        # Try environment variable first (optional convenience)
        password = os.environ.get(self.ENV_VAR_NAME)
        
        if password:
            print(f"[KEY] Master password loaded from {self.ENV_VAR_NAME} environment variable")
            return password
        
        # Prompt user (normal workflow)
        print(f"[KEY] Enter master password to decrypt credential store")
        print(f"    (Optional: Set {self.ENV_VAR_NAME} environment variable to skip prompt)")
        # User prefers visible asterisk-like hint; actual input remains hidden for safety
        password = self._get_password_with_mask("Master password (typing is active; characters will not be shown): ")
        
        if not password:
            raise ValueError("Master password cannot be empty")
        
        return password
    
    def _get_password_with_mask(self, prompt: str) -> str:
        """
        Get password input with asterisk masking.
        
        Args:
            prompt: The prompt to display
            
        Returns:
            The entered password
        """
        import msvcrt
        import sys
        
        print(prompt, end='', flush=True)
        
        password = ""
        while True:
            char = msvcrt.getch()
            
            # Enter key
            if char == b'\r' or char == b'\n':
                print()  # New line
                break
            
            # Backspace
            elif char == b'\x08':  # Backspace
                if password:
                    password = password[:-1]
                    # Move cursor back, print space, move cursor back again
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            
            # Regular character
            else:
                try:
                    char_str = char.decode('utf-8')
                    password += char_str
                    sys.stdout.write('*')
                    sys.stdout.flush()
                except UnicodeDecodeError:
                    # Skip invalid characters
                    pass
        
        return password
    
    def _ensure_state_directory(self) -> None:
        """Create ._state directory if it doesn't exist."""
        self.credential_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_encryption(self) -> None:
        """
        Initialize Fernet encryption with key derived from master password.
        
        Uses PBKDF2 with 100,000 iterations for key derivation.
        Salt is stored separately and reused for consistent key generation.
        """
        # Load or generate salt
        if self.salt_file.exists():
            with open(self.salt_file, 'rb') as f:
                salt = f.read()
        else:
            salt = os.urandom(16)  # 16-byte salt
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            print(f"🔐 Created new encryption salt: {self.salt_file}")
        
        # Derive key from password using PBKDF2HMAC
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode('utf-8')))
        
        # Initialize Fernet
        self.fernet = Fernet(key)
    
    def _load_credentials(self) -> Dict[str, str]:
        """
        Load and decrypt credentials from file.
        
        Returns:
            Dictionary of credential key-value pairs
        """
        if not self.credential_file.exists():
            return {}
        
        try:
            with open(self.credential_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode('utf-8'))
            return credentials
        
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials. Wrong password? Error: {e}")
    
    def _save_credentials(self, credentials: Dict[str, str]) -> None:
        """
        Encrypt and save credentials to file.
        
        Args:
            credentials: Dictionary of credential key-value pairs
        """
        # Encrypt credentials
        credentials_json = json.dumps(credentials)
        encrypted_data = self.fernet.encrypt(credentials_json.encode('utf-8'))
        
        # Save to file
        with open(self.credential_file, 'wb') as f:
            f.write(encrypted_data)
    
    def set_credential(self, key: str, value: str) -> None:
        """
        Store an encrypted credential.
        
        Args:
            key: Credential identifier (e.g., "opensubtitles_username")
            value: Credential value (e.g., username, password, API key)
        
        Example:
            creds.set_credential("opensubtitles_username", "myusername")
            creds.set_credential("opensubtitles_password", "mypassword")
        """
        credentials = self._load_credentials()
        credentials[key] = value
        self._save_credentials(credentials)
        print(f"✅ Credential stored: {key}")
    
    def get_credential(self, key: str) -> Optional[str]:
        """
        Retrieve a decrypted credential.
        
        Args:
            key: Credential identifier
        
        Returns:
            Decrypted credential value, or None if not found
        
        Example:
            username = creds.get_credential("opensubtitles_username")
            password = creds.get_credential("opensubtitles_password")
        """
        credentials = self._load_credentials()
        return credentials.get(key)
    
    def delete_credential(self, key: str) -> bool:
        """
        Delete a stored credential.
        
        Args:
            key: Credential identifier
        
        Returns:
            True if credential was deleted, False if not found
        """
        credentials = self._load_credentials()
        if key in credentials:
            del credentials[key]
            self._save_credentials(credentials)
            print(f"✅ Credential deleted: {key}")
            return True
        return False
    
    def list_credentials(self) -> List[str]:
        """
        List all stored credential keys (not values).
        
        Returns:
            List of credential identifiers
        """
        credentials = self._load_credentials()
        return list(credentials.keys())
    
    def credential_exists(self, key: str) -> bool:
        """
        Check if a credential exists.
        
        Args:
            key: Credential identifier
        
        Returns:
            True if credential exists, False otherwise
        """
        credentials = self._load_credentials()
        return key in credentials


# Standalone CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python credential_manager.py <command> [args]")
        print("Commands:")
        print("  set <key> <value>  - Store a credential")
        print("  get <key>          - Retrieve a credential")
        print("  delete <key>       - Delete a credential")
        print("  list               - List all credential keys")
        print("\nCommon credential keys:")
        print("  opensubtitles_username")
        print("  opensubtitles_password")
        print("  opensubtitles_com_username  (if using opensubtitles.com)")
        print("  opensubtitles_com_password")
        sys.exit(1)
    
    command = sys.argv[1]
    creds = CredentialManager()
    
    if command == "set":
        if len(sys.argv) < 4:
            print("Usage: python credential_manager.py set <key> <value>")
            sys.exit(1)
        key = sys.argv[2]
        value = sys.argv[3]
        creds.set_credential(key, value)
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: python credential_manager.py get <key>")
            sys.exit(1)
        key = sys.argv[2]
        value = creds.get_credential(key)
        if value:
            print(f"{key}: {value}")
        else:
            print(f"❌ Credential not found: {key}")
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: python credential_manager.py delete <key>")
            sys.exit(1)
        key = sys.argv[2]
        if creds.delete_credential(key):
            print(f"✅ Deleted: {key}")
        else:
            print(f"❌ Not found: {key}")
    
    elif command == "list":
        keys = creds.list_credentials()
        print(f"📋 Stored credentials ({len(keys)}):")
        for key in keys:
            print(f"   - {key}")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)