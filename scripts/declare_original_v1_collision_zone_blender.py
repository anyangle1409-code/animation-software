"""Declare (before any edit) the self-intersection zone of a posed candidate in the axilla-pit declaration format (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/declare_original_v1_collision_zone_blender.py -- <out declaration.json> <target_rev> <pose[,pose...]> <fraction[,fraction...]> [rings=2]

Rule (documented, deterministic): for every listed pose and arc fraction (the pose is replayed continuously from rest with the same swing/twist
interpolation as the arc audit; fraction 1 is the final pose) the evaluated bare mesh is tested with a polygon BVH overlap (pairs sharing a vertex
excluded - the pose-test definition). Vertices of the LEFT side (x <= 0) that take part in any intersecting pair are collected, dilated by <rings> mesh
rings inside the shoulder/torso/arm/neck regions, and the right side is the exact mirror. The seed triangles are the triangles of the intersecting polygons.
The output is accepted by scripts/optimize_original_v1_shoulder_corrective.py --mask-file and by scripts/apply_original_v1_axilla_delta_blender.py.
"""
import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
out, target, poses, fractions = Path(args[0]), args[1], args[2].split(","), [float(x) for x in args[3].split(",")]
rings = int(args[4]) if len(args) > 4 else 2
if out.exists():
    raise SystemExit("refusing to overwrite " + str(out))
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
me = body.data
me.calc_loop_triangles()
rest = np.array([v.co[:] for v in me.vertices])
nV = len(rest)
polys = [tuple(p.vertices) for p in me.polygons]
psets = [set(p) for p in polys]
tri_by_poly = {}
for t in me.loop_triangles:
    tri_by_poly.setdefault(t.polygon_index, []).append(t.index)
names = json.loads(bpy.context.scene["hgpt_region_names"])
reg = np.array([d.value for d in me.attributes["hgpt_region"].data])
okreg = np.isin(reg, [names.index(n) for n in ("shoulder", "torso", "arm", "neck")])
edges = np.array([e.vertices[:] for e in me.edges])


def swing_twist(q):
    v = Vector((q.x, q.y, q.z))
    proj = Vector((0, 1, 0)) * v.dot(Vector((0, 1, 0)))
    tw = Quaternion((q.w, proj.x, proj.y, proj.z))
    if tw.magnitude < 1e-12:
        tw = Quaternion((1, 0, 0, 0))
    tw.normalize()
    return q @ tw.inverted(), tw


hit_vertices, seed_polys, per_pose = set(), set(), {}
for name in poses:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[name]()
    upd()
    final = {p.name: (p.matrix_basis.to_quaternion(), p.matrix_basis.to_translation()) for p in rig.pose.bones}
    for f in fractions:
        for p in rig.pose.bones:
            q, t = final[p.name]
            sw, tw = swing_twist(q)
            ang = (2.0 * math.atan2(tw.y, tw.w) + math.pi) % (2.0 * math.pi) - math.pi
            qf = Quaternion((1, 0, 0, 0)).slerp(sw, f) @ Quaternion((0.0, 1.0, 0.0), f * ang)
            p.matrix_basis = Matrix.Translation(t * f) @ qf.to_matrix().to_4x4()
        upd()
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        V = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])
        tree = BVHTree.FromPolygons([Vector(p) for p in V], polys)
        pairs = {tuple(sorted((a, b))) for a, b in tree.overlap(tree) if a != b and not (psets[a] & psets[b])}
        n = 0
        ALLOWED = {names.index(x) for x in ("shoulder", "torso", "neck")}
        for a, b in pairs:
            if not ({int(reg[polys[a][0]]), int(reg[polys[b][0]])} & ALLOWED):
                continue                                   # keep only pairs involving shoulder/torso/neck skin (arm-arm contacts such as the elbow are not this zone)
            mid_x = float(V[list(polys[a]) + list(polys[b])][:, 0].mean())
            if mid_x > 1e-8:
                continue                                   # right side: covered by the mirror
            n += 1
            seed_polys.update((a, b))
            hit_vertices.update(polys[a])
            hit_vertices.update(polys[b])
        per_pose[f"{name}@{f:g}"] = {"pairs_total": len(pairs), "pairs_left": n}
reset()
left = np.zeros(nV, bool)
left[list(hit_vertices)] = True
left &= okreg & (rest[:, 0] <= 1e-8)
for _ in range(rings):
    nxt = left.copy()
    nxt[edges[left[edges[:, 0]], 1]] = True
    nxt[edges[left[edges[:, 1]], 0]] = True
    left = nxt & okreg & (rest[:, 0] <= 1e-8)
key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
mir = np.array([key[tuple(np.round(rest[i] * [-1, 1, 1], 5))] for i in range(nV)])
L = np.nonzero(left)[0]
R = mir[L[rest[L, 0] < -1e-8]]
seed_tris = sorted({t for pi in seed_polys for t in tri_by_poly.get(pi, [])})
tri_v = np.array([t.vertices[:] for t in me.loop_triangles])
mirror_tris = sorted({int(i) for i in seed_tris} | {int(np.nonzero((np.sort(mir[tri_v], axis=1) == np.sort(mir[tri_v[i]])[None]).all(axis=1))[0][0]) for i in seed_tris})
src_path = Path(bpy.data.filepath)
rec = {"schema_version": 1, "declared_utc": datetime.now(timezone.utc).isoformat(), "declared_before_edit": True, "target_revision": target,
       "source_candidate": src_path.name, "source_candidate_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(),
       "selection_rule": f"left-side vertices of every self-intersecting polygon pair (pose-test definition) over poses {poses} at arc fractions {fractions}, dilated by {rings} mesh rings inside shoulder/torso/arm/neck; right = exact mirror",
       "diagnostic_parameters": {"poses": poses, "fractions": fractions, "rings": rings, "intersection_counts": per_pose},
       "seed_triangle_ids": [int(i) for i in seed_tris], "mirror_closed_triangle_ids": mirror_tris,
       "left_owned_vertex_ids": [int(v) for v in L], "mirror_of_strict_left_vertex_ids": sorted(int(v) for v in R), "vertex_count_total": int(len(L) + len(R)),
       "ids_sha256": hashlib.sha256(np.asarray(L, dtype="<i8").tobytes()).hexdigest(),
       "rest_bbox_min_m": [round(float(x), 6) for x in rest[L].min(axis=0)], "rest_bbox_max_m": [round(float(x), 6) for x in rest[L].max(axis=0)],
       "allowed_change": "shoulder-corrective shape-key displacement of the declared mirror-closed vertices only; no bone, bind, weight, topology, pose-definition, threshold, baseline or other-vertex change",
       "production_approved": False}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("COLLISION ZONE DECLARED", out, "left", len(L), "total", len(L) + len(R), "seed triangles", len(seed_tris), "intersections", {k: v["pairs_total"] for k, v in per_pose.items()})
