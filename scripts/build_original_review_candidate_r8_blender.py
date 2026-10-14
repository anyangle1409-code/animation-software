#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R8 (Claude, 14 Oct 2026): shoulder-cap helper joint (owner: "Yes, build R8 with the helper
joint").  docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R8_20261014.md.

Parent: R5 (not R6/R7: their S1 stretch keys and S2 fold keys were solved for skin without the helper).
  1. scripts/original_v1_shoulder_cap_helper.assign_weights_axial: girdle -> shoulder_cap_<s> -> upper arm chain weights
     around the pivot (CAP_* parameters below), stored as vertex groups + rig props; the bones are recreated in memory by
     drives.setup() (the file stays a 67-bone rig);
  2. S1 stretch-zone relax keys re-solved on the helper base (R6 method and parameters).

  python3.13 build_original_review_candidate_r8_blender.py -- --blend R5.blend --out R8.blend --report JSON
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PARAMS = {"CAP_FRACTION": "0.45", "CAP_T": "-0.14,0.20", "CAP_FADE": "0.12,0.18", "CAP_REDUCE": "1",
          "S1_ZONE": "stretch", "S1_SRATIO": "1.2", "S1_SRINGS": "20", "S1_ITERS": "1000", "S1_KEYS": "105,120,145,160"}
os.environ.update(PARAMS)                                # read by the modules at import time

import bpy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_shoulder_relax_corrective_blender as s1  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import original_v1_shoulder_cap_helper as cap  # noqa: E402


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
    before = s1.sweep(res, True)                          # R5
    weights = cap.assign_weights_axial(body, rig)
    cap.install(rig)
    helper_only = s1.sweep(res, True)
    log = s1.build(res)
    after = s1.sweep(res, True)
    for a, b, c in zip(before, helper_only, after):
        print("R8SW", a["ht"], *((r["collapse"], r["stretch"], r["pairs"], round(r["volume_pct"], 2)) for r in (a, b, c)))
    output = s1.save(res, out, parent, "R8")
    max_inf = max(sum(1 for g in v.groups if g.weight > 0) for v in body.data.vertices)
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R8", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "params": PARAMS, "cap_weights": weights, "max_influences": max_inf, "s1": log,
           "sweep_r5": before, "sweep_r5_cap": helper_only, "sweep_r8": after, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
