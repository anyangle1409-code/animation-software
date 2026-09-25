"""Local safe V15f deterministic runner.

This process never edits mesh geometry and never makes visual/pass promotion
decisions. It only runs a strict whitelist of already-prepared deterministic
audit/render/report commands when V15F_STATUS says they are due.

It is useful if GPT Work reaches a usage limit immediately after saving an edit:
the local machine can still finish audits/renders and write the handoff.

Default lifetime: 8 hours.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BLEND=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
REPORTS=ROOT/"reports"
STATE=REPORTS/"v15f_safe_runner_state.json"
LOG=REPORTS/"v15f_safe_runner.log"
LOCK=REPORTS/"v15f_safe_runner.lock"
STOP=REPORTS/"v15f_safe_runner.stop"
STATUS_SCRIPT=ROOT/"scripts"/"v15f_status.py"
HANDOFF_SCRIPT=ROOT/"scripts"/"write_v15f_handoff.py"

ALLOWED_DIGITS={"ring_R","pinky_L","pinky_R","index_L","index_R","middle_L","middle_R"}

def now():
    return datetime.now(timezone.utc).isoformat()

def log(message):
    REPORTS.mkdir(parents=True,exist_ok=True)
    line=f"[{now()}] {message}"
    print(line,flush=True)
    with LOG.open("a",encoding="utf-8") as f:
        f.write(line+"\n")

def status():
    p=subprocess.run(
        [sys.executable,str(STATUS_SCRIPT)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if p.returncode:
        raise RuntimeError("V15F_STATUS failed:\n"+p.stdout)
    return json.loads(p.stdout)

def run_bat(name,*args):
    if os.name!="nt":
        raise RuntimeError("The prepared V15f .bat runner is intended for Windows.")
    cmd=["cmd","/c",name,*args]
    log("RUN "+" ".join(cmd))
    p=subprocess.run(
        cmd,cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,encoding="utf-8",errors="replace",
    )
    with LOG.open("a",encoding="utf-8") as f:
        f.write(p.stdout+"\n")
    log(f"DONE {name} rc={p.returncode}")
    subprocess.run([sys.executable,str(HANDOFF_SCRIPT)],cwd=ROOT,check=False)
    return p.returncode

def pure_command(action):
    if action=="AUDIT_V15F_STAGE_A.bat":
        return ("AUDIT_V15F_STAGE_A.bat",)
    if action=="GENERATE_V15F_RING_VISUAL_PROOF.bat":
        return ("GENERATE_V15F_RING_VISUAL_PROOF.bat",)
    if action=="GENERATE_V15F_STAGE_A_VISUAL_PROOF.bat":
        return ("GENERATE_V15F_STAGE_A_VISUAL_PROOF.bat",)
    m=re.fullmatch(r"GENERATE_V15F_STAGE_B_VISUAL\.bat (index_L|index_R|middle_L|middle_R)",action)
    if m:
        return ("GENERATE_V15F_STAGE_B_VISUAL.bat",m.group(1))
    m=re.fullmatch(r"RUN_V15_POST_EDIT_ALL\.bat (v15f_deep_hand_rebuild)",action)
    if m:
        return ("RUN_V15_POST_EDIT_ALL.bat",m.group(1))
    return None

def save_triggered_command(action):
    if "AUDIT_V15F_RING_PROOF.bat" in action:
        return ("AUDIT_V15F_RING_PROOF.bat",)
    m=re.search(r"AUDIT_V15F_DIGIT\.bat (ring_R|pinky_L|pinky_R)",action)
    if m:
        return ("AUDIT_V15F_DIGIT.bat",m.group(1))
    m=re.search(
        r"AUDIT_V15F_STAGE_B_DIGIT\.bat (index_L|index_R|middle_L|middle_R)",
        action,
    )
    if m:
        return ("AUDIT_V15F_STAGE_B_DIGIT.bat",m.group(1))
    return None

def write_state(**extra):
    data={
        "pid":os.getpid(),
        "updated_utc":now(),
        "blend_mtime_ns":BLEND.stat().st_mtime_ns if BLEND.is_file() else None,
        **extra,
    }
    STATE.write_text(json.dumps(data,indent=2),encoding="utf-8")

def acquire_lock(max_hours):
    REPORTS.mkdir(parents=True,exist_ok=True)
    if LOCK.exists():
        age=time.time()-LOCK.stat().st_mtime
        if age < max_hours*3600+3600:
            raise SystemExit(
                f"Safe runner lock already exists: {LOCK}. "
                "Use STOP_V15F_SAFE_RUNNER.bat or remove a stale lock after confirming no runner is active."
            )
        LOCK.unlink(missing_ok=True)
    LOCK.write_text(json.dumps({"pid":os.getpid(),"started_utc":now()}),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-hours",type=float,default=8.0)
    ap.add_argument("--poll-seconds",type=float,default=8.0)
    args=ap.parse_args()

    acquire_lock(args.max_hours)
    STOP.unlink(missing_ok=True)
    started=time.time()
    last_blend_mtime=BLEND.stat().st_mtime_ns if BLEND.is_file() else None
    last_pure_signature=None
    last_action=None
    log(f"START pid={os.getpid()} max_hours={args.max_hours}")
    write_state(state="running",last_action=None)

    try:
        while True:
            if STOP.exists():
                log("STOP flag detected")
                break
            if time.time()-started >= args.max_hours*3600:
                log("Max lifetime reached")
                break

            try:
                s=status()
            except Exception as exc:
                log(f"STATUS ERROR {exc}")
                write_state(state="status_error",error=str(exc))
                time.sleep(args.poll_seconds)
                continue

            action=str(s.get("next_action") or "")
            reason=str(s.get("reason") or "")
            current_mtime=BLEND.stat().st_mtime_ns if BLEND.is_file() else None
            blend_changed=current_mtime is not None and current_mtime!=last_blend_mtime

            if action!=last_action:
                log(f"STATUS next={action!r} reason={reason!r}")
                last_action=action

            # Stop once only the final full review is left.
            if action.startswith("OPEN_V15_REVIEW.bat"):
                subprocess.run([sys.executable,str(HANDOFF_SCRIPT)],cwd=ROOT,check=False)
                write_state(state="final_visual_review_required",last_action=action)
                log("Final visual review required; deterministic runner exiting")
                break

            pure=pure_command(action)
            if pure:
                signature=" ".join(pure)
                if signature!=last_pure_signature:
                    rc=run_bat(*pure)
                    last_pure_signature=signature
                    write_state(
                        state="ran_deterministic_command",
                        last_action=action,
                        last_command=signature,
                        last_returncode=rc,
                    )
                    # Never spin-retry a failed deterministic command.
                    time.sleep(args.poll_seconds)
                    continue

            save_cmd=save_triggered_command(action)
            if save_cmd and blend_changed:
                signature=" ".join(save_cmd)+f"@{current_mtime}"
                rc=run_bat(*save_cmd)
                write_state(
                    state="ran_save_triggered_command",
                    last_action=action,
                    last_command=signature,
                    last_returncode=rc,
                )
                last_blend_mtime=current_mtime
                last_pure_signature=None
                time.sleep(args.poll_seconds)
                continue

            if blend_changed:
                # Record the save even if the current state requires visual
                # judgement rather than an audit.
                log(f"Blend save observed mtime_ns={current_mtime}; no safe auto-command due")
                last_blend_mtime=current_mtime

            write_state(state="waiting",last_action=action,reason=reason)
            time.sleep(args.poll_seconds)
    finally:
        subprocess.run([sys.executable,str(HANDOFF_SCRIPT)],cwd=ROOT,check=False)
        write_state(state="stopped",last_action=last_action)
        LOCK.unlink(missing_ok=True)
        STOP.unlink(missing_ok=True)
        log("EXIT")

if __name__=="__main__":
    main()
