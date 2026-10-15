#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R17 (Claude, 15 Oct 2026): R15 + a lockout deltoid corrective (HGPT_S7_DELT_ keys).

Owner on R15's lockout: "I'm not sure the deforming is in the right place here", circling the back of the shoulder.  The
deltoid skin stops at about arm-out-sideways and bunches behind and below the joint, because the shoulder-cap helper (two thirds of
that skin) follows half of the arm-vs-scapula rotation.  R16 (rejected) made the helper follow up to 80 % near lockout.  That
lifted the deltoid, but it crushed the skin at the inner top of the shoulder: 88 collapsed faces and 199 self-intersecting pairs at
172 deg.  Any end fraction above 0.5 adds collapse there, and handing the inner cap weight back to the girdle did not help.

Option 1 (owner: "Yes continue with option 1 first"): keep R15's rig, and add a pose-space corrective whose target is the
higher-follow surface ONLY where it does not crush:
  target(ht) = P + smooth(m * (P_hi - P))
  * P is R15 posed at ht (all keys);
  * P_hi is the same with the cap following F_HI near lockout;
  * m is 1, except 0 on faces of P_hi whose area falls below COLLAPSE_RATIO of rest or that pass through other faces, plus
    MASK_RINGS rings, diffused; the masked displacement is then smoothed over the mesh (FIELD_PASSES Laplacian passes,
    crushing vertices held at 0): a hard blend of the two surfaces tore at the arm root.
The offsets are baked into rest space with the S5 machinery (build_original_bake_corrective_blender.build: target
interpenetration mask, LBS-inverse, smooth press-path guard + the shoulder-press benchmark path) at KEYS_HT, as the
HGPT_S7_DELT_ family (starts at 130 deg, original_v1_review_candidate_drives.S1_FAMILIES).  No new bones, and the cap
helper keeps 0.5.
  python3.13 build_original_review_candidate_r17_blender.py -- --make-targets --blend R15.blend --out targets.npz
  python3.13 build_original_review_candidate_r17_blender.py -- --bake --blend R15.blend --parent R15.blend --targets targets.npz \
      --out R17.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import original_v1_review_candidate_drives as drives  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREFIX = "HGPT_S7_DELT_"
ANGLES_PROP = "hgpt_s7_angles"
KEYS_HT = tuple(float(v) for v in os.environ.get("S7_KEYS", "145,160,172").split(","))
F_HI = float(os.environ.get("S7_F_HI", 0.8))
COLLAPSE_RATIO = float(os.environ.get("S7_COLLAPSE", 0.3))
MASK_RINGS = int(os.environ.get("S7_MASK_RINGS", 4))
MASK_PASSES = int(os.environ.get("S7_MASK_PASSES", 30))
FIELD_PASSES = int(os.environ.get("S7_FIELD_PASSES", 60))      # Laplacian smoothing of the displacement field (no tears)
GAIN = float(os.environ.get("S7_GAIN", 1.0))                  # applied after smoothing (smoothing halves the peak lift)


def get(flag):
    return args[args.index(flag) + 1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _setup(blend):
    import build_functional_shoulder_correction_blender as correction
    import build_original_movement_benchmarks_blender as bench
    import original_v1_press_extension as px
    bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    px.install()
    if px._PATH["name"] != "v4":
        raise RuntimeError("R17 needs the v4 press path (R15)")
    if "hgpt_cap_fraction_ramp" in rig:
        raise RuntimeError("the parent must not carry the rejected R16 cap ramp")
    bench._reset(rig)
    return res


def _areas(V, F):
    out = np.zeros(len(F))
    for k, f in enumerate(F):
        p0 = V[f[0]]
        a = 0.0
        for i in range(1, len(f) - 1):
            a += np.linalg.norm(np.cross(V[f[i]] - p0, V[f[i + 1]] - p0)) / 2
        out[k] = a
    return out


def make_targets():
    import build_original_movement_benchmarks_blender as bench
    import build_original_sculpt_corrective_blender as s4
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    res = _setup(get("--blend"))
    body, rig = res["body"], res["runtime"]
    V0, F = bench._evaluated(body)
    R = np.array([tuple(v) for v in V0])
    A0 = _areas(R, F)
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    out, log = {}, {}
    for ht in KEYS_HT:
        surf = {}
        for tag, ramp in (("P", None), ("HI", [F_HI, 90.0, 172.0])):
            if ramp is None:
                rig.pop("hgpt_cap_fraction_ramp", None)
            else:
                rig["hgpt_cap_fraction_ramp"] = ramp
            bench._reset(rig)
            s4.press_pose(res, ht)
            drives.drive(rig, body)
            V, _ = bench._evaluated(body)
            surf[tag] = np.array([tuple(v) for v in V])
        rig.pop("hgpt_cap_fraction_ramp", None)
        P, H = surf["P"], surf["HI"]
        ratio = _areas(H, F) / np.maximum(A0, 1e-12)
        bad = {v for k in np.where(ratio < COLLAPSE_RATIO)[0] for v in F[k]}
        tree = BVHTree.FromPolygons([Vector(x) for x in H], F, all_triangles=False)
        fs = [set(f) for f in F]
        bad |= {v for a, b in tree.overlap(tree) if a != b and not (fs[a] & fs[b]) for f in (a, b) for v in F[f]}
        m = np.ones(len(P))
        near = set(bad)
        for _ in range(MASK_RINGS):
            near |= {j for i in near for j in adj[i]}
        m[list(near)] = 0.0
        free = [i for i in near if i not in bad]
        for _ in range(MASK_PASSES):
            upd = {i: sum(m[j] for j in adj[i]) / len(adj[i]) for i in free}
            for i, x in upd.items():
                m[i] = x
        D = (H - P) * m[:, None]
        # a masked blend of two skinned surfaces tears where the mask switches (measured: jagged creases at the arm root);
        # smoothing the displacement FIELD over the mesh spreads the lift and cannot tear.  The masked (crushing) vertices
        # are held at 0 while it diffuses.
        act = set(np.where(np.linalg.norm(H - P, axis=1) > 1e-4)[0])
        zone = set(act)
        for _ in range(6):
            zone |= {j for i in zone for j in adj[i]}
        hold = set(bad)
        movable = [i for i in zone if i not in hold]
        for _ in range(FIELD_PASSES):
            upd = {i: (D[i] + sum(D[j] for j in adj[i])) / (1 + len(adj[i])) for i in movable}
            for i, x in upd.items():
                D[i] = x
        D *= GAIN
        out[str(ht)] = P + D
        mv = np.linalg.norm(D, axis=1)
        log[str(ht)] = {"masked_vertices": len(bad), "moved_gt_1mm": int((mv > 1e-3).sum()), "max_mm": round(float(mv.max()) * 1000, 1)}
        print("S7TARGET", ht, log[str(ht)])
    np.savez(get("--out"), **out)
    Path(get("--out") + ".json").write_text(json.dumps({"keys_ht": KEYS_HT, "f_hi": F_HI, "collapse_ratio": COLLAPSE_RATIO,
                                                        "mask_rings": MASK_RINGS, "field_passes": FIELD_PASSES, "gain": GAIN, "log": log}, indent=1) + "\n")


def bake():
    import build_original_bake_corrective_blender as s5
    import build_original_movement_benchmarks_blender as bench
    import build_original_shoulder_relax_corrective_blender as s1
    import original_v1_press_extension as px
    import original_v1_shoulder_r4 as r4
    out, report = Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    z = np.load(get("--targets"))
    targets = {k: z[k] for k in z.files}
    res = _setup(get("--blend"))
    body, rig = res["body"], res["runtime"]
    if any(kb.name.startswith(PREFIX) for kb in body.data.shape_keys.key_blocks):
        raise RuntimeError("the parent already has S7 keys")
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)

    def benchmark_press(t):                     # as R14: the benchmark's own path, without the press-extension hook
        hook = r4._S.get("extend")
        r4._S["extend"] = None
        try:
            bench.pose_press(res, t, __import__("build_functional_shoulder_correction_blender"))
        finally:
            r4._S["extend"] = hook
    log = s5.build(res, targets, prefix=PREFIX, keys_ht=KEYS_HT, angles_prop=ANGLES_PROP,
                   extra_guard_paths=[("benchmark_press", benchmark_press)])

    def path(use):
        rows = []
        for t in tuple(i / 20 for i in range(21)):
            a = px.pose_press_full(res, t)
            drives.drive(rig, body)
            if not use:
                for kb in body.data.shape_keys.key_blocks:
                    if kb.name.startswith(PREFIX):
                        kb.value = 0.0
            V, _ = bench._evaluated(body)
            m = bench.frame_metrics(V0, V, F, dom, floor)
            rows.append({"t": t, "ht": round(a["humerothoracic_elevation"], 2), "collapse": m["collapse_lt_0_1"],
                         "stretch": m["stretch_gt_2"], "pairs": m["self_intersecting_pairs"], "volume_pct": m["body_volume_change_pct"]})
        bench._reset(rig)
        return rows
    before, after = path(False), path(True)
    for a, b in zip(before, after):
        print("R17P", a["t"], a["ht"], (a["collapse"], a["stretch"], a["pairs"], round(a["volume_pct"], 2)), "->",
              (b["collapse"], b["stretch"], b["pairs"], round(b["volume_pct"], 2)))
    output = s1.save(res, out, get("--parent"), "R17")
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R17", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "press_path": "v4", "family": PREFIX, "keys_ht": KEYS_HT, "targets_sha256": sha(get("--targets")),
           "targets_recipe": json.loads(Path(get("--targets") + ".json").read_text()) if Path(get("--targets") + ".json").exists() else None,
           "s7": {"log": log}, "press_path_without_s7": before, "press_path_r17": after, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    if "--make-targets" in args:
        make_targets()
    else:
        bake()
