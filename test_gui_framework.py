#!/usr/bin/env python3
"""
Simple test for GUI automation framework
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from gui_automation_test import GUIAutomationTestSuite, TestScenario

def main():
    print("Testing GUI Automation Framework...")

    try:
        # Create test suite with basic workflow
        suite = GUIAutomationTestSuite(
            scenarios=[TestScenario.BASIC_WORKFLOW],
            verbose=True
        )

        print("✓ Test suite created successfully")

        # Run the test
        results = suite.run_test_suite()

        print("✓ Test suite executed successfully")
        print(f"Results: {results}")

        return 0

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())