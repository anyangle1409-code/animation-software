"""Declare the Phase 3E midline-relief edit mask BEFORE any geometry changes (numpy only; touches no Blend).

python scripts/declare_original_v1_midline_relief_mask.py <dump.npz> <out mask.json> [--depth-mm 10] [--half-width-mm 12] [--taper-mm 50] [--core-ratio 3.0]

Core = vertices exactly on the mirror plane (x = 0), 0.74 < z < 1.10, whose largest incident edge stretch in the lunge pose of the
dump exceeds core-ratio. The core ids, rule parameters and the full mask are written and committed before the edit.
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
import original_v1_midline_relief as mr  # noqa: E402


def core_from_dump(d, ratio):
    rest, E, ev = d["rest"], d["edges"], d["evaluated"][[str(x) for x in d["poses"]].index("lunge")]
    r = np.linalg.norm(ev[E[:, 0]] - ev[E[:, 1]], axis=1) / np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
    inc = np.zeros(len(rest))
    np.maximum.at(inc, E[:, 0], r)
    np.maximum.at(inc, E[:, 1], r)
    z = rest[:, 2]
    return [int(i) for i in np.nonzero((np.abs(rest[:, 0]) < 1e-8) & (z > 0.74) & (z < 1.10) & (inc > ratio))[0]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--depth-mm", type=float, default=10.0)
    ap.add_argument("--half-width-mm", type=float, default=12.0)
    ap.add_argument("--taper-mm", type=float, default=50.0)
    ap.add_argument("--core-ratio", type=float, default=3.0)
    a = ap.parse_args()
    d = dict(np.load(a.dump))
    rest, tris, region = d["rest"], d["tris"], d["region"]
    rn = [str(x) for x in d["region_names"]]
    core = core_from_dump(d, a.core_ratio)
    mask, disp, rep = mr.plan(rest, tris, core, a.depth_mm / 1000, a.half_width_mm / 1000, a.taper_mm / 1000)
    key = {tuple(np.round(rest[i], 5)): int(i) for i in range(len(rest))}
    m = set(mask)
    twins = [key.get(tuple(np.round(rest[i] * [-1, 1, 1], 5))) for i in mask]
    if any(t is None or t not in m for t in twins):
        raise SystemExit("mask is not mirror-closed")
    rec = {"declared_utc": datetime.now(timezone.utc).isoformat(), "phase": "3E", "declared_before_edit": True,
           "source_dump": str(d["source"]), "rule": mr.__doc__.split("Rule:")[1].strip(),
           "parameters": {"depth_mm": a.depth_mm, "half_width_mm": a.half_width_mm, "taper_mm": a.taper_mm, "core_ratio": a.core_ratio},
           "core_vertex_ids": core, "allowed_regions": sorted({rn[region[i]] for i in mask}),
           "allowed_vertex_ids": mask, "vertex_count": len(mask),
           "allowed_vertex_ids_sha256": hashlib.sha256(np.asarray(mask, dtype="<i8").tobytes()).hexdigest(),
           "planned": rep, "weights_changed_by_this_step": False, "topology_changed": False, "rig_changed": False,
           "frozen_untouched": ["canonical v4 rig/rest", "R2", "15 stress-pose definitions", "thresholds and tolerances"],
           "inputs": "this candidate's own ORIGINAL v1 mesh only"}
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("RELIEF MASK DECLARED", a.out, "core", len(core), "mask", len(mask), rec["allowed_regions"], "max %.2f mm" % rep["max_displacement_mm"])


if __name__ == "__main__":
    main()
