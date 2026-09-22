"""Audit influence loss on v2's appended midpoint vertices without rebuilding it."""

import json
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = next((ROOT / "reference").iterdir()) / "HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb"
args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
version = args[0] if args else "v3"
max_allowed_loss = float(args[1]) if len(args) > 1 else None
CANDIDATE = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb"


def open_glb(path):
    data = path.read_bytes()
    json_length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20 : 20 + json_length]), data[28 + json_length :]


def attribute(document, binary, accessor_index):
    accessor = document["accessors"][accessor_index]
    view = document["bufferViews"][accessor["bufferView"]]
    data_type = np.dtype({5126: "<f4", 5123: "<u2", 5125: "<u4"}[accessor["componentType"]])
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    return np.ndarray(
        (accessor["count"], components),
        data_type,
        buffer=binary,
        offset=view.get("byteOffset", 0) + accessor.get("byteOffset", 0),
        strides=(view.get("byteStride", components * data_type.itemsize), data_type.itemsize),
    ).copy()


source, source_bin = open_glb(SOURCE)
candidate, candidate_bin = open_glb(CANDIDATE)
source_primitive = source["meshes"][0]["primitives"][0]
candidate_primitive = candidate["meshes"][0]["primitives"][0]
source_attrs = {key: attribute(source, source_bin, value) for key, value in source_primitive["attributes"].items()}
candidate_attrs = {key: attribute(candidate, candidate_bin, value) for key, value in candidate_primitive["attributes"].items()}
triangles = attribute(source, source_bin, source_primitive["indices"]).reshape(-1, 3)
count = len(source_attrs["POSITION"])
reference = json.loads((ROOT / "reports/sculpt_reference.json").read_text())
names = [source["nodes"][index]["name"].lower() for index in source["skins"][0]["joints"]]
joints = source_attrs["JOINTS_0"]
weights = source_attrs["WEIGHTS_0"]
hand = np.array([share["hand"] > 0.001 for share in reference["ownership"]])
feet = np.array(
    [
        any(("foot" in names[int(bone)] or "toe" in names[int(bone)]) and weight > 0.001 for bone, weight in zip(bones, vertex_weights))
        for bones, vertex_weights in zip(joints, weights)
    ]
)
protected = hand | feet
posed = np.asarray(reference["points"])
shoulders = [np.asarray(value) for value in reference["shoulders"].values()]
edge_to_vertex = {}
records = []


def midpoint(a, b):
    a, b = int(a), int(b)
    if protected[a] or protected[b]:
        return
    edge = tuple(sorted((a, b)))
    if edge in edge_to_vertex:
        return
    influence = Counter()
    for endpoint in edge:
        endpoint_total = float(weights[endpoint].sum())
        for bone, value in zip(joints[endpoint], weights[endpoint]):
            influence[int(bone)] += float(value) * 0.5 / endpoint_total
    ranked = influence.most_common()
    top = ranked[:4]
    kept = sum(value for _, value in top)
    lost = max(0, sum(influence.values()) - kept)
    if version.startswith("v3") and lost > 0.05:
        return
    index = count + len(records)
    edge_to_vertex[edge] = index
    midpoint_pos = (posed[a] + posed[b]) * 0.5
    near_shoulder = any(np.linalg.norm(midpoint_pos - shoulder) < 0.15 for shoulder in shoulders)
    actual_bones = [int(v) for v in candidate_attrs["JOINTS_0"][index]]
    actual_weights = [float(v) for v in candidate_attrs["WEIGHTS_0"][index]]
    assert actual_bones == [bone for bone, _ in top] + [0] * (4 - len(top))
    assert np.allclose(actual_weights, [value / kept for _, value in top] + [0] * (4 - len(top)), atol=1e-6)
    records.append(
        {
            "vertex": index,
            "edge": edge,
            "loss": lost,
            "near_shoulder": near_shoulder,
            "posed_midpoint": [float(value) for value in midpoint_pos],
            "retained": [{"bone": names[bone], "weight": value} for bone, value in top],
            "discarded": [{"bone": names[bone], "weight": value} for bone, value in ranked[4:] if value > 1e-8],
        }
    )


for a, b, c in triangles:
    midpoint(a, b)
    midpoint(b, c)
    midpoint(c, a)

assert len(records) == len(candidate_attrs["POSITION"]) - count
losses = np.array([item["loss"] for item in records])
shoulder_records = [item for item in records if item["near_shoulder"]]
report = {
    "source_vertices": count,
    "new_vertices": len(records),
    "mean_lost_weight": float(losses.mean()),
    "max_lost_weight": float(losses.max()),
    "count_loss_above_1_percent": int((losses > 0.01).sum()),
    "count_loss_above_5_percent": int((losses > 0.05).sum()),
    "count_loss_above_10_percent": int((losses > 0.10).sum()),
    "shoulder_new_vertices": len(shoulder_records),
    "shoulder_max_lost_weight": max((item["loss"] for item in shoulder_records), default=0),
    "worst_20": sorted(records, key=lambda item: item["loss"], reverse=True)[:20],
}
(ROOT / f"reports/weight_audit_{version}.json").write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != "worst_20"}, indent=2))
print("Worst 5:")
for item in report["worst_20"][:5]:
    print(item)
if max_allowed_loss is not None:
    assert report["max_lost_weight"] <= max_allowed_loss + 1e-7, f"new midpoint loses {report['max_lost_weight']:.3%} of skin weight"

