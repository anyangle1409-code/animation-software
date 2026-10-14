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
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_movement_benchmarks_blender as bench

GAP_M = 0.002
TAPER_RINGS = 4
DELTA_CAP_M = 0.040            # knee LBS is well conditioned; 130 deg needs 37.6 mm (30 mm clipped 40 vertices)
INFLATE_CAP_M = 0.010
SOFT_M = 0.0                   # > 0: softplus contact (continuous push, no band edge); 0: hard projection (K1 default)
ACTIVATION_START = 60.0
SIDES = ("l", "r")
# hinge joints with single-plane flexion: proximal bone, flexing bone, a distal point, skin groups of each side of the
# crease, the local-X sign of flexion on the flexing bone, key poses, zone radius and the benchmarks that exercise them
HINGES = {
    "knee": {"proximal": "thigh_{s}", "flexing": "shin_{s}", "distal": "foot_{s}",
             "proximal_groups": ("thigh_{s}",), "distal_groups": ("shin_{s}",), "flex_sign": 1.0,
             "keys": (90, 110, 130), "zone_r_m": 0.30, "prefix": "HGPT_K1_KNEE_",
             "benchmarks": ("squat", "lunge", "single_leg_stance")},
    "elbow": {"proximal": "upperarm_{s}", "flexing": "forearm_{s}", "distal": "hand_{s}",
              "proximal_groups": ("upperarm_{s}",), "distal_groups": ("forearm_{s}", "forearm_tw0_{s}", "forearm_tw1_{s}"),
              "flex_sign": -1.0, "keys": (90, 120, 140), "zone_r_m": 0.22, "prefix": "HGPT_K1_ELBOW_",
              "benchmarks": ("bent_over_row", "grip")},
    # wrist EXTENSION (dorsal crease): the hand flexes about its local Z with a per-side sign (the rig's digit axes are not
    # mirrored; extension = -palmar sign: local -Z on _r, +Z on _l, checked against _palmar_sign by the tests)
    "wrist": {"proximal": "forearm_{s}", "flexing": "hand_{s}", "distal": "middle_01_{s}",
              "proximal_groups": ("forearm_{s}", "forearm_tw0_{s}", "forearm_tw1_{s}"),
              "distal_groups": ("hand_{s}", "metacarpal_index_{s}", "metacarpal_middle_{s}", "metacarpal_ring_{s}",
                                "metacarpal_pinky_{s}"),
              "axis": "z", "side_sign": {"l": 1.0, "r": -1.0}, "start": 30.0, "soft_m": 0.003, "guard": range(30, 101, 5),
              "keys": (60, 80, 100), "zone_r_m": 0.10, "prefix": "HGPT_K1_WRIST_",
              "benchmarks": ("wrist_circuit", "push_up")},
}


def _sign(h, s):
    return h["side_sign"][s] if "side_sign" in h else h["flex_sign"]
KEYS_DEG = HINGES["knee"]["keys"]          # knee aliases (K1 tests and report)
KEY_PREFIX = HINGES["knee"]["prefix"]
ZONE_R_M = HINGES["knee"]["zone_r_m"]


def hinge_angle_deg(rig, hinge, s):
    h = HINGES[hinge]
    prox, flex = h["proximal"].format(s=s), h["flexing"].format(s=s)
    rest_rel = rig.data.bones[prox].matrix_local.inverted() @ rig.data.bones[flex].matrix_local
    rel = rig.pose.bones[prox].matrix.inverted() @ rig.pose.bones[flex].matrix
    # swing-twist: remove the flexing bone's axial twist (about its own Y: forearm pronation/supination) before reading the
    # hinge component.  An XYZ-Euler read under-reported a pronated 110 deg elbow as 97.5 deg (supinated: 92.8), so the
    # elbow keys under-activated in twisted-forearm poses (push-up, forearm rotation).  Pure hinge poses read exactly as before.
    q = (rest_rel.inverted() @ rel).to_quaternion()
    tw = Quaternion((q.w, 0.0, q.y, 0.0))
    swing = q @ (tw.normalized().inverted() if tw.magnitude > 1e-12 else Quaternion())
    if swing.w < 0:
        swing.negate()
    ang = swing.angle
    if ang < 1e-9:
        return 0.0
    comp = swing.axis["xyz".index(h.get("axis", "x"))]
    return _sign(h, s) * math.degrees(ang * comp)


def knee_flexion_deg(rig, s):
    return hinge_angle_deg(rig, "knee", s)


def activations(angle, keys=None, start=None):
    """Piecewise-linear hats over (start or ACTIVATION_START, *keys); clamped to the last key above it."""
    keys = keys or KEYS_DEG
    knots = (ACTIVATION_START if start is None else start,) + tuple(keys)
    out = {k: 0.0 for k in keys}
    a = min(angle, keys[-1])
    for i, k in enumerate(keys):
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


def _pose_pure(rig, hinge, angle):
    h = HINGES[hinge]
    bench._reset(rig)
    for s in SIDES:
        bench._rot(rig.pose.bones[h["flexing"].format(s=s)], **{h.get("axis", "x"): _sign(h, s) * angle})
    bpy.context.view_layer.update()


def _pose_pure_knee(rig, angle):
    _pose_pure(rig, "knee", angle)


def build(result, hinge="knee"):
    """Solve and add the hinge's K1 keys (values 0) to the benchmark scene; returns the solve log."""
    h = HINGES[hinge]
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
    soft = h.get("soft_m", SOFT_M)
    for key in h["keys"]:
        _pose_pure(rig, hinge, key)
        V, F = bench._evaluated(body)
        vol_before = _volume(V, F)
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        disp = {}
        contact = set()
        entry = {}
        for s in SIDES:
            pb = rig.pose.bones
            c = pb[h["flexing"].format(s=s)].head
            ut = (pb[h["proximal"].format(s=s)].head - c).normalized()
            us = (pb[h["distal"].format(s=s)].head - c).normalized()
            n = (ut - us).normalized()                       # bisector-plane normal, towards the proximal segment
            b = (ut + us).normalized()                       # into the flexion wedge
            side_sign = 1.0 if c.x > 0 else -1.0
            fixed = {}
            for i, p in enumerate(V):
                w = W[i]
                wt = sum(w.get(g.format(s=s), 0.0) for g in h["proximal_groups"])
                ws = sum(w.get(g.format(s=s), 0.0) for g in h["distal_groups"])
                if wt + ws < 0.5 or p.x * side_sign <= 0:
                    continue
                r = p - c
                if r.length > h["zone_r_m"] or r.dot(b) <= 0:
                    continue
                d = r.dot(n)
                if soft > 0:                               # continuous contact: d' = g + s*softplus((d - g)/s) (thigh side)
                    sgn = 1.0 if wt >= ws else -1.0                # calf side mirrored: d' = -g - s*softplus((-g - d)/s)
                    x = (sgn * d - GAP_M) / soft
                    sp = math.log1p(math.exp(x)) if x < 30 else x
                    push = sgn * (GAP_M + soft * sp) - d
                    if abs(push) > 1e-5:
                        fixed[i] = n * push
                elif wt >= ws and d < GAP_M:
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
        for s in SIDES:                                      # one key per side; a vertex belongs to its joint's x side
            kb = body.shape_key_add(name=f"{h['prefix']}{s}_{key}", from_mix=False)
            kb.value = 0.0
            side_sign = 1.0 if rig.data.bones[h["flexing"].format(s=s)].head_local.x > 0 else -1.0
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
    if "guard" in h:
        log["guard"] = _guard(result, hinge, adj)
    result.setdefault("k1_logs", {})[hinge] = log
    if hinge == "knee":
        result["k1_log"] = log
    return log


def _guard(result, hinge, adj, rounds=8, rings=2):
    """Fold/collision guard over the hinge's driven range (pure poses at h["guard"] angles, interpolated key values): where
    the keyed mesh has MORE collapsed faces (area < 0.1 x rest) or more intersecting pairs than the key-free mesh, the
    vertices of the faces the key-free mesh lacks (+ rings) have their delta halved in the active keys; full passes repeat
    until one is clean (counts, not sets: the contact turns pass-through skin into compressed skin)."""
    from mathutils.bvhtree import BVHTree
    h = HINGES[hinge]
    body, rig = result["body"], result["runtime"]
    keys = [kb for kb in body.data.shape_keys.key_blocks if kb.name.startswith(h["prefix"])]
    rest = body.data.vertices
    bench._reset(rig)
    for kb in keys:
        kb.value = 0.0
    V0, F = bench._evaluated(body)
    A0 = [bench._area(V0, f) for f in F]
    moved = {kb.name: {i for i, d in enumerate(kb.data) if (d.co - rest[i].co).length > 1e-9} for kb in keys}

    def bad():
        V, _ = bench._evaluated(body)
        tree = BVHTree.FromPolygons(V, F, all_triangles=True)
        fs = [set(f) for f in F]
        pairs = {(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])}
        return pairs, {k for k, f in enumerate(F) if A0[k] > 1e-12 and bench._area(V, f) / A0[k] < 0.1}
    hist = []
    for _pass in range(4):
        passlog = {}
        for a in h["guard"]:
            _pose_pure(rig, hinge, a)
            for s in SIDES:
                for k, v in activations(hinge_angle_deg(rig, hinge, s), h["keys"], h.get("start")).items():
                    body.data.shape_keys.key_blocks[f"{h['prefix']}{s}_{k}"].value = v
            bpy.context.view_layer.update()
            vals = {kb.name: kb.value for kb in keys}
            active = [kb for kb in keys if kb.value > 0]
            if not active:
                continue
            for kb in keys:
                kb.value = 0.0
            base_p, base_c = bad()
            hh = []
            for _ in range(rounds):
                for kb in keys:
                    kb.value = vals[kb.name]
                p, c = bad()
                new_p, new_c = p - base_p, c - base_c
                hh.append((len(p) - len(base_p), len(c) - len(base_c)))
                if len(p) <= len(base_p) and len(c) <= len(base_c):     # counts no worse than key-free (contact turns
                    break                                                # pass-through skin into compressed skin)
                new_p = new_p if len(p) > len(base_p) else set()
                new_c = new_c if len(c) > len(base_c) else set()
                ring = {v for a2, b2 in new_p for f in (a2, b2) for v in F[f]} | {v for f in new_c for v in F[f]}
                for _r in range(rings):
                    ring |= {j for i in ring for j in adj[i]}
                for kb in active:
                    for i in ring & moved[kb.name]:
                        kb.data[i].co = rest[i].co + (kb.data[i].co - rest[i].co) * 0.5
            passlog[str(a)] = hh
            for kb in keys:
                kb.value = 0.0
        hist.append(passlog)
        if all(len(x) == 1 for x in passlog.values()):
            break
    bench._reset(rig)
    bpy.context.view_layer.update()
    return {"extra_pairs_and_collapsed_per_round": hist}


def drive(result):
    """Set every built K1 key from the current measured hinge angle (per side)."""
    body, rig = result["body"], result["runtime"]
    keys = body.data.shape_keys.key_blocks
    for hinge in result.get("k1_logs", {}):
        h = HINGES[hinge]
        for s in SIDES:
            for k, v in activations(hinge_angle_deg(rig, hinge, s), h["keys"], h.get("start")).items():
                keys[f"{h['prefix']}{s}_{k}"].value = v
    bpy.context.view_layer.update()


VIEWS = {"knee": (0.55, (("lateral", (3.0, 0.0, 0.0)), ("posterolateral", (2.1, 2.1, 0.0)))),
         "elbow": (0.45, (("lateral", (3.0, 0.0, 0.0)), ("anterolateral", (2.1, -2.1, 0.0))))}


def render_hinge(result, out, hinge="knee", angles=None):
    """Close-ups of the right (+X, F-SIDE-001) joint in pure flexion, without and with the K1 keys."""
    h = HINGES[hinge]
    angles = angles or h["keys"][:2]
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
    scale, views = VIEWS[hinge]
    cd = bpy.data.cameras.new("HGPT_K1_CAM_TMP"); cd.type = "ORTHO"; cd.ortho_scale = scale
    cam = bpy.data.objects.new("HGPT_K1_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for a in angles:
        for keyed in (False, True):
            _pose_pure(rig, hinge, a)
            for kb in body.data.shape_keys.key_blocks[1:]:
                kb.value = 0.0
            if keyed:
                drive(result)
            joint = rig.pose.bones[h["flexing"].format(s="r")].head.copy()
            for view, off in views:
                cam.location = joint + Vector(off)
                cam.rotation_euler = (joint - cam.location).to_track_quat("-Z", "Y").to_euler()
                name = f"{hinge}_{a}__{'k1' if keyed else 'base'}__{view}.png"
                scene.render.filepath = str(out / name)
                bpy.ops.render.render(write_still=True)
                written.append(name)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bench._reset(rig)
    return written


def hinge_sweep(result, with_keys, hinge="knee", angles=None):
    h = HINGES[hinge]
    angles = angles if angles is not None else range(0, h["keys"][-1] + 1, 10)
    body, rig = result["body"], result["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    floor = min(v.z for v in V0)
    rows = {}
    for a in angles:
        _pose_pure(rig, hinge, a)
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


def knee_sweep(result, with_keys, angles=range(0, 131, 10)):
    return hinge_sweep(result, with_keys, "knee", angles)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    hinge = args[args.index("--hinge") + 1] if "--hinge" in args else "knee"
    h = HINGES[hinge]
    only = list(h["benchmarks"])
    baseline = bench.run(None, only=only)
    holder = {}

    def setup(result):
        holder["result"] = result
        build(result, hinge)
        holder["before"] = hinge_sweep(result, False, hinge)
        holder["after"] = hinge_sweep(result, True, hinge)
        if "--renders" in args:
            holder["renders"] = render_hinge(result, Path(args[args.index("--renders") + 1]), hinge)

    corrected = bench.run(None, setup=setup, post_pose=drive, only=only)
    rep = {"kind": f"K1_{hinge.upper()}_CONTACT_CORRECTIVE", "approved": False, "scope": "experimental, in-memory keys; review-only",
           "parameters": {"hinge": hinge, "keys_deg": h["keys"], "activation_start_deg": ACTIVATION_START, "gap_mm": GAP_M * 1000,
                          "zone_radius_m": h["zone_r_m"], "taper_rings": TAPER_RINGS, "delta_cap_mm": DELTA_CAP_M * 1000},
           "solve_log": holder["result"]["k1_logs"][hinge],
           f"{hinge}_sweep": {"before": holder["before"], "after": holder["after"]},
           "benchmarks": {n: {"before": baseline["benchmarks"][n]["worst"], "after": corrected["benchmarks"][n]["worst"],
                              "volume_before": baseline["benchmarks"][n]["volume_change_pct_range"],
                              "volume_after": corrected["benchmarks"][n]["volume_change_pct_range"],
                              "frames_after": corrected["benchmarks"][n]["frames"]} for n in only},
           "renders": holder.get("renders", [])}
    print("K1", hinge, json.dumps(rep["solve_log"]))
    for n, b in rep["benchmarks"].items():
        print("K1", n, b["before"], "->", b["after"], b["volume_before"], "->", b["volume_after"])
    for a in holder["before"]:
        x, y = holder["before"][a], holder["after"][a]
        print("K1 sweep", a, x["self_intersecting_pairs"], "->", y["self_intersecting_pairs"], "collapse", x["collapse_lt_0_1"], "->",
              y["collapse_lt_0_1"], "stretch", x["stretch_gt_2"], "->", y["stretch_gt_2"], "vol", x["body_volume_change_pct"], "->", y["body_volume_change_pct"])
    if "--out" in args:
        out = Path(args[args.index("--out") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=1, default=str) + "\n")
