#!/usr/bin/env python3
"""Noncanonical, SHA-pinned intake for selected BoneHub Visible Human male STLs.

Zero third-party dependencies. Data and derived reports stay outside Git.
This is NOT a bone-centre solver, a coordinate registration, or CP1 acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "ORIGINAL_V1_WORK/anatomy/bonehub_reference_sources_20261010.json"
DATASET_URL = "https://huggingface.co/datasets/BoneHub/visible-human-3d-models/resolve/main/visible_human_3d_models/CT/Mesh/01_Male/"
MAX_BYTES = 12_000_000
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load_sources(path: Path = MANIFEST) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "HGPT_EXTERNAL_NONCANONICAL_BONE_SURFACE_SOURCE":
        raise ValueError("Unrecognized/unsafe evidence manifest")
    if data.get("acceptance") != {
        "raw_downloaded": False,
        "geometry_measured": False,
        "registered": False,
        "independent_anatomical_landmarks": False,
        "canonical_promoted": False,
        "cp1_passed": False,
    }:
        raise ValueError("Source manifest must not contain acceptance flags")
    if data.get("subject", {}).get("stature_cm") != 180:
        raise ValueError("Unexpected source subject; not the 182 cm HGPT character")
    found = set()
    for sample in data["samples"]:
        ident, rel, sha = sample["id"], sample["path"], sample["sha256"]
        if not re.fullmatch(r"[a-z0-9_]+", ident) or ident in found:
            raise ValueError("Unsafe or duplicate sample ID")
        if not HEX64.fullmatch(sha):
            raise ValueError("Missing/invalid immutable source SHA256")
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts or len(p.parts) != 2:
            raise ValueError("Unsafe remote path")
        folder, filename = p.parts
        if folder not in {"HAND_LEFT", "FOOT_LEFT", "THORAX"}:
            raise ValueError("Unexpected remote region")
        if filename != filename.upper() and not filename.endswith(".stl"):
            raise ValueError("Unexpected suffix")
        if not filename.endswith(".stl") or not filename[:-4].replace("_", "").isalnum():
            raise ValueError("Invalid STL filename")
        found.add(ident)
    if len(found) != 4:
        raise ValueError("Expected four independently pinned, small sample meshes")
    return data


def measure_binary_stl(raw: bytes) -> dict:
    """Audit binary-STL numeric geometry only; the source unit/frame is unknown."""
    if len(raw) < 134:
        raise ValueError("Truncated STL")
    count = struct.unpack_from("<I", raw, 80)[0]
    if not 0 < count <= MAX_BYTES // 50 or len(raw) != 84 + count * 50:
        raise ValueError("STL count/length mismatch or non-binary file")
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    nondegenerate = 0
    for i in range(count):
        record = 84 + 50 * i
        vals = struct.unpack_from("<9f", raw, record + 12)
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("Nonfinite STL vertex")
        vertices = [vals[0:3], vals[3:6], vals[6:9]]
        for v in vertices:
            for axis in range(3):
                lo[axis] = min(lo[axis], v[axis])
                hi[axis] = max(hi[axis], v[axis])
        ab = [vertices[1][j] - vertices[0][j] for j in range(3)]
        ac = [vertices[2][j] - vertices[0][j] for j in range(3)]
        cross = (ab[1]*ac[2]-ab[2]*ac[1],
                 ab[2]*ac[0]-ab[0]*ac[2],
                 ab[0]*ac[1]-ab[1]*ac[0])
        if any(t != 0.0 for t in cross):
            nondegenerate += 1
    if nondegenerate == 0 or any(hi[j] <= lo[j] for j in range(3)):
        raise ValueError("Degenerate or planar STL cannot be certified as 3D")
    return {
        "binary_stl_triangles": count,
        "nondegenerate_triangle_count": nondegenerate,
        "bounds_min_source_units": lo,
        "bounds_max_source_units": hi,
        "bbox_extent_source_units": [hi[j] - lo[j] for j in range(3)],
        "stl_unit_and_coordinate_frame": "UNKNOWN; no scale/axes/laterality registration",
        "closed_surface_or_joint_contact_validated": False,
    }


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download_verified(sample: dict, private_dir: Path, allow_download: bool) -> bytes:
    """Never store an unverified download; never overwrite existing source data."""
    dest = private_dir / (sample["id"] + ".stl")
    if dest.is_symlink():
        raise ValueError("Symlink sources are prohibited")
    if dest.exists():
        raw = dest.read_bytes()
    else:
        if not allow_download:
            raise FileNotFoundError(f"{sample['id']} not cached; add --download")
        url = DATASET_URL + urllib.parse.quote(sample["path"], safe="/")
        request = urllib.request.Request(url, headers={"User-Agent": "HGPT-source-reference-audit/1.0"})
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Remote STL exceeds capped size")
        if digest(raw) != sample["sha256"]:
            raise ValueError("Remote STL fails upstream SHA256; no file written")
        private_dir.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as out:
            out.write(raw)
    if len(raw) > MAX_BYTES or digest(raw) != sample["sha256"]:
        raise ValueError("Unverified existing source file or size limit")
    return raw


def private_location(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("Output must be OUTSIDE the repository; never commit reference STLs")
    if resolved == Path(resolved.anchor):
        raise ValueError("Refuse filesystem-root output")
    return resolved


def run(sample_ids: list[str], private_dir: Path, allow_download: bool) -> dict:
    manifest = load_sources()
    entries = {x["id"]: x for x in manifest["samples"]}
    location = private_location(private_dir)
    reports = []
    for sample_id in sample_ids:
        sample = entries[sample_id]
        raw = download_verified(sample, location, allow_download)
        measured = measure_binary_stl(raw)
        reports.append({
            "id": sample_id,
            "upstream_file": sample["path"],
            "sha256_verified": sample["sha256"],
            **measured,
            "independent_anatomical_validity": False,
            "bone_registration_approved": False,
            "canonical_retarget_approved": False,
        })
    return {
        "schema_version": 1,
        "source": manifest["source_dataset"],
        "source_doi": manifest["source_doi"],
        "subject": "Visible Human male, 180 cm; not the HGPT 182 cm target",
        "read_only_noncanonical": True,
        "source_subject_independence_from_NLM_CT": False,
        "items": reports,
        "gate6_or_cp1_passed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List pinned sources; no networking")
    parser.add_argument("--id", help="One pinned sample identifier")
    parser.add_argument("--all", action="store_true", help="All four pinned samples")
    parser.add_argument("--download", action="store_true", help="Opt into verified source download")
    parser.add_argument("--private-dir", type=Path, help="Directory outside the Git checkout")
    args = parser.parse_args()
    try:
        manifest = load_sources()
        entries = [s["id"] for s in manifest["samples"]]
        if args.list:
            print(json.dumps({"noncanonical_samples": entries}, indent=2))
            return 0
        if bool(args.id) == bool(args.all) or not args.private_dir:
            parser.error("Specify exactly one of --id/--all and an external --private-dir")
        ids = entries if args.all else [args.id]
        if any(i not in entries for i in ids):
            raise ValueError("Unrecognized pinned source ID")
        print(json.dumps(run(ids, args.private_dir, args.download), indent=2))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"Source intake rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
