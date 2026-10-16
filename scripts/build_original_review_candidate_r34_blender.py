"""R34 bounded front-patch experiment. No canonical or existing candidate files are written."""
from __future__ import annotations
import heapq
import hashlib
import json
import sys
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
os.environ["S7_LOCKOUT_HT"] = "166"
import bpy
import numpy as np
from mathutils import Vector
import build_original_review_candidate_r17_blender as r17
import build_original_bake_corrective_blender as bake
import build_original_sculpt_corrective_blender as sculpt
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
import original_v1_shoulder_r4 as r4
BASE = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r33_20261016"
PARENT = BASE / "HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R33_CLAUDE.blend"
OUT = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r34_20261016"
PREFIX = "HGPT_S7_DELT_"
KEYS = (120.0, 145.0, 156.0, 166.0)
REF = Path("/tmp/r34-raw-reference.npz")
def coords(kb):
    a = np.empty(len(kb.data) * 3)
    kb.data.foreach_get("co", a)
    return a.reshape(-1, 3)
def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mask_for(body):
    rest = np.array([tuple(v.co) for v in body.data.vertices])
    target = rest[18633] * np.array([-1, 1, 1])
    mirror = int(np.argmin(np.linalg.norm(rest - target, axis=1)))
    assert np.linalg.norm(rest[mirror] - target) < 1e-5
    adj = [[] for _ in rest]
    for e in body.data.edges:
        i, j = e.vertices
        w = float(np.linalg.norm(rest[i] - rest[j]))
        adj[i].append((j, w))
        adj[j].append((i, w))
    distance = np.full(len(rest), np.inf)
    q = [(0.0, 18633), (0.0, mirror)]
    distance[[18633, mirror]] = 0
    while q:
        d, i = heapq.heappop(q)
        if d > distance[i] or d > 0.05:
            continue
        for j, length in adj[i]:
            nd = d + length
            if nd < distance[j] and nd < 0.05:
                distance[j] = nd
                heapq.heappush(q, (nd, j))
    u = np.clip((distance - 0.02) / 0.03, 0, 1)
    weight = 1 - u * u * (3 - 2 * u)
    return weight, [[j for j, _ in row] for row in adj], mirror
def raw_reference():
    res = r17._setup(BASE / "stages/B5_base.blend")
    body, rig = res["body"], res["runtime"]
    rig["hgpt_s7_angles_start"] = 95.0
    with np.load(BASE / "stages/r33_targets.npz") as z:
        targets = {str(ht): z[str(ht)] for ht in KEYS}
    # Derive an inverse-bake reference only, without saving a model.
    # The actual candidate below retains and reruns both original guards.
    old_smooth, old_final = bake.smooth_guard, sculpt._guard
    bake.smooth_guard = lambda *a, **k: {"reference_only": True}
    sculpt._guard = lambda *a, **k: {"reference_only": True}
    try:
        bake.build(res, targets, prefix=PREFIX, keys_ht=KEYS, angles_prop="hgpt_s7_angles")
    finally:
        bake.smooth_guard, sculpt._guard = old_smooth, old_final
    data = {kb.name: coords(kb) for kb in body.data.shape_keys.key_blocks if kb.name.startswith(PREFIX)}
    weight, adj, mirror = mask_for(body)
    sculpt.press_pose(res, 130.0)
    drives.drive(rig, body)
    vv, _ = bench._evaluated(body)
    p = np.array([tuple(v) for v in vv])
    shaped = p.copy()
    active = np.where(weight > 0)[0]
    # Small volume-preserving fairing, bounded by the same geodesic patch.
    for _ in range(30):
        for lam in (0.5, -0.53):
            delta = np.array([shaped[adj[i]].mean(0) - shaped[i] for i in active])
            shaped[active] += lam * delta * weight[active, None]
    offset = shaped - p
    names = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform}
    mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
    dr = np.zeros_like(p)
    for i in active:
        a = sum(g.weight * mats[names[g.group]] for g in body.data.vertices[i].groups
                if names[g.group] in deform and g.weight > 0)
        u, sv, vt = np.linalg.svd(a)
        dr[i] = vt.T @ np.diag(sv / (sv * sv + bake.DAMP ** 2)) @ u.T @ offset[i]
    data["weight"] = weight
    data["local_delta_130"] = dr
    np.savez(REF, **data)
    print("R34_RAW_REFERENCE", json.dumps({"vertices_in_patch": int((weight > 0).sum()),
          "mirror_vertex": mirror, "max_130_smoothing_mm": float(np.linalg.norm(offset, axis=1).max() * 1000)}), flush=True)
def build():
    if OUT.exists():
        raise FileExistsError("Candidate folder already exists; use a new candidate number")
    OUT.mkdir(parents=True)
    res = r17._setup(PARENT)
    body, rig = res["body"], res["runtime"]
    blocks = body.data.shape_keys.key_blocks
    rest = coords(blocks[0])
    with np.load(REF) as ref:
        weight = ref["weight"]
        for side in ("l", "r"):
            for ht in (120, 145):
                kb = blocks[f"{PREFIX}{side}_{ht}"]
                old = coords(kb)
                kb.data.foreach_set("co", (old + weight[:, None] * (ref[kb.name] - old)).reshape(-1))
            a, b = coords(blocks[f"{PREFIX}{side}_120"]), coords(blocks[f"{PREFIX}{side}_145"])
            new = rest + 0.6 * (a - rest) + 0.4 * (b - rest)
            local = ref["local_delta_130"].copy()
            sign = 1 if side == "r" else -1
            local[rest[:, 0] * sign <= 0] = 0
            kb = body.shape_key_add(name=f"{PREFIX}{side}_130", from_mix=False)
            kb.data.foreach_set("co", (new + local).reshape(-1))
            rig[f"hgpt_s7_angles_{side}"] = [120.0, 130.0, 145.0, 156.0, 166.0]
    rig["hgpt_s7_angles_start"] = 95.0
    adj = [set() for _ in rest]
    for e in body.data.edges:
        i, j = e.vertices
        adj[i].add(j); adj[j].add(i)
    def benchmark_press(t):
        hook = r4._S.get("extend")
        r4._S["extend"] = None
        try:
            bench.pose_press(res, t, __import__("build_functional_shoulder_correction_blender"))
        finally:
            r4._S["extend"] = hook
    old_prefix, old_s4, old_paths = bake.PREFIX, sculpt.PREFIX, bake._EXTRA["paths"]
    bake.PREFIX = sculpt.PREFIX = PREFIX
    bake._EXTRA["paths"] = [("benchmark_press", benchmark_press)]
    # 41 samples include every original guard sample AND all nine benchmark samples.
    ts = tuple(i / 40 for i in range(41))
    try:
        smooth_log = bake.smooth_guard(res, adj, ts=ts)
        final_log = sculpt._guard(res, adj, rounds=10, ts=ts)
    finally:
        bake.PREFIX, sculpt.PREFIX, bake._EXTRA["paths"] = old_prefix, old_s4, old_paths
    bench._reset(rig)
    for kb in blocks[1:]:
        kb.value = 0
    import build_functional_original_attachment_blender as attachment
    attachment._remove_previous()
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for side in ("l", "r"):
        for name in ("deltoid_helper", "shoulder_cap", "axilla", "hip_crease", "muscle_pec", "muscle_lat", "muscle_trap"):
            helper = f"{name}_{side}"
            if helper in rig.data.edit_bones:
                rig.data.edit_bones.remove(rig.data.edit_bones[helper])
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    assert sum(b.use_deform for b in rig.data.bones) == 67
    scene = bpy.context.scene
    scene["hgpt_review_candidate"] = "ORIGINAL_V1_REVIEW_R34_CODEX"
    scene["hgpt_review_candidate_approved"] = False
    model = OUT / "HGPT_ORIGINAL_V1_REVIEW_R34_CODEX.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(model), copy=True)
    report = {"candidate": "R34", "status": "EXPERIMENT_NOT_ACCEPTED",
              "approved": False, "parent_sha256": digest(PARENT), "sha256": digest(model),
              "change": "restore inverse-bake detail only in a symmetric 2-to-5 cm front geodesic patch at 120/145; add locally faired 130 key",
              "patch_vertices": int((weight > 0).sum()), "smooth_guard": smooth_log,
              "final_guard": final_log, "guard_samples": list(ts)}
    (OUT / "r34_build.json").write_text(json.dumps(report, indent=2) + "\n")
    print("R34_SAVED", json.dumps({"path": str(model), "sha256": report["sha256"]}), flush=True)
mode = sys.argv[-1]
if mode == "raw":
    raw_reference()
elif mode == "build":
    build()
else:
    raise ValueError(mode)
