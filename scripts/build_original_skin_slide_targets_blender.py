#!/usr/bin/env python3
"""Skin-slide lockout targets for ORIGINAL_v1 review candidate R24 (Claude, 15 Oct 2026; review only; bpy).

For each key pose of the press (KEYS_HT), starting from the candidate's posed surface P (all keys on):
  1. light Taubin smoothing of the shoulder region (TAUB passes; free within RR[0] of each shoulder joint, fixed beyond RR[1]);
  2. lump fairing: umbrella smoothing (LUMP passes) in a zone centred LUMP_OFF from each shoulder joint (behind and just
     below it), free within LUMP_R[0] and fading out to LUMP_R[1].  This flattens the ball behind the joint.  Taubin alone
     only removed small creases (measured at 10, 40 and 80 passes);
  3. surface-walking skin slide on that shape (original_v1_skin_slide.slide, SLIDE steps): skin moves from the squashed
     deltoid into the stretched armpit / side of the chest.
Measured at 172 deg on R18 (TAUB 10, LUMP 200, SLIDE 60): 0 self-intersecting pairs; collapse 0 -> 6; squashed < 0.6:
2,800 -> 2,891; stretched > 1.5: 1,137 -> 621; stretched > 2: 255 -> 45.  Writes OUT/targets.npz (+ .json) for the S7 bake
(build_original_review_candidate_r17_blender.py --bake) and renders the 172 deg current / slid surfaces.
R26 adds FAIR / POSTFAIR (thin-plate rebuild of zones before / after the slide; the slide re-folded the hook beside the
neck, measured) and DELT_BUMP (rounded deltoid cap); see docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R26_20261015.md.
  KEYS_HT=145,160,172 TAUB=10 LUMP=200 SLIDE=60 python3.13 build_original_skin_slide_targets_blender.py R18.blend OUTDIR
"""
import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
import original_v1_review_candidate_drives as drives
from mathutils import Vector
from mathutils.bvhtree import BVHTree
blend, out = sys.argv[-2], sys.argv[-1]
TAUB = int(os.environ.get("TAUB", 30)); SLIDE = int(os.environ.get("SLIDE", 200)); ETA = float(os.environ.get("ETA", 0.3))
RIN, ROUT = (float(x) for x in os.environ.get("RR", "0.14,0.19").split(","))
KEYS = tuple(float(x) for x in os.environ.get("KEYS_HT", "145,160,172").split(","))
bpy.ops.wm.open_mainfile(filepath=blend)
if os.environ.get("LOCKOUT_HT"):                         # R29: lower lockout elevation (arms in a wider V)
    bpy.context.scene["hgpt_press_lockout_ht"] = float(os.environ["LOCKOUT_HT"])
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as s4
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
V0, F = bench._evaluated(body); R = np.array([tuple(v) for v in V0]); Fa = np.array(F)
nv = len(R)
nbr = [[] for _ in range(nv)]
for f in F:
    for i in range(3):
        a, b = f[i], f[(i + 1) % 3]; nbr[a].append(b); nbr[b].append(a)
nbr = [np.array(sorted(set(n))) for n in nbr]
def areas(Y):
    return np.linalg.norm(np.cross(Y[Fa[:, 1]] - Y[Fa[:, 0]], Y[Fa[:, 2]] - Y[Fa[:, 0]]), axis=1) / 2
A0 = np.maximum(areas(R), 1e-12)
W = rig.matrix_world
def fair_fill(S, spec, wfree):
    for zone in [z for z in spec.split(";") if z]:
        o_, r_ = zone.split(":")
        off3 = np.array([float(x) for x in o_.split(",")]); rf = float(r_)
        for s_ in "rl":
            sg = 1.0 if s_ == "r" else -1.0
            gh = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head))
            c = gh + np.array([off3[0] * sg, off3[1], off3[2]])
            inner = np.where((np.linalg.norm(S - c, axis=1) < rf) & (wfree > 0))[0]
            if not len(inner):
                continue
            pos = -np.ones(nv, int); pos[inner] = np.arange(len(inner))
            n_ = len(inner)
            ring = np.unique(np.concatenate([nbr[i] for i in inner])); ring = ring[pos[ring] < 0]
            rows = np.concatenate([inner, ring])         # bi-Laplacian: L applied at inner + first outside ring
            Lr = np.zeros((len(rows), nv))
            for k_, i in enumerate(rows):
                Lr[k_, i] = -1.0; Lr[k_, nbr[i]] += 1.0 / len(nbr[i])
            A_ = Lr[:, inner]; Bk = np.delete(np.arange(nv), inner)
            rhs = -(Lr[:, Bk] @ S[Bk])
            sol, *_ = np.linalg.lstsq(A_, rhs, rcond=None)
            S[inner] = sol
    return S
# R26b (owner, on R26: "check the shape of the arm in the upright position"): the same upper-arm vertices sit ~5 mm closer
# to the arm's axis at lockout than at rest over the middle third (S5 bake mostly, S7 partly; measured with the keys toggled),
# so the arm narrows between the deltoid cap and the elbow.  ARM_RESTORE="gain:f0,f1,f2,f3" moves those vertices radially
# back towards their rest distance from the shoulder-elbow axis, in a trapezoid window along the arm (fractions of the
# upper-arm length), weighted by their arm skinning weight.  Applied last, after the slide.
ARM_RESTORE = os.environ.get("ARM_RESTORE", "")
arm_rest = {}
arm_w = {}
arm_cyl = {}
if os.environ.get("ELBOW_FAIR") and os.environ.get("ELBOW_MODE") == "rest":
    # rest pose: each arm vertex's position along the arm (cm from the elbow), angle round it and radius from the
    # shoulder-wrist line - the target shape is a smooth fit of the RESTING arm (a steady taper, measured)
    bench._reset(rig); drives.drive(rig, body)
    Vr2, _ = bench._evaluated(body); Pr2 = np.array([tuple(v) for v in Vr2])
    for s_ in "rl":
        gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)); el_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
        wr_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].tail))
        ax0 = (wr_ - gh_) / np.linalg.norm(wr_ - gh_)
        rel = Pr2 - gh_; t0 = rel @ ax0; perp0 = rel - t0[:, None] * ax0
        ref = np.array([0.0, -1.0, 0.0]) - (-ax0[1]) * ax0; ref /= np.linalg.norm(ref); ref2 = np.cross(ax0, ref)
        arm_cyl[s_] = ((t0 - (el_ - gh_) @ ax0) * 100.0, np.arctan2(perp0 @ ref2, perp0 @ ref), np.linalg.norm(perp0, axis=1))
if os.environ.get("ELBOW_FAIR"):
    gi2 = {g.index: g.name for g in body.vertex_groups}
    for s_ in "rl":
        wa = np.zeros(nv)
        for v in body.data.vertices:
            for e in v.groups:
                n_ = gi2[e.group]
                if n_.endswith(f"_{s_}") and n_.startswith(("upperarm", "forearm", "lowerarm")):
                    wa[v.index] += e.weight
        arm_w[s_] = wa
if ARM_RESTORE or os.environ.get("ARM_UNS5") or os.environ.get("ARM_INFLATE"):
    gi_ = {g.index: g.name for g in body.vertex_groups}
    bench._reset(rig); drives.drive(rig, body)
    Vr_, _ = bench._evaluated(body); Pr_ = np.array([tuple(v) for v in Vr_])
    for s_ in "rl":
        wa = np.zeros(nv)
        for v in body.data.vertices:
            for e in v.groups:
                if gi_[e.group].startswith((f"upperarm_{s_}", f"forearm_{s_}", "upperarm_twist")) and gi_[e.group].endswith(f"_{s_}"):
                    wa[v.index] += e.weight
        gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)); el_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
        L_ = np.linalg.norm(el_ - gh_); ax0 = (el_ - gh_) / L_
        d_ = (Pr_ - gh_) @ ax0
        arm_rest[s_] = (np.clip(wa, 0, 1), d_ / L_, np.linalg.norm((Pr_ - gh_) - d_[:, None] * ax0, axis=1))
def arm_restore(X):
    g_, w_ = ARM_RESTORE.split(":"); gain = float(g_); a0, a1, a2, a3 = (float(x) for x in w_.split(","))
    X = X.copy()
    for s_ in "rl":
        wa, fr, r0 = arm_rest[s_]
        win = np.clip((fr - a0) / (a1 - a0), 0, 1) * np.clip((a3 - fr) / (a3 - a2), 0, 1)
        win = win * win * (3 - 2 * win)
        k = gain * win * wa
        sel = np.where(k > 1e-4)[0]
        gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)); el_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
        ax = (el_ - gh_) / np.linalg.norm(el_ - gh_)
        rel = X - gh_; d_ = rel @ ax; perp = rel - d_[:, None] * ax; r = np.linalg.norm(perp, axis=1)
        dr = np.zeros(nv); dr[sel] = k[sel] * (r0[sel] - r[sel])
        # the per-vertex radius change is noisy (vertices twist round the axis between rest and lockout): smooth the scalar
        # field over the mesh first, or the arm ripples (measured on the first try)
        zone = np.where(k > 1e-4)[0]
        for _ in range(int(os.environ.get("ARM_SMOOTH", 40))):
            dr[zone] = 0.5 * dr[zone] + 0.5 * np.array([dr[nbr[i]].mean() for i in zone])
        X[zone] += (dr[zone] / np.maximum(r[zone], 1e-6))[:, None] * perp[zone]
    return X
out_t = {}; logs = {}
for ht in KEYS:
    bench._reset(rig); s4.press_pose(res, ht); drives.drive(rig, body)
    V, _ = bench._evaluated(body); P = np.array([tuple(v) for v in V])
    P_noS5 = None
    if os.environ.get("ARM_UNS5"):                  # R26b: the same pose with the S5 bake keys off (they thin the mid upper arm)
        kept = {kb.name: kb.value for kb in body.data.shape_keys.key_blocks[1:] if kb.name.startswith("HGPT_S5_BAKE_")}
        for n_ in kept: body.data.shape_keys.key_blocks[n_].value = 0.0
        V5, _ = bench._evaluated(body); P_noS5 = np.array([tuple(v) for v in V5])
        for n_, v_ in kept.items(): body.data.shape_keys.key_blocks[n_].value = v_
    X = P.copy()
    wfree = np.zeros(nv)
    for s in "rl":
        gh = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s}"].head))
        dist = np.linalg.norm(P - gh, axis=1)
        wfree = np.maximum(wfree, 1 - np.clip((dist - RIN) / (ROUT - RIN), 0, 1))
    idx = np.where(wfree > 0)[0]
    # 1. shape: Taubin smoothing of the region (boundary held by wfree)
    S = P.copy()
    if os.environ.get("ARM_RIGID"):
        # R31b (owner: "there looks like there is a join here but there isn't.  The only joint will be the elbow.  That bone
        # should continue on into the shoulder"): the upper half of the upper arm is bound mostly to the cap helper, the
        # spine and the pec / lat helpers, so it lags 8-10 cm behind the humerus and the arm bends a third of the way down
        # (measured).  Re-binding it broke every benchmark (R31: walk / grip / push-up crossing pairs), so instead, at this
        # key, arm skin is moved to where it would be if it moved rigidly with the humerus: full from T1 m below the
        # shoulder pivot along the rest arm axis, blended out by T0 m; within RADIUS of the arm axis; not the torso beside the
        # arm (medial of the axis with the skin facing outwards)
        g_, t_ = os.environ["ARM_RIGID"].split(":"); gain_r = float(g_); T0r, T1r = (float(x) for x in t_.split(","))
        for kv in [x for x in os.environ.get("RIGID_KEY_GAIN", "").split(",") if x]:
            if abs(float(kv.split(":")[0]) - ht) < 0.5:
                gain_r *= float(kv.split(":")[1])
        if "rest_normals" not in arm_rest:
            Nf_ = np.cross(R[Fa[:, 1]] - R[Fa[:, 0]], R[Fa[:, 2]] - R[Fa[:, 0]]); Nv_ = np.zeros_like(R)
            for c_ in range(3):
                np.add.at(Nv_, Fa[:, c_], Nf_)
            arm_rest["rest_normals"] = Nv_ / np.maximum(np.linalg.norm(Nv_, axis=1)[:, None], 1e-15)
        Nv_ = arm_rest["rest_normals"]
        for s_ in "rl":
            sg = 1.0 if s_ == "r" else -1.0
            b_ = rig.data.bones[f"upperarm_{s_}"]; pb_ = rig.pose.bones[f"upperarm_{s_}"]
            h0 = np.array(tuple(W @ b_.head_local)); ax0 = np.array(tuple(W @ b_.tail_local)) - h0; Lb = np.linalg.norm(ax0); ax0 /= Lb
            lat = np.array([sg, 0.0, 0.0]) - (sg * ax0[0]) * ax0; lat /= np.linalg.norm(lat)
            rel = R - h0; tt = rel @ ax0; perp = rel - tt[:, None] * ax0; rr_ = np.linalg.norm(perp, axis=1)
            dirn = perp / np.maximum(rr_[:, None], 1e-9)
            torso = ((dirn @ lat) < -0.3) & ((Nv_ @ lat) > 0.2)
            f_ = np.clip((tt - T0r) / (T1r - T0r), 0, 1); f_ = f_ * f_ * (3 - 2 * f_)
            f_ *= ((rr_ < float(os.environ.get("RIGID_RADIUS", 0.085))) & ~torso & (tt < Lb * 0.95)).astype(float)
            fe = np.clip((Lb * 0.95 - tt) / (Lb * 0.15), 0, 1)        # fade out before the elbow (the forearm bends there)
            f_ *= fe
            M = np.array(W @ pb_.matrix @ b_.matrix_local.inverted() @ W.inverted())
            rigid = (np.c_[R, np.ones(len(R))] @ M.T)[:, :3]
            S += (gain_r * f_)[:, None] * (rigid - S)

    for k in range(TAUB):
        for lam in (0.5, -0.53):
            L = np.array([S[nbr[i]].mean(0) - S[i] for i in idx])
            S[idx] += lam * L * wfree[idx][:, None]
    # 1b. lump fairing: plain umbrella smoothing (membrane) in a zone centred behind / below each shoulder joint
    LUMP = int(os.environ.get("LUMP", 0))
    if LUMP:
        off = np.array([float(x) for x in os.environ.get("LUMP_OFF", "0,0.04,-0.02").split(",")])
        r0, r1 = (float(x) for x in os.environ.get("LUMP_R", "0.06,0.10").split(","))
        wl = np.zeros(nv)
        for s_ in "rl":
            sg = 1.0 if s_ == "r" else -1.0
            gh = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head))
            c = gh + np.array([off[0] * sg, off[1], off[2]])
            dd = np.linalg.norm(P - c, axis=1)
            wl = np.maximum(wl, 1 - np.clip((dd - r0) / (r1 - r0), 0, 1))
        zl = np.where(wl > 0)[0]
        for k in range(LUMP):
            L = np.array([S[nbr[i]].mean(0) - S[i] for i in zl])
            S[zl] += 0.5 * L * wl[zl][:, None]
    # 1c. extra zones (R25), each "passes:x,y,z:r0,r1" (offsets from the posed shoulder joint, x outward), separated by ";":
    #     the corner on the back of the upper arm ~8 cm up the arm (where full-follow arm skin meets the half-follow
    #     deltoid skin) and the pinched pocket between the arm and the neck - located on R24 by concavity and marked
    GUARD_ZONES = os.environ.get("GUARD_ZONES", "1") == "1"
    for zone in [z for z in os.environ.get("ZONES", "").split(";") if z]:
        np_, o_, r_ = zone.split(":")
        LUMP2 = int(np_)
        off2 = np.array([float(x) for x in o_.split(",")])
        q0, q1 = (float(x) for x in r_.split(","))
        w2 = np.zeros(nv)
        for s_ in "rl":
            sg = 1.0 if s_ == "r" else -1.0
            gh = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head))
            c = gh + np.array([off2[0] * sg, off2[1], off2[2]])
            dd = np.linalg.norm(P - c, axis=1)
            x_ = np.clip((dd - q0) / (q1 - q0), 0, 1)
            w2 = np.maximum(w2, 1 - x_ * x_ * (3 - 2 * x_))              # smoothstep fade (a linear fade left a crease ring)
        z2 = np.where(w2 > 0)[0]
        normal_only = LUMP2 < 0                     # negative passes: lift concave points along their normal only
        for k in range(abs(LUMP2)):
            L = np.array([S[nbr[i]].mean(0) - S[i] for i in z2])
            if normal_only:
                Fn = np.cross(S[Fa[:, 1]] - S[Fa[:, 0]], S[Fa[:, 2]] - S[Fa[:, 0]])
                vn_ = np.zeros_like(S)
                for c_ in range(3):
                    np.add.at(vn_, Fa[:, c_], Fn)
                vn_ = vn_[z2] / np.maximum(np.linalg.norm(vn_[z2], axis=1)[:, None], 1e-15)
                h_ = (L * vn_).sum(1)
                L = vn_ * np.maximum(h_, 0.0)[:, None]          # only where the centroid lies outward (a valley/pocket)
            prop = S.copy()
            prop[z2] += 0.5 * L * w2[z2][:, None]
            if GUARD_ZONES:                         # R25: no step may crush a triangle below 25 % of its rest area
                ar_ = np.linalg.norm(np.cross(prop[Fa[:, 1]] - prop[Fa[:, 0]], prop[Fa[:, 2]] - prop[Fa[:, 0]]), axis=1) / 2
                badf = np.where(ar_ / A0 < 0.25)[0]
                if len(badf):
                    bv = np.unique(Fa[badf].reshape(-1))
                    prop[bv] = S[bv]
            S[:] = prop
    # 1c''. fair fill (R26, owner item 1: the hook / curl beside the neck at lockout survived smoothing and normal lift):
    #      each zone "x,y,z:r" (offset from the posed shoulder joint, x outward) is rebuilt as a thin-plate (bi-Laplacian)
    #      surface from the ring of vertices just outside it, so no fold can remain inside; ";" separates zones
    S = fair_fill(S, os.environ.get("FAIR", ""), wfree)
    # 1c'. deltoid cap (R26, owner: the arm root had become thin and flat - "do both 1 and 2"): a smooth outward swell over the
    #      outer / back of the arm root, an ellipsoid longer along the (vertical, at lockout) arm than across it, applied
    #      along the vertex normal only where the surface faces away from the arm's axis (not into the armpit)
    if os.environ.get("DELT_BUMP"):
        a_, c_, ax_ = os.environ["DELT_BUMP"].split(":")
        amp = float(a_); cofs = np.array([float(x) for x in c_.split(",")]); ax_up, ax_side = (float(x) for x in ax_.split(","))
        Fn = np.cross(S[Fa[:, 1]] - S[Fa[:, 0]], S[Fa[:, 2]] - S[Fa[:, 0]])
        vn_ = np.zeros_like(S)
        for c2 in range(3):
            np.add.at(vn_, Fa[:, c2], Fn)
        vn_ /= np.maximum(np.linalg.norm(vn_, axis=1)[:, None], 1e-15)
        for s_ in "rl":
            sg = 1.0 if s_ == "r" else -1.0
            pb_ = rig.pose.bones[f"upperarm_{s_}"]
            gh = np.array(tuple(W @ pb_.head)); axis = np.array(tuple((W @ pb_.tail) - (W @ pb_.head))); axis /= np.linalg.norm(axis)
            c = gh + np.array([cofs[0] * sg, cofs[1], cofs[2]])
            rel_ = S - c
            along = rel_ @ axis
            perp = rel_ - along[:, None] * axis
            q = np.sqrt((along / ax_up) ** 2 + (np.linalg.norm(perp, axis=1) / ax_side) ** 2)
            x_ = np.clip(q, 0, 1)
            fall = 1 - x_ * x_ * (3 - 2 * x_)
            radial = (S - gh) - ((S - gh) @ axis)[:, None] * axis
            radial /= np.maximum(np.linalg.norm(radial, axis=1)[:, None], 1e-9)
            facing = np.clip((vn_ * radial).sum(1), 0, 1)              # surface facing away from the arm's axis
            outer = np.clip((radial * np.array([sg, 0.6, 0.0])).sum(1) + 0.3, 0, 1)   # lateral / back faces
            S += (amp * fall * facing * outer * (wfree > 0))[:, None] * vn_
    # 1d. a final light Taubin blend over the whole region, so the zone edges leave no seam
    for k in range(int(os.environ.get("BLEND", 0))):
        for lam in (0.5, -0.53):
            L = np.array([S[nbr[i]].mean(0) - S[i] for i in idx])
            S[idx] += lam * L * wfree[idx][:, None]
    # 1e. untangle (R25): crushed triangles left by the zone smoothing are spread back out IN the surface (each vertex of a
    #     crushed face and its ring moves towards its neighbours' centroid, projected onto its tangent plane), so the bake's
    #     guard has nothing to cut back - its local cut-backs left spikes / fins at the arm root (measured on R25 v1)
    for k in range(int(os.environ.get("UNTANGLE", 0))):
        ar_ = np.linalg.norm(np.cross(S[Fa[:, 1]] - S[Fa[:, 0]], S[Fa[:, 2]] - S[Fa[:, 0]]), axis=1) / 2
        badf = np.where((ar_ / A0 < 0.25) & (wfree[Fa[:, 0]] > 0))[0]
        if not len(badf):
            break
        bv = set(Fa[badf].reshape(-1))
        bv |= {j for i in list(bv) for j in nbr[i]}
        bv = np.array([i for i in bv if wfree[i] > 0])
        Fn = np.cross(S[Fa[:, 1]] - S[Fa[:, 0]], S[Fa[:, 2]] - S[Fa[:, 0]])
        vn_ = np.zeros_like(S)
        for c_ in range(3):
            np.add.at(vn_, Fa[:, c_], Fn)
        vn_ = vn_[bv] / np.maximum(np.linalg.norm(vn_[bv], axis=1)[:, None], 1e-15)
        L = np.array([S[nbr[i]].mean(0) - S[i] for i in bv])
        L -= (L * vn_).sum(1)[:, None] * vn_
        S[bv] += 0.5 * L
    import original_v1_skin_slide as walkslide
    lg = []
    X = walkslide.slide(S, Fa, A0, idx, wfree, iters=SLIDE, eta=ETA, log=lg, crush_w=float(os.environ.get("CRUSH_W", 0))) if SLIDE > 0 else S.copy()
    print("ENERGY", lg, flush=True)
    # 3b. post-slide fair fill (R26): the slide re-folded the zones rebuilt in 1c'' (measured), so the same rebuild is
    #     repeated on the slid surface
    if os.environ.get("POSTFAIR"):
        X = fair_fill(X, os.environ["POSTFAIR"], wfree)
    if ARM_RESTORE:
        X = arm_restore(X)
    if os.environ.get("ARM_INFLATE"):
        # R26b: a smooth, even radial push (metres) over the middle of the upper arm, trapezoid window along the arm,
        # weighted by arm skinning: restores the thickness the S5 bake takes off without re-opening the crumples it smooths
        g_, w_ = os.environ["ARM_INFLATE"].split(":"); amp = float(g_); a0, a1, a2, a3 = (float(x) for x in w_.split(","))
        for s_ in "rl":
            wa, fr, _r0 = arm_rest[s_]
            win = np.clip((fr - a0) / (a1 - a0), 0, 1) * np.clip((a3 - fr) / (a3 - a2), 0, 1)
            win = win * win * (3 - 2 * win)
            k = win * wa
            for _ in range(20):                     # smooth the weight field so its edges leave no step
                k = 0.5 * k + 0.5 * np.array([k[n].mean() if len(n) else 0.0 for n in nbr])
            gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)); el_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
            ax = (el_ - gh_) / np.linalg.norm(el_ - gh_)
            rel = X - gh_; perp = rel - (rel @ ax)[:, None] * ax
            X = X + (amp * k / np.maximum(np.linalg.norm(perp, axis=1), 1e-6))[:, None] * perp
    if os.environ.get("ELBOW_FAIR"):
        # R27 (owner: "the bicep should flow into the forearm without a big dip between"): with the arm overhead the skinned
        # arm bulges at the lower biceps and narrows just past the elbow (present in the raw skinning, measured).  In
        # cylindrical coordinates about the shoulder-wrist line, the radius profile of each of 16 sectors round the arm is
        # smoothed ALONG the arm (Gaussian, sigma cm) inside a window (fractions of the shoulder-wrist length); the radius
        # change is then smoothed over the mesh and applied radially, so the outline flows through the elbow.  The window is
        # in cm from the elbow along the arm (negative towards the shoulder).  Measured on R27 (front view at lockout): the
        # inner side of the lower upper arm juts ~4 cm over ~8 cm, then cuts in to the elbow (widths 12.7 / 8.7 / 9.7 cm)
        sg_, w_, g_ = os.environ["ELBOW_FAIR"].split(":"); sig = float(sg_) / 100; gain = float(g_)
        # per-key strength, "ht:gain,..." (R27: the full column fit at 145 deg, arm not yet overhead, crossed the skin -
        # 196 pairs measured)
        for kv in [x for x in os.environ.get("ARM_KEY_GAIN", "").split(",") if x]:
            if abs(float(kv.split(":")[0]) - ht) < 0.5:
                gain *= float(kv.split(":")[1])
        a0, a1, a2, a3 = (float(x) for x in w_.split(","))
        for s_ in ("rl" if gain > 0 else ""):            # gain 0 (per-key): the arm column is skipped at this key
            wa = arm_w[s_]
            gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)); wr_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].tail))
            Lw = np.linalg.norm(wr_ - gh_); ax = (wr_ - gh_) / Lw
            el_k = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
            flex_k = np.degrees(np.arccos(np.clip(((el_k - gh_) / np.linalg.norm(el_k - gh_)) @ ((wr_ - el_k) / np.linalg.norm(wr_ - el_k)), -1, 1)))
            upper_mode = bool(os.environ.get("TUBE_UPPER")) and flex_k > float(os.environ.get("TUBE_UPPER_DEG", 8))
            if upper_mode:
                # R33 (owner, on R31 at 132 / 145 deg: "the arms as it's raising up should be in a straight line", the bend
                # at the elbow "too sharp"): with the elbow still bent (30 deg at the 145 key) a column from the WRIST to the
                # root cuts across the elbow and kinks the upper arm (measured: the kink is absent with S7 off).  At bent
                # keys the column is the upper arm alone: its axis is shoulder -> elbow, the window and the far anchor end
                # just above the elbow, and only upper-arm skin (rest position above the elbow) is moved
                ax = (el_k - gh_) / np.linalg.norm(el_k - gh_)
                a0, a1, a2, a3 = (float(x) for x in os.environ["TUBE_UPPER"].split(","))
                if "upper_mask" not in arm_rest:
                    arm_rest["upper_mask"] = {}
                    for q_ in "rl":
                        bh = np.array(tuple(W @ rig.data.bones[f"upperarm_{q_}"].head_local)); be = np.array(tuple(W @ rig.data.bones[f"forearm_{q_}"].head_local))
                        au_ = (be - bh) / np.linalg.norm(be - bh)
                        arm_rest["upper_mask"][q_] = ((R - be) @ au_) < -0.01
                wa = wa * arm_rest["upper_mask"][s_]
                print("TUBE_UPPER", ht, s_, "elbow flexion %.1f deg" % flex_k, flush=True)
            rel = X - gh_; t_ = rel @ ax; perp = rel - t_[:, None] * ax; r = np.linalg.norm(perp, axis=1)
            el2 = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
            fr = (t_ - (el2 - gh_) @ ax) * 100.0       # cm along the arm from the elbow (negative towards the shoulder)
            ref = np.array([0.0, 1.0, 0.0]) - ax[1] * ax; ref /= np.linalg.norm(ref); ref2 = np.cross(ax, ref)
            th = np.arctan2(perp @ ref2, perp @ ref)
            win = np.clip((fr - a0) / (a1 - a0), 0, 1) * np.clip((a3 - fr) / (a3 - a2), 0, 1); win = win * win * (3 - 2 * win)
            cand = np.where((wa > float(os.environ.get("ARM_WMIN", 0.3))) & (fr > a0 - 3) & (fr < a3 + 3))[0]
            NS, BW = 16, 0.01
            sec = ((th[cand] + np.pi) / (2 * np.pi) * NS).astype(int) % NS
            b = np.floor(t_[cand] / BW).astype(int); b0 = b.min(); b -= b0; NB = b.max() + 1
            sm = np.zeros((NS, NB)); cnt = np.zeros((NS, NB))
            np.add.at(sm, (sec, b), r[cand]); np.add.at(cnt, (sec, b), 1)
            prof = np.where(cnt > 0, sm / np.maximum(cnt, 1), 0)
            xs = np.arange(NB) * BW
            G = np.exp(-0.5 * ((xs[:, None] - xs[None, :]) / sig) ** 2)
            fair = np.zeros_like(prof)
            for k_ in range(NS):
                w8 = (cnt[k_] > 0).astype(float)
                fair[k_] = (G @ (prof[k_] * w8)) / np.maximum(G @ w8, 1e-9)
                if os.environ.get("ELBOW_MODE", "hull") == "poly":
                    # owner (on R26/R27 trials, drawing the outline): the arm should be one smooth column from the forearm
                    # through the upper arm into the back.  Each sector's radius profile over the whole window is replaced
                    # by a low-degree polynomial fit (ARM_POLY_DEG, default 3): no bulb at the elbow, no jut at the biceps
                    deg = int(os.environ.get("ARM_POLY_DEG", 3))
                    if w8.sum() > deg + 2:
                        c_ = np.polyfit(xs[w8 > 0], prof[k_][w8 > 0], deg)
                        fair[k_] = np.polyval(c_, xs)
                    continue
                if os.environ.get("ELBOW_MODE", "hull") in ("hull", "both"):
                    # fill-only: raise the profile to its upper hull (dips filled up to the line between the biceps and the
                    # forearm); bulges kept.  Gaussian-faired first so single noisy bins do not set the hull
                    xs_ = xs[w8 > 0]; ys_ = fair[k_][w8 > 0]
                    hull = []
                    for pt in zip(xs_, ys_):
                        while len(hull) >= 2 and (hull[-1][0] - hull[-2][0]) * (pt[1] - hull[-2][1]) - (hull[-1][1] - hull[-2][1]) * (pt[0] - hull[-2][0]) >= 0:
                            hull.pop()
                        hull.append(pt)
                    hx, hy = zip(*hull)
                    hl = np.interp(xs, hx, hy)
                    # hull: fill only (bulges kept); both: the hull of the Gaussian-faired profile (the biceps peak is
                    # lowered to its faired height as well as the crease filled)
                    fair[k_] = np.maximum(hl, prof[k_]) if os.environ.get("ELBOW_MODE", "hull") == "hull" else hl
            dr = np.zeros(nv)
            dr[cand] = (fair[sec, b] - prof[sec, b]) * gain * win[cand] * np.clip(wa[cand], 0, 1)
            if os.environ.get("ELBOW_MODE") == "tube":
                # owner reference (dumbbell press from behind): each arm is a straight, steadily widening column from the
                # wrist into the shoulder.  The target is a tube about a straight centre line whose elliptical
                # cross-section (across / front-back half-widths) and centre vary LINEARLY between two anchor slices of
                # this body: the forearm near the wrist (TUBE_A cm from the elbow) and the arm root under the deltoid
                # (TUBE_B); every arm vertex in the window is moved onto it along its direction from the centre line
                ta_ = [float(x) for x in os.environ.get("TUBE_UPPER_A" if upper_mode else "TUBE_A", "-9,-5" if upper_mode else "14,20").split(",")]
                tb_ = [float(x) for x in os.environ.get("TUBE_B", "-25,-21").split(",")]
                u_ = perp @ ref2; v_ = perp @ ref                       # across (lateral) / front-back
                def anchor(lo, hi):
                    # the four edges of the slice (outer / inner / back / front), 95th percentile, measured from the arm's
                    # bone line (a single centre leaned the tube outwards: the deltoid pulls the root slice's centre out)
                    m_ = np.where((wa > 0.3) & (fr >= lo) & (fr < hi))[0]
                    return ((lo + hi) / 2, np.percentile(u_[m_], 95), -np.percentile(u_[m_], 5),
                            np.percentile(v_[m_], 95), -np.percentile(v_[m_], 5))
                A_, B_ = anchor(*ta_), anchor(*tb_)
                # R28: widen the column's root end (owner reference: the upper arm is thicker near the shoulder than R27's)
                rs_ = float(os.environ.get("TUBE_ROOT_SCALE", 1.0))
                B_ = (B_[0],) + tuple(e * rs_ for e in B_[1:])
                lam = np.clip((fr[cand] - B_[0]) / (A_[0] - B_[0]), -0.2, 1.2)
                edge = [B_[q] + lam * (A_[q] - B_[q]) for q in range(1, 5)]   # straight lines between the anchors
                for _it in range(int(os.environ.get("TUBE_ITERS", 1))):   # repeat: the smoothed move falls short of the lines
                    rel_ = X - gh_; perp_ = rel_ - (rel_ @ ax)[:, None] * ax; u_ = perp_ @ ref2; v_ = perp_ @ ref
                    du = u_[cand]; dv = v_[cand]; rr = np.maximum(np.hypot(du, dv), 1e-6)
                    cs, sn = du / rr, dv / rr
                    au = np.where(cs > 0, edge[0], edge[1]); av = np.where(sn > 0, edge[2], edge[3])
                    rt = 1.0 / np.sqrt((cs / au) ** 2 + (sn / av) ** 2)
                    k3 = gain * win[cand] * np.clip(wa[cand] / float(os.environ.get("ARM_WFULL", 0.5)), 0, 1)
                    Dv = np.zeros((nv, 3))
                    # radial move onto the tube about the straight centre line (also pulls slices the biceps jut had pushed
                    # off that line back onto it)
                    mv_ = rt - rr
                    if os.environ.get("TUBE_FILLROOT"):
                        # near the arm root only fill (the root is pinched); squeezing the deltoid edge onto the line
                        # crumpled the skin into a knot there (measured).  Full fill-only below f0, blended out by f1 cm
                        f0_, f1_ = (float(x) for x in os.environ["TUBE_FILLROOT"].split(","))
                        bl = np.clip((fr[cand] - f0_) / (f1_ - f0_), 0, 1)
                        mv_ = np.where(mv_ < 0, mv_ * bl, mv_)
                    Dv[cand] = (k3 * mv_)[:, None] * (cs[:, None] * ref2 + sn[:, None] * ref)
                    zone = np.unique(np.concatenate([cand] + [nbr[i] for i in cand]))
                    for _ in range(int(os.environ.get("ELBOW_SMOOTH", 10))):
                        Dv[zone] = 0.5 * Dv[zone] + 0.5 * np.array([Dv[nbr[i]].mean(0) for i in zone])
                    X = X + Dv
                # squeezing the biceps jut onto the line crumples its skin (measured on the first try): Taubin-smooth the
                # arm zone afterwards, weighted the same way, so the column is smooth as well as straight
                kz = np.zeros(nv); kz[cand] = k3
                for _ in range(20):
                    kz[zone] = 0.5 * kz[zone] + 0.5 * np.array([kz[nbr[i]].mean() for i in zone])
                for _ in range(int(os.environ.get("TUBE_RELAX", 0))):
                    for lam_ in (0.5, -0.53):
                        L_ = np.array([X[nbr[i]].mean(0) - X[i] for i in zone])
                        X[zone] += lam_ * L_ * kz[zone][:, None]
                if os.environ.get("ELBOW_DEBUG"):
                    rel2 = X - gh_; t2 = rel2 @ ax; p2 = rel2 - t2[:, None] * ax
                    u2 = p2 @ ref2; v2 = p2 @ ref
                    for lo in range(-27, 22, 3):
                        mm = (fr[cand] >= lo) & (fr[cand] < lo + 3)
                        if mm.sum():
                            ii = cand[mm]
                            print("TUBEDBG %s te %+3d n %3d  before u[%5.1f,%5.1f] v[%5.1f,%5.1f]  after u[%5.1f,%5.1f] v[%5.1f,%5.1f]  tube au %.1f av %.1f  k %.2f" % (s_, lo, mm.sum(), u_[ii].min()*100, u_[ii].max()*100, v_[ii].min()*100, v_[ii].max()*100, u2[ii].min()*100, u2[ii].max()*100, v2[ii].min()*100, v2[ii].max()*100, au[mm].mean()*100, av[mm].mean()*100, k3[mm].mean()))
                    print("TUBEDBG", s_, "anchor wrist (te, inner, outer, back, front)", np.round(np.array(A_) * [1, 100, 100, 100, 100], 1), "root", np.round(np.array(B_) * [1, 100, 100, 100, 100], 1))
                continue
            if os.environ.get("ELBOW_MODE") == "rest":
                # every arm vertex goes back to the radius a smooth fit of the RESTING arm gives it (cubic along the arm x
                # Fourier round it, fitted on rest coordinates): raising the arm pinched the upper arm 6-9 cm below the
                # shoulder (rest 5.8 cm -> 4.4 cm) and left the biceps as a bulb (owner: "why is it all bumpy")
                t0, th0, r0 = arm_cyl[s_]
                deg = int(os.environ.get("ARM_POLY_DEG", 3)); K = int(os.environ.get("ARM_FOURIER", 3))
                def design(tv, thv):
                    tt = tv / 30.0; cols = []
                    for i_ in range(deg + 1):
                        cols.append(tt ** i_)
                        for k2 in range(1, K + 1):
                            cols += [tt ** i_ * np.cos(k2 * thv), tt ** i_ * np.sin(k2 * thv)]
                    return np.stack(cols, 1)
                fitset = np.where((wa > 0.5) & (t0 > a0 - 3) & (t0 < a3 + 3))[0]
                coef, *_ = np.linalg.lstsq(design(t0[fitset], th0[fitset]), r0[fitset], rcond=None)
                rt = design(t0[cand], th0[cand]) @ coef * float(os.environ.get("ARM_SCALE", 1.0))
                dr[cand] = (rt - r[cand]) * gain * win[cand] * np.clip(wa[cand] / float(os.environ.get("ARM_WFULL", 0.5)), 0, 1)
            if os.environ.get("ELBOW_MODE") == "surf":
                # one smooth surface for the whole arm: r(t, theta) = sum of t^i x (1, cos k theta, sin k theta), i <= deg,
                # k <= K, least-squares over the arm vertices in the window; every vertex is moved onto it (its own radius,
                # not a bin mean), so the small bumps go as well as the elbow bulb and the biceps jut
                deg = int(os.environ.get("ARM_POLY_DEG", 3)); K = int(os.environ.get("ARM_FOURIER", 3))
                tt = fr[cand] / 30.0; thc = th[cand]
                cols = []
                for i_ in range(deg + 1):
                    cols.append(tt ** i_)
                    for k2 in range(1, K + 1):
                        cols += [tt ** i_ * np.cos(k2 * thc), tt ** i_ * np.sin(k2 * thc)]
                Aq = np.stack(cols, 1)
                wfit = (win[cand] > 0.05).astype(float) + 0.05
                coef, *_ = np.linalg.lstsq(Aq * wfit[:, None], r[cand] * wfit, rcond=None)
                # full strength wherever the skin is at least half arm (near the shoulder the skin is shared with the
                # clavicle / cap bones, and scaling by the raw weight left the arm narrow there - measured)
                dr[cand] = (Aq @ coef - r[cand]) * gain * win[cand] * np.clip(wa[cand] / float(os.environ.get("ARM_WFULL", 0.5)), 0, 1)
                if os.environ.get("ELBOW_DEBUG"):
                    fit_ = Aq @ coef
                    for lo in range(-30, 24, 3):
                        mm = (fr[cand] >= lo) & (fr[cand] < lo + 3)
                        if mm.sum(): print("SURFDBG %s te %+3d n %3d  r_mean %.2f fit_mean %.2f  dr_mean %.2f  win %.2f  wscale %.2f" % (s_, lo, mm.sum(), r[cand][mm].mean() * 100, fit_[mm].mean() * 100, dr[cand][mm].mean() * 100, win[cand][mm].mean(), np.clip(wa[cand][mm] / 0.5, 0, 1).mean()))
            zone = np.unique(np.concatenate([cand] + [nbr[i] for i in cand]))
            for _ in range(int(os.environ.get("ELBOW_SMOOTH", 30))):
                dr[zone] = 0.5 * dr[zone] + 0.5 * np.array([dr[nbr[i]].mean() for i in zone])
            X = X + (dr / np.maximum(r, 1e-6))[:, None] * perp
            if os.environ.get("ELBOW_DEBUG"):
                print("ELBOWDBG", s_, "cand", len(cand), "dr mm max/min", round(dr.max() * 1000, 1), round(dr.min() * 1000, 1))
                for bb in range(0, NB, 2):
                    print("ELBOWDBG  t %.2f fr %.2f  r(cm) by sector:" % ((bb + b0) * BW, (bb + b0) * BW / Lw), " ".join("%4.1f" % (prof[k_, bb] * 100) for k_ in range(0, NS, 2)), " fair:", " ".join("%4.1f" % (fair[k_, bb] * 100) for k_ in range(0, NS, 2)))
    if os.environ.get("ELBOW_ROUND"):
        # R33 (owner, on R31: "the bend at the elbow is too sharp and not subtle at all"): the skinned elbow folds within
        # ~3 cm of the joint (weights hand over from the humerus to the forearm over +-3 cm - measured; spreading that
        # hand-over flattened the outside of the bent elbow into a notch instead - tried).  Taubin (volume-keeping)
        # smoothing of the skin within RADIUS cm of the posed elbow joint, strength rising with the elbow bend (full at
        # FULL deg), so the corner rounds without thinning the arm.  "radius_cm:passes:full_deg"
        rad_, np2_, full_ = (float(x) for x in os.environ["ELBOW_ROUND"].split(":"))
        for s_ in "rl":
            gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)); el_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
            wr_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].tail))
            flex_ = np.degrees(np.arccos(np.clip(((el_ - gh_) / np.linalg.norm(el_ - gh_)) @ ((wr_ - el_) / np.linalg.norm(wr_ - el_)), -1, 1)))
            amt = min(flex_ / full_, 1.0)
            if amt <= 0.01:
                continue
            d_ = np.linalg.norm(X - el_, axis=1)
            x_ = np.clip(d_ / (rad_ / 100), 0, 1); kw = amt * (1 - x_ * x_ * (3 - 2 * x_))
            ze = np.where(kw > 1e-3)[0]
            for _ in range(int(np2_)):
                for lam_ in (0.5, -0.53):
                    L_ = np.array([X[nbr[i]].mean(0) - X[i] for i in ze])
                    X[ze] += lam_ * L_ * kw[ze][:, None]
            print("ELBOW_ROUND", ht, s_, "flexion %.1f deg, strength %.2f, vertices %d" % (flex_, amt, len(ze)), flush=True)
    if os.environ.get("LAT_WEB"):
        # R29 (owner reference, press from behind: the outer edge of the arm runs in ONE straight line into the side of the
        # back; R28 steps in 4-6 cm under the arm - the web of back muscle from the arm into the torso below the armpit is
        # too thin).  Seen from behind (x across, z up), a straight line is fitted to the outer edge of the upper arm and
        # extended down; the side of the torso below the armpit is pushed out across (x) to meet it, the push fading out
        # over LAT depth (cm) below the shoulder joint and with distance in from the side outline (sigma cm), then smoothed
        g_, dep_, sig_ = (float(x) for x in os.environ["LAT_WEB"].split(":"))
        for kv in [x for x in os.environ.get("LAT_KEY_GAIN", "").split(",") if x]:     # per-key strength "ht:gain"
            if abs(float(kv.split(":")[0]) - ht) < 0.5:
                g_ *= float(kv.split(":")[1])
        dep_ /= 100; sig_ /= 100
        gi3 = {g.index: g.name for g in body.vertex_groups}
        if "lat_arm" not in arm_rest:
            arm_rest["lat_arm"] = {}
            for s_ in "rl":
                wa = np.zeros(nv)
                for v in body.data.vertices:
                    for e in v.groups:
                        n_ = gi3[e.group]
                        if n_.endswith(f"_{s_}") and n_.startswith(("upperarm", "forearm", "lowerarm")):
                            wa[v.index] += e.weight
                arm_rest["lat_arm"][s_] = wa
        D = np.zeros((nv, 3))
        for s_ in "rl":
            sg = 1.0 if s_ == "r" else -1.0
            wa = arm_rest["lat_arm"][s_]
            gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)); el_ = np.array(tuple(W @ rig.pose.bones[f"forearm_{s_}"].head))
            xs_ = sg * X[:, 0]; zs_ = X[:, 2]
            # outer edge of the upper arm per 1 cm height slice (above the joint, below the elbow)
            zz, xx = [], []
            for z0 in np.arange(gh_[2] + 0.05, el_[2] - 0.03, 0.01):
                m_ = (wa > 0.5) & (zs_ >= z0) & (zs_ < z0 + 0.01)
                if m_.sum() > 2: zz.append(z0 + 0.005); xx.append(xs_[m_].max())
            b_, a_ = np.polyfit(zz, xx, 1)                   # x = a + b z (outer arm edge, seen from behind)
            torso = (wa < 0.5) & (xs_ > 0.03)
            for z0 in np.arange(gh_[2] - dep_, gh_[2] + 0.02, 0.01):
                m_ = np.where(torso & (zs_ >= z0) & (zs_ < z0 + 0.01))[0]
                if len(m_) < 3: continue
                edge = xs_[m_].max(); want = a_ + b_ * (z0 + 0.005)
                fade = np.clip((z0 - (gh_[2] - dep_)) / (0.4 * dep_), 0, 1); fade = fade * fade * (3 - 2 * fade)
                d_ = max(want - edge, 0.0) * g_ * fade
                if d_ <= 0: continue
                f_ = np.exp(-((edge - xs_[m_]) / sig_) ** 2)
                D[m_, 0] = np.maximum(D[m_, 0] * sg, d_ * f_) * sg
            if os.environ.get("ELBOW_DEBUG"):
                print("LATDBG", s_, "arm edge line x = %.3f + %.3f z (deg from vertical %.1f)" % (a_, b_, np.degrees(np.arctan(abs(b_)))), "max push mm %.1f" % (np.abs(D[:, 0]).max() * 1000))
        zl = np.where(np.abs(D[:, 0]) > 1e-5)[0]
        zl = np.unique(np.concatenate([zl] + [nbr[i] for i in zl])).astype(int)
        for _ in range(int(os.environ.get("LAT_SMOOTH", 20)) if len(zl) else 0):   # nothing to smooth at gain 0
            D[zl] = 0.5 * D[zl] + 0.5 * np.array([D[nbr[i]].mean(0) for i in zl])
        X = X + D
    if os.environ.get("POST_RR"):
        # R29: the back fill reaches ~55 cm below the shoulder, beyond the slide region (RR) - the skin there could only
        # stretch (measured: lockout stretch 282 after the bake).  The post-fit slides use their own, larger region
        pin_, pout_ = (float(x) for x in os.environ["POST_RR"].split(","))
        wfree2 = np.zeros(nv)
        for s_ in "rl":
            gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head))
            dist_ = np.linalg.norm(X - gh_, axis=1)
            wfree2 = np.maximum(wfree2, 1 - np.clip((dist_ - pin_) / (pout_ - pin_), 0, 1))
        idx2 = np.where(wfree2 > 0)[0]
    else:
        wfree2, idx2 = wfree, idx
    if int(os.environ.get("POST_SLIDE", 0)) > 0:
        # R27b: a short second skin slide after the arm column fit, so the triangles it squeezed at the arm root are spread
        # back out (the column fit left 3 crushed triangles / 2 crossing pairs - measured)
        X = walkslide.slide(X, Fa, A0, idx2, wfree2, iters=int(os.environ["POST_SLIDE"]), eta=ETA, log=[], crush_w=float(os.environ.get("CRUSH_W", 0)))
    for zone in [z for z in os.environ.get("POSTZONES", "").split(";") if z]:
        # R28 (owner reference: the arm meets the trapezius in a soft rounded U at the base of the neck; R27 has a flat
        # floor with two sharp corners - measured): after everything else, concave skin in each zone "passes:x,y,z:r0,r1"
        # (offset from the posed shoulder joint, x outward) is lifted along its normal only, so the corners fill into a
        # fillet while flat or convex skin stays put
        parts_ = zone.split(":"); np_, o_, r_ = parts_[:3]; off4 = np.array([float(x) for x in o_.split(",")]); q0, q1 = (float(x) for x in r_.split(","))
        nrad = float(parts_[3]) if len(parts_) > 3 else 0.0     # >0: neighbourhood = all skin within nrad m (corner-sized)
        w4 = np.zeros(nv)
        for s_ in "rl":
            sg = 1.0 if s_ == "r" else -1.0
            gh_ = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head))
            dd = np.linalg.norm(X - (gh_ + np.array([off4[0] * sg, off4[1], off4[2]])), axis=1)
            x_ = np.clip((dd - q0) / (q1 - q0), 0, 1); w4 = np.maximum(w4, 1 - x_ * x_ * (3 - 2 * x_))
        z4 = np.where(w4 > 0)[0]
        for _ in range(abs(int(np_))):                 # (sign ignored: always normal-only here)
            Fn = np.cross(X[Fa[:, 1]] - X[Fa[:, 0]], X[Fa[:, 2]] - X[Fa[:, 0]])
            vn_ = np.zeros_like(X)
            for c_ in range(3):
                np.add.at(vn_, Fa[:, c_], Fn)
            vn_ = vn_[z4] / np.maximum(np.linalg.norm(vn_[z4], axis=1)[:, None], 1e-15)
            if nrad > 0:
                # the one-ring umbrella only sees mm-scale creases; the arm/neck corner is cm-sized (measured: 800 passes
                # moved it < 0.5 mm), so compare each point with the mean of all skin within nrad
                if _ % 10 == 0:
                    from mathutils.kdtree import KDTree
                    kd = KDTree(len(X))
                    for i_, p_ in enumerate(X): kd.insert(p_, i_)
                    kd.balance()
                    ball = [np.array([j for (_c, j, _d) in kd.find_range(X[i], nrad)]) for i in z4]
                L = np.array([X[b_].mean(0) - X[i] for i, b_ in zip(z4, ball)])
            else:
                L = np.array([X[nbr[i]].mean(0) - X[i] for i in z4])
            h_ = (L * vn_).sum(1)
            X[z4] += (0.5 * np.maximum(h_, 0.0) * w4[z4])[:, None] * vn_
            if os.environ.get("ELBOW_DEBUG") and _ in (0, abs(int(np_)) - 1):
                print("PZDBG pass", _, "zone n", len(z4), "h mm max %.2f min %.2f, n concave %d" % (h_.max() * 1000, h_.min() * 1000, (h_ > 0).sum()))
    if int(os.environ.get("POST_SLIDE2", 0)) > 0:
        X = walkslide.slide(X, Fa, A0, idx2, wfree2, iters=int(os.environ["POST_SLIDE2"]), eta=ETA, log=[], crush_w=float(os.environ.get("CRUSH_W", 0)))
    for _pass in range(2 if int(os.environ.get("FINAL_SLIDE", 0)) > 0 else 1):
        if _pass == 1:
            # R29: the patch rebuilds stretch the skin round them (measured 81 -> 145 over-stretched); let it slide, then
            # clean up once more in case the slide re-folds anything
            X = walkslide.slide(X, Fa, A0, idx2, wfree2, iters=int(os.environ["FINAL_SLIDE"]), eta=ETA, log=[], crush_w=float(os.environ.get("CRUSH_W", 0)))
        for _round in range(int(os.environ.get("AUTO_UNCROSS", 0))):
            # R29: small fold-overs right at the armpit move with the lockout angle (the hand-placed front-fold rebuild sat
            # at the 172 deg position; measured 1-3 crossing pairs at 156 deg).  Each round finds the crossing pairs and
            # rebuilds a small patch (UNCROSS_R m) round each as a thin-plate surface from its outside ring
            tr_ = BVHTree.FromPolygons([Vector(x) for x in X], F, all_triangles=True); fs_ = [set(f) for f in F]
            bad_ = [(a, b) for a, b in tr_.overlap(tr_) if a < b and not (fs_[a] & fs_[b])]
            crushed_ = np.where(areas(X) / A0 < 0.1)[0]            # crushed triangles are rebuilt the same way
            if os.environ.get("UNCROSS_FOLDS"):
                # R29: sharp new folds (spikes / curls) near the shoulders are rebuilt the same way: edges whose dihedral is
                # above F1 deg and at least F2 deg above rest, within 22 cm of a shoulder joint (the hook beside the neck and the
                # front armpit fold moved with the 166 deg lockout - measured: dihedral up to 169 deg)
                f1_, f2_ = (float(x) for x in os.environ["UNCROSS_FOLDS"].split(","))
                # R33: per-key override "ht:f1,f2;..." - the lower threshold that clears the crumpled arm root at the bent-
                # elbow keys also catches the natural armpit fold at the lockout, and the growing patches crushed it there
                # (measured at 166 deg with 40,20: 122 crushed triangles; 90,45 there: 0)
                for kv in [x for x in os.environ.get("UNCROSS_FOLDS_AT", "").split(";") if x]:
                    if abs(float(kv.split(":")[0]) - ht) < 0.5:
                        f1_, f2_ = (float(x) for x in kv.split(":")[1].split(","))
                if "edges" not in arm_rest:
                    from collections import defaultdict
                    ef_ = defaultdict(list)
                    for k_, f in enumerate(F):
                        for i_ in range(3): ef_[tuple(sorted((f[i_], f[(i_ + 1) % 3])))].append(k_)
                    E_ = np.array([k for k, v in ef_.items() if len(v) == 2]); FF_ = np.array([ef_[tuple(e)] for e in E_])
                    nR_ = np.cross(R[Fa[:, 1]] - R[Fa[:, 0]], R[Fa[:, 2]] - R[Fa[:, 0]]); nR_ /= np.maximum(np.linalg.norm(nR_, axis=1)[:, None], 1e-15)
                    arm_rest["edges"] = (E_, FF_, np.degrees(np.arccos(np.clip((nR_[FF_[:, 0]] * nR_[FF_[:, 1]]).sum(1), -1, 1))))
                E_, FF_, dR_ = arm_rest["edges"]
                nX_ = np.cross(X[Fa[:, 1]] - X[Fa[:, 0]], X[Fa[:, 2]] - X[Fa[:, 0]]); nX_ /= np.maximum(np.linalg.norm(nX_, axis=1)[:, None], 1e-15)
                dX_ = np.degrees(np.arccos(np.clip((nX_[FF_[:, 0]] * nX_[FF_[:, 1]]).sum(1), -1, 1)))
                mid_ = (X[E_[:, 0]] + X[E_[:, 1]]) / 2
                near_ = np.zeros(len(E_), bool)
                for s_ in "rl":
                    near_ |= np.linalg.norm(mid_ - np.array(tuple(W @ rig.pose.bones[f"upperarm_{s_}"].head)), axis=1) < 0.22
                sharp_ = np.where(near_ & (dX_ > f1_) & (dX_ - dR_ > f2_))[0]
                crushed_ = np.concatenate([crushed_, FF_[sharp_, 0]]).astype(int)
            if not bad_ and not len(crushed_):
                break
            rr_ = float(os.environ.get("UNCROSS_R", 0.025)) * (1 + 0.3 * _round)
            # R33: cap the patch radius - at 156 deg with the lower fold threshold the rounds never settled and the patches
            # grew to 12 cm, leaving a knot by the neck (measured: 23 sharp folds left after 14 rounds)
            rr_ = min(rr_, float(os.environ.get("UNCROSS_RMAX", 1.0)))
            cents = np.array([X[list(F[a]) + list(F[b])].mean(0) for a, b in bad_] + [X[list(F[k])].mean(0) for k in crushed_])
            done_ = np.zeros(nv, bool)
            for c in cents:
                inner = np.where((np.linalg.norm(X - c, axis=1) < rr_) & ~done_)[0]
                if len(inner) < 3: continue
                done_[inner] = True
                pos = -np.ones(nv, int); pos[inner] = np.arange(len(inner))
                ring = np.unique(np.concatenate([nbr[i] for i in inner])); ring = ring[pos[ring] < 0]
                rows = np.concatenate([inner, ring])
                Lr = np.zeros((len(rows), nv))
                for k_, i in enumerate(rows):
                    Lr[k_, i] = -1.0; Lr[k_, nbr[i]] += 1.0 / len(nbr[i])
                Bk = np.delete(np.arange(nv), inner)
                sol, *_ = np.linalg.lstsq(Lr[:, inner], -(Lr[:, Bk] @ X[Bk]), rcond=None)
                X[inner] = sol
            print("UNCROSS round", _round, "pairs", len(bad_), "crushed / sharp", len(crushed_), "radius mm", round(rr_ * 1000), flush=True)
    if P_noS5 is not None:
        # cancel the S5 bake over the middle of the upper arm only (trapezoid window along the arm, arm skinning weight)
        a0, a1, a2, a3 = (float(x) for x in os.environ["ARM_UNS5"].split(","))
        for s_ in "rl":
            wa, fr, _r0 = arm_rest[s_]
            win = np.clip((fr - a0) / (a1 - a0), 0, 1) * np.clip((a3 - fr) / (a3 - a2), 0, 1)
            win = win * win * (3 - 2 * win)
            X += (win * wa)[:, None] * (P_noS5 - P)
    rP = areas(P) / A0; rX = areas(X) / A0
    tr = BVHTree.FromPolygons([Vector(x) for x in X], F, all_triangles=True); fs = [set(f) for f in F]
    pairs = sum(1 for a, b in tr.overlap(tr) if a < b and not (fs[a] & fs[b]))
    reg = np.zeros(len(F), bool); reg[[k for k, f in enumerate(F) if wfree[f[0]] > 0]] = True
    logs[ht] = {"collapse": [int((rP[reg] < 0.1).sum()), int((rX[reg] < 0.1).sum())], "squash<0.6": [int((rP[reg] < 0.6).sum()), int((rX[reg] < 0.6).sum())],
                "stretch>1.5": [int((rP[reg] > 1.5).sum()), int((rX[reg] > 1.5).sum())], "stretch>2": [int((rP[reg] > 2).sum()), int((rX[reg] > 2).sum())],
                "pairs": pairs, "max_move_mm": round(float(np.linalg.norm(X - P, axis=1).max()) * 1000, 1),
                "whole_body_stretch>2": [int((rP > 2).sum()), int((rX > 2).sum())], "whole_body_collapse": [int((rP < 0.1).sum()), int((rX < 0.1).sum())]}
    print("SLIDE", ht, logs[ht], flush=True)
    out_t[str(ht)] = X
    if ht == KEYS[-1]:
        np.save(out + "/P172.npy", P)
np.savez(out + "/targets.npz", **out_t)
import json; json.dump({"mode": "skin slide", "taubin": TAUB, "lump_passes": int(os.environ.get("LUMP", 0)), "lump_off": os.environ.get("LUMP_OFF", "0,0.04,-0.02"), "lump_r": os.environ.get("LUMP_R", "0.06,0.10"), "zones": os.environ.get("ZONES", ""), "blend_passes": int(os.environ.get("BLEND", 0)), "untangle_iters": int(os.environ.get("UNTANGLE", 0)), "guard_zones": os.environ.get("GUARD_ZONES", "1") == "1", "crush_w": float(os.environ.get("CRUSH_W", 0)), "deltoid_bump": os.environ.get("DELT_BUMP", ""), "fair": os.environ.get("FAIR", ""), "postfair": os.environ.get("POSTFAIR", ""), "arm_restore": ARM_RESTORE, "arm_uns5": os.environ.get("ARM_UNS5", ""), "arm_inflate": os.environ.get("ARM_INFLATE", ""), "elbow_fair": os.environ.get("ELBOW_FAIR", ""), "elbow_mode": os.environ.get("ELBOW_MODE", "hull"), "postzones": os.environ.get("POSTZONES", ""), "lat_web": os.environ.get("LAT_WEB", ""), "arm_rigid": os.environ.get("ARM_RIGID", ""), "rigid_key_gain": os.environ.get("RIGID_KEY_GAIN", ""), "lat_key_gain": os.environ.get("LAT_KEY_GAIN", ""), "post_rr": os.environ.get("POST_RR", ""), "auto_uncross": int(os.environ.get("AUTO_UNCROSS", 0)), "uncross_r": os.environ.get("UNCROSS_R", ""), "uncross_rmax": os.environ.get("UNCROSS_RMAX", ""), "uncross_folds": os.environ.get("UNCROSS_FOLDS", ""), "uncross_folds_at": os.environ.get("UNCROSS_FOLDS_AT", ""), "final_slide": int(os.environ.get("FINAL_SLIDE", 0)), "lockout_ht": float(bpy.context.scene.get("hgpt_press_lockout_ht", 172.0)), "post_slide": int(os.environ.get("POST_SLIDE", 0)), "post_slide2": int(os.environ.get("POST_SLIDE2", 0)), "arm_key_gain": os.environ.get("ARM_KEY_GAIN", ""), "tube_upper": {k: os.environ.get(k, "") for k in ("TUBE_UPPER", "TUBE_UPPER_A", "TUBE_UPPER_DEG")}, "elbow_round": os.environ.get("ELBOW_ROUND", ""), "tube": {k: os.environ.get(k, "") for k in ("TUBE_A", "TUBE_B", "TUBE_ITERS", "TUBE_RELAX", "TUBE_FILLROOT", "ARM_WMIN", "ELBOW_SMOOTH", "TUBE_ROOT_SCALE")}, "slide_iters": SLIDE, "eta": ETA, "region": [RIN, ROUT], "keys_ht": KEYS, "log": {str(k): v for k, v in logs.items()}}, open(out + "/targets.npz.json", "w"), indent=1)
# render 172
scene = bpy.context.scene
for o in scene.objects:
    if o.type in ("MESH", "CURVE"): o.hide_render = True
mt = bpy.data.materials.new("S"); mt.diffuse_color = (0.72, 0.55, 0.45, 1)
objs = {}
for tag, Y in (("current", np.load(out + "/P172.npy")), ("slid", out_t[str(KEYS[-1])])):
    me = bpy.data.meshes.new(tag); me.from_pydata([tuple(p) for p in Y], [], [tuple(f) for f in F]); me.materials.append(mt)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(tag, me); scene.collection.objects.link(o); objs[tag] = o
scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
scene.render.film_transparent = True; scene.render.resolution_x = scene.render.resolution_y = 600
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.75
cam = bpy.data.objects.new("C", cd); scene.collection.objects.link(cam); scene.camera = cam
gh = W @ rig.pose.bones["upperarm_r"].head
for tag, o in objs.items():
    for oo in objs.values(): oo.hide_render = oo is not o
    for view, d in (("three_quarter", (0.7, 0.7, 0.1)), ("back", (0, 1, 0.1)), ("side", (1, 0, 0.05)), ("front", (0, -1, 0.05)), ("close", (0.7, 0.7, 0.1))):
        d = Vector(d).normalized(); tgt = Vector((0.0, 0, gh.z - 0.08))
        cd.ortho_scale = 0.75
        if view == "close":
            tgt = Vector(tuple(gh)) + Vector((-0.04, 0.0, 0.0)); cd.ortho_scale = 0.32
        cam.location = tgt + d * 4.0; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        scene.render.filepath = f"{out}/{tag}_{view}.png"; bpy.ops.render.render(write_still=True)
