"""Hip-crease helper joint for ORIGINAL_v1 review candidates (bpy; R13, Claude, 15 Oct 2026).  Owner: "Yes. Continue" (the
hip fold with the shoulder recipe).

Why: in deep hip flexion (squat 110 deg, deadlift 135 deg) the skin of the groin crease, at and above the hip joint, is weighted
to the thigh and swings the full hip flexion, folding onto itself and passing through the lower abdomen (R12: squat 227,
deadlift 313 self-intersecting pairs, all in the crease).  This is the same fold the shoulder-cap helper removed at the top of
the shoulder (R8: 216 -> 0 pairs).

What: one extra deforming joint per side, `hip_crease_<s>`, as scripts/original_v1_shoulder_cap_helper.py:
  * head at the hip-joint centre (thigh head), the thigh's rest frame, parented to the pelvis;
  * driven statelessly to FRACTION of the thigh's rotation relative to the pelvis (axis-angle, principal branch);
  * chain weights: around the joint, each vertex's trunk (pelvis + spine_01) + thigh share is redistributed by its position
    along the rest thigh axis (trunk -> helper -> thigh between T1 and T2), thigh weight only ever reduced, faded back to
    the original weights between FADE_R0 and FADE_R1 from the joint; then the 4-influence limit.
The saved blend keeps the vertex groups and parameters (rig props `hgpt_hip_*`), not the bones; install() recreates them in
memory (drives.setup).  Review only: two more runtime joints are a contract change (owner + Lane G, PR #26).
"""
from __future__ import annotations

import math
import os

import bpy
from mathutils import Quaternion, Vector

_E = os.environ
FRACTION = float(_E.get("HIP_FRACTION", 0.45))
T1, T2 = (float(v) for v in _E.get("HIP_T", "-0.10,0.16").split(","))
FADE_R0, FADE_R1 = (float(v) for v in _E.get("HIP_FADE", "0.14,0.20").split(","))
TRUNK = ("pelvis", "spine_01")
SIDES = ("l", "r")


def name(s):
    return f"hip_crease_{s}"


def install(rig):
    if "hgpt_hip_fraction" not in rig or name("l") in rig.data.bones:
        return
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in SIDES:
        th = rig.data.edit_bones[f"thigh_{s}"]
        h = rig.data.edit_bones.new(name(s))
        h.head = th.head.copy()
        h.tail = th.head + (th.tail - th.head) * 0.3
        h.roll = th.roll
        h.parent = rig.data.edit_bones["pelvis"]
        h.use_connect = False
        h.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    view.update()


def drive(rig):
    if name("l") not in rig.pose.bones:
        return
    import original_v1_review_candidate_drives as drives
    bpy.context.view_layer.update()
    f = float(rig["hgpt_hip_fraction"])
    for s in SIDES:
        q = drives._rel_quat(rig, f"thigh_{s}", "pelvis")
        if q.w < 0:
            q.negate()
        h = rig.pose.bones[name(s)]
        h.rotation_mode = "QUATERNION"
        h.rotation_quaternion = Quaternion(q.axis, q.angle * f) if q.angle > 1e-9 else Quaternion()
    bpy.context.view_layer.update()


H1_PREFIX = "HGPT_H1_BAKE_"
H1_START = 20.0


def hip_flexion_deg(rig, s):
    """Sagittal hip flexion: the thigh's direction in the pelvis frame against rest, + when the knee comes forward."""
    pb, pp = rig.pose.bones[f"thigh_{s}"], rig.pose.bones["pelvis"]
    rest_p = rig.data.bones["pelvis"].matrix_local.to_3x3()
    d0 = rest_p.inverted() @ (rig.data.bones[f"thigh_{s}"].matrix_local.to_3x3().col[1])
    d = pp.matrix.to_3x3().inverted() @ pb.matrix.to_3x3().col[1]
    fwd = rest_p.inverted() @ Vector((0.0, -1.0, 0.0))            # body anterior (-Y) in the pelvis frame
    down = d0.normalized()
    a0 = math.atan2(d0.dot(fwd), d0.dot(down))
    a = math.atan2(d.dot(fwd), d.dot(down))
    return math.degrees(a - a0)


def drive_h1(rig, body):
    """HGPT_H1_BAKE_<s>_<deg> keys (R13 baked hip delta mush): piecewise linear on hip flexion from H1_START, the last
    key held above its angle (the S1 scheme, angle source = hip_flexion_deg)."""
    keys = body.data.shape_keys.key_blocks if body.data.shape_keys else []
    for s in SIDES:
        names = sorted((kb.name for kb in keys if kb.name.startswith(f"{H1_PREFIX}{s}_")), key=lambda n: int(n.rsplit("_", 1)[1]))
        if not names or f"hgpt_h1_angles_{s}" not in rig:
            continue
        pts = (H1_START,) + tuple(rig[f"hgpt_h1_angles_{s}"])
        e = hip_flexion_deg(rig, s)
        for n, nm in enumerate(names):
            lo, mid = pts[n], pts[n + 1]
            hi = pts[n + 2] if n + 2 < len(pts) else None
            if e <= lo:
                v = 0.0
            elif e <= mid:
                v = (e - lo) / (mid - lo)
            elif hi is None:
                v = 1.0
            else:
                v = max(0.0, (hi - e) / (hi - mid))
            keys[nm].value = v


def remove(rig):
    if name("l") not in rig.data.bones:
        return
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in SIDES:
        if name(s) in rig.data.edit_bones:
            rig.data.edit_bones.remove(rig.data.edit_bones[name(s)])
    bpy.ops.object.mode_set(mode="OBJECT")
    view.update()


def _smooth(t, a, b):
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3 - 2 * x)


def _limit_deform(body, rig, k):
    """4-influence limit over deform-bone groups only (mask groups are left alone), and only on vertices with a hip weight."""
    deform = {b.name for b in rig.data.bones if b.use_deform} | {name(s) for s in SIDES}
    names = {g.index: g.name for g in body.vertex_groups}
    helpers = {body.vertex_groups[name(s)].index for s in SIDES if name(s) in body.vertex_groups}
    fixed = 0
    for v in body.data.vertices:
        if not any(g.group in helpers and g.weight > 0 for g in v.groups):
            continue
        w = [(names[g.group], g.weight) for g in v.groups if g.weight > 0 and names[g.group] in deform]
        if len(w) <= k:
            continue
        keep = dict(sorted(w, key=lambda kv: -kv[1])[:k])
        tot = sum(keep.values())
        for n, _x in w:
            if n in keep:
                body.vertex_groups[n].add([v.index], keep[n] / tot, "REPLACE")
            else:
                body.vertex_groups[n].remove([v.index])
        fixed += 1
    return fixed


def assign_weights(body, rig, fraction=None, t1=None, t2=None, r0=None, r1=None, max_influences=4):
    fraction = FRACTION if fraction is None else fraction
    t1 = T1 if t1 is None else t1
    t2 = T2 if t2 is None else t2
    r0 = FADE_R0 if r0 is None else r0
    r1 = FADE_R1 if r1 is None else r1
    counts = {}
    for s in SIDES:
        names = {g.index: g.name for g in body.vertex_groups}
        sign = 1.0 if s == "r" else -1.0
        b = rig.data.bones[f"thigh_{s}"]
        piv, axis = b.head_local, (b.tail_local - b.head_local).normalized()
        grp = body.vertex_groups.get(name(s)) or body.vertex_groups.new(name=name(s))
        thigh = f"thigh_{s}"
        n = 0
        for v in body.data.vertices:
            if v.co.x * sign <= 0.0:                    # midline vertices keep their weights
                continue
            d = (v.co - piv).length
            if d >= r1:
                continue
            w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
            tot = sum(w.values())
            w = {k: x / tot for k, x in w.items()}
            A = w.get(thigh, 0.0)
            G = sum(w.get(k, 0.0) for k in TRUNK)
            M = A + G
            if A <= 1e-4 or M <= 1e-4:
                continue
            u = min(_smooth((v.co - piv).dot(axis), t1, t2), A / M)     # thigh weight only ever reduced
            new_a = M * max(0.0, 2 * u - 1)
            new_h = M * (1 - abs(2 * u - 1))
            new_g = M * max(0.0, 1 - 2 * u)
            fade = 1.0 - _smooth(d, r0, r1)
            a_w = A + fade * (new_a - A)
            h_w = fade * new_h
            g_tot = G + fade * (new_g - G)
            for k in TRUNK:
                if k in w:
                    body.vertex_groups[k].add([v.index], g_tot * (w[k] / G) if G > 1e-9 else 0.0, "REPLACE")
            if G <= 1e-9 and g_tot > 1e-6:
                body.vertex_groups["pelvis"].add([v.index], g_tot, "REPLACE")
            body.vertex_groups[thigh].add([v.index], a_w, "REPLACE")
            if h_w > 1e-5:
                grp.add([v.index], h_w, "REPLACE")
                n += 1
        counts[s] = n
    limited = _limit_deform(body, rig, max_influences)
    rig["hgpt_hip_fraction"] = fraction
    rig["hgpt_hip_params"] = {"t_m": [t1, t2], "fade_m": [r0, r1]}
    return {"vertices": counts, "influence_limited": limited}
