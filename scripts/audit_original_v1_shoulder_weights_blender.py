"""Read-only O4 shoulder-weight audit for the ORIGINAL v1 candidate.

Run inside Blender against a candidate Blend, for example:

blender --background --factory-startup \
  ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend \
  --python scripts/audit_original_v1_shoulder_weights_blender.py -- \
  ORIGINAL_V1_WORK/candidates/shoulder_weight_audit_r2.json

The script never saves the Blend. It reports how the current project-authored
weights are distributed around the shoulder/upper-torso transition so a repair
can be based on evidence rather than visual guesswork.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "ORIGINAL_V1_WORK" / "candidates" / "shoulder_weight_audit.json"
BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
RIG_NAME = "HGPT_CANONICAL_V4_ORIGINAL"
REGIONS = ("shoulder", "torso", "arm")
EPS = 1e-5


def args_after_double_dash() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def side_of_x(x: float) -> str:
    if x < -1e-6:
        return "l"
    if x > 1e-6:
        return "r"
    return "centre"


def weight_rows(body: bpy.types.Object) -> list[dict[str, float]]:
    group_names = {group.index: group.name for group in body.vertex_groups}
    rows: list[dict[str, float]] = []
    for vertex in body.data.vertices:
        row: dict[str, float] = {}
        for item in vertex.groups:
            name = group_names.get(item.group)
            if name is not None and item.weight > EPS:
                row[name] = float(item.weight)
        rows.append(row)
    return rows


def region_names(scene: bpy.types.Scene) -> list[str]:
    raw = scene.get("hgpt_region_names")
    if not isinstance(raw, str):
        raise SystemExit("Scene is missing hgpt_region_names JSON metadata.")
    names = json.loads(raw)
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise SystemExit("hgpt_region_names is not a JSON string list.")
    return names


def region_indices(body: bpy.types.Object, names: list[str]) -> list[str]:
    attr = body.data.attributes.get("hgpt_region")
    if attr is None or attr.domain != "POINT":
        raise SystemExit("Body mesh is missing point-domain hgpt_region attribute.")
    values: list[str] = []
    for item in attr.data:
        index = int(item.value)
        if index < 0 or index >= len(names):
            raise SystemExit(f"hgpt_region index {index} is outside the region-name table.")
        values.append(names[index])
    if len(values) != len(body.data.vertices):
        raise SystemExit("hgpt_region vertex count does not match body vertex count.")
    return values


def distance(a, b) -> float:
    return math.sqrt(
        (float(a[0]) - float(b[0])) ** 2
        + (float(a[1]) - float(b[1])) ** 2
        + (float(a[2]) - float(b[2])) ** 2
    )


def summarise(
    body: bpy.types.Object,
    rows: list[dict[str, float]],
    regions: list[str],
    rig: bpy.types.Object,
    region: str,
    side: str,
) -> dict:
    selected = [
        vertex.index
        for vertex in body.data.vertices
        if regions[vertex.index] == region and side_of_x(float(vertex.co.x)) == side
    ]
    if not selected:
        return {
            "vertex_count": 0,
            "max_weight_sum_error": None,
            "influence_count_histogram": {},
            "cross_side_weight_vertices": 0,
            "dominant_bones": {},
            "bone_stats": [],
            "distance_bands_from_upperarm_head": [],
        }

    suffix = f"_{side}"
    opposite = "_r" if side == "l" else "_l" if side == "r" else None
    sums = []
    influence_hist = Counter()
    cross_side = 0
    dominant = Counter()
    bone_acc: dict[str, dict[str, float | int]] = {}

    for index in selected:
        row = rows[index]
        total = sum(row.values())
        sums.append(total)
        influence_hist[len(row)] += 1
        if opposite and any(name.endswith(opposite) and weight > EPS for name, weight in row.items()):
            cross_side += 1
        if row:
            dominant[max(row.items(), key=lambda item: item[1])[0]] += 1
        for name, weight in row.items():
            stat = bone_acc.setdefault(
                name,
                {
                    "weight_sum": 0.0,
                    "max_weight": 0.0,
                    "vertices_gt_0_05": 0,
                    "vertices_gt_0_25": 0,
                },
            )
            stat["weight_sum"] = float(stat["weight_sum"]) + weight
            stat["max_weight"] = max(float(stat["max_weight"]), weight)
            if weight > 0.05:
                stat["vertices_gt_0_05"] = int(stat["vertices_gt_0_05"]) + 1
            if weight > 0.25:
                stat["vertices_gt_0_25"] = int(stat["vertices_gt_0_25"]) + 1

    bone_stats = []
    for name, stat in bone_acc.items():
        bone_stats.append(
            {
                "bone": name,
                "mean_weight_over_region": float(stat["weight_sum"]) / len(selected),
                "weight_sum": float(stat["weight_sum"]),
                "max_weight": float(stat["max_weight"]),
                "vertices_gt_0_05": int(stat["vertices_gt_0_05"]),
                "vertices_gt_0_25": int(stat["vertices_gt_0_25"]),
                "dominant_vertices": int(dominant.get(name, 0)),
            }
        )
    bone_stats.sort(key=lambda item: (-item["weight_sum"], item["bone"]))

    bands = []
    if side in ("l", "r"):
        joint = rig.data.bones[f"upperarm_{side}"].head_local
        boundaries = (0.04, 0.08, 0.12, 0.16)
        previous = 0.0
        for upper in boundaries:
            ids = [
                index
                for index in selected
                if previous <= distance(body.data.vertices[index].co, joint) < upper
            ]
            if ids:
                relevant = (
                    f"clavicle_{side}",
                    f"scapula_{side}",
                    f"upperarm_{side}",
                    "spine_02",
                    "spine_03",
                    "neck",
                )
                mean_by_bone = {
                    bone: sum(rows[index].get(bone, 0.0) for index in ids) / len(ids)
                    for bone in relevant
                }
                bands.append(
                    {
                        "distance_min_m": previous,
                        "distance_max_m": upper,
                        "vertex_count": len(ids),
                        "mean_weight_by_relevant_bone": mean_by_bone,
                    }
                )
            previous = upper

    return {
        "vertex_count": len(selected),
        "max_weight_sum_error": max(abs(total - 1.0) for total in sums),
        "influence_count_histogram": {
            str(key): int(value) for key, value in sorted(influence_hist.items())
        },
        "cross_side_weight_vertices": cross_side,
        "dominant_bones": dict(dominant.most_common()),
        "bone_stats": bone_stats,
        "distance_bands_from_upperarm_head": bands,
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    low = int(math.floor(position))
    high = int(math.ceil(position))
    if low == high:
        return ordered[low]
    t = position - low
    return ordered[low] * (1 - t) + ordered[high] * t


def gradient_stats(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean_l1": None, "p95_l1": None, "p99_l1": None, "max_l1": None}
    return {
        "count": len(values),
        "mean_l1": sum(values) / len(values),
        "p95_l1": percentile(values, 0.95),
        "p99_l1": percentile(values, 0.99),
        "max_l1": max(values),
    }


def edge_weight_gradients(
    body: bpy.types.Object,
    rows: list[dict[str, float]],
    regions: list[str],
) -> dict:
    buckets: dict[str, list[float]] = {
        "all_relevant": [],
        "shoulder_incident": [],
        "region_boundary": [],
        "left": [],
        "right": [],
    }
    top: list[dict] = []

    for edge in body.data.edges:
        a, b = (int(edge.vertices[0]), int(edge.vertices[1]))
        ra, rb = regions[a], regions[b]
        if ra not in REGIONS and rb not in REGIONS:
            continue
        row_a, row_b = rows[a], rows[b]
        bones = set(row_a) | set(row_b)
        l1 = sum(abs(row_a.get(name, 0.0) - row_b.get(name, 0.0)) for name in bones)

        xa = float(body.data.vertices[a].co.x)
        xb = float(body.data.vertices[b].co.x)
        side = side_of_x((xa + xb) * 0.5)
        buckets["all_relevant"].append(l1)
        if ra == "shoulder" or rb == "shoulder":
            buckets["shoulder_incident"].append(l1)
        if ra != rb:
            buckets["region_boundary"].append(l1)
        if side in ("l", "r"):
            buckets["left" if side == "l" else "right"].append(l1)

        largest = sorted(
            (
                {
                    "bone": name,
                    "delta": row_b.get(name, 0.0) - row_a.get(name, 0.0),
                    "abs_delta": abs(row_b.get(name, 0.0) - row_a.get(name, 0.0)),
                }
                for name in bones
            ),
            key=lambda item: (-item["abs_delta"], item["bone"]),
        )[:6]
        top.append(
            {
                "vertices": [a, b],
                "regions": [ra, rb],
                "side": side,
                "l1_weight_delta": l1,
                "midpoint": {
                    "x": (float(body.data.vertices[a].co.x) + float(body.data.vertices[b].co.x)) * 0.5,
                    "y": (float(body.data.vertices[a].co.y) + float(body.data.vertices[b].co.y)) * 0.5,
                    "z": (float(body.data.vertices[a].co.z) + float(body.data.vertices[b].co.z)) * 0.5,
                },
                "largest_bone_deltas": largest,
            }
        )

    top.sort(key=lambda item: (-item["l1_weight_delta"], item["vertices"]))
    return {
        "metric": (
            "L1 difference between normalised bone-weight vectors across one mesh edge. "
            "High values identify abrupt skinning transitions; they are diagnostic, not an "
            "automatic acceptance threshold."
        ),
        "stats": {name: gradient_stats(values) for name, values in buckets.items()},
        "top_25_edges": top[:25],
    }


def main() -> int:
    args = args_after_double_dash()
    out = Path(args[0]).resolve() if args else DEFAULT_OUT.resolve()

    scene = bpy.context.scene
    if scene.get("hgpt_candidate") != "O4_bind":
        raise SystemExit(
            f"Expected scene hgpt_candidate='O4_bind', got {scene.get('hgpt_candidate')!r}."
        )
    if not bool(scene.get("hgpt_not_production")):
        raise SystemExit("Expected candidate scene to remain marked hgpt_not_production.")

    body = bpy.data.objects.get(BODY_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if body is None or body.type != "MESH":
        raise SystemExit(f"Missing mesh object {BODY_NAME}.")
    if rig is None or rig.type != "ARMATURE":
        raise SystemExit(f"Missing armature object {RIG_NAME}.")

    names = region_names(scene)
    regions = region_indices(body, names)
    rows = weight_rows(body)

    report = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "O4 candidate shoulder-weight diagnostic (read-only, not production)",
        "blend": str(Path(bpy.data.filepath).resolve()),
        "blend_sha256": file_sha256(Path(bpy.data.filepath).resolve()),
        "body": BODY_NAME,
        "rig": RIG_NAME,
        "region_names": names,
        "rules": {
            "mutates_blend": False,
            "saves_blend": False,
            "purpose": (
                "Quantify current ORIGINAL-v1 O4 shoulder/upper-torso weight "
                "distribution before manual repair."
            ),
        },
        "regions": {},
        "edge_weight_gradients": edge_weight_gradients(body, rows, regions),
    }

    for region in REGIONS:
        report["regions"][region] = {
            side: summarise(body, rows, regions, rig, region, side)
            for side in ("l", "r", "centre")
        }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"WROTE {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
