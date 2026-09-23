"""Prepare a review-only Blender copy of V6 with named selection groups.

This script does not alter mesh positions, topology, normals or skin weights.
It adds non-deform AUDIT_* vertex groups solely to make the next Blender session
faster to navigate.

Run from HIGH_DETAIL_MESH_WORK, for example:

    blender --background --factory-startup --python scripts/tag_v6_review_regions.py -- \
      HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend \
      HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_WORK_READY.blend

Do not promote the resulting .blend as a production asset.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend"
DEFAULT_OUT = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_WORK_READY.blend"


def argv():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    source = Path(args[0]).resolve() if args else DEFAULT_IN
    destination = Path(args[1]).resolve() if len(args) > 1 else DEFAULT_OUT
    return source, destination


def add_group(obj, name, indices):
    group = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
    valid = sorted({int(i) for i in indices if 0 <= int(i) < len(obj.data.vertices)})
    if valid:
        group.add(valid, 1.0, "REPLACE")
    return len(valid)


def two_ring_region(mesh, seeds, rings=2):
    adjacency = [set() for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    region = set(int(i) for i in seeds)
    frontier = set(region)
    for _ in range(rings):
        new = set()
        for vertex in frontier:
            new.update(adjacency[vertex])
        new -= region
        region.update(new)
        frontier = new
    return region


source, destination = argv()
if not source.is_file():
    raise FileNotFoundError(source)

bpy.ops.wm.open_mainfile(filepath=str(source))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError("No mesh objects found")

body = max(meshes, key=lambda obj: len(obj.data.vertices))
if len(body.data.vertices) != 33089:
    raise RuntimeError(
        f"Expected V6 body with 33089 vertices; largest mesh is {body.name} "
        f"with {len(body.data.vertices)}"
    )

knee = json.loads((ROOT / "reports/knee_seam_v5.json").read_text())["knees"]
guard = json.loads((ROOT / "reports/hand_contact_guard_v5.json").read_text())["original_vertex_ids"]

summary = {}
for side in ("L", "R"):
    seam = {i for path in knee[side]["paths"] for i in path}
    region = two_ring_region(body.data, seam, rings=2)
    summary[f"AUDIT_KNEE_SEAM_{side}"] = add_group(body, f"AUDIT_KNEE_SEAM_{side}", seam)
    summary[f"AUDIT_KNEE_WORK_REGION_{side}"] = add_group(
        body, f"AUDIT_KNEE_WORK_REGION_{side}", region
    )

summary["AUDIT_PUSHUP_FLOOR_GUARD"] = add_group(
    body, "AUDIT_PUSHUP_FLOOR_GUARD", guard
)

body["audit_groups_only"] = True
body["audit_note"] = (
    "AUDIT_* vertex groups are non-production selection helpers only; "
    "do not use them as deform weights."
)

destination.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
print("Saved:", destination)
print(json.dumps(summary, indent=2))
