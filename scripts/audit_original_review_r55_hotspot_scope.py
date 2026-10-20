"""R55 read-only, source-pinned R52/R53 posterior shoulder hotspot and scope audit.

No weights, correctives, bones, shape keys, model files or acceptance limits edited.
All reported distances along REST mesh edges, not Euclidean across skin folds.
"""
import argparse
import heapq
import json
from pathlib import Path
import numpy as np


def dense_per_vertex_excess_mm(reference, actual):
    """Exactly the original dense R52 norm-of-second-difference metric per vertex."""
    a, b = np.asarray(reference, float), np.asarray(actual, float)
    if (a.shape != b.shape or a.ndim != 3 or a.shape[0] != 161 or
            a.shape[-1] != 3 or not np.isfinite(a).all() or
            not np.isfinite(b).all()):
        raise ValueError("Invalid 161-pose matching back trajectories")
    second = lambda x: x[2:] - 2*x[1:-1] + x[:-2]
    return (np.linalg.norm(second(b), axis=2) -
            np.linalg.norm(second(a), axis=2)).max(axis=0)*16000.0


def allowed_weight_scope(spec, allowed_union, frozen_union, vertex_count):
    """Verify the historical owner-approved 26-vertex *trial* without expanding it."""
    edit = np.asarray(spec["proposed_edit_vertices"], dtype=int)
    excluded = np.asarray(spec["excluded_source_frozen_vertices"], dtype=int)
    if (edit.shape != (26,) or np.unique(edit).size != 26 or
            (edit < 0).any() or (edit >= vertex_count).any() or
            np.intersect1d(edit, excluded).size or
            not allowed_union[edit].all() or frozen_union[edit].any()):
        raise ValueError("R53 26-vertex scope identity failed")
    if (tuple(spec["seed_edge"]) != (18081, 21057) or
            tuple(spec["mirror_edge"]) != (18057, 21044)):
        raise ValueError("Unexpected source edge identities")
    if not np.all(np.isin(np.asarray(spec["vertices"]), np.r_[edit, excluded])):
        raise ValueError("Inconsistent source patch")
    return edit


def geodesic_to_patch_mm(rest, edges, patch):
    """Multi-source shortest paths along actual rest-mesh edges."""
    rest, edges, patch = np.asarray(rest), np.asarray(edges), np.asarray(patch)
    n = len(rest)
    if (rest.shape != (n,3) or edges.ndim != 2 or edges.shape[1] != 2 or
            not np.isfinite(rest).all() or (edges < 0).any() or
            (edges >= n).any() or patch.size == 0 or
            (patch < 0).any() or (patch >= n).any()):
        raise ValueError("Bad topology or rest coordinates")
    adj = [[] for _ in range(n)]
    for i,j in edges:
        i,j=int(i),int(j)
        length=float(np.linalg.norm(rest[i]-rest[j]))
        adj[i].append((j,length))
        adj[j].append((i,length))
    distance = np.full(n,np.inf,dtype=float)
    queue = []
    for vertex in patch:
        vertex=int(vertex)
        distance[vertex]=0.0
        heapq.heappush(queue,(0.,vertex))
    while queue:
        d,i=heapq.heappop(queue)
        if d>distance[i]:
            continue
        for j,w in adj[i]:
            nd=d+w
            if nd<distance[j]:
                distance[j]=nd
                heapq.heappush(queue,(nd,j))
    return distance*1000.0


def audit(capture_dir, response_path, patch_json):
    capture_dir=Path(capture_dir)
    spec=json.loads(Path(patch_json).read_text())
    with np.load(response_path) as source, \
         np.load(capture_dir/"r52"/"rest_weights.npz") as mesh, \
         np.load(capture_dir/"r52"/"clip.npz") as r52, \
         np.load(capture_dir/"r41"/"clip.npz") as r41:
        rest=mesh["rest"]
        back_ids=np.asarray(mesh["back_ids"],dtype=int)
        shoulder_ids=np.asarray(mesh["shoulder_ids"],dtype=int)
        if (rest.ndim != 2 or rest.shape[1] != 3 or
                len(back_ids)==0 or len(shoulder_ids)==0 or
                not np.array_equal(np.unique(back_ids),back_ids) or
                not np.array_equal(np.unique(shoulder_ids),shoulder_ids) or
                back_ids.max()>=len(rest)):
            raise ValueError("Noncanonical rest/back identities")
        if not np.array_equal(r52["bone_matrices"],r41["bone_matrices"]):
            raise ValueError("Bone motion mismatch between original captures")
        base=r41["back_points"]
        current=r52["back_points"]
        per=dense_per_vertex_excess_mm(base,current)
        worst=float(per.max())
        if abs(worst-40.644618)>.05:
            raise ValueError("Original dense baseline does not reproduce R52")
        allowed=np.asarray(source["r47_allowed"]).any(axis=0)
        frozen=np.asarray(source["frozen_arm"]).any(axis=0)
        if allowed.shape!=(len(rest),) or frozen.shape!=(len(rest),):
            raise ValueError("Incorrect original source material dimensions")
        editable=allowed & ~frozen
        patch=allowed_weight_scope(spec,allowed,frozen,len(rest))
        distances=geodesic_to_patch_mm(rest,mesh["edges"],patch)
        # Use the existing R53 ablations to check whether S7 accounts for the
        # added R52 motion at all sampled back vertices. No model is altered.
        subset_idx=np.searchsorted(shoulder_ids,back_ids)
        if (subset_idx.max() >= len(shoulder_ids) or
                not np.array_equal(shoulder_ids[subset_idx],back_ids)):
            raise ValueError("Missing shoulder/back vertex identity")
        muted=(
            np.asarray(r52["baseline"][:,subset_idx],float) +
            np.asarray(r52["no_S7"][:,subset_idx],float))
        mute_replay_max_mm=float(np.linalg.norm(muted-np.asarray(base,float),axis=2).max()*1000)
        if mute_replay_max_mm>.01:
            raise ValueError("S7-only attribution failed actual captured replay")
        ranks=np.argsort(-per,kind="stable")
        hotspot=[]
        for index in ranks[:40]:
            index=int(index);v=int(back_ids[index]);d=float(distances[v])
            hotspot.append(dict(vertex=v,
                max_dense_motion_excess_mm=float(per[index]),
                rest_position_m=rest[v].tolist(),
                in_26_vertex_weight_trial=bool(np.isin(v,patch)),
                within_R47_allowed_skin_union=bool(allowed[v]),
                original_source_frozen_arm=bool(frozen[v]),
                eligible_R47_union_after_frozen_guard=bool(editable[v]),
                mesh_edge_distance_to_26_patch_mm=d if np.isfinite(d) else None))
        exceed=per>.5
        exceed_ids=back_ids[exceed]
        counts=dict(
            total_back_vertices=len(back_ids),
            vertices_exceeding_unchanged_0_5mm_motion_guard=int(exceed.sum()),
            exceedance_vertices_in_26_weight_patch=int(np.isin(exceed_ids,patch).sum()),
            exceedance_vertices_outside_26_weight_patch=int((~np.isin(exceed_ids,patch)).sum()),
            exceedance_vertices_inside_R47_allowed_union=int(allowed[exceed_ids].sum()),
            exceedance_vertices_inside_R47_editable_not_frozen=int(editable[exceed_ids].sum()),
            exceedance_vertices_frozen_by_original_source=int(frozen[exceed_ids].sum()))
        anchors={}
        for v in (19057,20913,18081,21057,18057,21044):
            if v<0 or v>=len(rest):
                raise ValueError("Known vertex id missing")
            j=np.where(back_ids==v)[0]
            anchors[str(v)]=dict(
                in_back_motion_region=bool(len(j)),
                excess_mm=float(per[j[0]]) if len(j) else None,
                within_26_weight_trial=bool(np.isin(v,patch)),
                R47_allowed_union=bool(allowed[v]),
                frozen_by_original_source=bool(frozen[v]),
                rest_mesh_distance_to_26_patch_mm=float(distances[v])
                if np.isfinite(distances[v]) else None)
        return dict(status="READ_ONLY_R55_SCOPE_AUDIT_NOT_A_REPAIR",
            model_saved=False,owner_approved_model=False,
            source_frames=161,
            original_unchanged_motion_guard_mm=0.5,
            reproduced_R52_dense_motion_excess_mm=worst,
            actual_S7_mute_R41_replay_max_mm=mute_replay_max_mm,
            authorized_weight_trial_vertex_count=len(patch),
            counts=counts,anchors=anchors,top_40_motion_hotspots=hotspot,
            limitations=[
                "0.5 mm threshold is the unchanged global maximum motion guard; per-vertex exceedance is descriptive only.",
                "Original permitted R47 union is not automatically authority to edit every underlying weight.",
                "Only 26 vertices were authorised for the previous reversible weight test, now rejected.",
                "Geodesic distances use rest mesh edges, not projected screen distance.",
                "Fixed-coordinates/fixed-matrices local weight changes cannot directly move vertices outside that patch; recomputed correctives are a different experiment.",
                "R52/S7 attribution is specific to the already captured press, not a universal anatomical diagnosis.",
                "No triangle collision, crease, area, outline, 13 benchmark or full native acceptance on any changed mesh occurs here.",
                "Do not expand material, change helper transforms or replace anatomy without owner permission."])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--capture",required=True)
    p.add_argument("--source",required=True)
    p.add_argument("--patch",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    result=audit(args.capture,args.source,args.patch)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in
                      ("status","reproduced_R52_dense_motion_excess_mm",
                       "actual_S7_mute_R41_replay_max_mm",
                       "counts","anchors")},indent=2))

if __name__=="__main__":
    main()
