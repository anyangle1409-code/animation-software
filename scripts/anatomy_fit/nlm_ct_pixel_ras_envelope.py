#!/usr/bin/env python3
"""First-party bounded pixel cell -> ORIGINAL GE scanner RAS placement.

The four corners are scanner geometry, but original documentation does not
yet independently settle whether "Top Left Hand Corner" refers to image
outer boundary or first pixel centre. Return a CELL/SLAB bound and an
explicit candidate centre under one named edge-origin assumption, never
a canonically accepted anatomical feature.

This does NOT calculate HU, identify bone, infer a 3D slice normal
beyond validated axial GE geometry, or map scanner RAS into Home Gym PT.
"""
import argparse
import json
import math
from pathlib import Path

def _pt(p):
    if (not isinstance(p,list) or len(p)!=3 or
            any(type(x) not in (int,float) or not math.isfinite(x) for x in p)):
        raise ValueError("invalid scanner position triple")
    return p

def place_pixel(scanner, row, col):
    width,height=scanner["image_dimensions"]
    if (width,height)!=(512,512):
        raise ValueError("unknown original scanner image grid")
    if (type(row)!=int or type(col)!=int or not 0<=row<height or not 0<=col<width):
        raise ValueError("pixel indices must be integer 0..511")
    tl=_pt(scanner["plane_TL_RAS_mm"])
    tr=_pt(scanner["plane_TR_RAS_mm"])
    br=_pt(scanner["plane_BR_RAS_mm"])
    dx=[(tr[i]-tl[i])/width for i in range(3)]
    dy=[(br[i]-tr[i])/height for i in range(3)]
    step_x=math.sqrt(sum(v*v for v in dx))
    step_y=math.sqrt(sum(v*v for v in dy))
    if not all(abs(v-w)<.0001 for v,w in zip((step_x,step_y),scanner["pixel_spacing_mm"])):
        raise ValueError("scanner pixel geometry disagrees with source spacing")
    thickness=scanner["slice_thickness_mm"]
    if not 0<thickness<10:
        raise ValueError("invalid CT slice thickness")
    def point(u,v):
        return [tl[i]+u*dx[i]+v*dy[i] for i in range(3)]
    # Bounds in scanner space if TL/TR/BR describe FOV edges.
    four=[point(col+x,row+y) for x,y in ((0,0),(1,0),(0,1),(1,1))]
    mid=point(col+.5,row+.5)
    return {
        "schema_version":1,
        "kind":"ORIGINAL_CT_PIXEL_TO_SCANNER_RAS_BOUNDED_OBSERVATION",
        "pixel_col_row":[col,row],
        "candidate_pixel_centre_RAS_mm_if_outer_FOV_corners":mid,
        "candidate_cell_four_corners_RAS_mm_if_outer_FOV_corners":four,
        "source_pixel_in_plane_step_mm":[step_x,step_y],
        "in_plane_half_pixel_size_mm":[step_x/2,step_y/2],
        "source_slice_centre_RAS_S_mm":mid[2],
        "source_slab_S_range_mm":[mid[2]-thickness/2,mid[2]+thickness/2],
        "voxel_index_to_physical_sample_centre_convention_verified":False,
        "original_CT_pixel_HU_verified":False,
        "anatomical_region_identified":False,
        "bone_surface_segmentation_verified":False,
        "HomeGymPT_world_transform_applied":False,
        "canonical_promotion_allowed":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scanner-geometry-report",type=Path,required=True)
    p.add_argument("--row",type=int,required=True)
    p.add_argument("--col",type=int,required=True)
    a=p.parse_args()
    s=json.loads(a.scanner_geometry_report.read_text())
    print(json.dumps(place_pixel(s,a.row,a.col),indent=2))

if __name__=="__main__":
    main()
