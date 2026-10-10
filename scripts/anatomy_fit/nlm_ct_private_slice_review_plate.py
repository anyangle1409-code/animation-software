#!/usr/bin/env python3
"""Prepare a PRIVATE browser-viewable three-slice CT plate with prior hypotheses.

Rewindows original source-pinned CT scanner intensities. Original medical PNG,
GE header, and generated review plate NEVER enter Git, a public artifact, or a
production asset. Review points are visibly marked as UNVERIFIED hypotheses.
Only a first-party Python stdlib PNG encoder is used; no PIL, Blender or cloud API.
"""
import argparse
import base64
import hashlib
from html import escape
import json
from pathlib import Path
import struct
import zlib

from ct_pelvis_window_geometry import assert_private_location
from nlm_ct_provisional_surface import GRID, _private_source_slice
from nlm_ct_raw_png_calibration import validate_calibration_evidence
from pelvic_ct_series_manifest import validate_series_bundle

WINDOWS=(("Soft tissue", -200, 400),("Bone review",-200,1600))


def encode_windowed_gray_png(stored_pixels, low_hu, high_hu, size=GRID):
    """Lossless 8-bit PNG of explicitly windowed HU for visual review only."""
    if (type(size) is not int or not 1<=size<=GRID or
            len(stored_pixels)!=size*size or
            type(low_hu) is not int or type(high_hu) is not int or
            high_hu<=low_hu):
        raise ValueError("invalid intensity window or image size")
    gain=255.0/(high_hu-low_hu)
    scan=bytearray()
    for row in range(size):
        scan.append(0)
        for v in stored_pixels[row*size:(row+1)*size]:
            hu=v-1024
            value=round((hu-low_hu)*gain)
            scan.append(max(0,min(255,value)))
    def chunk(name, data):
        return (struct.pack(">I",len(data))+name+data+
                struct.pack(">I",zlib.crc32(name+data)&0xffffffff))
    header=b"\x89PNG\r\n\x1a\n"
    return (header+
            chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,0,0,0,0))+
            chunk(b"IDAT",zlib.compress(bytes(scan),level=8))+
            chunk(b"IEND",b""))


def private_ct_plate(bundle, cal, review, group, centre_id, source_dir,
                     *, loader=None):
    """Generate a single embedded SVG from exact original three source slices."""
    validate_series_bundle(bundle)
    validate_calibration_evidence(cal,bundle)
    if review.get("kind")!="NLM_CT_ANATOMICAL_REVIEW_PACKET" or group not in (1,2):
        raise ValueError("invalid original review packet or acquisition group")
    rows=bundle["series"][group-1]["slices"]
    ids=[r["source_id"] for r in rows]
    if centre_id not in ids:
        raise ValueError("selected source image not in this verified acquisition")
    i=ids.index(centre_id)
    if not (1<=i<len(rows)-1):
        raise ValueError("three-slice inspection must not cross acquisition boundary")
    nearby=rows[i-1:i+2]
    selected=[]
    for point in review["observations"]:
        if point["source_id"]!=centre_id:
            continue
        centre=rows[i]
        if (point["source_png_sha256"]!=centre["source_png_sha256"] or
                point["source_header_sha256"]!=centre["source_header_sha256"] or
                abs(point["scanner_S_mm"]-centre["scanner_centre_RAS_mm"][2])>1e-6):
            raise ValueError("unverified observation source reference")
        r,c=point["pixel"]["row"],point["pixel"]["column"]
        if type(r) is not int or type(c) is not int or not 0<=r<GRID or not 0<=c<GRID:
            raise ValueError("invalid original source pixel coordinates")
        selected.append(point)
    if not selected:
        raise ValueError("no original candidate point on requested axial plane")
    source_dir=assert_private_location(source_dir)
    if loader is None:loader=_private_source_slice
    frames=[]
    for row in nearby:
        geometry,pixels=loader(source_dir,row)
        if len(pixels)!=GRID*GRID or abs(geometry["scanner_S_mm"]-
                                            row["scanner_centre_RAS_mm"][2])>1e-6:
            raise ValueError("original pinned GE header and CT image disagree")
        frames.append(pixels)
    # Legend colour visually identifies prior annotations; colours NEVER imply
    # verified anatomical material or segmentation.
    swatches=("#dc2626","#2563eb","#b45309","#16a34a","#9333ea")
    width=1692
    height=1220
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#151820"/>',
           '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#f8fafc}'
           '.small{font-size:15px;fill:#e5e7eb}.label{font-size:17px;fill:#f8fafc}'
           '.head{font-weight:bold;font-size:22px}</style>',
           '<text x="32" y="40" class="head">ORIGINAL CT SOURCE REVIEW — UNVERIFIED HYPOTHESIS PIXELS</text>',
           f'<text x="32" y="68" class="small">Source: NLM Visible Human, acquisition group {group}; centre {escape(centre_id)}'
           f'; exact original scanner orientation; axial spacing 3 mm</text>',
           '<text x="32" y="91" class="small">Screen/annotation only. NOT registered to HGPT skeleton. '
           'Original pixel/FOV centre convention remains unresolved.</text>']
    for w,(label,low,high) in enumerate(WINDOWS):
        y=125+w*545
        parts.append(f'<text x="32" y="{y-13}" class="label">'
                     f'{escape(label)} window: {low} to {high} HU</text>')
        for k,(row,pixels) in enumerate(zip(nearby,frames)):
            x=32+k*554
            png=encode_windowed_gray_png(pixels,low,high)
            uri=base64.b64encode(png).decode("ascii")
            parts.append(f'<g transform="translate({x} {y})">'
                         f'<image x="0" y="0" width="512" height="512" '
                         f'href="data:image/png;base64,{uri}"/>'
                         '<rect x="0" y="0" width="512" height="512" '
                         'fill="none" stroke="#e5e7eb" stroke-width="1"/>'
                         f'<text x="8" y="23" class="label" fill="#fff">'
                         f'{escape(row["source_id"])}  S={row["scanner_centre_RAS_mm"][2]:.0f} mm</text>')
            if k==1:
                for j,point in enumerate(selected):
                    r,c=point["pixel"]["row"],point["pixel"]["column"]
                    color=swatches[j%len(swatches)]
                    hu=pixels[r*GRID+c]-1024
                    parts.append(f'<circle cx="{c+.5}" cy="{r+.5}" r="8" '
                                 f'fill="none" stroke="{color}" stroke-width="2.6"/>')
                    parts.append(f'<path d="M {c-13} {r+.5} L {c-4} {r+.5} '
                                 f'M {c+5} {r+.5} L {c+14} {r+.5} '
                                 f'M {c+.5} {r-13} L {c+.5} {r-4} '
                                 f'M {c+.5} {r+5} L {c+.5} {r+14}" '
                                 f'stroke="{color}" stroke-width="1.3"/>')
                    # A small, clearly conditional letter is strictly an
                    # original point ID index, NOT a named-bone label.
                    parts.append(f'<text x="{c+11}" y="{r-10}" '
                                 f'font-size="16" fill="{color}" '
                                 f'stroke="#101010" stroke-width="0.7" '
                                 f'paint-order="stroke">{j+1}</text>')
            parts.append('</g>')
    legend_y=1200
    entries=[]
    for j,point in enumerate(selected):
        r,c=point["pixel"]["row"],point["pixel"]["column"]
        hu=frames[1][r*GRID+c]-1024
        entries.append({
            "ordinal":j+1,
            "id":point["observation_id"],
            "original_pixel_row":r,
            "original_pixel_column":c,
            "source_centre_HU":hu,
            "bone_identity_or_surface_verified":False,
        })
    parts.append('<text x="32" y="1125" class="small">Centre-plane annotations (number refers to original candidate point, NOT bone identity):</text>')
    for j,entry in enumerate(entries):
        x=32+(j%2)*830
        y=1150+(j//2)*20
        parts.append(f'<text x="{x}" y="{y}" class="small">'
                     f'<tspan fill="{swatches[j%len(swatches)]}">{j+1}.</tspan>'
                     f' {escape(entry["id"])}  ({entry["original_pixel_row"]},'
                     f'{entry["original_pixel_column"]})  {entry["source_centre_HU"]} HU</text>')
    parts.append('<text x="32" y="1214" class="small">ANATOMICAL IDENTITY NOT VERIFIED '
                 '— no landmarks, bones, joints, or canonical skeleton geometry accepted.</text>')
    parts.append('</svg>\n')
    # Check caption fits if there are more prior point hypotheses; no crop.
    if len(entries)>5:
        raise ValueError("source review plate legend exceeds verified capacity")
    return "".join(parts),{
        "kind":"PRIVATE_ORIGINAL_PINNED_CT_REVIEW_PLATE_NONCANONICAL",
        "source_ids":[r["source_id"] for r in nearby],
        "source_sha256":[r["source_png_sha256"] for r in nearby],
        "scanner_S_mm":[r["scanner_centre_RAS_mm"][2] for r in nearby],
        "windows_HU":[[v[1],v[2]] for v in WINDOWS],
        "points":entries,
        "raw_CT_or_header_bytes_committed":False,
        "reviewer_identified_real_bony_landmarks":0,
        "pixel_centre_convention_verified":False,
        "canonical_promotion_allowed":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ct-dir",required=True)
    p.add_argument("--bundle",required=True)
    p.add_argument("--calibration",required=True)
    p.add_argument("--review",required=True)
    p.add_argument("--group",type=int,required=True)
    p.add_argument("--source-id",required=True)
    p.add_argument("--out",required=True,help="private .svg review plate path (outside repo)")
    a=p.parse_args()
    out=assert_private_location(a.out)
    if out.suffix.lower()!=".svg":
        raise ValueError("private reviewer view is SVG, not a production mesh")
    side=out.with_suffix(".json")
    if out.exists() or side.exists():
        raise ValueError("refuse to overwrite any private source review")
    plate,evidence=private_ct_plate(
        json.loads(Path(a.bundle).read_text()),
        json.loads(Path(a.calibration).read_text()),
        json.loads(Path(a.review).read_text()),
        a.group,a.source_id,a.ct_dir)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:f.write(plate)
    with side.open("x",encoding="utf-8") as f:
        json.dump(evidence,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps({
        "source_ids":evidence["source_ids"],
        "candidate_pixels":evidence["points"],
        "svg_sha256":hashlib.sha256(plate.encode()).hexdigest(),
        "source_CT_image_or_header_published":False,
        "canonical_promotion_allowed":False,
    },indent=2))


if __name__=="__main__":
    main()
