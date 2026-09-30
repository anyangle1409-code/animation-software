"""Mirror-average an O4 candidate's skin weights into an exactly left/right-symmetric solution.

python scripts/symmetrize_original_v1_o4_weights.py <candidate_dump.npz> <solution.npz> [--reference <R2 dump.npz>]

Input is a dump from scripts/dump_original_v1_o4_pose_skinning_blender.py. Each
vertex and its mirror twin (x -> -x, matched to 0.01 mm) receive the average of
their weights with _l/_r bone names swapped; midline vertices are averaged with
themselves (their own _l/_r mirror). Top 4 influences, renormalised. The output
is a solution file for scripts/apply_original_v1_o4_weight_solution_blender.py
containing every vertex whose weights differ from the reference dump (default:
the input itself). Uses only the candidate's own weights; no external data.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--reference")
    a = ap.parse_args()
    d = np.load(a.dump)
    W, rest = d["W"], d["rest"]
    bones = [str(x) for x in d["bones"]]
    sw = [bones.index(n[:-2] + "_r") if n.endswith("_l") else bones.index(n[:-2] + "_l") if n.endswith("_r") else i
          for i, n in enumerate(bones)]
    key = {tuple(np.round(p * [-1, 1, 1], 5)): i for i, p in enumerate(rest)}
    mirror = np.array([key.get(tuple(np.round(p, 5)), -1) for p in rest])
    if (mirror < 0).any():
        raise SystemExit(f"{(mirror < 0).sum()} vertices have no mirror twin")
    S = 0.5 * (W + W[mirror][:, sw])
    order = np.argsort(-S, axis=1)
    keep = np.zeros_like(S, bool)
    keep[np.arange(len(S))[:, None], order[:, :4]] = True
    S = np.where(keep & (S > 1e-6), S, 0.0)
    S /= S.sum(axis=1, keepdims=True)
    ref = np.load(a.reference)["W"] if a.reference else W
    changed = np.nonzero(np.abs(S - ref).sum(axis=1) > 1e-6)[0]
    used = np.nonzero((S[changed] > 0).any(axis=0))[0]
    np.savez_compressed(a.out, vertices=changed, bones=np.array([bones[i] for i in used]), weights=S[changed][:, used])
    asym_before = np.abs(W - W[mirror][:, sw]).sum(axis=1)
    asym_after = np.abs(S - S[mirror][:, sw]).sum(axis=1)
    rec = {"generated_utc": datetime.now(timezone.utc).isoformat(), "method": "mirror average (x -> -x, _l/_r swap), top 4",
           "source_dump": str(d["source"]), "vertices_written": int(len(changed)),
           "asymmetry_L1_before": {"max": float(asym_before.max()), "verts_gt_0.05": int((asym_before > 0.05).sum())},
           "asymmetry_L1_after": {"max": float(asym_after.max()), "verts_gt_0.05": int((asym_after > 0.05).sum())},
           "inputs": "this candidate's own ORIGINAL v1 weights only"}
    Path(a.out).with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("SYMMETRIZED", json.dumps(rec))


if __name__ == "__main__":
    main()
