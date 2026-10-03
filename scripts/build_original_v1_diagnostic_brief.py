#!/usr/bin/env python3
"""Summarise measured Phase 3 probes without authorising edits or inferring causes."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from original_v1_production_control import ROOT,RC,build,digest,evidence,ensure_finite

TARGETS=(('pushup_bottom','hand','max'),('lunge','pelvis','max'),
         ('lunge','torso','min'),('lunge','torso','max'))


def number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('finite numeric measurement required')
    return value


def count(value):
    if type(value) is not int or value<0:raise ValueError('nonnegative integer ID/count required')
    return value


def vector(value):
    if not isinstance(value,list) or len(value)!=3:raise ValueError('three-coordinate vector required')
    return [number(v) for v in value]


def weights(rows):
    if not isinstance(rows,list) or not rows:raise ValueError('measured top weights required')
    names=[]
    for row in rows:
        if not isinstance(row['bone'],str) or not row['bone']:raise ValueError('bone name required')
        names.append(row['bone'])
        if not 0<number(row['weight'])<=1:raise ValueError('invalid top weight')
    if len(names)!=len(set(names)):raise ValueError('duplicate weight bones')


def summarize(grip,edges,primary,sha,script_sha,profile):
    try:return _summarize(grip,edges,primary,sha,script_sha,profile)
    except (KeyError,TypeError,IndexError,AttributeError) as exc:
        raise ValueError('incomplete or malformed diagnostic data: '+str(exc)) from exc


def _summarize(grip,edges,primary,sha,script_sha,profile):
    ensure_finite(grip);ensure_finite(edges);ensure_finite(primary)
    if any(d.get('schema_version')!=1 or d.get('source_candidate_sha256')!=sha for d in (grip,edges)):
        raise ValueError('diagnostic schema or candidate source differs')
    if grip.get('pose_script_sha256')!=script_sha:raise ValueError('grip probe uses a different pose script')
    gate=number(profile['grip_max_penetration_mm'])
    if grip.get('acceptance_gate_mm')!=gate:raise ValueError('probe gate differs from committed acceptance gate')
    poses={row['pose']:row for row in primary}
    if len(poses)!=len(primary):raise ValueError('duplicate primary poses')
    observations=[]
    for name in ('curl_handle','pullup_bar'):
        entry=grip['poses'][name]
        for side in 'lr':
            pre=entry['pre_close'][side];post=entry['post_close'][side]
            a=number(pre['max_penetration_mm']);b=number(post['max_penetration_mm'])
            if abs(b-number(poses[name]['grip_'+side]['max_penetration_mm']))>0.0051:
                raise ValueError('grip probe disagrees with primary rounded metrics: '+name+'/'+side)
            for sample in (pre,post):
                if number(sample['max_penetration_mm'])<0:raise ValueError('negative penetration')
                total=count(sample['finger_vertices'])
                if total==0 or any(count(sample[k])>total for k in ('inside_vertices','contact_vertices_within_2mm')):
                    raise ValueError('invalid sampled vertex counts')
                deepest=sample['deepest']
                if not isinstance(deepest,list) or not deepest:raise ValueError('deepest vertex evidence required')
                ids=[]
                for row in deepest:
                    ids.append(count(row['vertex']));vector(row['rest_position']);weights(row['top_weights'])
                    if not isinstance(row['region'],str) or not row['region']:raise ValueError('vertex region required')
                    if abs(max(0,-number(row['signed_distance_mm']))-number(row['penetration_mm']))>0.00011:
                        raise ValueError('signed distance/penetration mismatch')
                if len(ids)!=len(set(ids)) or abs(max(r['penetration_mm'] for r in deepest)-sample['max_penetration_mm'])>0.00011:
                    raise ValueError('deepest vertex evidence differs from maximum')
            handle=entry['handle'][side];axis=vector(handle['axis']);vector(handle['centre'])
            if abs(sum(x*x for x in axis)-1)>0.00001 or number(handle['radius_m'])<=0:
                raise ValueError('invalid measured handle frame')
            observations.append({'pose':name,'side':side,'pre_close_penetration_mm':a,'post_close_penetration_mm':b,
                'closing_delta_mm':round(b-a,4),'penetration_present_before_close':a>gate,
                'development_penetration_failed':b>gate,
                'post_close_contact_vertices':post['contact_vertices_within_2mm'],
                'development_contact_failed':post['contact_vertices_within_2mm']<profile['grip_min_contact_vertices_within_2mm'],
                'handle':handle,'pre_close_deepest':pre['deepest'],'post_close_deepest':post['deepest'],
                'next_inspection':'Inspect the listed thumb/finger points against the measured handle before editing. Pre-close penetration is an observation, not proof of a rig, weight or geometry cause.'})
    targets=edges['targets'];keys=[(t['pose'],t['region'],t['direction']) for t in targets]
    if len(keys)!=len(set(keys)) or set(keys)!=set(TARGETS):raise ValueError('missing/duplicate/unexpected edge targets')
    edge_observations=[]
    for key in TARGETS:
        target=targets[keys.index(key)];pose,region,direction=key;ratio=number(target['extreme_ratio'])
        if abs(ratio-number(poses[pose]['by_region'][region][direction+'_ratio']))>0.000501:
            raise ValueError('edge probe disagrees with primary rounded metrics: '+pose+'/'+region+'/'+direction)
        rows=target['edges'];total=count(target['edge_count_in_region'])
        if not isinstance(rows,list) or not rows or len(rows)>total:raise ValueError('extreme edge evidence required')
        ids=[];vertices=set()
        for row in rows:
            ids.append(count(row['edge_index']));count(row['rank'])
            pair=row['vertices']
            if not isinstance(pair,list) or len(pair)!=2 or pair[0]==pair[1]:raise ValueError('distinct edge vertex pair required')
            vertices.update(count(v) for v in pair)
            if number(row['ratio'])<0 or number(row['rest_length_m'])<0 or number(row['posed_length_m'])<0:
                raise ValueError('negative edge measurements')
            vector(row['rest_midpoint']);vector(row['posed_midpoint'])
            weights(row['vertex_a_weights']);weights(row['vertex_b_weights'])
            if row.get('mirror_edge_index') is not None:count(row['mirror_edge_index'])
            if row.get('mirror_ratio') is not None:number(row['mirror_ratio'])
        if len(ids)!=len(set(ids)) or ratio!=rows[0]['ratio']:
            raise ValueError('edge ordering/maximum evidence differs')
        limit=profile['region_min_ratio_min' if direction=='min' else 'region_max_ratio_max']
        edge_observations.append({'pose':pose,'region':region,'direction':direction,'extreme_ratio':ratio,
            'development_limit':limit,'development_failed':ratio<limit if direction=='min' else ratio>limit,
            'inspection_vertex_ids':sorted(vertices),'edges':rows,
            'work_package':'docs/work_packages/PHASE_3D_WRIST_PUSHUP.md' if pose=='pushup_bottom' else 'docs/work_packages/PHASE_3E_HIP_LUNGE.md'})
    return {'schema_version':1,'source_candidate_sha256':sha,'pose_script_sha256':script_sha,
        'grip_observations':observations,'edge_observations':edge_observations,
        'edit_authorised':False,'production_approved':False,'visual_review_available':False,
        'limits':['Inspection IDs are not an edit mask or correspondence proof.',
            'A single candidate probe cannot prove weight independence or distinguish rest/pose/frame/geometry causes.',
            'Development-clear edge rows can still contain strict active-epoch regressions; use the machine-selected immutable epoch baseline plus committed lineage comparisons.',
            'No model, weights, rig, poses, handle frames, baseline or thresholds are changed.']}


def markdown(result):
    lines=['# ORIGINAL v1 Phase 3 diagnostic brief','',
        'Candidate: '+result['candidate_revision']+' / `'+result['source_candidate_sha256']+'`','',
        'Evidence only. No edit is authorised. This brief contains no visual review images.','',
        '| Pose / side | Before close (mm) | After close (mm) | Closing delta (mm) | Contact vertices |',
        '|---|---:|---:|---:|---:|']
    for r in result['grip_observations']:
        lines.append(f"| {r['pose']} / {r['side']} | {r['pre_close_penetration_mm']} | {r['post_close_penetration_mm']} | {r['closing_delta_mm']} | {r['post_close_contact_vertices']} |")
    lines+=['','See JSON for exact pre/post deepest vertices, weights and measured handle frames.',
        'Pre-close penetration does not prove a causal diagnosis or permission to change a frozen structure.','']
    for r in result['edge_observations']:
        lines += [f"## {r['pose']} / {r['region']} / {r['direction']}",'',
            f"Measured ratio: {r['extreme_ratio']}; development limit: {r['development_limit']}; coarse failure: {r['development_failed']}.",
            'Inspection vertex IDs: '+', '.join(map(str,r['inspection_vertex_ids']))+'.',
            'Read `'+r['work_package']+'`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.','']
    baseline=result.get('active_epoch_baseline_revision','machine-selected active epoch baseline')
    lines += ['## Required continuation','',
        f'Preserve the active immutable stress-pose epoch baseline ({baseline}), direct-parent comparison and any specifically relevant committed historical controls. Do not hard-code R2/r28/r29 as current requirements. Run focused checks, full 15-pose evidence and mesh/weight audits for every NEW repair candidate. Publish actual review images; pending review does not stop safe work.','',
        'Source references:',*[f"- `{r['path']}` / `{r['sha256']}`" for r in result['source_evidence']], '',
        *['- '+s for s in result['limits']],'']
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('revision');args=ap.parse_args()
    try:
        state,_=build(ROOT)
        if args.revision!=state['current_candidate'] or state['candidate_state']=='rejected':raise ValueError('latest complete, non-rejected candidate required')
        folder=ROOT/RC/('remaining_diagnostics_'+args.revision)
        destinations=[folder/'diagnostic_brief.json',folder/'diagnostic_brief.md']
        if any(p.exists() for p in destinations):raise ValueError('diagnostic brief output already exists; preserve it')
        paths=[folder/'grip_penetration.json',folder/'edge_extremes.json']
        report=next(r['path'] for r in state['latest_evidence'] if r['path'].endswith('_merged_pose_report.json'))
        spec='ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json';script='scripts/pose_test_original_v1_o4_candidate_blender.py'
        result=summarize(*[json.loads(p.read_text(encoding='utf-8-sig')) for p in paths],
            json.loads((ROOT/report).read_text()),state['last_known_candidate_sha256'],digest(ROOT/script),
            json.loads((ROOT/spec).read_text())['profiles']['development_blocker'])
        result['candidate_revision']=args.revision
        result['active_epoch_baseline_revision']=state['pinned_baseline']['revision']
        result['active_epoch_baseline_candidate_sha256']=state['pinned_baseline'].get('candidate_sha256')
        result['source_evidence']=[evidence(ROOT,p.relative_to(ROOT).as_posix()) for p in paths]+[evidence(ROOT,p) for p in (report,spec,script)]
        destinations[0].write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        destinations[1].write_text(markdown(result),encoding='utf-8')
        print('DIAGNOSTIC BRIEF READY — evidence only, no edit authorisation');return 0
    except (OSError,ValueError,KeyError,TypeError,StopIteration) as exc:
        print('STOP — '+str(exc));return 1

if __name__=='__main__':raise SystemExit(main())
