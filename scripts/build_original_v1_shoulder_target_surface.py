"""Build the 'skin-sliding' target surface the shoulder corrective is fitted to (numpy only, deterministic, first-party).

python scripts/build_original_v1_shoulder_target_surface.py <arc_dump.npz> <declaration.json> <out.npz>
        [--arm-w 0.85] [--trunk-w 0.97] [--iters 4000] [--biharmonic 1]

Idea (anatomical, generic): in real skin the arm moves a lot, the thorax moves little, and the skin in between slides and stretches smoothly over a wide
band instead of being dragged as a sheet by whichever bone has the larger weight. For every training pose:
  * P_trunk  = the surface skinned by the trunk bones only (root..head, weights renormalised): detail-preserving, no arm influence;
  * P_lbs    = the candidate's own evaluated surface (the dump);
  * vertices OUTSIDE the declared zone, and zone vertices that are already arm-driven (upper-arm/forearm/hand weight >= --arm-w) or trunk-driven
    (trunk weight >= --trunk-w), keep P_lbs;
  * the remaining transition band (free vertices) gets the displacement field u = P - P_trunk that minimises the squared surface Laplacian
    (biharmonic, inverse-edge-length weights) given the fixed vertices: smooth tangent-continuous sliding, minimum-roughness strain distribution.
Output arrays: target [pose, vertex, 3] (float32), free (bool per vertex), plus the inputs' identity. The corrective solver fits shape-key
displacements to this target together with its edge/fold/area/roughness barriers; the target itself is never shipped.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("declaration")
    ap.add_argument("out")
    ap.add_argument("--arm-w", type=float, default=0.85)
    ap.add_argument("--trunk-w", type=float, default=0.97)
    ap.add_argument("--iters", type=int, default=4000)
    ap.add_argument("--free-lo", type=float, default=0.05, help="zone vertices need at least this much arm+scapula+clavicle weight to be free (others keep the skinned position)")
    ap.add_argument("--biharmonic", type=int, default=1)
    a = ap.parse_args()
    d = np.load(a.dump)
    W, rest, E, evald, mats = d["W"], d["rest"], d["edges"], d["evaluated"], d["mats"]
    bones = [str(x) for x in d["bones"]]
    b = {n: i for i, n in enumerate(bones)}
    nV, nP = len(rest), len(evald)
    decl = json.loads(Path(a.declaration).read_text(encoding="utf-8"))
    key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
    mir = np.array([key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(nV)])
    L = np.array(decl["left_owned_vertex_ids"])
    zone = np.zeros(nV, bool)
    zone[L] = True
    zone[mir[L]] = True
    trunk = [b[n] for n in ("root", "pelvis", "spine_01", "spine_02", "spine_03", "neck", "head") if n in b]
    armb = [b[n] for n in bones if n.startswith(("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky"))]
    wa, wt = W[:, armb].sum(axis=1), W[:, trunk].sum(axis=1)
    Wt = np.zeros_like(W)
    Wt[:, trunk] = W[:, trunk]
    Wt = Wt / np.maximum(Wt.sum(axis=1, keepdims=True), 1e-9)
    girdle = [b[n] for n in bones if n.startswith(("scapula", "clavicle"))]
    wg = W[:, girdle].sum(axis=1)
    free = zone & (wa < a.arm_w) & (wt < a.trunk_w) & ((wa + wg) >= a.free_lo)
    print("zone", int(zone.sum()), "free", int(free.sum()), "fixed-arm", int((zone & (wa >= a.arm_w)).sum()), "fixed-trunk", int((zone & (wt >= a.trunk_w)).sum()))
    # inverse-edge-length weighted graph Laplacian (row-normalised): (L x)_v = x_v - sum_j w_vj x_j / sum_j w_vj
    ew = 1.0 / np.maximum(np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1), 1e-6)
    wsum = np.bincount(E[:, 0], ew, nV) + np.bincount(E[:, 1], ew, nV)

    def lap(x):
        s = np.zeros_like(x)
        for c in range(3):
            s[:, c] = np.bincount(E[:, 0], ew * x[E[:, 1], c], nV) + np.bincount(E[:, 1], ew * x[E[:, 0], c], nV)
        return x - s / wsum[:, None]

    def lap_t(y):        # transpose of lap
        y2 = y / wsum[:, None]
        s = np.zeros_like(y)
        for c in range(3):
            s[:, c] = np.bincount(E[:, 0], ew * y2[E[:, 1], c], nV) + np.bincount(E[:, 1], ew * y2[E[:, 0], c], nV)
        return y - s

    fi = np.nonzero(free)[0]
    target = np.empty((nP, nV, 3), np.float32)
    stats = []
    for p in range(nP):
        T = np.einsum("bij,vj->vbi", mats[p][:, :3, :], np.c_[rest, np.ones(nV)])
        Ptr = np.einsum("vb,vbi->vi", Wt, T)
        u = evald[p] - Ptr                           # fixed everywhere; free vertices solved below
        u0 = u.copy()
        # harmonic start then biharmonic polish (CG on the free block of the normal equations)
        xf = u[fi].copy()

        def matvec(xf_, order=1):
            x = np.zeros((nV, 3))
            x[fi] = xf_
            return lap_t(lap(x))[fi]
        # minimise |L u|^2 (squared discrete Laplacian = biharmonic energy) over the free block, fixed vertices as boundary data
        xfix = u.copy()
        xfix[fi] = 0.0
        rhs = -lap_t(lap(xfix))[fi]
        xk = xf.copy()
        r = rhs - matvec(xk, 1)
        pdir = r.copy()
        rs = (r * r).sum()
        rs0 = rs
        for it in range(a.iters):
            Ap = matvec(pdir, 1)
            alpha = rs / max((pdir * Ap).sum(), 1e-30)
            xk += alpha * pdir
            r -= alpha * Ap
            rs_new = (r * r).sum()
            if rs_new < 1e-18 * max(rs0, 1e-30):
                break
            pdir = r + (rs_new / rs) * pdir
            rs = rs_new
        u[fi] = xk
        target[p] = (Ptr + u).astype(np.float32)
        dl = np.linalg.norm(u[fi] - u0[fi], axis=1) if len(fi) else np.zeros(1)
        stats.append((float(dl.mean()), float(dl.max()), it))
    L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
    ez = zone[E[:, 0]] | zone[E[:, 1]]
    worst_t, worst_l, low_t, low_l = 0.0, 0.0, 9.0, 9.0
    for p in range(nP):
        rt = np.linalg.norm(target[p][E[ez, 0]] - target[p][E[ez, 1]], axis=1) / L0[ez]
        rl = np.linalg.norm(evald[p][E[ez, 0]] - evald[p][E[ez, 1]], axis=1) / L0[ez]
        worst_t, worst_l, low_t, low_l = max(worst_t, rt.max()), max(worst_l, rl.max()), min(low_t, rt.min()), min(low_l, rl.min())
    print("zone edge ratio over all poses: target max %.2f min %.2f | LBS max %.2f min %.2f" % (worst_t, low_t, worst_l, low_l))
    print("free-vertex shift vs LBS: mean %.4f max %.4f m; CG iters max %d" % (np.mean([s[0] for s in stats]), max(s[1] for s in stats), max(s[2] for s in stats)))
    np.savez_compressed(a.out, target=target, free=free, zone=zone, poses=d["poses"], source_dump_sha256=hashlib.sha256(Path(a.dump).read_bytes()).hexdigest(),
                        declaration_sha256=hashlib.sha256(Path(a.declaration).read_bytes()).hexdigest(), arm_w=a.arm_w, trunk_w=a.trunk_w)
    print("TARGET SURFACE", a.out)


if __name__ == "__main__":
    main()
