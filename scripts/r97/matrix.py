"""Shoulder movement matrix: deterministic poses, renders and machine measurements (weights-only unless --correctives).

usage: matrix.py -- <blend> <out_dir> [--quick] [--no-render] [--correctives] [--poses a,b,c]
"""
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
blend, out = argv[0], Path(argv[1])
QUICK = "--quick" in argv
RENDER = "--no-render" not in argv
CORR = "--correctives" in argv
ONLY = set(argv[argv.index("--poses") + 1].split(",")) if "--poses" in argv else None
bpy.ops.wm.open_mainfile(filepath=blend)
from hgpt_pose import F, U, D, B, Poser, look, render, setup_render, lat  # noqa: E402

P = Poser()
P.set_correctives(0.0)
for o in bpy.data.objects:                       # bare body evidence: hide shorts, show the full body surface
    if o.type == "MESH" and "SHORTS" in o.name:
        o.hide_render = True; o.hide_viewport = True
for m in P.body.modifiers:
    if m.type == "MASK":
        m.show_render = False; m.show_viewport = False
RES = int(argv[argv.index("--res") + 1]) if "--res" in argv else (640 if QUICK else 900)
cam = setup_render(RES)
out.mkdir(parents=True, exist_ok=True)

me = P.body.data
n = len(me.vertices)
names = [g.name for g in P.body.vertex_groups]
Wm = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        Wm[v.index, g.group] = g.weight
gi = {nm: i for i, nm in enumerate(names)}
rest = P.evaluated()
tris = np.array([t.vertices[:] for t in me.loop_triangles]) if me.loop_triangles else None
if tris is None or len(tris) == 0:
    me.calc_loop_triangles(); tris = np.array([t.vertices[:] for t in me.loop_triangles])
edges = np.array([e.vertices[:] for e in me.edges])
rest_len = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)

# shoulder zone: anything with girdle/arm influence on the proximal half, per side
def zone(s):
    g = sum(Wm[:, gi[b]] for b in (f"clavicle_{s}", f"scapula_{s}", f"upperarm_{s}"))
    side = rest[:, 0] < 0 if s == "l" else rest[:, 0] > 0
    return side & (g > 0.02) & (rest[:, 2] > 1.25)
ZONE = {s: zone(s) for s in "lr"}
ZONE_ANY = ZONE["l"] | ZONE["r"]
TRANS = {s: ZONE[s] & (Wm[:, gi[f"upperarm_{s}"]] > 0.03) & (Wm[:, gi[f"upperarm_{s}"]] < 0.97) for s in "lr"}
zone_faces = np.nonzero(ZONE_ANY[tris].any(1))[0]
zone_edges = np.nonzero(ZONE_ANY[edges].any(1))[0]

# ------------------------------------------------------------------ pose matrix
def P_elev(plane, theta, axial=0.0, elbow=0.0, horizontal=0.0, sides="lr"):
    def f():
        for s in sides:
            P.elevate(s, plane, theta, axial=axial, elbow=elbow, horizontal=horizontal)
    return f

ELEV = [0, 30, 60, 90, 120, 150, 170] if not QUICK else [0, 90, 150, 170]
AX = {"internal": -40.0, "neutral": 0.0, "external": 40.0}
poses = {}
for plane in ("abduction", "flexion"):
    for th in ELEV:
        for an, av in AX.items():
            if th == 0 and an != "neutral" and QUICK:
                continue
            # external rotation range shrinks overhead; keep requested values anatomically reachable
            a = av if th <= 120 else av * 0.6
            poses[f"{plane}_{th:03d}_{an}"] = (P_elev(plane, th, axial=a), dict(plane=plane, theta=th, axial=an))
if not QUICK:
    poses["horizontal_adduction_90"] = (P_elev("flexion", 90, horizontal=35, elbow=20), {})
    poses["horizontal_abduction_90"] = (P_elev("abduction", 90, horizontal=-25, elbow=20), {})
    poses["arm_behind_torso"] = (P_elev(-90, 40, axial=-40, elbow=70), {})
    poses["bent_elbow_elevation_120"] = (P_elev("scaption", 120, elbow=100, axial=30), {})
    poses["lateral_raise_top"] = (P_elev("abduction", 90, elbow=10, axial=-10), {})
    poses["front_raise_top"] = (P_elev("flexion", 95, elbow=5, axial=-20), {})
    poses["press_bottom_like"] = (P_elev(20, 85, elbow=95, axial=60), {})
    poses["press_top_like"] = (P_elev(15, 165, elbow=15, axial=25), {})
    poses["pullup_hang_like"] = (P_elev(25, 170, elbow=5, axial=20), {})
    poses["pullup_top_like"] = (P_elev(10, 60, elbow=130, axial=10), {})
    poses["bench_bottom_like"] = (P_elev(5, 80, horizontal=-30, elbow=90, axial=55), {})
    poses["pushup_bottom_like"] = (P_elev(30, 55, horizontal=-20, elbow=95, axial=20), {})
    poses["row_top_like"] = (P_elev(-80, 45, elbow=100, axial=0), {})
    poses["curl_top_like"] = (P_elev("flexion", 15, elbow=125), {})
if ONLY:
    poses = {k: v for k, v in poses.items() if k in ONLY}

# ------------------------------------------------------------------ measurements
def self_intersections(Pts):
    faces = tris[zone_faces]
    tree = BVHTree.FromPolygons([tuple(p) for p in Pts], [tuple(f) for f in faces], all_triangles=True)
    pairs = tree.overlap(tree)
    bad = 0
    fs = [set(f) for f in faces]
    for a, b in pairs:
        if a < b and not (fs[a] & fs[b]):
            bad += 1
    return bad

def edge_ratio(Pts):
    e = edges[zone_edges]
    r = np.linalg.norm(Pts[e[:, 0]] - Pts[e[:, 1]], axis=1) / np.maximum(rest_len[zone_edges], 1e-9)
    return float(r.min()), float(np.percentile(r, 1)), float(np.percentile(r, 99)), float(r.max())

results, store = {}, {}
VIEWS = {"front": (0, 8, (0, 0, 1.30), 3.0), "front_three_quarter": (35, 10, (0, 0, 1.30), 3.0),
         "side": (90, 5, (0, 0, 1.30), 3.0), "rear_three_quarter": (145, 10, (0, 0, 1.30), 3.0),
         "rear": (180, 8, (0, 0, 1.30), 3.0)}
CLOSE = {"close_front": (25, 8, None, 0.95), "close_axilla": (75, -20, None, 0.95), "close_rear": (150, 10, None, 0.95)}
t0 = time.time()
for name, (fn, meta) in poses.items():
    P.reset(); fn()
    if CORR:
        pass
    Pts = P.evaluated()
    store[name] = Pts
    si = self_intersections(Pts)
    er = edge_ratio(Pts)
    gh = {s: np.array(P.pb(f"upperarm_{s}").head) for s in "lr"}
    shrink = {s: float(np.min(np.linalg.norm(Pts[TRANS[s]] - gh[s], axis=1) / np.maximum(np.linalg.norm(rest[TRANS[s]] - np.array(P.rig.data.bones[f"upperarm_{s}"].head_local), axis=1), 1e-6))) for s in "lr"}
    mirrored = Pts.copy(); mirrored[:, 0] *= -1
    mi = np.load("/home/user/r97/mirror_idx.npy")
    sym = float(np.abs(Pts[ZONE["l"]] - mirrored[mi][ZONE["l"]]).max())
    results[name] = dict(meta, self_intersections=si, edge_ratio_min=er[0], edge_ratio_p1=er[1], edge_ratio_p99=er[2], edge_ratio_max=er[3],
                         transition_shrink_min=shrink, symmetry_max_m=sym)
    if RENDER:
        for v, (az, el, tgt, dist) in VIEWS.items():
            look(cam, tgt, az, el, dist); render(out / f"{name}__{v}.png")
        c = np.array(P.pb("upperarm_l").head)
        for v, (az, el, _, dist) in CLOSE.items():
            look(cam, c + np.array([0.02, 0.0, -0.06]), az, el, dist); render(out / f"{name}__{v}.png")
# axial-rotation response: transition-zone and deltoid displacement between internal and external at matched elevation
axial = {}
for plane in ("abduction", "flexion"):
    for th in ELEV:
        k = lambda a: f"{plane}_{th:03d}_{a}"
        if k("internal") in store and k("external") in store:
            dlt = np.linalg.norm(store[k("external")] - store[k("internal")], axis=1)
            axial[f"{plane}_{th:03d}"] = {"transition_rms_mm": float(np.sqrt(np.mean(dlt[TRANS["l"]] ** 2)) * 1000),
                                          "zone_rms_mm": float(np.sqrt(np.mean(dlt[ZONE["l"]] ** 2)) * 1000),
                                          "torso_side_rms_mm": float(np.sqrt(np.mean(dlt[ZONE["l"] & (Wm[:, gi['upperarm_l']] < 0.5)] ** 2)) * 1000)}
# arc continuity: second difference of positions along each elevation arc (neutral axial)
arc = {}
for plane in ("abduction", "flexion"):
    seq = [store.get(f"{plane}_{th:03d}_neutral") for th in ELEV]
    if all(s is not None for s in seq) and len(seq) >= 3:
        worst = 0.0; where = None
        for i in range(1, len(seq) - 1):
            step_a = np.linalg.norm(seq[i] - seq[i - 1], axis=1); step_b = np.linalg.norm(seq[i + 1] - seq[i], axis=1)
            NR = ZONE["l"] & (Wm[:, gi["upperarm_l"]] < 0.97)
            dd = np.linalg.norm(seq[i + 1] - 2 * seq[i] + seq[i - 1], axis=1)[NR]
            ratio = float(dd.max() / max(1e-6, np.r_[step_a[NR], step_b[NR]].max()))
            if ratio > worst:
                worst, where = ratio, ELEV[i]
        arc[plane] = {"max_second_difference_ratio": worst, "at_theta": where}
summary = {"blend": blend, "correctives": CORR, "poses": results, "axial_response": axial, "arc_continuity": arc,
           "zone_vertices": int(ZONE_ANY.sum()), "seconds": time.time() - t0}
(out / "matrix_report.json").write_text(json.dumps(summary, indent=1))
print(json.dumps({"poses": len(results), "worst_self_intersections": max(r["self_intersections"] for r in results.values()),
                  "edge_ratio_min": min(r["edge_ratio_min"] for r in results.values()),
                  "edge_ratio_max": max(r["edge_ratio_max"] for r in results.values()),
                  "symmetry_max_m": max(r["symmetry_max_m"] for r in results.values()),
                  "axial": axial, "arc": arc, "seconds": round(time.time() - t0, 1)}, indent=1))
