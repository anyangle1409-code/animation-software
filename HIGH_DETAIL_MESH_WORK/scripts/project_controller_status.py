"""Print current project-controller state and current live V15f route."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/"reports"/"project_controller_state.json"
LOCK=ROOT/"reports"/"project_controller.lock"
CTRL=ROOT/"scripts"/"project_controller.py"

if LOCK.exists():
    print("controller: ACTIVE/LOCKED")
else:
    print("controller: not locked")

if STATE.is_file():
    try:
        data=json.loads(STATE.read_text(encoding="utf-8"))
        print(json.dumps(data,indent=2))
        raise SystemExit(0)
    except Exception as exc:
        print("state read error:",exc)

print("No saved state; running one non-daemon controller pass.")
subprocess.run([sys.executable,str(CTRL),"--once"],cwd=ROOT,check=False)
if STATE.is_file():
    print(STATE.read_text(encoding="utf-8"))
