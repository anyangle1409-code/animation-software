#!/usr/bin/env python3
"""Validate the ORIGINAL_v1 consolidated review candidate against the frozen a003 on every movement benchmark (bpy).

Runs scripts/build_original_movement_benchmarks_blender.py twice in one process, each on a freshly opened file:
  * baseline: a003 (67 joints, no correctives); peak frame rendered for comparison;
  * candidate (R1, R2, ...): with scripts/original_v1_review_candidate_drives.py driving the shoulder helpers, K1 (and S1) keys after every
    pose; five frames per benchmark rendered (three-quarter and side) for phone filmstrips.
Both runs use the same motion definitions (incl. H1 arm carriage, H2 thumb, P4 families).  Nothing is approved.

  python3.13 validate_original_review_candidate_blender.py -- --candidate R1.blend --baseline a003.blend --out JSON [--renders DIR] [--name R2]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1] if k in args else None
    cand, base, out, renders = get("--candidate"), get("--baseline"), Path(get("--out")), get("--renders")
    name = (get("--name") or "R1").lower()
    rdir = Path(renders) if renders else None

    bpy.ops.wm.open_mainfile(filepath=str(Path(base).resolve()))
    bench._CAM.clear(); bench._THUMB_CACHE.clear()
    bench.RENDER_FRAMES = (bench.FRAMES - 1,)
    bench.RENDER_VIEWS = (bench.THREE_QUARTER, ("side", (5.0, 0.0, 0.0)))
    baseline = bench.run(rdir / "a003" if rdir else None)

    bpy.ops.wm.open_mainfile(filepath=str(Path(cand).resolve()))
    bench._CAM.clear(); bench._THUMB_CACHE.clear()
    bench.RENDER_FRAMES = (0, 2, 4, 6, 8)
    candidate = bench.run(rdir / name if rdir else None, setup=drives.setup,
                          post_pose=lambda r: drives.drive(r["runtime"], r["body"]))

    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE_VALIDATION", "approved": False, "candidate": Path(cand).name, "name": name,
           "baseline": Path(base).name, "benchmarks": {}}
    for n in candidate["benchmarks"]:
        a, b = baseline["benchmarks"][n], candidate["benchmarks"][n]
        rep["benchmarks"][n] = {"a003_worst": a["worst"], f"{name}_worst": b["worst"],
                                "a003_volume_pct": a["volume_change_pct_range"], f"{name}_volume_pct": b["volume_change_pct_range"],
                                f"{name}_end_classes": b["frames"][-1]["self_intersection_classes_top"][:4],
                                f"{name}_peak_angles": b["frames"][-1]["angles_deg"]}
        print("VAL", n, a["worst"], "->", b["worst"], a["volume_change_pct_range"], "->", b["volume_change_pct_range"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
