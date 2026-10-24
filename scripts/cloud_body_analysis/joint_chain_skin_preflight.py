"""Synthetic-only full-body relative-frame and skin-edge continuity preflight.

Generic SO(3) angles are not ISB joint coordinates. No native model, muscle
attachment, ROM limit or skin deformation is certified or modified.
"""
import argparse
import json
import math
from pathlib import Path

from frame_math_contract import dot, point3, rotation_angle_degrees, verify_axes

PAIRS = (
    ("shoulder_clavicle", "thorax", "clavicle"),
    ("shoulder_scapula", "thorax", "scapula"),
    ("shoulder_glenohumeral_proxy", "scapula", "humerus"),
    ("elbow_forearm_proxy", "humerus", "forearm"),
    ("hip_proxy", "pelvis", "femur"),
    ("knee_proxy", "femur", "tibia"),
    ("ankle_hindfoot_proxy", "tibia", "hindfoot"),
    ("foot_forefoot_proxy", "hindfoot", "forefoot"),
)
STATUS = "SYNTHETIC_JOINT_CHAIN_SKIN_PREFLIGHT_NOT_NATIVE_OR_ANATOMICAL_VALIDATION"


def _rotation(parent, child):
    pa, ch = verify_axes(parent["axes"]), verify_axes(child["axes"])
    return tuple(tuple(dot(ch[j], pa[i]) for i in range(3)) for j in range(3))


def _edge_length(vertices, edge):
    a, b = (point3(vertices[str(i)]) for i in edge)
    return math.dist(a, b)


def analyze(data):
    if (data.get("source_kind") != "INVENTED_SYNTHETIC_FIXTURES"
        or data.get("native_landmarks_bound") != 0
        or data.get("anatomical_approval") is not False
        or data.get("native_motion_tests_executed") != 0):
        raise ValueError("synthetic-only, unapproved provenance required")
    samples = data.get("samples")
    if not isinstance(samples, list) or len(samples) < 3:
        raise ValueError("need start, intermediate, return samples")
    if [s.get("index") for s in samples] != list(range(len(samples))):
        raise ValueError("sample indices must be consecutive and unique")
    required = {seg for _, a, b in PAIRS for seg in (a, b)}
    edges = data.get("edges")
    if not isinstance(edges, list) or not edges:
        raise ValueError("nonempty stable mesh-edge list required")
    canonical = set()
    for edge in edges:
        if (not isinstance(edge, (list, tuple)) or len(edge) != 2
            or any(not isinstance(i, int) or isinstance(i, bool) or i < 0 for i in edge)
            or edge[0] == edge[1]):
            raise ValueError("invalid mesh edge")
        key = tuple(sorted(edge))
        if key in canonical:
            raise ValueError("duplicate undirected mesh edge")
        canonical.add(key)
    reference_ids = None
    for sample in samples:
        frames = sample.get("segments")
        verts = sample.get("skin_vertices")
        if not isinstance(frames, dict) or set(frames) != required:
            raise ValueError("full-body reference segment set mismatch")
        if not isinstance(verts, dict):
            raise ValueError("skin vertices missing")
        if reference_ids is None:
            reference_ids = set(verts)
        if set(verts) != reference_ids:
            raise ValueError("mesh topology or vertex identifiers changed")
        for frame in frames.values():
            point3(frame["origin"])
            verify_axes(frame["axes"])
        for value in verts.values():
            point3(value)
        for a, b in edges:
            if str(a) not in verts or str(b) not in verts:
                raise ValueError("edge endpoint absent")
    base = samples[0]
    chain = []
    for label, parent, child in PAIRS:
        ref = {"axes": _rotation(base["segments"][parent], base["segments"][child])}
        angles = []
        for sample in samples:
            rel = {"axes": _rotation(sample["segments"][parent], sample["segments"][child])}
            angles.append(round(rotation_angle_degrees(ref, rel), 7))
        chain.append({"generic_pair": label, "parent": parent, "child": child,
                      "unsigned_relative_orientation_change_deg_NOT_ISB": angles,
                      "returned_to_reference_deg": angles[-1]})
    continuity = []
    for edge in edges:
        base_length = _edge_length(base["skin_vertices"], edge)
        if not math.isfinite(base_length) or base_length < 1e-9:
            raise ValueError("zero-length or nonfinite reference edge")
        ratios = []
        for sample in samples:
            length = _edge_length(sample["skin_vertices"], edge)
            if not math.isfinite(length):
                raise ValueError("nonfinite mesh edge length")
            ratios.append(round(length / base_length, 7))
        continuity.append({"vertex_ids": list(edge), "reference_length_m": base_length,
                           "mesh_edge_length_ratios_NOT_tissue_strain": ratios})
    return {"status": STATUS, "source_kind": "INVENTED_SYNTHETIC_FIXTURES",
            "native_model_used": False, "native_landmarks_bound": 0,
            "isb_joint_frames_calibrated": False, "anatomical_side_verified": False,
            "generic_motion_tests_executed": 0, "skin_deformation_approved": False,
            "muscle_attachment_approved": False, "clinical_rom_limits_applied": False,
            "sample_count": len(samples), "chain_pairs": chain, "skin_edges": continuity,
            "unrepresented_anatomical_dependencies": [
                "Independent humeral epicondyles and radius/ulna segment frames",
                "Thorax/scapula/clavicle joint centres and reviewed side axes",
                "Pelvic/hip/knee/ankle joint centres, foot/toe frames and ground contact",
                "Validated native mesh topology, poses, collisions and skin continuity",
            ],
            "limitations": [
                "Relative SO(3) angle is unsigned, not joint flexion, pronation or scapular tilt.",
                "Mesh edge ratios are geometry descriptors, not muscle or tissue strain.",
                "No clinical population ROM means or confidence intervals used as limits.",
                "All frames, coordinates, rotations and edges are invented fixtures.",
            ]}


def synthetic_fixture():
    names = {seg for _, a, b in PAIRS for seg in (a, b)}
    poses = [dict.fromkeys(names, 0.0), {
        "thorax": 0, "clavicle": 10, "scapula": 15, "humerus": 30,
        "forearm": 45, "pelvis": 0, "femur": 25, "tibia": 40,
        "hindfoot": 15, "forefoot": 10,
    }, dict.fromkeys(names, 0.0)]
    samples = []
    for index, angles in enumerate(poses):
        frames = {}
        for name, deg in angles.items():
            c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            frames[name] = {"origin": [0.0, 0.0, 0.0],
                            "axes": [[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]]}
        samples.append({"index": index, "segments": frames,
                        "skin_vertices": {"1": [0, 0, 0],
                                          "2": [1.2 if index == 1 else 1, 0, 0],
                                          "3": [0, 1, 0]}})
    return {"source_kind": "INVENTED_SYNTHETIC_FIXTURES",
            "native_landmarks_bound": 0, "anatomical_approval": False,
            "native_motion_tests_executed": 0, "edges": [[1, 2], [1, 3]],
            "samples": samples}


def markdown(report):
    lines = ["# Synthetic full-body joint-chain and skin-edge preflight", "",
             "**INVENTED TEST COORDINATES — NO BLENDER MODEL OR ANATOMY VALIDATED.**", "",
             "| Generic relative segment pair | Intermediate rotation change (° unsigned) | Return (°) |",
             "|---|---:|---:|"]
    for pair in report["chain_pairs"]:
        values = pair["unsigned_relative_orientation_change_deg_NOT_ISB"]
        lines.append(f"| {pair['generic_pair']} | {values[1]:.4f} | {values[-1]:.4f} |")
    lines += ["", "| Synthetic mesh edge | Intermediate length / rest | Return / rest |",
              "|---|---:|---:|"]
    for edge in report["skin_edges"]:
        values = edge["mesh_edge_length_ratios_NOT_tissue_strain"]
        lines.append(f"| {edge['vertex_ids']} | {values[1]:.4f} | {values[-1]:.4f} |")
    lines += ["", "The 46 real landmarks remain unbound; 0/19 native generic motion tests approved.",
              "No ISB axes, anatomical sides, physiological strain, ROM limits or muscle attachments established.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(synthetic_fixture())
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "synthetic_joint_chain_skin_preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "synthetic_joint_chain_skin_preflight.md").write_text(markdown(report))
    print(STATUS, len(report["chain_pairs"]), "pairs", len(report["skin_edges"]), "edges")


if __name__ == "__main__":
    main()
