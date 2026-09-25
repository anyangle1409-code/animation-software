"""Report the exact next V15f action from local artifacts.

This does not modify geometry or run Blender. It is safe after interruptions.
A gate report is considered current only when it is at least as new as the
V15f Blend; otherwise the Blend changed after that audit and the gate is stale.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v15f_deep_hand_rebuild"
BLEND = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.blend"
DIGITS = ("ring_L", "ring_R", "pinky_L", "pinky_R")

def read_json(path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": str(exc)}

def gate_state(path, timestamp_sensitive=False):
    data = read_json(path)
    if data is None:
        return {"exists": False, "current": False, "pass": None, "path": str(path)}
    current = True
    if timestamp_sensitive:
        current = BLEND.is_file() and path.stat().st_mtime >= BLEND.stat().st_mtime
    return {
        "exists": True,
        "current": current,
        "pass": data.get("pass"),
        "path": str(path),
        "read_error": data.get("_read_error"),
    }

def main():
    result = {
        "version": VERSION,
        "blend_exists": BLEND.is_file(),
        "blend": str(BLEND),
        "gates": {},
        "next_action": None,
        "reason": None,
    }

    if not BLEND.is_file():
        result["next_action"] = "PREPARE_V15F_LOCAL_PATCH.bat"
        result["reason"] = "V15f Blend does not exist yet."
        print(json.dumps(result, indent=2))
        return

    proof = gate_state(ROOT / "reports" / "v15f_ring_l_proof_gate.json")
    result["gates"]["ring_L_proof"] = proof

    digit_states = {}
    for digit in DIGITS:
        state = gate_state(ROOT / "reports" / f"v15f_{digit}_incremental_gate.json")
        digit_states[digit] = state
        result["gates"][digit] = state

    stage_a = gate_state(ROOT / "reports" / "v15f_stage_a_gate.json")
    result["gates"]["stage_A"] = stage_a

    # Passed per-digit gates deliberately remain valid while later digits are
    # edited. The final Stage-A/full audit catches cross-digit/global regressions.
    # This avoids sending Work back to ring_L every time ring_R/pinky is saved.
    sequence = [
        ("ring_L", "AUDIT_V15F_RING_PROOF.bat", proof),
        ("ring_R", "AUDIT_V15F_DIGIT.bat ring_R", digit_states["ring_R"]),
        ("pinky_L", "AUDIT_V15F_DIGIT.bat pinky_L", digit_states["pinky_L"]),
        ("pinky_R", "AUDIT_V15F_DIGIT.bat pinky_R", digit_states["pinky_R"]),
    ]

    for digit, command, state in sequence:
        if not state["exists"]:
            result["next_action"] = (
                f"Inspect/edit {digit} only, save/checkpoint, then run: {command}"
            )
            result["reason"] = f"{digit} gate is missing."
            print(json.dumps(result, indent=2))
            return
        if state["pass"] is not True:
            result["next_action"] = (
                f"Repair {digit} only and rerun: {command}"
            )
            result["reason"] = f"{digit} gate is current but not passing."
            print(json.dumps(result, indent=2))
            return

    if not stage_a["exists"]:
        result["next_action"] = "AUDIT_V15F_STAGE_A.bat"
        result["reason"] = "All four incremental ring/pinky gates pass; Stage A is missing."
        print(json.dumps(result, indent=2))
        return
    if stage_a["pass"] is not True:
        result["next_action"] = (
            "Read reports/v15f_stage_a_gate.json and repair only the failing "
            "ring/pinky digit(s), then rerun AUDIT_V15F_STAGE_A.bat"
        )
        result["reason"] = "Stage A is current but failing."
        print(json.dumps(result, indent=2))
        return

    full_audit = gate_state(
        ROOT / "reports" / f"audit_{VERSION}_blender.json",
        timestamp_sensitive=True,
    )
    result["gates"]["full_blender_audit"] = full_audit

    dressed = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.glb"
    review = ROOT / f"V15_POST_EDIT_REPORT_{VERSION}.md"

    if not full_audit["current"]:
        result["next_action"] = (
            "Stage A passes. Checkpoint, inspect/rebuild index/middle only where "
            "visibly needed, save, then run the full Blender audit."
        )
        result["reason"] = "Ring/pinky Stage A cleared; whole-hand audit is stale."
    elif full_audit["pass"] is not True:
        result["next_action"] = "Repair the whole-hand Blender audit failure before export."
        result["reason"] = "Current full Blender audit is failing."
    elif not dressed.is_file() or dressed.stat().st_mtime < BLEND.stat().st_mtime:
        result["next_action"] = f"RUN_V15_POST_EDIT_ALL.bat {VERSION}"
        result["reason"] = "Whole-hand Blender audit passes; GLB/post-edit pipeline is missing/stale."
    elif not review.is_file() or review.stat().st_mtime < dressed.stat().st_mtime:
        result["next_action"] = f"RUN_V15_POST_EDIT_ALL.bat {VERSION}"
        result["reason"] = "Export exists but consolidated review/report is missing/stale."
    else:
        result["next_action"] = f"OPEN_V15_REVIEW.bat {VERSION}"
        result["reason"] = "Current V15f post-edit artifacts exist; inspect final review gate."

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
