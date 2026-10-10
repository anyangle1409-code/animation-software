#!/usr/bin/env python3
"""Read-only whole-carpus/tarsus/rib STL provenance + geometric-topology diagnostic.

Exactly 54 male source files (16 carpals/14 tarsals/24 ribs) at a PINNED
HF repository commit. No unit inference, patient-to-character registration,
clinical shape acceptance, or skeletal/production mutation is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import struct
import sys
import urllib.parse
import urllib.request

if __package__:
    from .bonehub_region_source_index import build_report, EXPECTED_SAMPLE_PINS, MALE_ROOT, REPO
    from .bonehub_surface_intake import private_location
else:
    from bonehub_region_source_index import build_report, EXPECTED_SAMPLE_PINS, MALE_ROOT, REPO
    from bonehub_surface_intake import private_location

FROZEN_UPSTREAM_REV = "ac8de2b38f5ae1a0996053ca0639dd6ae43358f1"
EXPECTED = {"carpus_file_candidate": 16, "tarsus_file_candidate": 14,
            "rib_file_candidate": 24}
MAX_FILE_BYTES = 16_000_000
MAX_TOTAL_BYTES = 220_000_000
ROOT = Path(__file__).resolve().parents[2]


def select_bones(index: dict) -> list[dict]:
    if (index.get("source_revision") != FROZEN_UPSTREAM_REV or
            index.get("cp1_anatomical_acceptance") is not False or
            index.get("canonical_geometry_modified") is not False or
            index.get("source_subject_independent_of_existing_CT") is not False):
        raise ValueError("Source revision or noncanonical safety flags changed")
    selected = [x for x in index["source_file_candidates"]
                if x["category"] in EXPECTED]
    count = {k: 0 for k in EXPECTED}
    sides = {(k, side): 0 for k in EXPECTED for side in ("LEFT", "RIGHT")}
    names = set()
    total_bytes = 0
    for x in selected:
        rel = x["source_relpath"]
        if rel in names or not isinstance(rel, str):
            raise ValueError("Duplicate or malformed source path")
        names.add(rel)
        cat = x["category"]
        path = rel.split("/")
        if len(path) != 2 or path[0] not in ("HAND_LEFT", "HAND_RIGHT", "FOOT_LEFT",
                                            "FOOT_RIGHT", "THORAX"):
            raise ValueError("Unexpected source path")
        filename = path[-1]
        if not filename.endswith(".stl") or not filename[:-4].replace("_", "").isalnum():
            raise ValueError("Unexpected file name")
        if cat == "carpus_file_candidate":
            side = path[0].removeprefix("HAND_")
            if not path[0].startswith("HAND_") or not filename.endswith("_" + side + ".stl"):
                raise ValueError("Inconsistent carpal side")
        elif cat == "tarsus_file_candidate":
            side = path[0].removeprefix("FOOT_")
            if not path[0].startswith("FOOT_") or not filename.endswith("_" + side + ".stl"):
                raise ValueError("Inconsistent tarsal side")
        else:
            if path[0] != "THORAX":
                raise ValueError("Rib outside thorax")
            side = "LEFT" if filename.endswith("_LEFT.stl") else "RIGHT"
            if not filename.endswith("_" + side + ".stl"):
                raise ValueError("Invalid rib side")
        count[cat] += 1
        sides[(cat, side)] += 1
        size = x.get("size_bytes")
        if type(size) is not int or not 84 < size <= MAX_FILE_BYTES:
            raise ValueError("Oversized, truncated or invalid source size")
        total_bytes += size
        pin = x.get("lfs_sha256_metadata") or EXPECTED_SAMPLE_PINS.get(rel)
        if (not isinstance(pin, str) or len(pin) != 64 or
                any(c not in "0123456789abcdef" for c in pin)):
            raise ValueError("Missing source SHA256 pin for " + rel)
        if rel in EXPECTED_SAMPLE_PINS and pin != EXPECTED_SAMPLE_PINS[rel]:
            raise ValueError("Historic verified source file SHA256 changed")
        x["selected_verified_pin"] = pin
        x["reported_side"] = side
    if count != EXPECTED:
        raise ValueError("Incomplete source file candidate coverage: " + repr(count))
    if any(sides[(c, s)] != (n//2) for c, n in EXPECTED.items()
           for s in ("LEFT", "RIGHT")):
        raise ValueError("Wrong left-right distribution")
    if total_bytes > MAX_TOTAL_BYTES:
        raise ValueError("Too much source geometry for controlled session")
    return sorted(selected, key=lambda i: i["source_relpath"])


def source_url(revision: str, rel: str) -> str:
    if revision != FROZEN_UPSTREAM_REV or ".." in Path(rel).parts or "\\" in rel:
        raise ValueError("Unsafe or nonfrozen source request")
    if rel.startswith("/") or len(rel.split("/")) != 2:
        raise ValueError("Invalid source file structure")
    return (f"https://huggingface.co/datasets/{REPO}/resolve/{revision}/"
            + urllib.parse.quote(MALE_ROOT + rel, safe="/"))


def verify_bytes(item: dict, raw: bytes) -> str:
    if len(raw) != item["size_bytes"]:
        raise ValueError("Raw source byte length differs from pinned metadata")
    got = hashlib.sha256(raw).hexdigest()
    if got != item["selected_verified_pin"]:
        raise ValueError("Raw STL SHA256 differs from pinned source")
    return got


def get_bytes(item: dict, folder: Path, allow_network: bool) -> bytes:
    """A wrong existing file is rejected, never repaired or overwritten."""
    filename = item["source_relpath"].replace("/", "__")
    dest = folder / filename
    if dest.is_symlink():
        raise ValueError("Symlink source cache prohibited")
    if dest.exists():
        raw = dest.read_bytes()
    else:
        if not allow_network:
            raise ValueError("Not in private cache; --download required")
        url = source_url(FROZEN_UPSTREAM_REV, item["source_relpath"])
        request = urllib.request.Request(url, headers={"User-Agent": "HGPT-source-research/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read(MAX_FILE_BYTES + 1)
        verify_bytes(item, raw)
        folder.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as fp:
            fp.write(raw)
    verify_bytes(item, raw)
    return raw


def mesh_diagnostics(raw: bytes) -> dict:
    """Exact float32 vertex welding; a diagnostic, NOT validated anatomical contact."""
    if len(raw) < 134:
        raise ValueError("Truncated binary STL")
    header_frames = set(re.findall(rb"SPACE=(LPS|RAS)", raw[:80].upper()))
    if len(header_frames) > 1:
        raise ValueError("Conflicting coordinate system declarations in source STL header")
    header_frame = next(iter(header_frames)).decode("ascii") if header_frames else None
    n = struct.unpack_from("<I", raw, 80)[0]
    if not (0 < n <= MAX_FILE_BYTES//50) or len(raw) != 84 + 50*n:
        raise ValueError("Binary STL count/length mismatch")
    lookup: dict[tuple[float, float, float], int] = {}
    roots: list[int] = []
    ranks: list[int] = []
    edges: dict[tuple[int, int], tuple[int, int]] = {}
    lo = [math.inf]*3
    hi = [-math.inf]*3
    degenerate = 0
    face_anchors: list[int] = []

    def vertex(v: tuple) -> int:
        if v not in lookup:
            lookup[v] = len(roots)
            roots.append(len(roots))
            ranks.append(0)
        for axis in range(3):
            lo[axis] = min(lo[axis], v[axis])
            hi[axis] = max(hi[axis], v[axis])
        return lookup[v]

    def find(i: int) -> int:
        while roots[i] != i:
            roots[i] = roots[roots[i]]
            i = roots[i]
        return i

    def union(a: int, b: int) -> None:
        a, b = find(a), find(b)
        if a == b:
            return
        if ranks[a] < ranks[b]:
            a, b = b, a
        roots[b] = a
        if ranks[a] == ranks[b]:
            ranks[a] += 1

    for idx in range(n):
        record = struct.unpack_from("<12fH", raw, 84 + 50*idx)
        v = [tuple(record[3+j*3:6+j*3]) for j in range(3)]
        if not all(math.isfinite(q) for triple in v for q in triple):
            raise ValueError("Nonfinite STL vertex")
        ids = [vertex(point) for point in v]
        ab = [v[1][j]-v[0][j] for j in range(3)]
        ac = [v[2][j]-v[0][j] for j in range(3)]
        cross = (
            ab[1]*ac[2]-ab[2]*ac[1],
            ab[2]*ac[0]-ab[0]*ac[2],
            ab[0]*ac[1]-ab[1]*ac[0],
        )
        if len(set(ids)) < 3 or all(c == 0.0 for c in cross):
            degenerate += 1
            continue
        union(ids[0], ids[1])
        union(ids[0], ids[2])
        face_anchors.append(ids[0])
        for a, b in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            pair = (min(a,b), max(a,b))
            sign = 1 if a < b else -1
            count, signed = edges.get(pair, (0, 0))
            edges[pair] = (count+1, signed+sign)
    if n == degenerate or any(not hi[j] > lo[j] for j in range(3)):
        raise ValueError("No three-dimensional nondegenerate faces")
    boundary = sum(1 for v in edges.values() if v[0] == 1)
    overused = sum(1 for v in edges.values() if v[0] > 2)
    disagree = sum(1 for v in edges.values() if v[0] == 2 and v[1] != 0)
    components = len({find(i) for i in range(len(roots))})
    face_components: dict[int, int] = {}
    for anchor in face_anchors:
        root_id = find(anchor)
        face_components[root_id] = face_components.get(root_id, 0) + 1
    per_component_faces = sorted(face_components.values(), reverse=True)
    orphan_vertex_only_components = components - len(face_components)
    return {
        "source_unit_known": False,
        "source_stl_header_explicit_coordinate_system": header_frame,
        "source_stl_header_field_verified_as_origin": False,
        "source_to_HGPT_registration_verified": False,
        "anatomical_joint_centres_accepted": False,
        "contact_patch_accepted": False,
        "raw_triangle_count": n,
        "exact_weld_unique_vertices": len(roots),
        "degenerate_triangles": degenerate,
        "boundary_edges_exact_weld": boundary,
        "nonmanifold_edges_over_two_faces": overused,
        "same_direction_two_face_edges": disagree,
        "vertex_connected_components_exact_weld": components,
        "nondegenerate_face_component_counts_desc": per_component_faces,
        "isolated_vertex_only_components_no_valid_faces": orphan_vertex_only_components,
        "bbox_min_source_units_unknown": lo,
        "bbox_max_source_units_unknown": hi,
        "bbox_extent_source_units_unknown": [hi[j]-lo[j] for j in range(3)],
        "watertight_candidate_exact_weld_only": (
            degenerate == 0 and boundary == 0 and overused == 0 and
            disagree == 0 and components == 1
        ),
    }


def scan(index: dict, private_dir: Path, allow_network: bool) -> dict:
    selected = select_bones(index)
    directory = private_location(private_dir)
    records = []
    for item in selected:
        raw = get_bytes(item, directory, allow_network)
        stats = mesh_diagnostics(raw)
        records.append({
            "source_relpath": item["source_relpath"],
            "source_repository_revision": FROZEN_UPSTREAM_REV,
            "reference_sha256_verified": verify_bytes(item, raw),
            "source_label_laterality_unconfirmed": item["reported_side"],
            "source_file_group": item["category"],
            **stats,
        })
    return {
        "schema_version": 1,
        "kind": "HGPT_NONCANONICAL_54_BONE_SURFACE_QA",
        "source": "Visible Human male, derivative segmentation; same donor as NLM CT",
        "source_revision": FROZEN_UPSTREAM_REV,
        "independent_subject_evidence": False,
        "stl_physical_units_and_axes_confirmed": False,
        "canonical_geometry_changed": False,
        "region_readiness_changed": False,
        "cp1_gate6_approved": False,
        "items": records,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--download", action="store_true",
                   help="Allow fetching 54 pinned raw STLs into a private external cache")
    p.add_argument("--private-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        private_dir = private_location(args.private_dir)
        report_path = args.output.expanduser().resolve()
        private_location(report_path.parent)
        if report_path.exists():
            raise ValueError("Never overwrite existing diagnostic report")
        index = build_report()
        report = scan(index, private_dir, args.download)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x", encoding="utf-8") as fd:
            json.dump(report, fd, indent=2, sort_keys=True)
            fd.write("\n")
        totals = {
            "source_STLs_verified": len(report["items"]),
            "source_revision": report["source_revision"],
            "degenerate_triangle_records": sum(r["degenerate_triangles"] for r in report["items"]),
            "boundary_edges_exact_weld": sum(r["boundary_edges_exact_weld"] for r in report["items"]),
            "nonmanifold_edges_over_two_faces": sum(r["nonmanifold_edges_over_two_faces"] for r in report["items"]),
            "watertight_single_component_candidates": sum(r["watertight_candidate_exact_weld_only"] for r in report["items"]),
            "canonical_approved": False,
            "report": str(report_path),
        }
        print(json.dumps(totals, indent=2))
        return 0
    except (ValueError, KeyError, OSError, urllib.error.URLError) as error:
        print("Fail-closed 54-STL diagnostic: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
