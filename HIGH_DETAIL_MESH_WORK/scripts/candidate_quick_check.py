"""Fast, non-destructive structural guard for a new mesh-only candidate GLB.

Usage:
    python scripts/candidate_quick_check.py path/to/candidate.glb
    python scripts/candidate_quick_check.py path/to/candidate.glb --baseline path/to/baseline.glb

The default baseline is accepted V8 knee geometry. This is intentionally a fast guard, not a
replacement for the exercise, contact, clearance, renderer/exporter or visual tests.
"""

from __future__ import annotations

import argparse
import json
import struct
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb"

DTYPE = {
    5120: "i1",
    5121: "u1",
    5122: "<i2",
    5123: "<u2",
    5125: "<u4",
    5126: "<f4",
}
COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16,
}

def load_glb(path: Path):
    data = path.read_bytes()
    if len(data) < 28 or struct.unpack_from("<I", data, 0)[0] != 0x46546C67:
        raise ValueError(f"Not a GLB: {path}")
    version = struct.unpack_from("<I", data, 4)[0]
    if version != 2:
        raise ValueError(f"Unsupported GLB version {version}: {path}")
    json_len, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise ValueError("First GLB chunk is not JSON")
    document = json.loads(data[20:20 + json_len])
    binary_header = 20 + json_len
    if binary_header + 8 > len(data):
        raise ValueError("GLB has no BIN chunk")
    bin_len, bin_type = struct.unpack_from("<II", data, binary_header)
    if bin_type != 0x004E4942:
        raise ValueError("Second GLB chunk is not BIN")
    binary = data[binary_header + 8: binary_header + 8 + bin_len]
    return document, binary

def accessor(document, binary, index):
    a = document["accessors"][index]
    if "bufferView" not in a:
        raise ValueError(f"Sparse/no-buffer accessor not supported by quick guard: {index}")
    v = document["bufferViews"][a["bufferView"]]
    dtype = np.dtype(DTYPE[a["componentType"]])
    columns = COMPONENTS[a["type"]]
    stride = v.get("byteStride", dtype.itemsize * columns)
    offset = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    return np.ndarray(
        (a["count"], columns), dtype,
        buffer=binary, offset=offset,
        strides=(stride, dtype.itemsize),
    ).copy()

def first_body_primitive(document):
    return document["meshes"][0]["primitives"][0]

def topology_stats(document, binary):
    primitive = first_body_primitive(document)
    positions = accessor(document, binary, primitive["attributes"]["POSITION"]).astype(float)
    triangles = accessor(document, binary, primitive["indices"]).reshape(-1, 3).astype(np.int64)
    if not np.isfinite(positions).all():
        raise AssertionError("POSITION contains NaN/Inf")
    if triangles.size and (triangles.min() < 0 or triangles.max() >= len(positions)):
        raise AssertionError("Triangle index outside POSITION range")
    p0, p1, p2 = positions[triangles[:, 0]], positions[triangles[:, 1]], positions[triangles[:, 2]]
    twice_area = np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1)
    edges = Counter(
        tuple(sorted((int(a), int(b))))
        for face in triangles
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0]))
    )
    return {
        "vertices": int(len(positions)),
        "triangles": int(len(triangles)),
        "degenerate_triangles": int(np.count_nonzero(twice_area < 1e-12)),
        "nonmanifold_edges_gt2": int(sum(count > 2 for count in edges.values())),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--allow-materials", action="store_true",
                        help="Allow materials/textures/images/samplers to differ while keeping rig/animation protected")
    args = parser.parse_args()

    candidate = args.candidate.resolve()
    baseline = args.baseline.resolve()
    if candidate == baseline:
        raise SystemExit("Candidate and baseline are the same file")

    base_doc, base_bin = load_glb(baseline)
    cand_doc, cand_bin = load_glb(candidate)

    protected = ["nodes", "skins", "scenes", "animations"]
    if not args.allow_materials:
        protected += ["materials", "textures", "images", "samplers"]
    changed = [field for field in protected if cand_doc.get(field) != base_doc.get(field)]
    if changed:
        raise AssertionError(
            "Mesh-only candidate changed protected GLB fields: " + ", ".join(changed)
        )

    base_stats = topology_stats(base_doc, base_bin)
    cand_stats = topology_stats(cand_doc, cand_bin)

    if cand_stats["degenerate_triangles"] > base_stats["degenerate_triangles"]:
        raise AssertionError(
            f"Degenerate triangles increased: {base_stats['degenerate_triangles']} -> "
            f"{cand_stats['degenerate_triangles']}"
        )
    if cand_stats["nonmanifold_edges_gt2"] > base_stats["nonmanifold_edges_gt2"]:
        raise AssertionError(
            f">2-face non-manifold edges increased: {base_stats['nonmanifold_edges_gt2']} -> "
            f"{cand_stats['nonmanifold_edges_gt2']}"
        )

    print(json.dumps({
        "baseline": str(baseline),
        "candidate": str(candidate),
        "protected_glb_fields_unchanged": True,
        "materials_allowed_to_change": bool(args.allow_materials),
        "baseline_stats": base_stats,
        "candidate_stats": cand_stats,
        "quick_guard": "PASS",
        "note": "Run the full candidate guards and exercise review before acceptance.",
    }, indent=2))

if __name__ == "__main__":
    main()
