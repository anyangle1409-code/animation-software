#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R20 (Claude, 15 Oct 2026): R18 + the deltoid hand-over to the upper arm
(original_v1_deltoid_handover).  The lockout lump behind the shoulder is the outer/back deltoid skin left at about
arm-out-sideways.  R18's other layers (shape keys, edge layout, helpers, press path v4) are kept.  Saved weights only; the
in-memory helper bones are removed again by the save (67-bone file).
  python3.13 build_original_review_candidate_r20_blender.py -- --blend R18.blend --out R20.blend --report JSON
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))
import original_v1_review_candidate_drives as drives  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = __import__("os").environ.get("HANDOVER_MODE", "handover")
NAME = "R22" if MODE == "profile" else "R20"


def get(flag):
    return args[args.index(flag) + 1]


def press_rows(res, use_keys):
    import build_original_movement_benchmarks_blender as bench
    import original_v1_press_extension as px
    body, rig = res["body"], res["runtime"]
    bench._reset(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)
    rows = []
    for t in tuple(i / 20 for i in range(21)):
        a = px.pose_press_full(res, t)
        drives.drive(rig, body)
        if not use_keys:
            for kb in body.data.shape_keys.key_blocks[1:]:
                kb.value = 0.0
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, floor)
        rows.append({"t": t, "ht": round(a["humerothoracic_elevation"], 2), "collapse": m["collapse_lt_0_1"],
                     "stretch": m["stretch_gt_2"], "pairs": m["self_intersecting_pairs"], "volume_pct": m["body_volume_change_pct"]})
    bench._reset(rig)
    return rows


def main():
    import build_functional_shoulder_correction_blender as correction
    import build_original_shoulder_relax_corrective_blender as s1
    import original_v1_deltoid_handover as delt
    import original_v1_press_extension as px
    blend, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    if not bpy.context.scene.get("hgpt_shoulder_fold_flip"):
        raise RuntimeError("R20's parent must be R18")
    drives.setup(res)
    px.install()
    before = press_rows(res, True)
    if MODE == "profile":                               # R22: continuous follow profile (original_v1_deltoid_handover.assign_profile)
        moved = delt.assign_profile(body, rig)
    else:
        moved = delt.assign(body, rig)
    after = press_rows(res, True)
    for a, b in zip(before, after):
        print("R20P", a["t"], a["ht"], (a["collapse"], a["stretch"], a["pairs"]), "->", (b["collapse"], b["stretch"], b["pairs"]))
    output = s1.save(res, out, blend, NAME)
    key = "hgpt_deltoid_follow_profile" if MODE == "profile" else "hgpt_deltoid_handover"
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": NAME, "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "mode": MODE, "deltoid": dict(rig[key]), "moved_vertices": moved,
           "press_path_r18": before, "press_path_after": after, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
