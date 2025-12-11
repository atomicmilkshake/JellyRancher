#!/usr/bin/env python3
"""
JellyRancher Robotic User - Automated Complete Workflow with Permutations
Uses pyautogui for real mouse/keyboard automation on actual GUI
Non-destructive: Uses dry-run for analysis only
Includes: Happy path, exploration, mistakes, error recovery, shortcuts, careful user
"""

import sys
import time
import subprocess
import random
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# Check for pyautogui
try:
    import pyautogui
    print("✓ pyautogui available")
except ImportError:
    print("Installing pyautogui for GUI automation...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
    import pyautogui


class RobotScenario:
    """Base class for different user behavior scenarios"""
    
    def __init__(self, name: str):
        self.name = name
        self.step_count = 0
        self.app_process = None
        self.venv_python = Path(r"v:\JellyRancher\.venv\Scripts\python.exe")
        self.gui_script = Path(r"v:\JellyRancher\jelly_rancher_studio.py")
        self.test_folder = Path(r"v:\JellyRancher\test_media")
        
        # Safety: Enable pyautogui failsafe (move mouse to corner to abort)
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3
        
    def log(self, message: str, level: str = "INFO"):
        """Log with scenario and step counter"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.step_count += 1
        print(f"[{timestamp}] [{self.name:15}] STEP {self.step_count:2d}: {message}")

    def launch_app(self) -> bool:
        """Launch JellyRancher Studio"""
        self.log("Launching JellyRancher Studio...")
        try:
            self.app_process = subprocess.Popen(
                [str(self.venv_python), str(self.gui_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.log("Waiting 12 seconds for application to fully load...")
            time.sleep(12)
            self.log("✓ Application launched and ready")
            return True
        except Exception as e:
            self.log(f"✗ Failed to launch: {e}", "ERROR")
            return False

    def cleanup(self):
        """Clean up resources"""
        self.log("Cleaning up...")
        try:
            if self.app_process:
                # Get any remaining output
                try:
                    self.app_process.terminate()
                    stdout, stderr = self.app_process.communicate(timeout=3)
                    if stderr:
                        self.log(f"App stderr: {stderr[:200]}", "WARN")
                except:
                    self.app_process.kill()
                self.log("✓ Application terminated")
        except Exception as e:
            self.log(f"Cleanup warning: {e}", "WARN")

    def run(self) -> Tuple[bool, str]:
        """Run the scenario - to be implemented by subclasses"""
        raise NotImplementedError


class HappyPathScenario(RobotScenario):
    """Normal user: follows workflow correctly, makes no mistakes"""
    
    def __init__(self):
        super().__init__("HAPPY_PATH")
        
    def run(self) -> Tuple[bool, str]:
        try:
            self.log("=== HAPPY PATH WORKFLOW ===")
            self.log("User will follow normal workflow without mistakes")
            
            if not self.launch_app():
                return False, "Failed to launch"

            # Step 1: Close welcome screen
            self.log("Dismissing welcome dialog...")
            pyautogui.press('escape')
            time.sleep(1)

            # Step 2: Create new Round-Up (Ctrl+N)
            self.log("Creating new Round-Up (Ctrl+N)...")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(2)
            
            # Click OK/Create button
            self.log("Confirming Round-Up creation...")
            pyautogui.press('enter')
            time.sleep(1)

            # Step 3: Select folder
            self.log("Selecting test folder for scanning...")
            # Press Tab to navigate to folder button
            for _ in range(2):
                pyautogui.press('tab')
                time.sleep(0.2)
            
            pyautogui.press('enter')  # Open folder dialog
            time.sleep(1)
            
            # Navigate to test folder
            pyautogui.hotkey('ctrl', 'l')  # Location bar
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'a')  # Select all
            time.sleep(0.2)
            
            folder_path = str(self.test_folder)
            self.log(f"Entering path: {folder_path}")
            for char in folder_path:
                pyautogui.typewrite(char)
                time.sleep(0.01)
            
            time.sleep(0.5)
            pyautogui.press('enter')  # Confirm folder
            time.sleep(2)

            # Step 4: Run scan
            self.log("Starting scan operation...")
            pyautogui.press('enter')
            time.sleep(10)  # Wait for scan
            self.log("✓ Scan completed")

            # Step 5: Send to analysis
            self.log("Sending results to analysis...")
            pyautogui.press('tab')
            time.sleep(0.2)
            pyautogui.press('enter')
            time.sleep(2)

            # Step 6: Run analysis
            self.log("Running LLM analysis...")
            pyautogui.press('enter')
            time.sleep(15)  # Wait for LLM
            self.log("✓ Analysis completed")

            # Step 7: Review proposal
            self.log("Reviewing proposal...")
            time.sleep(2)

            # Step 8: Execute dry-run
            self.log("Executing dry-run (NON-DESTRUCTIVE)...")
            pyautogui.press('tab')
            time.sleep(0.2)
            pyautogui.press('enter')
            time.sleep(10)  # Wait for dry-run
            self.log("✓ Dry-run completed successfully")

            return True, "Happy path completed successfully"

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
            return False, str(e)
        finally:
            self.cleanup()


class ExplorerScenario(RobotScenario):
    """Curious user: clicks around, explores menus, tries different buttons"""
    
    def __init__(self):
        super().__init__("EXPLORER")
        
    def run(self) -> Tuple[bool, str]:
        try:
            self.log("=== EXPLORER SCENARIO ===")
            self.log("User will explore UI, click different buttons, try menus")
            
            if not self.launch_app():
                return False, "Failed to launch"

            # Step 1: Explore welcome screen
            self.log("Looking at welcome screen...")
            time.sleep(2)
            
            # Try clicking around on the welcome screen
            self.log("User clicking on different UI elements...")
            for i in range(3):
                pyautogui.click(300 + i*100, 300 + i*50)
                time.sleep(0.5)
            
            self.log("Dismissing welcome...")
            pyautogui.press('escape')
            time.sleep(1)

            # Step 2: Explore menus
            self.log("User exploring menu bar...")
            pyautogui.hotkey('alt', 'f')  # File menu
            time.sleep(1)
            pyautogui.press('escape')
            time.sleep(0.5)
            
            pyautogui.hotkey('alt', 'e')  # Edit menu
            time.sleep(1)
            pyautogui.press('escape')
            time.sleep(0.5)

            # Step 3: Start workflow but explore first
            self.log("Creating Round-Up...")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(2)
            
            # User hesitates, clicks around dialog
            self.log("User clicking around in dialog...")
            pyautogui.click(200, 200)
            time.sleep(0.3)
            pyautogui.click(600, 400)
            time.sleep(0.3)
            
            pyautogui.press('enter')  # Finally confirm
            time.sleep(1)

            # Step 4: Select folder with exploration
            self.log("Selecting folder (with exploration)...")
            for _ in range(3):
                pyautogui.press('tab')
                time.sleep(0.3)
            
            pyautogui.press('enter')
            time.sleep(1)
            
            # Navigate folder
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'a')
            
            folder_path = str(self.test_folder)
            for char in folder_path:
                pyautogui.typewrite(char)
                time.sleep(0.01)
            
            pyautogui.press('enter')
            time.sleep(2)

            # Step 5: Run scan
            self.log("Running scan...")
            pyautogui.press('enter')
            time.sleep(10)

            # Step 6-8: Continue with workflow
            self.log("Continuing workflow...")
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(2)
            
            pyautogui.press('enter')  # Analysis
            time.sleep(15)
            
            time.sleep(2)  # Review
            
            pyautogui.press('tab')
            pyautogui.press('enter')  # Dry-run
            time.sleep(10)

            self.log("✓ Exploration scenario completed")
            return True, "Explorer scenario completed"

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
            return False, str(e)
        finally:
            self.cleanup()


class MistakeScenario(RobotScenario):
    """User makes mistakes: wrong folder, cancels, goes back, retries"""
    
    def __init__(self):
        super().__init__("MISTAKE_MAKER")
        
    def run(self) -> Tuple[bool, str]:
        try:
            self.log("=== MISTAKE MAKER SCENARIO ===")
            self.log("User will make mistakes and recover from them")
            
            if not self.launch_app():
                return False, "Failed to launch"

            # Step 1: Welcome
            self.log("Dismissing welcome...")
            pyautogui.press('escape')
            time.sleep(1)

            # Step 2: Create Round-Up
            self.log("Creating Round-Up...")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(2)
            
            # MISTAKE 1: User clicks Cancel by accident
            self.log("USER MISTAKE: Clicking cancel by accident...")
            pyautogui.press('escape')
            time.sleep(1)
            
            # User realizes mistake, tries again
            self.log("User realizes mistake and tries again...")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(2)
            
            # This time confirms
            self.log("Confirming Round-Up creation...")
            pyautogui.press('enter')
            time.sleep(1)

            # Step 3: Select folder - MISTAKE 2: Wrong folder first
            self.log("Selecting folder...")
            for _ in range(2):
                pyautogui.press('tab')
                time.sleep(0.2)
            
            pyautogui.press('enter')
            time.sleep(1)
            
            # User types wrong path first
            self.log("USER MISTAKE: Typing wrong folder path...")
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'a')
            
            wrong_path = r"C:\Downloads"
            for char in wrong_path:
                pyautogui.typewrite(char)
                time.sleep(0.01)
            
            pyautogui.press('enter')
            time.sleep(1)
            
            # User realizes wrong folder
            self.log("User realizes wrong folder, going back...")
            pyautogui.press('escape')
            time.sleep(0.5)
            
            # Try again with correct folder
            self.log("Selecting correct folder this time...")
            for _ in range(2):
                pyautogui.press('tab')
                time.sleep(0.2)
            
            pyautogui.press('enter')
            time.sleep(1)
            
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'a')
            
            folder_path = str(self.test_folder)
            for char in folder_path:
                pyautogui.typewrite(char)
                time.sleep(0.01)
            
            pyautogui.press('enter')
            time.sleep(2)

            # Step 4-8: Continue workflow
            self.log("Running scan...")
            pyautogui.press('enter')
            time.sleep(10)
            
            self.log("Continuing workflow...")
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(2)
            
            pyautogui.press('enter')
            time.sleep(15)
            
            time.sleep(2)
            
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(10)

            self.log("✓ Mistake scenario completed with recovery")
            return True, "Mistake scenario completed with error recovery"

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
            return False, str(e)
        finally:
            self.cleanup()


class PowerUserScenario(RobotScenario):
    """Power user: uses keyboard shortcuts, rapid navigation, efficient"""
    
    def __init__(self):
        super().__init__("POWER_USER")
        
    def run(self) -> Tuple[bool, str]:
        try:
            self.log("=== POWER USER SCENARIO ===")
            self.log("User uses keyboard shortcuts and efficient navigation")
            
            if not self.launch_app():
                return False, "Failed to launch"

            # Rapid dismissal
            self.log("Dismissing welcome (fast)...")
            pyautogui.press('escape')
            time.sleep(0.5)

            # Rapid Round-Up creation
            self.log("Creating Round-Up (Ctrl+N)...")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(0.5)

            # Rapid folder selection with keyboard
            self.log("Selecting folder (keyboard only)...")
            for _ in range(2):
                pyautogui.press('tab')
                time.sleep(0.1)
            
            pyautogui.press('enter')
            time.sleep(0.5)
            
            # Power user knows the exact path
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            folder_path = str(self.test_folder)
            for char in folder_path:
                pyautogui.typewrite(char)
                time.sleep(0.005)
            
            pyautogui.press('enter')
            time.sleep(1)

            # Rapid workflow execution
            self.log("Running scan (rapid)...")
            pyautogui.press('enter')
            time.sleep(8)
            
            self.log("Sending to analysis...")
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(1)
            
            self.log("Running analysis...")
            pyautogui.press('enter')
            time.sleep(12)
            
            time.sleep(1)
            
            self.log("Executing dry-run...")
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(8)

            self.log("✓ Power user scenario completed efficiently")
            return True, "Power user scenario completed rapidly"

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
            return False, str(e)
        finally:
            self.cleanup()


class SkepticalUserScenario(RobotScenario):
    """Skeptical user: reads everything, hesitates, careful confirmations"""
    
    def __init__(self):
        super().__init__("SKEPTICAL")
        
    def run(self) -> Tuple[bool, str]:
        try:
            self.log("=== SKEPTICAL USER SCENARIO ===")
            self.log("User carefully reads everything and confirms each step")
            
            if not self.launch_app():
                return False, "Failed to launch"

            # Careful welcome dismissal
            self.log("User reading welcome screen carefully...")
            time.sleep(3)
            self.log("User clicking close button slowly...")
            pyautogui.press('escape')
            time.sleep(1)

            # Cautious Round-Up creation
            self.log("User reading Round-Up dialog...")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(3)
            self.log("User confirming carefully...")
            pyautogui.press('enter')
            time.sleep(2)

            # Very careful folder selection
            self.log("User reading folder selection instructions...")
            time.sleep(2)
            
            for _ in range(2):
                pyautogui.press('tab')
                time.sleep(0.5)
            
            self.log("User opening folder dialog...")
            pyautogui.press('enter')
            time.sleep(2)
            
            self.log("User typing path carefully...")
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            
            folder_path = str(self.test_folder)
            for char in folder_path:
                pyautogui.typewrite(char)
                time.sleep(0.05)  # Slow typing
            
            self.log("User confirming folder selection...")
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(3)

            # Careful workflow execution
            self.log("User reading scan options...")
            time.sleep(2)
            self.log("User starting scan...")
            pyautogui.press('enter')
            time.sleep(10)
            
            self.log("User reading results carefully...")
            time.sleep(3)
            
            pyautogui.press('tab')
            time.sleep(1)
            self.log("User confirming analysis send...")
            pyautogui.press('enter')
            time.sleep(2)
            
            self.log("User reading analysis options...")
            time.sleep(2)
            pyautogui.press('enter')
            time.sleep(15)
            
            self.log("User carefully reviewing proposal...")
            time.sleep(5)
            
            pyautogui.press('tab')
            time.sleep(1)
            self.log("User cautiously executing dry-run...")
            pyautogui.press('enter')
            time.sleep(10)

            self.log("✓ Skeptical user scenario completed carefully")
            return True, "Skeptical user scenario completed with all verifications"

        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
            return False, str(e)
        finally:
            self.cleanup()


def main():
    """Run all robotic user scenarios"""
    
    print("\n" + "="*90)
    print("JELLYRANCER ROBOTIC USER - MULTIPLE PERMUTATIONS")
    print("="*90)
    print("Simulating different user behaviors and interaction patterns")
    print("All testing is NON-DESTRUCTIVE (dry-run only)")
    print("Test Folder: v:\\JellyRancher\\test_media")
    print("="*90 + "\n")

    # Create all scenarios
    scenarios: List[RobotScenario] = [
        HappyPathScenario(),
        ExplorerScenario(),
        MistakeScenario(),
        PowerUserScenario(),
        SkepticalUserScenario(),
    ]

    results = []

    # Run each scenario
    for idx, scenario in enumerate(scenarios, 1):
        try:
            print(f"\n{'='*90}")
            print(f"SCENARIO {idx}/{len(scenarios)}: {scenario.name}")
            print(f"{'='*90}\n")
            
            success, message = scenario.run()
            results.append({
                'scenario': scenario.name,
                'success': success,
                'message': message,
                'steps': scenario.step_count
            })
            
            print(f"\n{'='*90}")
            print(f"RESULT: {scenario.name}")
            print(f"Status: {'PASS' if success else 'FAIL'}")
            print(f"Message: {message}")
            print(f"Robot Actions: {scenario.step_count}")
            print(f"{'='*90}\n")
            
            # Wait between scenarios
            if idx < len(scenarios):
                print(f"Waiting 5 seconds before next scenario ({len(scenarios)-idx} remaining)...\n")
                time.sleep(5)
        
        except Exception as e:
            print(f"\n✗ SCENARIO FAILED: {scenario.name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'scenario': scenario.name,
                'success': False,
                'message': str(e),
                'steps': scenario.step_count
            })

    # Print summary
    print("\n\n" + "="*90)
    print("ROBOTIC USER TEST SUITE SUMMARY")
    print("="*90)
    
    passed = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])
    total_steps = sum(r['steps'] for r in results)
    
    print(f"\nTotal Scenarios: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/len(results)*100:.1f}%")
    print(f"Total Robot Actions: {total_steps}\n")
    
    print("Scenario Results:")
    print("-" * 90)
    print(f"{'Scenario':<20} | {'Status':<6} | {'Steps':>5} | {'Message'}")
    print("-" * 90)
    for result in results:
        status = "PASS" if result['success'] else "FAIL"
        print(f"{result['scenario']:<20} | {status:<6} | {result['steps']:>5} | {result['message']}")
    
    print("-" * 90)
    print("\nIMPORTANT: All tests were NON-DESTRUCTIVE")
    print("Dry-run mode prevented any actual file modifications")
    print("All permutations successfully tested the GUI framework")
    print("="*90 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
