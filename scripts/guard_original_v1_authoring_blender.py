"""Keep ORIGINAL v1 O2 authoring inside the first-party Blender boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from original_v1_authoring_boundary import ROOT, TAINT_RECORD, inspect_boundary, write_taint

SESSION_RECORD = ROOT / "ORIGINAL_V1_WORK" / "AUTHORING_SESSION.json"
_guard_running = False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
        ).strip()
    except Exception:
        return "unknown"


if TAINT_RECORD.exists():
    raise RuntimeError(
        "AUTHORING_TAINT.json already exists. Recover/inspect the last clean checkpoint; "
        "do not delete the record merely to make the guard pass."
    )

initial = inspect_boundary(require_guarded=False)
if initial:
    raise RuntimeError(f"Guarded-authoring preflight failed: {initial}")

scene = bpy.context.scene
scene["hgpt_guarded_authoring"] = True
scene["hgpt_authoring_tainted"] = False
scene["hgpt_authoring_guard_version"] = 1
scene["hgpt_authoring_session_started_utc"] = datetime.now(timezone.utc).isoformat()

blend_path = Path(bpy.data.filepath)
SESSION_RECORD.write_text(json.dumps({
    "started_utc": scene["hgpt_authoring_session_started_utc"],
    "blend": bpy.data.filepath,
    "blend_sha256_at_start": sha256(blend_path),
    "branch": git_value("branch", "--show-current"),
    "head": git_value("rev-parse", "HEAD"),
    "policy": "ORIGINAL v1 O2: project-authored geometry only; no import/append/link/reference image/third-party add-on transfer.",
}, indent=2) + "\n", encoding="utf-8")


def check(source: str) -> None:
    global _guard_running
    if _guard_running or bool(bpy.context.scene.get("hgpt_authoring_tainted")):
        return
    _guard_running = True
    try:
        blockers = inspect_boundary(require_guarded=False)
        if blockers:
            record = write_taint(blockers, source)
            print("HGPT AUTHORING TAINTED")
            print(json.dumps(record, indent=2))
    finally:
        _guard_running = False


@persistent
def hgpt_guard_depsgraph(_scene, _depsgraph) -> None:
    check("depsgraph_update_post")


@persistent
def hgpt_guard_save_pre(_dummy) -> None:
    check("save_pre")


@persistent
def hgpt_guard_load_post(_dummy) -> None:
    check("load_post")


def install(handler_list, handler) -> None:
    for existing in list(handler_list):
        if getattr(existing, "__name__", "") == handler.__name__:
            handler_list.remove(existing)
    handler_list.append(handler)


install(bpy.app.handlers.depsgraph_update_post, hgpt_guard_depsgraph)
install(bpy.app.handlers.save_pre, hgpt_guard_save_pre)
install(bpy.app.handlers.load_post, hgpt_guard_load_post)

print("=" * 72)
print("HGPT ORIGINAL v1 GUARDED AUTHORING ACTIVE")
print("Edit only HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD with stock Blender tools.")
print("Import/append/link, external images, add-ons, extra objects/materials or saved helpers taint the session.")
print("After each region run CHECKPOINT_ORIGINAL_V1_O2.bat <region>.")
print("=" * 72)
