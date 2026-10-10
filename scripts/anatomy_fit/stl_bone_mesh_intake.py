#!/usr/bin/env python3
"""First-party, read-only intake of externally obtained binary/ASCII STL bones.

This does NOT download, distribute, transform, fit, repair or approve a mesh.
The external mesh's units, 3D orientation, licence and anatomical source must
be independently established. In particular a teaching print sculpt is NOT
an unmodified CT-derived segmented bone and cannot satisfy the canonical
pelvis/APP evidence gate by itself.

For selected landmark points in native STL units, the stream records the
nearest *actual triangle vertex* distance, closing the previous gap where
a JSON packet could claim a surface point with no physical mesh bytes.
That is only geometric membership; a nearest vertex cannot authenticate
that it is really osseous ASIS, pubic tubercle or femoral head articular rim.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

MAX_BYTES=256*1024*1024
MAX_TRIANGLES=3_000_000
MAX_REFERENCE_POINTS=100
MANIFEST_ID="NIH3D_3DPX_015682_V2"


def valid_point(p):
    if (not isinstance(p,list) or len(p)!=3 or
            any(type(v) not in (int,float) or not math.isfinite(v) for v in p)):
        raise ValueError("nonfinite or invalid native coordinate")
    return p


def _tri_area(vertices):
    a,b,c=vertices
    u=[b[i]-a[i] for i in range(3)]
    v=[c[i]-a[i] for i in range(3)]
    cross=[u[1]*v[2]-u[2]*v[1],
           u[2]*v[0]-u[0]*v[2],
           u[0]*v[1]-u[1]*v[0]]
    n2=sum(w*w for w in cross)
    e2=max(sum(x*x for x in u),
           sum(x*x for x in v),
           sum((b[i]-c[i])**2 for i in range(3)))
    if e2<=1e-20 or n2<=1e-16*e2*e2:
        raise ValueError("zero/near-degenerate triangle in STL")
    return .5*math.sqrt(n2)


def _binary_triangles(path, count):
    with path.open('rb') as f:
        f.seek(84)
        for i in range(count):
            buf=f.read(50)
            if len(buf)!=50:
                raise ValueError("truncated binary STL")
            fields=struct.unpack('<12fH',buf)
            if any(not math.isfinite(v) for v in fields[:12]):
                raise ValueError(f"nonfinite binary STL triangle {i}")
            yield [list(fields[3:6]),list(fields[6:9]),list(fields[9:12])]


def _ascii_triangles(path):
    active=[]
    inside=False
    with path.open('rt',encoding='ascii',errors='strict') as f:
        for n,line in enumerate(f,1):
            s=line.strip()
            if not s:
                continue
            parts=s.split()
            if len(parts)==2 and parts[0].lower()=='outer' and parts[1].lower()=='loop':
                if inside:
                    raise ValueError("nested ASCII STL outer loop")
                inside=True
                active=[]
            elif parts[0].lower()=='vertex':
                if not inside or len(parts)!=4:
                    raise ValueError(f"malformed ASCII STL vertex at line {n}")
                try:
                    p=[float(x) for x in parts[1:]]
                except ValueError as exc:
                    raise ValueError("invalid ASCII vertex scalar") from exc
                valid_point(p)
                if len(active)>=3:
                    raise ValueError("ASCII STL facet has more than three vertices")
                active.append(p)
            elif parts[0].lower()=='endloop':
                if not inside or len(active)!=3:
                    raise ValueError("incomplete ASCII STL triangle")
                yield active
                active=[]
                inside=False
        if inside:
            raise ValueError("unterminated ASCII STL triangle")


def scan(path, references=None):
    path=Path(path)
    size=path.stat().st_size
    if size<10 or size>MAX_BYTES:
        raise ValueError("unsupported STL byte size")
    refs={} if references is None else references
    if not isinstance(refs,dict) or len(refs)>MAX_REFERENCE_POINTS:
        raise ValueError("invalid landmark reference-point collection")
    for p in refs.values():
        valid_point(p)
    with path.open('rb') as f:
        first=f.read(84)
    if len(first)<84:
        if not first.lstrip().lower().startswith(b'solid'):
            raise ValueError("truncated binary STL header")
        kind="ascii"
    else:
        count=struct.unpack('<I',first[80:84])[0]
        if count<=MAX_TRIANGLES and size==84+50*count:
            kind="binary"
        elif first.lstrip().lower().startswith(b'solid'):
            kind="ascii"
        else:
            raise ValueError("binary STL length/count mismatch")
    iterator=_binary_triangles(path,count) if kind=="binary" else _ascii_triangles(path)
    mins=[float('inf')]*3
    maxs=[float('-inf')]*3
    minima={name:float('inf') for name in refs}
    ntris=0
    area_sum=0.
    for triangle in iterator:
        if ntris>=MAX_TRIANGLES:
            raise ValueError("too many STL triangles")
        area_sum+=_tri_area(triangle)
        ntris+=1
        for p in triangle:
            valid_point(p)
            for i in range(3):
                mins[i]=min(mins[i],p[i])
                maxs[i]=max(maxs[i],p[i])
            for key,target in refs.items():
                dsq=sum((p[i]-target[i])**2 for i in range(3))
                minima[key]=min(minima[key],dsq)
    if not ntris:
        raise ValueError("empty STL mesh")
    sha=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            block=f.read(1024*1024)
            if not block:
                break
            sha.update(block)
    return {
        "format":kind,
        "file_size_bytes":size,
        "content_sha256":sha.hexdigest(),
        "triangle_count":ntris,
        "bounding_box_native_units":{"min":mins,"max":maxs,
            "diagonal":math.dist(mins,maxs)},
        "sum_triangle_area_native_units_sq":area_sum,
        "nearest_actual_vertex_native_units":
            {k:math.sqrt(v) for k,v in minima.items()},
        "STL_native_units_identified":False,
        "physical_landmark_identity_verified":False,
    }


def audit(mesh_path,manifest,bone_id,expected_sha256=None,references=None):
    if (manifest.get("schema_version")!=1 or
            manifest.get("entry_id")!=MANIFEST_ID or
            manifest.get("canonical_promotion_allowed") is not False or
            manifest.get("status")!="SOURCE_DISCOVERY_ONLY"):
        raise ValueError("source manifest identity/status changed")
    if manifest.get("license_status")!="UNVERIFIED_ENTRY_SPECIFIC_LICENSE":
        raise ValueError("review entry-specific licence before changing licence declaration")
    files=manifest.get("files",[])
    mapped={x["bone_id"]:x for x in files}
    if len(mapped)!=7 or len(files)!=7 or bone_id not in mapped:
        raise ValueError("unrecognised skeletal source inventory")
    row=mapped[bone_id]
    if Path(mesh_path).name!=row["source_filename"]:
        raise ValueError("file name does not match recorded bone identity")
    if row.get("unit_to_m") is not None or row.get("mesh_local_to_world") is not None:
        raise ValueError("unverified print scale or world orientation must not be silently applied")
    computed=scan(mesh_path,references)
    if expected_sha256 is not None:
        if (not isinstance(expected_sha256,str) or len(expected_sha256)!=64 or
                any(c not in '0123456789abcdef' for c in expected_sha256)):
            raise ValueError("expected sha256 must be a lowercase digest")
        if computed["content_sha256"]!=expected_sha256:
            raise ValueError("external mesh SHA-256 does not match pinned expected bytes")
    return {
        "schema_version":1,
        "kind":"UNTRUSTED_BONE_MESH_BYTES_INTAKE",
        "status":"SOURCE_LICENSE_SCALE_ANATOMY_REVIEW_REQUIRED",
        "bone_id":bone_id,
        "source_manifest_id":MANIFEST_ID,
        "source_filename":row["source_filename"],
        "mesh":computed,
        "bytes_match_independently_provided_sha256":expected_sha256 is not None,
        "source_asset_class":"sculpted_print_prepared_teaching_mesh_not_CT_segmentation",
        "actual_original_CT_voxels_inspected":False,
        "individual_stature_known":False,
        "physical_landmark_identity_verified":False,
        "source_mesh_scale_verified":False,
        "world_transform_verified":False,
        "entry_licence_verified":False,
        "commercial_reuse_permitted":False,
        "bone_anatomical_geometry_verified":False,
        "bone_surface_reconstruction_permitted":False,
        "canonical_promotion_allowed":False,
        "do_not_fit_skin_mesh_or_muscle_to_this_unregistered_data":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mesh",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--bone-id",required=True)
    p.add_argument("--expected-sha256")
    p.add_argument("--reference-points",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    manifest=json.loads(a.manifest.read_text())
    refs=json.loads(a.reference_points.read_text()) if a.reference_points else None
    result=audit(a.mesh,manifest,a.bone_id,a.expected_sha256,refs)
    payload=json.dumps(result,indent=2)+'\n'
    if a.out:
        with a.out.open('x',encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload,end='')


if __name__=="__main__":
    main()
