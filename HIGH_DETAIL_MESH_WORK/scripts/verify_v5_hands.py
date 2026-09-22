"""Check V5 contact-safe hand candidate isolation and bare/dressed equivalence."""

import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
reference = next((root / "reference").iterdir())
frozen = reference / "HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb"
v4_file = root / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v4b.glb"
v5_file = root / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v5_hands_curved.glb"
bare_file = root / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v5_hands_curved_BARE.glb"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glb(path):
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20 : 20 + length]), data[28 + length :]


def read(document, binary, accessor_index):
    accessor = document["accessors"][accessor_index]
    view = document["bufferViews"][accessor["bufferView"]]
    kind = np.dtype({5126: "<f4", 5123: "<u2", 5125: "<u4", 5121: "u1"}[accessor["componentType"]])
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    return np.ndarray(
        (accessor["count"], components), kind, buffer=binary,
        offset=view.get("byteOffset", 0) + accessor.get("byteOffset", 0),
        strides=(view.get("byteStride", kind.itemsize * components), kind.itemsize),
    ).copy()


source, source_bin = glb(frozen)
v4, v4_bin = glb(v4_file)
v5, v5_bin = glb(v5_file)
bare, bare_bin = glb(bare_file)
assert v5_bin[: len(source_bin)] == source_bin
assert v5_bin == bare_bin
assert source["meshes"][1:] == v5["meshes"][1:]
for field in ("nodes", "skins", "scenes", "animations", "materials", "textures", "images", "samplers"):
    assert v5.get(field) == source.get(field), field
expected_bare = json.loads(json.dumps(v5))
shorts = [node for node in expected_bare["nodes"] if node.get("name") == "HomeGymPT_Shorts"]
assert len(shorts) == 1
del shorts[0]["mesh"]
assert bare == expected_bare

source_primitive = source["meshes"][0]["primitives"][0]
v4_primitive = v4["meshes"][0]["primitives"][0]
v5_primitive = v5["meshes"][0]["primitives"][0]
source_count = source["accessors"][source_primitive["attributes"]["POSITION"]]["count"]
for attr in source_primitive["attributes"]:
    old = read(v4, v4_bin, v4_primitive["attributes"][attr])[:source_count]
    new = read(v5, v5_bin, v5_primitive["attributes"][attr])[:source_count]
    assert np.array_equal(old, new), attr

vertices = read(v5, v5_bin, v5_primitive["attributes"]["POSITION"]).astype(float)
triangles = read(v5, v5_bin, v5_primitive["indices"]).reshape(-1, 3)
assert np.isfinite(vertices).all()
assert triangles.min() >= 0 and triangles.max() < len(vertices)
twice_area = np.linalg.norm(np.cross(vertices[triangles[:, 1]] - vertices[triangles[:, 0]], vertices[triangles[:, 2]] - vertices[triangles[:, 0]]), axis=1)
edges = Counter(tuple(sorted((int(a), int(b)))) for face in triangles for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])))
source_triangles = read(source, source_bin, source_primitive["indices"]).reshape(-1, 3)
source_edges = Counter(tuple(sorted((int(a), int(b)))) for face in source_triangles for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])))
assert sum(count > 2 for count in edges.values()) <= sum(count > 2 for count in source_edges.values())
assert np.count_nonzero(twice_area < 1e-12) <= 2 * np.count_nonzero(np.linalg.norm(np.cross(
    read(source, source_bin, source_primitive["attributes"]["POSITION"])[source_triangles[:, 1]] - read(source, source_bin, source_primitive["attributes"]["POSITION"])[source_triangles[:, 0]],
    read(source, source_bin, source_primitive["attributes"]["POSITION"])[source_triangles[:, 2]] - read(source, source_bin, source_primitive["attributes"]["POSITION"])[source_triangles[:, 0]],
), axis=1) < 1e-12)

hashes = json.loads((root / "reports/reference_hashes.json").read_text())
assert all(digest(reference / name) == value for name, value in hashes.items())
prior = json.loads((root / "reports/final_integrity_v4b.json").read_text())["artifacts"]
assert all(digest(root / name) == value["sha256"] for name, value in prior.items())
report = {
    "reference_files_unchanged": len(hashes),
    "v4b_artifacts_unchanged": True,
    "source_rig_skin_animation_and_materials_equal": True,
    "v4b_original_attributes_equal": True,
    "bare_body_and_binary_equal": True,
    "body_vertices": len(vertices),
    "body_triangles": len(triangles),
    "degenerate_triangles": int(np.count_nonzero(twice_area < 1e-12)),
    "nonmanifold_edges_more_than_two_faces": sum(count > 2 for count in edges.values()),
    "source_nonmanifold_edges_more_than_two_faces": sum(count > 2 for count in source_edges.values()),
    "artifacts": {path.name: {"bytes": path.stat().st_size, "sha256": digest(path)} for path in (v5_file, bare_file, root / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v5_hands_curved.blend")},
}
(root / "reports/final_integrity_v5_hands_curved.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
