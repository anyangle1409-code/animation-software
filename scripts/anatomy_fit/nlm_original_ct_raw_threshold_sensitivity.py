#!/usr/bin/env python3
"""Evidence-safe NLM 72 CT volume threshold sensitivity diagnostic.

Real first-party source byte ingestion and actual 3D 6-neighbour diagnostics.
Do NOT mistake stored 16-bit PNG scalars for Hounsfield units, classify
structures as cortical bone or export source patient images.

The existing Blender 13,273-block occupancy was uncalibrated. Here we audit
an INDEPENDENT, explicitly specified family of tile operators:
  any (at least one pixel over threshold in 8x8 source-pixel tile)
  eight (at least EIGHT of 64 pixels over threshold)
We do not attempt to match Blender's undocumented block occupancy operator.
For each separate scanner group and each raw stored-scalar threshold, report
occupancy, 3D connectivity, and Jaccard overlap versus threshold 1200.
Never stitch separate source groups or export 3D mesh/image pixels.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path

import nlm_original_ct_png_probe as png
import nlm_pelvis_region_scout as scout
import pelvic_ct_series_manifest as series

TILE_WIDTH = 8
TILES = 64
TILE_COUNT = TILES*TILES
EXPECTED_SLICES = 72
THRESHOLDS = (900,1050,1200,1350,1500,1800)
OPERATORS = ('any', 'eight')
BASELINE = 1200


def compute_tile_order_stats(pixels):
    """For each 8x8 tile compute largest and eighth-largest raw scalar."""
    if len(pixels) != 512*512:
        raise ValueError('only original 512x512 CT image decoded arrays supported')
    if any(type(v) is not int or v<0 or v>65535 for v in pixels):
        raise ValueError('nonfinite/negative/out of range source pixel')
    maxes=[]
    eighth=[]
    for y in range(TILES):
        for x in range(TILES):
            off_y = y*TILE_WIDTH
            off_x = x*TILE_WIDTH
            values=[]
            for r in range(TILE_WIDTH):
                start = (off_y+r)*512+off_x
                values.extend(pixels[start:start+TILE_WIDTH])
            values.sort()
            maxes.append(values[-1])
            eighth.append(values[-8])
    if len(maxes)!=TILE_COUNT or len(eighth)!=TILE_COUNT:
        raise AssertionError('tile count changed')
    return {'any':maxes,'eight':eighth}


def one_slice(row):
    name=row['source_id']
    if not isinstance(name,str) or not name.startswith('cvm') or not name.endswith('f'):
        raise ValueError('original NLM source identifier invalid')
    raw=scout._safe_download(scout.INDEX_BASE+name+'.png',png.MAX_BYTES)
    source=png.inspect_png(raw)
    if (source['source_sha256']!=row['source_png_sha256'] or
            source['bytes']!=row['source_png_bytes']):
        raise ValueError('original CT image bytes differ from independently pinned source')
    values=scout.decode_grayscale_png16(raw)
    stats=compute_tile_order_stats(values)
    return name,stats


def _mask(values,threshold):
    return bytearray(v>=threshold for v in values)


def _component_sizes(masks):
    """6-neighbour components WITHOUT linking across source-group boundaries."""
    if not isinstance(masks,list) or any(len(mask)!=TILE_COUNT for mask in masks):
        raise ValueError('invalid 64x64 source tile group')
    if not masks:
        raise ValueError('group must contain source slices')
    all_bits = bytearray().join(masks)
    voxels = len(all_bits)
    seen = bytearray(voxels)
    component_sizes=[]
    plane=TILE_COUNT
    for root in range(voxels):
        if not all_bits[root] or seen[root]:
            continue
        seen[root]=1
        stack=[root]
        count=0
        while stack:
            current=stack.pop()
            count+=1
            z, remainder = divmod(current,plane)
            y,x=divmod(remainder,TILES)
            neighbors=[]
            if x:neighbors.append(current-1)
            if x<TILES-1:neighbors.append(current+1)
            if y:neighbors.append(current-TILES)
            if y<TILES-1:neighbors.append(current+TILES)
            if z:neighbors.append(current-plane)
            if z<len(masks)-1:neighbors.append(current+plane)
            for nxt in neighbors:
                if all_bits[nxt] and not seen[nxt]:
                    seen[nxt]=1
                    stack.append(nxt)
        component_sizes.append(count)
    component_sizes.sort(reverse=True)
    return component_sizes


def _jaccard(masks_a,masks_b):
    if len(masks_a)!=len(masks_b) or any(len(a)!=len(b) for a,b in zip(masks_a,masks_b)):
        raise ValueError('cannot compare different scanner grids')
    intersection=union=0
    for a,b in zip(masks_a,masks_b):
        for p,q in zip(a,b):
            intersection+=bool(p and q)
            union+=bool(p or q)
    return 1.0 if union==0 else intersection/union


def evaluate_group(stats, operator, thresholds=THRESHOLDS):
    if operator not in OPERATORS or len(stats)<2:
        raise ValueError('invalid source tile operator or group size')
    if any(not isinstance(row,dict) or operator not in row or
           len(row[operator])!=TILE_COUNT for row in stats):
        raise ValueError('missing source tile-statistic frame')
    if thresholds!=THRESHOLDS:
        raise ValueError('review fixed stored scalar thresholds, do not silently change calibration')
    masks={t:[_mask(row[operator],t) for row in stats] for t in thresholds}
    baseline=masks[BASELINE]
    results=[]
    for t in thresholds:
        mm=masks[t]
        count=sum(sum(mask) for mask in mm)
        sizes=_component_sizes(mm)
        results.append({
            'raw_stored_PNG_scalar_cutoff':t,
            'source_tile_operator':operator,
            'active_8x8x_slice_blocks':count,
            'component_count_6_neighbor':len(sizes),
            'component_top_ten_block_counts':sizes[:10],
            'largest_component_block_fraction':round(sizes[0]/count,6) if count else 0,
            'jaccard_to_same_operator_raw_1200':round(_jaccard(mm,baseline),6),
            'not_a_bone_mask_or_HU_threshold':True,
        })
    count_by_threshold=[r['active_8x8x_slice_blocks'] for r in results]
    if any(count_by_threshold[i] < count_by_threshold[i+1]
           for i in range(len(count_by_threshold)-1)):
        raise AssertionError('raw threshold occupancy not monotone')
    return {
        'operator':operator,
        'block_rule':'one_or_more_of_64_raw_scalars' if operator=='any' else
                     'eight_or_more_of_64_raw_scalars',
        'source_slices':len(stats),
        'baseline_threshold_raw_stored_scalar':BASELINE,
        'occupancy_monotone_nonincreasing_with_threshold':True,
        'results':results,
        'bone_threshold_supported_by_anatomy':False,
    }


def analyze(bundle,download_one=one_slice):
    meta=series.validate_series_bundle(bundle)
    if meta['slice_count']!=EXPECTED_SLICES or len(bundle['series'])!=2:
        raise ValueError('expected preserved two-source-group 72-image CT volume')
    all_rows=[row for group in bundle['series'] for row in group['slices']]
    # Fetch source images only into temporary process memory; no patient images
    # or PNG bytes are returned by the workers or saved to the repository.
    with ThreadPoolExecutor(max_workers=4) as pool:
        fetched=list(pool.map(download_one,all_rows))
    lookup=dict(fetched)
    if len(lookup)!=EXPECTED_SLICES:
        raise ValueError('duplicate or missing CT scout image')
    report=[]
    for group_i,group in enumerate(bundle['series'],1):
        stats=[]
        for row in group['slices']:
            source=lookup.get(row['source_id'])
            if not isinstance(source,dict):
                raise ValueError('missing tile summary for source frame')
            stats.append(source)
        report.append({
            'source_group_index':group_i,
            'scanner_superior_range_mm':[group['slices'][0]['scanner_centre_RAS_mm'][2],
                                         group['slices'][-1]['scanner_centre_RAS_mm'][2]],
            'individual_group_original_pinned_source_count':len(stats),
            'operators':[evaluate_group(stats,operator) for operator in OPERATORS],
            'no_3d_components_connected_to_other_scanner_group':True,
        })
    return {
        'schema_version':1,
        'kind':'CT_ORIGINAL_STORED_SCALAR_THRESHOLD_SENSITIVITY',
        'status':'UNCALIBRATED_GEOMETRY_DIAGNOSTIC_NOT_BONE_SEGMENTATION',
        'original_NLM_PNG_sha256_verified_for_each_image':True,
        'source_slices_verified':len(fetched),
        'source_groups_evaluated_separately':len(report),
        'native_block_xy_source_pixels':[8,8],
        'thresholds_are_original_PNG_stored_scalars_not_HU':True,
        'thresholds_tested_original_stored_scalar':list(THRESHOLDS),
        'comparison_is_not_original_Blender_occupancy_implementation':True,
        'scanner_S_and_in_plane_source_geometry_comes_from_pinned_bundle':True,
        'current_source_coverage_approved_for_all_pelvic_features':False,
        'provisional_image_intensity_to_HU_conversion_verified':False,
        'cortical_or_cancellous_bone_label_independently_verified':False,
        'individual_bones_separated_from_artifacts_or_nonbone':False,
        '3d_bone_surface_extracted':False,
        'source_skeleton_or_production_mesh_modified':False,
        'canonical_promotion_allowed':False,
        'group_reports':report,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-bundle',type=Path,required=True)
    p.add_argument('--live-source-threshold-probe',action='store_true')
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    if not args.live_source_threshold_probe:
        p.error('real source acquisition must be explicit')
    bundle=json.loads(args.source_bundle.read_text(encoding='utf-8'))
    result=analyze(bundle)
    output=json.dumps(result,indent=2)+'\n'
    if args.out:
        with args.out.open('x',encoding='utf-8') as f:
            f.write(output)
    else:
        print(output,end='')


if __name__=='__main__':
    main()
