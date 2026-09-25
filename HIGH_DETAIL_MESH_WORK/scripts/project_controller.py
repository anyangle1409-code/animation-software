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
COMPARE_USAGE = ROOT / "scripts" / "compare_work_models.py"
PLAN_WORK_TASK = ROOT / "scripts" / "plan_work_task.py"
REMOTE_SYNC = ROOT / "scripts" / "remote_state_sync.py"
REMOTE_SYNC_DEBOUNCE_SECONDS = 300

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
        "work_window_percent": data.get("work_window_percent", data.get("work_percent")),
        "work_week_percent": data.get("work_week_percent"),
        "claude_percent": data.get("claude_percent"),
        "work_window_reset_note": data.get("work_window_reset_note", data.get("work_reset_note")),
        "work_week_reset_note": data.get("work_week_reset_note"),
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

def infer_task_class(next_action):
    action=(next_action or "").lower()
    if action.startswith(("audit_v15f_","generate_v15f_","run_v15_post_edit_all.bat")):
        return "local_script"
    if "open_v15" in action or "mark_v15f_" in action:
        return "visual_review"
    if any(x in action for x in ("ring_l","ring_r","pinky_l","pinky_r","index_l","index_r","middle_l","middle_r")):
        if any(x in action for x in ("inspect/edit","repair","topology")):
            return "one_digit_topology"
    if "blender" in action and ("repair" in action or "failure" in action):
        return "blender_debug"
    if "inspect" in action or "status" in action or "file" in action:
        return "status_or_file_check"
    return "open_ended"

def estimate_models(task_class):
    rc,out=run_capture([
        sys.executable,COMPARE_USAGE,task_class,
        "--context","small","--reasoning","medium"
    ])
    if rc!=0:
        return {"error":out}
    try:return json.loads(out)
    except Exception:return {"error":out}

def plan_work(task_class, cfg):
    models=cfg.get("available_work_models") or ["Luna","Terra","Sol","Astra"]
    rc,out=run_capture([
        sys.executable,PLAN_WORK_TASK,task_class,
        "--context","small",
        "--failed-attempts","0",
        "--available-models",",".join(models),
    ])
    if rc!=0:
        return {"decision":"ERROR","reason":out}
    try:return json.loads(out)
    except Exception:return {"decision":"ERROR","reason":out}

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
        return "GPT_WORK"
    if not action:
        return "NORMAL_CHAT"
    return "NORMAL_CHAT"

def make_work_prompt(status, route, work_plan):
    action = status.get("next_action") or "Run V15F_STATUS.bat"
    reason = status.get("reason") or ""
    model = work_plan.get("recommended_model") or "Use controller recommendation"
    reasoning = work_plan.get("reasoning") or "lowest sensible"
    fast = work_plan.get("fast_mode", False)
    scope = work_plan.get("scope") or action
    estimate = work_plan.get("estimated_five_hour_drop_percent") or {}
    return f"""Before sending this task, set Work to:
Model: {model}
Reasoning: {reasoning}
Fast mode: {"ON" if fast else "OFF"}

Estimated 5-hour allowance use:
{estimate.get("low", "?")}% to {estimate.get("high", "?")}% (approximate)

Open anyangle1409-code/animation-software on branch:
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

Amended task scope:
{scope}

Reason:
{reason}

Do only this scoped task first. Do not broaden it during the same Work task.
Continue unattended through documented recoverable steps inside this scope.
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

def write_outputs(status, route, budget, repo_state, usage_estimate, work_plan):
    WORK_PROMPT.write_text(make_work_prompt(status, route, work_plan), encoding="utf-8")
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
        f"- Work 5-hour remaining (manual): {budget.get('work_window_percent')}",
        f"- Work weekly remaining (manual): {budget.get('work_week_percent')}",
        f"- Claude remaining (manual): {budget.get('claude_percent')}",
        f"- branch: {repo_state.get('branch')}",
        f"- HEAD: {repo_state.get('head')}",
        f"- working tree dirty: **{repo_state.get('dirty')}**",
        "",
        "## Estimated Work usage if AI is needed",
    ]
    if isinstance(usage_estimate, dict) and usage_estimate.get("models"):
        for item in usage_estimate["models"]:
            rng=item.get("estimated_five_hour_drop_percent",{})
            lines.append(
                f"- {item.get('model')}: ~{rng.get('low')}%-{rng.get('high')}% "
                f"({item.get('risk_band')}; {item.get('estimate_source')})"
            )
        lines.append(
            "- ranges are estimates, not guaranteed costs; they improve as real project samples are logged."
        )
    else:
        lines.append(f"- unavailable: {usage_estimate.get('error') if isinstance(usage_estimate,dict) else usage_estimate}")
    lines.append("")
    lines += [
        "## Pre-flight Work plan",
        f"- decision: **{work_plan.get('decision')}**",
        f"- model: {work_plan.get('recommended_model')}",
        f"- reasoning: {work_plan.get('reasoning')}",
        f"- Fast mode: {'ON' if work_plan.get('fast_mode') else 'OFF'}",
        f"- amended scope: {work_plan.get('scope')}",
        f"- planner reason: {work_plan.get('reason')}",
        "",
    ]
    if route == "LOCAL_SCRIPT":
        lines.append("The local deterministic runner should handle this without spending GPT Work or Claude allowance.")
    elif route == "WAIT_FOR_WORK_RESET":
        lines.append("Do not start this Work task yet. Preserve the current allowance and wait for the tighter reset while local/normal-Chat work continues.")
    elif route == "SPLIT_BEFORE_WORK":
        lines.append("Do not launch the task as currently scoped. Use the amended scope above as the next smaller proof, then re-run preflight.")
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

def file_signature(path):
    try:
        path = Path(path)
        return [path.name, path.stat().st_mtime_ns] if path.is_file() else None
    except (OSError, TypeError, ValueError):
        return None

def latest_checkpoint_signature():
    try:
        files = list((ROOT / "checkpoints" / "v15_manual").glob("*v15f*.blend"))
        latest = max(files, key=lambda p: p.stat().st_mtime_ns) if files else None
        return file_signature(latest) if latest else None
    except OSError:
        return None

def request_remote_sync(event):
    """Launch an isolated best-effort sync; it must never block the controller."""
    kwargs = {
        "cwd": str(ROOT),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen(
            [sys.executable, str(REMOTE_SYNC), "--sync", "--automatic"],
            **kwargs,
        )
        log(f"remote snapshot requested: {event}")
    except Exception as exc:
        log(f"remote snapshot request failed but controller continues: {type(exc).__name__}")

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
    last_remote_signature = None
    last_remote_sync = 0.0
    pending_remote_event = "controller_started"
    last_fetch = 0.0
    stopped_normally = False
    try:
        while True:
            if STOP_PATH.exists():
                log("Stop requested.")
                stopped_normally = True
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
            task_class=infer_task_class(status.get("next_action"))
            usage_estimate=estimate_models(task_class)
            work_plan=plan_work(task_class,cfg)

            if route=="GPT_WORK":
                decision=work_plan.get("decision")
                if decision=="WAIT":
                    route="WAIT_FOR_WORK_RESET"
                elif decision=="SPLIT":
                    route="SPLIT_BEFORE_WORK"
                elif decision=="LOCAL":
                    route="LOCAL_SCRIPT"
                elif decision not in ("START",):
                    route="NORMAL_CHAT"

            write_outputs(status, route, budget, repo_state, usage_estimate, work_plan)
            payload = {
                "updated_utc": utcnow(),
                "route": route,
                "v15f": status,
                "budget": budget,
                "repository": repo_state,
                "task_class": task_class,
                "usage_estimate": usage_estimate,
                "work_plan": work_plan,
                "next_file": str(NEXT_MD),
                "work_prompt": str(WORK_PROMPT),
                "claude_prompt": str(CLAUDE_PROMPT),
            }
            STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            safe_runner_state = read_json(REPORTS / "v15f_safe_runner_state.json", {})
            remote_signature = json.dumps(
                {
                    "route": route,
                    "action": status.get("next_action"),
                    "reason": status.get("reason"),
                    "version": status.get("version"),
                    "blend_exists": status.get("blend_exists"),
                    "candidate": file_signature(status.get("blend")),
                    "gates": status.get("gates"),
                    "latest_checkpoint": latest_checkpoint_signature(),
                    "safe_runner": {
                        "state": safe_runner_state.get("state"),
                        "last_action": safe_runner_state.get("last_action"),
                        "reason": safe_runner_state.get("reason"),
                    },
                },
                sort_keys=True,
            )
            if last_remote_signature is not None and remote_signature != last_remote_signature:
                pending_remote_event = "route, candidate, or gate changed"
            last_remote_signature = remote_signature

            signature = json.dumps(
                {"route": route, "action": status.get("next_action"), "reason": status.get("reason"),
                 "work_window": budget.get("work_window_percent"),
                 "work_week": budget.get("work_week_percent"),
                 "claude": budget.get("claude_percent"),
                 "head": repo_state.get("head")},
                sort_keys=True,
            )
            if signature != last_signature:
                log(
                    f"route={route} next={status.get('next_action')!r} "
                    f"work5h={budget.get('work_window_percent')} "
                    f"workweek={budget.get('work_week_percent')} "
                    f"claude={budget.get('claude_percent')} "
                    f"plan={work_plan.get('decision')}/{work_plan.get('recommended_model')}/{work_plan.get('reasoning')}"
                )
                last_signature = signature

            subprocess.run([sys.executable, str(V15_HANDOFF)], cwd=ROOT, check=False)
            if pending_remote_event and time.time() - last_remote_sync >= REMOTE_SYNC_DEBOUNCE_SECONDS:
                request_remote_sync(pending_remote_event)
                pending_remote_event = None
                last_remote_sync = time.time()
            try:
                LOCK_PATH.touch()
            except Exception:
                pass
            if args.once:
                stopped_normally = True
                break
            time.sleep(float(cfg.get("poll_seconds", 15)))
    finally:
        LOCK_PATH.unlink(missing_ok=True)
        STOP_PATH.unlink(missing_ok=True)
        log("EXIT")
        if stopped_normally:
            request_remote_sync("controller_stopped_normally")

if __name__ == "__main__":
    main()
