"""Build a privacy-safe, source-ordered frame plan for Blender CT review."""
import hashlib
import math
import re
from pathlib import Path


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SOURCE_ID = re.compile(r"[A-Za-z0-9._-]{1,128}\Z")


def write_private_display_copy(path, data):
    """Create a display derivative, or reuse it only when bytes match exactly."""
    target = Path(path)
    if target.is_symlink():
        raise ValueError("private display copy must not be a symlink")
    if target.exists():
        if not target.is_file() or target.read_bytes() != data:
            raise ValueError("existing private display copy does not match expected bytes")
    else:
        with target.open("xb") as handle:
            handle.write(data)
    return hashlib.sha256(data).hexdigest()


def build_frame_plan(bundle):
    """Flatten rows only for timeline numbering; preserve acquisition groups."""
    if (not isinstance(bundle, dict) or bundle.get("schema_version") != 1 or
            bundle.get("kind") != "CANDIDATE_PELVIC_CT_SERIES_BUNDLE"):
        raise ValueError("unsupported pelvic CT source bundle")
    if bundle.get("source_skeleton_governs_geometry") is not True:
        raise ValueError("source skeleton must remain geometry authority")
    if bundle.get("canonical_promotion_allowed") is not False:
        raise ValueError("canonical promotion must remain prohibited")
    groups = bundle.get("series")
    if not isinstance(groups, list) or len(groups) < 2:
        raise ValueError("at least two separate acquisition groups are required")

    frames = []
    group_rows = []
    source_ids = set()
    for group_index, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            raise ValueError("each acquisition group must be an object")
        slices = group.get("slices")
        if not isinstance(slices, list) or not slices:
            raise ValueError("each acquisition group must contain source slices")
        first_frame = len(frames) + 1
        for group_frame, row in enumerate(slices, start=1):
            if not isinstance(row, dict):
                raise ValueError("each source frame must be an object")
            source_id = row.get("source_id")
            if (not isinstance(source_id, str) or
                    _SOURCE_ID.fullmatch(source_id) is None):
                raise ValueError("each source frame requires a privacy-safe source_id")
            if source_id in source_ids:
                raise ValueError("duplicate source_id across acquisition groups")
            source_ids.add(source_id)
            for key in ("source_png_sha256", "source_header_sha256"):
                value = row.get(key)
                if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                    raise ValueError("each source frame requires lowercase SHA-256 hashes")
            centre = row.get("scanner_centre_RAS_mm")
            if (not isinstance(centre, list) or len(centre) != 3 or
                    any(isinstance(value, bool) or
                        not isinstance(value, (int, float)) or
                        not math.isfinite(float(value)) for value in centre)):
                raise ValueError("each source frame requires finite scanner RAS coordinates")
            frames.append({
                "frame": len(frames) + 1,
                "group_index": group_index,
                "group_frame": group_frame,
                "source_id": source_id,
                "source_png_sha256": row["source_png_sha256"],
                "source_header_sha256": row["source_header_sha256"],
                "scanner_centre_RAS_mm": [float(value) for value in centre],
                "scanner_S_mm": float(centre[2]),
                "scanner_grid": row.get("scanner_grid"),
                "pixel_spacing_mm": row.get("pixel_spacing_mm"),
                "slice_thickness_mm": row.get("slice_thickness_mm"),
            })
        group_rows.append({
            "group_index": group_index,
            "frame_start": first_frame,
            "frame_end": len(frames),
            "slice_count": len(slices),
        })

    return {
        "total_frames": len(frames),
        "groups": group_rows,
        "group_boundary_frames": [row["frame_start"] for row in group_rows[1:]],
        "group_boundary_frame": (group_rows[1]["frame_start"]
                                  if len(group_rows) > 1 else None),
        "frames": frames,
        "source_skeleton_governs_geometry": True,
        "canonical_promotion_allowed": False,
        "anatomical_coverage_verified": False,
        "patient_scanner_to_HGPT_world_verified": False,
    }
