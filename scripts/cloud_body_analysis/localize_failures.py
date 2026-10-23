"""Home Gym PT: pinned, read-only native pose failure localization.

Reads previous GitHub Actions JSON/NPZ evidence; never opens/saves a .blend.
Dominant weight labels are inspection proxies, not anatomical causes or anchors.
"""
from __future__ import annotations
import argparse
from collections import Counter
from io import BytesIO
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np

SOURCES = {
    "W8": ("2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c",
           "3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e"),
    "V14": ("5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91",
            "5f11a9441cf5bb1d29ba3fae72c945f59c9109a26023cea15508d3310cb774e0"),
    "R120": ("fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb",
             "cf26902334a90cb3928821d797fcc88e27340a7837911a0e080b6973b5017a2f"),
}
FRAMES = {"shoulder_press": (0, 6, 8), "squat": (0, 7, 8)}
CATEGORIES = {"collapsed": "collapse_lt_0_1", "stretched": "stretch_gt_2",
              "intersections": "self_intersecting_pairs"}


class Evidence:
    def __init__(self, model, path):
        self.path = Path(path)
        self.zip = zipfile.ZipFile(self.path) if self.path.is_file() else None
        if self.zip:
            with open(self.path, "rb") as f:
                if hashlib.file_digest(f, "sha256").hexdigest() != SOURCES[model][1]:
                    raise ValueError(f"{model}: diagnostic ZIP hash mismatch")
        elif not self.path.is_dir():
            raise ValueError(f"{model}: diagnostic evidence missing")

    def read(self, name):
        item = "visual_evidence_new/" + name
        return self.zip.read(item) if self.zip else (self.path / item).read_bytes()

    def load_json(self, name):
        return json.loads(self.read(name))

    def close(self):
        if self.zip:
            self.zip.close()


def top_groups(groups, triangles, flagged):
    if not len(flagged):
        return []
    labels = groups[triangles[flagged].reshape(-1)]
    names, counts = np.unique(labels, return_counts=True)
    ranked = sorted(zip(names, counts), key=lambda t: (-int(t[1]), str(t[0])))
    return [{"group_label": str(n), "triangle_corner_equivalent": round(int(c) / 3, 3)}
            for n, c in ranked[:12]]


def bins(vertices, triangles, flagged, size=0.05):
    if not len(flagged):
        return []
    centres = vertices[triangles[flagged]].mean(axis=1)
    coords, amounts = np.unique(np.floor(centres / size).astype(np.int32),
                                axis=0, return_counts=True)
    order = sorted(range(len(amounts)), key=lambda i: (-int(amounts[i]),
                   tuple(int(v) for v in coords[i])))[:8]
    return [{"xyz_cell": [int(v) for v in coords[i]],
             "centre_evaluated_m": [round((float(v) + 0.5) * size, 4) for v in coords[i]],
             "flagged_triangles": int(amounts[i])} for i in order]


def sample(evidence, model, movement, number):
    stem = f"{model}__{movement}__sample{number:02d}"
    record = evidence.load_json(stem + "__triangles.json")
    if record["sample_index"] != number or record["geometry_file"] != stem + "__geometry.npz":
        raise ValueError(f"{stem}: file identity mismatch")
    with np.load(BytesIO(evidence.read(stem + "__geometry.npz")), allow_pickle=False) as saved:
        tri, xyz, groups = saved["triangles"], saved["posed_vertices"], saved["dominant_groups"]
        if (tri.ndim != 2 or tri.shape[1] != 3 or
            not np.issubdtype(tri.dtype, np.integer) or len(tri) == 0 or
            xyz.ndim != 2 or xyz.shape[1] != 3 or len(xyz) == 0 or
            len(groups) != len(xyz)):
            raise ValueError(f"{stem}: invalid geometry arrays")
        if int(tri.min()) < 0 or int(tri.max()) >= len(xyz) or not np.all(np.isfinite(xyz)):
            raise ValueError(f"{stem}: bad topology indices or nonfinite positions")
        result = {"sample": number, "t": record["t"], "counts": record["counts"],
                  "rest_triangles_sha256": record["triangle_indices_sha256"], "flags": {}}
        raw = {}
        for category, count_name in CATEGORIES.items():
            flagged = np.asarray(saved[category], dtype=np.int64)
            expected = np.asarray(record["flags"][category], dtype=np.int64)
            if category == "intersections":
                expected = expected.reshape(-1, 2)
                if flagged.ndim != 2 or flagged.shape[1] != 2:
                    raise ValueError(f"{stem}: invalid intersecting pair array")
            elif flagged.ndim != 1:
                raise ValueError(f"{stem}: invalid flag vector")
            if not np.array_equal(flagged, expected) or len(flagged) != record["counts"][count_name]:
                raise ValueError(f"{stem}: {category} counts or flags differ")
            if flagged.size and (int(flagged.min()) < 0 or int(flagged.max()) >= len(tri)):
                raise ValueError(f"{stem}: out-of-range flagged triangle")
            raw[category] = flagged
            distinct = np.unique(flagged.reshape(-1))
            result["flags"][category] = {
                "records": int(len(flagged)), "distinct_triangles": int(len(distinct)),
                "dominant_group_proxies": top_groups(groups, tri, distinct),
                "top_5cm_evaluated_coordinate_bins": bins(xyz, tri, distinct),
            }
        result["reported_collision_classes"] = record["metrics"].get("self_intersection_classes_top", [])
        return result, raw


def grip_report(diagnosis):
    trials = diagnosis["paths"]["grip"].get("grip_trials", [])
    passing_pairs = [x for x in trials if isinstance(x.get("pairs"), int) and x["pairs"] <= 5]
    return {
        "trial_count": len(trials),
        "runtime_suffix_counts": dict(sorted(Counter(x.get("runtime_suffix", "?") for x in trials).items())),
        "trials_meeting_collision_pair_limit": len(passing_pairs),
        "hand_collapse_for_those_trials": [x.get("hand_collapse") for x in passing_pairs],
        "status": "UNRESOLVED_COMBINED_GRIP_ACCEPTANCE",
        "limitations": "Finite grid; untested suffix has no positive or negative result",
    }


def process(model, path):
    evidence = Evidence(model, path)
    try:
        diagnosis = evidence.load_json("diagnosis.json")
        if diagnosis["model"] != model or diagnosis["source_sha256"] != SOURCES[model][0]:
            raise ValueError(f"{model}: wrong model identity or source SHA256")
        if (diagnosis["approved"] is not False or
            diagnosis["anatomical_approval"] != "NOT_GRANTED" or
            diagnosis["source_and_copy_unchanged"] is not True):
            raise ValueError(f"{model}: source-preservation/approval guard violation")
        result = {"model": model, "source_sha256": SOURCES[model][0],
                  "source_unchanged": True, "anatomical_approval": "NOT_GRANTED",
                  "visual_diagnostic_run": 39937882229, "paths": {}, "grip": grip_report(diagnosis)}
        for movement, samples in FRAMES.items():
            frames, raws = [], {}
            for number in samples:
                frame, arrays = sample(evidence, model, movement, number)
                declared = next((x for x in diagnosis["paths"][movement]["frames"]
                                 if x["sample_index"] == number), None)
                if (declared is None or declared["counts"] != frame["counts"] or
                    declared["triangle_indices_sha256"] != frame["rest_triangles_sha256"]):
                    raise ValueError(f"{model}/{movement}: inconsistent summary evidence")
                frames.append(frame)
                raws[number] = arrays
            if len({x["rest_triangles_sha256"] for x in frames}) != 1:
                raise ValueError(f"{model}/{movement}: changed rest triangle ID fingerprint")
            persistence = {}
            for category in ("collapsed", "stretched"):
                first = set(raws[samples[0]][category].tolist())
                late = [set(raws[point][category].tolist()) for point in samples[1:]]
                persistence[category] = {
                    "new_vs_initial": {str(i): len(s-first) for i, s in zip(samples[1:], late)},
                    "from_initial_still_flagged": {str(i): len(s & first) for i, s in zip(samples[1:], late)},
                    "same_flag_at_two_later_samples": len(late[0] & late[1]),
                }
            result["paths"][movement] = {"samples": frames, "flag_persistence": persistence}
        return result
    finally:
        evidence.close()


def markdown(report):
    lines = ["# Home Gym PT — read-only movement failure localization", "",
             "**Anatomy NOT APPROVED.** Saved evidence is from unverified reconstructions.",
             "Dominant weight groups are geometric labels, not confirmed muscle attachments.",
             "5 cm coordinate bins are for spatial investigation only.", ""]
    for model, doc in report["models"].items():
        lines += [f"## {model}", "",
                  "| Movement / sample | Collapse | Stretch | Collision pairs | Top stretch-group labels |",
                  "|---|---:|---:|---:|---|"]
        for name in FRAMES:
            for frame in doc["paths"][name]["samples"]:
                c = frame["counts"]
                gs = frame["flags"]["stretched"]["dominant_group_proxies"][:4]
                labels = ", ".join(f"{x['group_label']} ({x['triangle_corner_equivalent']})" for x in gs)
                lines.append(f"| {name} / {frame['sample']} | {c['collapse_lt_0_1']:,} | "
                             f"{c['stretch_gt_2']:,} | {c['self_intersecting_pairs']:,} | {labels} |")
        grip = doc["grip"]
        lines += ["", f"Grip: {grip['trial_count']} attempted configurations, "
                  f"suffix counts {grip['runtime_suffix_counts']}, "
                  f"{grip['trials_meeting_collision_pair_limit']} at pair threshold; no accepted grip.", ""]
    lines += ["## Interpretation", "",
              "- Counts from different mesh topologies are not a model-quality ranking.",
              "- Within a fixed topology, changing flagged triangle IDs across samples can be tracked.",
              "- Intersecting pairs are not equivalent to distinct involved triangles.",
              "- Runtime side suffixes are not independently verified anatomical sides.",
              "- Archive equivalence, anatomy, grip, movement and production approval remain failed or blocked.",
              "- No models or PT_MODEL_VERSION were changed.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    for model in SOURCES:
        ap.add_argument("--" + model.lower(), type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    report = {"status": "READ_ONLY_ANATOMY_NOT_GRANTED", "source_run": 39937882229,
              "models": {model: process(model, getattr(args, model.lower())) for model in SOURCES}}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "movement_failure_localization.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "movement_failure_localization.md").write_text(markdown(report))
    for model, item in report["models"].items():
        for movement, p in item["paths"].items():
            print(model, movement, [(f["sample"], f["counts"]) for f in p["samples"]])


if __name__ == "__main__":
    main()
