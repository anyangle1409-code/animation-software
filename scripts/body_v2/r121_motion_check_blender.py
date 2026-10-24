"""Read-only motion check for a body_v2 blend (R120 / R121 candidates): pose the rig in a few benchmark poses with the
correctives driven, and count folded / sharp triangle pairs on the evaluated (deformed) mesh.  Nothing is saved.

Poses: rest; arm abduction 90 / 120 / 135 / 150 deg; forward flexion 90 / 150 deg; elbow flexion 120 deg; the movement benchmark's own deep squat (t = 1).
Counts per pose: edges whose two faces differ by more than 90 deg and by more than 120 deg (folds), over the whole body
and over the arm-root band (0.70-0.82 H, |x| > 0.12 m), hands and feet excluded.

usage: python3.13 r121_motion_check_blender.py -- <body.blend> <r57src> <out.json>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402  (after bpy)
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, ROOT, OUT = Path(args[0]), Path(args[1]), Path(args[2])
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(Path(__file__).resolve().parent)]
bpy.ops.wm.open_mainfile(filepath=str(SRC))
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402  (candidate arm-raise keys; no-op without them)

body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
GN = [g.name for g in body.vertex_groups]
skip_g = {i for i, g in enumerate(GN) if any(k in g for k in ("hand", "thumb", "index", "middle", "ring", "pinky",
                                                            "metacarpal", "foot", "toe", "ball"))}
SKIP = np.zeros(len(me.vertices), bool)
for v in me.vertices:
    SKIP[v.index] = sum(g.weight for g in v.groups if g.group in skip_g) > 0.3
R0 = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", R0); R0 = R0.reshape(-1, 3)
z0 = float(R0[:, 2].min()); H = float(R0[:, 2].max()) - z0
BAND = (np.abs(R0[:, 0]) > 0.12) & ((R0[:, 2] - z0) / H > 0.70) & ((R0[:, 2] - z0) / H < 0.82)
bench._reset(rig)
rest_heads = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in ("l", "r")}


def arms(abd=0.0, elb=0.0):
    bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * abd))
        fb = rig.pose.bones[f"forearm_{sd}"]; fb.rotation_mode = "XYZ"; fb.rotation_euler = (math.radians(-elb), 0.0, 0.0)
    bpy.context.view_layer.update()


def flex(deg):
    """forward raise in the sagittal plane: the local-X sign that moves the elbow forward (-y)"""
    bench._reset(rig)
    for sd in ("r", "l"):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"
        best = None
        for sg in (1.0, -1.0):
            pb.rotation_euler = (math.radians(sg * deg), 0.0, 0.0); bpy.context.view_layer.update()
            y = pb.tail.y
            if best is None or y < best[1]:
                best = (sg, y)
        pb.rotation_euler = (math.radians(best[0] * deg), 0.0, 0.0)
    bpy.context.view_layer.update()


POSES = {"rest": lambda: arms(), "abduct_90": lambda: arms(90.0), "abduct_120": lambda: arms(120.0), "abduct_135": lambda: arms(135.0),
         "abduct_150": lambda: arms(150.0),
         "flex_90": lambda: flex(90.0), "flex_150": lambda: flex(150.0),
         "elbow_120": lambda: arms(16.0, 120.0), "squat": lambda: bench.pose_squat(rig, 1.0, rest_heads)}
REP = {"source": SRC.name}
for name, fn in POSES.items():
    fn(); bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body)
    bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new(); bm.from_object(ev, bpy.context.evaluated_depsgraph_get()); bm.normal_update()
    c = {"gt35": 0, "gt90": 0, "gt120": 0, "band_gt35": 0, "band_gt90": 0, "band_gt120": 0}
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        i0, i1 = e.verts[0].index, e.verts[1].index
        if SKIP[i0] or SKIP[i1]:
            continue
        d = e.link_faces[0].normal.dot(e.link_faces[1].normal)
        for th, k in ((0.82, "gt35"), (0.0, "gt90"), (-0.5, "gt120")):
            if d < th:
                c[k] += 1
                if BAND[i0]:
                    c["band_" + k] += 1
    ang = []
    for e in bm.edges:
        if len(e.link_faces) == 2 and BAND[e.verts[0].index] and not SKIP[e.verts[0].index]:
            ang.append(e.link_faces[0].normal.dot(e.link_faces[1].normal))
    ang = np.degrees(np.arccos(np.clip(np.array(ang), -1, 1)))
    c["band_mean_angle_deg"] = round(float(ang.mean()), 2); c["band_p95_angle_deg"] = round(float(np.percentile(ang, 95)), 2)
    bm.free()
    REP[name] = c
    print("MOTION", name, json.dumps(c), flush=True)
bench._reset(rig)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(REP, indent=1))
