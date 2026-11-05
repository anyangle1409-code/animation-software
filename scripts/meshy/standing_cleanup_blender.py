"""Standing-model cleanup on the bound body (rest geometry) - writes a NEW file. Proportions and the corrective keys
are preserved: every rest-position edit is applied to every shape-key layer as well (key deltas unchanged).

Zones are in rest space (metres; the body faces -y, +x is the character's left). Steps, in order:
  1. MIDLINE (upper back: spine groove; front: sternum). Measured per vertex: the body follows the approved source
     there, and the SOURCE itself carries a spinal crease only 1-2 mm wide and ~8 mm deep (e.g. 136.8 mm at the midline
     vs 144.5 mm 6 mm to the side, z 1.34 m) and a fine sternal line; at the source's density they read as fine lines,
     at the body's density as a dark slit and a notched seam. (A first profile probe with a +-2.5 mm window read the
     crease walls and wrongly suggested the body was deeper than the source.) A volume-preserving Taubin smoothing
     (lambda/mu) in a band that fades from the midline to BAND rounds the crease into a broad, shallower groove (about
     4 mm over +-5 mm) - a deliberate departure from the source artefact; the back / chest muscles beyond the band are
     untouched.
  2. CRINKLES (neck-to-trapezius transition, under the jaw back to its angle): small-scale ridges are measured as the
     umbrella vector along the normal; 20 Taubin passes in box zones (fading at the edges), concentrated on the
     crinkling vertices (above the zone's 70th percentile, plus one ring), remove the 1-2 edge scale wrinkles without
     changing the neck volume (Taubin does not shrink). Runs after the pelvis step (it needs box_weight).
  3. PELVIS - neutral anatomical nude base form (the source wears modelled shorts, so there is no anatomical reference
     under them): the pelvis zone is made symmetric from its cleaner side (the side whose genital zone has the lower
     umbrella energy is the master; the other side takes the mirrored master surface, blended at the zone edge; up to 45 mm - with 20 mm the protruding flap on the left was skipped); the
     genital mass (within 55 mm of the midline, in front of y = -50 mm, reaching the thigh junction where the flap sat) is reduced to a simple smooth volume (up
     to 60 Taubin passes, fewer if skin would cross - volume kept, fold / flap removed, no detail);
     the perineum / lower gluteal fold and the hard vertical lines at the hip sides (the source's shorts side seams) get
     16 lighter passes; the deep crease where the genital mass meets the inner thigh (the 'flap') is filled - concave
     vertices only move outward - for a neutral junction (symmetric weights on the mirrored surface keep it symmetric; mirroring once more afterwards made
     skin cross - 40 rest pairs - and was dropped). (A first pass with 10 passes
     around a centre on the pubic mound left the flap in place.)
  4. FULLNESS (hands, feet): vertices lying more than 0.7 mm inside the source are put on it along their normal
     (within 4 mm) - the measured thinness of the hands (0.8 mm mean, 2.6 mm p5 inside) and toes.
     A vertex whose move would make touching fingers / toes cross is left where it was.
  Guards: rest self-intersections not increased (a step that adds some is undone), drivers kept.

usage: python3.13 standing_cleanup_blender.py -- <bound .blend> <retopo checkpoint with source proxy> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCBLEND, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
with bpy.data.libraries.load(str(SRCBLEND), link=False) as (src, dst):
    dst.objects = ["HGPT_SOURCE_PROXY_Mesh_0"]
SRC = dst.objects[0]
sb = BVHTree.FromPolygons([v.co.copy() for v in SRC.data.vertices], [tuple(p.vertices) for p in SRC.data.polygons])
body = bpy.data.objects["MESHY_BODY"]; me = body.data
drivers0 = len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.normal_update()
SK = list(bm.verts.layers.shape.values()); L4 = bm.verts.layers.int["t4_part"]; L5 = bm.verts.layers.int["t5_part"]
NV = len(bm.verts); nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
X0 = np.array([v.co[:] for v in bm.verts])


def P():
    return np.array([v.co[:] for v in bm.verts])


def apply(Xnew, mask=None):
    """move basis to Xnew (only mask), the same offset on every shape-key layer"""
    for i in (np.where(mask)[0] if mask is not None else range(NV)):
        v = bm.verts[int(i)]; d = Vector(Xnew[i]) - v.co
        if d.length < 1e-9:
            continue
        v.co = v.co + d
        for L in SK:
            v[L] = v[L] + d


def intersections():
    tris = bm.calc_loop_triangles(); bm.verts.index_update(); T = [tuple(l.vert.index for l in t) for t in tris]
    b = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
    return sum(1 for i, j in b.overlap(b) if not set(T[i]) & set(T[j]))


def normals():
    bm.normal_update(); return np.array([v.normal[:] for v in bm.verts])


def umbrella(X):
    return np.array([X[n].mean(0) - X[i] if n else np.zeros(3) for i, n in enumerate(nbr)])


def taubin(X, w, passes, lam=0.5, mu=-0.53):
    """volume-preserving smoothing; w in [0,1] per vertex (0 = fixed)"""
    act = np.where(w > 0)[0]
    for _ in range(passes):
        for f in (lam, mu):
            U = umbrella(X); X = X.copy(); X[act] += (f * w[act])[:, None] * U[act]
    return X


def smoothstep(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def snap_to_source(X, mask, maxd, min_dev=0.0):
    N = normals(); Y = X.copy(); n_done = 0
    for i in np.where(mask)[0]:
        p = Vector(X[i]); n = Vector(N[i]); best = None
        for d in (n, -n):
            h = sb.ray_cast(p, d, maxd)
            if h[0] is not None and h[1].dot(n) > 0.3 and (best is None or h[3] < best[3]):
                best = h
        if best is not None and best[3] > min_dev:
            Y[i] = np.array(best[0]); n_done += 1
    return Y, n_done


def snap_axis(X, mask, direction, maxd=0.012):
    """put mask vertices on the source by a ray along +-direction (front/back axis): inside a narrow slit the vertex
    normals tilt sideways and miss the surface"""
    Y = X.copy(); n_done = 0; dvec = Vector(direction)
    for i in np.where(mask)[0]:
        p = Vector(X[i]); best = None
        for d in (dvec, -dvec):
            h = sb.ray_cast(p - d * 1e-4, d, maxd)
            if h[0] is not None and (best is None or h[3] < best[3]):
                best = h
        if best is not None:
            Y[i] = np.array(best[0]); n_done += 1
    return Y, n_done


def crinkle_energy(X, mask):
    N = normals(); U = umbrella(X); return float(np.mean(np.abs(np.einsum("ij,ij->i", U, N))[mask]) * 1000)


rep = {"method": __doc__.split("usage")[0].strip(), "steps": {}}
inter0 = intersections(); rep["rest_intersections_before"] = inter0
x, y, z = X0[:, 0], X0[:, 1], X0[:, 2]
hand = np.array([v[L4] > 0 for v in bm.verts]); foot = np.array([v[L5] in (7, 8) for v in bm.verts])


def step(name, fn):
    before = P(); info = fn() or {}
    k = intersections()
    if k > inter0:                                          # guard: undo the step
        apply(before); info["status"] = f"UNDONE: rest intersections {k} > {inter0}"
    else:
        info["rest_intersections_after"] = k
    mv = np.linalg.norm(P() - before, axis=1); info["moved_vertices"] = int((mv > 1e-5).sum()); info["max_move_mm"] = round(float(mv.max()) * 1000, 2)
    rep["steps"][name] = info; print("STEP", name, json.dumps(info), flush=True)


STRIP, BAND = 0.006, 0.035
back = (y > 0.02) & (z > 1.10) & (z < 1.52); front = (y < -0.02) & (z > 1.24) & (z < 1.47) & ~hand


def midline():
    out = {}
    for nm, zone, ax, passes in (("spine", back, (0, 1, 0), 30), ("sternum", front, (0, -1, 0), 14)):
        e0 = crinkle_energy(P(), zone & (np.abs(x) < BAND)); n = 0
        w = np.where(zone, 1 - smoothstep(np.abs(x) / BAND), 0.0)
        X = taubin(P(), w, passes); apply(X, w > 0)
        out[nm] = {"taubin_passes": passes, "band_crinkle_mm_before_after": [round(e0, 3), round(crinkle_energy(P(), zone & (np.abs(x) < BAND)), 3)]}
    return out


def crinkles():
    """box-weighted zones (a radial weight from the zone centroid put the two-sided neck zone's centre on the midline,
    near neither crinkle); the pass is concentrated on the crinkling vertices (umbrella along the normal above the
    zone's 70th percentile, spread one ring) and stronger (20 Taubin passes)"""
    zones = {"neck_trapezius": [((0.03, -0.12, 1.45), (0.14, 0.10, 1.60)), ((-0.14, -0.12, 1.45), (-0.03, 0.10, 1.60))],
             "under_jaw_to_angle": [((-0.095, -0.12, 1.555), (0.095, 0.05, 1.645))]}
    out = {}; N = normals(); U = umbrella(P()); cr = np.abs(np.einsum("ij,ij->i", U, N))
    for nm, boxes in zones.items():
        w = np.zeros(NV)
        for lo, hi in boxes:
            w = np.maximum(w, box_weight(X0, lo, hi, 0.012))
        w[hand] = 0; zone = w > 0.5
        hot = zone & (cr > np.percentile(cr[zone], 70)); spread = hot.copy()
        for i in np.where(hot)[0]:
            spread[nbr[i]] = True
        wt = w * np.where(spread, 1.0, 0.35)
        e0 = crinkle_energy(P(), zone); apply(taubin(P(), wt, 20), wt > 0)
        out[nm] = {"vertices": int(zone.sum()), "crinkle_vertices": int(hot.sum()), "crinkle_mm_before_after": [round(e0, 3), round(crinkle_energy(P(), zone), 3)]}
    return out


def mirror_from(master, zone, wz, dmax=0.045):
    """the zone takes the mirrored surface of its master side (blended by wz at the zone edge); midline onto x = 0"""
    X = P(); tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
    Xm = X.copy(); Xm[:, 0] *= -1; mb = BVHTree.FromPolygons([tuple(p) for p in Xm], T, all_triangles=True); Y = X.copy()
    for i in np.where(zone & (X[:, 0] * master < -0.003))[0]:
        loc, n, ti, d = mb.find_nearest(Vector(X[i]))
        if loc is not None and d < dmax and np.sign(Xm[T[ti][0], 0]) == np.sign(X[i, 0]):
            Y[i] = X[i] + wz[i] * (np.array(loc) - X[i])
    mid = zone & (np.abs(X[:, 0]) <= 0.003); Y[mid, 0] = X[mid, 0] * (1 - wz[mid]); apply(Y, zone); return T


def box_weight(X, lo, hi, fade):
    t = np.ones(len(X))
    for k in range(3):
        t = np.minimum(t, np.minimum((X[:, k] - lo[k]) / fade, (hi[k] - X[:, k]) / fade))
    return smoothstep(t)


def pelvis():
    zone = (z > 0.74) & (z < 1.02) & (np.abs(x) < 0.21) & ~hand
    X = P(); gen = (np.abs(x) < 0.075) & (z > 0.78) & (z < 0.94) & (y < -0.05)
    eL = crinkle_energy(X, gen & (x > 0.004)); eR = crinkle_energy(X, gen & (x < -0.004))
    master = 1 if eL < eR else -1                                        # +1: character's left side is cleaner
    edge = np.minimum.reduce([(z - 0.74) / 0.04, (1.02 - z) / 0.04, (0.21 - np.abs(x)) / 0.04]); wz = np.where(zone, smoothstep(edge), 0.0)
    T = mirror_from(master, zone, wz)
    g0 = crinkle_energy(P(), gen)
    # genital form: reduced to a simple smooth volume (Taubin keeps the volume, removes the fold / flap)
    # the genital mass only: within 45 mm of the midline and in front of the thigh fronts (the 85 mm box also took the
    # inner thighs and pulled the two skins into each other: 40 rest crossings); fewer passes if skin would still cross
    wg = box_weight(X0, (-0.055, -0.25, 0.785), (0.055, -0.05, 0.935), 0.015) * zone; used = 0
    base = P()
    for passes in (60, 40, 25, 12):
        apply(taubin(base, wg, passes), wg > 0)
        if intersections() <= inter0:
            used = passes; break
        apply(base)
    # groin junction: the 'flap' is a deep narrow crease where the genital mass meets the inner thigh (two surfaces
    # nearly touching - volume-preserving smoothing cannot open it). For the neutral base form the valley is FILLED:
    # concave vertices (umbrella along the normal > 0) move outward towards their neighbours, convex ones never move
    wc = box_weight(X0, (-0.085, -0.13, 0.775), (0.085, -0.025, 0.885), 0.012) * zone; base = P(); used3 = 0
    for passes in (40, 25, 12):
        Xf = base.copy()
        for _ in range(passes):
            bm_n = normals() if False else None
            U = umbrella(Xf); c = np.einsum("ij,ij->i", U, normals()); m = (wc > 0) & (c > 0)
            Xf[m] += (0.5 * wc[m])[:, None] * U[m]
            apply(Xf, m)
        if intersections() <= inter0:
            used3 = passes; break
        apply(base)
    # perineum / lower gluteal fold and the hip-side lines left by the source's shorts seams: lighter
    wp_ = box_weight(X0, (-0.06, -0.06, 0.74), (0.06, 0.08, 0.86), 0.02) * zone
    wh = (box_weight(X0, (0.13, -0.12, 0.82), (0.215, 0.12, 1.02), 0.02) + box_weight(X0, (-0.215, -0.12, 0.82), (-0.13, 0.12, 1.02), 0.02)) * zone
    base = P(); wl = np.maximum(wp_, wh); used2 = 0
    for passes in (16, 8):
        apply(taubin(base, wl, passes), wl > 0)
        if intersections() <= inter0:
            used2 = passes; break
        apply(base)
    Xc = P(); kd = BVHTree.FromPolygons([tuple(p * np.array([-1, 1, 1])) for p in Xc], T, all_triangles=True); asym = []
    for i in np.where(zone)[0][::7]:
        loc, _, _, d = kd.find_nearest(Vector(Xc[i])); asym.append(d)
    return {"master_side": "left (+x)" if master > 0 else "right (-x)", "genital_umbrella_mm_left_right": [round(eL, 3), round(eR, 3)],
            "genital_umbrella_mm_after_symmetry_after_form": [round(g0, 3), round(crinkle_energy(P(), gen), 3)],
            "genital_taubin_passes": used, "perineum_hip_side_passes": used2, "groin_crease_fill_passes": used3,
            "pelvis_asymmetry_mm_mean_max": [round(float(np.mean(asym)) * 1000, 2), round(float(np.max(asym)) * 1000, 2)]}


def crossing_verts():
    tris = bm.calc_loop_triangles(); bm.verts.index_update(); T = [tuple(l.vert.index for l in t) for t in tris]
    b = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True); out = set()
    for i, j in b.overlap(b):
        if not set(T[i]) & set(T[j]):
            out |= set(T[i]) | set(T[j])
    return out


def fullness():
    X0_ = P(); out = {}
    for nm, zone in (("hands", hand), ("feet", foot)):
        Y, n = snap_to_source(P(), zone, 0.004, min_dev=0.0007); apply(Y, zone); out[nm] = {"vertices": int(zone.sum()), "moved_to_source": n}
    moved = np.linalg.norm(P() - X0_, axis=1) > 1e-6; reverted = 0
    for _ in range(12):                                   # touching fingers / toes: undo only the moves that cross skin
        cv = crossing_verts()
        bad = {w.index for i in cv for f in bm.verts[i].link_faces for w in f.verts if moved[w.index]}
        if not bad:
            break
        Xr = P(); idx = np.array(sorted(bad)); Xr[idx] = X0_[idx]; m = np.zeros(NV, bool); m[idx] = True; apply(Xr, m)
        moved[idx] = False; reverted += len(bad)
    out["reverted_where_skin_would_cross"] = reverted
    return out


step("1_midline", midline)
step("3_pelvis_neutral_form", pelvis)
step("2_crinkles", crinkles)
step("4_hands_feet_fullness", fullness)
bm.to_mesh(me); me.update()
rep["drivers_before_after"] = [drivers0, len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0]
bpy.data.objects.remove(SRC, do_unlink=True)
body["STANDING_CLEANUP"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("CLEANUP done")
