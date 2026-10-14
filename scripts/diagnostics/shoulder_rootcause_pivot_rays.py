"""Shoulder root-cause diagnostic (14 Oct 2026; docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md). Diagnostic only."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parents[2])
import sys
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT + "/scripts/anatomy_fit")
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=ROOT + "/ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend")
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
res = correction.build_corrected_scene(); rig, body = res["runtime"], res["body"]
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
bench._reset(rig); V, F = bench._evaluated(body)
tree = BVHTree.FromPolygons(V, F, all_triangles=True)
for s, sx in (("r", 1), ("l", -1)):
    for bone in (f"upperarm_{s}", f"scapula_{s}", f"clavicle_{s}"):
        b = rig.data.bones[bone]
        print("BONE", bone, "head", [round(c*1000) for c in b.head_local], "tail", [round(c*1000) for c in b.tail_local])
    h = rig.data.bones[f"upperarm_{s}"].head_local
    d = {}
    for name, v in (("lateral", (sx, 0, 0)), ("superior", (0, 0, 1)), ("anterior", (0, -1, 0)), ("posterior", (0, 1, 0)), ("medial", (-sx, 0, 0)), ("inferior", (0, 0, -1))):
        hit = tree.ray_cast(h, Vector(v))
        d[name] = round(hit[3] * 1000, 1) if hit[0] else None
    print("RAY", s, d)
    # skin cross-section at the joint height: extent of the arm/shoulder ring in y at the head's x,z
    ring = [p for p in V if abs(p.z - h.z) < 0.01 and abs(p.x - h.x) < 0.01]
    if ring: print("SLICE", s, "y range mm", round(min(p.y for p in ring)*1000), round(max(p.y for p in ring)*1000), "head y", round(h.y*1000))
