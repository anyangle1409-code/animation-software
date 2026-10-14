"""R4 shoulder rebuild for ORIGINAL_v1 (bpy; review candidate work, owner-approved 14 Oct 2026: "do all four including
lowering the pivot").  docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md explains the defects this addresses.

  1. anatomical scapula orientation: the profile's ISB angles (internal rotation, upward rotation, posterior tilt) are
     applied in the scapula's landmark frame relative to the thorax (original_v1_scapula_isb_drive.scapula_rotation), not
     as an Euler in the runtime bone's local axes;
  2. scapulothoracic contact: the blade hangs from the AC joint (runtime clavicle tail) and an extra clavicle rotation about
     the sternoclavicular joint (protraction about world Z, elevation about the clavicle-normal axis) is solved (damped least
     squares, CONTACT_PENALTY; plus an extra scapular internal rotation that wraps the blade around the thorax) so the medial border (TS) and inferior angle (AI) keep their rest distances to a thorax
     ellipsoid fitted to the rib/sternum guides - the blade glides on the thorax instead of pivoting off it (the rib tubes
     themselves are not a surface: a first version solved against them and produced a 30 deg shrug; rejected);
  3. weights: the scapula's influence is tapered with distance from the AC joint (full within TAPER_R0, none beyond
     TAPER_R1; the rest goes to the thorax) and the deltoid cap's girdle weight lateral of the AC joint is moved to the upper
     arm (DELTOID_SHIFT at full lateral distance) - the deltoid inserts on the humerus;
  4. arm pivot: the runtime upper-arm bone head moves to the anatomical glenohumeral-centre landmark (53 mm lower); its
     tail (the elbow) stays.  This edits the review copy's rest bone, never a003.
Runtime `_r` pairs with the anatomical-LEFT landmarks (F-SIDE-001).  install() wraps the coupled pose in memory.
"""
from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

import original_v1_scapula_isb_drive as isb

TAPER_R0, TAPER_R1 = (float(v) for v in __import__("os").environ.get("R4_TAPER", "0.10,0.18").split(","))
_E = __import__("os").environ
DELTOID_SHIFT = float(_E.get("R4_SHIFT", 0.6))
DELTOID_BAND = tuple(float(v) for v in _E.get("R4_BAND", "-0.02,0.08").split(","))   # lateral ramp 0 -> DELTOID_SHIFT
NO_LEAK = _E.get("R4_NOLEAK", "0") == "1"         # smoothing may not create upper-arm weight on skin that had none
WEIGHT_SMOOTH = int(_E.get("R4_WSMOOTH", 10))     # Laplacian passes over the changed weights (+3 rings), renormalised
# selected 14 Oct from a sweep (coupled 80-160 deg + renders): an unsmoothed 2-5 cm ramp creased the posterior deltoid at
# 90 deg (upper-arm self-pairs 18-74 at 80-100 deg); -2..8 cm, 0.6, 10 passes removed it (0 pairs at 80-100 deg).
# penalties (m of contact error per rad) on the extra (clavicle protraction, clavicle elevation, scapular internal rotation):
# the blade wraps on the thorax by internal rotation; the clavicle is held near the profile (a clavicle-only solve produced
# a 25-30 deg shrug, and freer clavicle protraction (0.04, 0.10) creased the skin between the blades: both rejected).  The
# selected penalties leave 16-23 mm of lift-off at 160 deg HT (was 91-117 mm with no contact term).
# five solver variables: clavicle protraction, clavicle elevation, and deviations of the scapula's ISB internal rotation,
# upward rotation and posterior tilt from the profile.  Upward rotation and tilt are held near the profile (the first R4
# let a free extra rotation reach ~9 deg EXTERNAL rotation, 6 deg less upward rotation and 11 deg more tilt than the
# profile: the "hanging" blade seen in the x-ray).  Selected (owner: "fix the blade tilt"): upward rotation and tilt held
# to the profile (penalty 1.0), internal rotation free (0.01) - it settles ~9 deg external at 160 deg HT to stay near the
# thorax; with this model's blade and thorax shapes the profile's three angles cannot all hold with the blade on the ribs
# (exact profile angles leave the inferior angle 49 mm off; the selected setting 47 mm; a freer clavicle shrugs).
CONTACT_PENALTY = tuple(float(v) for v in __import__("os").environ.get("R4_PEN", "0.25,0.25,0.01,1.0,1.0").split(","))
# R4 as published (52e375bd) used the "wrap" mode: clavicle protraction, clavicle elevation and a free extra rotation about
# the blade's superior axis, penalties below.  Kept so the R4 blend replays exactly; R5 uses the "isb" mode above.
WRAP_PENALTY = (0.25, 0.25, 0.005)
MODES = {"R4": "wrap", "R5": "isb"}
_S = {}


def lower_pivot(result):
    """Move upperarm_<s>.head to the anatomical GH landmark (rest), keeping the tail.  Returns the moves in mm."""
    rig = result["runtime"]
    gh = {s: bpy.data.objects[f"LM_scapula_{a}__GH"].matrix_world.translation.copy() for s, a in isb.ANAT.items()}
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    moved = {}
    for s in ("r", "l"):
        eb = rig.data.edit_bones[f"upperarm_{s}"]
        roll = eb.roll
        moved[s] = [round((gh[s][i] - eb.head[i]) * 1000, 1) for i in range(3)]
        eb.head = gh[s]
        eb.roll = roll
    bpy.ops.object.mode_set(mode="OBJECT")
    view.update()
    import build_functional_shoulder_correction_blender as correction
    for side, name in correction.HUMERI:                      # the axial reference follows the moved rest bone
        b = rig.data.bones[name]
        result["humeral_rest_axial_deg"][name] = correction.corr.humeral_axial_angle_deg(
            tuple(b.tail_local - b.head_local), tuple(b.matrix_local.col[0].xyz), 40.0, side)
    return moved


def reweight(result):
    """Scapula taper + deltoid-cap shift (see module doc).  Returns counts."""
    body, rig = result["body"], result["runtime"]
    names = {g.index: g.name for g in body.vertex_groups}
    G = body.vertex_groups
    before = _weights(body)
    tapered = isb.taper_scapula_weights(result, TAPER_R0, TAPER_R1)
    shifted = 0
    for s, sign in (("r", 1.0), ("l", -1.0)):
        ac = rig.data.bones[f"clavicle_{s}"].tail_local
        for v in body.data.vertices:
            lat = sign * v.co.x - sign * ac.x
            if lat <= DELTOID_BAND[0] or v.co.z < ac.z - 0.16 or v.co.x * sign <= 0:
                continue
            w = {names[g.group]: g.weight for g in v.groups}
            wu = w.get(f"upperarm_{s}", 0.0)
            girdle = {n: x for n, x in w.items() if n in (f"clavicle_{s}", f"scapula_{s}") and x > 0}
            if wu <= 0 or not girdle:
                continue
            u = min(1.0, (lat - DELTOID_BAND[0]) / (DELTOID_BAND[1] - DELTOID_BAND[0]))
            f = DELTOID_SHIFT * u * u * (3 - 2 * u)
            moved = 0.0
            for n, x in girdle.items():
                G[n].add([v.index], x * (1 - f), "REPLACE")
                moved += x * f
            G[f"upperarm_{s}"].add([v.index], wu + moved, "REPLACE")
            shifted += 1
    smoothed = _smooth_changed(result, before) if WEIGHT_SMOOTH else 0
    return {"scapula_tapered": tapered, "deltoid_shifted": shifted, "smoothed_vertices": smoothed}


def _weights(body):
    names = {g.index: g.name for g in body.vertex_groups}
    return [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in body.data.vertices]


def _smooth_changed(result, before):
    """Laplacian smoothing (WEIGHT_SMOOTH passes) of the full weight vectors over the vertices whose weights changed plus 3
    rings, renormalised: removes the sharp gradients the taper/shift leave (a 3 cm ramp creased the posterior deltoid)."""
    body = result["body"]
    after = _weights(body)
    adj = [set() for _ in body.data.vertices]
    for e in body.data.edges:
        a, b = e.vertices
        adj[a].add(b); adj[b].add(a)
    zone = {i for i, (x, y) in enumerate(zip(before, after)) if x != y}
    for _ in range(3):
        zone |= {j for i in zone for j in adj[i]}
    W = {i: dict(after[i]) for i in range(len(after))}
    for _ in range(WEIGHT_SMOOTH):
        new = {}
        for i in zone:
            acc = dict(W[i])
            for j in adj[i]:
                for n, x in W[j].items():
                    acc[n] = acc.get(n, 0.0) + x
            k = 1 + len(adj[i])
            new[i] = {n: x / k for n, x in acc.items()}
        W.update(new)
    G = body.vertex_groups
    for i in zone:
        if NO_LEAK:
            for n in [n for n in W[i] if n.startswith("upperarm_") and after[i].get(n, 0.0) <= 0.0]:
                del W[i][n]
        keep = sorted(((n, x) for n, x in W[i].items() if x > 1e-4), key=lambda kv: -kv[1])[:4]
        tot = sum(x for _, x in keep)
        for g in list(body.data.vertices[i].groups):
            G[g.group].remove([i])
        for n, x in keep:
            G[n].add([i], x / tot, "REPLACE")
    return len(zone)


def _thorax_ellipsoid(result):
    """Axis-aligned ellipsoid least-squares fitted to the rib/sternum guide vertices (the smooth gliding surface classic
    scapulothoracic models use; the individual rib tubes are not a surface - the blade's landmarks fall between them)."""
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for k, o in result["objects"].items():
        if k.startswith("rib_") or k == "sternum":
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            pts += [ev.matrix_world @ v.co for v in me.vertices]
            ev.to_mesh_clear()
    P = np.array([tuple(p) for p in pts])
    A = np.column_stack([P[:, 0] ** 2, P[:, 1] ** 2, P[:, 2] ** 2, P[:, 0], P[:, 1], P[:, 2]])
    k = np.linalg.lstsq(A, np.ones(len(P)), rcond=None)[0]
    centre = -k[3:] / (2 * k[:3])
    g = 1 + sum(k[i + 3] ** 2 / (4 * k[i]) for i in range(3))
    radii = np.sqrt(g / k[:3])
    return Vector(centre), Vector(radii)


def _dist(p):
    """Approximate signed distance from p to the thorax ellipsoid (+ = outside): radial scaling of the normalised radius."""
    c, r = _S["centre"], _S["radii"]
    q = p - c
    t = math.sqrt((q.x / r.x) ** 2 + (q.y / r.y) ** 2 + (q.z / r.z) ** 2)
    return (t - 1.0) * q.length / t if t > 1e-9 else -min(r)


def _clav_rot(s, a, b):
    """Extra clavicle rotation about the SC joint: a = protraction about world Z, b = elevation about the clavicle-normal."""
    cl = _S["clav_dir"][s]
    elev_axis = cl.cross(Vector((0, 0, 1))).normalized()
    return Matrix.Rotation(a, 3, Vector((0, 0, 1))) @ Matrix.Rotation(b, 3, elev_axis)


def apply_coupled_pose_r4(result, ht_elevation_deg):
    ext = _S.get("extend")                                     # review-only >160 deg / shrug hook (original_v1_press_extension)
    profile = _S["orig"](result, min(ht_elevation_deg, 160.0) if ext else ht_elevation_deg)   # clavicle + arm aim
    if ext:
        profile = ext(result, profile, ht_elevation_deg)
    rig = result["runtime"]
    pb = rig.pose.bones
    log = {}
    for s in ("r", "l"):
        pb[f"scapula_{s}"].matrix_basis.identity()
    bpy.context.view_layer.update()
    for s in ("r", "l"):
        cl = pb[f"clavicle_{s}"]
        sc_rest = rig.data.bones[f"scapula_{s}"].matrix_local.copy()
        R = isb.scapula_rotation(s, profile)                   # thorax-frame orientation change (3x3)
        ac_rest = _S["ac_rest"][s]
        head = cl.head.copy()
        tail0 = cl.tail.copy()
        P = isb._STATE["frames"][s]["points"]

        target = (profile["scapula_internal_rotation_deg"], profile["scapula_upward_rotation_deg"],
                  profile["scapula_posterior_tilt_deg"])
        wrap = _S.get("mode") == "wrap"
        y_axis = R @ isb._STATE["frames"][s]["axes"][1]           # blade's superior axis after the profile rotation

        def orient(x):
            if wrap:                                               # R4: free extra rotation about the superior axis
                return Matrix.Rotation(x[2], 3, y_axis) @ R
            return isb.scapula_rotation(s, profile, angles=(target[0] + math.degrees(x[2]), target[1] + math.degrees(x[3]),
                                                            target[2] + math.degrees(x[4])))

        def landmarks(x):
            ac = head + _clav_rot(s, x[0], x[1]) @ (tail0 - head)
            Ro = orient(x)
            return ac, {n: ac + Ro @ (P[n] - ac_rest) for n in ("TS", "AI")}

        def residual(x):
            _, L = landmarks(x)
            return [_dist(L["TS"]) - _S["d0"][s]["TS"], _dist(L["AI"]) - _S["d0"][s]["AI"]]
        import numpy as np
        lam = np.array(WRAP_PENALTY if wrap else CONTACT_PENALTY)
        nv = len(lam)
        x = np.zeros(nv)
        for _ in range(40):
            f = np.array(residual(x))
            J = np.zeros((2, nv))
            for j in range(nv):
                xx = x.copy(); xx[j] += 1e-3
                J[:, j] = (np.array(residual(xx)) - f) / 1e-3
            A = J.T @ J + np.diag(lam ** 2)
            g = -(J.T @ f) - lam ** 2 * x
            dx = np.linalg.solve(A, g)
            step = float(np.abs(dx).max())
            if step > math.radians(5):
                dx *= math.radians(5) / step
            x = x + dx
            if step < 1e-6:
                break
        x = [float(v) for v in x]
        res = residual(x)
        Rc = _clav_rot(s, x[0], x[1]).to_4x4()
        R = orient(x)
        cl.matrix = Matrix.Translation(head) @ Rc @ Matrix.Translation(-head) @ cl.matrix
        bpy.context.view_layer.update()
        ac = cl.tail.copy()
        pb[f"scapula_{s}"].matrix = Matrix.Translation(ac) @ R.to_4x4() @ Matrix.Translation(-ac_rest) @ sc_rest
        log[s] = {"clavicle_extra_protraction_deg": round(math.degrees(x[0]), 2),
                  "clavicle_extra_elevation_deg": round(math.degrees(x[1]), 2),
                  "mode": _S.get("mode"),
                  "scapula_extra_rotation_deg": round(math.degrees(x[2]), 2) if wrap else None,
                  "scapula_isb_deg": None if wrap else [round(target[0] + math.degrees(x[2]), 2),
                                                        round(target[1] + math.degrees(x[3]), 2),
                                                        round(target[2] + math.degrees(x[4]), 2)],
                  "scapula_isb_target_deg": [round(v, 2) for v in target],
                  "contact_residual_mm": [round(r * 1000, 2) for r in res]}
    bpy.context.view_layer.update()
    elevation, plane = math.radians(profile["ht_elevation_deg"]), math.radians(profile["plane_deg"])
    for sign, name in ((1.0, "upperarm_r"), (-1.0, "upperarm_l")):
        bone = pb[name]
        pivot = bone.head.copy()
        current = (bone.tail - bone.head).normalized()
        target = Vector((sign * math.sin(elevation) * math.cos(plane), -math.sin(elevation) * math.sin(plane),
                         -math.cos(elevation)))
        corr = current.rotation_difference(target).to_matrix().to_4x4()
        bone.matrix = Matrix.Translation(pivot) @ corr @ Matrix.Translation(-pivot) @ bone.matrix
    bpy.context.view_layer.update()
    _S["last"] = log
    return dict(profile, scapula_drive="R4: ISB thorax frame + scapulothoracic contact", r4_contact=log)


def install(result, contact=True, mode="isb"):
    """Wrap the coupled pose (idempotent).  Call after build_corrected_scene() and any lower_pivot(), rig at rest."""
    import build_functional_original_coupled_motion_blender as coupled
    if _S.get("installed"):
        return
    rig = result["runtime"]
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    isb.install(result)                                         # frames, AC rest; replaces apply_coupled_pose
    coupled.apply_coupled_pose = isb._STATE["orig"]             # undo the plain ISB wrap; R4 wraps the original
    centre, radii = _thorax_ellipsoid(result)
    _S.update(orig=isb._STATE["orig"], centre=centre, radii=radii, installed=True, mode=mode,
              ac_rest={s: rig.data.bones[f"clavicle_{s}"].tail_local.copy() for s in ("r", "l")},
              clav_dir={s: (rig.data.bones[f"clavicle_{s}"].tail_local - rig.data.bones[f"clavicle_{s}"].head_local).normalized()
                        for s in ("r", "l")})
    _S["d0"] = {s: {n: _dist(isb._STATE["frames"][s]["points"][n]) for n in ("TS", "AI")} for s in ("r", "l")}
    if contact:
        coupled.apply_coupled_pose = apply_coupled_pose_r4
    else:
        coupled.apply_coupled_pose = isb.apply_coupled_pose_isb
