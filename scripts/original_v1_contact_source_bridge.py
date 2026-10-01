#!/usr/bin/env python3
"""Verify the project-owned exercise/contact source bridge without running the runtime."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, digest, ensure_finite

SPEC = "ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.json"
HELPER = "scripts/original_v1_contact_source_bridge.py"


def require(pattern: str, text: str, label: str, flags: int = re.S):
    match = re.search(pattern, text, flags)
    if not match:
        raise ValueError(f"{label} source signature missing or changed")
    return match


def close(actual: float, expected: float, label: str, tol: float = 1e-9) -> None:
    if abs(actual - expected) > tol:
        raise ValueError(f"{label} differs: {actual} != {expected}")


def vec_match(text: str, name: str) -> tuple[float, float, float]:
    m = require(
        rf"const\s+{re.escape(name)}\s*=\s*vec3\(\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*\)",
        text,
        name,
    )
    return tuple(float(x) for x in m.groups())


def root_pair(text: str, start_name: str, peak_name: str, with_pitch: bool):
    if with_pitch:
        pat = r"const\s+{}\s*=\s*\{{\s*pitch:\s*([-+]?\d+(?:\.\d+)?)\s*,\s*root:\s*\{{\s*y:\s*([-+]?\d+(?:\.\d+)?)\s*,\s*z:\s*([-+]?\d+(?:\.\d+)?)\s*\}}\s*\}}"
        a = require(pat.format(re.escape(start_name)), text, start_name)
        b = require(pat.format(re.escape(peak_name)), text, peak_name)
        return tuple(map(float, a.groups())), tuple(map(float, b.groups()))
    pat = r"const\s+{}\s*=\s*\{{\s*y:\s*([-+]?\d+(?:\.\d+)?)\s*,\s*z:\s*([-+]?\d+(?:\.\d+)?)\s*\}}"
    a = require(pat.format(re.escape(start_name)), text, start_name)
    b = require(pat.format(re.escape(peak_name)), text, peak_name)
    return tuple(map(float, a.groups())), tuple(map(float, b.groups()))


def verify_bridge(root: Path, spec: dict) -> dict:
    if spec.get("production_approved") is not False or spec.get("phase_complete") is not False:
        raise ValueError("source bridge cannot claim approval or phase completion")
    if spec.get("status") != "PREPARED_SOURCE_BRIDGE":
        raise ValueError("unexpected source bridge status")
    sources = spec.get("sources")
    if not isinstance(sources, list) or not sources or len(sources) != len(set(sources)):
        raise ValueError("source bridge paths invalid")
    texts = {}
    evidence = []
    for rel in sources:
        if not isinstance(rel, str):
            raise ValueError("source path must be string")
        path = (root / rel).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"source missing: {rel}")
        texts[rel] = path.read_text(encoding="utf-8")
        evidence.append({"path": rel, "sha256": digest(path)})

    push_def = texts["src/exercises/definitions/pushUp.ts"]
    hp = texts["src/exercises/families/horizontalPress.ts"]
    curl_def = texts["src/exercises/definitions/bicepCurl.ts"]
    curl = texts["src/exercises/families/curl.ts"]
    pull_def = texts["src/exercises/definitions/pullUp.ts"]
    vp = texts["src/exercises/families/verticalPull.ts"]
    attach = texts["src/equipment/attach.ts"]
    library = texts["src/equipment/library.ts"]
    types = texts["src/equipment/types.ts"]

    scenarios = spec["scenarios"]

    # Push-up source facts.
    p = scenarios["push_up"]
    require(r"horizontalPressFamily\(\s*\{[\s\S]*?id:\s*'push_up'", push_def, "push_up definition")
    top, bottom = root_pair(hp, "TOP", "BOTTOM", True)
    for actual, expected, label in zip(
        top,
        (p["root_endpoints"]["start"]["pitch_deg"], p["root_endpoints"]["start"]["y_m"], p["root_endpoints"]["start"]["z_m"]),
        ("push top pitch", "push top y", "push top z"),
    ):
        close(actual, expected, label)
    for actual, expected, label in zip(
        bottom,
        (p["root_endpoints"]["peak"]["pitch_deg"], p["root_endpoints"]["peak"]["y_m"], p["root_endpoints"]["peak"]["z_m"]),
        ("push bottom pitch", "push bottom y", "push bottom z"),
    ):
        close(actual, expected, label)
    hand = vec_match(hp, "HAND_L")
    for actual, expected, axis in zip(hand, (p["left_hand_world_m"]["x"], p["left_hand_world_m"]["y"], p["left_hand_world_m"]["z"]), "xyz"):
        close(actual, expected, f"push left hand {axis}")
    require(r"startPose:\s*\{[\s\S]*?label:\s*'Top'[\s\S]*?TOP\.root\.y[\s\S]*?TOP\.pitch", hp, "push start")
    require(r"peakPose:\s*\{[\s\S]*?label:\s*'Bottom'[\s\S]*?BOTTOM\.root\.y[\s\S]*?BOTTOM\.pitch", hp, "push peak")
    require(r"mode:\s*'world'[\s\S]*?position:\s*hand", hp, "push world hand lock")
    require(r"hands:\s*\{\s*grip:\s*'floor'", hp, "push floor grip")
    require(r"plantedContact\(\{\s*point:\s*\{\s*bone:\s*'toe_l'", hp, "push toe contact")

    # Curl/equipment source facts.
    c = scenarios["dumbbell_bicep_curl"]
    require(r"curlFamily\(\s*\{[\s\S]*?id:\s*'dumbbell_bicep_curl'[\s\S]*?grip:\s*'supinated'", curl_def, "bicep curl definition")
    require(r"kind:\s*'dumbbell'\s+as\s+const[\s\S]*?attachment:\s*\{\s*mode:\s*'hand'\s+as\s+const,\s*side,\s*socket:\s*'grip'", curl, "curl hand equipment")
    require(r"hands:\s*\{[\s\S]*?grip:\s*'dumbbell'", curl, "curl dumbbell grip")
    require(r"dumbbell:\s*\{[\s\S]*?sockets:\s*\[socket\(\s*'grip'\s*,\s*'Handle'\s*,\s*\[\s*0\s*,\s*0\s*,\s*0\s*\]\s*\)\]", library, "dumbbell grip socket")
    require(r"if\s*\(attachment\.mode\s*===\s*'hand'\)", attach, "hand attachment resolver")
    require(r"evaluation\.firstPartyEvaluation\.matrix\(hand\)\.clone\(\)\.multiply\(local\)", attach, "hand-driven equipment matrix")
    require(r"mode:\s*'hand'[\s\S]*?socket:\s*string", types, "hand attachment type")

    # Pull-up/static rack source facts.
    u = scenarios["pull_up"]
    require(r"verticalPullFamily\(\s*\{[\s\S]*?id:\s*'pull_up'", pull_def, "pull_up definition")
    hang, top2 = root_pair(vp, "HANG", "TOP", False)
    for actual, expected, label in zip(hang, (u["root_endpoints"]["start"]["y_m"], u["root_endpoints"]["start"]["z_m"]), ("pull hang y", "pull hang z")):
        close(actual, expected, label)
    for actual, expected, label in zip(top2, (u["root_endpoints"]["peak"]["y_m"], u["root_endpoints"]["peak"]["z_m"]), ("pull top y", "pull top z")):
        close(actual, expected, label)
    require(r"kind:\s*'squat_rack'[\s\S]*?attachment:\s*\{\s*mode:\s*'static'\s*\}", vp, "pull static rack")
    require(r"mode:\s*'equipment'[\s\S]*?equipmentId:\s*'rack'[\s\S]*?socket:\s*'pullup_l'", vp, "pull equipment lock")
    require(r"hands:\s*\{\s*grip:\s*'bar'", vp, "pull bar grip")
    require(r"socket\(\s*'pullup_l'[\s\S]*?\[\s*-PULLUP_GRIP_HALF_WIDTH\s*,\s*1\.97\s*,\s*0\s*\]", library, "pull left socket")
    require(r"socket\(\s*'pullup_r'[\s\S]*?\[\s*PULLUP_GRIP_HALF_WIDTH\s*,\s*1\.97\s*,\s*0\s*\]", library, "pull right socket")
    require(r"if\s*\(attachment\.mode\s*===\s*'static'\)", attach, "static equipment resolver")

    report = {
        "schema_version": 1,
        "status": "EVIDENCE_ONLY",
        "production_approved": False,
        "phase_complete": False,
        "runtime_executed": False,
        "source_bridge_status": "VERIFIED_CURRENT_MODEL_BRANCH_SOURCE",
        "source_files": evidence,
        "scenarios": scenarios,
        "required_future_evidence": spec.get("required_future_evidence", []),
        "limits": spec.get("limits", []),
    }
    ensure_finite(report)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        spec_path = ROOT / SPEC
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        out = args.json_out.resolve()
        if not out.is_relative_to(ROOT.resolve()):
            raise ValueError("output must remain inside repository")
        if out.exists():
            raise ValueError("output collision; preserve existing source evidence")
        report = verify_bridge(ROOT, spec)
        report.update({
            "bridge_spec": {"path": SPEC, "sha256": digest(spec_path)},
            "verifier": {"path": HELPER, "sha256": digest(ROOT / HELPER)},
            "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        })
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, indent=2) + "\n")
        print("CONTACT SOURCE BRIDGE VERIFIED — source facts only; runtime not executed")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
