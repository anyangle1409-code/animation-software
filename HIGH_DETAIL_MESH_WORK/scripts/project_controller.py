"""Budget-aware Home Gym PT background project controller.

No AI API calls. No automatic Work/Claude invocation.
Routes the next action and keeps cheap deterministic local work moving.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORTS = ROOT / "reports"
CONFIG_PATH = ROOT / "PROJECT_CONTROLLER_CONFIG.json"
BUDGET_PATH = REPORTS / "ai_budget_state.json"
STATE_PATH = REPORTS / "project_controller_state.json"
LOG_PATH = REPORTS / "project_controller.log"
STOP_PATH = REPORTS / "project_controller.stop"
LOCK_PATH = REPORTS / "project_controller.lock"
NEXT_MD = ROOT / "PROJECT_CONTROLLER_NEXT.md"
WORK_PROMPT = ROOT / "PROJECT_CONTROLLER_WORK_PROMPT.txt"
CLAUDE_PROMPT = ROOT / "PROJECT_CONTROLLER_CLAUDE_PROMPT.txt"
V15_STATUS = ROOT / "scripts" / "v15f_status.py"
V15_HANDOFF = ROOT / "scripts" / "write_v15f_handoff.py"
SAFE_RUNNER_START = ROOT / "scripts" / "start_v15f_safe_runner.py"

DEFAULT_CONFIG = {
    "poll_seconds": 15,
    "source_check_minutes": 30,
    "work_low_budget_percent": 20,
    "work_critical_budget_percent": 8,
    "claude_low_budget_percent": 20,
    "auto_run_deterministic": True,
    "auto_fetch_source": False,
    "allow_ai_api_calls": False,
}

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def log(msg):
    REPORTS.mkdir(parents=True, exist_ok=True)
    line = f"[{utcnow()}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except Exception:
        return default

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    cfg.update(read_json(CONFIG_PATH, {}))
    return cfg

def load_budget():
    data = read_json(BUDGET_PATH, {})
    return {
        "work_percent": data.get("work_percent"),
        "claude_percent": data.get("claude_percent"),
        "work_reset_note": data.get("work_reset_note"),
        "claude_reset_note": data.get("claude_reset_note"),
        "updated_utc": data.get("updated_utc"),
    }

def run_capture(cmd, cwd=ROOT):
    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return p.returncode, p.stdout.strip()

def git_value(*args):
    rc, out = run_capture(["git", *args], cwd=REPO)
    return out if rc == 0 else None

def v15_status():
    rc, out = run_capture([sys.executable, V15_STATUS])
    if rc != 0:
        return {"next_action": "Inspect V15F_STATUS failure", "reason": out}
    try:
        return json.loads(out)
    except Exception:
        return {"next_action": "Inspect V15F_STATUS output", "reason": out}

def classify(next_action, budget, cfg):
    action = (next_action or "").strip()
    if action.startswith(("AUDIT_V15F_", "GENERATE_V15F_", "RUN_V15_POST_EDIT_ALL.bat")):
        return "LOCAL_SCRIPT"
    if action.startswith("OPEN_V15") or "MARK_V15F_" in action:
        return "HUMAN_VISUAL"
    blender_words = (
        "Inspect/edit", "Repair ring", "Repair pinky", "Repair index",
        "Repair middle", "Repair only", "Blender", "topology",
    )
    if any(x.lower() in action.lower() for x in blender_words):
        work = budget.get("work_percent")
        if isinstance(work, (int, float)) and work <= cfg["work_low_budget_percent"]:
            return "WAIT_FOR_WORK_RESET"
        return "GPT_WORK"
    if not action:
        return "NORMAL_CHAT"
    return "NORMAL_CHAT"

def make_work_prompt(status, route):
    action = status.get("next_action") or "Run V15F_STATUS.bat"
    reason = status.get("reason") or ""
    return f"""Open anyangle1409-code/animation-software on branch:
work/v15-deep-hand-rebuild-prep-20260925

Do not modify or merge chatgpt/absolute-retarget-imports.

Read HIGH_DETAIL_MESH_WORK/AI_USAGE_BUDGET.md,
HIGH_DETAIL_MESH_WORK/WORK_RESUME_AFTER_LIMIT.md, and
HIGH_DETAIL_MESH_WORK/V15F_LATEST_HANDOFF.md if present.

From HIGH_DETAIL_MESH_WORK run:
RESUME_V15F_WORK.bat

Controller route: {route}
Exact current next action:
{action}

Reason:
{reason}

Continue unattended through documented recoverable steps.
Use Work time only for Blender/local-GUI work and required visual reasoning.
Let local scripts handle deterministic audits/renders/reports.
Do not promote geometry, start Phase C, merge source, alter production
references, or weaken validation gates without the documented acceptance gate.
"""

def make_claude_prompt():
    return """Open anyangle1409-code/animation-software on branch:
work/v15-deep-hand-rebuild-prep-20260925

Read CLAUDE.md and HIGH_DETAIL_MESH_WORK/CLAUDE_LOW_USAGE_HANDOFF.md.

Do not continue the whole project. Wait for one narrowly scoped source-code,
report-analysis, or mathematical task. Read only files directly needed for that
task, use focused tests first, write durable state to the repo, then stop.
"""

def write_outputs(status, route, budget, repo_state):
    WORK_PROMPT.write_text(make_work_prompt(status, route), encoding="utf-8")
    CLAUDE_PROMPT.write_text(make_claude_prompt(), encoding="utf-8")
    action = status.get("next_action") or "(none)"
    reason = status.get("reason") or ""
    lines = [
        "# Project Controller - next action",
        "",
        f"- updated: {utcnow()}",
        f"- route: **{route}**",
        f"- next action: {action}",
        f"- reason: {reason}",
        f"- Work remaining (manual): {budget.get('work_percent')}",
        f"- Claude remaining (manual): {budget.get('claude_percent')}",
        f"- branch: {repo_state.get('branch')}",
        f"- HEAD: {repo_state.get('head')}",
        f"- working tree dirty: **{repo_state.get('dirty')}**",
        "",
    ]
    if route == "LOCAL_SCRIPT":
        lines.append("The local deterministic runner should handle this without spending GPT Work or Claude allowance.")
    elif route == "WAIT_FOR_WORK_RESET":
        lines.append("Do not start another substantial Work topology task. Keep deterministic work running and resume Blender work after reset.")
    elif route == "GPT_WORK":
        lines += ["Use GPT Work for the current Blender/local-GUI step.", "Prompt file: PROJECT_CONTROLLER_WORK_PROMPT.txt"]
    elif route == "HUMAN_VISUAL":
        lines.append("A visual decision is required. Open the exact board named by V15F_STATUS; do not launch a broad Work task just to rediscover it.")
    else:
        lines.append("Use normal Chat for planning/report interpretation unless a narrow Claude source task is identified.")
    NEXT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

def acquire_lock():
    REPORTS.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        age = time.time() - LOCK_PATH.stat().st_mtime
        if age < 12 * 3600:
            raise SystemExit(f"Controller appears active: {LOCK_PATH}")
        LOCK_PATH.unlink(missing_ok=True)
    LOCK_PATH.write_text(json.dumps({"pid": os.getpid(), "started_utc": utcnow()}, indent=2), encoding="utf-8")

def maybe_start_safe_runner(cfg):
    if cfg.get("auto_run_deterministic", True):
        subprocess.run(
            [sys.executable, str(SAFE_RUNNER_START)],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    acquire_lock()
    STOP_PATH.unlink(missing_ok=True)
    maybe_start_safe_runner(cfg)
    log(f"START pid={os.getpid()} once={args.once}")
    last_signature = None
    last_fetch = 0.0
    try:
        while True:
            if STOP_PATH.exists():
                log("Stop requested.")
                break
            if cfg.get("auto_fetch_source") and time.time() - last_fetch >= cfg["source_check_minutes"] * 60:
                rc, out = run_capture(["git", "fetch", "origin", "chatgpt/absolute-retarget-imports"], cwd=REPO)
                log(f"source fetch rc={rc}: {out[-500:]}")
                last_fetch = time.time()

            status = v15_status()
            budget = load_budget()
            route = classify(status.get("next_action"), budget, cfg)
            dirty_out = git_value("status", "--porcelain")
            repo_state = {
                "branch": git_value("branch", "--show-current"),
                "head": git_value("rev-parse", "HEAD"),
                "dirty": bool(dirty_out),
                "source_local": git_value("rev-parse", "chatgpt/absolute-retarget-imports"),
                "source_remote": git_value("rev-parse", "origin/chatgpt/absolute-retarget-imports"),
            }
            write_outputs(status, route, budget, repo_state)
            payload = {
                "updated_utc": utcnow(),
                "route": route,
                "v15f": status,
                "budget": budget,
                "repository": repo_state,
                "next_file": str(NEXT_MD),
                "work_prompt": str(WORK_PROMPT),
                "claude_prompt": str(CLAUDE_PROMPT),
            }
            STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            signature = json.dumps(
                {"route": route, "action": status.get("next_action"), "reason": status.get("reason"),
                 "work": budget.get("work_percent"), "claude": budget.get("claude_percent"),
                 "head": repo_state.get("head")},
                sort_keys=True,
            )
            if signature != last_signature:
                log(f"route={route} next={status.get('next_action')!r} work={budget.get('work_percent')} claude={budget.get('claude_percent')}")
                last_signature = signature

            subprocess.run([sys.executable, str(V15_HANDOFF)], cwd=ROOT, check=False)
            if args.once:
                break
            time.sleep(float(cfg.get("poll_seconds", 15)))
    finally:
        LOCK_PATH.unlink(missing_ok=True)
        STOP_PATH.unlink(missing_ok=True)
        log("EXIT")

if __name__ == "__main__":
    main()
