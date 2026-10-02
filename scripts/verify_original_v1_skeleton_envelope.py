#!/usr/bin/env python3
"""Check every joint of every stress pose against the project movement envelope (python only; evidence, never approval).

python scripts/verify_original_v1_skeleton_envelope.py <joint_kinematics.json> [--json-out out.json]

The kinematics file comes from scripts/audit_original_v1_joint_kinematics_blender.py. All samples (not just the final pose) are
checked. Also checks elbow hinge purity (the forearm's abduction component stays within the carrying-angle range) and left/right
symmetry of mirrored poses (excluding the intentionally asymmetric lunge).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_envelope():
    env = json.loads((ROOT / "ORIGINAL_V1_SKELETON_MOVEMENT_ENVELOPE.json").read_text(encoding="utf-8"))
    table = {}
    for j in env["joints"]:
        for b in j["bones"]:
            table[b] = j
    return env, table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kinematics")
    ap.add_argument("--json-out")
    a = ap.parse_args()
    env, table = load_envelope()
    k = json.loads(Path(a.kinematics).read_text(encoding="utf-8"))
    violations, checked = [], 0
    for pose in k["poses"]:
        for sample in pose["samples"]:
            for bone, comp in sample["joints"].items():
                base = bone[:-2] if bone.endswith(("_l", "_r")) else bone
                j = table.get(base)
                if j is None:
                    continue
                for key in ("flex_deg", "abd_deg", "twist_deg"):
                    if key not in comp:
                        continue
                    lo, hi = j[key]
                    checked += 1
                    v = comp[key]
                    if v < lo - 1e-6 or v > hi + 1e-6:
                        violations.append({"pose": pose["pose"], "fraction": sample["fraction"], "bone": bone, "component": key,
                                           "value_deg": v, "envelope_deg": [lo, hi], "joint": j["id"]})
    asym = []
    for pose in k["poses"]:
        if pose["pose"] == "lunge":
            continue
        j = pose["samples"][-1]["joints"]
        for b, comp in j.items():
            if b.endswith("_l") and b[:-2] + "_r" in j:
                r = j[b[:-2] + "_r"]
                for key in ("flex_deg", "twist_deg"):
                    if key in comp and abs(comp[key] - (r[key] if key == "flex_deg" else -r[key])) > 0.6:
                        asym.append({"pose": pose["pose"], "bone": b, "component": key, "left": comp[key], "right": r[key]})
    out = {"schema_version": 1, "envelope_revision": env["revision"], "kinematics": Path(a.kinematics).name,
           "source_candidate": k.get("source_candidate"), "source_candidate_sha256": k.get("source_candidate_sha256"),
           "pose_definition_script_sha256": k.get("pose_definition_script_sha256"), "components_checked": checked,
           "violations": violations, "left_right_asymmetries": asym,
           "status": "PASS" if not violations and not asym else "FLAGGED",
           "note": "Envelope check is evidence, not approval; ranges are reference-based project limits (see the envelope file)."}
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"SKELETON ENVELOPE {out['status']}: {checked} components checked, {len(violations)} violations, {len(asym)} L/R asymmetries")
    for v in violations[:25]:
        print("  ", v)
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
