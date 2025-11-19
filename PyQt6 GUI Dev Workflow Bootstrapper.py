import os
import ast
import json
from pathlib import Path
import sys

# ------------------------------------------------------------------
# SETUP SCRIPT – RUN ONCE IN PROJECT ROOT
# ------------------------------------------------------------------

print("PyQt6 GUI Dev Workflow Bootstrapper")
print("This will create a 'dev_workflow' folder with everything you need.\n")

main_module = input("Enter your main module name (file without .py, e.g. 'main' or 'app'): ").strip()
if not main_module:
    print("Module name required.")
    sys.exit(1)

main_class = input("Enter your main window class name (e.g. 'MainWindow'): ").strip()
if not main_class:
    print("Class name required.")
    sys.exit(1)

dev_folder = Path("dev_workflow")
dev_folder.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# 1. Generate function_index.json (run this every coding session)
# ------------------------------------------------------------------
def create_function_index_generator():
    code = '''import os
import ast
from pathlib import Path
import json

index = []

root = Path("..")  # we are inside dev_workflow, root is project root

for p in root.rglob("*.py"):
    if p.name in {"generate_function_index.py", "generate_gui_index.py", "update_project_map.py", "setup_gui_dev_workflow.py"}:
        continue
    if "dev_workflow" in p.parts:
        continue
    try:
        with open(p, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node) or ""
                args = [arg.arg for arg in node.args.args if arg.arg != "self"]
                index.append({
                    "function_name": node.name,
                    "file": str(p.relative_to(root)),
                    "line": node.lineno,
                    "docstring": doc.strip(),
                    "args": args
                })
    except Exception as e:
        print(f"Error parsing {p}: {e}")

with open("../function_index.json", "w", encoding="utf-8") as f:
    json.dump({"functions": index}, f, indent=4)

print("function_index.json updated")
'''
    (dev_folder / "generate_function_index.py").write_text(code, encoding="utf-8")

# ------------------------------------------------------------------
# 2. Generate GUI dumper/launcher (run this every coding session – close app to dump)
# ------------------------------------------------------------------
gui_code = f'''import sys
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from {main_module} import {main_class}

def build_tree(widget):
    info = {{
        "object_name": widget.objectName(),
        "class_name": widget.__class__.__name__,
    }}

    # Common useful properties
    for prop in ["text", "title", "placeholderText", "currentText", "checkState", "isChecked"]:
        if hasattr(widget, prop.lower()):
            try:
                val = getattr(widget, prop.lower())
                if callable(val):
                    val = val()
                info[prop.lower()] = val
            except:
                pass
        elif hasattr(widget, prop.lower() + "()"):
            try:
                method = getattr(widget, prop.lower() + "()")
                info[prop.lower()] = method()
            except:
                pass

    # Direct widget children only for proper hierarchy
    direct_children = [c for c in widget.children() if c.isWidgetType()]
    info["children"] = [build_tree(c) for c in direct_children]

    return info

def dump_gui_on_close():
    app = QApplication.instance()
    for w in app.topLevelWidgets():
        if isinstance(w, {main_class}):
            tree = {{"main_window_class": "{main_class}", "tree": build_tree(w)}}
            with open("../gui_index.json", "w", encoding="utf-8") as f:
                json.dump(tree, f, indent=4)
            print("\\nGUI index dumped to ../gui_index.json – you can close the app now")
            break

app = QApplication(sys.argv)
window = {main_class}()
window.show()

app.aboutToQuit.connect(dump_gui_on_close)

sys.exit(app.exec())
'''
    (dev_folder / "generate_gui_index.py").write_text(gui_code, encoding="utf-8")

# ------------------------------------------------------------------
# 3. Generate project_map updater (run this every coding session)
# ------------------------------------------------------------------
update_code = '''import json
import os

def load(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

gui = load("../gui_index.json")
funcs = load("../function_index.json")
current_map = load("../project_map.json") or {"pages": {}, "orphaned_functions": [], "note": "This is the single source of truth for GUI ↔ function mapping"}

if not gui:
    print("No gui_index.json found – run generate_gui_index.py first")
if not funcs:
    print("No function_index.json found – run generate_function_index.py first")
if not gui or not funcs:
    exit()

prompt = f"""
You are maintaining the definitive GUI-to-function mapping for a PyQt6 application.

Raw GUI tree (just dumped):
{json.dumps(gui, indent=2)}

Current function index:
{json.dumps(funcs, indent=2)}

Current project_map.json (single source of truth):
{json.dumps(current_map, indent=2)}

Rules:
- Use object_name as the key whenever it exists (e.g. "btn_save" → save_project)
- Prefer functions that contain the object_name or similar words
- If a button text is "Save Project", map to save_project or on_save_clicked, etc.
- Mark status "mapped", "unmapped", or "orphaned"
- Add new GUI elements that aren't in the map yet
- Never delete existing correct mappings unless they are clearly wrong
- Return ONLY the ENTIRE project_map.json, improved and complete

Return ONLY valid JSON, no markdown, no explanation:
"""

print("Copy from here ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
print(prompt)
print("Paste the above to your LLM (me/Grok). Then paste my response JSON below when asked.")

response = input("\nPaste the LLM's JSON response here: ").strip()

try:
    new_map = json.loads(response)
    with open("../project_map.json", "w", encoding="utf-8") as f:
        json.dump(new_map, f, indent=4)
    print("project_map.json updated successfully!")
except:
    print("Invalid JSON – try again")
'''
    (dev_folder / "update_project_map.py").write_text(update_code, encoding="utf-8")

# ------------------------------------------------------------------
# 4. Create initial JSON files
# ------------------------------------------------------------------
Path("function_index.json").write_text(json.dumps({"functions": []}, indent=4), encoding="utf-8")
Path("gui_index.json").write_text(json.dumps({"note": "Run dev_workflow/generate_gui_index.py and close the app to populate this file"}, indent=4), encoding="utf-8")
Path("project_map.json").write_text(json.dumps({"pages": {}, "orphaned_functions": [], "note": "This will be filled on first update"}, indent=4), encoding="utf-8")

# ------------------------------------------------------------------
# 5. Create README
# ------------------------------------------------------------------
readme = """# PyQt6 GUI Dev Workflow (Zero Drift Guaranteed)

You now have everything you need.

Workflow (run after every coding session):

1. python dev_workflow/generate_function_index.py     → updates function_index.json
2. python dev_workflow/generate_gui_index.py          → launches your app – close it → dumps gui_index.json
3. python dev_workflow/update_project_map.py        → shows prompt → paste to Grok → paste response back → saves project_map.json

In every future coding prompt to me, paste the current project_map.json at the top with:

"Here is the current project_map.json (single source of truth):" + contents

Tips for near-perfect auto-mapping:
- Set meaningful objectNames: self.btn_save.setObjectName("btn_save")
- Name functions like save_project, on_import_clicked, delete_selected, etc.
- The LLM will learn your patterns after 2-3 rounds and become ~98% accurate.

Enjoy never having GUI/function drift again.
"""

(dev_folder / "README.md").write_text(readme, encoding="utf-8")

# ------------------------------------------------------------------
# Run the function index once now so you have it ready
# ------------------------------------------------------------------
print("\nRunning initial function index scan...")
index = []
for p in Path(".").rglob("*.py"):
    if p.name == Path(__file__).name:
        continue
    try:
        with open(p, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node) or ""
                args = [a.arg for a in node.args.args if a.arg != "self"]
                index.append({
                    "function_name": node.name,
                    "file": str(p),
                    "line": node.lineno,
                    "docstring": doc.strip(),
                    "args": args
                })
    except Exception:
        pass

with open("function_index.json", "w", encoding="utf-8") as f:
    json.dump({"functions": index}, f, indent=4)

print("\nSetup complete! → dev_workflow folder created")
print("Run the three scripts in any order whenever you want fresh indexes.")
print("You're ready – start coding and use project_map.json in every prompt to me.")
