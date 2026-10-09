#!/usr/bin/env python3
"""Bony anterior pelvic plane (APP) registration, with strict provenance gates.

First-party, stdlib-only mathematical implementation. APP axes:
  LEFT:      R-ASIS -> L-ASIS (+X in HGPT neutral model)
  POSTERIOR: plane normal chosen so LEFT x POSTERIOR = SUPERIOR
  SUPERIOR:  ASIS midpoint minus pubic-tubercles midpoint, orthogonal to LEFT
This is a pelvic ANATOMICAL frame, not standing pose or hip-motion frame.
The plane needs 2 bony ASIS and the midpoint of 2 bony pubic TUBERCLES;
skin/groove landmarks and provisional pubic controls are not adequate.

An APP plane is geometrically definable without proof that its landmark
inputs are anatomical. Therefore provenance and numerical geometry are
reported SEPARATELY. No output authorizes changing the canonical skeleton.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

REQUIRED_BONY = ('asis_left', 'asis_right',
                 'pubic_tubercle_left', 'pubic_tubercle_right',
                 's1_endplate_centre', 'hip_centre_left', 'hip_centre_right')
APP_INPUT = REQUIRED_BONY[:4]


def _pt(pt, name='landmark'):
    if (not isinstance(pt, list) or len(pt) != 3 or
            any(type(x) not in (float, int) or not math.isfinite(x) for x in pt)):
        raise ValueError(f'{name}: invalid finite 3D coordinate')
    return pt


def _sub(a,b):
    return [a[i]-b[i] for i in range(3)]


def _add(a,b):
    return [a[i]+b[i] for i in range(3)]


def _mul(a,s):
    return [v*s for v in a]


def _dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def _cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0]]


def _length(a):
    return math.sqrt(_dot(a,a))


def _unit(a,label,min_length=.000001):
    n=_length(a)
    if n<min_length:
        raise ValueError(f'{label}: degenerate geometry/collinear landmarks')
    return _mul(a,1/n)


def _mid(a,b):
    return _mul(_add(a,b),.5)


def app_frame(points):
    """Return proper orthonormal anatomical axes; not anatomical approval."""
    for key in APP_INPUT:
        _pt(points[key],key)
    L,R=(points[k] for k in ('asis_left','asis_right'))
    PL,PR=(points[k] for k in ('pubic_tubercle_left','pubic_tubercle_right'))
    asis=_mid(L,R)
    pubic=_mid(PL,PR)
    left=_unit(_sub(L,R),'left/right ASIS separation',.03)
    inferior_to_superior=_sub(asis,pubic)
    up_component=_sub(inferior_to_superior,_mul(left,_dot(inferior_to_superior,left)))
    up=_unit(up_component,'ASIS-to-pubic height/APP collinearity',.03)
    posterior=_unit(_cross(up,left),'APP plane normal')
    up=_unit(_cross(left,posterior),'orthonormal superior axis')
    axes={'left':left,'posterior':posterior,'superior':up}
    for a in axes.values():
        if abs(_length(a)-1)>1e-10:
            raise AssertionError('not unit')
    if abs(_dot(left,posterior))>1e-10 or abs(_dot(left,up))>1e-10 or abs(_dot(up,posterior))>1e-10:
        raise AssertionError('not orthogonal')
    handedness=_dot(_cross(left,posterior),up)
    if abs(handedness-1)>1e-9:
        raise AssertionError('not right handed')

    # Record pubic-left/right surface departure from the ideal APP normal:
    # 3-point APP uses the midpoint, 4-point anatomy is never perfectly coplanar.
    surface_spread_mm=abs(_dot(_sub(PL,PR),posterior))*1000
    return {'origin_asises_mid_m':asis,'pubic_tubercles_mid_m':pubic,
            'axis_world_unit':axes,
            'axis_handedness_determinant':handedness,
            'pubic_landmark_plane_normal_spread_mm':surface_spread_mm,
            'source_landmark_identity_verified':False,
            'canonical_promotion_allowed':False}


def world_to_app_delta_mm(frame,world_a,world_b):
    """Components of point a relative to b in an APP 3D anatomical basis."""
    a=_pt(world_a);b=_pt(world_b)
    d=_sub(a,b)
    return {k:1000*_dot(d,frame['axis_world_unit'][k])
            for k in ('left','posterior','superior')}


def _cohort_comparison(app_position,source):
    pelvic=next(s for s in source['source_landmarks'] if s['id']=='S1_HIP_IMAI_2019')
    m=pelvic['measurement']
    # Published DYp/DZp are APP-frame measures; we report sign-specific
    # model components, but do not assert source's coordinate axis
    # orientation/pelvic landmark identity verified.
    ap=app_position['posterior']
    up=app_position['superior']
    return {'model_APP_derived_posterior_component_mm':round(ap,3),
            'model_APP_derived_superior_component_mm':round(up,3),
            'model_APP_sagittal_length_mm':round(math.hypot(ap,up),3),
            'published_male_DYp_mm':m['male_dyp_mean_mm'],
            'published_male_DZp_mm':m['male_dzp_mean_mm'],
            'published_male_total_mm':m['male_total_mean_mm'],
            'published_spreads_two_sd':True,
            'absolute_or_sign_equivalence_established':False,
            'source_stature_compatible_with_model':False,
            'anatomical_target_selected':False}


def _check_evidence(provenance):
    """An external bony mesh + landmark extraction must be independently audited.

    These fields are descriptive, not cryptographic proof of biological
    correctness. Hashes protect identity but not scientific validity.
    """
    if not isinstance(provenance,dict):
        return ['no bone-landmark provenance record']
    reasons=[]
    for key in REQUIRED_BONY:
        x=provenance.get(key)
        if not isinstance(x,dict):
            reasons.append(f'{key}: no source evidence');continue
        if x.get('source_kind') != 'independently_segmented_bone_surface':
            reasons.append(f'{key}: skin or unsourced schematic coordinate')
        if x.get('feature_identity_verified') is not True:
            reasons.append(f'{key}: physical bony feature identity unverified')
        sha=x.get('source_asset_sha256','')
        if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
            reasons.append(f'{key}: source-asset content hash missing')
        if not isinstance(x.get('extraction_method'),str) or not x['extraction_method'].strip():
            reasons.append(f'{key}: extraction method undocumented')
    return reasons


def legacy_controls(candidate):
    """Expose, but NEVER approve, prior r95-skin/approximation endpoints."""
    s=candidate['landmarks_and_joint_centres']['sides']
    b=candidate['bones']
    return {'asis_left':s['left']['hip']['asis_skin']['value_m'],
            'asis_right':s['right']['hip']['asis_skin']['value_m'],
            'pubic_tubercle_left':s['left']['derived_points']['pubic_symphysis_side'],
            'pubic_tubercle_right':s['right']['derived_points']['pubic_symphysis_side'],
            's1_endplate_centre':b['sacrum']['tail_m'],
            'hip_centre_left':b['femur_left']['head_m'],
            'hip_centre_right':b['femur_right']['head_m']}


def _sensitivity(points,initial):
    """Demonstrate sensitivity of the LEGACY skin ASIS to its own ±20mm note."""
    rows=[]
    for key in ('asis_left','asis_right'):
        for axis in (1,2):
            for sign in (-1,1):
                x={k:list(v) for k,v in points.items()}
                x[key][axis]+=.02*sign
                try:
                    f=app_frame(x)
                except ValueError:
                    continue
                original=initial['axis_world_unit']['superior']
                vector=f['axis_world_unit']['superior']
                degrees=math.degrees(math.acos(max(-1,min(1,_dot(original,vector)))))
                hip=_mid(x['hip_centre_left'],x['hip_centre_right'])
                old=world_to_app_delta_mm(initial,x['s1_endplate_centre'],hip)
                new=world_to_app_delta_mm(f,x['s1_endplate_centre'],hip)
                rows.append({'moved_low_confidence_landmark':key,
                             'world_axis':'Y' if axis==1 else 'Z',
                             'perturbation_mm':20*sign,
                             'APP_superior_axis_change_deg':round(degrees,4),
                             'S1_posterior_component_change_mm':round(
                                  new['posterior']-old['posterior'],4)})
    return {'study_kind':'UNSOURCED_LEGACY_LANDMARK_SENSITIVITY_ONLY',
            'perturbation_mm':20,
            'number_of_scenarios':len(rows),
            'max_APP_axis_change_deg':max(x['APP_superior_axis_change_deg'] for x in rows),
            'max_abs_S1_AP_component_change_mm':max(abs(x['S1_posterior_component_change_mm']) for x in rows),
            'scenarios':rows}


def audit(points,source,provenance=None,legacy=False):
    if source.get('canonical_promotion_allowed') is not False:
        raise ValueError('source registry must not permit promotion')
    for key in REQUIRED_BONY:
        _pt(points[key],key)
    frame=app_frame(points)
    hip=_mid(points['hip_centre_left'],points['hip_centre_right'])
    delta=world_to_app_delta_mm(frame,points['s1_endplate_centre'],hip)
    blockers=_check_evidence(provenance)
    if legacy:
        blockers.insert(0,'legacy model ASIS from aesthetic skin inguinal groove (±20mm) and pubic symphysis control are NOT verified osseous ASIS/pubic tubercles')
    # Evidence metadata alone is NOT adequate to approve a frame until the
    # independent physical/clinical registration is reviewed.
    blocked=bool(blockers)
    return {'schema_version':1,
            'kind':'PELVIC_APP_BONE_FRAME_PREPRODUCTION_DIAGNOSTIC',
            'status':'LEGACY_SKIN_FRAME_REJECTED' if legacy else
                     'PROVENANCE_INCOMPLETE' if blocked else
                     'EVIDENCE_DECLARED_INDEPENDENT_REVIEW_REQUIRED',
            'APP':frame,'S1_relative_to_hip_in_APP_mm':
                {k:round(v,3) for k,v in delta.items()},
            'Imai_2019_APP_study_comparison':_cohort_comparison(delta,source),
            'evidence_blockers':blockers,
            'legacy_landmark_uncertainty_stress_test':_sensitivity(points,frame) if legacy else None,
            'APP_geometry_numerically_defined':True,
            'source_bone_surfaces_independently_validated':False,
            'world_to_study_cohort_endpoints_registered':False,
            'source_to_target_stature_transfer_validated':False,
            'canonical_promotion_allowed':False,
            'candidate_written':False,
            'muscles_mesh_or_rig_changed':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--legacy-record',type=Path)
    mode.add_argument('--bone-landmarks',type=Path)
    ap.add_argument('--source-registry',type=Path,required=True)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    src_bytes=args.source_registry.read_bytes()
    if args.legacy_record:
        record_bytes=args.legacy_record.read_bytes()
        record=json.loads(record_bytes)
        result=audit(legacy_controls(record),json.loads(src_bytes),legacy=True)
    else:
        record_bytes=args.bone_landmarks.read_bytes()
        data=json.loads(record_bytes)
        result=audit(data['points_m'],json.loads(src_bytes),
                     data.get('provenance'),legacy=False)
    result['input_sha256']={
        'model_or_landmarks':hashlib.sha256(record_bytes).hexdigest(),
        'source_registry':hashlib.sha256(src_bytes).hexdigest()}
    value=json.dumps(result,indent=2)+'\n'
    if args.out:
        with args.out.open('x',encoding='utf-8') as f:
            f.write(value)
    else:
        print(value,end='')


if __name__=='__main__':
    main()
