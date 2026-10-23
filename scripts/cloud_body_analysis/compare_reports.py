"""Compare three immutable phone Blender JSON audits. Never opens or saves a .blend.

Centroid differences describe vertex-group influence distribution; they are neither
physical muscle attachments nor a mesh-quality ranking across changed topology.
"""
import argparse
import json
import math
from pathlib import Path

MODELS = ("W8", "V14", "R120")
EXPECTED = {
    "W8": "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c",
    "V14": "5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91",
    "R120": "fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb",
}
PAIRS = (("W8", "V14"), ("V14", "R120"), ("W8", "R120"))

def load_model(root, name):
    path = root / name
    def load(filename):
        return json.loads((path / filename).read_text(encoding="utf-8"))
    inventory = load("inventory.json")
    integrity = load("integrity_checks.json")
    audit = load("rest_anatomy_inventory.json")
    for doc in (inventory, integrity, audit):
        if doc["model"] != name or doc["source_sha256"] != EXPECTED[name]:
            raise ValueError(f"{name}: unexpected source hash or model name")
    if inventory["source_unchanged"] is not True or inventory["approved"] is not False:
        raise ValueError(f"{name}: source preservation / approval guard failed")
    if integrity["result"] != "PASS" or integrity["approval"] != "NOT_GRANTED":
        raise ValueError(f"{name}: report integrity not established")
    if audit["approval"] != "NOT_GRANTED":
        raise ValueError(f"{name}: report incorrectly claims model approval")
    if inventory["vertices"] != audit["mesh"]["vertices"]:
        raise ValueError(f"{name}: vertex count disagreement")
    if inventory["bones"] != len(audit["rig"]["bones"]):
        raise ValueError(f"{name}: bone count disagreement")
    if inventory["groups"] != len(audit["groups"]):
        raise ValueError(f"{name}: vertex-group count disagreement")
    if integrity["unweighted_vertices"] != audit["mesh"]["unweighted_vertices"]:
        raise ValueError(f"{name}: unweighted count disagreement")
    if len({g["name"] for g in audit["groups"]}) != inventory["groups"]:
        raise ValueError(f"{name}: duplicate vertex-group names")
    if len({b["name"] for b in audit["rig"]["bones"]}) != inventory["bones"]:
        raise ValueError(f"{name}: duplicate bone names")
    for group in audit["groups"]:
        xyz = group["weighted_centroid_body_local_m"]
        if xyz is not None and (len(xyz) != 3 or not all(math.isfinite(v) for v in xyz)):
            raise ValueError(f"{name}: nonfinite or invalid vertex-group centroid")
    return {"inventory": inventory, "integrity": integrity, "audit": audit}

def skeleton_signature(doc):
    return sorted((
        bone["name"], bone["parent"],
        tuple(bone["head_body_local_m"]),
        tuple(bone["tail_body_local_m"]), bone["use_deform"],
    ) for bone in doc["audit"]["rig"]["bones"])

def compare_pair(a, b, documents):
    left, right = documents[a]["audit"], documents[b]["audit"]
    la = {g["name"]: g for g in left["groups"]}
    rb = {g["name"]: g for g in right["groups"]}
    if la.keys() != rb.keys():
        raise ValueError(f"{a}/{b}: vertex-group names differ")
    differences = []
    for name in sorted(la):
        ga, gb = la[name], rb[name]
        v1, v2 = ga["weighted_centroid_body_local_m"], gb["weighted_centroid_body_local_m"]
        delta = None if v1 is None or v2 is None else round(math.dist(v1, v2) * 1000, 3)
        differences.append({
            "group": name, "centroid_separation_mm": delta,
            "influenced_vertices_a": ga["vertices_with_influence"],
            "influenced_vertices_b": gb["vertices_with_influence"],
        })
    differences.sort(key=lambda row: (
        row["centroid_separation_mm"] is None,
        -(row["centroid_separation_mm"] or 0), row["group"],
    ))
    return {
        "a": a, "b": b,
        "same_rest_bone_coordinates_at_six_decimal_metres":
            skeleton_signature(documents[a]) == skeleton_signature(documents[b]),
        "groups_compared": len(differences),
        "groups_with_centroid_shift_over_10mm":
            sum((x["centroid_separation_mm"] or 0) > 10 for x in differences),
        "largest_centroid_shifts": differences[:20],
    }

def build_report(root):
    documents = {model: load_model(root, model) for model in MODELS}
    pairs = [compare_pair(a, b, documents) for a, b in PAIRS]
    return {
        "status": "READ_ONLY_REPORT_INTEGRITY_PASS_ANATOMY_NOT_APPROVED",
        "run_ids": {m: documents[m]["inventory"]["run"] for m in MODELS},
        "source_sha256": EXPECTED,
        "models": {
            m: {
                "vertices": documents[m]["inventory"]["vertices"],
                "bones": documents[m]["inventory"]["bones"],
                "groups": documents[m]["inventory"]["groups"],
                "shape_keys": documents[m]["inventory"]["shape_keys"],
                "unweighted_vertices": documents[m]["integrity"]["unweighted_vertices"],
            } for m in MODELS
        },
        "pairs": pairs,
        "limitations": [
            "Reconstructed candidates are not verified original .blend files",
            "Bone positions are rounded to six decimals in body-local metres",
            "Weighted centroids are distribution summaries, not anatomical muscle anchors",
            "Different mesh densities/topologies prevent direct quality comparisons",
            "X-coordinate sign does not independently certify anatomical left/right",
            "Movement/deformation gates remain failed; model approval NOT_GRANTED",
            "Archived V14 expects 238067 vertices; reconstruction has 238065",
        ],
    }

def markdown(result):
    lines = [
        "# Home Gym PT read-only cloud Blender cross-model report", "",
        "**Status:** report integrity PASS; anatomy and archive equivalence NOT APPROVED.", "",
        "| Model | Vertices | Bones | Groups | Keys | Unweighted |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, x in result["models"].items():
        lines.append(f"| {name} | {x['vertices']:,} | {x['bones']} | {x['groups']} | {x['shape_keys']} | {x['unweighted_vertices']} |")
    for p in result["pairs"]:
        lines += [
            "", f"## {p['a']} to {p['b']}", "",
            f"Matching rest-bone coordinates to report precision: **{p['same_rest_bone_coordinates_at_six_decimal_metres']}**.",
            f"Weighted-centroid separations over 10 mm: **{p['groups_with_centroid_shift_over_10mm']}** of {p['groups_compared']} groups.",
            "", "| Group | Separation (mm) | Influenced vertices A to B |", "|---|---:|---:|",
        ]
        for entry in p["largest_centroid_shifts"][:12]:
            d = entry["centroid_separation_mm"]
            lines.append(f"| {entry['group']} | {d if d is not None else 'n/a'} | {entry['influenced_vertices_a']:,} to {entry['influenced_vertices_b']:,} |")
    lines += ["", "## Limitations", ""]
    lines += [f"- {limitation}" for limitation in result["limitations"]]
    lines += ["", "No .blend modified; no anatomical repair or muscle attachment authorized.", ""]
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = build_report(args.root)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "rest_comparison.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.out / "rest_comparison.md").write_text(markdown(result), encoding="utf-8")
    for p in result["pairs"]:
        print(p["a"], p["b"], "rest_equal", p["same_rest_bone_coordinates_at_six_decimal_metres"],
              "centroids_gt_10mm", p["groups_with_centroid_shift_over_10mm"])

if __name__ == "__main__":
    main()
