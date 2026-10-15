#!/usr/bin/env python3
"""ORIGINAL_v1 shoulder / armpit mesh rebuild, stage 1: edges re-routed along the folds (review only; bpy).
Claude, 15 Oct 2026.

The owner circled the back of the shoulder at the top of the press ("This highlighted areas shouldn't be crinkled"), then
answered "Yes please" to rebuilding the shoulder/armpit mesh.

Measured on R15 at lockout, right shoulder, 20 cm around the shoulder joint:
  * 285 edges fold sharply (posed dihedral > 30 deg and > 15 deg more than at rest);
  * the folds lie on the boundary between the squashed deltoid / arm root and the stretched side of the chest;
  * on this all-triangle mesh the crease crosses triangle diagonals, so it shows as a zig-zag crinkle instead of a line.

This stage keeps every vertex (position, every weight, every shape key) and the vertex count.  Only the triangulation
changes: a greedy edge-flip optimisation.  An interior edge (a, b) with opposite vertices c, d is replaced by (c, d) when
that lowers the weighted sum of squared dihedral angles over the quad's five edges.  The sum covers:
  * the rest pose (weight 2);
  * the press at 121 / 145 / 160 / 172 deg (0.5 / 1 / 1 / 1);
  * the bent-over-row end and the push-up bottom (0.5 each).
Guards:
  * rest minimum angle >= MIN_ANG;
  * rest dihedral of the new diagonal <= REST_DIH;
  * no posed triangle flips orientation.
The right side is optimised and every flip is mirrored on the left (exact mirror vertex map), so the mesh stays symmetric.

  python3.13 build_original_shoulder_fold_flip_blender.py -- --blend R15.blend --out R18.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))
import original_v1_review_candidate_drives as drives  # noqa: E402

_E = os.environ
POSES = {k: float(w) for k, w in (x.split(":") for x in _E.get(
    "FLIP_POSES", "rest:2,p121:0.5,p145:1,p160:1,p172:1,row10:0.5,pushup10:0.5").split(","))}
REG_R = float(_E.get("FLIP_REGION_R", 0.20))
MIN_ANG = float(_E.get("FLIP_MIN_ANG", 12.0))
REST_DIH = float(_E.get("FLIP_REST_DIH", 20.0))
ITERS = int(_E.get("FLIP_ITERS", 8))
BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def get(flag):
    return args[args.index(flag) + 1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sample_positions(res):
    """Rest + posed (all drives and keys) vertex positions at the poses in POSES."""
    import build_functional_original_coupled_motion_blender as coupled
    import build_original_movement_benchmarks_blender as bench
    import build_original_sculpt_corrective_blender as s4
    body, rig = res["body"], res["runtime"]
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    X = {"rest": np.array([tuple(v) for v in V0])}
    rest_heads = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in ("l", "r")}
    posers = {"row": lambda t: bench.pose_row(rig, t, rest_heads, coupled.clavicle_basis),
              "pushup": lambda t: bench.pose_pushup(rig, body, t)}
    for k in POSES:
        if k == "rest":
            continue
        bench._reset(rig)
        if k[0] == "p" and k[1:].isdigit():
            s4.press_pose(res, float(k[1:]))
        else:
            name = k.rstrip("0123456789")
            posers[name](int(k[len(name):]) / 10)
        drives.drive(rig, body)
        V, _ = bench._evaluated(body)
        X[k] = np.array([tuple(v) for v in V])
    bench._reset(rig)
    return X, [tuple(f) for f in F]


def optimise(X, F, gh):
    R = X["rest"]
    nv = len(R)
    kd = KDTree(nv)
    for i, p in enumerate(R):
        kd.insert(tuple(p), i)
    kd.balance()
    mir = np.full(nv, -1)
    for i, p in enumerate(R):
        _, j, dist = kd.find((-p[0], p[1], p[2]))
        if dist < 5e-4:
            mir[i] = j
    region = (np.linalg.norm(R - gh, axis=1) < REG_R) & (R[:, 0] > 0.004)
    faces = dict(enumerate(F))
    e2f = {}
    for i, f in faces.items():
        for k in range(3):
            e2f.setdefault(frozenset((f[k], f[(k + 1) % 3])), set()).add(i)

    def normal(Xp, f):
        n = np.cross(Xp[f[1]] - Xp[f[0]], Xp[f[2]] - Xp[f[0]])
        ln = np.linalg.norm(n)
        return n / ln if ln > 1e-15 else n

    def dih(Xp, f1, f2):
        return math.acos(max(-1.0, min(1.0, float(np.dot(normal(Xp, f1), normal(Xp, f2))))))

    def min_angle(f):
        out = []
        for k in range(3):
            p, q, r = R[f[k]], R[f[(k + 1) % 3]], R[f[(k + 2) % 3]]
            u, v = q - p, r - p
            nu, nw = np.linalg.norm(u), np.linalg.norm(v)
            if nu < 1e-12 or nw < 1e-12:
                return 0.0
            out.append(math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(u, v) / (nu * nw)))))))
        return min(out)

    def energy(pair, border):
        E = 0.0
        for k, w in POSES.items():
            E += w * dih(X[k], pair[0], pair[1]) ** 2
            for of, inner in border:
                E += w * dih(X[k], inner, of) ** 2
        return E

    def try_flip(a, b):
        fs = e2f.get(frozenset((a, b)))
        if not fs or len(fs) != 2:
            return None
        i1, i2 = sorted(fs)
        f1, f2 = faces[i1], faces[i2]

        def has(f, u, v):
            return any(f[k] == u and f[(k + 1) % 3] == v for k in range(3))
        if not has(f1, a, b):
            f1, f2, i1, i2 = f2, f1, i2, i1
        if not (has(f1, a, b) and has(f2, b, a)):
            return None
        c = [v for v in f1 if v not in (a, b)][0]
        d = [v for v in f2 if v not in (a, b)][0]
        if c == d or frozenset((c, d)) in e2f:
            return None
        n1, n2 = (a, d, c), (d, b, c)

        def border(tris):
            out = []
            for t in tris:
                for k in range(3):
                    e = frozenset((t[k], t[(k + 1) % 3]))
                    if e in (frozenset((a, b)), frozenset((c, d))):
                        continue
                    others = [j for j in e2f[e] if j not in (i1, i2)]
                    if others:
                        out.append((faces[others[0]], t))
            return out
        if min(min_angle(n1), min_angle(n2)) < MIN_ANG or math.degrees(dih(R, n1, n2)) > REST_DIH:
            return None
        for k in POSES:
            ref = normal(X[k], f1) + normal(X[k], f2)
            if any(np.dot(normal(X[k], t), ref) < 0 for t in (n1, n2)):
                return None
        return (energy((f1, f2), border((f1, f2))) - energy((n1, n2), border((n1, n2))), i1, i2, n1, n2)

    def apply(r):
        _, i1, i2, n1, n2 = r
        for i in (i1, i2):
            f = faces[i]
            for k in range(3):
                e = frozenset((f[k], f[(k + 1) % 3]))
                e2f[e].discard(i)
                if not e2f[e]:
                    del e2f[e]
        faces[i1], faces[i2] = n1, n2
        for i in (i1, i2):
            f = faces[i]
            for k in range(3):
                e2f.setdefault(frozenset((f[k], f[(k + 1) % 3])), set()).add(i)
    log = []
    for _ in range(ITERS):
        gains = []
        for e in list(e2f):
            a, b = tuple(e)
            if region[a] and region[b]:
                r = try_flip(a, b)
                if r and r[0] > 1e-4:
                    gains.append((r[0], a, b))
        gains.sort(reverse=True)
        n = 0
        for _, a, b in gains:
            r = try_flip(a, b)
            if not (r and r[0] > 1e-4) or mir[a] < 0 or mir[b] < 0:
                continue
            rm = try_flip(mir[a], mir[b])
            if rm is None:
                continue
            apply(r)
            apply(rm)
            n += 1
        log.append(n)
        print("FLIP iteration", len(log), "flips per side", n, flush=True)
        if n == 0:
            break
    return [faces[i] for i in range(len(F))], log, float((mir[region] >= 0).mean())


def fold_metrics(X, F, gh):
    R = X["rest"]
    Fa = np.array(F)
    region = (np.linalg.norm(R - gh, axis=1) < REG_R) & (R[:, 0] > 0)

    def nrm(Y):
        N = np.cross(Y[Fa[:, 1]] - Y[Fa[:, 0]], Y[Fa[:, 2]] - Y[Fa[:, 0]])
        return N / np.maximum(np.linalg.norm(N, axis=1)[:, None], 1e-15)
    N0 = nrm(R)
    e2f = {}
    for i, f in enumerate(F):
        for k in range(3):
            e2f.setdefault(tuple(sorted((f[k], f[(k + 1) % 3]))), []).append(i)
    pairs = [fs for e, fs in e2f.items() if len(fs) == 2 and region[e[0]] and region[e[1]]]
    p = np.array(pairs)
    a0 = np.degrees(np.arccos(np.clip((N0[p[:, 0]] * N0[p[:, 1]]).sum(1), -1, 1)))
    out = {}
    for k, Y in X.items():
        N = nrm(Y)
        a = np.degrees(np.arccos(np.clip((N[p[:, 0]] * N[p[:, 1]]).sum(1), -1, 1)))
        out[k] = {"sharp_folds": int(((a > 30) & (a - a0 > 15)).sum()), "bending": round(float((np.radians(a) ** 2).sum()), 1)}
    return out


def main():
    import build_functional_shoulder_correction_blender as correction
    import build_original_shoulder_relax_corrective_blender as s1
    import original_v1_press_extension as px
    blend, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    drives.setup(res)
    px.install()
    gh = np.array(tuple(rig.data.bones["upperarm_r"].head_local))
    X, F = sample_positions(res)
    if any(len(f) != 3 for f in F):
        raise RuntimeError("the shoulder fold flip expects an all-triangle body")
    newF, log, mirror_cov = optimise(X, F, gh)
    before, after = fold_metrics(X, F, gh), fold_metrics(X, newF, gh)
    for k in X:
        print("FOLDS", k, before[k], "->", after[k])
    me = body.data
    keys0 = {kb.name: np.array([tuple(d.co) for d in kb.data]) for kb in me.shape_keys.key_blocks}
    groups0 = [sorted((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices]
    old = {frozenset(f) for f in F}
    new = {frozenset(f) for f in newF}
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    drop = [f for f in bm.faces if frozenset(v.index for v in f.verts) not in new]
    sharp = drop[0].smooth if drop else True
    mat = drop[0].material_index if drop else 0
    bmesh.ops.delete(bm, geom=drop, context="FACES_ONLY")
    for f in newF:
        if frozenset(f) not in old:
            nf = bm.faces.new([bm.verts[i] for i in f])
            nf.smooth = sharp
            nf.material_index = mat
    bm.to_mesh(me)
    bm.free()
    me.update()
    # every per-vertex layer must be untouched
    if len(me.vertices) != len(X["rest"]):
        raise RuntimeError("vertex count changed")
    for kb in me.shape_keys.key_blocks:
        if not np.array_equal(np.array([tuple(d.co) for d in kb.data]), keys0[kb.name]):
            raise RuntimeError(f"shape key {kb.name} changed")
    if [sorted((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices] != groups0:
        raise RuntimeError("vertex weights changed")
    if {frozenset(p.vertices) for p in me.polygons} != new:
        raise RuntimeError("face set mismatch after the rebuild")
    bpy.context.scene["hgpt_shoulder_fold_flip"] = True
    output = s1.save(res, out, blend, "R18")
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R18", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED",
           "approved": False, "stage": "shoulder/armpit mesh rebuild 1: edges re-routed along the folds",
           "params": {"poses": POSES, "region_r": REG_R, "min_angle_deg": MIN_ANG, "rest_dihedral_deg": REST_DIH},
           "mirror_coverage": mirror_cov, "flips_per_side_by_iteration": log, "flips_per_side": sum(log),
           "vertices": len(me.vertices), "faces": len(me.polygons), "folds_before": before, "folds_after": after,
           "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
