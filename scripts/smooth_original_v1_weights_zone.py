"""Deterministic weight diffusion inside a DECLARED vertex zone (numpy only; touches no Blend).

python scripts/smooth_original_v1_weights_zone.py <dump.npz> <declaration.json> <out solution.npz> [--iters 6] [--lam 0.5] [--rings 0]

Hypothesis behind it: the shoulder-top self-intersections are clavicle-driven skin crossing upper-arm-driven skin where the clavicle/upper-arm weights
change very steeply between neighbouring vertices. This widens that ramp: for the declared zone vertices (left-owned + exact mirror, optionally dilated
by <rings> rings) it repeats W_v <- (1 - lam) W_v + lam * (inverse-edge-length weighted mean of the neighbour weights), neighbours outside the zone are
fixed boundary data, the result is mirror-symmetrised (L/R columns swapped), reduced to the 4 largest influences and renormalised. The output is a
weight solution in the format scripts/apply_original_v1_o4_weight_solution_blender.py reads (all deform bones as columns).
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("dump")
ap.add_argument("declaration")
ap.add_argument("out")
ap.add_argument("--iters", type=int, default=6)
ap.add_argument("--lam", type=float, default=0.5)
ap.add_argument("--rings", type=int, default=0)
a = ap.parse_args()
d = np.load(a.dump)
W0, rest, E = d["W"].copy(), d["rest"], d["edges"]
bones = [str(b) for b in d["bones"]]
nV = len(rest)
decl = json.loads(Path(a.declaration).read_text(encoding="utf-8"))
key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
mir = np.array([key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(nV)])
zone = np.zeros(nV, bool)
zone[decl["left_owned_vertex_ids"]] = True
zone[decl["mirror_of_strict_left_vertex_ids"]] = True
for _ in range(a.rings):
    nxt = zone.copy()
    nxt[E[zone[E[:, 0]], 1]] = True
    nxt[E[zone[E[:, 1]], 0]] = True
    zone = nxt
swap = []
for n in bones:
    m = n[:-2] + ("_r" if n.endswith("_l") else "_l") if n[-2:] in ("_l", "_r") else n
    swap.append(bones.index(m))
swap = np.array(swap)
ew = 1.0 / np.maximum(np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1), 1e-6)
W = W0.copy()
for _ in range(a.iters):
    acc = np.zeros_like(W)
    den = np.zeros(nV)
    np.add.at(acc, E[:, 0], ew[:, None] * W[E[:, 1]])
    np.add.at(acc, E[:, 1], ew[:, None] * W[E[:, 0]])
    np.add.at(den, E[:, 0], ew)
    np.add.at(den, E[:, 1], ew)
    mean = acc / np.maximum(den, 1e-12)[:, None]
    Wn = W.copy()
    Wn[zone] = (1 - a.lam) * W[zone] + a.lam * mean[zone]
    W = Wn
W[zone] = 0.5 * (W[zone] + W[mir[zone]][:, swap])          # exact left/right symmetry (zone is mirror closed)
idx = np.nonzero(zone)[0]
Wz = W[idx]
for r in range(len(Wz)):                                   # keep the 4 largest influences
    if (Wz[r] > 1e-6).sum() > 4:
        small = np.argsort(Wz[r])[:-4]
        Wz[r, small] = 0.0
    Wz[r] = Wz[r] / Wz[r].sum()
Wz[Wz < 1e-6] = 0.0
Wz = Wz / Wz.sum(axis=1, keepdims=True)
ch = [bones.index("clavicle_l"), bones.index("upperarm_l")]
ce = zone[E[:, 0]] & zone[E[:, 1]] & (rest[E[:, 0], 0] <= 0) & (rest[E[:, 1], 0] <= 0)
Wfull = W0.copy()
Wfull[idx] = Wz
g0 = np.abs(W0[E[ce, 0]][:, ch] - W0[E[ce, 1]][:, ch]).max(axis=1)
g1 = np.abs(Wfull[E[ce, 0]][:, ch] - Wfull[E[ce, 1]][:, ch]).max(axis=1)
rec = {"iters": a.iters, "lam": a.lam, "rings": a.rings, "zone_vertices": int(len(idx)), "max_weight_change": float(np.abs(Wfull[idx] - W0[idx]).max()),
       "clavicle_upperarm_edge_jump_mean_before": float(g0.mean()), "after": float(g1.mean()), "p90_before": float(np.percentile(g0, 90)), "p90_after": float(np.percentile(g1, 90)),
       "max_before": float(g0.max()), "max_after": float(g1.max()), "declaration_sha256": hashlib.sha256(Path(a.declaration).read_bytes()).hexdigest()}
np.savez(a.out, vertices=idx.astype(np.int64), bones=np.array(bones), weights=Wz)
Path(a.out).with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("WEIGHT SMOOTH", json.dumps(rec))
