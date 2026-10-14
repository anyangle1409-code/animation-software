"""Shoulder-cap helper joint for ORIGINAL_v1 review candidate R8 (bpy; owner, 14 Oct 2026: "Yes, build R8 with the helper
joint").

Why: at 140-160 deg humerothoracic elevation the skin on top of the shoulder, above the glenohumeral pivot, is weighted to
the upper arm and swings the full arm-vs-scapula rotation (~119 deg) around the pivot, folding onto itself and tucking
under the girdle skin (R7: 216 self-intersecting pairs at 160 deg, 6-20 mm deep; pose-space keys cannot unfold it).

What: one extra deforming joint per side, `shoulder_cap_<s>`:
  * head at the upper-arm pivot (GH centre), same rest frame as the upper arm, parented like the upper arm (it follows the
    girdle);
  * driven statelessly: FRACTION of the upper arm's rotation relative to the scapula (axis-angle, principal branch);
  * weights: a cap of skin around the pivot (radius RADIUS, upper side only, faded below the pivot over Z_FADE) takes up to
    AMOUNT helper weight, removed proportionally from the vertex's existing weights (sum stays 1), then the usual 4-influence
    limit.
Like R1's W3A helper, the saved blend keeps the vertex groups and parameters (rig props `hgpt_cap_*`) but not the bones, so
the file stays a 67-bone rig; install() recreates the bones in memory before posing.  Review only: a 69-joint runtime is a
contract change (owner + Lane G, PR #26).
"""
from __future__ import annotations

import math
import os

import bpy
from mathutils import Quaternion, Vector

_E = os.environ
FRACTION = float(_E.get("CAP_FRACTION", 0.5))
AMOUNT = float(_E.get("CAP_AMOUNT", 0.6))
RADIUS = float(_E.get("CAP_RADIUS", 0.10))
Z_FADE = float(_E.get("CAP_ZFADE", 0.03))
Z_OFFSET = float(_E.get("CAP_ZOFF", 0.0))      # cap starts this far above (+) / below (-) the pivot
MODE = _E.get("CAP_MODE", "axial")
CAP_ONLY_REDUCE = _E.get("CAP_REDUCE", "1") == "1"
T1, T2 = (float(v) for v in _E.get("CAP_T", "-0.06,0.10").split(","))   # axial mode: girdle -> helper -> arm along the arm axis
FADE_R0, FADE_R1 = (float(v) for v in _E.get("CAP_FADE", "0.16,0.22").split(","))   # blend back to the original weights
SIDES = ("l", "r")


def name(s):
    return f"shoulder_cap_{s}"


def install(rig):
    """Recreate shoulder_cap_<s> in memory (no-op without R8 data or when already present).  Rig at rest."""
    if "hgpt_cap_fraction" not in rig or name("l") in rig.data.bones:
        return
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in SIDES:
        up = rig.data.edit_bones[f"upperarm_{s}"]
        h = rig.data.edit_bones.new(name(s))
        h.head = up.head.copy()
        h.tail = up.head + (up.tail - up.head) * 0.4
        h.roll = up.roll
        h.parent = up.parent
        h.use_connect = False
        h.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    view.update()


def drive(rig):
    if name("l") not in rig.pose.bones:
        return
    import original_v1_review_candidate_drives as drives
    bpy.context.view_layer.update()
    f = float(rig["hgpt_cap_fraction"])
    for s in SIDES:
        q = drives._rel_quat(rig, f"upperarm_{s}", f"scapula_{s}")
        if q.w < 0:
            q.negate()
        h = rig.pose.bones[name(s)]
        h.rotation_mode = "QUATERNION"
        h.rotation_quaternion = Quaternion(q.axis, q.angle * f) if q.angle > 1e-9 else Quaternion()
    bpy.context.view_layer.update()


def _smooth(t, a, b):
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3 - 2 * x)


def assign_weights_axial(body, rig, fraction=None, t1=None, t2=None, r0=None, r1=None, max_influences=4):
    """Chain weights along the arm axis: around the pivot the girdle+arm share M of each vertex is redistributed by the
    signed distance t along the rest arm axis (pivot -> elbow): girdle below u=0.5 of the ramp, helper at its middle, arm
    beyond - every neighbouring pair of influences is at most FRACTION (or 1-FRACTION) of the rotation apart, so no
    candy-wrapper collapse.  Faded back to the original weights between r0 and r1 from the pivot."""
    fraction = FRACTION if fraction is None else fraction
    t1 = T1 if t1 is None else t1
    t2 = T2 if t2 is None else t2
    r0 = FADE_R0 if r0 is None else r0
    r1 = FADE_R1 if r1 is None else r1
    names = {g.index: g.name for g in body.vertex_groups}
    counts = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0                       # F-SIDE-001: runtime _r is +X
        b = rig.data.bones[f"upperarm_{s}"]
        piv, axis = b.head_local, (b.tail_local - b.head_local).normalized()
        grp = body.vertex_groups.get(name(s)) or body.vertex_groups.new(name=name(s))
        arm, gird = f"upperarm_{s}", (f"clavicle_{s}", f"scapula_{s}")
        n = 0
        for v in body.data.vertices:
            if v.co.x * sign < 0.03:
                continue
            d = (v.co - piv).length
            if d >= r1:
                continue
            w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
            tot = sum(w.values())
            w = {k: x / tot for k, x in w.items()}
            A = w.get(arm, 0.0)
            G = sum(w.get(k, 0.0) for k in gird)
            M = A + G
            if A <= 1e-4 or M <= 1e-4:
                continue
            u = _smooth((v.co - piv).dot(axis), t1, t2)
            if CAP_ONLY_REDUCE:                    # never give the arm more of a vertex than it had (armpit / chest stay)
                u = min(u, A / M)
            new_arm = M * max(0.0, 2 * u - 1)
            new_h = M * (1 - abs(2 * u - 1))
            new_g = M * max(0.0, 1 - 2 * u)
            fade = 1.0 - _smooth(d, r0, r1)
            arm_w = A + fade * (new_arm - A)
            h_w = fade * new_h
            g_tot = G + fade * (new_g - G)
            for k in gird:                                          # keep the clavicle/scapula split
                if k in w:
                    body.vertex_groups[k].add([v.index], g_tot * (w[k] / G) if G > 1e-9 else 0.0, "REPLACE")
            if G <= 1e-9 and g_tot > 1e-6:
                body.vertex_groups[f"scapula_{s}"].add([v.index], g_tot, "REPLACE")
            body.vertex_groups[arm].add([v.index], arm_w, "REPLACE")
            for k, x in w.items():
                if k != arm and k not in gird:
                    body.vertex_groups[k].add([v.index], x, "REPLACE")
            if h_w > 1e-5:
                grp.add([v.index], h_w, "REPLACE")
                n += 1
        counts[s] = n
    limited = _limit(body, max_influences)
    rig["hgpt_cap_fraction"] = fraction
    rig["hgpt_cap_params"] = {"mode": "axial", "t_m": [t1, t2], "fade_m": [r0, r1]}
    return {"vertices": counts, "influence_limited": limited}


def assign_weights(body, rig, amount=None, radius=None, z_fade=None, z_offset=None, fraction=None, max_influences=4):
    """Add the cap weights (in place) and store the parameters on the rig.  Returns per-side vertex counts."""
    amount = AMOUNT if amount is None else amount
    radius = RADIUS if radius is None else radius
    z_fade = Z_FADE if z_fade is None else z_fade
    z_offset = Z_OFFSET if z_offset is None else z_offset
    fraction = FRACTION if fraction is None else fraction
    names = {g.index: g.name for g in body.vertex_groups}
    counts = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0                       # F-SIDE-001: runtime _r is +X
        piv = rig.data.bones[f"upperarm_{s}"].head_local
        grp = body.vertex_groups.get(name(s)) or body.vertex_groups.new(name=name(s))
        n = 0
        for v in body.data.vertices:
            if v.co.x * sign < 0.03:
                continue
            w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
            if not any(k.endswith(f"_{s}") and k.startswith(("upperarm_", "clavicle_", "scapula_")) for k in w):
                continue
            d = (v.co - piv).length
            if d >= radius:
                continue
            radial = 0.5 * (1 + math.cos(math.pi * d / radius))          # 1 at the pivot, 0 at the radius
            dz = v.co.z - (piv.z + z_offset)
            vert = 1.0 if dz >= 0 else max(0.0, 1.0 + dz / z_fade)        # upper side; fades below
            h = amount * radial * vert
            if h < 1e-4:
                continue
            tot = sum(w.values())
            for k, x in w.items():
                body.vertex_groups[k].add([v.index], x / tot * (1 - h), "REPLACE")
            grp.add([v.index], h, "REPLACE")
            n += 1
        counts[s] = n
    limited = _limit(body, max_influences)
    rig["hgpt_cap_fraction"] = fraction
    rig["hgpt_cap_params"] = {"amount": amount, "radius_m": radius, "z_fade_m": z_fade, "z_offset_m": z_offset}
    return {"vertices": counts, "influence_limited": limited}


def _limit(body, k):
    names = {g.index: g.name for g in body.vertex_groups}
    fixed = 0
    for v in body.data.vertices:
        w = [(names[g.group], g.weight) for g in v.groups if g.weight > 0]
        if len(w) <= k:
            continue
        keep = sorted(w, key=lambda kv: -kv[1])[:k]
        tot = sum(x for _, x in keep)
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([v.index])
        for n, x in keep:
            body.vertex_groups[n].add([v.index], x / tot, "REPLACE")
        fixed += 1
    return fixed


def remove(rig):
    """Delete the in-memory helper bones (before saving: the review blend stays a 67-bone file)."""
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
