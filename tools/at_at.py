#!/usr/bin/env python3
"""
AT-AT: Autonomous Testing - Automated Traversal
================================================

All Terrain Armored Transport for JellyRancher Studio GUI testing.

An autonomous GUI testing system that uses LLM reasoning (Grok-4.1-Fast-Reasoning via Poe.com)
to walk through the entire application workflow, detect issues, and self-heal.

This is NOT a proof of concept - it actually executes actions on the real GUI.
Like its Imperial namesake, it walks methodically and relentlessly through your application.

Features:
- Captures live GUI state at each step
- Uses LLM to reason about what action to take next
- Executes actions via PyQt6 test utilities
- Detects errors and asks LLM for fixes
- Logs everything to master log + dedicated walkthrough log
- Stop-fix-iterate loop for self-healing

Usage:
    .venv\\Scripts\\python.exe tools/at_at.py

    Options:
        --workflow WORKFLOW   Workflow to execute (default: full_roundup)
        --max-steps N         Maximum steps before stopping (default: 100)
        --dry-run             Show what would be done without executing
        --model MODEL         LLM model to use (default: Grok-4.1-Fast-Reasoning)
"""

import sys
import os
import json
import time
import traceback
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QRadioButton, QSpinBox, QDoubleSpinBox,
    QSlider, QListWidget, QTreeWidget, QTableWidget, QTabWidget,
    QMenu, QMenuBar, QDialog, QMessageBox, QFileDialog,
    QTreeWidgetItem, QTableWidgetItem, QListWidgetItem
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, QEventLoop
from PyQt6.QtTest import QTest

# Import project components
from scripts._common.logger import MasterLogger, ProjectLogger
from scripts.ai.ravenmaven_client import PoeClient


class ActionType(Enum):
    """Types of GUI actions the walker can perform."""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    CLEAR_AND_TYPE = "clear_and_type"
    SELECT_COMBO_ITEM = "select_combo_item"
    SELECT_LIST_ITEM = "select_list_item"
    SELECT_TREE_ITEM = "select_tree_item"
    CHECK_CHECKBOX = "check_checkbox"
    UNCHECK_CHECKBOX = "uncheck_checkbox"
    SELECT_TAB = "select_tab"
    MENU_ACTION = "menu_action"
    KEY_PRESS = "key_press"
    WAIT = "wait"
    ASSERT_STATE = "assert_state"
    CAPTURE_STATE = "capture_state"


@dataclass
class GUIAction:
    """Represents a single GUI action to execute."""
    action_type: ActionType
    target: str  # Widget identifier (object_name, text, or path)
    value: Optional[str] = None  # For type_text, select_item, etc.
    description: str = ""  # Human-readable description
    expected_result: str = ""  # What should happen after this action
    timeout_ms: int = 5000  # How long to wait for result


@dataclass
class WalkStep:
    """A single step in the walkthrough with full context."""
    step_number: int
    timestamp: str
    action: GUIAction
    gui_state_before: Dict[str, Any]
    gui_state_after: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    llm_reasoning: str = ""
    fix_attempts: List[str] = field(default_factory=list)


@dataclass
class WalkSession:
    """Complete walkthrough session data."""
    session_id: str
    workflow_name: str
    started_at: str
    model: str
    steps: List[WalkStep] = field(default_factory=list)
    completed: bool = False
    final_status: str = ""
    total_llm_calls: int = 0
    total_fix_attempts: int = 0


class GUIStateCapture:
    """Captures the current state of the GUI for LLM analysis."""

    @staticmethod
    def capture_widget(widget: QWidget, depth: int = 0, max_depth: int = 10) -> Dict[str, Any]:
        """Recursively capture widget state."""
        if depth > max_depth:
            return {"truncated": True, "reason": "max_depth_exceeded"}

        info = {
            "object_name": widget.objectName() or "(unnamed)",
            "class_name": widget.__class__.__name__,
            "enabled": widget.isEnabled(),
            "visible": widget.isVisible(),
        }

        # Capture type-specific properties
        if isinstance(widget, QPushButton):
            info["text"] = widget.text()
            info["checkable"] = widget.isCheckable()
            if widget.isCheckable():
                info["checked"] = widget.isChecked()

        elif isinstance(widget, QLineEdit):
            info["text"] = widget.text()
            info["placeholder"] = widget.placeholderText()
            info["read_only"] = widget.isReadOnly()

        elif isinstance(widget, QTextEdit):
            info["text"] = widget.toPlainText()[:500]  # Truncate long text
            info["read_only"] = widget.isReadOnly()

        elif isinstance(widget, QComboBox):
            info["current_text"] = widget.currentText()
            info["current_index"] = widget.currentIndex()
            info["items"] = [widget.itemText(i) for i in range(min(widget.count(), 20))]

        elif isinstance(widget, QCheckBox):
            info["text"] = widget.text()
            info["checked"] = widget.isChecked()

        elif isinstance(widget, QRadioButton):
            info["text"] = widget.text()
            info["checked"] = widget.isChecked()

        elif isinstance(widget, QSpinBox):
            info["value"] = widget.value()
            info["minimum"] = widget.minimum()
            info["maximum"] = widget.maximum()

        elif isinstance(widget, QTabWidget):
            info["current_index"] = widget.currentIndex()
            info["current_tab"] = widget.tabText(widget.currentIndex()) if widget.count() > 0 else None
            info["tabs"] = [widget.tabText(i) for i in range(widget.count())]

        elif isinstance(widget, QListWidget):
            info["count"] = widget.count()
            info["current_row"] = widget.currentRow()
            items = []
            for i in range(min(widget.count(), 20)):
                item = widget.item(i)
                if item:
                    items.append({"row": i, "text": item.text(), "selected": item.isSelected()})
            info["items"] = items

        elif isinstance(widget, QTreeWidget):
            info["column_count"] = widget.columnCount()
            info["top_level_count"] = widget.topLevelItemCount()
            # Capture top-level items
            items = []
            for i in range(min(widget.topLevelItemCount(), 20)):
                item = widget.topLevelItem(i)
                if item:
                    items.append({
                        "index": i,
                        "text": item.text(0),
                        "expanded": item.isExpanded(),
                        "selected": item.isSelected(),
                        "child_count": item.childCount()
                    })
            info["items"] = items

        elif isinstance(widget, QTableWidget):
            info["row_count"] = widget.rowCount()
            info["column_count"] = widget.columnCount()
            info["current_row"] = widget.currentRow()
            info["current_column"] = widget.currentColumn()
            # Capture headers
            headers = []
            for i in range(widget.columnCount()):
                header = widget.horizontalHeaderItem(i)
                headers.append(header.text() if header else f"Column {i}")
            info["headers"] = headers

        # Capture layout info
        if widget.layout():
            info["layout_type"] = widget.layout().__class__.__name__

        # Recursively capture children
        children = []
        for child in widget.children():
            if isinstance(child, QWidget) and child.isVisible():
                children.append(GUIStateCapture.capture_widget(child, depth + 1, max_depth))

        if children:
            info["children"] = children

        return info

    @staticmethod
    def capture_full_state(app: QApplication) -> Dict[str, Any]:
        """Capture the complete application state."""
        state = {
            "timestamp": datetime.now().isoformat(),
            "windows": [],
            "active_window": None,
            "modal_dialogs": []
        }

        active = app.activeWindow()
        if active:
            state["active_window"] = active.__class__.__name__

        for widget in app.topLevelWidgets():
            if widget.isVisible():
                window_state = GUIStateCapture.capture_widget(widget)
                window_state["is_modal"] = widget.isModal() if hasattr(widget, 'isModal') else False

                if window_state.get("is_modal"):
                    state["modal_dialogs"].append(window_state)
                else:
                    state["windows"].append(window_state)

        return state


class GUIActionExecutor:
    """Executes GUI actions on real widgets."""

    def __init__(self, app: QApplication, logger: logging.Logger):
        self.app = app
        self.logger = logger

    def find_widget(self, target: str, widget_type: type = None) -> Optional[QWidget]:
        """
        Find a widget by various identifiers.

        Target can be:
        - Object name: "btn_scan"
        - Text content: "text:Start Scan"
        - Path: "MainWindow/QStackedWidget/ScanView/btn_scan"
        - Class+text: "QPushButton:Start Scan"
        """
        self.logger.debug(f"Finding widget: {target}")

        # Check all top-level widgets
        for top_widget in self.app.topLevelWidgets():
            if not top_widget.isVisible():
                continue

            result = self._find_widget_recursive(top_widget, target, widget_type)
            if result:
                return result

        return None

    def _find_widget_recursive(self, parent: QWidget, target: str, widget_type: type = None) -> Optional[QWidget]:
        """Recursively search for widget."""
        # Check if this widget matches
        if self._widget_matches(parent, target, widget_type):
            return parent

        # Search children
        for child in parent.children():
            if isinstance(child, QWidget):
                result = self._find_widget_recursive(child, target, widget_type)
                if result:
                    return result

        return None

    def _widget_matches(self, widget: QWidget, target: str, widget_type: type = None) -> bool:
        """Check if widget matches target criteria."""
        if widget_type and not isinstance(widget, widget_type):
            return False

        # Match by object name
        if widget.objectName() == target:
            return True

        # Match by "text:Content" pattern
        if target.startswith("text:"):
            search_text = target[5:]
            if hasattr(widget, 'text') and callable(widget.text):
                if widget.text() == search_text:
                    return True
            if hasattr(widget, 'title') and callable(widget.title):
                if widget.title() == search_text:
                    return True

        # Match by "placeholder:Content" pattern (for QLineEdit)
        if target.startswith("placeholder:"):
            search_text = target[12:]
            if hasattr(widget, 'placeholderText') and callable(widget.placeholderText):
                if search_text in widget.placeholderText():
                    return True

        # Match by "ClassName:text" pattern
        if ":" in target and not target.startswith("text:") and not target.startswith("placeholder:"):
            class_name, text = target.split(":", 1)
            if widget.__class__.__name__ == class_name:
                if hasattr(widget, 'text') and callable(widget.text):
                    if widget.text() == text:
                        return True
                # Also try placeholder text for QLineEdit
                if hasattr(widget, 'placeholderText') and callable(widget.placeholderText):
                    if text in widget.placeholderText():
                        return True

        return False

    def execute_action(self, action: GUIAction) -> Tuple[bool, Optional[str]]:
        """
        Execute a GUI action.

        Returns:
            Tuple of (success, error_message)
        """
        self.logger.info(f"Executing: {action.action_type.value} on '{action.target}'")

        try:
            if action.action_type == ActionType.WAIT:
                wait_ms = int(action.value) if action.value else 1000
                self._process_events(wait_ms)
                return True, None

            if action.action_type == ActionType.CAPTURE_STATE:
                # Just capture, no action needed
                return True, None

            # Find target widget
            widget = self.find_widget(action.target)
            if not widget:
                return False, f"Widget not found: {action.target}"

            if not widget.isEnabled():
                return False, f"Widget is disabled: {action.target}"

            if not widget.isVisible():
                return False, f"Widget is not visible: {action.target}"

            # Execute based on action type
            if action.action_type == ActionType.CLICK:
                self._click_widget(widget)

            elif action.action_type == ActionType.DOUBLE_CLICK:
                self._double_click_widget(widget)

            elif action.action_type == ActionType.TYPE_TEXT:
                if isinstance(widget, (QLineEdit, QTextEdit)):
                    self._type_text(widget, action.value or "")
                else:
                    return False, f"Cannot type into {widget.__class__.__name__}"

            elif action.action_type == ActionType.CLEAR_AND_TYPE:
                if isinstance(widget, QLineEdit):
                    widget.clear()
                    self._type_text(widget, action.value or "")
                elif isinstance(widget, QTextEdit):
                    widget.clear()
                    self._type_text(widget, action.value or "")
                else:
                    return False, f"Cannot clear and type into {widget.__class__.__name__}"

            elif action.action_type == ActionType.SELECT_COMBO_ITEM:
                if isinstance(widget, QComboBox):
                    index = widget.findText(action.value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    else:
                        return False, f"Combo item not found: {action.value}"
                else:
                    return False, f"Not a combo box: {widget.__class__.__name__}"

            elif action.action_type == ActionType.CHECK_CHECKBOX:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(True)
                else:
                    return False, f"Not a checkbox: {widget.__class__.__name__}"

            elif action.action_type == ActionType.UNCHECK_CHECKBOX:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(False)
                else:
                    return False, f"Not a checkbox: {widget.__class__.__name__}"

            elif action.action_type == ActionType.SELECT_TAB:
                if isinstance(widget, QTabWidget):
                    for i in range(widget.count()):
                        if widget.tabText(i) == action.value:
                            widget.setCurrentIndex(i)
                            break
                    else:
                        return False, f"Tab not found: {action.value}"
                else:
                    return False, f"Not a tab widget: {widget.__class__.__name__}"

            elif action.action_type == ActionType.SELECT_LIST_ITEM:
                if isinstance(widget, QListWidget):
                    for i in range(widget.count()):
                        item = widget.item(i)
                        if item and item.text() == action.value:
                            widget.setCurrentItem(item)
                            break
                    else:
                        return False, f"List item not found: {action.value}"
                else:
                    return False, f"Not a list widget: {widget.__class__.__name__}"

            elif action.action_type == ActionType.KEY_PRESS:
                key_map = {
                    "Enter": Qt.Key.Key_Return,
                    "Return": Qt.Key.Key_Return,
                    "Escape": Qt.Key.Key_Escape,
                    "Tab": Qt.Key.Key_Tab,
                    "F12": Qt.Key.Key_F12,
                    "Delete": Qt.Key.Key_Delete,
                    "Backspace": Qt.Key.Key_Backspace,
                }
                key = key_map.get(action.value)
                if key:
                    QTest.keyClick(widget, key)
                else:
                    return False, f"Unknown key: {action.value}"

            else:
                return False, f"Unsupported action type: {action.action_type}"

            # Process events and wait for UI to update
            self._process_events(500)

            return True, None

        except Exception as e:
            error_msg = f"Action failed: {e}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            return False, error_msg

    def _click_widget(self, widget: QWidget):
        """Click a widget."""
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton)

    def _double_click_widget(self, widget: QWidget):
        """Double-click a widget."""
        QTest.mouseDClick(widget, Qt.MouseButton.LeftButton)

    def _type_text(self, widget: QWidget, text: str):
        """Type text into a widget."""
        widget.setFocus()
        self._process_events(100)
        QTest.keyClicks(widget, text)

    def _process_events(self, wait_ms: int = 100):
        """Process pending Qt events and optionally wait."""
        self.app.processEvents()
        if wait_ms > 0:
            loop = QEventLoop()
            QTimer.singleShot(wait_ms, loop.quit)
            loop.exec()


class LLMOrchestrator:
    """Uses LLM to reason about GUI state and determine next actions."""

    SYSTEM_PROMPT = """You are AT-AT, an autonomous GUI test agent for JellyRancher Studio.

APPLICATION CONTEXT:
JellyRancher Studio is a PyQt6 desktop app that organizes messy media files (movies, TV shows) into a clean Jellyfin-compatible library structure. It uses LLM analysis to identify titles, fetches metadata from TMDB/TVDB, and executes file operations.

THE 8-STEP WORKFLOW:
1. Welcome Screen → Click "New Round-Up" → Enter project name → Click OK
2. Scan View → Add folders (test folder: v:/JellyRancher/test_media/unsorted) → Click "Start Scan"
3. Analysis View → Select analysis mode → Click "Analyze"
4. Canonical DB → Match files to TMDB/TVDB metadata
5. Review Table → Approve/edit proposed operations
6. Execution → Run file operations (or dry-run)
7. Subtitles → Check subtitle coverage
8. Complete → Verify results

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no ```json blocks, no explanation text
2. Use object_name when available - it's the most reliable targeting method
3. ONE action per response - never try to do multiple things at once
4. If a dialog is open, you MUST interact with it before anything else
5. After typing text, you usually need to click OK/confirm button

WIDGET TARGETING (in order of preference):
1. object_name: "roundup_name_input" (exact match)
2. text:Content: "text:Start Scan" (button/label text)
3. placeholder:Content: "placeholder:TV Library" (input placeholder)
4. ClassName:text: "QPushButton:OK" (class + text)

KNOWN OBJECT NAMES:
Welcome Screen:
- new_roundup_dialog: Create New Round-Up dialog
- roundup_name_input: QLineEdit for project name
- roundup_dialog_buttons: OK/Cancel button box

Main Window:
- Look for QPushButton with text like "New Round-Up", "Start Scan", "Add Folder"
- QTabWidget for switching between views
- QTreeWidget for file listings

AVAILABLE ACTIONS:
- click: target="object_name" or "QPushButton:Button Text"
- type_text: target=input field, value=text (use for roundup_name_input)
- clear_and_type: target=input, value=text (clears first)
- select_combo_item: target=combo, value=item text
- select_tab: target=tab widget, value=tab name
- key_press: value=Enter/Escape/Tab (use Enter to confirm dialogs)
- wait: value=milliseconds (use 1000-2000 after major actions)

STEP-BY-STEP GUIDANCE:

Step 1 (Create Round-Up):
- If you see "New Round-Up" button → click it
- If new_roundup_dialog is visible → type_text into roundup_name_input with value "AT-AT Test Project"
- Then click "QPushButton:OK" or key_press Enter

Step 2 (Add Folders):
- Look for "Add Folder" button → click it
- A folder dialog should appear - if so, note we need the test folder path

Step 3 (Scan):
- After folders added, look for "Start Scan" button → click it
- Wait for scan to complete (progress bar)

RESPONSE FORMAT:
{"reasoning":"What I see and why I'm taking this action","action":{"action_type":"click","target":"widget_id","value":null,"description":"Click New Round-Up button","expected_result":"Dialog opens"},"workflow_progress":"Step 1: Creating Round-Up","confidence":0.9,"is_workflow_complete":false,"issues_detected":[]}

ERROR FORMAT (when stuck):
{"reasoning":"Problem description","action":null,"workflow_progress":"Stuck at step X","confidence":0.0,"is_workflow_complete":false,"issues_detected":["Issue description"],"suggested_fix":"Recovery suggestion"}

COMMON ISSUES & FIXES:
- Widget not found → Try alternative targeting (text: or ClassName:)
- Dialog blocking → Handle dialog first before other actions
- Action failed → Try waiting (wait action) then retry
- Empty input → Use clear_and_type instead of type_text
"""

    def __init__(self, model: str = "Grok-4.1-Fast-Reasoning", logger: logging.Logger = None):
        self.model = model
        self.logger = logger or logging.getLogger(__name__)
        self.client = PoeClient(default_model=model, logger=self.logger)
        self.conversation_history = []

    def get_next_action(
        self,
        gui_state: Dict[str, Any],
        workflow: str,
        previous_steps: List[WalkStep],
        error_context: Optional[str] = None,
        screenshot_path: Optional[str] = None  # TODO: Future multimodal support
    ) -> Dict[str, Any]:
        """
        Ask LLM to determine the next action based on current state.

        Args:
            gui_state: Widget hierarchy as JSON
            workflow: Workflow description
            previous_steps: History of actions taken
            error_context: Error message if recovering from failure
            screenshot_path: Path to screenshot image (future multimodal support)

        Returns:
            Dictionary with reasoning, action, and metadata

        TODO: When Poe points refresh, add screenshot support:
            - Capture screenshot with QScreen.grabWindow()
            - Send as base64 image with multimodal model
            - LLM can see actual UI, not just widget tree
        """
        # Build context message
        context_parts = [
            f"WORKFLOW OBJECTIVE: {workflow}",
            f"STEP COUNT: {len(previous_steps)} actions taken so far",
            "",
            "CURRENT GUI STATE (widget hierarchy):",
            json.dumps(gui_state, indent=2),
        ]

        if previous_steps:
            context_parts.extend([
                "",
                f"RECENT ACTIONS (last 5 of {len(previous_steps)}):",
            ])
            # Include last 5 steps for context
            for step in previous_steps[-5:]:
                status = "✓" if step.success else f"✗ {step.error}"
                action_info = f"{step.action.action_type.value}({step.action.target})"
                if step.action.value:
                    action_info += f" = '{step.action.value}'"
                context_parts.append(f"  {step.step_number}. {action_info} → {status}")

        if error_context:
            context_parts.extend([
                "",
                "ERROR CONTEXT:",
                error_context,
                "",
                "Please suggest how to recover from this error or an alternative approach."
            ])

        prompt = self.SYSTEM_PROMPT + "\n\n" + "\n".join(context_parts)

        self.logger.info(f"Sending GUI state to {self.model} for analysis...")

        try:
            response = self.client.send_message(
                prompt,
                model=self.model,
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more consistent actions
            )

            # Parse JSON response
            # Try to extract JSON from response (in case there's extra text)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            result = json.loads(response.strip())
            self.logger.info(f"LLM reasoning: {result.get('reasoning', 'No reasoning provided')}")

            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            self.logger.error(f"Raw response: {response[:500]}...")
            return {
                "reasoning": "Failed to parse LLM response",
                "action": None,
                "issues_detected": [f"JSON parse error: {e}"],
                "is_workflow_complete": False
            }
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return {
                "reasoning": f"LLM call failed: {e}",
                "action": None,
                "issues_detected": [str(e)],
                "is_workflow_complete": False
            }

    def get_fix_suggestion(
        self,
        error: str,
        gui_state: Dict[str, Any],
        failed_action: GUIAction
    ) -> Dict[str, Any]:
        """Ask LLM how to fix an error."""
        prompt = f"""{self.SYSTEM_PROMPT}

AN ERROR OCCURRED. Please analyze and suggest a fix.

FAILED ACTION:
  Type: {failed_action.action_type.value}
  Target: {failed_action.target}
  Value: {failed_action.value}
  Description: {failed_action.description}

ERROR:
{error}

CURRENT GUI STATE:
{json.dumps(gui_state, indent=2)}

Please respond with:
1. What likely caused this error
2. A specific action to try as a fix
3. Whether this is recoverable or we should abort
"""

        try:
            response = self.client.send_message(
                prompt,
                model=self.model,
                max_tokens=1500,
                temperature=0.3
            )

            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]

            return json.loads(response.strip())

        except Exception as e:
            self.logger.error(f"Fix suggestion failed: {e}")
            return {
                "reasoning": f"Could not get fix suggestion: {e}",
                "action": None,
                "should_abort": True
            }


class ATAT:
    """
    AT-AT: Autonomous Testing - Automated Traversal

    Main orchestrator that walks through the GUI autonomously,
    like an Imperial walker methodically advancing through hostile terrain.
    """

    # Define available workflows
    WORKFLOWS = {
        "full_roundup": """
Complete Round-Up Workflow (8 Steps):
1. Create a new Round-Up project
2. Add source folders for scanning
3. Run the file scan
4. Perform structure analysis (regex/LLM)
5. Review the canonical database matches
6. Review and approve proposed operations
7. Execute the file operations (or simulate)
8. Check subtitle coverage

Goal: Successfully complete all 8 steps of the media organization workflow.
Start by clicking "New Round-Up" on the welcome screen.
""",
        "scan_only": """
Scan Workflow (Steps 1-3):
1. Create a new Round-Up project
2. Add source folders for scanning
3. Run the file scan and verify results

Goal: Successfully scan folders and display file inventory.
""",
        "quick_test": """
Quick Application Test:
1. Verify application launches
2. Check menu accessibility
3. Open and close a dialog
4. Return to welcome screen

Goal: Verify basic application functionality.
"""
    }

    def __init__(
        self,
        workflow: str = "full_roundup",
        model: str = "Grok-4.1-Fast-Reasoning",
        max_steps: int = 100,
        max_fix_attempts: int = 3,
        dry_run: bool = False
    ):
        self.workflow = workflow
        self.workflow_description = self.WORKFLOWS.get(workflow, workflow)
        self.model = model
        self.max_steps = max_steps
        self.max_fix_attempts = max_fix_attempts
        self.dry_run = dry_run

        # Initialize logging
        self.master_logger = MasterLogger()
        self.logger = self.master_logger.get_child_logger("AT-AT")

        # Create dedicated walkthrough log
        self.walk_log_dir = project_root / "logs" / "at_at_missions"
        self.walk_log_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.walk_log_file = self.walk_log_dir / f"atat_mission_{self.session_id}.json"

        # Initialize session
        self.session = WalkSession(
            session_id=self.session_id,
            workflow_name=workflow,
            started_at=datetime.now().isoformat(),
            model=model
        )

        # Will be initialized when app starts
        self.app: Optional[QApplication] = None
        self.main_window = None
        self.executor: Optional[GUIActionExecutor] = None
        self.orchestrator: Optional[LLMOrchestrator] = None

    def run(self) -> bool:
        """
        Run the intelligent GUI walkthrough.

        Returns:
            True if workflow completed successfully
        """
        self.logger.info("=" * 80)
        self.logger.info("AT-AT: Autonomous Testing - Automated Traversal")
        self.logger.info(f"Mission ID: {self.session_id}")
        self.logger.info(f"Objective: {self.workflow}")
        self.logger.info(f"Tactical AI: {self.model}")
        self.logger.info(f"Max maneuvers: {self.max_steps}")
        self.logger.info(f"Simulation mode: {self.dry_run}")
        self.logger.info("=" * 80)

        try:
            # Initialize Qt application
            self.app = QApplication.instance() or QApplication(sys.argv)

            # Initialize LLM orchestrator
            self.orchestrator = LLMOrchestrator(model=self.model, logger=self.logger)

            # Initialize action executor
            self.executor = GUIActionExecutor(self.app, self.logger)

            # Launch the application
            self.logger.info("Launching JellyRancher Studio...")
            from jelly_rancher_studio import JellyRancherStudio
            self.main_window = JellyRancherStudio()
            self.main_window.show()

            # Process events to ensure window is displayed
            self.app.processEvents()
            time.sleep(1)  # Give window time to fully initialize

            self.logger.info("Application launched successfully")

            # Run the main walkthrough loop
            success = self._walkthrough_loop()

            # Finalize session
            self.session.completed = success
            self.session.final_status = "COMPLETED" if success else "FAILED"
            self._save_session()

            self.logger.info("=" * 80)
            self.logger.info(f"Walkthrough {'COMPLETED' if success else 'FAILED'}")
            self.logger.info(f"Total steps: {len(self.session.steps)}")
            self.logger.info(f"Total LLM calls: {self.session.total_llm_calls}")
            self.logger.info(f"Total fix attempts: {self.session.total_fix_attempts}")
            self.logger.info(f"Session log: {self.walk_log_file}")
            self.logger.info("=" * 80)

            return success

        except Exception as e:
            self.logger.critical(f"Fatal error: {e}")
            self.logger.critical(traceback.format_exc())
            self.session.final_status = f"FATAL ERROR: {e}"
            self._save_session()
            return False

        finally:
            # Cleanup
            if self.main_window:
                self.main_window.close()

    def _walkthrough_loop(self) -> bool:
        """Main loop that iterates through steps."""
        step_number = 0

        while step_number < self.max_steps:
            step_number += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"STEP {step_number}")
            self.logger.info(f"{'='*60}")

            # Capture current GUI state
            gui_state = GUIStateCapture.capture_full_state(self.app)

            # Ask LLM for next action
            self.session.total_llm_calls += 1
            llm_response = self.orchestrator.get_next_action(
                gui_state=gui_state,
                workflow=self.workflow_description,
                previous_steps=self.session.steps
            )

            # Check if workflow is complete
            if llm_response.get("is_workflow_complete"):
                self.logger.info("Workflow marked as complete by LLM")
                return True

            # Check if LLM detected issues it can't resolve
            if llm_response.get("action") is None:
                issues = llm_response.get("issues_detected", [])
                self.logger.error(f"LLM could not determine next action. Issues: {issues}")
                return False

            # Parse the action
            action_data = llm_response["action"]
            try:
                action = GUIAction(
                    action_type=ActionType(action_data["action_type"]),
                    target=action_data["target"],
                    value=action_data.get("value"),
                    description=action_data.get("description", ""),
                    expected_result=action_data.get("expected_result", "")
                )
            except Exception as e:
                self.logger.error(f"Failed to parse action: {e}")
                return False

            # Create step record
            step = WalkStep(
                step_number=step_number,
                timestamp=datetime.now().isoformat(),
                action=action,
                gui_state_before=gui_state,
                llm_reasoning=llm_response.get("reasoning", "")
            )

            # Execute action (or simulate in dry run)
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would execute: {action.action_type.value} on {action.target}")
                step.success = True
            else:
                success, error = self.executor.execute_action(action)
                step.success = success
                step.error = error

                if not success:
                    # Try to fix
                    fixed = self._attempt_fix(step, gui_state, action, error)
                    if not fixed:
                        self.session.steps.append(step)
                        self._save_session()
                        return False

            # Capture state after action
            step.gui_state_after = GUIStateCapture.capture_full_state(self.app)

            # Record step
            self.session.steps.append(step)
            self._save_session()

            self.logger.info(f"Step {step_number} completed: {action.description}")

            # Small delay between steps
            time.sleep(0.5)

        self.logger.warning(f"Reached maximum steps ({self.max_steps})")
        return False

    def _attempt_fix(
        self,
        step: WalkStep,
        gui_state: Dict[str, Any],
        failed_action: GUIAction,
        error: str
    ) -> bool:
        """Attempt to fix a failed action."""
        for attempt in range(self.max_fix_attempts):
            self.session.total_fix_attempts += 1
            self.logger.warning(f"Fix attempt {attempt + 1}/{self.max_fix_attempts}")

            # Ask LLM for fix
            self.session.total_llm_calls += 1
            fix_response = self.orchestrator.get_fix_suggestion(
                error=error,
                gui_state=gui_state,
                failed_action=failed_action
            )

            step.fix_attempts.append(json.dumps(fix_response))

            if fix_response.get("should_abort"):
                self.logger.error("LLM recommends aborting")
                return False

            fix_action_data = fix_response.get("action")
            if not fix_action_data:
                continue

            try:
                fix_action = GUIAction(
                    action_type=ActionType(fix_action_data["action_type"]),
                    target=fix_action_data["target"],
                    value=fix_action_data.get("value"),
                    description=f"FIX: {fix_action_data.get('description', '')}",
                    expected_result=fix_action_data.get("expected_result", "")
                )

                success, fix_error = self.executor.execute_action(fix_action)
                if success:
                    self.logger.info("Fix successful!")
                    step.success = True
                    step.error = None
                    return True
                else:
                    error = fix_error  # Update error for next attempt

            except Exception as e:
                self.logger.error(f"Fix attempt failed: {e}")

        return False

    def _save_session(self):
        """Save session data to JSON file."""
        try:
            # Convert session to dict, handling dataclasses and enums
            session_dict = {
                "session_id": self.session.session_id,
                "workflow_name": self.session.workflow_name,
                "started_at": self.session.started_at,
                "model": self.session.model,
                "completed": self.session.completed,
                "final_status": self.session.final_status,
                "total_llm_calls": self.session.total_llm_calls,
                "total_fix_attempts": self.session.total_fix_attempts,
                "steps": []
            }

            for step in self.session.steps:
                step_dict = {
                    "step_number": step.step_number,
                    "timestamp": step.timestamp,
                    "action": {
                        "action_type": step.action.action_type.value,
                        "target": step.action.target,
                        "value": step.action.value,
                        "description": step.action.description,
                        "expected_result": step.action.expected_result
                    },
                    "success": step.success,
                    "error": step.error,
                    "llm_reasoning": step.llm_reasoning,
                    "fix_attempts": step.fix_attempts,
                    # Don't save full GUI state to keep file manageable
                    "gui_state_summary": {
                        "windows_count": len(step.gui_state_before.get("windows", [])),
                        "modal_dialogs": len(step.gui_state_before.get("modal_dialogs", [])),
                        "active_window": step.gui_state_before.get("active_window")
                    }
                }
                session_dict["steps"].append(step_dict)

            with open(self.walk_log_file, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")


def main():
    """Main entry point - Deploy the AT-AT."""
    import argparse

    print("""
    ___    _________    ___    ______
   /   |  /_  __/   |  / _ \\  /_  __/
  / /| |   / / / /| | / ___/   / /
 / ___ |  / / / ___ |/ /      / /
/_/  |_| /_/ /_/  |_/_/      /_/

Autonomous Testing - Automated Traversal
    """)

    parser = argparse.ArgumentParser(
        description="AT-AT: Autonomous Testing - Automated Traversal for JellyRancher Studio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available missions:
  full_roundup  - Complete 8-step media organization workflow
  scan_only     - Just create project and scan folders (steps 1-3)
  quick_test    - Basic application functionality test

Examples:
  python tools/at_at.py
  python tools/at_at.py --workflow scan_only
  python tools/at_at.py --dry-run --max-steps 10
  python tools/at_at.py --model GPT-4o
"""
    )

    parser.add_argument(
        '--workflow', '-w',
        choices=list(ATAT.WORKFLOWS.keys()),
        default='full_roundup',
        help='Mission objective (default: full_roundup)'
    )
    parser.add_argument(
        '--max-steps', '-n',
        type=int,
        default=100,
        help='Maximum maneuvers before retreat (default: 100)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Simulation mode - show what would be done without executing'
    )
    parser.add_argument(
        '--model', '-m',
        default='Grok-4.1-Fast-Reasoning',
        help='Tactical AI model (default: Grok-4.1-Fast-Reasoning)'
    )
    parser.add_argument(
        '--max-fix-attempts',
        type=int,
        default=3,
        help='Maximum repair attempts per obstacle (default: 3)'
    )

    args = parser.parse_args()

    walker = ATAT(
        workflow=args.workflow,
        model=args.model,
        max_steps=args.max_steps,
        max_fix_attempts=args.max_fix_attempts,
        dry_run=args.dry_run
    )

    print(f"Deploying AT-AT for mission: {args.workflow}")
    print(f"Tactical AI: {args.model}")
    print()

    success = walker.run()

    if success:
        print("\nMission accomplished. AT-AT returning to base.")
    else:
        print("\nMission failed. AT-AT requires repair.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
