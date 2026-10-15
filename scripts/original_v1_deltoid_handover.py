"""Deltoid hand-over to the upper arm for ORIGINAL_v1 review candidates (bpy; weights only).  R20 (Claude, 15 Oct 2026).

Owner, on the press lockout: "I'm not sure the deforming is in the right place here" / "This highlighted areas shouldn't be
crinkled", then "I want it fixed".  Measured on R18: the outer / back deltoid band (0-12 cm below the shoulder joint) is
about 63 % shoulder_cap helper + 31 % arm (+ girdle).  The cap helper follows half of the arm-vs-scapula rotation and was
assigned with "never give the arm more of a vertex than it had", so this skin only follows the arm about two thirds of the
way.  At lockout it is left at about arm-out-sideways: the ball behind and below the joint.

Here, on the arm's lateral and posterior faces (radial direction within LAT of lateral/posterior), from T0 above to T1 below
the pivot along the rest arm axis, a smoothstep share k of each vertex's cap weight + GAMMA x its girdle (clavicle +
scapula) weight is handed to the upper arm.  The arm's medial face (armpit, chest wall) and everything above T0 (the top of
the shoulder, where a higher follow crushes the skin, R16) keep their weights.  Swept on R18 (raw skin at lockout, keys
off), recorded in docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R20_20261015.md:
  * band 2-8 cm, all of it: a hard crease line across the arm, and 112-144 pairs;
  * band -2..16 cm, 40 % girdle, outer + back: no crease, the ball much smaller, 0 pairs at lockout (default).
No bones are added and no influence is added beyond the vertex's own groups (the arm group already exists on these vertices).
"""
from __future__ import annotations

T0, T1 = -0.02, 0.16
GAMMA = 0.4
LAT = -0.4
RADIAL_MAX = 0.10
SIDES = ("l", "r")


def _sm(x, a, b):
    x = min(1.0, max(0.0, (x - a) / (b - a)))
    return x * x * (3 - 2 * x)


def assign(body, rig, t0=T0, t1=T1, gamma=GAMMA, lat=LAT, radial_max=RADIAL_MAX):
    names = {g.index: g.name for g in body.vertex_groups}
    moved = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0                    # F-SIDE-001: runtime _r is +X
        b = rig.data.bones[f"upperarm_{s}"]
        piv, axis = b.head_local, (b.tail_local - b.head_local).normalized()
        arm, cap, gird = f"upperarm_{s}", f"shoulder_cap_{s}", (f"clavicle_{s}", f"scapula_{s}")
        n = 0
        for v in body.data.vertices:
            if v.co.x * sign < 0.03:
                continue
            t = (v.co - piv).dot(axis)
            if t < t0 or t > t1 + 0.04:
                continue
            radial = (v.co - piv) - axis * t
            if radial.length > radial_max or radial.length < 1e-6:
                continue
            face = max(radial.x * sign, radial.y) / radial.length      # +1 lateral or posterior, -1 medial / anterior
            k = _sm(t, t0, t1) * _sm(face, lat, lat + 0.3)
            if k <= 1e-3:
                continue
            w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
            tot = sum(w.values())
            w = {x: y / tot for x, y in w.items()}
            H = w.get(cap, 0.0)
            G = sum(w.get(x, 0.0) for x in gird)
            m = k * (H + gamma * G)
            if m <= 1e-4:
                continue
            body.vertex_groups[arm].add([v.index], w.get(arm, 0.0) + m, "REPLACE")
            if H > 0:
                body.vertex_groups[cap].add([v.index], H * (1 - k), "REPLACE")
            for x in gird:
                if x in w:
                    body.vertex_groups[x].add([v.index], w[x] * (1 - k * gamma), "REPLACE")
            for x, y in w.items():
                if x not in gird and x not in (arm, cap):
                    body.vertex_groups[x].add([v.index], y, "REPLACE")
            n += 1
        moved[s] = n
    rig["hgpt_deltoid_handover"] = {"t_m": [t0, t1], "gamma": gamma, "lat": lat, "radial_max_m": radial_max}
    return moved


# R22: a smooth follow profile instead of a partial hand-over.  "Follow" = how much of the arm-vs-scapula turn a vertex makes:
# arm 1, shoulder_cap its fraction (0.5), girdle / trunk 0.  The owner circled a kink at the arm root (R18/R21): the follow
# drops from 100 % to ~50 % within a few cm there.  Here, on the arm's outer / back faces, each vertex's follow is raised
# towards 1 by smoothstep(t; P0, P1) along the rest arm axis (no change at P0, full at P1), faded out around the arm and
# towards the medial face, so it changes gradually over the whole deltoid; vertex weights are rewritten as arm / cap /
# girdle with that follow.  (F_TOP is unused since the continuous form; kept for the record of the first sweep.)
P0, P1, F_TOP = -0.04, 0.16, 0.5


def assign_profile(body, rig, p0=P0, p1=P1, f_top=F_TOP, lat=LAT, radial_max=RADIAL_MAX):
    names = {g.index: g.name for g in body.vertex_groups}
    fcap = float(rig.get("hgpt_cap_fraction", 0.5))
    moved = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0
        b = rig.data.bones[f"upperarm_{s}"]
        piv, axis = b.head_local, (b.tail_local - b.head_local).normalized()
        arm, cap, gird = f"upperarm_{s}", f"shoulder_cap_{s}", (f"clavicle_{s}", f"scapula_{s}")
        n = 0
        for v in body.data.vertices:
            if v.co.x * sign < 0.03:
                continue
            t = (v.co - piv).dot(axis)
            if t < p0 - 0.02 or t > p1 + 0.04:
                continue
            radial = (v.co - piv) - axis * t
            if radial.length > radial_max or radial.length < 1e-6:
                continue
            face = _sm(max(radial.x * sign, radial.y) / radial.length, lat, lat + 0.3)
            if face <= 1e-3:
                continue
            w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
            tot = sum(w.values())
            w = {x: y / tot for x, y in w.items()}
            A, H = w.get(arm, 0.0), w.get(cap, 0.0)
            G = sum(w.get(x, 0.0) for x in gird)
            M = A + H + G                                 # the arm/cap/girdle share (other bones keep theirs)
            if M <= 1e-4:
                continue
            f_now = (A + fcap * H) / M
            # continuous everywhere: no change at t = p0 and at the radial / facing edges, full follow at t = p1
            # (a target jump to f_top tore the skin where raised vertices met unchanged ones - measured, R22 sweep)
            fade_r = 1.0 - _sm(radial.length, radial_max - 0.03, radial_max)
            f_new = f_now + face * fade_r * _sm(t, p0, p1) * (1.0 - f_now)
            if f_new - f_now <= 1e-4:
                continue
            # arm/cap/girdle split with follow f_new: girdle shrinks first, then cap -> arm
            if f_new <= fcap:
                h, a = f_new / fcap, 0.0
                g = 1 - h
            else:
                a = (f_new - fcap) / (1 - fcap)
                h = 1 - a
                g = 0.0
            body.vertex_groups[arm].add([v.index], M * a, "REPLACE")
            body.vertex_groups[cap].add([v.index], M * h, "REPLACE")
            for x in gird:
                if x in w:
                    body.vertex_groups[x].add([v.index], M * g * (w[x] / G) if G > 1e-9 else 0.0, "REPLACE")
            if G <= 1e-9 and g > 1e-6:
                body.vertex_groups[f"scapula_{s}"].add([v.index], M * g, "REPLACE")
            for x, y in w.items():
                if x not in gird and x not in (arm, cap):
                    body.vertex_groups[x].add([v.index], y, "REPLACE")
            n += 1
        moved[s] = n
    rig["hgpt_deltoid_follow_profile"] = {"t_m": [p0, p1], "f_top": f_top, "lat": lat, "radial_max_m": radial_max}
    return moved
