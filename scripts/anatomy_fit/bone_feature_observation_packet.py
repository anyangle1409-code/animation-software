#!/usr/bin/env python3
"""Source-bone landmark observation packet — numerical provenance contract.

Collects seven anatomically named features from independently segmented BONY
surfaces, not from skin or stick-control endpoints: four bony ASIS/pubic
tubercles selected from vertices; S1 from four labelled endplate rim points;
and two femoral-head centres from independent articular sphere fits.

A reported JSON asset (even with zero residual) cannot prove that these
are correctly classified physical anatomical features or a correct CT
segmentation. Output is ALWAYS unapproved and never changes a skeleton.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

FEATURES={
    'asis_left':('hip_bone_left','surface_vertex'),
    'asis_right':('hip_bone_right','surface_vertex'),
    'pubic_tubercle_left':('hip_bone_left','surface_vertex'),
    'pubic_tubercle_right':('hip_bone_right','surface_vertex'),
    's1_endplate_centre':('sacrum','endplate_four_rim_midpoint'),
    'hip_centre_left':('femur_left','articular_sphere_fit'),
    'hip_centre_right':('femur_right','articular_sphere_fit'),
}
BUDGET_MM=1.0  # engineering registration; NOT a CT accuracy bound


def pt(v):
    if (not isinstance(v,list) or len(v)!=3 or
            any(type(x) not in (int,float) or not math.isfinite(x) for x in v)):
        raise ValueError('invalid 3D point')
    return v


def sub(a,b):
    return [a[i]-b[i] for i in range(3)]


def add(a,b):
    return [a[i]+b[i] for i in range(3)]


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def mid(a,b):
    return [(x+y)/2 for x,y in zip(a,b)]


def norm(a):
    return math.sqrt(dot(a,a))


def solve3(A,b):
    """Gauss-Jordan normal equations with singularity rejection."""
    M=[[float(A[i][j]) for j in range(3)]+[float(b[i])] for i in range(3)]
    scale=max(abs(v) for row in M for v in row[:3])
    if scale<=0:
        raise ValueError('degenerate articular samples')
    for col in range(3):
        row=max(range(col,3),key=lambda i:abs(M[i][col]))
        if abs(M[row][col]) <= scale*1e-9:
            raise ValueError('degenerate/non-spatial articular sphere fit')
        M[row],M[col]=M[col],M[row]
        pivot=M[col][col]
        M[col]=[x/pivot for x in M[col]]
        for j in range(3):
            if j==col:
                continue
            mul=M[j][col]
            M[j]=[x-mul*y for x,y in zip(M[j],M[col])]
    return [row[3] for row in M]


def sphere_fit(points):
    """Algebraic first-party spherical regression, numeric screening only."""
    if not isinstance(points,list) or len(points)<6:
        raise ValueError('at least six femoral articular samples required')
    P=[pt(p) for p in points]
    a=P[0]
    u=[sub(x,a) for x in P[1:]]
    A=[[0.,0.,0.] for _ in range(3)]
    b=[0.,0.,0.]
    for v in u:
        vv=dot(v,v)
        for i in range(3):
            b[i]+=v[i]*vv
            for j in range(3):
                A[i][j]+=2*v[i]*v[j]
    cr=solve3(A,b)
    centre=add(a,cr)
    distances=[norm(sub(p,centre)) for p in P]
    radius=sum(distances)/len(distances)
    rms=math.sqrt(sum((r-radius)**2 for r in distances)/len(distances))
    if not .005<radius<.1:
        raise ValueError('sphere radius outside broad diagnostic corridor')
    if rms>max(.001,radius*.05):
        raise ValueError('articular samples do not fit a coherent sphere')
    return centre, {'fitted_sphere_radius_m':radius,
                    'sphere_surface_rms_mm':rms*1000,
                    'sample_count':len(P),
                    'clinical_head_centre_verified':False}


def extract(packet):
    if packet.get('schema_version')!=1 or packet.get('kind')!='SOURCE_BONE_FEATURE_OBSERVATION_PACKET':
        raise ValueError('unexpected source observation schema')
    if packet.get('status')!='AUDIT_ONLY' or packet.get('canonical_promotion_allowed') is not False:
        raise ValueError('packet cannot authorize canonical promotion')
    if packet.get('units')!='m':
        raise ValueError('features must be in world metres, not mm')
    if packet.get('world_convention')!='HGPT_LEFT_POSITIVE_X_POSTERIOR_Y_SUPERIOR_Z':
        raise ValueError('world convention mismatch; registration required')
    data=packet.get('features',{})
    if set(data)!=set(FEATURES):
        raise ValueError('seven physical bone features required; no extras')
    points,provenance,diagnostics={}, {}, {}
    for name,(expected_bone,method) in FEATURES.items():
        f=data[name]
        if f.get('source_bone_id')!=expected_bone or f.get('extraction_method')!=method:
            raise ValueError(f'{name}: wrong source bone or physical extraction method')
        if f.get('source_asset_class')!='independently_segmented_bone_surface':
            raise ValueError(f'{name}: skin, legacy proxy or unsegmented source forbidden')
        sha=f.get('source_asset_sha256')
        if not isinstance(sha,str) or len(sha)!=64 or any(ch not in '0123456789abcdef' for ch in sha):
            raise ValueError(f'{name}: invalid source asset SHA256')
        if not isinstance(f.get('source_asset_uri'),str) or not f['source_asset_uri'].startswith('https://'):
            raise ValueError(f'{name}: stable source asset link required')
        supplied=pt(f.get('reported_world_point_m'))
        if method=='surface_vertex':
            actual=pt(f.get('selected_bony_surface_vertex_m'))
            info={'selected_surface_vertex_delta_mm':norm(sub(actual,supplied))*1000}
        elif method=='endplate_four_rim_midpoint':
            rim=f.get('rim_points_world_m',{})
            if set(rim)!=set(('left','right','anterior','posterior')):
                raise ValueError('four labelled S1 endplate rim points required')
            R={k:pt(v) for k,v in rim.items()}
            actual=mid(mid(R['left'],R['right']),
                       mid(R['anterior'],R['posterior']))
            if norm(sub(R['left'],R['right']))<.03 or norm(sub(R['anterior'],R['posterior']))<.03:
                raise ValueError('degenerate S1 rim spans')
            info={'endplate_rim_lateral_span_mm':norm(sub(R['left'],R['right']))*1000,
                  'endplate_rim_AP_span_mm':norm(sub(R['anterior'],R['posterior']))*1000}
        else:
            actual,info=sphere_fit(f.get('articular_points_world_m'))
        delta=norm(sub(actual,supplied))*1000
        if delta>BUDGET_MM:
            raise ValueError(f'{name}: claimed landmark differs from feature-derived centre by {delta:.3f} mm')
        points[name]=actual
        diagnostics[name]={**info,'claim_vs_computed_mm':round(delta,6),
                           'physical_feature_identity_independently_checked':False}
        provenance[name]={
            'source_kind':'independently_segmented_bone_surface',
            'feature_identity_verified':False,
            'source_asset_sha256':sha,
            'extraction_method':method,
            'source_asset_uri':f['source_asset_uri'],
            'evidence_decision':'COMPUTED_NOT_ANATOMICAL_ACCEPTANCE'}
    return {
        'schema_version':1,
        'kind':'BONY_PELVIC_LANDMARK_EXTRACTION_DIAGNOSTIC',
        'status':'NUMERIC_GEOMETRY_ONLY_SOURCE_IDENTITY_UNVERIFIED',
        'points_m':points,
        'provenance':provenance,
        'feature_diagnostics':diagnostics,
        'canonical_promotion_allowed':False,
        'source_surface_identity_verified':False,
        'independent_anatomy_review_required':True,
        'no_skin_mesh_used':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    data=a.packet.read_bytes()
    result=extract(json.loads(data))
    result['packet_sha256']=hashlib.sha256(data).hexdigest()
    payload=json.dumps(result,indent=2)+'\n'
    if a.out:
        with a.out.open('x',encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload,end='')


if __name__=='__main__':
    main()
