#!/usr/bin/env python3
"""
Simple Real GUI Test Runner
Tests if real GUI automation works with pywinauto
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("Testing Real GUI Automation Setup")
    print("=" * 40)

    # Check if pywinauto is available
    try:
        import pywinauto
        print("✓ pywinauto is available")
    except ImportError:
        print("✗ pywinauto not found - installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywinauto"])
            print("✓ pywinauto installed successfully")
            import pywinauto
        except Exception as e:
            print(f"✗ Failed to install pywinauto: {e}")
            return 1

    # Test basic GUI automation
    try:
        from pywinauto import Application, Desktop
        print("✓ pywinauto imports successful")

        # Try to get desktop
        desktop = Desktop(backend="uia")
        print("✓ Desktop connection successful")

    except Exception as e:
        print(f"✗ pywinauto setup failed: {e}")
        return 1

    print("\nRunning basic GUI automation test...")
    print("This will launch JellyRancher Studio and test basic interactions")

    try:
        # Import test suite
        sys.path.insert(0, str(Path(__file__).parent))
        from gui_automation_test import GUIAutomationTestSuite, TestScenario

        # Run just basic workflow test
        suite = GUIAutomationTestSuite(
            scenarios=[TestScenario.BASIC_WORKFLOW],
            verbose=True
        )

        results = suite.run_test_suite()

        print("\n" + "=" * 40)
        print("BASIC REAL GUI TEST RESULTS")
        print("=" * 40)
        print(f"Success: {'PASS' if results['success'] else 'FAIL'}")
        print(f"Duration: {results.get('suite_duration_seconds', 0):.2f}s")
        print(f"Scenarios Run: {results.get('scenarios_run', 0)}")
        print(f"Scenarios Passed: {results.get('scenarios_passed', 0)}")
        print(f"Scenarios Failed: {results.get('scenarios_failed', 0)}")

        return 0 if results['success'] else 1

    except Exception as e:
        print(f"✗ Real GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())