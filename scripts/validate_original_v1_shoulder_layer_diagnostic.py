#!/usr/bin/env python3
"""Validate read-only shoulder/axilla deformation-layer diagnostic output."""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ZONES = {
    "l_shoulder_neighborhood",
    "r_shoulder_neighborhood",
    "l_axilla_neighborhood",
    "r_axilla_neighborhood",
    "l_anterior_axilla",
    "r_anterior_axilla",
    "l_posterior_axilla",
    "r_posterior_axilla",
    "l_lateral_chest_root",
    "r_lateral_chest_root",
    "torso_or_shoulder",
}


def ensure_finite(value, where="root"):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{where}: non-finite value")
    if isinstance(value, dict):
        for key, child in value.items():
            ensure_finite(child, f"{where}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            ensure_finite(child, f"{where}[{idx}]")


def validate(data):
    ensure_finite(data)
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if data.get("status") != "READ_ONLY_SHOULDER_LAYER_DIAGNOSTIC":
        raise ValueError("unexpected diagnostic status")
    if data.get("source_saved_or_modified") is not False:
        raise ValueError("diagnostic must explicitly record source_saved_or_modified=false")
    sha = data.get("candidate_sha256")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ValueError("candidate_sha256 missing/invalid")
    if not data.get("candidate"):
        raise ValueError("candidate filename missing")
    if not SHA_RE.fullmatch(str(data.get("pose_definition_script_sha256", ""))):
        raise ValueError("pose-definition script hash missing/invalid")
    if not SHA_RE.fullmatch(str(data.get("flexion_driver_script_sha256", ""))):
        raise ValueError("driver script hash missing/invalid")

    samples = data.get("samples_per_pose")
    if not isinstance(samples, int) or samples < 3:
        raise ValueError("samples_per_pose invalid")

    families = data.get("corrective_families")
    if not isinstance(families, dict):
        raise ValueError("corrective_families missing")
    if set(families) - {"abduction", "flexion", "scapular"}:
        raise ValueError("unknown corrective family")

    contract = data.get("zone_contract") or {}
    counts = contract.get("zone_vertex_counts") or {}
    missing_zones = REQUIRED_ZONES - set(counts)
    if missing_zones:
        raise ValueError(f"required diagnostic zones missing: {sorted(missing_zones)}")
    if any(not isinstance(counts[z], int) or counts[z] <= 0 for z in REQUIRED_ZONES):
        raise ValueError("a required diagnostic zone has no vertices")

    weight_ownership = contract.get("static_weight_ownership") or {}
    if not REQUIRED_ZONES.issubset(weight_ownership):
        raise ValueError("static weight ownership missing required zones")

    requested = data.get("poses_requested") or []
    poses = data.get("poses") or {}
    if requested != list(poses):
        raise ValueError("pose order/coverage differs from poses_requested")
    if not requested:
        raise ValueError("no poses recorded")

    for pose, rows in poses.items():
        if not isinstance(rows, list) or len(rows) != samples:
            raise ValueError(f"{pose}: sample count differs")
        fractions = [row.get("fraction") for row in rows]
        if fractions[0] != 0.0 or fractions[-1] != 1.0:
            raise ValueError(f"{pose}: arc endpoints missing")
        if any(fractions[i] >= fractions[i + 1] for i in range(len(fractions) - 1)):
            raise ValueError(f"{pose}: fractions not strictly increasing")

        for idx, row in enumerate(rows):
            if not isinstance(row.get("elevation_l_deg"), (int, float)) or not isinstance(row.get("elevation_r_deg"), (int, float)):
                raise ValueError(f"{pose}[{idx}]: elevation missing")
            if not isinstance(row.get("shape_key_values"), dict):
                raise ValueError(f"{pose}[{idx}]: shape_key_values missing")
            acts = row.get("family_activation") or {}
            if set(acts) != set(families):
                raise ValueError(f"{pose}[{idx}]: family activation coverage differs")
            residual = row.get("linear_decomposition_residual_max_m")
            if not isinstance(residual, (int, float)) or residual > 1e-6:
                raise ValueError(f"{pose}[{idx}]: layer decomposition residual too large")
            zones = row.get("zones") or {}
            if not REQUIRED_ZONES.issubset(zones):
                raise ValueError(f"{pose}[{idx}]: required zone evidence missing")
            for zone in REQUIRED_ZONES:
                z = zones[zone]
                for name in (
                    "weights_vs_trunk_proxy",
                    "shoulder_combined_vs_weights",
                    "all_active_shapes_vs_weights",
                ):
                    stat = z.get(name) or {}
                    if stat.get("count") != counts[zone]:
                        raise ValueError(f"{pose}[{idx}] {zone}: {name} count differs")
                for family in families:
                    stat = z.get(f"{family}_vs_weights") or {}
                    if stat.get("count") != counts[zone]:
                        raise ValueError(f"{pose}[{idx}] {zone}: {family} count differs")

    return {
        "candidate": data["candidate"],
        "candidate_sha256": sha,
        "poses": requested,
        "samples_per_pose": samples,
        "families": sorted(families),
        "required_zones": len(REQUIRED_ZONES),
        "status": "PASS",
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if len(argv) != 1:
        print("Usage: validate_original_v1_shoulder_layer_diagnostic.py <report.json>")
        return 2
    try:
        path = Path(argv[0])
        result = validate(json.loads(path.read_text(encoding="utf-8")))
        print("SHOULDER LAYER DIAGNOSTIC VALIDATION: PASS")
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
