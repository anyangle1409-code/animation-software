#!/usr/bin/env python3
"""NLM pelvic-region CT SCOUT: source-image statistics and scanner RAS only.

Read a SMALL explicit representative set of original 16-bit grayscale CT
PNG files, verified source by NLM HTTPS and each corresponding original
scanner header. Never derive HU, segment a bone or call an image a "pelvis"
without anatomical image review. Do not export raw patient headers/pixels,
only geometry, salted-independent (SHA-256) source identity and a
diagnostic raw stored-pixel distribution.

Original CT scan groups have DIFFERENT FOV, slice thickness and spacing.
Every slice uses its OWN scanner geometry; stitching is not performed.
"""
import argparse
import hashlib
import json
import math
import struct
import urllib.request
import zlib
from pathlib import Path
import nlm_original_ct_png_probe as png_probe
import nlm_ct_scanner_geometry_header as hdr

INDEX_BASE="https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCT/"
HEADER_BASE=hdr.ROOT
# Selected from actual NLM PNG index; no adjacent-slice or pelvis label implied.
SCOUT_IDS=(1300,1399,1451,1500,1551,1602,1650,1701,1752,1800,1906,1948)
MAX_HEADER_BYTES=64*1024


def _safe_download(url,limit):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):
            raise ValueError("NLM source redirected")
    opener=urllib.request.build_opener(NoRedirect())
    req=urllib.request.Request(url,headers={"User-Agent":"HomeGymPT-SkeletalCT-SourceScout/1.0"})
    with opener.open(req,timeout=25) as response:
        if response.status!=200:
            raise ValueError("NLM source file not found")
        blob=response.read(limit+1)
    if len(blob)>limit:
        raise ValueError("source file exceeds acquisition limit")
    return blob


def _paeth(a,b,c):
    p=a+b-c
    aa,bb,cc=abs(p-a),abs(p-b),abs(p-c)
    return a if aa<=bb and aa<=cc else b if bb<=cc else c


def decode_grayscale_png16(blob):
    """Decode ONLY 16-bit grayscale, non-interlaced PNG; bounded rows."""
    info=png_probe.inspect_png(blob)
    ihdr=info['image_header']
    if (ihdr["width_pixels"]!=512 or ihdr["height_pixels"]!=512 or
            ihdr["bit_depth"]!=16 or ihdr["colour_type"]!=0 or
            ihdr["interlace_method"]!=0):
        raise ValueError("CT scout requires original 512x512 16-bit grayscale PNG")
    pos=8
    compressed=[]
    seen_idat=False
    while pos<len(blob):
        n=struct.unpack_from(">I",blob,pos)[0]
        tag=blob[pos+4:pos+8]
        if tag==b"IDAT":
            compressed.append(blob[pos+8:pos+8+n])
            seen_idat=True
        elif tag==b"IEND":
            break
        pos+=12+n
    if not seen_idat:
        raise ValueError("PNG missing compressed pixels")
    width=ihdr["width_pixels"]
    height=ihdr["height_pixels"]
    stride=width*2
    expected=height*(stride+1)
    dec=zlib.decompressobj()
    # Strict decompression limit; no unbounded large in-memory scan.
    raw=dec.decompress(b"".join(compressed),expected+1)
    if (len(raw)!=expected or not dec.eof or dec.unused_data or dec.unconsumed_tail):
        raise ValueError("PNG source decompressed row size inconsistent with IHDR")
    prev=bytearray(stride)
    values=[]
    for rownum in range(height):
        start=rownum*(stride+1)
        filtertype=raw[start]
        src=raw[start+1:start+1+stride]
        dst=bytearray(stride)
        if filtertype not in range(5):
            raise ValueError("unsupported PNG row filter")
        for k,ch in enumerate(src):
            left=dst[k-2] if k>=2 else 0
            above=prev[k]
            up_left=prev[k-2] if k>=2 else 0
            if filtertype==0:
                predict=0
            elif filtertype==1:
                predict=left
            elif filtertype==2:
                predict=above
            elif filtertype==3:
                predict=(left+above)//2
            else:
                predict=_paeth(left,above,up_left)
            dst[k]=(ch+predict)&255
        prev=dst
        values.extend(v[0] for v in struct.iter_unpack(">H",dst))
    if len(values)!=512*512:
        raise AssertionError("unexpected decoded pixel count")
    return values


def raw_statistics(values):
    if not isinstance(values,list) or not values:
        raise ValueError("raw source pixels absent")
    if any(type(v)!=int or v<0 or v>65535 for v in values):
        raise ValueError("source pixel out of 16-bit range")
    s=sorted(values)
    n=len(values)
    get=lambda p:s[min(n-1, int((n-1)*p))]
    return {
        "number_of_raw_pixels":n,
        "stored_png_scalar_range":[s[0],s[-1]],
        "mean_stored_png_scalar":round(sum(values)/n,2),
        "raw_percentile_01":get(.01),"raw_percentile_10":get(.1),
        "raw_percentile_50":get(.5),"raw_percentile_90":get(.9),
        "raw_percentile_99":get(.99),
        "number_of_zero_scalars":sum(v==0 for v in values),
        "original_CT_HU_rescale_verified":False,
        "clinical_bone_density_threshold_approved":False,
        "anatomical_bone_segmentation_performed":False,
    }



def pixel_tile_signal(values,threshold,tiles=32):
    """Low-resolution RAW-STORED-SCALAR occupancy, NOT cortical bone.

    Each symbol means the fraction of original 16-bit scalar values at
    or above a deliberately provisional numeric threshold. This is a
    lossy pixel-data diagnostic, not HU, bone, medical image identification
    or anatomical verification; no input CT image is exported.
    """
    if type(threshold)!=int or not 0<=threshold<=65535:
        raise ValueError("invalid integer raw pixel threshold")
    if tiles!=32 or len(values)!=512*512:
        raise ValueError("tiles require original 512x512 source scalar matrix")
    pixels_per_tile=16*16
    palette=" .:-=+*#%@"
    grid=[]
    for ty in range(32):
        row=""
        for tx in range(32):
            n=0
            for yy in range(ty*16,(ty+1)*16):
                offset=yy*512+tx*16
                n+=sum(x>=threshold for x in values[offset:offset+16])
            # Nine thresholds partition [0%,100%], emphasizing modest
            # occupancy without falsely calling "bright" tissue bone.
            fraction=n/pixels_per_tile
            index=min(len(palette)-1,int(fraction*len(palette)))
            row+=palette[index]
        grid.append(row)
    return {
        "raw_scalar_threshold":threshold,
        "grid_size":[32,32],
        "tile_method":"fraction of stored PNG scalars at-or-above threshold",
        "tile_characters":" .:-=+*#%@",
        "tiles":grid,
        "unverified_HU_and_bone_identity":True,
        "canonical_promotion_allowed":False,
    }


def geometry_only(header_bytes):
    # Identifying fields are discarded and never printed or returned.
    safe=hdr.scanner_geometry_from_text(header_bytes)
    return {
        "scanner_RAS_image_location_superior_mm":safe['image_location_superior_mm'],
        "scanner_RAS_center_mm":safe['reported_plane_centre_RAS_mm'],
        "in_plane_mm_per_pixel":safe['pixel_spacing_mm'],
        "slice_thickness_mm":safe['slice_thickness_mm'],
        "nominal_slice_spacing_mm":safe['nominal_series_slice_spacing_mm'],
        "safe_geometry_parser_PIIs_excluded":safe["patient_identifiers_excluded_by_allowlist"],
        "image_to_patient_sample_center_mapping_still_unverified":True,
        "source_header_sha256":hashlib.sha256(header_bytes).hexdigest(),
    }


def record(name,png_bytes,header_bytes,include_signal=False):
    identity=png_probe.inspect_png(png_bytes)
    values=decode_grayscale_png16(png_bytes)
    geometry=geometry_only(header_bytes)
    source_id=int(name[3:7])
    return {
        "slice_id":source_id,
        "filename":name,
        "source_https_url":INDEX_BASE+name,
        "source_png_sha256":identity["source_sha256"],
        "source_png_bytes":identity["bytes"],
        "PNG_byte_integrity_valid":True,
        **geometry,
        "raw_pixel_statistics":raw_statistics(values),
        "raw_pixel_signal_tiles":[pixel_tile_signal(values,1200),pixel_tile_signal(values,1600)] if include_signal else None,
        "bone_region_identified_by_anatomical_review":False,
        "sample_reference_region_only":"NLM 1948 gallery image is stated upper thigh below femoral heads"
             if source_id==1948 else None,
        "no_source_image_or_identifier_committed":True,
    }


def atlas(source_ids,loader,include_signal=False):
    ids=tuple(source_ids)
    if len(ids)>len(SCOUT_IDS) or len(set(ids))!=len(ids) or any(x not in SCOUT_IDS for x in ids):
        raise ValueError("requested slice not in reviewed NLM source scout allowlist")
    rows=[]
    for n in ids:
        name=f"cvm{n}f.png"
        header=f"cvm{n}f.txt"
        img=loader(INDEX_BASE+name,png_probe.MAX_BYTES)
        met=loader(HEADER_BASE+header,MAX_HEADER_BYTES)
        rows.append(record(name,img,met,include_signal=include_signal))
    # Differences in scanner spacing are meaningful; never connect
    # z-positions by numeric source ID or assume uniform 1 mm sample spacing.
    rows.sort(key=lambda r:r["scanner_RAS_image_location_superior_mm"],reverse=True)
    return {
        "schema_version":1,
        "kind":"NLM_ORIGINAL_CT_ANATOMICAL_REGION_SCOUT_PROVISIONAL",
        "status":"RAW_CT_SOURCE_STATS_ONLY_NOT_PELVIS_CONFIRMED",
        "source_custodian":"US National Library of Medicine",
        "slice_count":len(rows),
        "scanner_positions_sorted_not_rebuilt_as_volume":True,
        "all_scan_groups_retain_individual_pixel_and_slice_spacing":True,
        "stored_PNG_scalars_not_verified_Hounsfield_units":True,
        "reference_1948_upper_thigh_from_official_gallery_not_human_verified_in_this_run":True,
        "raw_source_images_saved_or_redistributed":False,
        "anatomical_landmarks_verified":False,
        "skeleton_updated":False,
        "canonical_promotion_allowed":False,
        "slices":rows,
    }


def verify_pinned_manifest(atlas_record, manifest):
    """Fail closed on NLM image or original-header byte changes.

    Scanner geometry and cryptographic source hashes are verified as data
    integrity only. A match does not authenticate anatomical region labels,
    bone surfaces, HU or pixel-world centre convention.
    """
    if (manifest.get("schema_version")!=1 or
            manifest.get("kind")!="PINNED_NLM_CT_SCOUT_SOURCE_MANIFEST" or
            manifest.get("canonical_promotion_allowed") is not False or
            manifest.get("anatomical_pelvic_slice_confirmed") is not False):
        raise ValueError("source manifest improperly claims anatomical acceptance")
    pinned=manifest.get("slices",[])
    if len(pinned)!=len(SCOUT_IDS) or set(x.get("id") for x in pinned)!=set(SCOUT_IDS):
        raise ValueError("original 12 pinned CT source records must be complete and unique")
    actual=atlas_record["slices"]
    by_id={x["id"]:x for x in pinned}
    for row in actual:
        x=by_id[row["slice_id"]]
        if (x["source_png_name"]!=row["filename"] or
                x["source_png_sha256"]!=row["source_png_sha256"] or
                x["source_header_sha256"]!=row["source_header_sha256"]):
            raise ValueError("original NLM pixel or scanner header SHA changed from pinned bytes")
        if (abs(x["scanner_superior_mm"]-
                row["scanner_RAS_image_location_superior_mm"])>1e-6 or
                x["pixel_spacing_mm"]!=row["in_plane_mm_per_pixel"] or
                x["thickness_mm"]!=row["slice_thickness_mm"]):
            raise ValueError("original CT scanner coordinates/scale changed from pinned record")
    return {
        "source_hashes_and_scanner_positions_match_previously_verified_inputs":True,
        "source_slices_checked":len(actual),
        "original_bony_regions_identified":False,
        "Hounsfield_calibration_proven":False,
        "anatomical_image_landmarks_verified":False,
        "canonical_promotion_allowed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live-scout",action="store_true")
    p.add_argument("--slice-ids",nargs="+",type=int,default=list(SCOUT_IDS))
    p.add_argument("--out",type=Path)
    p.add_argument("--pinned-manifest",type=Path)
    p.add_argument("--density-ascii",action="store_true",help="Output lossy 32x32 raw scalar occupancy grids; never interpreted as bone")
    a=p.parse_args()
    if not a.live_scout:
        p.error("network scout requires explicit --live-scout")
    output=atlas(a.slice_ids,_safe_download,include_signal=a.density_ascii)
    if a.pinned_manifest:
        output['previous_source_byte_identity_check']=verify_pinned_manifest(
            output,json.loads(a.pinned_manifest.read_text()))
    content=json.dumps(output,indent=2)+"\n"
    if a.out:
        with a.out.open('x',encoding="utf-8") as f:
            f.write(content)
    else:
        print(content)


if __name__=="__main__":
    main()
