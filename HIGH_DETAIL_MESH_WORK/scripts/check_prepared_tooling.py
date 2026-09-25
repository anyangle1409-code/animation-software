"""Static self-check for the prepared autonomous-studio tooling.

Safe to run at any phase. It does not need Blender, Node modules or network
access and does not modify candidates/source.

Checks:
- every Python helper in HIGH_DETAIL_MESH_WORK/scripts compiles;
- authoritative roadmap/phase/launcher files exist;
- prompt certification manifest has 16 unique families and 28 unique proving
  exercise IDs;
- every declared family state is recognised;
- every manifest family has a builder file path and proving set.

Writes reports/prepared_tooling_check.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "prepared_tooling_check.json"
MANIFEST = ROOT / "PROMPT_FAMILY_CERTIFICATION_MANIFEST.json"

REQUIRED = [
    "AUTONOMOUS_STUDIO_MASTER_PLAN.md",
    "BLENDER_ONLY_REMAINING.md",
    "CURRENT_STATE.md",
    "NEXT_ACTION.md",
    "WORK_MASTER_HANDOFF.md",
    "V15_DEEP_HAND_REBUILD_PLAN.md",
    "V15_WORK_HANDOFF.md",
    "V15_FAILURE_RECOVERY.md",
    "AUDIT_V15F_STAGE_A.bat",
    "AUDIT_V15F_DIGIT.bat",
    "V15F_STATUS.bat",
    "AUDIT_V15F_RING_PROOF.bat",
    "WORK_RESUME_AFTER_LIMIT.md",
    "PREPARE_V15F_LOCAL_PATCH.bat",
    "V15F_LOCAL_PATCH_PLAN.md",
    "START_V15_HAND.bat",
    "RUN_V15_POST_EDIT_ALL.bat",
    "OPEN_V15_REVIEW.bat",
    "PHASE_C_GRIP_REFIT_PLAN.md",
    "EVALUATE_PHASE_C_GRIP.bat",
    "OPEN_PHASE_C_GRIP_REVIEW.bat",
    "GENERATE_PHASE_C_GRIP_SEEDS.bat",
    "PHASE_C_GRIP_CANDIDATE_TEMPLATE.json",
    "PHASE_D_SKIN_MATERIAL_PLAN.md",
    "PHASE_E_SHOULDER_TOPOLOGY_PLAN.md",
    "PHASE_F_FINAL_BINDING_PLAN.md",
    "PHASE_G_MOVEMENT_ACTIVATION_PLAN.md",
    "PHASE_H_SELF_SUFFICIENT_GENERATION_PLAN.md",
    "FINAL_SYSTEM_ACCEPTANCE_PLAN.md",
    "MAKE_PHASE_D_SKIN_SWEEP.bat",
    "AUDIT_PHASE_F_SOURCE_RIG.bat",
    "VALIDATE_PHASE_F_RUNTIME.bat",
    "START_PROMPT_FAMILY_CERTIFICATION.bat",
    "AUDIT_PROMPT_GENERATION_COVERAGE.bat",
    "RUN_FINAL_SYSTEM_ACCEPTANCE.bat",
    "PROMPT_FAMILY_CERTIFICATION_MANIFEST.json",
    "PROMPT_FAMILY_CERTIFICATION_MATRIX.md",
    "PROMPT_FAMILY_CERTIFICATION_TEMPLATE.md",
]

VALID_STATES = {"CERTIFIED", "NOT_CERTIFIED", "IN_REVIEW", "BLOCKED"}

def main():
    failures = []
    warnings = []
    details = {}

    syntax = {}
    for path in sorted((ROOT / "scripts").glob("*.py")):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
            syntax[path.name] = "PASS"
        except Exception as exc:
            syntax[path.name] = f"{type(exc).__name__}: {exc}"
            failures.append(f"Python syntax failure: {path.name}: {exc}")
    details["python_syntax"] = syntax
    details["python_script_count"] = len(syntax)

    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    details["missing_required_files"] = missing
    if missing:
        failures.append("Missing prepared files: " + ", ".join(missing))

    if not MANIFEST.is_file():
        failures.append("Missing prompt family certification manifest.")
        manifest = {}
    else:
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception as exc:
            manifest = {}
            failures.append(f"Invalid prompt certification manifest JSON: {exc}")

    families = manifest.get("families", [])
    family_ids = [x.get("id") for x in families]
    exercise_ids = [
        exercise
        for family in families
        for exercise in family.get("library", [])
    ]
    states = [x.get("status") for x in families]

    details["family_count"] = len(families)
    details["unique_family_count"] = len(set(family_ids))
    details["proving_exercise_count"] = len(exercise_ids)
    details["unique_proving_exercise_count"] = len(set(exercise_ids))
    details["certified_families"] = [
        x.get("id") for x in families if x.get("status") == "CERTIFIED"
    ]
    details["unresolved_families"] = [
        {"id": x.get("id"), "status": x.get("status")}
        for x in families if x.get("status") != "CERTIFIED"
    ]

    if len(families) != 16:
        failures.append(f"Expected 16 family entries, found {len(families)}.")
    if len(set(family_ids)) != len(family_ids):
        failures.append("Duplicate family IDs in certification manifest.")
    if len(exercise_ids) != 28 or len(set(exercise_ids)) != 28:
        failures.append(
            f"Expected 28 unique proving exercise IDs, found "
            f"{len(exercise_ids)} entries / {len(set(exercise_ids))} unique."
        )
    invalid_states = sorted({x for x in states if x not in VALID_STATES})
    if invalid_states:
        failures.append("Unknown certification states: " + ", ".join(map(str, invalid_states)))

    for family in families:
        fid = family.get("id", "<missing>")
        if not family.get("builder"):
            failures.append(f"{fid}: missing builder name.")
        if not family.get("file"):
            failures.append(f"{fid}: missing builder file path.")
        if not family.get("library"):
            failures.append(f"{fid}: empty proving set.")
        if family.get("status") != "CERTIFIED" and not family.get("refusal_marker"):
            warnings.append(f"{fid}: no refusal_marker recorded for unresolved family.")

    report = {
        "pass": not failures,
        "failures": failures,
        "warnings": warnings,
        "details": details,
        "note": (
            "Static prepared-tooling check only. Phase-specific runtime, Blender, "
            "Git and latest-source checks remain separate."
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
