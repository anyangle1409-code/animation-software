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
STAGE_B_ORDER = ("index_L", "index_R", "middle_L", "middle_R")
RING_VISUAL = ROOT / "reports" / "v15f_ring_visual_decision.json"
RING_BOARD = ROOT / "renders_v15f_ring_proof" / "V15F_V13E_RING_L_PROOF.jpg"
AUDIT = ROOT / "reports" / f"audit_{VERSION}_blender.json"
STAGE_A_VISUAL = ROOT / "reports" / "v15f_stage_a_visual_decision.json"
STAGE_A_BOARD = ROOT / "renders_v15f_stage_a" / "V15F_V13E_STAGE_A_RING_PINKY_PROOF.jpg"

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

def current_surface_fingerprints():
    audit = read_json(AUDIT)
    if not audit:
        return {}
    return {
        key: item.get("surface_fingerprint_sha256")
        for key, item in (
            audit.get("candidate_topology", {})
            .get("per_digit_surface", {})
            .items()
        )
    }

def visual_decision_state():
    data = read_json(RING_VISUAL)
    if data is None:
        return {
            "exists": False,
            "current": False,
            "pass": None,
            "board_exists": RING_BOARD.is_file(),
            "path": str(RING_VISUAL),
        }
    fingerprints = current_surface_fingerprints()
    current = bool(
        RING_BOARD.is_file()
        and data.get("surface_fingerprint_sha256")
        and data.get("surface_fingerprint_sha256") == fingerprints.get("ring_L")
    )
    return {
        "exists": True,
        "current": current,
        "pass": data.get("pass") if current else None,
        "decision": data.get("decision"),
        "notes": data.get("notes"),
        "board_exists": RING_BOARD.is_file(),
        "path": str(RING_VISUAL),
    }

def stage_a_visual_state():
    data = read_json(STAGE_A_VISUAL)
    if data is None:
        return {
            "exists": False,
            "current": False,
            "pass": None,
            "board_exists": STAGE_A_BOARD.is_file(),
            "path": str(STAGE_A_VISUAL),
        }
    fingerprints = current_surface_fingerprints()
    expected = data.get("surface_fingerprints_sha256") or {}
    current = bool(
        STAGE_A_BOARD.is_file()
        and expected
        and all(expected.get(key) == fingerprints.get(key) for key in expected)
    )
    return {
        "exists": True,
        "current": current,
        "pass": data.get("pass") if current else None,
        "decision": data.get("decision"),
        "notes": data.get("notes"),
        "board_exists": STAGE_A_BOARD.is_file(),
        "path": str(STAGE_A_VISUAL),
    }

def stage_b_visual_state(key):
    path = ROOT / "reports" / f"v15f_stage_b_{key}_visual_decision.json"
    board = ROOT / "renders_v15f_stage_b" / key / f"V15F_V13E_{key.upper()}_PROOF.jpg"
    data = read_json(path)
    if data is None:
        return {
            "exists": False,
            "current": False,
            "pass": None,
            "board_exists": board.is_file(),
            "path": str(path),
        }
    fingerprints = current_surface_fingerprints()
    current = bool(
        board.is_file()
        and data.get("surface_fingerprint_sha256")
        and data.get("surface_fingerprint_sha256") == fingerprints.get(key)
    )
    return {
        "exists": True,
        "current": current,
        "pass": data.get("pass") if current else None,
        "decision": data.get("decision"),
        "notes": data.get("notes"),
        "board_exists": board.is_file(),
        "path": str(path),
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
    ring_visual = visual_decision_state()
    result["gates"]["ring_L_visual"] = ring_visual

    digit_states = {}
    for digit in DIGITS:
        state = gate_state(ROOT / "reports" / f"v15f_{digit}_incremental_gate.json")
        digit_states[digit] = state
        result["gates"][digit] = state

    stage_a = gate_state(ROOT / "reports" / "v15f_stage_a_gate.json")
    result["gates"]["stage_A"] = stage_a
    stage_a_visual = stage_a_visual_state()
    result["gates"]["stage_A_visual"] = stage_a_visual

    if proof["exists"] and proof["pass"] is True:
        if not ring_visual["board_exists"]:
            result["next_action"] = "GENERATE_V15F_RING_VISUAL_PROOF.bat"
            result["reason"] = (
                "ring_L numeric proof passes, but matched visual proof images are missing."
            )
            print(json.dumps(result, indent=2))
            return
        if not ring_visual["exists"] or not ring_visual["current"]:
            result["next_action"] = (
                "OPEN_V15F_RING_VISUAL_PROOF.bat, inspect V13e vs V15f ring_L, "
                "then run: MARK_V15F_RING_VISUAL.bat pass|fail"
            )
            result["reason"] = (
                "ring_L numeric proof passes; an explicit visual verdict for the "
                "current Blend is still required before ring_R."
            )
            print(json.dumps(result, indent=2))
            return
        if ring_visual["pass"] is not True:
            result["next_action"] = (
                "Repair ring_L only, save/checkpoint, then rerun "
                "AUDIT_V15F_RING_PROOF.bat"
            )
            result["reason"] = (
                "The current ring_L visual proof is explicitly marked FAIL."
            )
            print(json.dumps(result, indent=2))
            return

    # Passed per-digit gates deliberately remain valid while later digits are
    # edited. The final Stage-A/full audit catches cross-digit/global regressions.
    # This avoids sending Work back to ring_L every time ring_R/pinky is saved.
    sequence = [
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

    if stage_a["pass"] is True:
        if not stage_a_visual["board_exists"]:
            result["next_action"] = "GENERATE_V15F_STAGE_A_VISUAL_PROOF.bat"
            result["reason"] = (
                "Stage A numeric gate passes, but the matched ring/pinky visual board is missing."
            )
            print(json.dumps(result, indent=2))
            return
        if not stage_a_visual["exists"] or not stage_a_visual["current"]:
            result["next_action"] = (
                "OPEN_V15F_STAGE_A_VISUAL_PROOF.bat, inspect V13e vs V15f "
                "ring/pinky, then run: MARK_V15F_STAGE_A_VISUAL.bat pass|fail"
            )
            result["reason"] = (
                "Stage A numeric gate passes; a current explicit visual verdict "
                "is required before index/middle."
            )
            print(json.dumps(result, indent=2))
            return
        if stage_a_visual["pass"] is not True:
            result["next_action"] = (
                "Repair only the visually failing ring/pinky digit(s), rerun their "
                "incremental gates, then rerun AUDIT_V15F_STAGE_A.bat"
            )
            result["reason"] = "The current Stage-A visual proof is explicitly marked FAIL."
            print(json.dumps(result, indent=2))
            return

    # Stage B — index/middle, one digit at a time. Each numeric pass must
    # receive an explicit current visual verdict before the next digit unlocks.
    for key in STAGE_B_ORDER:
        numeric = gate_state(ROOT / "reports" / f"v15f_stage_b_{key}_gate.json")
        visual = stage_b_visual_state(key)
        result["gates"][f"stage_B_{key}"] = numeric
        result["gates"][f"stage_B_{key}_visual"] = visual

        if not numeric["exists"]:
            result["next_action"] = (
                f"Inspect/edit {key} only, save/checkpoint, then run: "
                f"AUDIT_V15F_STAGE_B_DIGIT.bat {key}"
            )
            result["reason"] = f"Stage-B {key} numeric gate is missing."
            print(json.dumps(result, indent=2))
            return
        if numeric["pass"] is not True:
            result["next_action"] = (
                f"Repair {key} only and rerun: AUDIT_V15F_STAGE_B_DIGIT.bat {key}"
            )
            result["reason"] = f"Stage-B {key} numeric gate is failing."
            print(json.dumps(result, indent=2))
            return
        if not visual["board_exists"]:
            result["next_action"] = f"GENERATE_V15F_STAGE_B_VISUAL.bat {key}"
            result["reason"] = f"Stage-B {key} numeric gate passes; visual board is missing."
            print(json.dumps(result, indent=2))
            return
        if not visual["exists"] or not visual["current"]:
            result["next_action"] = (
                f"OPEN_V15F_STAGE_B_VISUAL.bat {key}, inspect V13e vs V15f, then run: "
                f"MARK_V15F_STAGE_B_VISUAL.bat {key} pass|fail"
            )
            result["reason"] = (
                f"Stage-B {key} numeric gate passes; a current visual verdict is required."
            )
            print(json.dumps(result, indent=2))
            return
        if visual["pass"] is not True:
            result["next_action"] = (
                f"Repair {key} only, save/checkpoint, then rerun "
                f"AUDIT_V15F_STAGE_B_DIGIT.bat {key}"
            )
            result["reason"] = f"Stage-B {key} visual proof is explicitly marked FAIL."
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
            "All Stage-A and Stage-B numeric+visual gates pass. Rerun the full "
            "V15 Blender audit before export."
        )
        result["reason"] = "All per-digit V15f gates are cleared; whole-hand audit is stale."
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
