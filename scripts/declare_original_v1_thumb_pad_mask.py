"""Declare the Phase 3C thumb-pad edit mask BEFORE any geometry changes (numpy only; touches no Blend).

python scripts/declare_original_v1_thumb_pad_mask.py <survey.json> <dump.npz> <out mask.json> [--margin-mm 0.6] [--falloff-mm 10]

The survey comes from scripts/survey_original_v1_thumb_pad_clearance_blender.py and the dump from
scripts/dump_original_v1_o4_pose_skinning_blender.py (both of the same candidate). The mask is computed by the rule in
scripts/original_v1_thumb_pad.py: thumb-region vertices within the falloff radius of a vertex that is inside the frozen
handle. The output lists the exact vertex ids and the rule parameters, and is committed before the edit so the audit
policy can use the SAME scope. It also states the planned maximum displacement, for plausibility only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import original_v1_thumb_pad as tp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("survey")
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--margin-mm", type=float, default=0.6)
    ap.add_argument("--falloff-mm", type=float, default=10.0)
    a = ap.parse_args()
    survey = json.loads(Path(a.survey).read_text(encoding="utf-8"))
    d = np.load(a.dump)
    rest, region = d["rest"], d["region"]
    rn = [str(x) for x in d["region_names"]]
    thumb_ids = np.nonzero(region == rn.index("thumb"))[0]
    side_of = lambda i: "l" if rest[i, 0] < 0 else "r"
    mask, disp, report = tp.plan(survey, rest, thumb_ids, side_of, a.margin_mm / 1000.0, a.falloff_mm / 1000.0)
    if not mask:
        raise SystemExit("no thumb vertex is inside the handle: nothing to declare")
    # mirror closure and mirror-symmetric displacement (the poses/handles are mirror images)
    key = {tuple(np.round(rest[i] * [-1, 1, 1], 5)): int(i) for i in range(len(rest))}
    m = set(mask)
    twin = {i: key.get(tuple(np.round(rest[i], 5))) for i in m}
    if any(t is None for t in twin.values()):
        raise SystemExit("mask vertex without a mirror twin")
    if any(t not in m for t in twin.values()):
        raise SystemExit("mask is not mirror-closed: " + str(sum(1 for t in twin.values() if t not in m)) + " twins missing")
    asym = max(float(np.abs(disp[i] * np.array([-1, 1, 1]) - disp[twin[i]]).max()) for i in m)
    if asym > 1e-6:
        raise SystemExit(f"planned displacement is not mirror-symmetric (max {asym:.2e} m)")
    after = tp.clearance_after(survey, rest, disp, side_of)
    inside_before = {i for side in "lr" for i in tp.inside_vertices(survey, side, [j for j in thumb_ids if side_of(j) == side])}
    worst = min(after[i] for i in inside_before)
    rec = {
        "declared_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "3C", "declared_before_edit": True,
        "source_survey": Path(a.survey).name, "source_survey_sha256": hashlib.sha256(Path(a.survey).read_bytes()).hexdigest(),
        "source_dump": str(d["source"]),
        "rule": ("thumb-region vertices within falloff_mm of a thumb vertex that is inside the frozen handle in curl_handle or "
                 "pullup_bar before closing; displacement = envelope A(v)=max_u (penetration_u+margin)*cos^2 falloff, along each "
                 "vertex's own radial direction away from the handle axis (rest coordinates of the hand)"),
        "parameters": {"margin_mm": a.margin_mm, "falloff_mm": a.falloff_mm},
        "allowed_regions": ["thumb"], "allowed_vertex_ids": [int(i) for i in mask], "vertex_count": len(mask),
        "allowed_vertex_ids_sha256": hashlib.sha256(np.asarray(mask, dtype="<i8").tobytes()).hexdigest(),
        "planned": {"per_side": report, "min_clearance_after_mm_of_formerly_inside_vertices": worst * 1000.0,
                    "mirror_asymmetry_m": asym},
        "weights_changed": False, "topology_changed": False, "rig_changed": False,
        "frozen_untouched": ["handle frame (place_handle)", "frozen grip poses", "canonical v4 rig/rest", "acceptance thresholds"],
        "inputs": "this candidate's own ORIGINAL v1 mesh and the project's own handle frame only",
    }
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("THUMB MASK DECLARED", a.out, "vertices", len(mask), "sha", rec["allowed_vertex_ids_sha256"][:16],
          "| planned max displacement %.2f mm" % max(v["max_displacement_mm"] for v in report.values()),
          "| min clearance after %.2f mm" % (worst * 1000))


if __name__ == "__main__":
    main()
