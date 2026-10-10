#!/usr/bin/env python3
"""Prepare legacy six exactly pinned original CT frames for existing safe Blender scene.

RUN BEFORE Blender. First-party only, no paid AI:
  python scripts/anatomy_fit/nlm_ct_blender_six_source_prep.py

The original six frames are sourced from the immutable original 72-frame NLM
series, checked against a SEPARATE Claude six-frame pinned-manifest digest,
and downloaded only into PRIVATE HOME storage. Does not create, move or
alter skeleton geometry; does not modify any existing .blend file.
"""
import argparse
import json
from pathlib import Path

from ct_pelvis_window_geometry import (
    assert_private_location, load_pinned_manifest,
)
from nlm_ct_laptop_review import (
    DEFAULT_BUNDLE, DEFAULT_WORKSPACE, download_original_pinned_pair,
)
from pelvic_ct_series_manifest import validate_series_bundle

REPO=Path(__file__).resolve().parents[2]
SIX=REPO/"ORIGINAL_V1_WORK"/"anatomy"/"audit"/"claude_pelvis_ct_review_20261009"/"pinned_six_frames_from_pr15_4680b49.json"


def original_six_source_rows(bundle, six_manifest):
    validate_series_bundle(bundle)
    trusted=load_pinned_manifest(six_manifest)
    by_id={r["source_id"]:r for series in bundle["series"] for r in series["slices"]}
    rows=[]
    found=[]
    for item in six_manifest["exact_png_and_scanner_header_sha256"]:
        sid=f'cvm{item["source_id"]}f'
        if sid not in by_id or item["source_id"] not in trusted["by_id"]:
            raise ValueError("legacy six-source ID missing from original CT series")
        row=by_id[sid]
        if (row["source_png_sha256"]!=item["png_sha256"] or
                row["source_header_sha256"]!=item["scanner_header_sha256"] or
                row["source_png_bytes"]!=item["png_bytes"] or
                abs(row["scanner_centre_RAS_mm"][2]-item["scanner_S_mm"])>1e-6):
            raise ValueError("six pinned Blender CT frames disagree with independent 72-image manifest")
        rows.append(row)
        found.append(item["source_id"])
    if found!=[1749,1752,1755,1797,1800,1803]:
        raise ValueError("exact six original CT review frames or order changed")
    return rows


def prepare(root=DEFAULT_WORKSPACE, *, bundle=DEFAULT_BUNDLE, six=SIX, downloader=None):
    if downloader is None:downloader=download_original_pinned_pair
    p=Path(root)
    if p.is_symlink():
        raise ValueError("private CT review destination must not be symlinked")
    location=assert_private_location(p)/"original_NLM_CT_sources"
    if location.is_symlink():
        raise ValueError("private CT source cache must not be symlinked")
    rows=original_six_source_rows(
        json.loads(Path(bundle).read_text()),
        json.loads(Path(six).read_text()))
    location.mkdir(parents=True,exist_ok=True)
    new=reused=0
    for row in rows:
        a,b=downloader(row,location)
        new+=a
        reused+=b
    return {
        "kind":"PRIVATE_SIX_ORIGINAL_CT_BLENDER_SOURCE_PREFLIGHT",
        "original_six_source_ids":[row["source_id"] for row in rows],
        "original_six_verified_source_count":len(rows),
        "files_new":new,
        "files_reused":reused,
        "private_ct_dir":str(location),
        "accepted_skeleton_or_model_modified":False,
        "scanner_to_HGPT_world_registered":False,
        "canonical_promotion_allowed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace",type=Path,default=DEFAULT_WORKSPACE)
    args=p.parse_args()
    print(json.dumps(prepare(args.workspace),indent=2))


if __name__=="__main__":
    main()
