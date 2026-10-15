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
out_t = {}; logs = {}
for ht in KEYS:
    bench._reset(rig); s4.press_pose(res, ht); drives.drive(rig, body)
    V, _ = bench._evaluated(body); P = np.array([tuple(v) for v in V])
    X = P.copy()
    wfree = np.zeros(nv)
    for s in "rl":
        gh = np.array(tuple(W @ rig.pose.bones[f"upperarm_{s}"].head))
        dist = np.linalg.norm(P - gh, axis=1)
        wfree = np.maximum(wfree, 1 - np.clip((dist - RIN) / (ROUT - RIN), 0, 1))
    idx = np.where(wfree > 0)[0]
    # 1. shape: Taubin smoothing of the region (boundary held by wfree)
    S = P.copy()
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
    rP = areas(P) / A0; rX = areas(X) / A0
    tr = BVHTree.FromPolygons([Vector(x) for x in X], F, all_triangles=True); fs = [set(f) for f in F]
    pairs = sum(1 for a, b in tr.overlap(tr) if a < b and not (fs[a] & fs[b]))
    reg = np.zeros(len(F), bool); reg[[k for k, f in enumerate(F) if wfree[f[0]] > 0]] = True
    logs[ht] = {"collapse": [int((rP[reg] < 0.1).sum()), int((rX[reg] < 0.1).sum())], "squash<0.6": [int((rP[reg] < 0.6).sum()), int((rX[reg] < 0.6).sum())],
                "stretch>1.5": [int((rP[reg] > 1.5).sum()), int((rX[reg] > 1.5).sum())], "stretch>2": [int((rP[reg] > 2).sum()), int((rX[reg] > 2).sum())],
                "pairs": pairs, "max_move_mm": round(float(np.linalg.norm(X - P, axis=1).max()) * 1000, 1)}
    print("SLIDE", ht, logs[ht], flush=True)
    out_t[str(ht)] = X
    if ht == KEYS[-1]:
        np.save(out + "/P172.npy", P)
np.savez(out + "/targets.npz", **out_t)
import json; json.dump({"mode": "skin slide", "taubin": TAUB, "lump_passes": int(os.environ.get("LUMP", 0)), "lump_off": os.environ.get("LUMP_OFF", "0,0.04,-0.02"), "lump_r": os.environ.get("LUMP_R", "0.06,0.10"), "zones": os.environ.get("ZONES", ""), "blend_passes": int(os.environ.get("BLEND", 0)), "untangle_iters": int(os.environ.get("UNTANGLE", 0)), "guard_zones": os.environ.get("GUARD_ZONES", "1") == "1", "crush_w": float(os.environ.get("CRUSH_W", 0)), "slide_iters": SLIDE, "eta": ETA, "region": [RIN, ROUT], "keys_ht": KEYS, "log": {str(k): v for k, v in logs.items()}}, open(out + "/targets.npz.json", "w"), indent=1)
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
