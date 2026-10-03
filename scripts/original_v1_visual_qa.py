#!/usr/bin/env python3
"""Deterministic mask-based visual QA for ORIGINAL-v1 capture evidence.

This tool uses only Python standard-library code and project-authored manifests.
It verifies source/mask identity, measures crop/visibility/silhouette/asymmetry,
and optionally compares matched captures. It never approves anatomy or a model phase.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, ensure_finite

CONTRACT = "ORIGINAL_V1_VISUAL_QA_CONTRACT.json"
REFERENCE_INVENTORY = "ORIGINAL_V1_VISUAL_QA_REFERENCE_INVENTORY.json"
HELPER = "scripts/original_v1_visual_qa.py"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_path(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("manifest path escapes evidence root")
    return path


def _tokens(data: bytes):
    i = 0
    n = len(data)
    while i < n:
        while i < n and data[i] in b" \t\r\n":
            i += 1
        if i < n and data[i] == 35:
            while i < n and data[i] not in b"\r\n":
                i += 1
            continue
        if i >= n:
            break
        j = i
        while j < n and data[j] not in b" \t\r\n#":
            j += 1
        yield data[i:j], j
        i = j


def read_pgm(path: Path) -> dict:
    data = path.read_bytes()
    gen = _tokens(data)
    try:
        magic_b, pos = next(gen)
        width_b, pos = next(gen)
        height_b, pos = next(gen)
        max_b, pos = next(gen)
    except StopIteration as exc:
        raise ValueError("PGM header incomplete") from exc
    magic = magic_b.decode("ascii", "strict")
    if magic not in ("P5", "P2"):
        raise ValueError("unsupported PGM magic")
    width, height, max_value = int(width_b), int(height_b), int(max_b)
    if width <= 0 or height <= 0 or max_value <= 0 or max_value > 255:
        raise ValueError("unsupported PGM dimensions/max value")

    if magic == "P2":
        values = [int(tok) for tok, _ in gen]
        if len(values) != width * height:
            raise ValueError("PGM pixel count differs")
    else:
        # Locate binary payload after the max-value token and mandatory whitespace.
        header_end = pos
        while header_end < len(data) and data[header_end] in b" \t\r\n":
            header_end += 1
        payload = data[header_end:]
        if len(payload) != width * height:
            raise ValueError("PGM binary payload length differs")
        values = list(payload)
    if any(v < 0 or v > max_value for v in values):
        raise ValueError("PGM sample outside declared range")
    mask = [v > 0 for v in values]
    return {"width": width, "height": height, "max_value": max_value, "mask": mask}


def mask_metrics(mask_data: dict, symmetry_axis_x: float | None = None) -> dict:
    width, height, mask = mask_data["width"], mask_data["height"], mask_data["mask"]
    points = [(i % width, i // width) for i, on in enumerate(mask) if on]
    count = len(points)
    if count == 0:
        return {
            "pixel_count": 0,
            "occupancy_ratio": 0.0,
            "bbox": None,
            "centroid": None,
            "edge_touch_pixels": 0,
            "component_count": 0,
            "largest_component_ratio": None,
            "symmetry": None,
        }
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    bbox = [min(xs), min(ys), max(xs), max(ys)]
    centroid = [sum(xs) / count, sum(ys) / count]
    edge_touch = sum(x in (0, width - 1) or y in (0, height - 1) for x, y in points)

    seen = set()
    components = []
    on = set(points)
    for start in points:
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        size = 0
        while q:
            x, y = q.popleft()
            size += 1
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                p = (x + dx, y + dy)
                if p in on and p not in seen:
                    seen.add(p)
                    q.append(p)
        components.append(size)

    symmetry = None
    if symmetry_axis_x is not None:
        mirrored_diff = 0
        union = 0
        left = right = 0
        for y in range(height):
            for x in range(width):
                a = mask[y * width + x]
                mx = int(round(2 * symmetry_axis_x - x))
                b = 0 <= mx < width and mask[y * width + mx]
                if a or b:
                    union += 1
                if a != b:
                    mirrored_diff += 1
                if a:
                    if x < symmetry_axis_x:
                        left += 1
                    elif x > symmetry_axis_x:
                        right += 1
        symmetry = {
            "axis_x": symmetry_axis_x,
            "mirrored_xor_ratio": mirrored_diff / union if union else None,
            "left_pixels": left,
            "right_pixels": right,
            "side_occupancy_delta_ratio": abs(left - right) / max(left + right, 1),
            "centroid_offset_from_axis_px": centroid[0] - symmetry_axis_x,
        }

    return {
        "pixel_count": count,
        "occupancy_ratio": count / (width * height),
        "bbox": bbox,
        "centroid": centroid,
        "edge_touch_pixels": edge_touch,
        "component_count": len(components),
        "largest_component_ratio": max(components) / count,
        "symmetry": symmetry,
    }


def matched_metrics(a: dict, b: dict) -> dict:
    if a["width"] != b["width"] or a["height"] != b["height"]:
        raise ValueError("matched mask dimensions differ")
    ma, mb = a["mask"], b["mask"]
    inter = union = xor = ca = cb = 0
    ax = ay = bx = by = 0.0
    width = a["width"]
    for i, (va, vb) in enumerate(zip(ma, mb)):
        if va:
            ca += 1; ax += i % width; ay += i // width
        if vb:
            cb += 1; bx += i % width; by += i // width
        inter += bool(va and vb)
        union += bool(va or vb)
        xor += bool(va != vb)
    centroid_shift = None
    if ca and cb:
        centroid_shift = math.hypot(ax/ca - bx/cb, ay/ca - by/cb)
    am = mask_metrics(a); bm = mask_metrics(b)
    bbox_delta = None
    if am["bbox"] is not None and bm["bbox"] is not None:
        bbox_delta = [bm["bbox"][i] - am["bbox"][i] for i in range(4)]
    return {
        "iou": inter / union if union else 1.0,
        "xor_ratio": xor / union if union else 0.0,
        "occupancy_delta": bm["occupancy_ratio"] - am["occupancy_ratio"],
        "centroid_shift_px": centroid_shift,
        "bbox_edge_delta_px": bbox_delta,
    }


def capture_identity(manifest: dict) -> dict:
    capture = manifest.get("capture", {})
    source = manifest.get("source_image", {})
    return {
        "candidate_sha256": manifest.get("candidate_sha256"),
        "asset_sha256": manifest.get("asset_sha256"),
        "target_runtime_commit": manifest.get("target_runtime_commit"),
        "source_width": source.get("width"),
        "source_height": source.get("height"),
        "capture_key": capture.get("capture_key"),
        "view_id": capture.get("view_id"),
        "pose_or_exercise": capture.get("pose_or_exercise"),
        "frame_or_time": capture.get("frame_or_time"),
        "renderer": capture.get("renderer"),
        "colour_management": capture.get("colour_management"),
        "crop": capture.get("crop"),
        "dressed": capture.get("dressed"),
    }


def verify_manifest(root: Path, manifest: dict, contract: dict) -> tuple[dict, dict[str, dict]]:
    if manifest.get("production_approved") is not False or manifest.get("phase_complete") is not False:
        raise ValueError("visual QA capture cannot claim approval or phase completion")
    if manifest.get("status") != "CAPTURE_EVIDENCE":
        raise ValueError("visual QA capture must be CAPTURE_EVIDENCE")

    source = manifest.get("source_image")
    if not isinstance(source, dict):
        raise ValueError("source image receipt missing")
    source_path = safe_path(root, source.get("path", ""))
    if not source_path.is_file() or digest(source_path) != source.get("sha256"):
        raise ValueError("source image bytes differ")
    if type(source.get("width")) is not int or type(source.get("height")) is not int:
        raise ValueError("source image dimensions missing")

    identity = capture_identity(manifest)
    missing = [k for k, v in identity.items() if v is None]
    if missing:
        raise ValueError("capture identity incomplete: " + ", ".join(missing))
    if not re.fullmatch(r"[0-9a-f]{64}", str(identity["candidate_sha256"])):
        raise ValueError("capture candidate SHA-256 invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(identity["asset_sha256"])):
        raise ValueError("capture asset SHA-256 invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", str(identity["target_runtime_commit"])):
        raise ValueError("capture target runtime commit invalid")

    mask_rows = manifest.get("masks")
    if not isinstance(mask_rows, list) or not mask_rows:
        raise ValueError("visual QA masks missing")
    roles = contract["mask_roles"]
    seen = set()
    masks = {}
    results = []
    for row in mask_rows:
        role = row.get("role")
        if role in seen or role not in roles:
            raise ValueError("mask role invalid or duplicate")
        seen.add(role)
        path = safe_path(root, row.get("path", ""))
        if not path.is_file() or digest(path) != row.get("sha256"):
            raise ValueError("mask bytes differ")
        data = read_pgm(path)
        if data["width"] != source["width"] or data["height"] != source["height"]:
            raise ValueError("mask dimensions differ from source image")
        axis = row.get("symmetry_axis_x")
        if axis is not None and type(axis) not in (int, float):
            raise ValueError("symmetry axis must be numeric")
        metrics = mask_metrics(data, float(axis) if axis is not None else None)
        expected_visible = row.get("expected_visible")
        allow_edge = row.get("allow_edge_touch")
        if type(expected_visible) is not bool or type(allow_edge) is not bool:
            raise ValueError("mask visibility/crop policy missing")
        if expected_visible and metrics["pixel_count"] == 0:
            crop_status = "FAIL_MISSING_VISIBLE_REGION"
        elif metrics["edge_touch_pixels"] and not allow_edge:
            crop_status = "FAIL_CROPPED"
        else:
            crop_status = "PASS"
        masks[role] = data
        results.append({
            "role": role,
            "path": row["path"],
            "sha256": row["sha256"],
            "expected_visible": expected_visible,
            "allow_edge_touch": allow_edge,
            "crop_visibility_status": crop_status,
            "metrics": metrics,
        })
    if "subject" not in seen:
        raise ValueError("subject mask required")
    return {"identity": identity, "masks": results}, masks


def compare_capture(current_manifest: dict, current_masks: dict[str, dict],
                    reference_manifest: dict, reference_masks: dict[str, dict]) -> dict:
    a = capture_identity(reference_manifest)
    b = capture_identity(current_manifest)
    required_match = (
        "source_width", "source_height", "capture_key", "view_id",
        "pose_or_exercise", "frame_or_time", "renderer",
        "colour_management", "crop", "dressed",
    )
    mismatches = [key for key in required_match if a.get(key) != b.get(key)]
    if mismatches:
        return {
            "status": "CAPTURE_MISMATCH",
            "mismatched_fields": mismatches,
            "per_role": [],
        }
    rows = []
    for role in sorted(set(current_masks) & set(reference_masks)):
        rows.append({"role": role, "metrics": matched_metrics(reference_masks[role], current_masks[role])})
    return {
        "status": "MEASURED",
        "mismatched_fields": [],
        "per_role": rows,
    }



def verify_reference_inventory(root: Path, reference_path: Path, reference_manifest: dict) -> dict:
    """Require an immutable owner-accepted first-party reference inventory entry."""
    inventory_path = root / REFERENCE_INVENTORY
    if not inventory_path.is_file():
        raise ValueError("visual QA reference inventory missing")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
    ensure_finite(inventory)
    if (
        inventory.get("schema_version") != 1
        or inventory.get("mode") != "explicit_versioned_references_only"
        or inventory.get("production_approved") is not False
        or inventory.get("phase_complete") is not False
    ):
        raise ValueError("unexpected visual QA reference inventory contract")
    rows = inventory.get("references")
    if not isinstance(rows, list):
        raise ValueError("visual QA reference inventory rows missing")
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not isinstance(x, str) or not x.strip() for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("visual QA reference inventory IDs missing/duplicated")

    rel = reference_path.relative_to(root.resolve()).as_posix()
    sha = digest(reference_path)
    matches = [
        row for row in rows
        if isinstance(row, dict)
        and row.get("capture_manifest") == {"path": rel, "sha256": sha}
    ]
    if len(matches) != 1:
        raise ValueError("reference manifest is not uniquely pinned in visual QA reference inventory")
    row = matches[0]
    if row.get("owner_review") != "accepted":
        raise ValueError("visual QA reference is not owner-accepted")

    identity = capture_identity(reference_manifest)
    expected_identity = {
        "candidate_sha256": identity.get("candidate_sha256"),
        "asset_sha256": identity.get("asset_sha256"),
        "target_runtime_commit": identity.get("target_runtime_commit"),
    }
    recorded_identity = {
        "candidate_sha256": row.get("candidate_sha256"),
        "asset_sha256": row.get("asset_sha256"),
        "target_runtime_commit": row.get("runtime_commit"),
    }
    if recorded_identity != expected_identity:
        raise ValueError("reference inventory candidate/asset/runtime identity differs")

    source = reference_manifest.get("source_image") or {}
    if row.get("source_image_sha256") != source.get("sha256"):
        raise ValueError("reference inventory source-image identity differs")
    masks = reference_manifest.get("masks")
    if not isinstance(masks, list):
        raise ValueError("reference manifest masks missing")
    actual_masks = {m.get("role"): m.get("sha256") for m in masks if isinstance(m, dict)}
    recorded_masks = row.get("mask_sha256")
    if not isinstance(recorded_masks, dict) or recorded_masks != actual_masks:
        raise ValueError("reference inventory mask identity differs")
    return row

def analyse(root: Path, capture_path: Path, contract: dict, reference_path: Path | None = None) -> dict:
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    current, current_masks = verify_manifest(root, capture, contract)
    comparison = {"status": "NOT_REQUESTED", "per_role": []}
    reference_receipt = None
    if reference_path is not None:
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        ref_verified, ref_masks = verify_manifest(root, reference, contract)
        comparison = compare_capture(capture, current_masks, reference, ref_masks)
        reference_receipt = {
            "path": reference_path.relative_to(root).as_posix(),
            "sha256": digest(reference_path),
            "identity": ref_verified["identity"],
        }

    failures = [
        row for row in current["masks"]
        if row["crop_visibility_status"].startswith("FAIL_")
    ]
    report = {
        "schema_version": 1,
        "status": "EVIDENCE_ONLY",
        "phase_complete": False,
        "production_approved": False,
        "capture_manifest": {
            "path": capture_path.relative_to(root).as_posix(),
            "sha256": digest(capture_path),
        },
        "capture_identity": current["identity"],
        "mask_results": current["masks"],
        "comparison": comparison,
        "reference_receipt": reference_receipt,
        "summary": {
            "crop_visibility_failures": len(failures),
            "automatic_visual_checks_complete": False,
            "owner_anatomy_acceptance_inferred": False,
        },
        "unknown_or_unimplemented": [
            "subjective anatomy quality",
            "occluded-surface anatomy",
            "physical contact correctness without runtime/model contact evidence",
            "lighting/material aesthetic quality",
            "continuous-motion temporal smoothness unless supplied by runtime evidence",
        ],
        "limits": "Deterministic mask measurements only. No aggregate quality score or production approval is inferred.",
    }
    ensure_finite(report)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture-manifest", type=Path, required=True)
    ap.add_argument("--reference-manifest", type=Path)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        contract_path = ROOT / CONTRACT
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        capture_path = args.capture_manifest.resolve()
        if not capture_path.is_relative_to(ROOT.resolve()):
            raise ValueError("capture manifest must remain inside repository")
        reference_path = args.reference_manifest.resolve() if args.reference_manifest else None
        if reference_path is not None and not reference_path.is_relative_to(ROOT.resolve()):
            raise ValueError("reference manifest must remain inside repository")
        reference_inventory_entry = None
        if reference_path is not None:
            if not reference_path.is_file():
                raise ValueError("reference manifest missing")
            reference_manifest = json.loads(reference_path.read_text(encoding="utf-8"))
            verify_manifest(ROOT, reference_manifest, contract)
            reference_inventory_entry = verify_reference_inventory(ROOT, reference_path, reference_manifest)
        out = args.json_out.resolve()
        if not out.is_relative_to(ROOT.resolve()):
            raise ValueError("output must remain inside repository")
        if out.exists():
            raise ValueError("visual QA output collision; preserve existing evidence")
        report = analyse(ROOT, capture_path, contract, reference_path)
        report.update({
            "qa_contract": {"path": CONTRACT, "sha256": digest(contract_path)},
            "reference_inventory": {"path": REFERENCE_INVENTORY, "sha256": digest(ROOT / REFERENCE_INVENTORY)},
            "selected_reference_inventory_id": reference_inventory_entry.get("id") if reference_inventory_entry else None,
            "verifier": {"path": HELPER, "sha256": digest(ROOT / HELPER)},
            "source_git_commit": subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        })
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, indent=2) + "\n")
        print("VISUAL QA MEASURED — EVIDENCE_ONLY; owner anatomy acceptance not inferred")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
