#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R10 (Claude, 14 Oct 2026): R9 + S4 sculpt corrective keys for the full-range overhead press
(owner, with a reference photo series of the press: "Yes, start with A then do B").  docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R10_20261014.md.

A (movement, runtime): scripts/original_v1_press_extension.py - lockout to 172 deg and a 12 deg shrug.
B (this builder): scripts/build_original_sculpt_corrective_blender.py keys solved on the full-press poses at 85/110/145/172
deg: rounder (contracted) deltoid, armpit hollow, upper-trapezius bunching at lockout, plus unfolding of the lockout armpit
crease; count-based guard along the press path.

  python3.13 build_original_review_candidate_r10_blender.py -- --blend R9.blend --out R10.blend --report JSON
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PARAMS = {"S4_SCALE": "2.0"}
os.environ.update(PARAMS)

import bpy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_movement_benchmarks_blender as bench  # noqa: E402
import build_original_sculpt_corrective_blender as s4  # noqa: E402
import build_original_shoulder_relax_corrective_blender as s1  # noqa: E402
import original_v1_press_extension as px  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402

PATH_T = tuple(i / 20 for i in range(21))


def press_path(res, use_keys, V0, F, dom, floor):
    body, rig = res["body"], res["runtime"]
    rows = []
    for t in PATH_T:
        a = px.pose_press_full(res, t)
        drives.drive(rig, body)
        if not use_keys:
            for kb in body.data.shape_keys.key_blocks:
                if kb.name.startswith(s4.PREFIX):
                    kb.value = 0.0
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, floor)
        rows.append({"t": t, "ht": round(a["humerothoracic_elevation"], 2), "elbow": round(a["elbow_flexion"], 2),
                     "shrug": round(a["shrug"], 2), "collapse": m["collapse_lt_0_1"], "stretch": m["stretch_gt_2"],
                     "pairs": m["self_intersecting_pairs"], "volume_pct": m["body_volume_change_pct"]})
    bench._reset(rig)
    return rows


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    parent, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    import build_functional_shoulder_correction_blender as correction
    bpy.ops.wm.open_mainfile(filepath=str(Path(parent).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    px.install()
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)
    log = s4.build(res)
    before = press_path(res, False, V0, F, dom, floor)
    after = press_path(res, True, V0, F, dom, floor)
    for a, b in zip(before, after):
        print("R10P", a["t"], a["ht"], (a["collapse"], a["stretch"], a["pairs"], round(a["volume_pct"], 2)), "->",
              (b["collapse"], b["stretch"], b["pairs"], round(b["volume_pct"], 2)))
    output = s1.save(res, out, parent, "R10")
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R10", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "params": PARAMS, "s4": {"keys_ht": s4.KEYS_HT, "regions": s4.REGIONS, "depths_m": {str(k): v for k, v in s4.DEPTHS.items()},
                                    "scale": s4._scale, "unfold_iters": s4.UNFOLD_ITERS, "log": log},
           "press_extension": {"lockout_ht": px.LOCKOUT_HT, "shrug_max_deg": px.SHRUG_MAX_DEG, "ext_per_20_deg": px.EXT_PER_20_DEG},
           "press_path_r9": before, "press_path_r10": after, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
