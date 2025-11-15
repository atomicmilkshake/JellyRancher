"""
Test script to verify help system integration.
Opens UI and checks that help buttons are present in all tabs.
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from jellyfin_ui import JellyfinMainWindow


def test_help_buttons():
    """Test that all tabs have help buttons."""
    print("\n=== Testing Help System Integration ===\n")
    
    app = QApplication(sys.argv)
    window = JellyfinMainWindow()
    
    # Get the central widget (QTabWidget)
    tabs_widget = window.centralWidget()
    tabs = [
        ("Organization", 0),
        ("Subtitles", 1),
        ("Tools", 2),
        ("Analytics", 3),
        ("Settings", 4)
    ]
    
    results = []
    
    try:
        for tab_name, tab_index in tabs:
            try:
                tabs_widget.setCurrentIndex(tab_index)
                QTest.qWait(50)  # Shorter wait
                
                # Find help button in current tab
                current_tab = tabs_widget.currentWidget()
                help_buttons = current_tab.findChildren(QPushButton)
                help_button_found = False
                
                for btn in help_buttons:
                    if "❓" in btn.text() or "Help" in btn.text():
                        help_button_found = True
                        print(f"✅ {tab_name} tab: Help button found - '{btn.text()}'")
                        results.append((tab_name, True))
                        break
                
                if not help_button_found:
                    print(f"❌ {tab_name} tab: No help button found")
                    results.append((tab_name, False))
                    
            except Exception as e:
                print(f"❌ {tab_name} tab: Error - {str(e)}")
                results.append((tab_name, False))
                
    except Exception as e:
        print(f"⚠️  Test loop error: {str(e)}")
    
    finally:
        # Summary
        print("\n=== Test Summary ===")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        print(f"Help buttons working: {passed}/{total}")
        
        if passed == total:
            print("\n✅ ALL TESTS PASSED - Help system fully integrated!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
        
        window.close()
        app.quit()
    
    return passed == total


if __name__ == "__main__":
    try:
        success = test_help_buttons()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
