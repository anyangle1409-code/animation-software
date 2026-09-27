"""Generate the clean Home Gym PT ORIGINAL v1 scaffold in Blender.

Prerequisite:
  Run scripts/init_original_v1_blender.py first, or open the resulting
  ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend.

This script recreates the project-authored procedural body specification pinned
at e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62 from numeric data only.

It does NOT import:
- MakeHuman geometry/data;
- V5/V6/V7/V8/CORNER_FINAL;
- V9-V15 candidates;
- legacy UVs, weights, materials, inverse bind matrices, or source rig transforms.

The scaffold is not a production character. It is a clean starting surface for
substantial ORIGINAL v1 topology/anatomy work and later canonical-v4 binding.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ORIGINAL_V1_WORK"
BLEND = OUT_DIR / "HomeGymPT_Male_ORIGINAL_v1.blend"
PROVENANCE = OUT_DIR / "ORIGINAL_V1_PROVENANCE.json"

PINNED_COMMIT = "e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62"
PROFILE_BLOB = "ee56a49bfb2e32530520fd1811ed9427460256bd"
MESH_BLOB = "0216035a6574a0b753f8716f49e603967923f68f"
RIG_COMMIT = "287f72c6a6ac9b1dcd771946ef548d77a40b8ea1"
RIG_BLOB = "5c0182ae6db57e8de99547aa96d80216105a36ba"

FINGERS = ("thumb", "index", "middle", "ring", "pinky")


def v(x: float, y: float, z: float) -> Vector:
    return Vector((x, y, z))


def project_to_blender(p: Vector) -> Vector:
    # Project coordinates: +Y up, +Z forward.
    # Blender scaffold: +Z up, -Y forward. This is a proper rotation (det +1).
    return Vector((p.x, -p.z, p.y))


def mirror_project(p: Vector) -> Vector:
    return Vector((-p.x, p.y, p.z))


def bone(name, parent, head, tail):
    return {"name": name, "parent": parent, "head": v(*head), "tail": v(*tail)}


CENTRE = [
    bone("root", None, (0, 0, 0), (0, 0.2, 0)),
    bone("pelvis", "root", (0, 0.95, 0), (0, 1.03, 0)),
    bone("spine_01", "pelvis", (0, 1.03, 0), (0, 1.15, 0)),
    bone("spine_02", "spine_01", (0, 1.15, 0), (0, 1.27, 0)),
    bone("spine_03", "spine_02", (0, 1.27, 0), (0, 1.42, 0)),
    bone("neck", "spine_03", (0, 1.42, 0), (0, 1.52, 0)),
    bone("head", "neck", (0, 1.52, 0), (0, 1.75, 0)),
]

LEFT_CORE = [
    bone("clavicle_l", "spine_03", (-0.02, 1.42, 0.012), (-0.17, 1.44, 0)),
    bone("upperarm_l", "clavicle_l", (-0.17, 1.44, 0), (-0.17, 1.14, 0)),
    bone("forearm_l", "upperarm_l", (-0.17, 1.14, 0), (-0.17, 0.88, 0)),
    bone("hand_l", "forearm_l", (-0.17, 0.88, 0), (-0.17, 0.79, 0)),
    bone("thigh_l", "pelvis", (-0.09, 0.92, 0), (-0.082, 0.5, 0)),
    bone("shin_l", "thigh_l", (-0.082, 0.5, 0), (-0.082, 0.08, 0)),
    bone("foot_l", "shin_l", (-0.082, 0.08, 0), (-0.082, 0.025, 0.14)),
    bone("toe_l", "foot_l", (-0.082, 0.025, 0.14), (-0.082, 0.02, 0.21)),
]

FINGER_SPECS = {
    "thumb": {
        "knuckle": (-0.163, 0.852, 0.022),
        "direction": (0.06, -0.72, 0.69),
        "segments": (0.042, 0.032, 0.024),
    },
    "index": {
        "knuckle": (-0.171, 0.789, 0.032),
        "direction": (-0.01, -1, 0.02),
        "segments": (0.042, 0.026, 0.02),
    },
    "middle": {
        "knuckle": (-0.172, 0.788, 0.011),
        "direction": (0, -1, 0),
        "segments": (0.046, 0.028, 0.021),
    },
    "ring": {
        "knuckle": (-0.171, 0.789, -0.01),
        "direction": (0.005, -1, -0.015),
        "segments": (0.042, 0.026, 0.02),
    },
    "pinky": {
        "knuckle": (-0.168, 0.792, -0.03),
        "direction": (0.01, -1, -0.03),
        "segments": (0.034, 0.021, 0.017),
    },
}


def finger_bones_left():
    out = []
    for finger, spec in FINGER_SPECS.items():
        head = v(*spec["knuckle"])
        direction = v(*spec["direction"]).normalized()
        for index, length in enumerate(spec["segments"], start=1):
            tail = head + direction * length
            out.append({
                "name": f"{finger}_0{index}_l",
                "parent": "hand_l" if index == 1 else f"{finger}_0{index - 1}_l",
                "head": head.copy(),
                "tail": tail.copy(),
            })
            head = tail
    return out


def mirrored_bone(source):
    def swap(name):
        return f"{name[:-2]}_r" if name and name.endswith("_l") else name
    return {
        "name": swap(source["name"]),
        "parent": swap(source["parent"]),
        "head": mirror_project(source["head"]),
        "tail": mirror_project(source["tail"]),
    }


LEFT_ALL = LEFT_CORE + finger_bones_left()
BONES = CENTRE + LEFT_ALL + [mirrored_bone(x) for x in LEFT_ALL]
BONE_BY_NAME = {x["name"]: x for x in BONES}


def ring(t, rx, rz, oz=0.0, ox=0.0):
    return {"t": t, "rx": rx, "rz": rz, "oz": oz, "ox": ox}


TRUNK = {
    "id": "trunk", "sides": 20, "domeStart": 0.28, "domeEnd": 0.6,
    "parts": [
        {"bone": "pelvis", "rings": [
            ring(-1.15, 0.121, 0.09, -0.008),
            ring(-0.95, 0.148, 0.102, -0.016),
            ring(-0.6, 0.167, 0.111, -0.016),
            ring(-0.1, 0.166, 0.108, -0.006),
            ring(0.45, 0.157, 0.102),
            ring(0.95, 0.15, 0.1, 0.003),
        ]},
        {"bone": "spine_01", "blend": 0.06, "rings": [
            ring(0.1, 0.147, 0.1, 0.004),
            ring(0.45, 0.141, 0.099, 0.006),
            ring(0.8, 0.139, 0.1, 0.006),
        ]},
        {"bone": "spine_02", "blend": 0.06, "rings": [
            ring(0.05, 0.142, 0.103, 0.005),
            ring(0.45, 0.153, 0.111, 0.002),
            ring(0.85, 0.166, 0.117),
        ]},
        {"bone": "spine_03", "blend": 0.06, "rings": [
            ring(0.05, 0.171, 0.119, -0.002),
            ring(0.35, 0.181, 0.121, -0.004),
            ring(0.62, 0.183, 0.114, -0.009),
            ring(0.88, 0.169, 0.098, -0.015),
        ]},
        {"bone": "neck", "blend": 0.05, "rings": [
            ring(0.02, 0.107, 0.088, -0.016),
            ring(0.3, 0.068, 0.066, -0.008),
            ring(0.62, 0.059, 0.06, -0.005),
            ring(0.9, 0.057, 0.059, -0.003),
        ]},
        {"bone": "head", "blend": 0.035, "rings": [
            ring(0.02, 0.064, 0.07, 0.006),
            ring(0.12, 0.073, 0.086, 0.018),
            ring(0.26, 0.079, 0.096, 0.021),
            ring(0.42, 0.083, 0.102, 0.016),
            ring(0.56, 0.084, 0.103, 0.009),
            ring(0.68, 0.081, 0.099, 0.002),
            ring(0.78, 0.073, 0.09, -0.005),
        ]},
    ],
}


def side_chains(side):
    suffix = side
    clavicle = {
        "id": f"clavicle_{suffix}", "sides": 10,
        "parts": [{"bone": f"clavicle_{suffix}", "blend": 0.03, "rings": [
            ring(0.15, 0.03, 0.046, -0.012),
            ring(0.6, 0.028, 0.042, -0.007),
            ring(0.92, 0.032, 0.046, -0.002),
        ]}],
    }
    arm = {
        "id": f"arm_{suffix}", "sides": 14, "domeStart": 0.4, "domeEnd": 0.45,
        "parts": [
            {"bone": f"upperarm_{suffix}", "blend": 0.05, "rings": [
                ring(-0.06, 0.051, 0.05, -0.002),
                ring(0.02, 0.055, 0.054, 0.002),
                ring(0.15, 0.054, 0.053, 0.004),
                ring(0.4, 0.049, 0.051, 0.005),
                ring(0.68, 0.043, 0.046, 0.003),
                ring(0.92, 0.038, 0.04),
            ]},
            {"bone": f"forearm_{suffix}", "blend": 0.05, "rings": [
                ring(0.06, 0.038, 0.041, 0.001),
                ring(0.22, 0.044, 0.045, 0.002),
                ring(0.5, 0.037, 0.038, 0.001),
                ring(0.75, 0.03, 0.03),
                ring(0.95, 0.026, 0.025),
            ]},
            {"bone": f"hand_{suffix}", "blend": 0.025, "rings": [
                ring(0.08, 0.022, 0.031, 0.003),
                ring(0.4, 0.021, 0.038, 0.004),
                ring(0.78, 0.019, 0.039, 0.004),
                ring(1.0, 0.017, 0.035, 0.002),
            ]},
        ],
    }
    leg = {
        "id": f"leg_{suffix}", "sides": 16, "domeStart": 0.5, "domeEnd": 0.4,
        "parts": [
            {"bone": f"thigh_{suffix}", "blend": 0.07, "rings": [
                ring(-0.08, 0.086, 0.097, -0.012),
                ring(0.08, 0.089, 0.098, -0.008),
                ring(0.35, 0.081, 0.088, -0.002),
                ring(0.62, 0.07, 0.076, 0.001),
                ring(0.87, 0.059, 0.061, 0.002),
            ]},
            {"bone": f"shin_{suffix}", "blend": 0.06, "rings": [
                ring(0.06, 0.053, 0.058, -0.002),
                ring(0.17, 0.056, 0.063, -0.014),
                ring(0.36, 0.052, 0.06, -0.016),
                ring(0.6, 0.044, 0.047, -0.01),
                ring(0.84, 0.035, 0.035, -0.002),
                ring(0.99, 0.032, 0.031, 0.002),
            ]},
        ],
    }
    foot = {
        "id": f"foot_{suffix}", "sides": 12, "domeStart": 0.75, "domeEnd": 0.9,
        "parts": [
            {"bone": f"foot_{suffix}", "blend": 0.035, "rings": [
                ring(-0.4, 0.033, 0.035, 0.029),
                ring(-0.18, 0.038, 0.044, 0.022),
                ring(0.12, 0.04, 0.049, 0.013),
                ring(0.5, 0.042, 0.044, 0.008),
                ring(0.85, 0.044, 0.038, 0.005),
            ]},
            {"bone": f"toe_{suffix}", "blend": 0.022, "rings": [
                ring(0.05, 0.043, 0.033, 0.007),
                ring(0.55, 0.041, 0.029, 0.006),
                ring(0.95, 0.033, 0.023, 0.005),
            ]},
        ],
    }
    radii = {
        "thumb": (0.0125, 0.011, 0.0092),
        "index": (0.0102, 0.0092, 0.008),
        "middle": (0.0105, 0.0095, 0.0082),
        "ring": (0.0099, 0.009, 0.0077),
        "pinky": (0.009, 0.008, 0.0069),
    }
    fingers = []
    for finger in FINGERS:
        parts = []
        for index, radius in enumerate(radii[finger], start=1):
            parts.append({
                "bone": f"{finger}_0{index}_{suffix}",
                "blend": 0.009,
                "rings": [
                    ring(0.04, radius, radius * 0.95),
                    ring(0.55, radius * 0.97, radius * 0.92),
                    ring(0.96, radius * 0.9, radius * 0.86),
                ],
            })
        fingers.append({
            "id": f"{finger}_{suffix}",
            "sides": 7,
            "domeStart": 0.5,
            "domeEnd": 0.95,
            "parts": parts,
        })
    return [clavicle, arm, leg, foot, *fingers]


BODY_CHAINS = [TRUNK, *side_chains("l"), *side_chains("r")]
BODY_BLOBS = [
    {"bone": "head", "centre": (0, 0.088, 0.11), "radii": (0.0095, 0.032, 0.014)},
    {"bone": "head", "centre": (0, 0.024, 0.086), "radii": (0.031, 0.019, 0.016)},
    {"bone": "head", "centre": (-0.077, 0.078, -0.004), "radii": (0.009, 0.023, 0.014)},
    {"bone": "head", "centre": (0.077, 0.078, -0.004), "radii": (0.009, 0.023, 0.014)},
    {"bone": "hand_l", "centre": (0, 0.03, 0.03), "radii": (0.017, 0.028, 0.014)},
    {"bone": "hand_r", "centre": (0, 0.03, 0.03), "radii": (0.017, 0.028, 0.014)},
]


def frame_for(b):
    y = (b["tail"] - b["head"]).normalized()
    forward = v(0, 0, 1)
    up = v(0, 1, 0)
    reference = up if abs(y.dot(forward)) > 0.985 else forward
    z = (reference - y * y.dot(reference)).normalized()
    x = y.cross(z).normalized()
    return x, y, z


def bone_length(name):
    b = BONE_BY_NAME[name]
    return (b["tail"] - b["head"]).length


def local_to_project(name, local):
    b = BONE_BY_NAME[name]
    x, y, z = frame_for(b)
    return b["head"] + x * local.x + y * local.y + z * local.z


def dome(source, height, direction, length):
    radius = (source["rx"] + source["rz"]) / 2
    added = []
    for step in (3, 2, 1):
        angle = (step / 3) * (math.pi / 2)
        entry = dict(source)
        entry["t"] = source["t"] + direction * height * radius * math.sin(angle) / max(1e-4, length)
        entry["rx"] = source["rx"] * math.cos(angle)
        entry["rz"] = source["rz"] * math.cos(angle)
        added.append(entry)
    return added


def rings_with_domes(chain, rings, length, part_index, part_count):
    ordered = sorted((dict(x) for x in rings), key=lambda x: x["t"])
    out = []
    if chain.get("domeStart") and part_index == 0:
        out.extend(dome(ordered[0], chain["domeStart"], -1, length))
    out.extend(ordered)
    if chain.get("domeEnd") and part_index == part_count - 1:
        out.extend(reversed(dome(ordered[-1], chain["domeEnd"], 1, length)))
    return out


def place_chain(chain):
    parts = [x for x in chain["parts"] if x["bone"] in BONE_BY_NAME]
    placed = []
    for part_index, part in enumerate(parts):
        name = part["bone"]
        b = BONE_BY_NAME[name]
        previous = parts[part_index - 1] if part_index > 0 else None
        nxt = parts[part_index + 1] if part_index < len(parts) - 1 else None
        parent_name = previous["bone"] if previous else (
            b["parent"] if b["parent"] and b["parent"] != "root" else None
        )
        head_blend = part.get("blend", 0.0)
        tail_blend = nxt.get("blend", 0.0) if nxt else 0.0
        length = bone_length(name)
        for entry in rings_with_domes(chain, part["rings"], length, part_index, len(parts)):
            distance = entry["t"] * length
            other = None
            own_weight = 1.0
            if parent_name and head_blend > 0 and distance < head_blend:
                other = parent_name
                own_weight = max(0.0, min(1.0, 0.5 + 0.5 * distance / head_blend))
            elif nxt and tail_blend > 0 and length - distance < tail_blend:
                other = nxt["bone"]
                own_weight = max(0.0, min(1.0, 0.5 + 0.5 * (length - distance) / tail_blend))
            placed.append((name, entry, other, own_weight))
    return placed


vertices = []
faces = []
weights = []


def add_vertex(project_point, vertex_weights):
    vertices.append(tuple(project_to_blender(project_point)))
    weights.append(vertex_weights)
    return len(vertices) - 1


for chain in BODY_CHAINS:
    placed = place_chain(chain)
    if len(placed) < 2:
        continue
    sides = chain.get("sides", 16)
    starts = []
    for name, entry, other, own_weight in placed:
        starts.append(len(vertices))
        length = bone_length(name)
        for side in range(sides):
            angle = (side / sides) * math.pi * 2
            local = v(
                entry.get("ox", 0.0) + entry["rx"] * math.cos(angle),
                entry["t"] * length,
                entry.get("oz", 0.0) + entry["rz"] * math.sin(angle),
            )
            vw = {name: own_weight}
            if other and own_weight < 1:
                vw[other] = 1 - own_weight
            add_vertex(local_to_project(name, local), vw)

    for rindex in range(len(placed) - 1):
        a = starts[rindex]
        b = starts[rindex + 1]
        for side in range(sides):
            nxt = (side + 1) % sides
            faces.append((a + side, b + side, b + nxt))
            faces.append((a + side, b + nxt, a + nxt))

    def cap(which, front):
        name, entry, other, own_weight = placed[which]
        if max(entry["rx"], entry["rz"]) < 0.0015:
            return
        length = bone_length(name)
        local = v(entry.get("ox", 0.0), entry["t"] * length, entry.get("oz", 0.0))
        vw = {name: own_weight}
        if other and own_weight < 1:
            vw[other] = 1 - own_weight
        centre = add_vertex(local_to_project(name, local), vw)
        start = starts[which]
        for side in range(sides):
            nxt = (side + 1) % sides
            faces.append((centre, start + side, start + nxt) if front else
                         (centre, start + nxt, start + side))

    cap(0, True)
    cap(-1, False)


for blob in BODY_BLOBS:
    name = blob["bone"]
    stacks = 8
    slices = 12
    start = len(vertices)
    cx, cy, cz = blob["centre"]
    rx, ry, rz = blob["radii"]
    for stack in range(stacks + 1):
        phi = (stack / stacks) * math.pi
        for sl in range(slices):
            theta = (sl / slices) * math.pi * 2
            local = v(
                cx + rx * math.sin(phi) * math.cos(theta),
                cy + ry * math.cos(phi),
                cz + rz * math.sin(phi) * math.sin(theta),
            )
            add_vertex(local_to_project(name, local), {name: 1.0})
    for stack in range(stacks):
        for sl in range(slices):
            nxt = (sl + 1) % slices
            a = start + stack * slices + sl
            b = start + (stack + 1) * slices + sl
            c = start + (stack + 1) * slices + nxt
            d = start + stack * slices + nxt
            faces.append((a, c, b))
            faces.append((a, d, c))


scene = bpy.context.scene
if not scene.get("hgpt_clean_room"):
    raise RuntimeError("Refusing to generate scaffold: scene is not marked hgpt_clean_room.")
if scene.get("hgpt_legacy_geometry_imported"):
    raise RuntimeError("Refusing to generate scaffold: scene says legacy geometry was imported.")

body_collection = bpy.data.collections.get("ORIGINAL_BODY")
rig_collection = bpy.data.collections.get("ORIGINAL_RIG")
if body_collection is None or rig_collection is None:
    raise RuntimeError("Clean-room collections missing. Run init_original_v1_blender.py first.")

for name in ("HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD", "HGPT_CLEAN_HISTORICAL_REFERENCE_RIG"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

mesh = bpy.data.meshes.new("HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD_MESH")
mesh.from_pydata(vertices, [], faces)
mesh.update(calc_edges=True)
body = bpy.data.objects.new("HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD", mesh)
body_collection.objects.link(body)

body["hgpt_clean_scaffold"] = True
body["hgpt_production_ready"] = False
body["hgpt_geometry_source"] = "project-authored numeric scaffold"
body["hgpt_pinned_profile_commit"] = PINNED_COMMIT
body["hgpt_profile_blob_sha"] = PROFILE_BLOB
body["hgpt_historical_mesh_algorithm_blob_sha"] = MESH_BLOB
body["hgpt_third_party_geometry_imported"] = False

material = bpy.data.materials.get("HGPT_ORIGINAL_SCAFFOLD_MAT")
if material is None:
    material = bpy.data.materials.new("HGPT_ORIGINAL_SCAFFOLD_MAT")
    material.diffuse_color = (0.55, 0.58, 0.62, 1.0)
    material.roughness = 0.7
body.data.materials.append(material)

# Historical clean reference armature. It is deliberately NOT canonical v4.
arm_data = bpy.data.armatures.new("HGPT_CLEAN_HISTORICAL_REFERENCE_ARMATURE")
arm_obj = bpy.data.objects.new("HGPT_CLEAN_HISTORICAL_REFERENCE_RIG", arm_data)
rig_collection.objects.link(arm_obj)
arm_obj["hgpt_reference_only"] = True
arm_obj["hgpt_rig_source_commit"] = RIG_COMMIT
arm_obj["hgpt_rig_blob_sha"] = RIG_BLOB
arm_obj["hgpt_target_replacement"] = "hgpt_canonical_v4_original"

bpy.context.view_layer.objects.active = arm_obj
arm_obj.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
edit = {}
for item in BONES:
    eb = arm_data.edit_bones.new(item["name"])
    eb.head = project_to_blender(item["head"])
    eb.tail = project_to_blender(item["tail"])
    if (eb.tail - eb.head).length < 1e-5:
        eb.tail.z += 0.01
    edit[item["name"]] = eb
for item in BONES:
    parent = item["parent"]
    if parent:
        edit[item["name"]].parent = edit[parent]
        edit[item["name"]].use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")
arm_obj.select_set(False)

groups = {name: body.vertex_groups.new(name=name) for name in BONE_BY_NAME}
for index, row in enumerate(weights):
    total = sum(row.values())
    if total <= 0:
        continue
    for name, value in row.items():
        groups[name].add([index], value / total, "REPLACE")

modifier = body.modifiers.new("HGPT Clean Historical Scaffold Armature", "ARMATURE")
modifier.object = arm_obj
body.parent = arm_obj

# Smooth shading only; no sculpting, shrink-wrap, remesh or legacy projection.
for poly in mesh.polygons:
    poly.use_smooth = True

scene["hgpt_scaffold_generated"] = True
scene["hgpt_scaffold_pinned_commit"] = PINNED_COMMIT
scene["hgpt_scaffold_vertex_count"] = len(vertices)
scene["hgpt_scaffold_triangle_count"] = len(faces)
scene["hgpt_scaffold_bone_count"] = len(BONES)
scene["hgpt_next_rig"] = "hgpt_canonical_v4_original"

OUT_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


record = {}
if PROVENANCE.exists():
    try:
        record = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    except Exception:
        record = {}
record.update({
    "asset_id": "HomeGymPT_Male_ORIGINAL_v1",
    "clean_room": True,
    "legacy_geometry_imported": False,
    "scaffold": {
        "status": "clean_project_authored_scaffold_not_production",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "profile_commit": PINNED_COMMIT,
        "profile_blob_sha": PROFILE_BLOB,
        "historical_mesh_algorithm_blob_sha": MESH_BLOB,
        "historical_clean_rig_commit": RIG_COMMIT,
        "historical_clean_rig_blob_sha": RIG_BLOB,
        "vertex_count": len(vertices),
        "triangle_count": len(faces),
        "bone_count": len(BONES),
        "third_party_geometry_imported": False,
        "legacy_projection_used": False,
        "next_required_rig": "hgpt_canonical_v4_original",
    },
    "blend_path": str(BLEND.relative_to(ROOT)).replace("\\", "/"),
    "blend_sha256": sha256(BLEND),
})
PROVENANCE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

print(json.dumps(record["scaffold"], indent=2))
