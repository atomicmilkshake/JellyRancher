#!/usr/bin/env python3
"""
Direct execution of GUI automation test suite
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("🚀 Starting GUI Automation Test Suite - All Scenarios")
print("=" * 60)

try:
    from gui_automation_test import GUIAutomationTestSuite, TestScenario

    # Run all scenarios
    all_scenarios = [
        TestScenario.BASIC_WORKFLOW,
        TestScenario.SLOW_USER,
        TestScenario.FAST_USER,
        TestScenario.INTERRUPTED_WORKFLOW,
        TestScenario.ERROR_RECOVERY,
        TestScenario.ALTERNATIVE_PATHS
    ]

    print(f"Running {len(all_scenarios)} scenarios:")
    for scenario in all_scenarios:
        print(f"  • {scenario.value}")
    print()

    # Create and run test suite
    suite = GUIAutomationTestSuite(
        scenarios=all_scenarios,
        verbose=True
    )

    results = suite.run_test_suite()

    # Print final summary
    print("\n" + "=" * 60)
    print("🎭 GUI AUTOMATION TEST SUITE RESULTS")
    print("=" * 60)
    print(f"Success: {'✓' if results['success'] else '✗'}")
    print(f"Duration: {results.get('suite_duration_seconds', 'N/A'):.2f}s")
    print(f"Scenarios Run: {results.get('scenarios_run', 0)}")
    print(f"Scenarios Passed: {results.get('scenarios_passed', 0)}")
    print(f"Scenarios Failed: {results.get('scenarios_failed', 0)}")
    print(f"Total GUI Interactions: {results.get('total_gui_interactions', 0)}")
    print(f"Total Errors: {results.get('total_errors', 0)}")
    if 'report_file' in results:
        print(f"Report: {results['report_file']}")
    print("=" * 60)

    print("\n✅ TEST EXECUTION COMPLETED")
    print("Check the generated log and report files for detailed results.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)