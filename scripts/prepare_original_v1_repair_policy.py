#!/usr/bin/env python3
"""Prepare candidate-bound Phase 3 repair drafts; never derives edit permissions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from original_v1_production_control import ROOT,CAND,RC,build,digest,evidence
from build_original_v1_diagnostic_brief import summarize
from original_v1_locked_rig import load_locked_rig

PACKAGES={
    '3C':{'path':'docs/work_packages/PHASE_3C_GRIP_THUMB.md','region_envelope':['thumb','hand','finger'],
          'purpose':'Diagnose equipment penetration; independently author a minimal thumb/web repair only if measurements establish a mesh defect.',
          'focused_checks':['hand'],'forbidden':'No whole-hand remesh, blind weight solve, rig rest, handle frame/radius or frozen closing-pose edits.'},
    '3D':{'path':'docs/work_packages/PHASE_3D_WRIST_PUSHUP.md','region_envelope':['hand','arm'],
          'purpose':'Repair the local forearm/hand transition while retaining finger improvements and unchanged floor contact.',
          'focused_checks':['pushup','hand'],'forbidden':'No broad hand re-solve, finger/PIP changes, shoulder/body edits, floor or push-up pose changes.'},
    '3E':{'path':'docs/work_packages/PHASE_3E_HIP_LUNGE.md','region_envelope':['pelvis','torso','leg'],
          'purpose':'Repair the pelvis/upper-thigh/lower-torso transition for lunge without worsening squat or distant regions.',
          'focused_checks':['hip'],'forbidden':'No shoulders, arms/hands/feet, shorts, frozen rig rest, lunge/squat definitions or threshold changes.'}}


def verified_diagnostics(root,state,folder):
    paths=[folder/'grip_penetration.json',folder/'edge_extremes.json']
    report=next(ref['path'] for ref in state['latest_evidence'] if ref['path'].endswith('_merged_pose_report.json'))
    script='scripts/pose_test_original_v1_o4_candidate_blender.py';spec='ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json'
    result=summarize(*[json.loads(p.read_text(encoding='utf-8-sig')) for p in paths],
        json.loads((root/report).read_text()),state['last_known_candidate_sha256'],digest(root/script),
        json.loads((root/spec).read_text())['profiles']['development_blocker'])
    refs=[evidence(root,p.relative_to(root).as_posix()) for p in paths]+[evidence(root,p) for p in (report,script,spec)]
    return result,refs


def prepare(root,phase,state):
    if phase not in PACKAGES:raise ValueError('supported repair packages are 3C, 3D and 3E')
    if state['candidate_state']=='rejected':raise ValueError('cannot prepare edits on a rejected candidate')
    package=PACKAGES[phase];rev=state['current_candidate'];sha=state['last_known_candidate_sha256']
    baseline=state.get('pinned_baseline') or {}
    baseline_revision=baseline.get('revision') or 'machine-selected active epoch baseline'
    rig_contract=load_locked_rig(root)
    manifest=f'{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json'
    if json.loads((root/manifest).read_text(encoding='utf-8-sig')).get('candidate_sha256')!=sha:
        raise ValueError('parent manifest differs from current evidence')
    refs=[evidence(root,p) for p in (manifest,'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json','ORIGINAL_V1_PRODUCTION_CONTROL.json')]
    for ref in state['latest_evidence']:
        if digest(root/ref['path'])!=ref['sha256']:raise ValueError('current evidence changed: '+ref['path'])
        refs.append(ref)
    context={'schema_version':1,'phase':phase,'candidate_revision':rev,'source_candidate_sha256':sha,
        'diagnostics_state':'AWAITING_PROBES','inspection_vertex_ids':[],'observations':[],
        'edit_authorised':False,'production_approved':False,
        'active_epoch_baseline':baseline,
        'locked_rig':{'revision':rig_contract['revision'],'rig_structure_sha256':rig_contract['rig_structure_sha256'],
            'bone_count':rig_contract['bone_count'],'deform_bone_count':rig_contract['deform_bone_count'],
            'lock':rig_contract['lock'],'payload':rig_contract['payload']},
        'note':'Inspection IDs never become allowed IDs automatically. No candidate-specific mask exists until an author records the local scope.'}
    folder=root/RC/('remaining_diagnostics_'+rev)
    available=[(folder/name).is_file() for name in ('grip_penetration.json','edge_extremes.json')]
    if any(available) and not all(available):raise ValueError('partial diagnostic pair; preserve and reconcile it')
    if all(available):
        summary,diagnostic_refs=verified_diagnostics(root,state,folder);refs+=diagnostic_refs
        observations=summary['grip_observations'] if phase=='3C' else [r for r in summary['edge_observations'] if (r['pose']=='pushup_bottom')==(phase=='3D')]
        ids={r['vertex'] for row in observations for key in ('pre_close_deepest','post_close_deepest') for r in row.get(key,[])}
        ids|={v for row in observations for v in row.get('inspection_vertex_ids',[])}
        context.update(diagnostics_state='VERIFIED_PROBES',inspection_vertex_ids=sorted(ids),observations=observations)
    unique={ref['path']:ref for ref in refs};refs=[unique[p] for p in sorted(unique)]
    context['source_evidence']=refs
    policy={'schema_version':1,'state':'INCOMPLETE','phase':phase,
        'before_candidate_sha256':sha,'candidate_sha256':None,
        'allowed_regions':[],'allowed_vertex_ids':[],'allowed_bones':[],
        'index_correspondence_confirmed':False,'change_epsilon':1e-8,
        'normalization_tolerance':1e-6,'max_influences':4,'production_approved':False,
        'note':'Draft only. Empty lists permit no changes; unknown child SHA prevents an audit. Fill a new policy copy after explicit local scope and actual operation/correspondence evidence.'}
    intent={'schema_version':1,'state':'DRAFT','phase':phase,'parent_candidate':rev,
        'before_candidate_sha256':sha,'child_candidate':None,'candidate_sha256':None,
        'work_package':package['path'],'purpose':package['purpose'],
        'change_type':None,'local_defect_description':None,'planned_operations':[],
        'permitted_vertex_ids':[],'allowed_regions':[],'allowed_bones':[],
        'mask_basis_evidence':[],'symmetry_plan':None,'index_correspondence_basis':None,
        'frozen_constraints':[f'active immutable stress-pose epoch baseline: {baseline_revision}',
            f"locked rev2c rig: {rig_contract['revision']} / {rig_contract['bone_count']} bones",
            'all historical epoch baselines remain immutable','acceptance thresholds',
            'stress poses','equipment handle frames','first-party provenance'],
        'source_evidence':refs,'production_approved':False,
        'note':'Record a pre-edit intent before any candidate edit. Preserve it and append actual operation evidence; do not retrospectively broaden the mask to hide changes.'}
    readme=f"""# Phase {phase} repair preparation — {rev}

Parent SHA-256: `{sha}`. PREPARATION ONLY; no edit is authorised by these drafts.
Read `{package['path']}` and run the next-action selector first. Hand recovery
precedes these repairs. If a newer continuation candidate exists, regenerate into
a NEW folder for that candidate; do not relabel this parent-bound packet.

## Before editing

1. Check LIVE branch, preflight and the latest complete candidate. Preserve newer work.
2. Run remaining diagnostics on the appropriate continuation candidate; read the
   brief and raw points/weights. This packet's diagnostic state is
   **{context['diagnostics_state']}**. Missing probes are not a diagnosis.
3. Export the parent's raw schema-2 snapshot using the existing snapshot exporter.
   Inspect the measured defect in Blender. Inspection IDs are not permission lists;
   select the minimal local scope and verify actual region membership and symmetry.
   Region envelope: {', '.join(package['region_envelope'])}. This does not permit a
   whole-region edit. {package['forbidden']}
4. Copy `edit_intent_template.json` to a fresh operation-record path. Record explicit
   vertex IDs, regions, bones, mask evidence, intended operation and symmetry plan.
   Keep the original template unchanged. Freeze this intent before editing.
5. Work only on a NEW experimental candidate. Do not modify the source Blend.

## After the local experiment

Record child revision/hash and actual operations in a new operation record linked
to the pre-edit intent. Export a fresh child snapshot. Copy the audit policy to a
NEW file and bind both actual candidate hashes and the SAME intended scope.
Confirm index correspondence from operation history, never equal counts alone.
If topology/order changed, preserve that evidence; numerical deltas cannot be
claimed without separately authored correspondence. Do not widen permissions after
seeing unexpected changes; reject or diagnose the experiment instead.

Use the existing commands, with fresh snapshot/policy/output paths:

```bat
blender --background --factory-startup <verified parent.blend> --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- <new before.json>
blender --background --factory-startup <verified child.blend> --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- <new after.json>
python scripts/audit_original_v1_changes.py <before.json> <after.json> --policy <completed policy.json> --json-out <new audit.json>
```

An audit being written is not a gate PASS. Inspect unexpected vertices/bones,
normalisation, influences, cross-side weights, symmetry and topology/correspondence.
Run focused groups **{', '.join(package['focused_checks'])}**, then full 15-pose
evidence and the active immutable epoch-baseline/direct-parent comparisons plus only specifically relevant historical controls. Do not hard-code R2/r28/r29 as current requirements. Follow the package's exact gates
and renders. Publish actual review images and record pending NON-BLOCKING review;
continue safe work. Preserve rejected experiments and all their evidence.

The preparation manifest hashes the original templates and source context. It is
not a model candidate manifest or an approval record. No Blender work was run.
"""
    return {'audit_policy_template.json':policy,'edit_intent_template.json':intent,
        'inspection_context.json':context,'README.md':readme}


def publish(root,folder,files):
    root=root.resolve();folder=folder.resolve()
    if not folder.is_relative_to(root) or folder==root:raise ValueError('output folder must be inside repository')
    if folder.exists():raise ValueError('output folder already exists; preserve previous preparation')
    folder.mkdir(parents=True)
    for name,content in files.items():
        (folder/name).write_text(content if isinstance(content,str) else json.dumps(content,indent=2)+'\n',encoding='utf-8')
    context=files['inspection_context.json']
    receipt={'schema_version':1,'state':'PREPARATION_ONLY','phase':context['phase'],
        'parent_candidate':context['candidate_revision'],'before_candidate_sha256':context['source_candidate_sha256'],
        'diagnostics_state':context['diagnostics_state'],'source_evidence':context['source_evidence'],
        'outputs':[evidence(root,(folder/name).relative_to(root).as_posix()) for name in sorted(files)],
        'edit_authorised':False,'production_approved':False}
    (folder/'preparation_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('phase',choices=sorted(PACKAGES))
    ap.add_argument('--out-dir',required=True,type=Path);args=ap.parse_args()
    try:
        state,_=build(ROOT);publish(ROOT,args.out_dir,prepare(ROOT,args.phase,state))
        print('REPAIR DRAFTS PREPARED — empty permissions, no edit or approval');return 0
    except (OSError,ValueError,KeyError,TypeError,StopIteration) as exc:
        print('STOP — '+str(exc));return 1

if __name__=='__main__':raise SystemExit(main())
