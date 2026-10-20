"""R57 reversible, unsaved S7-only shoulder temporal smoothing experiment.

This deliberately tests ONE bounded local hypothesis (not an anatomy fix).
Existing R52 dense S7 material coordinates/permissions remain the only edit area.
No skeleton, Basis, weights, geometry topology, non-S7 keys or BLEND saved.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from original_review_r52_projection import allowed_dense
from original_review_r52_temporal import SOURCE, oscillation
from audit_original_review_r55_hotspot_scope import geodesic_to_patch_mm

CENTER_VERTICES = (19057, 20913)
TEMPORAL_CENTRE_DEG = 118
TEMPORAL_RADIUS_DEG = 5
MATERIAL_RADIUS_MM = 55.0
STRENGTH = 0.65


def mirror_centres(rest,centres=CENTER_VERTICES,max_error_mm=5.0):
    a=np.asarray(rest,float)
    if a.ndim!=2 or a.shape[1]!=3 or not np.isfinite(a).all():
        raise ValueError("Invalid original rest coordinates")
    ids=[]
    for v in centres:
        if v<0 or v>=len(a):
            raise ValueError("Source anchor outside original mesh")
        mirror=np.array([-a[v,0],a[v,1],a[v,2]])
        distances=np.linalg.norm(a-mirror,axis=1)
        other=int(distances.argmin())
        if float(distances[other]*1000)>max_error_mm:
            raise ValueError("Could not verify original bilateral counterpart")
        ids.extend((int(v),other))
    return np.asarray(sorted(set(ids)),dtype=int)


def bounded_smoothing(old, mask, rest, edges, centres,
                      spatial_radius_mm=MATERIAL_RADIUS_MM,strength=STRENGTH):
    old=np.asarray(old,float)
    mask=np.asarray(mask,bool)
    if (old.ndim!=3 or old.shape[0]!=72 or old.shape[2]!=3 or
            mask.shape!=old.shape[:2] or
            not np.isfinite(old).all() or
            np.any(old[~mask]!=0) or
            np.linalg.norm(old,axis=2).max()>.045+1e-10 or
            not 0<strength<=1 or spatial_radius_mm<=0):
        raise ValueError("Unsafe original dense input or smoothing settings")
    distance=geodesic_to_patch_mm(rest,edges,np.asarray(centres,dtype=int))
    f=np.clip(1.-distance/spatial_radius_mm,0.,1.)
    spatial=f*f*(3.-2.*f)
    # Use a read-only snapshot: never propagate a previous edited value
    # into the next temporal step.
    out=old.copy()
    changed_controls=[]
    for angle in range(114,123):
        index=angle-95
        t=max(0.,1.-abs(angle-TEMPORAL_CENTRE_DEG)/TEMPORAL_RADIUS_DEG)
        alpha=(strength*t*spatial*mask[index])[:,None]
        filtered=(old[index-2]+4*old[index-1]+6*old[index]+
                  4*old[index+1]+old[index+2])/16.
        out[index]=old[index]+alpha*(filtered-old[index])
        changed_controls.append(angle)
    if (np.any(out[~mask]!=0) or
            np.linalg.norm(out,axis=2).max()>.045+1e-10 or
            np.any(out[[0,15,71]]!=0)):
        raise ValueError("Candidate exceeds unchanged original scope or material cap")
    if not np.array_equal(out[:114-95],old[:114-95]):
        raise ValueError("Lower source/key range unexpectedly edited")
    if not np.array_equal(out[123-95:],old[123-95:]):
        raise ValueError("Marked outline/late motion controls unexpectedly edited")
    changed=np.any(out!=old,axis=2)
    if not changed.any():
        raise ValueError("No actual correction hypothesis produced")
    return out,dict(
        changed_vertices=int(changed.any(0).sum()),
        changed_node_vertex_pairs=int(changed.sum()),
        modified_dense_angles=changed_controls,
        nearest_original_mesh_distance_mm=float(np.nanmin(distance)),
        original_material_peak_mm=float(np.linalg.norm(old,axis=2).max()*1000),
        candidate_material_peak_mm=float(np.linalg.norm(out,axis=2).max()*1000),
        original_max_adjacent_control_mm=oscillation(old)["maximum_adjacent_mm"],
        candidate_max_adjacent_control_mm=oscillation(out)["maximum_adjacent_mm"],
        model_saved=False,shape_approved=False)


def make(source_path,solution_path,certificate_path,output):
    certificate=json.loads(Path(certificate_path).read_text())
    if certificate["status"]!="READ_ONLY_R56_PER_CONTROL_SCOPE_CERTIFICATE_NOT_REPAIRED":
        raise ValueError("R56 source/key certificate missing")
    selected={int(v["vertex"]):v for v in certificate["per_vertex"]}
    for anchor in CENTER_VERTICES:
        a=selected[anchor]["active_midpress_118_and_119"]
        if not a["angle_118_allowed"] or not a["angle_119_allowed"]:
            raise ValueError("R56 does not permit movement at the measured hotspot")
    with np.load(source_path) as src,np.load(solution_path) as sol:
        rest=src["rest"];faces=src["faces"];old=sol["dense_delta"]
        mask=allowed_dense(src)
        if mask.shape!=old.shape[:2]:
            raise ValueError("Source mask/solution identity changed")
        mirror=mirror_centres(rest)
        edges=np.unique(np.sort(np.concatenate((
            faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1),axis=0)
        candidate,metrics=bounded_smoothing(old,mask,rest,edges,mirror)
        for v in mirror:
            if not (mask[118-95,v] and mask[119-95,v]):
                raise ValueError("Mirrored hotspot lacks original S7 authority")
        # Historical source knot/source135.625 pose footprint remains unchanged
        # for every control at and after123 degrees. This does NOT make the
        # complete original R47 outline test redundant.
        if np.any(candidate[~mask]!=0):
            raise ValueError("Scope error")
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(path,dense_delta=candidate,delta=candidate[SOURCE])
        metrics.update(status="R57_IN_MEMORY_STUDY_NOT_ACCEPTED",
            mirror_seed_vertices=mirror.tolist(),
            anchors=CENTER_VERTICES,
            source_masks_unchanged=True,
            material_scope_expanded=False,
            owner_approved=False,
            model_saved=False,
            notes=[
                "Temporal and spatial filters are diagnostic hypotheses, not anatomical prescriptions.",
                "Only integer-degree S7 increments 114..122 are affected inside existing original masks.",
                "Historical original R47 marked pose unaffected by original dense 123..166 control identity, but still must be tested natively.",
                "No 83-pose contacts/normals, 161-pose geometry, 13 benchmarks or visual review are implied by this preflight.",
                "A passing generator is not a saved or production-ready Blender model."])
        Path(str(path)+".json").write_text(json.dumps(metrics,indent=2)+chr(10))
        print(json.dumps(metrics,indent=2))
        return metrics


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--response",required=True)
    p.add_argument("--solution",required=True)
    p.add_argument("--r56",required=True)
    p.add_argument("--out",required=True)
    q=p.parse_args()
    make(q.response,q.solution,q.r56,q.out)
