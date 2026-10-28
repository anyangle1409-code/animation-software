#!/usr/bin/env python3
"""Read-only squat foot-surface lower-envelope proxy from pinned pose evidence."""
from __future__ import annotations
import argparse
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from localize_failures import Evidence, SOURCES  # noqa: E402

SAMPLES = (0, 7, 8)
STATUS = "READ_ONLY_SQUAT_FOOT_SURFACE_PROXY_NOT_GROUND_CONTACT_APPROVAL"
PINNED_MEMBER_SHA256 = {
    "W8": {
        "diagnosis.json": "b1afed85ffbf247604f2fd2afce6a9e8a0b3fe0d69ab93f943e8d49d36ec5923",
        "W8__squat__sample00__triangles.json": "958267c0b9b452651816310fd6e831b7da0b752cd34e01553d2121c984f4ba09",
        "W8__squat__sample00__geometry.npz": "5a3e543edc3b1bb5959f738a0b4009a2ca90fddfc0bd8194cd136b8b80f5c265",
        "W8__squat__sample07__triangles.json": "1f6529420fd0d191c97928f7d5c43f06435510f78edeee8a5f041f6cf8323fe8",
        "W8__squat__sample07__geometry.npz": "7cb08878c9db9651b372d1991ef07d55a36265449fffedc80ffc2caa0a0e8e98",
        "W8__squat__sample08__triangles.json": "679a929b6676406734e1754ffa9422688833b33d1bb090f7784fb32aa8806b09",
        "W8__squat__sample08__geometry.npz": "d211aaaae918bf83a9430b3fc526e731667e41c724f59b7313fe826ab0c658b2",
    },
    "V14": {
        "diagnosis.json": "2f49c51a780acf3834e35ef9e9a122515d16c8bed3e069a71282cd6983dd9321",
        "V14__squat__sample00__triangles.json": "afeb0121735a1935f0c1e0b1c8489188e870f7142b0225940bd0d8e24448fd7d",
        "V14__squat__sample00__geometry.npz": "c0c6816a75e32bcb8989b7c42aa256d0db053322856d7e18b3218cf30d98d8b6",
        "V14__squat__sample07__triangles.json": "c0d87ce287ca96cb32cbaf2154952e4020bef1e2f11b91b66c625d03c3e7c8a9",
        "V14__squat__sample07__geometry.npz": "1070fbdb61e694ffb2a725ea64e4e1aa0b169a412f955279b6064f533952420c",
        "V14__squat__sample08__triangles.json": "ba965be26a8a9ba0adf073b555fe23f29053a77a215061357b751f4580f38cef",
        "V14__squat__sample08__geometry.npz": "cc179989a347a0b037235eff95f3172c0457d5c66c43c43141d2e93cffa67007",
    },
    "R120": {
        "diagnosis.json": "399cca503451fea4f84812e97675bdcc8c57c26aaa9c2a9c6c18b0ad2fb68e5e",
        "R120__squat__sample00__triangles.json": "5cbbe6cff8b7fc587cfd84b6c40675d2edd2813ce0f7379818a5e545299000ff",
        "R120__squat__sample00__geometry.npz": "78c0972c74eebef6718c103bfab6cdc36acbbc10dccd444bde6c4d985b4951af",
        "R120__squat__sample07__triangles.json": "0dc1ca4f18e6b8b7793a5f348f610840caa87fcd547de4017edfadb1f1a99914",
        "R120__squat__sample07__geometry.npz": "5ff7ef95b9471c78c9e2f6cd776cebf862271607463a8dc975a5366532c693c8",
        "R120__squat__sample08__triangles.json": "8db05a90846749d3e640a779076e7225ef43f5dbfdb7ad4b43f4d340ea78e773",
        "R120__squat__sample08__geometry.npz": "edbb40d550047a233cbc47d1882b7a648532f3cdb2e7bfb165804e236a9831dc",
    },
}


def _rounded(values):
    return [round(float(value), 12) for value in values]


def verify_member_hashes(model, reader, expected=None):
    expected = PINNED_MEMBER_SHA256.get(model) if expected is None else expected
    if not isinstance(expected, dict) or not expected:
        raise ValueError(f"{model}: pinned member hashes unavailable")
    for name, wanted in expected.items():
        try:
            raw = reader(name)
        except (KeyError, FileNotFoundError) as error:
            raise ValueError(f"{model}: missing pinned {name} member") from error
        actual = hashlib.sha256(raw).hexdigest()
        if actual != wanted:
            raise ValueError(f"{model}: {name} member hash mismatch")


def _validate_arrays(sample, arrays):
    required = {"rest_vertices", "posed_vertices", "triangles", "dominant_groups"}
    if set(arrays) != required:
        raise ValueError(f"sample {sample}: exact geometry arrays required")
    rest = np.asarray(arrays["rest_vertices"])
    posed = np.asarray(arrays["posed_vertices"])
    triangles = np.asarray(arrays["triangles"])
    groups = np.asarray(arrays["dominant_groups"])
    if (rest.ndim != 2 or rest.shape[1] != 3 or posed.shape != rest.shape
            or groups.ndim != 1 or len(groups) != len(rest)):
        raise ValueError(f"sample {sample}: invalid vertex or dominant-group arrays")
    if (triangles.ndim != 2 or triangles.shape[1] != 3
            or not np.issubdtype(triangles.dtype, np.integer) or len(triangles) == 0
            or int(triangles.min()) < 0 or int(triangles.max()) >= len(rest)):
        raise ValueError(f"sample {sample}: invalid topology")
    if not np.all(np.isfinite(rest)) or not np.all(np.isfinite(posed)):
        raise ValueError(f"sample {sample}: nonfinite vertices")
    return rest, posed, triangles, groups.astype(str)


def _lowest_ids(points, selected_ids, count):
    order = np.lexsort((selected_ids, points[:, 2]))
    return selected_ids[order[:count]]


def analyze_samples(model, source_sha256, samples):
    if set(samples) != set(SAMPLES):
        raise ValueError("exact samples 0, 7 and 8 required")
    validated = {sample: _validate_arrays(sample, samples[sample]) for sample in SAMPLES}
    base_rest, base_posed, base_triangles, base_groups = validated[0]
    for sample in SAMPLES[1:]:
        rest, _, triangles, groups = validated[sample]
        if not np.array_equal(triangles, base_triangles):
            raise ValueError(f"sample {sample}: topology changed")
        if not np.array_equal(groups, base_groups):
            raise ValueError(f"sample {sample}: dominant-group assignment changed")
        if not np.array_equal(rest, base_rest):
            raise ValueError(f"sample {sample}: rest vertices changed")

    suffixes = {}
    for suffix in ("l", "r"):
        labels = (f"foot_{suffix}", f"toe_{suffix}")
        selected_ids = np.flatnonzero(np.isin(base_groups, labels))
        if not len(selected_ids):
            raise ValueError(f"no foot/toe vertices for suffix {suffix}")
        label_counts = {label: int(np.count_nonzero(base_groups[selected_ids] == label))
                        for label in labels}
        if not all(label_counts.values()):
            raise ValueError(f"no foot/toe vertices for suffix {suffix}")
        standing_points = base_posed[selected_ids]
        low_count = max(1, math.ceil(len(selected_ids) * 0.01))
        standing_low_ids = _lowest_ids(standing_points, selected_ids, low_count)
        standing_centroid = standing_points.mean(axis=0)
        standing_minimum = float(standing_points[:, 2].min())
        rows = {}
        for sample in SAMPLES:
            points = validated[sample][1][selected_ids]
            displacement = points - standing_points
            lengths = np.linalg.norm(displacement, axis=1)
            low_ids = _lowest_ids(points, selected_ids, low_count)
            overlap = len(np.intersect1d(standing_low_ids, low_ids, assume_unique=True))
            centroid = points.mean(axis=0)
            rows[str(sample)] = {
                "minimum_z_m": float(points[:, 2].min()),
                "minimum_z_delta_from_standing_m":
                    float(points[:, 2].min() - standing_minimum),
                "lowest_one_percent_mean_z_m":
                    float(validated[sample][1][low_ids, 2].mean()),
                "lowest_one_percent_id_overlap_count": int(overlap),
                "lowest_one_percent_id_overlap_fraction": float(overlap / low_count),
                "centroid_xyz_m": _rounded(centroid),
                "centroid_delta_from_standing_m": _rounded(centroid - standing_centroid),
                "maximum_selected_vertex_displacement_m": float(lengths.max()),
                "rms_selected_vertex_displacement_m":
                    float(np.sqrt(np.mean(lengths * lengths))),
            }
        suffixes[suffix] = {
            "authored_suffix_NOT_anatomical_side": suffix,
            "selected_vertex_count": int(len(selected_ids)),
            "label_counts": label_counts,
            "standing_lowest_one_percent_vertex_count": int(low_count),
            "samples": rows,
        }

    return {
        "status": STATUS,
        "model": model,
        "source_sha256": source_sha256,
        "samples": list(SAMPLES),
        "axis_semantics": "source-authored XYZ; Z treated only as model vertical proxy",
        "standing_reference": "sample 0 lower envelope, not a verified ground plane",
        "source_unchanged": True,
        "ground_plane_verified": False,
        "contact_approval": False,
        "anatomical_side_verified": False,
        "authored_suffixes": suffixes,
    }


def load_model(model, path):
    evidence = Evidence(model, path)
    try:
        verify_member_hashes(model, evidence.read)
        diagnosis = evidence.load_json("diagnosis.json")
        if (diagnosis.get("model") != model
                or diagnosis.get("source_sha256") != SOURCES[model][0]
                or diagnosis.get("source_and_copy_unchanged") is not True
                or diagnosis.get("anatomical_approval") != "NOT_GRANTED"):
            raise ValueError(f"{model}: invalid source or preservation metadata")
        samples = {}
        for sample in SAMPLES:
            stem = f"{model}__squat__sample{sample:02d}"
            record = evidence.load_json(stem + "__triangles.json")
            if (record.get("sample_index") != sample
                    or record.get("geometry_file") != stem + "__geometry.npz"):
                raise ValueError(f"{stem}: file identity mismatch")
            with np.load(BytesIO(evidence.read(stem + "__geometry.npz")),
                         allow_pickle=False) as saved:
                samples[sample] = {
                    name: np.array(saved[name], copy=True)
                    for name in ("rest_vertices", "posed_vertices", "triangles",
                                 "dominant_groups")
                }
        return analyze_samples(model, SOURCES[model][0], samples)
    finally:
        evidence.close()


def markdown(report):
    lines = [
        "# Squat foot-surface lower-envelope proxy — read-only",
        "",
        "**No verified ground plane, anatomical side or contact approval.**",
        "Standing sample 0 is only a source-coordinate reference. Dominant foot/toe "
        "weight labels are selection proxies, not anatomical landmarks.",
    ]
    for model, result in report["models"].items():
        lines += ["", f"## {model}", "",
                  "| Authored suffix / sample | Selected vertices | Minimum Z delta vs standing | Centroid delta XYZ | Lowest 1% ID overlap |",
                  "|---|---:|---:|---|---:|"]
        for suffix, side in result["authored_suffixes"].items():
            for sample in ("0", "7", "8"):
                row = side["samples"][sample]
                delta = ", ".join(f"{x:.6f}" for x in row["centroid_delta_from_standing_m"])
                lines.append(
                    f"| `{suffix}` / {sample} | {side['selected_vertex_count']:,} | "
                    f"{row['minimum_z_delta_from_standing_m']:.9f} m | {delta} m | "
                    f"{row['lowest_one_percent_id_overlap_count']}/"
                    f"{side['standing_lowest_one_percent_vertex_count']} |")
    lines += ["", "These values are descriptive geometry only. They do not establish a floor, "
              "load distribution, balance, friction, pressure, physiological foot contact or "
              "safe squat technique.", ""]
    return "\n".join(lines)


def _aliases(first, second):
    first = Path(first)
    second = Path(second)
    if first.resolve(strict=False) == second.resolve(strict=False):
        return True
    try:
        return first.exists() and second.exists() and os.path.samefile(first, second)
    except OSError:
        return False


def write_outputs(report, out, evidence_paths):
    out = Path(out)
    json_path = out / "squat_foot_surface_proxy.json"
    markdown_path = out / "squat_foot_surface_proxy.md"
    outputs = (json_path, markdown_path)
    if _aliases(*outputs):
        raise ValueError("outputs must be outside and distinct from evidence")
    out_resolved = out.resolve(strict=False)
    for evidence_path in map(Path, evidence_paths):
        evidence_resolved = evidence_path.resolve(strict=False)
        if evidence_path.is_dir() and (
                out_resolved == evidence_resolved
                or out_resolved.is_relative_to(evidence_resolved)):
            raise ValueError("outputs must be outside and distinct from evidence")
        if any(_aliases(output, evidence_path) for output in outputs):
            raise ValueError("outputs must be outside and distinct from evidence")
    out.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown(report), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    for model in SOURCES:
        parser.add_argument("--" + model.lower(), type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    selected = {model: getattr(args, model.lower()) for model in SOURCES
                if getattr(args, model.lower()) is not None}
    if not selected:
        parser.error("at least one model evidence path is required")
    report = {
        "status": STATUS,
        "source_run": 39937882229,
        "models": {model: load_model(model, path) for model, path in selected.items()},
        "anatomical_approval": "NOT_GRANTED",
        "ground_contact_approval": "NOT_GRANTED",
    }
    write_outputs(report, args.out, selected.values())


if __name__ == "__main__":
    main()
