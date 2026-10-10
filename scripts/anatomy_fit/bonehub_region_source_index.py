#!/usr/bin/env python3
"""Inventory BoneHub male 3D source STLs by pinned upstream Git revision.

First-party read-only metadata intake; no mesh, CT, Blender, rig or anatomy edits.
Provisional filename enumeration is NOT osseous verification or CP1 acceptance.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import PurePosixPath

HOST = "huggingface.co"
REPO = "BoneHub/visible-human-3d-models"
MALE_ROOT = "visible_human_3d_models/CT/Mesh/01_Male/"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_ENTRIES = 10000
MAX_PAGES = 30
EXPECTED_SAMPLE_PINS = {
    "HAND_LEFT/SCAPHOID_LEFT.stl": "362d0d42bf1b4475e705846d8c7c48965bb052f875a93355c8e302937ddef762",
    "FOOT_LEFT/TALUS_LEFT.stl": "b79dcb8037223d2652e300cb42124c9d4e16dfedcc49ff36b4d44ed3fc24602e",
    "FOOT_LEFT/CUBOID_LEFT.stl": "7ed61043826f269aecee108a1d1298e59dc2cf2da29b0083a297f548d48d0353",
    "THORAX/RIB_1_LEFT.stl": "5b5216f2df8cac598aa94b1fe89039ce6734a15e520b9f1f788ddae3a6070295",
}


def permitted_api_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == HOST
        and parsed.port is None
        and not parsed.username
        and not parsed.password
        and (parsed.path == f"/api/datasets/{REPO}" or parsed.path.startswith(f"/api/datasets/{REPO}/"))
    )


def read_api(url: str) -> tuple[object, str | None]:
    if not permitted_api_url(url):
        raise ValueError("Unsafe metadata URL")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HGPT-noncanonical-source-index/1.0",
                 "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        if not permitted_api_url(response.geturl()):
            raise ValueError("Unexpected API redirect host/path")
        raw = response.read(6_000_001)
        if len(raw) > 6_000_000:
            raise ValueError("Oversized metadata response")
        doc = json.loads(raw)
        link = response.headers.get("Link")
    next_url = None
    if link:
        for section in link.split(","):
            m = re.match(r'\s*<([^>]+)>;\s*rel="next"', section.strip())
            if m:
                next_url = m.group(1)
                if not permitted_api_url(next_url):
                    raise ValueError("Unsafe pagination URL")
                break
    return doc, next_url


def classify(path: str) -> tuple[str, str] | None:
    """Return grouping/relpath only. Path names do not establish bone identity."""
    if not isinstance(path, str) or not path.startswith(MALE_ROOT):
        return None
    rel = path[len(MALE_ROOT):]
    if "\x00" in rel or "\\" in rel:
        return None
    segments = PurePosixPath(rel).parts
    if len(segments) != 2 or ".." in segments:
        return None
    folder, name = segments
    if not name.endswith(".stl") or not re.fullmatch(r"[A-Za-z0-9_-]+\.stl", name):
        return None
    if folder in ("HAND_LEFT", "HAND_RIGHT"):
        if any(k in name.upper() for k in (
            "SCAPHOID", "LUNATE", "TRIQUET", "PISIFORM",
            "TRAPEZI", "CAPITATE", "HAMATE"
        )):
            return "carpus_file_candidate", rel
        return "other_hand_file", rel
    if folder in ("FOOT_LEFT", "FOOT_RIGHT"):
        if any(k in name.upper() for k in (
            "TALUS", "CALCANEUS", "NAVICULAR", "CUBOID", "CUNEIFORM"
        )):
            return "tarsus_file_candidate", rel
        return "other_foot_file", rel
    if folder == "THORAX" and re.fullmatch(r"RIB_?[0-9]{1,2}_(LEFT|RIGHT)\.stl", name, flags=re.I):
        return "rib_file_candidate", rel
    if folder == "THORAX":
        return "other_thorax_file", rel
    return None


def analyze_tree(entries: list, upstream_sha: str) -> dict:
    if not HEX40.fullmatch(upstream_sha) or len(entries) > MAX_ENTRIES:
        raise ValueError("Unpinned revision or excessive source entries")
    accepted = {}
    seen_all = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid upstream metadata item")
        path = entry.get("path")
        if not isinstance(path, str) or path in seen_all:
            raise ValueError("Duplicate or malformed upstream path")
        seen_all.add(path)
        if entry.get("type") not in ("file", "directory"):
            raise ValueError("Unexpected tree object type")
        if entry.get("type") != "file":
            continue
        match = classify(path)
        if not match:
            continue
        category, rel = match
        size = entry.get("size")
        if type(size) is not int or size <= 0 or size > 200_000_000:
            raise ValueError("Unreasonable source file size")
        lfs = entry.get("lfs") or {}
        oid = lfs.get("oid") if isinstance(lfs, dict) else None
        if oid is not None:
            if not HEX64.fullmatch(oid):
                raise ValueError("Malformed source LFS checksum")
        accepted[rel] = {
            "category": category,
            "source_relpath": rel,
            "size_bytes": size,
            "lfs_sha256_metadata": oid,
            "source_file_sha256_verified": False,
            "unit_frame_laterality_verified": False,
            "bone_geometry_verified": False,
            "contact_patch_verified": False,
        }
    for sample_path, original_sha in EXPECTED_SAMPLE_PINS.items():
        if sample_path not in accepted:
            raise ValueError("Pinned baseline sample missing from upstream revision")
        existing = accepted[sample_path]["lfs_sha256_metadata"]
        if existing is not None and existing != original_sha:
            raise ValueError("Existing verified sample differs from upstream metadata")
    if not accepted or any(not any(v["category"] == typ for v in accepted.values())
                           for typ in ("carpus_file_candidate", "tarsus_file_candidate",
                                       "rib_file_candidate")):
        raise ValueError("No usable entries in one or more blocked regions")
    counts = Counter(v["category"] for v in accepted.values())
    return {
        "schema_version": 1,
        "kind": "HGPT_NONCANONICAL_SOURCE_COVERAGE_DIAGNOSTIC",
        "source_repo": REPO,
        "source_revision": upstream_sha,
        "subject": "NLM Visible Human Male, 180 cm, same subject as existing NLM CT",
        "source_subject_independent_of_existing_CT": False,
        "counts_by_source_filename_category": dict(sorted(counts.items())),
        "expected_name_coverage": {
            "carpal_stl_files": 16,
            "tarsal_stl_files": 14,
            "rib_stl_files": 24
        },
        "source_file_candidates": [accepted[k] for k in sorted(accepted)],
        "source_data_downloaded": False,
        "canonical_geometry_modified": False,
        "cp1_anatomical_acceptance": False,
    }


def build_report() -> dict:
    info, _ = read_api(f"https://{HOST}/api/datasets/{REPO}")
    if not isinstance(info, dict) or not HEX40.fullmatch(str(info.get("sha", ""))):
        raise ValueError("Dataset HEAD revision not a full Git SHA")
    sha = info["sha"]
    path = urllib.parse.quote(MALE_ROOT.rstrip("/"), safe="/")
    start = f"https://{HOST}/api/datasets/{REPO}/tree/{sha}/{path}?recursive=true&expand=false"
    url = start
    seen_pages = set()
    entries = []
    while url:
        if url in seen_pages or len(seen_pages) >= MAX_PAGES:
            raise ValueError("Source pagination loop or too many pages")
        seen_pages.add(url)
        page, url = read_api(url)
        if not isinstance(page, list):
            raise ValueError("Tree metadata is not a list")
        entries.extend(page)
        if len(entries) > MAX_ENTRIES:
            raise ValueError("Source tree exceeds safe size limit")
    return analyze_tree(entries, sha)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", action="store_true",
                        help="Explicitly opt into read-only HF metadata lookup")
    parser.add_argument("--output", help="Report path (never raw STL/CT material)")
    args = parser.parse_args()
    if not args.network:
        parser.error("Read-only network access requires --network")
    try:
        report = build_report()
        text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            from pathlib import Path
            output = Path(args.output).expanduser().resolve()
            from anatomy_fit.bonehub_surface_intake import private_location
            private_location(output.parent)
            if output.exists():
                raise ValueError("Do not overwrite existing source report")
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as file:
                file.write(text)
        else:
            print(text)
        return 0
    except (ValueError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"Fail-closed source metadata lookup: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
