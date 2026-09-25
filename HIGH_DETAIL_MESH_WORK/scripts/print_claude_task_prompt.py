"""Print a minimal Claude Code prompt for one discrete task."""
from __future__ import annotations
import argparse

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("task", nargs="+")
    args=ap.parse_args()
    task=" ".join(args.task).strip()
    print(f"""Open anyangle1409-code/animation-software on branch:
work/v15-deep-hand-rebuild-prep-20260925

Read CLAUDE.md.
Read HIGH_DETAIL_MESH_WORK/CLAUDE_LOW_USAGE_HANDOFF.md.
Read HIGH_DETAIL_MESH_WORK/V15F_LATEST_HANDOFF.md only if relevant.

Work only on this task:
{task}

Read only the files/report directly needed for that task.
Do not scan the repository or historical hand documents unless the current
failure explicitly requires them.
Use focused tests first; do not run the full suite until focused checks pass.
Do not modify or merge chatgpt/absolute-retarget-imports.
Do not duplicate GPT Work's Blender GUI task.
Keep output concise, write durable state/results to the repo, verify the task,
then stop.""")
if __name__=="__main__":
    main()
