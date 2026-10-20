"""Read-only R56: certify individual ORIGINAL_v1 S7 key authority.

The previous R55 R47 material UNION is not permission to edit every key.
Only ORIGINAL R52 and R55 immutable captures are read; no model/key edits.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from original_review_r52_projection import allowed_dense
from original_review_r52_temporal import SOURCE

SOURCE_ANGLES = (110, 120, 130, 136, 145, 156, 166)
DENSE_ANGLES = np.arange(95, 167)
ANCHORS = (19057, 20913, 18081, 21057, 18057, 21044)


def checked_permissions(r47, frozen):
    """Keep the project's *existing* per-source and dense permissions distinct."""
    r47 = np.asarray(r47)
    frozen = np.asarray(frozen)
    if (r47.ndim != 2 or r47.shape[0] != 7 or
            frozen.shape != r47.shape or r47.dtype != bool or
            frozen.dtype != bool):
        raise ValueError("Invalid ORIGINAL R47 source mask inventories")
    dense = allowed_dense({"r47_allowed": r47})
    if dense.shape != (72, r47.shape[1]):
        raise ValueError("Malformed original dense mask")
    if (dense[[0, 15, 71]].any() or
            not np.array_equal(dense[SOURCE], r47 & (np.arange(7)[:,None] != 0) &
                               (np.arange(7)[:,None] != 6))):
        # Original 110/166 controls are separately zeroed in the dense contract.
        raise ValueError("Source and dense S7 restrictions disagree")
    if not np.array_equal(dense[[0, 15, 71]], np.zeros_like(dense[[0,15,71]])):
        raise ValueError("Ghost and original lockout nodes are editable")
    return dense


def source_key_rows(vertex, original, frozen, original_free, dense, delta):
    rows = []
    for j, angle in enumerate(SOURCE_ANGLES):
        node = int(SOURCE[j])
        rows.append(dict(angle_deg=int(angle),
                         existing_R47_source_allowed=bool(original[j, vertex]),
                         source_frozen_arm=bool(frozen[j, vertex]),
                         existing_free_array=bool(original_free[j,vertex]),
                         actual_R52_dense_control_allowed=bool(dense[node,vertex]),
                         actual_R52_control_magnitude_mm=float(
                             np.linalg.norm(delta[node,vertex])*1000)))
    return rows


def control_rows(vertex, dense, delta):
    return [dict(angle_deg=int(angle),
                 allowed=bool(dense[i,vertex]),
                 actual_R52_increment_mm=float(
                     np.linalg.norm(delta[i,vertex])*1000))
            for i, angle in enumerate(DENSE_ANGLES)]


def validate_inputs(source, solution, r55):
    rest = source["rest"]
    n = len(rest)
    if rest.ndim != 2 or rest.shape[1] != 3 or not np.isfinite(rest).all():
        raise ValueError("Invalid original rest vertices")
    r47 = np.asarray(source["r47_allowed"])
    frozen = np.asarray(source["frozen_arm"])
    free = np.asarray(source["free"])
    if free.shape != (7,n) or free.dtype != bool:
        raise ValueError("Invalid original source free mask")
    dense = checked_permissions(r47, frozen)
    delta = np.asarray(solution["dense_delta"])
    if (delta.shape != (72,n,3) or not np.isfinite(delta).all() or
            np.linalg.norm(delta,axis=2).max() > .045+1e-10 or
            np.any(delta[~dense] != 0)):
        raise ValueError("Original R52 delta escapes authorized material/cap")
    if r55["status"] != "READ_ONLY_R55_SCOPE_AUDIT_NOT_A_REPAIR":
        raise ValueError("R55 source not a signed diagnostic result")
    if (abs(float(r55["reproduced_R52_dense_motion_excess_mm"])-40.644618)>.05 or
            abs(float(r55["actual_S7_mute_R41_replay_max_mm"]))>.01 or
            int(r55["counts"]["total_back_vertices"]) != 1796):
        raise ValueError("R55 replay/identity does not match known native evidence")
    return rest, r47, frozen, free, dense, delta


def analyze(response_path, solution_path, prior_json):
    prior = json.loads(Path(prior_json).read_text())
    with np.load(response_path) as source, np.load(solution_path) as solution:
        rest, r47, frozen, free, dense, delta = validate_inputs(source, solution, prior)
        n = len(rest)
        hotspots = prior["top_40_motion_hotspots"]
        chosen = sorted(set(ANCHORS).union(int(h["vertex"]) for h in hotspots))
        if len(chosen) < 40 or max(chosen) >= n:
            raise ValueError("R55 hotspot inventory incomplete")
        original_union = r47.any(0)
        frozen_union = frozen.any(0)
        back = ((abs(rest[:,0])>.08) & (abs(rest[:,0])<.25) &
                (rest[:,2]>1.27) & (rest[:,2]<1.49) & (rest[:,1]>.025))
        if int(back.sum()) != 1796:
            raise ValueError("R53 back-region vertex inventory changed")
        rows = []
        for v in chosen:
            entries=source_key_rows(v,r47,frozen,free,dense,delta)
            ctl=control_rows(v,dense,delta)
            rows.append(dict(vertex=v,
                historical_R55_motion_excess_mm=next(
                    (h["max_dense_motion_excess_mm"] for h in hotspots if int(h["vertex"])==v),
                    prior["anchors"].get(str(v),{}).get("excess_mm")),
                back_motion_region=bool(back[v]),
                R47_any_source_allowed=bool(original_union[v]),
                source_frozen_in_one_or_more_keys=bool(frozen_union[v]),
                source_key_rows=entries,
                active_midpress_118_and_119=dict(
                    angle_118_allowed=ctl[118-95]["allowed"],
                    angle_119_allowed=ctl[119-95]["allowed"],
                    source_110_allowed=bool(r47[0,v]),
                    source_120_allowed=bool(r47[1,v]),
                    source_110_frozen=bool(frozen[0,v]),
                    source_120_frozen=bool(frozen[1,v])),
                existing_72_dense_controls=ctl))
        back_ids=np.flatnonzero(back)
        counts=[]
        for k,angle in enumerate(SOURCE_ANGLES):
            counts.append(dict(angle_deg=angle,
                original_R47_source_allowed_in_back=int(r47[k,back_ids].sum()),
                original_frozen_arm_in_back=int(frozen[k,back_ids].sum()),
                originally_free_source_in_back=int(free[k,back_ids].sum()),
                actual_dense_node_allowed_in_back=int(dense[int(SOURCE[k]),back_ids].sum())))
        top40=np.array([int(h["vertex"]) for h in hotspots],int)
        mid118=dense[118-95,top40]
        mid119=dense[119-95,top40]
        return dict(
            status="READ_ONLY_R56_PER_CONTROL_SCOPE_CERTIFICATE_NOT_REPAIRED",
            model_saved=False, approved=False, scope_expanded=False,
            original_R52_source_controls=list(SOURCE_ANGLES),
            dense_ghost_and_locked_angles=[95,110,166],
            marked_R47_shape_approval="historical marked outline only",
            original_unchanged_motion_limit_mm=0.5,
            R55_motion_excess_mm=float(prior["reproduced_R52_dense_motion_excess_mm"]),
            R55_S7_muted_R41_R52_back_replay_max_mm=float(
                prior["actual_S7_mute_R41_replay_max_mm"]),
            per_source_key_back_region_counts=counts,
            ranked_R55_top40_at_dense_118=dict(
                allowed_count=int(mid118.sum()),frozen_at_either_adjacent_source=int(
                    (frozen[0,top40] | frozen[1,top40]).sum()),
                allowed_despite_110_or_120_frozen=int((
                    mid118 & (frozen[0,top40] | frozen[1,top40])).sum())),
            ranked_R55_top40_at_dense_119=dict(allowed_count=int(mid119.sum())),
            per_vertex=rows,
            next_model_action="NONE: a targeted S7 adjustment requires separate proposal, native safety and owner visual review",
            limitations=[
                "Existing dense mask is union-derived at intermediate angles; it is NOT blanket authorization to change source-frozen material at neighboring knots.",
                "Source frozen_arm is a per-source array. Union across source knots overstates always-frozen or always-editable status.",
                "This audit reports original editing masks and current R52 amplitudes, not optimized new shapes or skin weights.",
                "The historical R47 outline is approved only at the marked pose; no full motion surface approval.",
                "Changing a permitted dense control can influence neighboring frames and vertices. Original 83/native/161/13 benchmarks and visual checks remain mandatory.",
                "No change to 26-vertex owner weight trial, canonical skeleton, helper transforms, Basis, skinning, topology or production assets."])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--response",required=True)
    p.add_argument("--solution",required=True)
    p.add_argument("--r55",required=True)
    p.add_argument("--out",required=True)
    opt=p.parse_args()
    report=analyze(opt.response,opt.solution,opt.r55)
    dest=Path(opt.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+chr(10))
    small={k:report[k] for k in (
       "status","dense_ghost_and_locked_angles",
       "R55_motion_excess_mm","R55_S7_muted_R41_R52_back_replay_max_mm",
       "per_source_key_back_region_counts",
       "ranked_R55_top40_at_dense_118")}
    small["anchors"]={str(v):next(row for row in report["per_vertex"]
                      if row["vertex"]==v)["active_midpress_118_and_119"] for v in (19057,20913)}
    print(json.dumps(small,indent=2))


if __name__=="__main__":
    main()
