"""Pinned W8 fixed-rest-vertex edge-length continuity during a saved shoulder press.

Read-only geometric diagnostics, not anatomical elbow flexion/pronation validation.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from elbow_taper_audit import BANDS, W8_SHA, RIG_SHA, band_ids, controls
from track_rest_hotspots import Evidence, read_frame

FRAMES = (0, 6, 8)
STATUS = "W8_ELBOW_LOCAL_EDGE_RATIOS_DESCRIPTIVE_ANATOMY_NOT_APPROVED"


def region_edges(triangles, vertex_ids, vertex_count):
    """Unique mesh edges with BOTH vertices in one frozen rest-space band."""
    tri = np.asarray(triangles)
    ids = np.asarray(vertex_ids)
    if (tri.ndim != 2 or tri.shape[1] != 3 or not np.issubdtype(tri.dtype, np.integer)
        or ids.ndim != 1 or not np.issubdtype(ids.dtype, np.integer)
        or type(vertex_count) is not int or vertex_count <= 0
        or not len(ids) or len(np.unique(ids)) != len(ids)
        or int(ids.min()) < 0 or int(ids.max()) >= vertex_count
        or not len(tri) or int(tri.min()) < 0 or int(tri.max()) >= vertex_count):
        raise ValueError("invalid mesh topology or rest band IDs")
    mask = np.zeros(vertex_count, dtype=bool)
    mask[ids] = True
    edges = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        candidates = tri[:, [a, b]]
        selected = candidates[mask[candidates].all(axis=1)]
        if len(selected):
            edges.append(np.sort(selected, axis=1))
    if not edges:
        raise ValueError("no mesh edges in frozen rest band")
    unique = np.unique(np.concatenate(edges, axis=0), axis=0)
    if np.any(unique[:, 0] == unique[:, 1]) or len(unique) < 10:
        raise ValueError("degenerate or insufficient local mesh edges")
    return unique


def edge_ratios(rest, pose, edges):
    """Unitless corresponding edge length ratio; no normal tissue limit inferred."""
    rest = np.asarray(rest, dtype=float)
    pose = np.asarray(pose, dtype=float)
    edges = np.asarray(edges)
    if (rest.ndim != 2 or rest.shape[1] != 3 or pose.shape != rest.shape
        or edges.ndim != 2 or edges.shape[1] != 2
        or not np.issubdtype(edges.dtype, np.integer) or not len(edges)
        or int(edges.min()) < 0 or int(edges.max()) >= len(rest)
        or not np.isfinite(rest).all() or not np.isfinite(pose).all()):
        raise ValueError("invalid edge geometry")
    a = np.linalg.norm(rest[edges[:, 1]] - rest[edges[:, 0]], axis=1)
    b = np.linalg.norm(pose[edges[:, 1]] - pose[edges[:, 0]], axis=1)
    if np.any(a < 1e-8) or not np.isfinite(b).all():
        raise ValueError("zero-length or invalid rest edges")
    return b / a


def describe(ratios, baseline=None):
    r = np.asarray(ratios, dtype=float)
    if r.ndim != 1 or not len(r) or not np.isfinite(r).all() or np.any(r < 0):
        raise ValueError("invalid edge ratios")
    q = np.percentile(r, [5, 50, 95])
    result = {"min": round(float(np.min(r)), 6), "p05": round(float(q[0]), 6),
              "median": round(float(q[1]), 6), "p95": round(float(q[2]), 6),
              "max": round(float(np.max(r)), 6)}
    if baseline is not None:
        b = np.asarray(baseline, dtype=float)
        if b.shape != r.shape or not np.isfinite(b).all() or np.any(b < 0):
            raise ValueError("baseline edge identity/values invalid")
        result["p95_abs_ratio_change_from_pose_sample0"] = round(
            float(np.percentile(np.abs(r - b), 95)), 6)
    return result



def ranked_rest_edge_hotspots(rest, edges, ratios, top_n=5):
    """Deterministic mesh-edge IDs for reviewing extremes; NOT clinical thresholds.

    Same rest edge IDs across saved pose samples; ranks use no anatomical
    left/right inference. This does not label causes or approve deformation.
    """
    points = np.asarray(rest, dtype=float)
    links = np.asarray(edges)
    if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all()
        or links.ndim != 2 or links.shape[1] != 2
        or not np.issubdtype(links.dtype, np.integer) or len(links) == 0
        or int(links.min()) < 0 or int(links.max()) >= len(points)
        or np.any(links[:, 0] == links[:, 1])
        or len(np.unique(np.sort(links, axis=1), axis=0)) != len(links)
        or type(top_n) is not int or not 1 <= top_n <= 10
        or set(ratios) != set(FRAMES)):
        raise ValueError("invalid fixed-rest hotspot inputs")
    values = {i: np.asarray(ratios[i], dtype=float) for i in FRAMES}
    if any(v.shape != (len(links),) or not np.isfinite(v).all()
           or np.any(v < 0) for v in values.values()):
        raise ValueError("invalid saved pose edge ratios")

    def rows(indices):
        result = []
        for k in indices[:top_n]:
            a, b = map(int, links[k])
            result.append({
                "rest_mesh_edge_vertex_ids": [a, b],
                "rest_midpoint_body_local_m": [
                    round(float(v), 6) for v in (points[a] + points[b]) / 2],
                "pose_over_rest_edge_ratio_by_sample": {
                    str(i): round(float(values[i][k]), 6) for i in FRAMES},
                "abs_ratio_change_sample0_to_6": round(
                    float(abs(values[6][k] - values[0][k])), 6),
                "abs_ratio_change_sample0_to_8": round(
                    float(abs(values[8][k] - values[0][k])), 6)})
        return result

    def order(metric, reverse=False):
        return sorted(range(len(links)),
                      key=lambda k: ((-1 if reverse else 1) * float(metric[k]),
                                     int(min(links[k])), int(max(links[k]))))

    return {
        "interpretation": "Ranked fixed mesh edges only; not tissue strain, "
                          "anatomical landmarks, joint axes or repair coordinates.",
        "shortest_pose_over_rest_edges": {
            str(i): rows(order(values[i])) for i in FRAMES},
        "longest_pose_over_rest_edges": {
            str(i): rows(order(values[i], reverse=True)) for i in FRAMES},
        "largest_absolute_ratio_change_from_sample0": {
            str(i): rows(order(np.abs(values[i] - values[0]), reverse=True))
            for i in FRAMES if i != 0},
    }


def audit(w8, rig):
    axes = controls(rig)  # exact pinned W8 rig JSON member hash; unapproved anatomy
    source = Evidence("W8", w8)
    try:
        diagnosis = json.loads(source.read("diagnosis.json"))
        if (diagnosis.get("model") != "W8" or diagnosis.get("source_sha256") != W8_SHA
            or diagnosis.get("source_and_copy_unchanged") is not True
            or diagnosis.get("approved") is not False
            or diagnosis.get("anatomical_approval") != "NOT_GRANTED"):
            raise ValueError("pinned W8 diagnosis identity or approval mismatch")
        frames = {i: read_frame(source, "W8", "shoulder_press", i) for i in FRAMES}
        first = frames[0]
        if len(first["rest"]) != 219974:
            raise ValueError("unexpected W8 rest vertex count")
        fingerprint = first["record"]["triangle_indices_sha256"]
        for i, f in frames.items():
            record = next((r for r in diagnosis["paths"]["shoulder_press"]["frames"]
                           if r["sample_index"] == i), None)
            if (record is None or record["counts"] != f["record"]["counts"]
                or record["triangle_indices_sha256"] != fingerprint
                or f["record"]["triangle_indices_sha256"] != fingerprint
                or not np.array_equal(f["tri"], first["tri"])
                or not np.array_equal(f["rest"], first["rest"])
                or not np.array_equal(f["labels"], first["labels"])):
                raise ValueError("unstable rest topology, labels or diagnostic counts")
        regions = {}
        for suffix, (head, tail) in axes.items():
            regions[suffix] = {}
            for name, fraction in BANDS.items():
                ids = band_ids(first["rest"], first["labels"], head, tail, suffix, fraction)
                edges = region_edges(first["tri"], ids, len(first["rest"]))
                ratios = {i: edge_ratios(first["rest"], f["pose"], edges)
                          for i, f in frames.items()}
                regions[suffix][name] = {
                    "fixed_rest_vertex_count": int(len(ids)), "unique_mesh_edge_count": int(len(edges)),
                    "authored_upperarm_axis_fraction_NOT_elbow_joint": fraction,
                    "pose_samples": {str(i): describe(ratios[i], ratios[0]) for i in FRAMES},
                    "ranked_rest_edge_hotspots_NOT_anatomical_landmarks":
                        ranked_rest_edge_hotspots(first["rest"], edges, ratios)}
        return {"status": STATUS, "model": "W8", "source_blend_sha256": W8_SHA,
                "pinned_rig_json_sha256": RIG_SHA, "native_source_run": 39937882229,
                "native_rig_run": 40029398965, "triangle_indices_sha256": fingerprint,
                "sample_indices": list(FRAMES), "stable_rest_vertex_and_edge_ids": True,
                "suffixes_NOT_anatomical_sides": regions,
                "anatomical_side_verified": False, "isb_joint_axes_verified": False,
                "elbow_centre_verified": False, "forearm_pronation_tested": False,
                "generic_motion_tests_executed": 0, "skin_deformation_approved": False,
                "model_files_written": False, "muscle_attachments_approved": False,
                "clinical_rom_means_used_as_limits": False, "muscle_highlighting_implemented": False,
                "limitations": [
                    "Mesh edge ratios describe local surface strain proxies, not muscle or tissue strain.",
                    "Fixed rest bands use authored upperarm controls, not independently verified elbow landmarks.",
                    "Press samples 0/6/8 are not isolated elbow flexion or forearm pronation trials.",
                    "Surface edge ratios do not detect every collision, volume error or anatomical defect.",
                    "No universal human range limits, approved movement, cause or correction inferred."]}
    finally:
        source.close()


def markdown(report):
    lines = ["# W8 fixed-rest elbow-region edge continuity — read-only", "",
             "**ANATOMY AND SKIN NOT APPROVED.** Ratios are mesh-edge geometry only.", "",
             "| Authored suffix | Rest band | Edges | Press 0 p95 | Press 6 p95 | Press 8 p95 |",
             "|---|---|---:|---:|---:|---:|"]
    for suffix, regions in report["suffixes_NOT_anatomical_sides"].items():
        for name, row in regions.items():
            vals = row["pose_samples"]
            lines.append(f"| {suffix} | {name} | {row['unique_mesh_edge_count']} | " +
                         " | ".join(f"{vals[str(i)]['p95']:.4f}" for i in FRAMES) + " |")
    lines += ["", "All bands fixed in rest space. No elbow anatomical joint axis, radioulnar rotation or muscle attachment is validated.",
              "No model changes or clinical ROM clamping; existing shoulder press quality failures persist.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--w8", type=Path, required=True)
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.w8, args.rig)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "w8_elbow_edge_continuity.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "w8_elbow_edge_continuity.md").write_text(markdown(report))
    print(STATUS, "regions", sum(map(len, report["suffixes_NOT_anatomical_sides"].values())))


if __name__ == "__main__":
    main()
