#!/usr/bin/env python3
"""Source-verified 3D CT intensity bridge witness, NOT articular-bone segmentation.

This computes the shortest physically weighted six-neighbour path through one
thresholded CT ROI between two PRE-EXISTING candidate pixels.  It documents
why raw HU connectivity cannot prove separation of hip joint bones. Scanner
pixel FOV origin remains unresolved; only *relative* physical distances are
used (unaffected by a common half-pixel offset). No image/mesh is published.
"""
import argparse
import heapq
import json
import math
from pathlib import Path

from ct_pelvis_window_geometry import assert_private_location
from nlm_ct_provisional_surface import GRID, MAX_ROI_SAMPLES, _private_source_slice
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

NEIGHBOURS = ((-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1))
MAX_VOXELS = 350_000


def source_spacing_mm(geometry, slice_mm=3.0):
    tl, tr, br = (geometry[k] for k in (
        "plane_TL_RAS_mm", "plane_TR_RAS_mm", "plane_BR_RAS_mm"))
    col = math.dist(tl, tr) / GRID
    row = math.dist(tr, br) / GRID
    if not (2.9 <= slice_mm <= 3.1 and .1 <= col <= 3 and .1 <= row <= 3):
        raise ValueError("unreasonable or source-unverified voxel spacing")
    return [slice_mm, row, col]


def weighted_shortest_intensity_bridge(voxels, point_a, point_b, roi, n_slices,
                                       voxel_spacings_mm, *, max_settled=MAX_VOXELS,
                                       scalar_layers=None):
    """Return an intensity-only path witness; do not interpret as real joint contact.

    Integer micrometre costs give deterministic shortest physical routes even
    when images are very anisotropic (3-mm slice pitch, ~.9-mm in plane).
    """
    a, b = tuple(point_a), tuple(point_b)
    if (len(a) != 3 or len(b) != 3 or
            any(type(v) is not int for v in a+b) or
            not isinstance(voxels, set)):
        raise ValueError("source candidate voxel indices must be integer triplets")
    col0,col1,row0,row1=roi
    if not (0 <= col0 < col1 <= GRID and 0 <= row0 < row1 <= GRID and
            type(n_slices) is int and 2 <= n_slices <= 72):
        raise ValueError("invalid voxel selection")
    if not isinstance(voxel_spacings_mm, (list,tuple)) or len(voxel_spacings_mm)!=3:
        raise ValueError("voxel spacings are required")
    steps=[]
    for v in voxel_spacings_mm:
        if type(v) not in (int,float) or not math.isfinite(v) or not .1 <= v <= 5:
            raise ValueError("invalid physical voxel spacing")
        steps.append(round(v*1_000_000))
    if (len(voxels) > MAX_VOXELS or type(max_settled) is not int
            or max_settled <= 0 or max_settled > MAX_VOXELS):
        raise ValueError("HU mask exceeds audited budget")
    for z,r,c in (a,b):
        if not (0 <= z < n_slices and row0 <= r < row1 and col0 <= c < col1):
            raise ValueError("review point outside selected source group or ROI")
    if scalar_layers is not None and (
            len(scalar_layers) != n_slices or
            any(len(layer) != GRID*GRID for layer in scalar_layers)):
        raise ValueError("bad decoded scanner image evidence")

    result = {
        "start_seed_occupied": a in voxels,
        "end_seed_occupied": b in voxels,
        "source_geometry_spacings_mm_z_row_col": voxel_spacings_mm,
        "same_HU_component": None,
        "path_exists_and_is_hu_only": False,
        "anatomical_joint_contact_or_separation_proven": False,
        "independent_bone_identity_verified": False,
        "pixel_centre_origin_convention_verified": False,
        "canonical_promotion_allowed": False,
    }
    if a not in voxels or b not in voxels:
        result["no_path_reason"] = "one_or_both_source_seed_pixels_below_HU_threshold"
        return result

    distances={a:0}
    parents={a:None}
    queue=[(0,a)]
    settled=0
    while queue:
        value, point = heapq.heappop(queue)
        if value != distances.get(point):
            continue
        settled+=1
        if settled > max_settled:
            raise ValueError("physical bridge search exceeded reviewed node budget")
        if point == b:
            break
        z,r,c=point
        for delta,mm in zip(NEIGHBOURS,(steps[0],steps[0],steps[1],
                                       steps[1],steps[2],steps[2])):
            nxt=(z+delta[0],r+delta[1],c+delta[2])
            if nxt not in voxels:
                continue
            nd=value+mm
            if nd < distances.get(nxt, 2**62):
                distances[nxt]=nd
                parents[nxt]=point
                heapq.heappush(queue,(nd,nxt))
    if b not in parents:
        result["same_HU_component"]=False
        result["no_path_reason"]="disconnected_in_supplied_6_neighbour_HU_mask"
        result["search_settled_voxels"]=settled
        return result

    path=[]
    point=b
    while point is not None:
        path.append(point)
        point=parents[point]
    path.reverse()
    extent={
        "slice_min_max": [min(p[0] for p in path),max(p[0] for p in path)],
        "row_min_max": [min(p[1] for p in path),max(p[1] for p in path)],
        "column_min_max": [min(p[2] for p in path),max(p[2] for p in path)],
    }
    contacts=set()
    for z,r,c in path:
        if z==0:contacts.add("source_group_first_plane")
        if z==n_slices-1:contacts.add("source_group_last_plane")
        if r==row0:contacts.add("ROI_row_min")
        if r==row1-1:contacts.add("ROI_row_max")
        if c==col0:contacts.add("ROI_col_min")
        if c==col1-1:contacts.add("ROI_col_max")
    direct=math.sqrt(sum(
        ((a[i]-b[i])*voxel_spacings_mm[i])**2 for i in range(3)))
    length=value / 1_000_000
    result.update({
        "same_HU_component":True,
        "path_exists_and_is_hu_only": True,
        "least_physical_length_mm_in_thresholded_ROI":round(length,3),
        "seed_direct_euclidean_distance_mm":round(direct,3),
        "route_length_over_direct_distance":round(length/direct,4) if direct else 1.0,
        "path_voxel_samples":len(path),
        "path_slice_planes_visited":len({p[0] for p in path}),
        "path_scanner_plane_index_extent":extent,
        "path_touches_source_or_ROI_cut":bool(contacts),
        "path_selection_cut_contacts":sorted(contacts),
        "path_minimum_source_HU":min(
            scalar_layers[z][r*GRID+c]-1024 for z,r,c in path
        ) if scalar_layers is not None else None,
        "search_settled_voxels":settled,
        "path_is_arbitrary_HU_route_not_contiguous_articular_bone":True,
    })
    return result


def select_source_pins(bundle, review, group, start, count, names):
    if group not in (1,2) or type(start) is not int or type(count) is not int:
        raise ValueError("a single original acquisition group is required")
    rows=bundle["series"][group-1]["slices"]
    if start < 0 or count < 2 or start+count > len(rows):
        raise ValueError("selected slice interval outside original acquisition group")
    chosen=rows[start:start+count]
    indexed={row["source_id"]:(i,row) for i,row in enumerate(chosen)}
    if not isinstance(names,(list,tuple)) or len(names)!=2 or names[0]==names[1]:
        raise ValueError("two distinct explicit original observation IDs required")
    observations=[]
    for name in names:
        found=[p for p in review["observations"] if p["observation_id"]==name]
        if len(found)!=1:
            raise ValueError("source-linked named observation must be unique")
        point=found[0]
        if point["source_id"] not in indexed:
            raise ValueError("observation lies outside the selected source acquisition interval")
        z,source=indexed[point["source_id"]]
        if (point["source_png_sha256"]!=source["source_png_sha256"] or
                point["source_header_sha256"]!=source["source_header_sha256"] or
                abs(point["scanner_S_mm"]-source["scanner_centre_RAS_mm"][2])>1e-5):
            raise ValueError("original source landmark hypothesis hash/position mismatch")
        r,c=point["pixel"]["row"],point["pixel"]["column"]
        if type(r) is not int or type(c) is not int or not 0<=r<GRID or not 0<=c<GRID:
            raise ValueError("invalid original observation pixel")
        observations.append({
            "id":name, "source_id":point["source_id"],
            "voxel_z_row_col":[z,r,c],
            "anatomical_label_verified":False,
        })
    return chosen,observations


def analyze(bundle,cal,review,group,start,count,roi,hues,ct_dir,names,
            *,source_loader=None):
    validate_series_bundle(bundle)
    validate_calibration_evidence(cal,bundle)
    if review.get("kind")!="NLM_CT_ANATOMICAL_REVIEW_PACKET":
        raise ValueError("cannot use an unrecognized anatomical hypothesis packet")
    if (not isinstance(hues,(list,tuple)) or not 1<=len(hues)<=4
            or any(type(h) is not int or h < -1024 or h > 3000 for h in hues)
            or list(hues)!=sorted(set(hues))):
        raise ValueError("one through four sorted unique HU thresholds required")
    col0,col1,row0,row1=roi
    if not (0<=col0<col1<=GRID and 0<=row0<row1<=GRID):
        raise ValueError("invalid HU ROI")
    chosen,observations=select_source_pins(bundle,review,group,start,count,names)
    if count*(col1-col0)*(row1-row0)>MAX_ROI_SAMPLES:
        raise ValueError("ROI exceeds audited memory budget")
    source=assert_private_location(ct_dir)
    if source_loader is None:source_loader=_private_source_slice
    layers=[]
    first=None
    for z,row in enumerate(chosen):
        if abs(row["scanner_centre_RAS_mm"][2]-
               (chosen[0]["scanner_centre_RAS_mm"][2]-3*z))>1e-5:
            raise ValueError("source axial acquisition pitch changed")
        geom,pixels=source_loader(source,row)
        if len(pixels)!=GRID*GRID or abs(geom["scanner_S_mm"]-row["scanner_centre_RAS_mm"][2])>1e-5:
            raise ValueError("source hash-verified CT pixels/header disagree")
        if first is None:
            first=geom
        else:
            for k in ("plane_TL_RAS_mm","plane_TR_RAS_mm","plane_BR_RAS_mm"):
                if any(abs(first[k][i]-geom[k][i])>.01 for i in range(3)
                       if i!=2):
                    raise ValueError("inconsistent original scanner XY geometry")
        layers.append(pixels)
    spacings=source_spacing_mm(first)
    candidates={}
    for hu in hues:
        volume=set()
        limit=hu+1024
        for z,pixels in enumerate(layers):
            for r in range(row0,row1):
                offset=r*GRID
                for c in range(col0,col1):
                    if pixels[offset+c]>=limit:
                        volume.add((z,r,c))
                        if len(volume)>MAX_VOXELS:
                            raise ValueError("original HU source mask exceeds audited voxel budget")
        a,b=[p["voxel_z_row_col"] for p in observations]
        candidates[str(hu)]={
            "HU":hu,
            "source_thresholded_voxels":len(volume),
            "physical_HU_bridge_witness_not_anatomical_contact":
                weighted_shortest_intensity_bridge(
                    volume,a,b,roi,count,spacings,scalar_layers=layers),
        }
    return {
        "schema_version":1,
        "kind":"PINNED_ORIGINAL_CT_HU_BRIDGE_WITNESS_NOT_BONE_SEGMENTATION",
        "original_source_group":group,
        "original_source_slice_count":count,
        "source_ids":[row["source_id"] for row in chosen],
        "source_png_sha256":[row["source_png_sha256"] for row in chosen],
        "original_candidate_points":observations,
        "HU_thresholds":candidates,
        "scanner_frame":"ORIGINAL_SCANNER_RAS_MM",
        "pixel_origin_convention_verified":False,
        "distinct_bone_surface_identity_verified":False,
        "hip_joint_articular_gap_verified":False,
        "pelvic_landmarks_accepted":0,
        "anatomical_reviewer_approval":False,
        "source_image_or_header_exported":False,
        "canonical_promotion_allowed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ct-dir",required=True)
    p.add_argument("--bundle",required=True)
    p.add_argument("--calibration",required=True)
    p.add_argument("--review",required=True)
    p.add_argument("--group",type=int,required=True)
    p.add_argument("--start",type=int,required=True)
    p.add_argument("--count",type=int,required=True)
    p.add_argument("--roi",type=int,nargs=4,required=True)
    p.add_argument("--hu",type=int,nargs="+",required=True)
    p.add_argument("--seed-observation",action="append",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    out=assert_private_location(a.out)
    if out.exists():
        raise ValueError("refuse to overwrite original private CT review")
    bundle=json.loads(Path(a.bundle).read_text())
    cal=json.loads(Path(a.calibration).read_text())
    review=json.loads(Path(a.review).read_text())
    report=analyze(bundle,cal,review,a.group,a.start,a.count,a.roi,a.hu,
                   a.ct_dir,a.seed_observation)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x") as f:
        json.dump(report,f,sort_keys=True,indent=2)
        f.write("\n")
    print(json.dumps({
        "kind":report["kind"],
        "review_seed_ids":a.seed_observation,
        "outcomes":[
            {"HU":v["HU"],
             "bridge":v["physical_HU_bridge_witness_not_anatomical_contact"]}
            for v in report["HU_thresholds"].values()],
        "canonical_promotion_allowed":False,
    },indent=2))


if __name__=="__main__":
    main()
