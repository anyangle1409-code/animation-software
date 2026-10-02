"""Read-only face-level surface-quality diagnostic of the posed (evaluated: shape keys + skinning) body (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/diagnose_original_v1_surface_folds_blender.py -- <out.json> <pose[,pose...]> [area_ratio_floor=0.15] [fold_cos=0.0]

For each pose and each triangle (quads split along the stored diagonal) it reports
  * area ratio  = posed area / rest area (collapse when small),
  * orientation = dot(posed normal, rest normal rotated by the best local rigid fit of the three vertices' LBS neighbourhood) is NOT available
    cheaply, so inversion is measured against the face's own neighbours: the dihedral cosine between each pair of edge-adjacent triangles
    in the posed mesh compared with the same pair at rest (fold = posed cosine < fold_cos while rest cosine > 0.5, i.e. a crease that did not exist),
and lists the vertices that belong to collapsed / folded faces, with their regions and whether they sit in a declared vertex set.
Used to track the surface defects the edge-stretch metrics cannot see (slivers, fold-over, crumpling) and as the training signal for the corrective.
"""
import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
out = Path(args[0])
poses = args[1].split(",")
FLOOR = float(args[2]) if len(args) > 2 else 0.15
FOLD = float(args[3]) if len(args) > 3 else 0.0
ps = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = ps.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": ps.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "defs", "exec"), ns)
sys.argv = saved
rig, body, POSES, reset, upd = ns["rig"], ns["body"], ns["POSES"], ns["reset"], ns["upd"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False
me = body.data
rest = np.array([v.co[:] for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([t.vertices[:] for t in me.loop_triangles])
names = json.loads(bpy.context.scene["hgpt_region_names"])
reg = np.array([d.value for d in me.attributes["hgpt_region"].data])


def tri_geom(P):
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    n = np.cross(b - a, c - a)
    ar = 0.5 * np.linalg.norm(n, axis=1)
    return n / np.maximum(2 * ar, 1e-18)[:, None], ar


# edge-adjacent triangle pairs
em = {}
for t, (x, y, z) in enumerate(tris):
    for e in ((x, y), (y, z), (z, x)):
        em.setdefault((min(e), max(e)), []).append(t)
ADJ = np.array([v for v in em.values() if len(v) == 2])
n0, A0 = tri_geom(rest)
cos0 = (n0[ADJ[:, 0]] * n0[ADJ[:, 1]]).sum(axis=1)
EDG = np.array([e.vertices[:] for e in me.edges])
DEG = np.zeros(len(rest))
np.add.at(DEG, EDG[:, 0], 1)
np.add.at(DEG, EDG[:, 1], 1)
_el = np.linalg.norm(rest[EDG[:, 0]] - rest[EDG[:, 1]], axis=1)
ELEN = np.zeros(len(rest))
np.add.at(ELEN, EDG[:, 0], _el)
np.add.at(ELEN, EDG[:, 1], _el)
ELEN = ELEN / DEG
result = {"source": Path(bpy.data.filepath).name, "area_ratio_floor": FLOOR, "fold_cos": FOLD, "poses": {}}
for name in poses:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[name]()
    upd()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg).to_mesh()
    P = np.array([v.co[:] for v in ev.vertices])
    n1, A1 = tri_geom(P)
    ratio = A1 / np.maximum(A0, 1e-18)
    cos1 = (n1[ADJ[:, 0]] * n1[ADJ[:, 1]]).sum(axis=1)
    fold = (cos1 < FOLD) & (cos0 > 0.5)
    small = ratio < FLOOR
    bad_v = set(tris[small].ravel().tolist()) | set(tris[ADJ[fold].ravel()].ravel().tolist())
    # spikiness: distance of a vertex from the mean of its edge neighbours, in units of its mean edge length, posed minus rest
    def lap_mag(Q):
        s = np.zeros_like(Q)
        np.add.at(s, EDG[:, 0], Q[EDG[:, 1]])
        np.add.at(s, EDG[:, 1], Q[EDG[:, 0]])
        return np.linalg.norm(Q - s / DEG[:, None], axis=1) / ELEN
    spike = np.maximum(lap_mag(P) - lap_mag(rest), 0.0)
    sp_v = np.nonzero(spike > 0.5)[0]
    result_spike = {"n_spike_vertices": int(len(sp_v)), "max_spike": round(float(spike.max()), 3),
                    "spike_regions": {names[r]: int(c) for r, c in zip(*np.unique(reg[sp_v], return_counts=True))} if len(sp_v) else {},
                    "spike_vertices": [int(v) for v in sp_v]}
    result["poses"][name] = {"spikes": result_spike,
        "triangles": int(len(tris)), "area_ratio_min": round(float(ratio.min()), 4), "area_ratio_p01": round(float(np.percentile(ratio, 1)), 4),
        "n_collapsed": int(small.sum()), "n_fold_pairs": int(fold.sum()), "n_vertices_in_bad_faces": len(bad_v),
        "bad_vertices": sorted(int(v) for v in bad_v),
        "bad_regions": {names[r]: int(c) for r, c in zip(*np.unique(reg[sorted(bad_v)], return_counts=True))} if bad_v else {}}
    print("SPIKES", name, {k: v for k, v in result["poses"][name]["spikes"].items() if k != "spike_vertices"})
    print("SURFACE", name, "area min %.3f collapsed %d folds %d vertices %d" % (ratio.min(), small.sum(), fold.sum(), len(bad_v)), result["poses"][name]["bad_regions"])
reset()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
