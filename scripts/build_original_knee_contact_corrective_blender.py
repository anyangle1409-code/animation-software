"""K1: experimental knee deep-flexion contact corrective on the unchanged ORIGINAL_v1 male (review-only diagnostic).

M1/M2 found calf/thigh interpenetration at deep knee flexion (squat, lunge, single-leg stance: 42-102 pairs per side).
Unlike the shoulder (W2: blended LBS matrices near-singular, sigma_min 0.0024), the knee is a single-plane hinge whose
blended skinning matrices stay well conditioned (sigma_min = cos(theta/2): 0.71 / 0.57 / 0.42 at 90 / 110 / 130 deg),
so a bounded rest-space corrective is feasible.

Contact model (an engineering assumption, not tissue mechanics): in the pure knee-flexion key pose the posterior
thigh and calf skin are flattened onto the plane through the knee-joint centre that bisects the flexion angle, leaving
2 * GAP_M between them, as compressed soft tissue would.  Per key and side:
  1. wedge zone: skin within ZONE_R_M of the knee centre on the flexion side (posterior), split into thigh / calf side
     by its rest thigh-vs-shin weight;
  2. thigh-side skin below +GAP_M and calf-side skin above -GAP_M are moved along the plane normal onto it;
  3. the displacement is extended harmonically over TAPER_RINGS rings (zero at the outer ring, so no seam);
  4. the volume removed is restored by a normal offset of the same tapered band (one linearised step, capped);
  5. the posed displacement is mapped to rest space through each vertex's blended LBS matrix (no damping needed;
     condition is logged) and capped at DELTA_CAP_M.
Keys HGPT_K1_KNEE_<side>_<deg> are added in memory only (never saved).  They are driven per side by the measured knee
flexion with piecewise-linear hats (0 at <= ACTIVATION_START, clamped above the last key).
Measured before/after: a pure knee sweep and the M1/M2 squat, lunge and single-leg benchmarks.  Nothing is approved.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_movement_benchmarks_blender as bench

KEYS_DEG = (90, 110, 130)
ACTIVATION_START = 60.0
GAP_M = 0.002
ZONE_R_M = 0.30
TAPER_RINGS = 4
DELTA_CAP_M = 0.040            # knee LBS is well conditioned; 130 deg needs 37.6 mm (30 mm clipped 40 vertices)
INFLATE_CAP_M = 0.010
KEY_PREFIX = "HGPT_K1_KNEE_"
SIDES = ("l", "r")


def knee_flexion_deg(rig, s):
    thigh, shin = rig.pose.bones[f"thigh_{s}"], rig.pose.bones[f"shin_{s}"]
    rest_rel = rig.data.bones[f"thigh_{s}"].matrix_local.inverted() @ rig.data.bones[f"shin_{s}"].matrix_local
    rel = thigh.matrix.inverted() @ shin.matrix
    return math.degrees((rest_rel.inverted() @ rel).to_euler("XYZ").x)


def activations(angle):
    """Piecewise-linear hats over (ACTIVATION_START, *KEYS_DEG); clamped to the last key above it."""
    knots = (ACTIVATION_START,) + KEYS_DEG
    out = {k: 0.0 for k in KEYS_DEG}
    a = min(angle, KEYS_DEG[-1])
    for i, k in enumerate(KEYS_DEG):
        lo, hi = knots[i], (knots[i + 2] if i + 2 < len(knots) else None)
        if lo < a <= k:
            out[k] = (a - lo) / (k - lo)
        elif hi is not None and k < a < hi:
            out[k] = (hi - a) / (hi - k)
    return out


def _volume(V, F):
    return sum(V[f[0]].dot(V[f[1]].cross(V[f[2]])) for f in F) / 6.0


def _rings(adj, seeds, n):
    dist = {i: 0 for i in seeds}
    frontier = list(seeds)
    for r in range(1, n + 1):
        nxt = []
        for i in frontier:
            for j in adj[i]:
                if j not in dist:
                    dist[j] = r
                    nxt.append(j)
        frontier = nxt
    return dist


def _pose_pure_knee(rig, angle):
    bench._reset(rig)
    for s in SIDES:
        bench._rot(rig.pose.bones[f"shin_{s}"], x=angle)
    bpy.context.view_layer.update()


def build(result):
    """Solve and add the K1 keys (values 0) to the benchmark scene; returns the solve log."""
    body, rig = result["body"], result["runtime"]
    names = {g.index: g.name for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    W = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    if not body.matrix_world.is_identity or not rig.matrix_world.is_identity:
        raise RuntimeError("identity object transforms required (world = armature space)")
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    log = {}
    for key in KEYS_DEG:
        _pose_pure_knee(rig, key)
        V, F = bench._evaluated(body)
        vol_before = _volume(V, F)
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        disp = {}
        contact = set()
        entry = {}
        for s in SIDES:
            pb = rig.pose.bones
            c = pb[f"shin_{s}"].head
            ut = (pb[f"thigh_{s}"].head - c).normalized()
            us = (pb[f"foot_{s}"].head - c).normalized()
            n = (ut - us).normalized()                       # bisector-plane normal, towards the thigh
            b = (ut + us).normalized()                       # into the flexion wedge (posterior)
            side_sign = 1.0 if c.x > 0 else -1.0
            fixed = {}
            for i, p in enumerate(V):
                w = W[i]
                wt, ws = w.get(f"thigh_{s}", 0.0), w.get(f"shin_{s}", 0.0)
                if wt + ws < 0.5 or p.x * side_sign <= 0:
                    continue
                r = p - c
                if r.length > ZONE_R_M or r.dot(b) <= 0:
                    continue
                d = r.dot(n)
                if wt >= ws and d < GAP_M:
                    fixed[i] = n * (GAP_M - d)
                elif ws > wt and d > -GAP_M:
                    fixed[i] = n * (-GAP_M - d)
            ring = _rings(adj, fixed, TAPER_RINGS)
            free = [i for i, r in ring.items() if 0 < r < TAPER_RINGS]
            field = {i: fixed.get(i, Vector()) for i in ring}
            for _ in range(60):                              # harmonic extension: fixed seeds, zero at the outer ring
                for i in free:
                    nb = [field[j] for j in adj[i] if j in field]
                    field[i] = sum(nb, Vector()) / len(nb)
            disp.update({i: v for i, v in field.items() if v.length > 0})
            contact.update(fixed)
            entry[s] = {"contact_vertices": len(fixed), "taper_vertices": len(free),
                        "max_posed_push_mm": round(max((v.length for v in fixed.values()), default=0) * 1000, 2)}
        # volume restoration over the tapered band (free ring vertices, both sides)
        V1 = [V[i] + disp.get(i, Vector()) for i in range(len(V))]
        lost = vol_before - _volume(V1, F)
        band = [i for i in disp if i not in contact]       # taper ring only: contact skin stays on the plane
        normals = [Vector() for _ in V1]
        for f in F:
            a, b2, c2 = (V1[k] for k in f)
            nrm = (b2 - a).cross(c2 - a)                     # area-weighted
            for k in f:
                normals[k] += nrm / 2.0
        gain = sum(normals[i].length for i in band) / 3.0   # d(volume)/d(alpha) for a unit normal offset of the band
        alpha = max(-INFLATE_CAP_M, min(INFLATE_CAP_M, lost / gain)) if gain > 0 else 0.0
        for i in band:
            nn = normals[i].normalized() if normals[i].length > 0 else Vector()
            disp[i] = disp[i] + nn * alpha
        # map to rest space
        keyed = {}
        sig_min, clipped = 1.0, 0
        for i, dv in disp.items():
            A = sum(x * mats[nm] for nm, x in W[i].items())
            sv = np.linalg.svd(A, compute_uv=False)
            sig_min = min(sig_min, float(sv.min()))
            dr = np.linalg.solve(A, np.array(dv))
            L = float(np.linalg.norm(dr))
            if L > DELTA_CAP_M:
                dr *= DELTA_CAP_M / L
                clipped += 1
            keyed[i] = Vector(dr)
        for s in SIDES:                                      # one key per side; a vertex belongs to its knee's x side
            kb = body.shape_key_add(name=f"{KEY_PREFIX}{s}_{key}", from_mix=False)
            kb.value = 0.0
            side_sign = 1.0 if rig.data.bones[f"shin_{s}"].head_local.x > 0 else -1.0
            for i, dv in keyed.items():
                if body.data.vertices[i].co.x * side_sign > 0:
                    kb.data[i].co = body.data.vertices[i].co + dv
        V2 = [V[i] + disp.get(i, Vector()) for i in range(len(V))]
        log[str(key)] = {"sides": entry, "volume_lost_by_flattening_pct": round(lost / vol_before * 100, 4),
                         "band_normal_offset_mm": round(alpha * 1000, 3),
                         "volume_after_restoration_pct": round((_volume(V2, F) - vol_before) / vol_before * 100, 4),
                         "blended_lbs_sigma_min": round(sig_min, 4), "rest_deltas_clipped": clipped,
                         "max_rest_delta_mm": round(max((v.length for v in keyed.values()), default=0) * 1000, 2)}
    bench._reset(rig)
    result["k1_log"] = log
    return log


def drive(result):
    """Set every K1 key from the current measured knee flexion (per side)."""
    body, rig = result["body"], result["runtime"]
    keys = body.data.shape_keys.key_blocks
    for s in SIDES:
        act = activations(knee_flexion_deg(rig, s))
        for k, v in act.items():
            keys[f"{KEY_PREFIX}{s}_{k}"].value = v
    bpy.context.view_layer.update()


def render_knee(result, out, angles=(90, 110)):
    """Close-ups of the right (+X, F-SIDE-001) knee in pure flexion, without and with the K1 keys."""
    body, rig = result["body"], result["runtime"]
    scene = bpy.context.scene
    for o in scene.objects:
        if o.type in ("MESH", "CURVE") and o is not body:
            o.hide_render = True
    body.data.materials.clear()
    mat = bpy.data.materials.new("HGPT_K1_SKIN_TMP"); mat.diffuse_color = (0.64, 0.44, 0.36, 1.0)
    body.data.materials.append(mat)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light, scene.display.shading.color_type = "STUDIO", "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 700, 700
    scene.render.image_settings.file_format = "PNG"
    cd = bpy.data.cameras.new("HGPT_K1_CAM_TMP"); cd.type = "ORTHO"; cd.ortho_scale = 0.55
    cam = bpy.data.objects.new("HGPT_K1_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for a in angles:
        for keyed in (False, True):
            _pose_pure_knee(rig, a)
            for kb in body.data.shape_keys.key_blocks[1:]:
                kb.value = 0.0
            if keyed:
                drive(result)
            knee = rig.pose.bones["shin_r"].head.copy()
            for view, off in (("lateral", Vector((3.0, 0.0, 0.0))), ("posterolateral", Vector((2.1, 2.1, 0.0)))):
                cam.location = knee + off
                cam.rotation_euler = (knee - cam.location).to_track_quat("-Z", "Y").to_euler()
                name = f"knee_{a}__{'k1' if keyed else 'base'}__{view}.png"
                scene.render.filepath = str(out / name)
                bpy.ops.render.render(write_still=True)
                written.append(name)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bench._reset(rig)
    return written


def knee_sweep(result, with_keys, angles=range(0, 131, 10)):
    body, rig = result["body"], result["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)
    rows = {}
    for a in angles:
        _pose_pure_knee(rig, a)
        if with_keys:
            drive(result)
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, floor)
        rows[a] = {k: m[k] for k in ("collapse_lt_0_1", "stretch_gt_2", "self_intersecting_pairs", "body_volume_change_pct",
                                    "area_ratio_min", "self_intersection_classes_top")}
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
    bench._reset(rig)
    return rows


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only = ["squat", "lunge", "single_leg_stance"]
    baseline = bench.run(None, only=only)
    holder = {}

    def setup(result):
        holder["result"] = result
        build(result)
        holder["before"] = knee_sweep(result, False)
        holder["after"] = knee_sweep(result, True)
        if "--renders" in args:
            holder["renders"] = render_knee(result, Path(args[args.index("--renders") + 1]))

    corrected = bench.run(None, setup=setup, post_pose=drive, only=only)
    rep = {"kind": "K1_KNEE_CONTACT_CORRECTIVE", "approved": False, "scope": "experimental, in-memory keys; review-only",
           "parameters": {"keys_deg": KEYS_DEG, "activation_start_deg": ACTIVATION_START, "gap_mm": GAP_M * 1000,
                          "zone_radius_m": ZONE_R_M, "taper_rings": TAPER_RINGS, "delta_cap_mm": DELTA_CAP_M * 1000},
           "solve_log": holder["result"]["k1_log"],
           "knee_sweep": {"before": holder["before"], "after": holder["after"]},
           "benchmarks": {n: {"before": baseline["benchmarks"][n]["worst"], "after": corrected["benchmarks"][n]["worst"],
                              "volume_before": baseline["benchmarks"][n]["volume_change_pct_range"],
                              "volume_after": corrected["benchmarks"][n]["volume_change_pct_range"],
                              "frames_after": corrected["benchmarks"][n]["frames"]} for n in only},
           "renders": holder.get("renders", [])}
    print("K1", json.dumps(rep["solve_log"]))
    for n, b in rep["benchmarks"].items():
        print("K1", n, b["before"], "->", b["after"], b["volume_before"], "->", b["volume_after"])
    for a in rep["knee_sweep"]["before"]:
        x, y = rep["knee_sweep"]["before"][a], rep["knee_sweep"]["after"][a]
        print("K1 sweep", a, x["self_intersecting_pairs"], "->", y["self_intersecting_pairs"], "collapse", x["collapse_lt_0_1"], "->",
              y["collapse_lt_0_1"], "stretch", x["stretch_gt_2"], "->", y["stretch_gt_2"], "vol", x["body_volume_change_pct"], "->", y["body_volume_change_pct"])
    if "--out" in args:
        out = Path(args[args.index("--out") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=1, default=str) + "\n")
