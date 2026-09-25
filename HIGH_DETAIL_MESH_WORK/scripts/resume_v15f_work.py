"""Single safe entry point for resuming V15f work after interruption/usage reset.

This does not pull/reset/clean Git and never discards local files.
- runs the prepared-tooling static self-check;
- prints current V15f status;
- if V15f does not exist yet, starts the prepared local-patch workflow;
- otherwise refreshes the interruption handoff, starts the safe deterministic
  runner, and opens the existing V15f Blend with the V15 Hand sidebar.

It does not make visual PASS/FAIL decisions or edit geometry automatically.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BLEND=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
STATUS=ROOT/"scripts"/"v15f_status.py"

def find_blender():
    e=os.environ.get("BLENDER_EXE")
    if e and Path(e).is_file():
        return e
    f=shutil.which("blender")
    if f:
        return f
    if os.name=="nt":
        hits=sorted(
            glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),
            reverse=True,
        )
        if hits:
            return hits[0]
    raise SystemExit("Blender not found. Set BLENDER_EXE or add Blender to PATH.")

def run(cmd,check=True):
    print("+"," ".join(str(x) for x in cmd),flush=True)
    return subprocess.run([str(x) for x in cmd],cwd=ROOT,check=check)

def main():
    run([sys.executable,ROOT/"scripts"/"check_prepared_tooling.py"])

    p=subprocess.run(
        [sys.executable,STATUS],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(p.stdout,flush=True)
    try:
        status=json.loads(p.stdout)
    except Exception:
        status={}

    if not BLEND.is_file():
        print("V15f candidate missing; starting prepared local-patch workflow.",flush=True)
        run([sys.executable,ROOT/"scripts"/"start_v15f_local_patch.py"])
        return

    run([sys.executable,ROOT/"scripts"/"write_v15f_handoff.py"],check=False)
    run([sys.executable,ROOT/"scripts"/"start_v15f_safe_runner.py"],check=False)

    next_action=status.get("next_action")
    if next_action:
        print("V15F_NEXT_ACTION",next_action,flush=True)

    exe=find_blender()
    print("Opening existing V15f candidate:",BLEND,flush=True)
    subprocess.Popen([
        exe,str(BLEND),
        "--python",str(ROOT/"scripts"/"register_v15_blender_tools.py"),
    ],cwd=ROOT)

if __name__=="__main__":
    main()
