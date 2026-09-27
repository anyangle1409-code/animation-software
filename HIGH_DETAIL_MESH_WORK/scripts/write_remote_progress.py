"""Write the compact, sanitised unattended-run progress heartbeat."""
from __future__ import annotations

import argparse
import ctypes
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT = ROOT / "REMOTE_PROGRESS.md"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def elapsed_since(value: str) -> str:
    try:
        started = datetime.fromisoformat(value.replace("Z", "+00:00"))
        seconds = max(0, int((datetime.now(timezone.utc) - started).total_seconds()))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except (TypeError, ValueError):
        return "unknown"


def clean(value: object) -> str:
    text = str(value or "none").replace("\r", " ").replace("\n", " ").strip()
    text = re.sub(r"(?i)[a-z]:[\\/][^,;]+", "[local path]", text)
    text = re.sub(r"(?i)\b(?:token|password|secret|account[_ -]?id)\s*[:=]\s*\S+", "[redacted]", text)
    return text[:600]


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def running(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    return False


def lock_state(path: Path) -> str:
    data = read_json(path)
    return "running" if running(data.get("pid")) else "stopped"


def old_field(name: str, default: str = "") -> str:
    if not OUT.is_file():
        return default
    match = re.search(rf"^- {re.escape(name)}:\s*(.*)$", OUT.read_text(encoding="utf-8"), re.M)
    return match.group(1).strip() if match else default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", choices=["ACTIVE", "WAITING", "BLOCKED", "COMPLETE", "ERROR"], required=True)
    parser.add_argument("--task-start")
    parser.add_argument("--operation-start")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--digit", default="none")
    parser.add_argument("--attempt", default="none")
    parser.add_argument("--operation", required=True)
    parser.add_argument("--completed", required=True)
    parser.add_argument("--checkpoint", default="none")
    parser.add_argument("--numeric", default="none")
    parser.add_argument("--visual", default="none")
    parser.add_argument("--last-successful-gate", default="none")
    parser.add_argument("--blocker", default="none")
    parser.add_argument("--report", default="none")
    parser.add_argument("--blender-state", choices=["running", "idle", "unavailable"], default="unavailable")
    parser.add_argument("--geometry-changed", choices=["true", "false"], default="false")
    parser.add_argument("--audit-running", choices=["true", "false"], default="false")
    parser.add_argument("--work-blocked", choices=["true", "false"], default="false")
    parser.add_argument("--error", default="none")
    parser.add_argument("--next", required=True)
    parser.add_argument("--battery", default="unknown")
    parser.add_argument("--work-remaining", default="unknown")
    parser.add_argument("--stop-reason", default="none")
    args = parser.parse_args()

    previous_counter = int(old_field("progress_counter", "0") or 0)
    previous_operation = old_field("exact operation currently being performed")
    previous_streak = int(old_field("same-operation heartbeat streak", "0") or 0)
    streak = previous_streak + 1 if previous_operation == args.operation else 1
    possible_stall = streak >= 2 and args.status == "ACTIVE"
    task_start = args.task_start or old_field("local task start time if known", utcnow())
    operation_start = (
        old_field("current operation start time", args.operation_start or utcnow())
        if previous_operation == args.operation
        else (args.operation_start or utcnow())
    )
    controller = lock_state(ROOT / "reports" / "project_controller.lock")
    safe = clean(read_json(ROOT / "reports" / "v15f_safe_runner_state.json").get("state") or "unknown")

    content = "\n".join([
        "# Remote progress heartbeat", "",
        f"- UTC timestamp: {utcnow()}",
        f"- local task start time if known: {clean(task_start)}",
        f"- current branch: {clean(git('branch', '--show-current'))}",
        f"- current HEAD: {clean(git('rev-parse', 'HEAD'))}",
        f"- controller state: {controller}",
        f"- safe-runner state: {safe}",
        f"- Blender state: {args.blender_state}",
        f"- current phase: {clean(args.phase)}",
        f"- current digit: {clean(args.digit)}",
        f"- current repair strategy/attempt number: {clean(args.attempt)}",
        f"- exact operation currently being performed: {clean(args.operation)}",
        f"- current operation start time: {clean(operation_start)}",
        f"- current operation elapsed time: {elapsed_since(operation_start)}",
        f"- most recent operation completed: {clean(args.completed)}",
        f"- latest checkpoint: {clean(args.checkpoint)}",
        f"- latest numeric gate: {clean(args.numeric)}",
        f"- latest visual gate: {clean(args.visual)}",
        f"- last successful gate: {clean(args.last_successful_gate)}",
        f"- current unresolved blocker: {clean(args.blocker)}",
        f"- latest relevant report: {clean(args.report)}",
        f"- geometry changed since previous heartbeat: {args.geometry_changed}",
        f"- audit/render currently running: {args.audit_running}",
        f"- Work appears blocked/waiting: {args.work_blocked}",
        f"- last error: {clean(args.error)}",
        f"- next expected operation: {clean(args.next)}",
        f"- approximate battery percentage: {clean(args.battery)}",
        f"- approximate Work usage remaining: {clean(args.work_remaining)}",
        f"- progress_status: {args.status}",
        f"- progress_counter: {previous_counter + 1}",
        f"- possible_stall: {str(possible_stall).lower()}",
        f"- same-operation heartbeat streak: {streak}",
        f"- exact stop reason: {clean(args.stop_reason)}", "",
    ])
    OUT.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"progress_counter": previous_counter + 1, "possible_stall": possible_stall, "path": OUT.name}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
