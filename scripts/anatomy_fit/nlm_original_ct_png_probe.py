#!/usr/bin/env python3
"""First-party NLM Visible Human CT PNG byte-integrity preflight.

Downloads only explicitly allowlisted original NLM PNG-converted CT slices
on explicit --download; never selects landmarks, decodes Hounsfield units,
creates any mesh, registers geometry or imports data to Home Gym PT assets.

The PNG lossless container integrity and NIH NLM source provenance can be
checked independently. PNG pixel values should NOT be presumed to encode
calibrated HU or physical millimetres without original scanner headers.
Do not mistake a few adjacent source images for a 3D pelvis segmentation.
"""
import argparse
import hashlib
import json
import struct
import urllib.request
import zlib
from pathlib import Path

BASE="https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCT/"
ALLOWED=("cvm1012f.png","cvm1013f.png")
MAGIC=b"\x89PNG\r\n\x1a\n"
MAX_BYTES=2*1024*1024


def inspect_png(blob):
    if not isinstance(blob,bytes) or not blob.startswith(MAGIC):
        raise ValueError("invalid PNG signature")
    if len(blob)>MAX_BYTES:
        raise ValueError("PNG preview larger than allowed size")
    offset=len(MAGIC)
    chunks=[]
    ihdr=None
    saw_end=False
    while offset<len(blob):
        if offset+12>len(blob):
            raise ValueError("truncated PNG chunk header")
        length=struct.unpack_from(">I",blob,offset)[0]
        kind=blob[offset+4:offset+8]
        if any(ch<65 or ch>122 for ch in kind):
            raise ValueError("invalid PNG chunk type")
        if length>MAX_BYTES or offset+12+length>len(blob):
            raise ValueError("truncated or oversized PNG chunk")
        payload=blob[offset+8:offset+8+length]
        provided=struct.unpack_from(">I",blob,offset+8+length)[0]
        actual=zlib.crc32(kind+payload)&0xffffffff
        if actual!=provided:
            raise ValueError("PNG CRC32 integrity mismatch")
        chunks.append(kind.decode("ascii"))
        if len(chunks)==1:
            if kind!=b"IHDR" or length!=13:
                raise ValueError("PNG missing first IHDR")
            width,height,depth,color,compression,filtermethod,interlace=struct.unpack(">IIBBBBB",payload)
            if not (0<width<=8192 and 0<height<=8192 and compression==0 and filtermethod==0
                    and color in (0,2,3,4,6) and depth in (1,2,4,8,16) and interlace in (0,1)):
                raise ValueError("invalid PNG image dimensions or encoding")
            ihdr={"width_pixels":width,"height_pixels":height,
                  "bit_depth":depth,"colour_type":color,"interlace_method":interlace}
        elif kind==b"IHDR":
            raise ValueError("duplicate PNG IHDR")
        offset+=12+length
        if kind==b"IEND":
            if length or offset!=len(blob):
                raise ValueError("IEND not final zero-length PNG chunk")
            saw_end=True
            break
    if not saw_end or "IDAT" not in chunks:
        raise ValueError("PNG missing pixel data or terminator")
    return {
        "container_format":"PNG",
        "PNG_chunk_CRC32_all_checked":True,
        "pixel_data_is_not_anatomically_calibrated_by_this_script":True,
        "image_header":ihdr,
        "container_chunks":chunks,
        "source_sha256":hashlib.sha256(blob).hexdigest(),
        "bytes":len(blob),
        "source_3d_geometry_registered":False,
        "CT_Hounsfield_units_verified":False,
        "axial_slice_patient_world_transform_verified":False,
        "S1_ASIS_pubis_femur_features_identified":False,
        "canonical_promotion_allowed":False,
    }


def probe_file(path,expected_name=None):
    p=Path(path)
    if p.stat().st_size>MAX_BYTES:
        raise ValueError("oversized preview source image")
    if expected_name is not None and p.name!=expected_name:
        raise ValueError("preview file identity mismatch")
    return inspect_png(p.read_bytes())


def download_allowlisted(name,destination):
    if name not in ALLOWED:
        raise ValueError("not a pinned NLM preview slice identifier")
    dst=Path(destination)
    if dst.exists():
        raise ValueError("refuse to replace any existing downloaded CT preview")
    req=urllib.request.Request(BASE+name,headers={"User-Agent":"HomeGymPT-CT-Source-Integrity-Check/1.0"})
    # No URL redirection to other hosts to prevent changing source custody.
    class NLMOnlyRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            raise ValueError("NLM source redirected: review source custody before download")
    opener=urllib.request.build_opener(NLMOnlyRedirect())
    with opener.open(req,timeout=20) as response:
        if response.status!=200:
            raise ValueError("original NLM CT file unavailable")
        data=response.read(MAX_BYTES+1)
    result=inspect_png(data)
    if result["image_header"]["width_pixels"]!=512 or result["image_header"]["height_pixels"]!=512:
        raise ValueError("PNG frame is not the original 512x512 CT frame")
    with dst.open("xb") as f:
        f.write(data)
    result["source_url"]=BASE+name
    result["original_png_downloaded_only_to_temporary_staging"]=True
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file",type=Path)
    p.add_argument("--download",choices=ALLOWED)
    p.add_argument("--temporary-out",type=Path)
    a=p.parse_args()
    if bool(a.file)==bool(a.download):
        p.error("choose exactly --file or --download")
    if a.download:
        if not a.temporary_out:
            p.error("--download requires create-only --temporary-out path")
        result=download_allowlisted(a.download,a.temporary_out)
    else:
        result=probe_file(a.file)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
