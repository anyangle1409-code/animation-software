"""R54 read-only S5/S7 interaction screen on authentic R53 161-pose captures.

No Blender or model write. Shape-key ablations are affine in key values under the
verified fixed linear skinning pose, but this screen does NOT certify mesh safety,
new contact, triangle normal orientation, anatomy or exercise acceptance.
"""
import argparse
import json
import sys
from pathlib import Path
import numpy as np


def combine(baseline, no_s5_delta, no_s7_delta, s5, s7):
    a, b, c = (np.asarray(x, dtype=np.float64) for x in
               (baseline, no_s5_delta, no_s7_delta))
    if (a.shape != b.shape or a.shape != c.shape or a.ndim != 3 or
            a.shape[0] != 161 or a.shape[-1] != 3 or
            not all(np.isfinite(x).all() for x in (a, b, c))):
        raise ValueError("Incomplete/nonfinite matching 161-pose captures")
    if not all(np.isfinite(t) and 0.0 <= t <= 2.0 for t in (s5, s7)):
        raise ValueError("Invalid corrective scale")
    # The ablation arrays are q_mute - q_active, not independent shape values.
    return a + (1.0 - s5) * b + (1.0 - s7) * c


def max_dense_motion_excess_mm(candidate, reference):
    candidate, reference = map(lambda v: np.asarray(v, dtype=np.float64),
                               (candidate, reference))
    if (candidate.shape != reference.shape or candidate.ndim != 3 or
            candidate.shape[0] != 161 or candidate.shape[-1] != 3 or
            not np.isfinite(candidate).all() or not np.isfinite(reference).all()):
        raise ValueError("Invalid full-length point histories")
    # Existing R52 normalization: (160 / 40)^2, NOT physical mm/s^2.
    second = lambda x: x[2:] - 2.0 * x[1:-1] + x[:-2]
    # Exact original R52 guard: compare the magnitudes of each trajectory's
    # second difference; do NOT take the norm of the vector difference.
    before = np.linalg.norm(second(reference), axis=2)
    after = np.linalg.norm(second(candidate), axis=2)
    return float((after-before).max() * 1000.0 * 16.0)


def locate_subset(whole, subset):
    whole, subset = np.asarray(whole), np.asarray(subset)
    if (whole.ndim != 1 or subset.ndim != 1 or len(whole) == 0 or
            not np.issubdtype(whole.dtype, np.integer) or
            not np.issubdtype(subset.dtype, np.integer) or
            not np.all(np.diff(whole) > 0) or
            not np.all(np.diff(subset) > 0)):
        raise ValueError("Vertex inventories must be strictly increasing")
    idx = np.searchsorted(whole, subset)
    if (not len(subset) or idx.max(initial=-1) >= len(whole) or
            not np.array_equal(whole[idx], subset)):
        raise ValueError("Back vertices absent from shoulder inventory")
    return idx


def analyze(capture, source_path):
    capture = Path(capture)
    with np.load(source_path) as src, np.load(capture / "r52" / "rest_weights.npz") as mesh, \
         np.load(capture / "r52" / "clip.npz") as r52, \
         np.load(capture / "r41" / "clip.npz") as r41, \
         np.load(capture / "r52" / "snapshots.npz") as snapshots:
        idx = locate_subset(mesh["shoulder_ids"], mesh["back_ids"])
        baseline_back = np.asarray(r52["back_points"], dtype=np.float64)
        reference_back = np.asarray(r41["back_points"], dtype=np.float64)
        baseline_shoulder = np.asarray(r52["baseline"], dtype=np.float64)
        if (baseline_shoulder.shape[0] != 161 or
                not np.array_equal(baseline_shoulder[:, idx].astype(np.float32),
                                   baseline_back.astype(np.float32))):
            raise ValueError("Captured shoulder/back histories do not match")
        if not np.array_equal(r52["bone_matrices"], r41["bone_matrices"]):
            raise ValueError("R41/R52 bone motion differs: invalid attribution")
        delta5, delta7 = r52["no_S5"][:, idx], r52["no_S7"][:, idx]
        # Reuse the original unchanged owner-profile outline algorithm.
        sys.path.insert(0, str(Path(__file__).resolve().parent / "tests"))
        from test_original_review_r48_approved_outline import outline
        faces = src["faces"]
        target_outline = outline(src["r48_profile_target_points"], faces)
        baseline_full = snapshots["baseline_100"]
        active_outline = float(abs(outline(baseline_full, faces) -
                                   target_outline).max() * 1000.0)
        # A real-world capture guard: require the known R52 marked frame and
        # original dense-motion failures to reproduce before screening.
        active_motion = max_dense_motion_excess_mm(baseline_back, reference_back)
        if abs(active_outline - 0.949948) > 0.02:
            raise ValueError("Cannot reproduce authentic R52 profile measurement")
        if abs(active_motion - 40.644618) > 0.05:
            raise ValueError("Cannot reproduce authentic R52 161-pose measurement")

        rows = []
        scales = (0.90, 0.95, 1.0, 1.05, 1.10)
        for s5 in scales:
            for s7 in scales:
                q = combine(baseline_back, delta5, delta7, s5, s7)
                full_mark = (baseline_full +
                             (1.0-s5)*(snapshots["no_S5_100"]-baseline_full) +
                             (1.0-s7)*(snapshots["no_S7_100"]-baseline_full))
                err = float(abs(outline(full_mark, faces)-target_outline).max()*1000.0)
                motion = max_dense_motion_excess_mm(q, reference_back)
                rows.append(dict(s5_scale=s5, s7_scale=s7,
                                 approved_R47_marked_outline_error_mm=err,
                                 dense_motion_excess_mm=motion,
                                 historical_outline_1mm_guard_met=bool(err <= 1.0),
                                 original_motion_0_5mm_guard_met=bool(motion <= 0.5)))
        baseline = next(row for row in rows if row["s5_scale"] == 1.0 and
                        row["s7_scale"] == 1.0)
        if (abs(baseline["approved_R47_marked_outline_error_mm"]-active_outline) > 1e-6
                or abs(baseline["dense_motion_excess_mm"]-active_motion) > 1e-6):
            raise ValueError("Reference scale failed to reproduce R52 baseline")
        ordered = sorted(rows, key=lambda row: (
            not row["historical_outline_1mm_guard_met"],
            row["dense_motion_excess_mm"],
            row["approved_R47_marked_outline_error_mm"]))
        return dict(
            status="DIAGNOSTIC_SCREEN_ONLY_NOT_ACCEPTED",
            model_saved=False, production_ready=False, anatomy_verified=False,
            real_r53_capture_verified=True, source_frame_count=161,
            active_baseline=baseline, combinations_checked=len(rows),
            combinations_meeting_both_screen_guards=sum(
                r["historical_outline_1mm_guard_met"] and
                r["original_motion_0_5mm_guard_met"] for r in rows),
            tested_scales=list(scales), rows=rows, best_screened_pair=ordered[0],
            limitations=[
                "Linear key scaling is exact only under the captured unchanged LBS poses and weights.",
                "Only S5/S7 global influence multipliers are screened; this is not a fitted local weight/shape candidate.",
                "The R47 outline guard is checked at the historical marked pose, not across every press frame.",
                "No contact, area, reversed-normal, crease, early-outward, spatial-weight-change or 13-benchmark safety tests ran on altered scales.",
                "The earlier authorised 26-vertex weight smoothing was rejected; no weight change is proposed or adopted here.",
                "No model, rig, bone, skin weight, shape-key geometry or source capture is modified.",
                "Screen success is not native Blender acceptance or owner visual approval."])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    opts = parser.parse_args()
    report = analyze(opts.capture, opts.source)
    out = Path(opts.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(status=report["status"],
                          active=report["active_baseline"],
                          best_screened_pair=report["best_screened_pair"],
                          both_screen_guards=report["combinations_meeting_both_screen_guards"])))
    # Diagnostics may complete without any safe candidate: do not make CI green
    # conditional on an anatomically satisfactory pair.
if __name__ == "__main__":
    main()
