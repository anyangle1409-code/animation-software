"""Add non-destructive V15f ring/pinky fold hotspot selections/guides.

Run inside:
  HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend

This script must not move geometry. It creates diagnostic vertex groups from
current V13e-derived surface dihedral angles and PIP/DIP proximity, then saves
the same Blend.

Groups:
  V15F_<DIGIT>_<SIDE>_GT35/GT50/GT75/GT100
  V15F_<DIGIT>_<SIDE>_PIP_HOT
  V15F_<DIGIT>_<SIDE>_DIP_HOT

It also creates V15F_HOTSPOT_GUIDES empties at strongest local folds.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
REPORT = ROOT / "reports" / "prepare_v15f_hotspots.json"
BODY = "Mike_Freeman"
RIG = "HomeGymPT_Male_Rig"
DIGITS = ("ring", "pinky")
SIDES = ("L", "R")
THRESHOLDS = (35, 50, 75, 100)

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
blend = Path(args[0]).resolve() if args else DEFAULT_BLEND
if not blend.is_file():
    raise SystemExit(f"Missing V15f Blend: {blend}")

bpy.ops.wm.open_mainfile(filepath=str(blend))
body = bpy.data.objects[BODY]
arm = bpy.data.objects[RIG]
mesh = body.data

before = [v.co.copy() for v in mesh.vertices]

bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bm.normal_update()

deform = bm.verts.layers.deform.active
groups = {g.name: g.index for g in body.vertex_groups}

def members(name):
    gid = groups.get(name)
    if gid is None:
        raise RuntimeError(f"Missing diagnostic group {name}")
    return {v for v in bm.verts if v[deform].get(gid, 0.0) > 0.5}

def chain_for(digit, side):
    prefix = f"DEF-f_{digit}."
    bones = arm.data.bones
    return [bones[prefix + "01." + side].head_local.copy()] + [
        bones[prefix + f"{i:02d}." + side].tail_local.copy() for i in (1, 2, 3)
    ]

def project_info(point, chain):
    best = None
    travelled = 0.0
    for a, b in zip(chain[:-1], chain[1:]):
        ab = b - a
        length = ab.length
        if length <= 1e-12:
            continue
        t = max(0.0, min(1.0, (point - a).dot(ab) / (length * length)))
        q = a + t * ab
        d = (point - q).length_squared
        item = (d, travelled + t * length, ab.normalized())
        if best is None or d < best[0]:
            best = item
        travelled += length
    return (best[1], best[2]) if best else (0.0, Vector((1, 0, 0)))

def project_arc(point, chain):
    return project_info(point, chain)[0]

def replace_group(name, indices):
    old = body.vertex_groups.get(name)
    if old is not None:
        body.vertex_groups.remove(old)
    group = body.vertex_groups.new(name=name)
    if indices:
        group.add(sorted(indices), 1.0, "REPLACE")
    return len(indices)

guide = bpy.data.collections.get("V15F_HOTSPOT_GUIDES")
if guide is not None:
    for obj in list(guide.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(guide)
guide = bpy.data.collections.new("V15F_HOTSPOT_GUIDES")
bpy.context.scene.collection.children.link(guide)

def add_guide(name, co, size=0.004):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = size
    obj.location = co
    obj.hide_render = True
    obj.show_in_front = True
    guide.objects.link(obj)

report = {"blend": blend.name, "digits": {}, "geometry_max_move_mm": 0.0}

for digit in DIGITS:
    for side in SIDES:
        key = f"{digit.upper()}_{side}"
        owned = members("V15_" + key)
        core = members("V15_" + key + "_CORE")
        chain = chain_for(digit, side)
        pip_arc = (chain[1] - chain[0]).length
        dip_arc = pip_arc + (chain[2] - chain[1]).length

        threshold_vertices = {t: set() for t in THRESHOLDS}
        ranked = []
        pip_hot = set()
        dip_hot = set()
        band_gt35 = set()
        long_gt35 = set()

        for edge in bm.edges:
            if len(edge.link_faces) != 2:
                continue
            if any(v not in owned for v in edge.verts):
                continue
            dot = max(-1.0, min(1.0, edge.link_faces[0].normal.dot(edge.link_faces[1].normal)))
            angle = math.degrees(math.acos(dot))
            if angle < THRESHOLDS[0]:
                continue

            midpoint = (edge.verts[0].co + edge.verts[1].co) * 0.5
            arc, tangent = project_info(midpoint, chain)
            endpoint_indices = {v.index for v in edge.verts}
            edge_vec = edge.verts[1].co - edge.verts[0].co
            axial_alignment = (
                abs(edge_vec.normalized().dot(tangent))
                if edge_vec.length > 1e-12 else 0.0
            )

            for threshold in THRESHOLDS:
                if angle > threshold:
                    threshold_vertices[threshold].update(endpoint_indices)

            if angle > 35:
                if axial_alignment < 0.45:
                    band_gt35.update(endpoint_indices)
                elif axial_alignment > 0.70:
                    long_gt35.update(endpoint_indices)

            if edge.verts[0] in core and edge.verts[1] in core:
                if abs(arc - pip_arc) <= 0.008:
                    pip_hot.update(endpoint_indices)
                if abs(arc - dip_arc) <= 0.008:
                    dip_hot.update(endpoint_indices)

            ranked.append({
                "angle_deg": angle,
                "edge_length_mm": edge.calc_length() * 1000.0,
                "midpoint": [float(x) for x in midpoint],
                "arc_mm": arc * 1000.0,
                "axial_alignment": axial_alignment,
                "orientation": (
                    "cross_band" if axial_alignment < 0.45 else
                    "longitudinal" if axial_alignment > 0.70 else
                    "diagonal"
                ),
                "near_joint": (
                    "PIP" if abs(arc - pip_arc) <= 0.008 else
                    "DIP" if abs(arc - dip_arc) <= 0.008 else
                    "shaft"
                ),
                "vertices": sorted(endpoint_indices),
            })

        counts = {}
        for threshold in THRESHOLDS:
            name = f"V15F_{key}_GT{threshold}"
            counts[name] = replace_group(name, threshold_vertices[threshold])
        counts[f"V15F_{key}_PIP_HOT"] = replace_group(f"V15F_{key}_PIP_HOT", pip_hot)
        counts[f"V15F_{key}_DIP_HOT"] = replace_group(f"V15F_{key}_DIP_HOT", dip_hot)
        counts[f"V15F_{key}_BAND_GT35"] = replace_group(
            f"V15F_{key}_BAND_GT35", band_gt35
        )
        counts[f"V15F_{key}_LONG_GT35"] = replace_group(
            f"V15F_{key}_LONG_GT35", long_gt35
        )

        ranked.sort(key=lambda x: (x["angle_deg"], x["edge_length_mm"]), reverse=True)
        for i, item in enumerate(ranked[:12], 1):
            add_guide(
                f"V15F_{key}_HOT_{i:02d}_{item['angle_deg']:.1f}deg",
                Vector(item["midpoint"]),
                0.0035 if item["angle_deg"] < 100 else 0.005,
            )

        report["digits"][key] = {
            "owned_vertices": len(owned),
            "core_vertices": len(core),
            "pip_arc_mm": pip_arc * 1000.0,
            "dip_arc_mm": dip_arc * 1000.0,
            "group_counts": counts,
            "edge_counts": {
                **{
                    f"gt_{threshold}": sum(item["angle_deg"] > threshold for item in ranked)
                    for threshold in THRESHOLDS
                },
                "gt35_cross_band": sum(
                    item["angle_deg"] > 35 and item["orientation"] == "cross_band"
                    for item in ranked
                ),
                "gt35_longitudinal": sum(
                    item["angle_deg"] > 35 and item["orientation"] == "longitudinal"
                    for item in ranked
                ),
                "gt35_diagonal": sum(
                    item["angle_deg"] > 35 and item["orientation"] == "diagonal"
                    for item in ranked
                ),
            },
            "top_edges": ranked[:20],
        }

bm.free()

after = [v.co.copy() for v in mesh.vertices]
max_move = max(((a - b).length for a, b in zip(before, after)), default=0.0)
report["geometry_max_move_mm"] = max_move * 1000.0
if max_move > 1e-12:
    raise RuntimeError(f"Hotspot preparation moved geometry by {max_move*1000:.9f} mm")

body["v15f_hotspot_note"] = (
    "Diagnostic only. Ring/pinky V15f local patch preparation; geometry unchanged."
)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("V15F_HOTSPOTS", json.dumps({
    "blend": blend.name,
    "geometry_max_move_mm": report["geometry_max_move_mm"],
    "digits": {
        key: value["edge_counts"]
        for key, value in report["digits"].items()
    }
}, indent=2), flush=True)
