#!/usr/bin/env python3
"""
Simple test runner for GUI automation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gui_automation_test import GUIAutomationTestSuite, TestScenario

if __name__ == "__main__":
    print("Starting GUI Automation Test Suite...")

    try:
        suite = GUIAutomationTestSuite(
            scenarios=[
                TestScenario.BASIC_WORKFLOW,
                TestScenario.SLOW_USER,
                TestScenario.FAST_USER,
                TestScenario.INTERRUPTED_WORKFLOW,
                TestScenario.ERROR_RECOVERY,
                TestScenario.ALTERNATIVE_PATHS
            ],
            verbose=True
        )

        results = suite.run_test_suite()

        print("\n" + "="*60)
        print("RESULTS SUMMARY")
        print("="*60)
        print(f"Success: {'YES' if results['success'] else 'NO'}")
        print(f"Scenarios Run: {results.get('scenarios_run', 0)}")
        print(f"Scenarios Passed: {results.get('scenarios_passed', 0)}")
        print(f"Scenarios Failed: {results.get('scenarios_failed', 0)}")
        print(f"Total Interactions: {results.get('total_gui_interactions', 0)}")
        print(f"Total Errors: {results.get('total_errors', 0)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()