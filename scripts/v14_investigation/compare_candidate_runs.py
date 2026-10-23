#!/usr/bin/env python3
"""Compare two independent deterministic-candidate builds (W8 -> V14 and W8 -> legs-only base -> R120), each from
a separate GitHub runner.  Plain Python + numpy + scipy.

usage: python3 compare_candidate_runs.py <run A dir> <run B dir> <out.json>
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def arr_cmp(a, b):
    if a.shape != b.shape:
        return {"same_shape": False, "shapes": [list(a.shape), list(b.shape)]}
    return {"same_shape": True, "bit_identical": bool(np.array_equal(a, b)),
            "max_abs_dev": float(np.abs(a.astype(np.float64) - b.astype(np.float64)).max()) if a.size else 0.0}


def mesh_cmp(fa, fb):
    A, B = np.load(fa), np.load(fb)
    R = {"vertices": [len(A["positions"]), len(B["positions"])],
         "faces": [len(A["face_sizes"]), len(B["face_sizes"])]}
    if R["vertices"][0] == R["vertices"][1]:
        R["positions_same_order"] = arr_cmp(A["positions"], B["positions"])
        R["faces_identical"] = bool(np.array_equal(A["face_sizes"], B["face_sizes"]) and np.array_equal(A["face_verts"], B["face_verts"]))
        R["weights"] = arr_cmp(A["weights"], B["weights"])
    d, _ = cKDTree(B["positions"]).query(A["positions"])
    R["nn_dist_mm"] = {"max": float(d.max() * 1000), "count_gt_0.01mm": int((d > 1e-5).sum())}
    return R


def main():
    a, b, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    R = {}
    for f in ("rest.npy", "tris.npy"):
        R[f"W8_{f}"] = arr_cmp(np.load(a / "W8" / f), np.load(b / "W8" / f))
    oa, ob = np.load(a / "W8/body_v2_offsets.npz"), np.load(b / "W8/body_v2_offsets.npz")
    for k in ("offsets", "proportion"):
        R[f"W8_{k}"] = arr_cmp(oa[k], ob[k])
    for name in ("V14", "R120"):
        R[f"{name}_mesh"] = mesh_cmp(a / f"{name}_mesh.npz", b / f"{name}_mesh.npz")
    for rep in ("W8/body_v2_report.json", "V14/legs_v2_report.json", "R120/rebuild_report.json"):
        ra, rb = json.loads((a / rep).read_text()), json.loads((b / rep).read_text())
        R[f"report_identical:{rep}"] = ra == rb
    R["PASS_W8_triangulation_identical"] = R["W8_tris.npy"].get("bit_identical", False) and R["W8_rest.npy"].get("bit_identical", False)
    R["PASS_V14_identical_topology"] = R["V14_mesh"].get("faces_identical", False)
    R["PASS_R120_identical_topology"] = R["R120_mesh"].get("faces_identical", False)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(R, indent=1)); print(json.dumps(R, indent=1))


if __name__ == "__main__":
    main()
