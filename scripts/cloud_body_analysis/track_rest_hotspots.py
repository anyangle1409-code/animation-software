"""Read-only rest-space persistence of native pose failure triangles.

Inputs: immutable GitHub Actions diagnostic archives (or extracted directories).
The same triangle ID is comparable across sampled poses only inside one model
with unchanged rest triangle topology, coordinates, and dominant-group labels.
Group names identify inspection regions, not anatomical anchors or causes.
"""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import zipfile
import numpy as np

MODELS = {
    "W8": ("2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c",
           "3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e"),
    "V14": ("5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91",
            "5f11a9441cf5bb1d29ba3fae72c945f59c9109a26023cea15508d3310cb774e0"),
    "R120": ("fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb",
             "cf26902334a90cb3928821d797fcc88e27340a7837911a0e080b6973b5017a2f"),
}
FRAMES = {"shoulder_press": (0, 6, 8), "squat": (0, 7, 8)}
FLAG_CLASSES = {"stretched": "stretch_gt_2", "collapsed": "collapse_lt_0_1"}

class Evidence:
    def __init__(self, model, path):
        self.path = Path(path)
        if self.path.is_file():
            with self.path.open("rb") as f:
                if hashlib.file_digest(f, "sha256").hexdigest() != MODELS[model][1]:
                    raise ValueError(model + ": pinned ZIP hash mismatch")
        self.zip = zipfile.ZipFile(self.path) if self.path.is_file() else None
        if self.zip is None and not self.path.is_dir():
            raise ValueError("Missing evidence " + str(path))

    def read(self, name):
        name = "visual_evidence_new/" + name
        return self.zip.read(name) if self.zip else (self.path / name).read_bytes()

    def close(self):
        if self.zip:
            self.zip.close()

def read_frame(source, model, movement, sample):
    stem = f"{model}__{movement}__sample{sample:02d}"
    record = json.loads(source.read(stem + "__triangles.json"))
    if record["sample_index"] != sample or record["geometry_file"] != stem + "__geometry.npz":
        raise ValueError(stem + ": sample name/index mismatch")
    with np.load(BytesIO(source.read(stem + "__geometry.npz")), allow_pickle=False) as arrays:
        fields = ("triangles", "rest_vertices", "posed_vertices", "dominant_groups")
        if not set(fields + tuple(FLAG_CLASSES)).issubset(arrays.files):
            raise ValueError(stem + ": missing arrays")
        tri, rest, pose, labels = [arrays[k].copy() for k in fields]
        if (tri.ndim != 2 or tri.shape[1] != 3 or not np.issubdtype(tri.dtype, np.integer)
            or rest.ndim != 2 or rest.shape[1] != 3 or rest.shape != pose.shape
            or len(labels) != len(rest) or not len(rest) or not len(tri)
            or int(tri.min()) < 0 or int(tri.max()) >= len(rest)
            or not np.all(np.isfinite(rest)) or not np.all(np.isfinite(pose))):
            raise ValueError(stem + ": malformed or nonfinite rest/evaluated geometry")
        flags = {}
        for kind, key in FLAG_CLASSES.items():
            a = arrays[kind].copy()
            if (a.ndim != 1 or not np.issubdtype(a.dtype, np.integer)
                or not np.array_equal(a, np.asarray(record["flags"][kind]))
                or len(a) != record["counts"][key] or len(a) != len(np.unique(a))
                or (len(a) and (int(a.min()) < 0 or int(a.max()) >= len(tri)))):
                raise ValueError(stem + ": " + kind + " flags/counts invalid")
            flags[kind] = set(a.tolist())
    return {"tri": tri, "rest": rest, "pose": pose, "labels": labels,
            "flags": flags, "record": record}

def event_stats(frame, selected):
    ids = np.fromiter(sorted(selected), dtype=np.int64)
    result = {"count": int(len(ids)), "dominant_group_proxies": [],
              "top_5cm_REST_cells": [],
              "posed_centroid_displacement_mm": None}
    if not len(ids):
        return result
    triangles = frame["tri"][ids]
    labels = frame["labels"][triangles.ravel()]
    names, counts = np.unique(labels, return_counts=True)
    ranking = sorted(zip(names.tolist(), counts.tolist()), key=lambda r: (-r[1], r[0]))
    result["dominant_group_proxies"] = [
        {"label": n, "triangle_corner_equivalent": round(c / 3.0, 3)}
        for n, c in ranking[:12]
    ]
    rest_centres = frame["rest"][triangles].mean(axis=1)
    posed_centres = frame["pose"][triangles].mean(axis=1)
    xyz, counts = np.unique(np.floor(rest_centres / 0.05).astype(np.int32),
                            return_counts=True, axis=0)
    order = sorted(range(len(counts)), key=lambda i: (-int(counts[i]), tuple(xyz[i])))[:12]
    result["top_5cm_REST_cells"] = [
        {"xyz_bin": xyz[i].astype(int).tolist(),
         "centre_body_local_rest_m": [round((float(u) + 0.5) * 0.05, 4) for u in xyz[i]],
         "flagged_triangles": int(counts[i])} for i in order
    ]
    distances = np.linalg.norm(posed_centres - rest_centres, axis=1) * 1000
    result["posed_centroid_displacement_mm"] = {
        "median": round(float(np.median(distances)), 2),
        "p90": round(float(np.percentile(distances, 90)), 2),
        "max": round(float(np.max(distances)), 2),
    }
    return result

def process_path(source, diagnosis, model, path):
    frames = {n: read_frame(source, model, path, n) for n in FRAMES[path]}
    first, middle, last = FRAMES[path]
    tr0, rst0, lab0 = (frames[first][k] for k in ("tri", "rest", "labels"))
    signature = frames[first]["record"]["triangle_indices_sha256"]
    for n, f in frames.items():
        row = next((r for r in diagnosis["paths"][path]["frames"] if r["sample_index"] == n), None)
        if (row is None or row["counts"] != f["record"]["counts"]
            or row["triangle_indices_sha256"] != f["record"]["triangle_indices_sha256"]):
            raise ValueError(f"{model}/{path}: diagnostic summary mismatch")
        if (f["record"]["triangle_indices_sha256"] != signature
            or not np.array_equal(f["tri"], tr0) or not np.array_equal(f["rest"], rst0)
            or not np.array_equal(f["labels"], lab0)):
            raise ValueError(f"{model}/{path}: rest topology, coordinates or labels changed")
    output = {"samples": [first, middle, last], "stable_rest_topology": True,
              "triangle_indices_sha256": signature, "categories": {}}
    for kind in FLAG_CLASSES:
        a, b, c = [frames[n]["flags"][kind] for n in (first, middle, last)]
        events = {
            "new_at_middle_vs_start": b - a,
            "persisting_at_last_from_new_middle": (b - a) & c,
            "resolved_at_last_from_new_middle": (b - a) - c,
            "present_at_both_middle_and_last": b & c,
            "new_at_last_vs_start": c - a,
        }
        output["categories"][kind] = {
            "sample_counts": {str(n): len(frames[n]["flags"][kind]) for n in (first, middle, last)},
            "events": {k: event_stats(frames[last if k == "new_at_last_vs_start" else middle], v)
                       for k, v in events.items()},
        }
    return output

def analyse(paths):
    result = {"status": "READ_ONLY_TRIANGLE_TRACKING_ANATOMY_NOT_APPROVED",
              "source_run": 39937882229, "models": {},
              "limitations": [
                  "Only 3 saved samples per movement are available; no complete trajectory",
                  "All labels and 5cm rest XYZ bins are proxies, not verified anatomical landmarks",
                  "Displacement describes overall pose translation, not local tissue strain",
                  "Absolute triangle counts cannot rank models with different tessellations",
                  "Source reconstructions are not confirmed originals; no joint/anatomy/muscle approval",
              ]}
    for model in MODELS:
        e = Evidence(model, paths[model])
        try:
            d = json.loads(e.read("diagnosis.json"))
            if (d.get("model") != model or d.get("source_sha256") != MODELS[model][0]
                or d.get("source_and_copy_unchanged") is not True
                or d.get("approved") is not False or d.get("anatomical_approval") != "NOT_GRANTED"):
                raise ValueError(model + ": source hash/preservation/approval guard mismatch")
            result["models"][model] = {
                "source_sha256": MODELS[model][0], "anatomical_approval": "NOT_GRANTED",
                "movements": {path: process_path(e, d, model, path) for path in FRAMES},
            }
        finally:
            e.close()
    return result

def format_markdown(result):
    lines = ["# Home Gym PT — tracked rest-space pose-failure hotspots", "",
             "**READ ONLY — anatomical approval NOT_GRANTED.** These are reconstructed candidates.",
             "Triangle IDs are tracked within a model/path only when the exact rest geometry is unchanged.", ""]
    for model, data in result["models"].items():
        lines += [f"## {model}", "", "| Movement | Flag type | Start / middle / end | Newly flagged midway | Still flagged at end |",
                  "|---|---|---:|---:|---:|"]
        for movement, row in data["movements"].items():
            for kind, stats in row["categories"].items():
                counts = stats["sample_counts"]
                mid = stats["events"]["new_at_middle_vs_start"]
                retained = stats["events"]["persisting_at_last_from_new_middle"]
                lines.append(f"| {movement} | {kind} | " + " / ".join(str(counts[str(n)]) for n in row["samples"]) +
                             f" | {mid['count']} | {retained['count']} |")
                parts = [f"{v['label']} ({v['triangle_corner_equivalent']})"
                         for v in mid["dominant_group_proxies"][:6]]
                cells = [f"{c['centre_body_local_rest_m']} ({c['flagged_triangles']})"
                         for c in mid["top_5cm_REST_cells"][:4]]
                lines += ["", f"**{movement} / {kind}, new at middle:** weight-region proxies: " + ", ".join(parts),
                          "Most populated rest-space 5cm cells: " + ", ".join(cells), ""]
    lines += ["## Limitations", ""] + [f"- {v}" for v in result["limitations"]]
    lines += ["", "Original .blend files, bone locations, weights, production and PT_MODEL_VERSION 1.0 unchanged.", ""]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    for model in MODELS:
        parser.add_argument("--" + model.lower(), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyse({model: getattr(args, model.lower()) for model in MODELS})
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "tracked_rest_hotspots.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.out / "tracked_rest_hotspots.md").write_text(format_markdown(result))
    for model, data in result["models"].items():
        for path, entry in data["movements"].items():
            print(model, path, {k: v["events"]["new_at_middle_vs_start"]["count"]
                                for k, v in entry["categories"].items()})

if __name__ == "__main__":
    main()
