"""Generate a concise interruption/resume handoff for the current V15f state."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
VERSION = "v15f_deep_hand_rebuild"
BLEND = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"
OUT = ROOT / "V15F_LATEST_HANDOFF.md"
DIGITS = ("ring_L", "ring_R", "pinky_L", "pinky_R")

def git(*args):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=REPO, text=True, stderr=subprocess.STDOUT
        ).strip()
    except Exception as exc:
        return f"ERROR: {exc}"

def read_json(path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_error": str(exc)}

def status_text():
    try:
        p = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "v15f_status.py")],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return json.loads(p.stdout)
    except Exception as exc:
        return {
            "next_action": "Run V15F_STATUS.bat",
            "reason": f"Could not parse status: {exc}",
        }

def state(path):
    data = read_json(path)
    if data is None:
        return "missing"
    if data.get("_error"):
        return "unreadable"
    return "PASS" if data.get("pass") is True else "FAIL"

def main():
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain")
    status = status_text()

    checkpoints = sorted(
        (ROOT / "checkpoints" / "v15_manual").glob(f"{VERSION}_checkpoint_*.blend")
    )
    audit = read_json(ROOT / "reports" / f"audit_{VERSION}_blender.json")
    stage_a = read_json(ROOT / "reports" / "v15f_stage_a_gate.json")

    lines = [
        "# V15f latest interruption handoff",
        "",
        "Generated automatically from local artifacts.",
        "",
        "## Repository",
        f"- branch: {branch}",
        f"- HEAD: {head}",
        f"- working tree dirty: {'yes' if dirty and not dirty.startswith('ERROR:') else 'no'}",
        "",
        "## Candidate",
        f"- Blend: {BLEND.name} — {'present' if BLEND.is_file() else 'missing'}",
        f"- checkpoints: {len(checkpoints)}",
    ]
    if checkpoints:
        lines.append(f"- latest checkpoint: {checkpoints[-1].relative_to(ROOT)}")

    lines += ["", "## Incremental gates"]
    proof = ROOT / "reports" / "v15f_ring_l_proof_gate.json"
    lines.append(f"- ring_L proof: {state(proof)}")
    visual = read_json(ROOT / "reports" / "v15f_ring_visual_decision.json")
    if visual:
        lines.append(
            f"- ring_L visual: {visual.get('decision', 'UNKNOWN')} "
            f"— {visual.get('notes', '')}"
        )
    else:
        lines.append("- ring_L visual: missing")
    for digit in DIGITS:
        path = ROOT / "reports" / f"v15f_{digit}_incremental_gate.json"
        lines.append(f"- {digit}: {state(path)}")
    lines.append(
        f"- Stage A: {state(ROOT / 'reports' / 'v15f_stage_a_gate.json')}"
    )
    stage_visual = read_json(ROOT / "reports" / "v15f_stage_a_visual_decision.json")
    if stage_visual:
        lines.append(
            f"- Stage A visual: {stage_visual.get('decision', 'UNKNOWN')} "
            f"— {stage_visual.get('notes', '')}"
        )
    else:
        lines.append("- Stage A visual: missing")

    lines += ["", "## Stage B"]
    for key in ("index_L", "index_R", "middle_L", "middle_R"):
        gate = state(ROOT / "reports" / f"v15f_stage_b_{key}_gate.json")
        visual = read_json(ROOT / "reports" / f"v15f_stage_b_{key}_visual_decision.json")
        visual_text = (
            f"{visual.get('decision', 'UNKNOWN')} — {visual.get('notes', '')}"
            if visual else "missing"
        )
        lines.append(f"- {key}: numeric {gate}; visual {visual_text}")

    if audit:
        lines += [
            "",
            "## Latest Blender audit",
            f"- general invariant pass: {audit.get('pass')}",
            f"- total >100° digit folds: "
            f"{audit.get('baseline_topology', {}).get('digit_folds_over_100deg')} -> "
            f"{audit.get('candidate_topology', {}).get('digit_folds_over_100deg')}",
            f"- protected max move: {audit.get('protected_max_move_mm')} mm",
            f"- non-digit max move: {audit.get('non_digit_max_move_mm')} mm",
            f"- original digit weight rows changed: {audit.get('original_digit_weight_rows_changed')}",
        ]
        movement = audit.get("per_digit_original_movement_vs_v13e", {})
        if movement:
            lines.append("- original source-vertex movement by digit:")
            for key in sorted(movement):
                item = movement[key]
                lines.append(
                    f"  - {key}: max {item.get('max_move_mm', 0):.6f} mm; "
                    f"moved {item.get('moved_source_vertices', 0)}"
                )

    if stage_a and stage_a.get("failures"):
        lines += ["", "## Stage-A failures"]
        lines += [f"- {item}" for item in stage_a["failures"]]

    lines += [
        "",
        "## Next action",
        status.get("next_action", "Run V15F_STATUS.bat"),
        "",
        status.get("reason", ""),
        "",
        "## Resume references",
        "- WORK_RESUME_AFTER_LIMIT.md",
        "- V15F_LOCAL_PATCH_PLAN.md",
        "- V15F_FAILURE_RECOVERY.md",
        "",
        "Do not promote geometry or begin Phase C from this handoff alone.",
    ]

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT)
    print("\n".join(lines))

if __name__ == "__main__":
    main()
