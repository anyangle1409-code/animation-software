"""Muscle-line helper joints for the ORIGINAL_v1 review candidates (bpy).  R14 (Claude, 15 Oct 2026).

Owner: "Is this an issue with the mesh or weights? The muscles around the arm and shoulder ..." -> "Ok please proceed with it".

The reference photos' armpit is shaped by muscles: the pectoralis major (front axillary fold) and latissimus dorsi (back
axillary fold) run from the trunk to the upper humerus and STRETCH as the arm goes overhead, with the hollow between them.
Skinning to bones alone (trunk / shoulder cap / arm) gave a taut ridge to the collarbone and a bulge on the side of the back.

Each helper is a stretch joint along the muscle's line of action: head at an origin point fixed in the thorax (spine_03),
tail at an insertion point fixed in the humerus (upperarm); every frame it is aimed from the origin at the insertion and
scaled along its length (volume preserving across).  Skin over the muscle belly weighted to it therefore stays with the trunk
near the origin and moves with the arm near the insertion, interpolating along the muscle - the fold forms along the muscle
line instead of along a weight boundary.  Weights: inside a tapered corridor around the origin-insertion segment (belly
radius RADIUS at the origin end tapering to INS_RADIUS), on the muscle's side (front / back), a share HELPER_MAX of each
vertex's trunk + shoulder (+ arm) weight moves to the helper, smoothly faded at the corridor edge, at both ends and across
the front/back split at the GH pivot (SIDE_BAND; a hard split left a vertical crack on the side of the chest).

Landmarks are project-authored from the rig (no cohort source): positions relative to the glenohumeral pivot (GH) of each
side, x lateral (+) for the side, y anterior (-) / posterior (+), z up, metres; insertions as fractions along the rest humerus
plus an offset.  Helpers live in memory only (installed by drives.setup when the rig carries hgpt_muscle_lines), so the
saved blend stays a 67-bone file.  Review only: more runtime joints are a contract item (owner + Lane G, PR #26).
"""
from __future__ import annotations

import math
import os

import bpy
from mathutils import Matrix, Vector

_E = os.environ
SIDES = ("l", "r")
MUSCLES = {
    # origin rel. GH (x medial(-), y, z), insertion: (fraction along humerus, offset rel. humerus point in rest space)
    "pec": {"origin": (-0.17, -0.07, -0.08), "ins_frac": 0.20, "ins_off": (0.0, -0.025, 0.0), "side": "front"},
    "lat": {"origin": (-0.13, 0.08, -0.26), "ins_frac": 0.17, "ins_off": (-0.01, 0.0, 0.0), "side": "back",
            # the lat takes trunk weight only: taking the shoulder/arm share too dragged the back of the armpit into the arm
            # at the bent-over row's end pose (4 -> 36 pairs); trunk-only gives 0
            "takes": _E.get("ML_LAT_TAKES", "trunk"), "max_scale": float(_E.get("ML_LAT_SCALE", 1.0))},
}
ANATOMICAL = _E.get("ML_ANAT", "1") == "1"
ACTIVE = tuple(_E.get("ML_MUSCLES", "pec,lat,trap").split(","))
RADIUS = float(_E.get("ML_RADIUS", 0.14))
INS_RADIUS = float(_E.get("ML_INS_RADIUS", 0.07))
HELPER_MAX = float(_E.get("ML_MAX", 0.45))
SIDE_BAND = float(_E.get("ML_SIDE_BAND", 0.05))   # front (pec) / back (lat) blend half-width around the GH pivot (m)
BULGE_MAX = float(_E.get("ML_BULGE_MAX", 1.0))   # cross-scale cap when the muscle shortens (1.0: no thickening; the
                                                 # bent-over row's end pose pushed a thickened lat into the arm)
INNER = float(_E.get("ML_INNER", 0.1))        # full helper share inside INNER * radius, fading to 0 at the radius
S_FADE = (0.05, 0.25)        # fade in from the origin end (fraction of the segment)
S_END = (0.95, 1.15)         # fade out past the insertion


# R14b (owner: "Continue with fix", after the muscle-evidence question): attachments from standard descriptive anatomy,
# placed on this skeleton's own landmarks (LM_* empties of the anatomical audit: sternum IJ/PX, clavicle SC/AC, scapula
# AA/AI/TS/GH, humerus EJC), no third-party model data (the MoBL-ARMS OpenSim model is licensed non-commercial only).
# Muscle lengths along press path v2 measured on this rig (docs, R14): lat 156 %, teres major 139 %, pectoralis major
# sternal head 132 % of rest at lockout (stretched: the axillary folds), deltoid middle 54 %, anterior 79 %, upper
# trapezius 80 % (shortened: bunching).  Origin carried by `obone`, insertion by `ibone`; `bulge` caps the cross-scale
# when the line shortens (the trapezius bunches, the others do not thicken).
ANAT = {
    "pec": {"obone": "spine_03", "ibone": "upperarm", "side": "front", "takes": "all", "bulge": 1.0, "radius": (0.14, 0.07)},
    "lat": {"obone": "scapula", "ibone": "upperarm", "side": "back", "takes": "trunk", "bulge": 1.0, "radius": (0.12, 0.07)},
    "trap": {"obone": "neck", "ibone": "clavicle", "side": "top", "takes": "neckgird", "radius": (0.06, 0.06),
             "bulge": float(_E.get("ML_TRAP_BULGE", 1.25)), "max_scale": float(_E.get("ML_TRAP_SCALE", 1.0))},
}


def name(m, s):
    return f"muscle_{m}_{s}"


def _lm(n):
    o = bpy.data.objects.get(f"LM_{n}")
    return o.matrix_world.translation.copy() if o else None


def _anat_points(rig, m, s):
    """(origin, insertion) of muscle m on side s from the skeleton landmarks (runtime _r = anatomical left)."""
    side = "left" if s == "r" else "right"
    GH, EJC = _lm(f"scapula_{side}__GH"), _lm(f"humerus_{side}__EJC")
    IJ, PX, AI = _lm("sternum__ij_skin"), _lm("sternum__px_skin"), _lm(f"scapula_{side}__AI")
    SC, AC = _lm(f"clavicle_{side}__SC"), _lm(f"clavicle_{side}__AC")
    if None in (GH, EJC, IJ, PX, AI, SC, AC):
        return None
    sign = 1.0 if GH.x > 0 else -1.0
    hum = lambda f: GH + (EJC - GH) * f
    if m == "pec":      # sternocostal head: mid-sternum (2.5 cm deep to the skin landmarks, 2 cm lateral) -> lateral lip of
        return (IJ.lerp(PX, 0.5) + Vector((sign * 0.02, 0.025, 0.0)), hum(0.17) + Vector((0.0, -0.012, 0.0)))  # the groove
    if m == "lat":      # visible part of the posterior fold: inferior angle of the scapula -> floor of the groove
        return (AI.copy(), hum(0.14) + Vector((-sign * 0.008, -0.004, 0.0)))
    if m == "trap":     # descending part: nuchal line / C7 region -> lateral third of the clavicle
        return (Vector((sign * 0.02, IJ.y + 0.12, IJ.z + 0.12)), SC.lerp(AC, 0.85))
    return None


def _points(rig, m, s):
    if ANATOMICAL:
        pts = _anat_points(rig, m, s)
        if pts is None:
            raise RuntimeError("anatomical muscle lines need the skeleton landmarks (LM_*) in the blend")
        return pts
    sign = 1.0 if s == "r" else -1.0
    ub = rig.data.bones[f"upperarm_{s}"]
    gh = ub.head_local
    spec = MUSCLES[m]
    o = spec["origin"]
    origin = gh + Vector((o[0] * sign, o[1], o[2]))
    hum = ub.head_local + (ub.tail_local - ub.head_local) * spec["ins_frac"]
    off = spec["ins_off"]
    insertion = hum + Vector((off[0] * sign, off[1], off[2]))
    return origin, insertion


def _active():
    return ACTIVE if ANATOMICAL else tuple(MUSCLES)


def _spec(m):
    if ANATOMICAL:
        return ANAT[m]
    return {"obone": "spine_03", "ibone": "upperarm", "side": MUSCLES[m]["side"], "takes": MUSCLES[m].get("takes", "all"),
            "bulge": BULGE_MAX, "max_scale": MUSCLES[m].get("max_scale", 1.0)}


def _bone(key, s):
    return {"spine_03": "spine_03", "neck": "neck", "scapula": f"scapula_{s}", "clavicle": f"clavicle_{s}",
            "upperarm": f"upperarm_{s}"}[key]


def _first(rig):
    return name(_active()[0], "l")


def install(rig):
    if "hgpt_muscle_lines" not in rig or _first(rig) in rig.data.bones:
        return
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in SIDES:
        for m in _active():
            origin, insertion = _points(rig, m, s)
            b = rig.data.edit_bones.new(name(m, s))
            b.head, b.tail = origin, insertion
            b.parent = rig.data.edit_bones[_bone(_spec(m)["obone"], s)]
            b.use_connect = False
            b.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    view.update()


def drive(rig):
    if _first(rig) not in rig.pose.bones:
        return
    bpy.context.view_layer.update()
    carry = lambda bn: rig.pose.bones[bn].matrix @ rig.data.bones[bn].matrix_local.inverted()
    for s in SIDES:
        for m in _active():
            spec = _spec(m)
            ob, ib = carry(_bone(spec["obone"], s)), carry(_bone(spec["ibone"], s))
            bone = rig.data.bones[name(m, s)]
            o0, i0 = bone.head_local, bone.tail_local
            o1, i1 = ob @ o0, ib @ i0
            d0 = i0 - o0
            rest_rot = ob.to_3x3() @ bone.matrix_local.to_3x3()          # rest frame carried by the origin bone
            q = (ob.to_3x3() @ d0).normalized().rotation_difference((i1 - o1).normalized())
            sy = (i1 - o1).length / d0.length
            sx = min(1.0 / math.sqrt(max(sy, 1e-6)), spec["bulge"])  # thins when stretched; capped thickening when shortened
            M = Matrix.Translation(o1) @ (q.to_matrix() @ rest_rot).to_4x4() @ Matrix.Diagonal((sx, sy, sx, 1.0))
            rig.pose.bones[name(m, s)].matrix = M
    bpy.context.view_layer.update()


def remove(rig):
    names = [name(m, s) for s in SIDES for m in set(MUSCLES) | set(ANAT)]
    if not any(n in rig.data.bones for n in names):
        return
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for n in names:
        if n in rig.data.edit_bones:
            rig.data.edit_bones.remove(rig.data.edit_bones[n])
    bpy.ops.object.mode_set(mode="OBJECT")
    view.update()


def _smooth(t, a, b):
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3 - 2 * x)


def assign_weights(body, rig, helper_max=None, radius=None, ins_radius=None, muscles=None):
    helper_max = HELPER_MAX if helper_max is None else helper_max
    muscles = muscles or _active()
    counts = {}
    for s in SIDES:
        sign = 1.0 if s == "r" else -1.0
        gh = rig.data.bones[f"upperarm_{s}"].head_local
        sets = {"all": ("spine_03", "spine_02", "spine_01", f"clavicle_{s}", f"scapula_{s}", f"shoulder_cap_{s}", f"upperarm_{s}"),
                "trunk": ("spine_03", "spine_02", "spine_01"),
                "neckgird": ("head", "neck", "spine_03", f"clavicle_{s}", f"scapula_{s}")}
        for m in muscles:
            spec = _spec(m)
            r0 = spec.get("radius", (RADIUS, INS_RADIUS))[0] if radius is None else radius
            r1 = spec.get("radius", (RADIUS, INS_RADIUS))[1] if ins_radius is None else ins_radius
            names = {g.index: g.name for g in body.vertex_groups}
            o, i = _points(rig, m, s)
            seg = i - o
            L2 = seg.length_squared
            grp = body.vertex_groups.get(name(m, s)) or body.vertex_groups.new(name=name(m, s))
            movable = sets[spec["takes"]]
            hmax = helper_max * spec.get("max_scale", 1.0)
            n = 0
            for v in body.data.vertices:
                p = v.co
                if p.x * sign <= 0.0:
                    continue
                sp = (p - o).dot(seg) / L2
                if sp < S_FADE[0] or sp > S_END[1]:
                    continue
                d = (p - (o + seg * min(max(sp, 0.0), 1.0))).length
                r = r0 + (r1 - r0) * min(max(sp, 0.0), 1.0)
                if d >= r:
                    continue
                if spec["side"] == "top":
                    side = 1.0
                else:
                    side = 1 - _smooth(p.y, gh.y - SIDE_BAND, gh.y + SIDE_BAND)    # 1 in front of the GH pivot, 0 behind
                    side = side if spec["side"] == "front" else 1 - side
                if side < 1e-3:
                    continue
                w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
                tot = sum(w.values())
                w = {k: x / tot for k, x in w.items()}
                mov = sum(w.get(k, 0.0) for k in movable)
                if mov < 1e-3:
                    continue
                h = hmax * side * (1 - _smooth(d, INNER * r, r)) * _smooth(sp, *S_FADE) * (1 - _smooth(sp, *S_END))
                if h < 1e-3:
                    continue
                take = min(h, mov)
                for k in movable:
                    if k in w:
                        body.vertex_groups[k].add([v.index], w[k] * (1 - take / mov), "REPLACE")
                grp.add([v.index], w.get(name(m, s), 0.0) + take, "REPLACE")
                n += 1
            counts[f"{m}_{s}"] = n
    rig["hgpt_muscle_lines"] = {"muscles": list(muscles), "helper_max": helper_max, "anatomical": ANATOMICAL}
    return counts
