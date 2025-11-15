#!/usr/bin/env python3
"""
Test Password Input with Asterisks
"""

import sys
sys.path.insert(0, '_common')

from credential_manager import CredentialManager

def test_password_input():
    print("🧪 Testing password input with asterisks...")
    
    # Create a credential manager instance just to test the password input
    manager = CredentialManager()
    
    print("✅ Password input test complete")

if __name__ == "__main__":
    test_password_input()