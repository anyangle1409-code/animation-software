"""Print a minimal GPT Work resume prompt from the current V15f state."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/"scripts"/"v15f_status.py"

def main():
    p=subprocess.run(
        [sys.executable,str(STATUS)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        state=json.loads(p.stdout)
    except Exception:
        state={"next_action":"Run RESUME_V15F_WORK.bat","reason":"Status unavailable."}

    next_action=state.get("next_action") or "Run RESUME_V15F_WORK.bat"
    reason=state.get("reason") or ""

    print(
f"""Open anyangle1409-code/animation-software on branch:
work/v15-deep-hand-rebuild-prep-20260925

Do not modify or merge chatgpt/absolute-retarget-imports.

Read HIGH_DETAIL_MESH_WORK/AI_USAGE_BUDGET.md and
HIGH_DETAIL_MESH_WORK/WORK_RESUME_AFTER_LIMIT.md.
Read HIGH_DETAIL_MESH_WORK/V15F_LATEST_HANDOFF.md if present.

From HIGH_DETAIL_MESH_WORK run:
RESUME_V15F_WORK.bat

Current expected next action:
{next_action}

Current reason:
{reason}

Continue unattended through documented recoverable steps.
Use Work time mainly for Blender topology and required visual judgement.
Do not rediscover project history or rerun deterministic work already scripted.
Do not promote geometry, start Phase C, merge source, alter production
references or weaken validation gates without the documented acceptance gate."""
    )

if __name__=="__main__":
    main()
