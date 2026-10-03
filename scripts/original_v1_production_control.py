"""Evidence-led ORIGINAL-v1 state, shared by dashboard, selector and preflight.

Standard library plus existing project-owned evaluators. Never writes assets,
changes gates, promotes candidates or silently substitutes the pinned baseline.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
from pathlib import Path
import evaluate_original_v1_deformation_report as deval
import compare_original_v1_deformation_reports as comparator

ROOT = Path(__file__).resolve().parents[1]
CAND = 'ORIGINAL_V1_WORK/candidates'
RC = CAND + '/repair_checks'


def read(root, path):
    return json.loads((root / path).read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def evidence(root, path):
    return {'path':path, 'sha256':digest(root/path)}


def revision_key(rev):
    m = re.fullmatch(r'r(\d+)(.*)', rev)
    return (int(m[1]), m[2]) if m else (-1, rev)


def candidate_lineage(entries, current_revision):
    """Return current->ancestor candidate rows using exact parent SHA identity.

    Multiple revision labels may legitimately identify identical candidate bytes in
    historical/synthetic evidence. They are one asset identity when their declared
    parent SHA is consistent. Conflicting parent identities remain fail-closed.
    """
    if current_revision not in entries:
        raise ValueError("current candidate missing from lineage map")
    by_sha = {}
    for revision, row in entries.items():
        sha = row.get("sha256")
        if isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha):
            by_sha.setdefault(sha, []).append(row)
    for sha, rows in by_sha.items():
        parents = {row.get("parent_sha256") for row in rows if row.get("parent_sha256")}
        if len(parents) > 1:
            raise ValueError("identical candidate SHA has conflicting parent lineage")

    chain = []
    seen = set()
    row = entries[current_revision]
    while row:
        sha = row.get("sha256")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("invalid candidate SHA in lineage")
        if sha in seen:
            raise ValueError("candidate lineage cycle")
        seen.add(sha)
        chain.append(row)
        parent_sha = row.get("parent_sha256")
        if not parent_sha:
            break
        parents = by_sha.get(parent_sha)
        if not parents:
            # Parent may be the non-candidate original source. Never infer a candidate
            # ancestor from a filename or revision number when its SHA is unavailable.
            break
        # All rows sharing this SHA have already been proven to agree on parent SHA.
        # Prefer the newest revision label only for deterministic reporting.
        row = max(parents, key=lambda x: revision_key(x.get("revision", "")))
    return chain


def phase_checkpoint_on_lineage(entries, current_revision, checkpoint_sha):
    if not isinstance(checkpoint_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", checkpoint_sha):
        raise ValueError("phase completion candidate SHA invalid")
    lineage = candidate_lineage(entries, current_revision)
    for depth, row in enumerate(lineage):
        if row["sha256"] == checkpoint_sha:
            return {"revision": row["revision"], "sha256": checkpoint_sha, "depth": depth}
    raise ValueError("phase completion candidate is not on current candidate lineage")


def ensure_finite(value):
    if isinstance(value, float) and not math.isfinite(value): raise ValueError('non-finite evidence')
    if isinstance(value, dict):
        for v in value.values(): ensure_finite(v)
    if isinstance(value, list):
        for v in value: ensure_finite(v)


def evaluate(root, path, profile='development_blocker', historical=False):
    report = read(root,path); ensure_finite(report)
    spec = read(root,'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json')
    required = {'neutral'} | set().union(*map(set,spec['required_pose_groups'].values()))
    poses = [x['pose'] for x in report]
    if (not historical and set(poses) != required) or len(poses) != len(set(poses)) or not set(poses).issubset(required):
        raise ValueError(f'{path}: incomplete/duplicate pose coverage')
    # Existing evaluator treats absent grip rows as optional: full control requires them.
    for pose in ('curl_handle','pullup_bar'):
        row = next(x for x in report if x['pose']==pose)
        if not all(isinstance(row.get('grip_'+side),dict) for side in ('l','r')):
            raise ValueError(f'{path}: missing bilateral equipment grip coverage')
    return deval.make_summary(report,report,spec,profile,'core_five')


def verify_comparison(root, path, base_path, candidate_path, historical=False):
    committed = read(root,path)
    spec = read(root,'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json')
    limits = spec['profiles']['development_blocker']; tol = spec['comparison_tolerances']
    base, cand = read(root,base_path), read(root,candidate_path)
    selected = committed.get('selected_poses')
    if selected:
        if not historical and set(selected) != {x['pose'] for x in base}:
            raise ValueError(f'comparison {path} has partial coverage')
        base = [x for x in base if x['pose'] in selected]
        cand = [x for x in cand if x['pose'] in selected]
    bp, cp = comparator.pose_failure_counts(base,limits), comparator.pose_failure_counts(cand,limits)
    bg, cg = comparator.grip_failure_counts(base,limits), comparator.grip_failure_counts(cand,limits)
    pr, pi = comparator.compare_pose_severity(base,cand,tol)
    gr, gi = comparator.compare_grip_severity(base,cand,tol)
    regressions = comparator.compare_counts(bp,cp,'pose') + comparator.compare_counts(bg,cg,'grip') + pr + gr
    improvements = pi + gi
    count = sum(cp.values())+sum(cg.values())
    before = sum(bp.values())+sum(bg.values())
    expected = {'baseline_failed_checks':before,'candidate_failed_checks':count,
                'regression_count':len(regressions),'improvement_count':len(improvements),
                'status':'REGRESSION' if regressions else ('IMPROVED' if count < before or improvements else 'UNCHANGED')}
    if any(committed.get(k)!=v for k,v in expected.items()) or committed.get('comparison_tolerances')!=tol:
        raise ValueError(f'comparison {path} disagrees with recomputed evidence')
    if committed.get('regressions') != regressions or committed.get('improvements') != improvements:
        raise ValueError(f'comparison {path} disagrees with detailed metrics')
    return {**expected,'evidence':evidence(root,path),'regressions':regressions}


def verify_full_receipt(root, rev):
    """Verify committed numeric source lineage; actual PNG bytes have a separate audit.

    Every source report and render manifest must be committed. Full-resolution PNGs
    may stay on the laptop; the compact review collector verifies their bytes there.
    Historical pre-r30 evidence is preserved without retroactive invented receipts.
    """
    from merge_original_v1_repair_group_reports import GROUP_POSES
    path=f'{RC}/full_{rev}_evidence_manifest.json'
    try:
        receipt=read(root,path)
        man_path=f'{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.json'
        man=read(root,man_path)
        merged_path=f'{RC}/full_{rev}_merged_pose_report.json'
        if (receipt.get('schema_version')!=1 or receipt.get('candidate_revision')!=rev or
            receipt.get('candidate_sha256')!=man['candidate_sha256'] or
            receipt.get('candidate_manifest_sha256')!=digest(root/man_path) or
            receipt.get('production_approved') is not False):
            raise ValueError('source receipt candidate identity/schema differs: '+rev)
        script_sha=receipt.get('render_script_sha256','')
        if not re.fullmatch('[0-9a-f]{64}',script_sha):raise ValueError('source receipt script identity missing')
        if receipt.get('merged_pose_report_sha256')!=digest(root/merged_path):
            raise ValueError('source receipt merged report hash differs')
        groups=receipt['groups'];names=[x['group'] for x in groups]
        if len(names)!=len(set(names)) or set(names)!=set(GROUP_POSES):
            raise ValueError('source receipt requires all six groups')
        rows={}
        for row in groups:
            group=row['group']
            report_path=f'{RC}/{group}_{rev}/pose_test_report.json'
            source_path=f'{RC}/{group}_{rev}/render_source_manifest.json'
            if row['pose_report']!=report_path or row['render_source_manifest']!=source_path:
                raise ValueError('source receipt group paths differ')
            if (row['pose_report_sha256']!=digest(root/report_path) or
                row['render_source_manifest_sha256']!=digest(root/source_path)):
                raise ValueError('source receipt group hash differs: '+group)
            source=read(root,source_path)
            if (source.get('candidate_sha256')!=man['candidate_sha256'] or
                source.get('render_script_sha256')!=script_sha or
                source.get('pose_report_sha256')!=row['pose_report_sha256'] or
                not source.get('blender_version')):
                raise ValueError('source receipt capture identity differs: '+group)
            report=read(root,report_path);ensure_finite(report)
            poses=[x['pose'] for x in report]
            if len(poses)!=len(set(poses)) or set(poses)!=set(GROUP_POSES[group]):
                raise ValueError('source receipt group pose coverage differs: '+group)
            for pose in report:
                name=pose['pose']
                if name in rows and rows[name]!=pose:raise ValueError('source receipt overlapping metrics differ: '+name)
                rows[name]=pose
        order=[x['pose'] for x in read(root,f'{CAND}/pose_test_report_r2.json')]
        if set(rows)!=set(order) or receipt.get('pose_count')!=len(order):
            raise ValueError('source receipt full coverage differs')
        if [rows[name] for name in order]!=read(root,merged_path):
            raise ValueError('source receipt merged metrics differ from original groups')
        return evidence(root,path)
    except (OSError,KeyError,TypeError) as exc:
        raise ValueError('source receipt missing/incomplete for '+rev+': '+str(exc)) from exc


def verified_review(root, revision, candidate_sha, kind):
    """Verify published images and small original capture manifests, not raw render folders."""
    path=f'{CAND}/review/{kind}_{revision}/visual_review_manifest.json'
    if not (root/path).exists():return None
    packet=read(root,path)
    man=f'{CAND}/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.json'
    if (packet.get('candidate_revision')!=revision or packet.get('candidate_sha256')!=candidate_sha or
        packet.get('candidate_manifest_sha256')!=digest(root/man) or
        packet.get('production_approved') is not False or packet.get('blocking') is not False):
        raise ValueError('review identity/non-blocking contract differs: '+path)
    folder=(root/path).parent.resolve();names=set();sources={}
    for reference in packet['source_manifests']:
        target=(root/reference['path']).resolve()
        if not target.is_relative_to((root/RC).resolve()) or digest(target)!=reference['sha256']:
            raise ValueError('review source manifest hash/path differs')
        capture=read(root,reference['path'])
        if capture.get('candidate_sha256')!=candidate_sha:raise ValueError('review capture candidate differs')
        for image in capture['images']:
            sources.setdefault(image['file'],[]).append(image)
    for row in packet['files']:
        image=(root/row['output']).resolve()
        if not image.is_relative_to(folder) or image.name in names or digest(image)!=row['sha256']:
            raise ValueError('review published image hash/path differs')
        names.add(image.name)
        source_name=Path(row.get('source',row.get('file',image.name))).name
        if not any(x['sha256']==row['sha256'] and x.get('capture')==row.get('capture') for x in sources.get(source_name,[])):
            raise ValueError('review image differs from original capture manifest')
    if not names:raise ValueError('review has no actual published images')
    result={'checkpoint':f'{revision} {kind} snapshot','owner_review':'pending','blocking':False,
            'candidate_sha256':candidate_sha,'evidence':evidence(root,path)}
    index=(root/path).parent/'README.md'
    if index.exists():result['review_index']=index.relative_to(root).as_posix()
    return result


def next_action(status, control):
    incomplete = status['incomplete_candidates']
    if incomplete:
        return {'action':'STOP','reason':'new candidate evidence is incomplete: '+', '.join(incomplete),
                'command':None,'safe_parallel_task':'Inspect partial files read-only; preserve them and finish their evidence using a new collision-free label.'}
    rev = status['current_candidate']
    if status['candidate_state']=='rejected':
        return {'action':'STOP','reason':'current candidate is rejected; resolve valid parent lineage','command':None}
    if rev == 'r29':
        return {'action':'RUN r30','reason':'authorised finger-minimum recovery, preserving curl_peak clearance',
                'command':'RUN_ORIGINAL_V1_R30.bat','execution_parent':'r29'}
    diagnostics = f'{RC}/remaining_diagnostics_{rev}'
    refs = {x['path'] for x in status['latest_evidence']}
    if not all(diagnostics+'/'+name in refs for name in ('edge_extremes.json','grip_penetration.json')):
        return {'action':'RUN remaining diagnostics','reason':'isolate wrist/grip/lunge locally before editing',
                'command':f'RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat {rev}'}
    decision = control.get('continuation_decisions',{}).get(rev)
    if not decision or decision.get('candidate_sha256')!=status['last_known_candidate_sha256']:
        return {'action':'RECONCILE trial lineage','reason':'record evidence-backed continuation choice; a trade-off is not auto-promoted',
                'command':None,'safe_parallel_task':'Read-only analysis and review collection; compare the active epoch baseline and all declared predecessors.'}
    active = control.get('active_local_repair')
    if isinstance(active,dict) and active.get('candidate_revision')==rev and active.get('candidate_sha256')==status['last_known_candidate_sha256']:
        return {'action':active['action'],'reason':active['reason'],'command':active.get('command'),
                'work_package':active.get('work_package'),'safe_parallel_task':active.get('safe_parallel_task')}
    phases = status['phases']
    for phase, action, package in [('3B','REPAIR hands/fingers','PHASE_3B_HANDS.md'),
                                   ('3D','REPAIR wrist','PHASE_3D_WRIST_PUSHUP.md'),
                                   ('3C','REPAIR grip/thumb','PHASE_3C_GRIP_THUMB.md'),
                                   ('3E','REPAIR lunge','PHASE_3E_HIP_LUNGE.md')]:
        if phases[phase]['state'] in ('active','blocked','refinement'):
            return {'action':action,'reason':phases[phase]['reason'],'command':None,
                    'work_package':'docs/work_packages/'+package}
    if status['development_failure_count']:
        return {'action':'STOP','reason':'unmapped development blockers','command':None}
    if status['unresolved_regressions']:
        return {'action':'RECONCILE freeze regressions','reason':'zero blockers is insufficient for strict freeze; unresolved strict active-epoch regressions remain',
                'command':None,'safe_parallel_task':'Read-only active-epoch regression diagnostics; do not reopen frozen structure.'}
    if phases['4']['state']!='complete':
        return {'action':'ENTER development freeze validation','reason':'zero blockers and no unresolved strict regressions','command':None,
                'work_package':'docs/work_packages/PHASE_4_DEVELOPMENT_FREEZE.md'}
    if phases['5']['state']!='complete':
        for region in ('5A','5B','5C','5D','5E','5F','5G'):
            if phases[region]['state']!='complete':
                return {'action':f'EXECUTE Phase {region} anatomy',
                        'reason':'development freeze recorded; execute the next unverified anatomy region in order',
                        'command':f'RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat --template {region} <fresh-template.json>',
                        'work_package':phases[region].get('work_package'),
                        'review_command':f'RUN_ORIGINAL_V1_PHASE5_REGION_REVIEW.bat {region} <candidate-rN>'}
        return {'action':'VERIFY Phase 5 exit',
                'reason':'all 5A-5G regional evidence records are verified; Phase 5 exit packet is still required',
                'command':'python scripts/verify_original_v1_phase_exit.py --phase 5 --template --json-out <fresh-template.json>',
                'work_package':'docs/work_packages/PHASE_5_ANATOMY_EXECUTION_PROTOCOL.md'}
    for n in range(6,13):
        if phases[str(n)]['state']!='complete':
            return {'action':f'ENTER Phase {n} validation','reason':'ordered phase dependencies satisfied','command':None}
    return {'action':'VERIFY production promotion packet','reason':'final separate owner and release gates required','command':None}


def epoch_baseline(root, rev):
    """(baseline name, pose-report path) of the stress-pose epoch that candidate `rev` belongs to."""
    try:
        control = read(root,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
    except FileNotFoundError:           # evidence-only roots without the control file use the historical R2 epoch
        return 'R2', CAND+'/pose_test_report_r2.json'
    epochs = control.get('baseline_epochs') or [{'name':'R2','baseline':CAND+'/DEFORMATION_BASELINE_R2.json','first_rev':0}]
    ep = max((e for e in epochs if e['first_rev']<=revision_key(rev)[0]),key=lambda e:e['first_rev'])
    return ep['name'], read(root,ep['baseline'])['inputs']['pose_report']['path']


def build(root=ROOT):
    control = read(root,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
    for path, sha in control['frozen_inputs'].items():
        if digest(root/path)!=sha: raise ValueError('frozen input changed: '+path)
    pose_pin = control.get('frozen_pose_definition')
    if pose_pin:
        prefix=(root/pose_pin['path']).read_text(encoding='utf-8').split('# ---------------------------------------------------------------- metrics',1)[0].replace('import hashlib\n','')
        if hashlib.sha256(prefix.encode()).hexdigest()!=pose_pin['sha256']:
            raise ValueError('frozen stress-pose definition changed')
        for hist in control.get('pose_definition_history',[]):
            hp=(root/hist['path']).read_text(encoding='utf-8').split('# ---------------------------------------------------------------- metrics',1)[0].replace('import hashlib\n','')
            if hashlib.sha256(hp.encode()).hexdigest()!=hist['sha256']:
                raise ValueError('historical stress-pose definition changed: '+hist['revision'])
    baseline = read(root,CAND+'/DEFORMATION_BASELINE_R2.json')
    baseline_path = baseline['inputs']['pose_report']['path']
    base_eval = evaluate(root,baseline_path)
    if base_eval['failure_count']!=baseline['evaluation']['development_blocker_failed_checks']:
        raise ValueError('pinned baseline count changed')
    # Baseline EPOCHS: each stress-pose definition revision has its own pinned baseline (R2 = P1 era r1..r38; P2B1 = P2 era).
    epochs = control.get('baseline_epochs') or [{'name':'R2','baseline':CAND+'/DEFORMATION_BASELINE_R2.json','first_rev':0}]
    bases = {}
    for ep in epochs:
        b = baseline if ep['name']=='R2' else read(root,ep['baseline'])
        bp = b['inputs']['pose_report']['path']
        ev0 = base_eval if ep['name']=='R2' else evaluate(root,bp)
        if ev0['failure_count']!=b['evaluation']['development_blocker_failed_checks']:
            raise ValueError('pinned baseline count changed: '+ep['name'])
        bases[ep['name']] = {'baseline':b,'path':bp,'first_rev':ep['first_rev'],'file':ep['baseline'],'eval':ev0}
    def pin_of(rev_):
        return max((n for n in bases if bases[n]['first_rev']<=revision_key(rev_)[0]),key=lambda n:bases[n]['first_rev'])
    old_path = root/'ORIGINAL_V1_CANDIDATE_LEDGER.json'
    old = json.loads(old_path.read_text()) if old_path.exists() else {'candidates':[]}
    historic = {x['revision']:x for x in old['candidates']}
    entries = dict(historic); complete = []; incomplete = []; observed = set()
    for manifest in sorted((root/CAND).glob('HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r*.json')):
        rev = manifest.stem.split('_CANDIDATE_',1)[1]
        observed.add(rev)
        man = json.loads(manifest.read_text(encoding='utf-8-sig'))
        sha = man['candidate_sha256']
        if not re.fullmatch('[0-9a-f]{64}',sha): raise ValueError('invalid candidate hash: '+rev)
        previous = historic.get(rev,{})
        if previous.get('sha256') and previous['sha256']!=sha: raise ValueError('candidate identity replaced: '+rev)
        report_path = f'{RC}/full_{rev}_merged_pose_report.json'
        comparisons = {}
        report = root/report_path
        eval_result = None
        receipt_ref = None
        if report.exists():
            if revision_key(rev)[0]>=30:
                receipt_ref=verify_full_receipt(root,rev)
            eval_result = evaluate(root,report_path,historical=(rev=='r20'))
            paths = sorted((root/RC).glob(f'full_{rev}_comparison_vs_*.json'))
            for p in paths:
                name = p.stem.split('_comparison_vs_',1)[1]
                bpath = bases[name]['path'] if name in bases else f'{RC}/full_{name}_merged_pose_report.json'
                if not (root/bpath).exists(): raise ValueError('missing comparison predecessor: '+bpath)
                comparisons[name] = verify_comparison(root,p.relative_to(root).as_posix(),bpath,report_path,historical=(rev=='r20'))
            pin = pin_of(rev)
            if pin not in comparisons: raise ValueError('missing '+pin+' comparison: '+rev)
            if eval_result['failure_count']!=comparisons[pin]['candidate_failed_checks']:
                raise ValueError('comparison count disagrees: '+rev)
            if rev=='r30' and not {'r29','r28'}.issubset(comparisons):
                incomplete.append(rev)
            elif rev != 'r20': complete.append(rev)
        topology = man.get('topology_changed')
        if topology is None and man.get('solution'): topology = False  # weight-only apply script
        disposition = previous.get('state','experimental')
        reason = previous.get('reason','Experimental evidence only; owner acceptance not recorded.')
        if rev in control['historical_dispositions']['rejected']:
            disposition='rejected'; reason=control['historical_dispositions']['reason']
        pin = pin_of(rev)
        predecessors = [x for name,x in comparisons.items() if name not in bases]
        classification = ('TRADE-OFF' if any(x['regression_count'] for x in predecessors)
                          else 'STRICT IMPROVEMENT' if predecessors and any(x['improvement_count'] or x['candidate_failed_checks']<x['baseline_failed_checks'] for x in predecessors)
                          else 'EXPERIMENTAL')
        entries[rev] = {'revision':rev,'sha256':sha,'parent':man.get('source_candidate'),
            'parent_sha256':man.get('source_sha256'),'change_type':man.get('stage'),
            'weight_solution':man.get('solution'),'weight_solution_sha256':man.get('solution_sha256'),
            'topology_change':topology,'development_failure_count':eval_result['failure_count'] if eval_result else None,
            'regression_count':comparisons.get(pin,{}).get('regression_count'),
            'improvement_count':comparisons.get(pin,{}).get('improvement_count'),
            'pinned_baseline_name':pin,
            'comparison_baselines':list(comparisons),'comparisons':comparisons,'classification':classification,
            'state':disposition,'reason':reason,'owner_review':previous.get('owner_review','pending'),
            'evidence_location':report_path if report.exists() else None,
            'manifest':evidence(root,manifest.relative_to(root).as_posix()),
            'visual_review_location': f'{CAND}/review/visual_{rev}/visual_review_manifest.json' if (root/f'{CAND}/review/visual_{rev}/visual_review_manifest.json').exists() else None,
            'evidence_timestamp':man.get('generated_utc')}
        if receipt_ref: entries[rev]['full_evidence_receipt']=receipt_ref
    if not complete: raise ValueError('no complete experimental candidate evidence')
    rev = max(complete,key=revision_key); current=entries[rev]
    # Any later manifest or report/solution is partial until full evidence verifies.
    for r in entries:
        if revision_key(r)[0]>revision_key(rev)[0] and r in observed and r not in incomplete: incomplete.append(r)
    planned=control['planned_experiment']['revision']
    if planned not in complete and ((root/f'{CAND}/weight_solutions/{control["planned_experiment"]["solution"]}').exists() or
         (root/f'{RC}/full_{planned}_merged_pose_report.json').exists()):
        if planned not in incomplete: incomplete.append(planned)
    ev = evaluate(root,current['evidence_location']); fails=ev['failures']
    r2cmp=current['comparisons'][current['pinned_baseline_name']]; regs=r2cmp['regressions']
    foundation=read(root,'ORIGINAL_V1_CANDIDATE_STATUS.json')['gates']
    prov=read(root,'ORIGINAL_V1_WORK/ORIGINAL_V1_PROVENANCE.json')
    if not prov.get('clean_room') or prov.get('starting_geometry')!='blank' or prov.get('legacy_geometry_imported') is not False:
        raise ValueError('foundation provenance conflict')
    phases={}
    checks=[('0','o1_clean_scaffold_provenance',{'verified'}),('1','o2_neutral_numeric',{'passed'}),('2','canonical_v4_structure',{'verified_candidate'})]
    for phase,gate,allowed in checks:
        phases[phase]={'state':'complete' if foundation[gate]['status'] in allowed else 'blocked',
                       'reason':'Verified foundation checkpoint; visual acceptance tracked separately.',
                       'evidence_source':'ORIGINAL_V1_CANDIDATE_STATUS.json#'+gate}
    shoulder_poses=set(read(root,'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json')['repair_priority'][0]['poses'])
    shoulders=[f for f in fails if f['pose'] in shoulder_poses and f.get('region') not in ('hand','finger','thumb','grip_l','grip_r')]
    hand=[f for f in fails if f.get('region') in ('hand','finger','thumb') or f['pose'] in ('curl_peak','grip')]
    hand_reg=[r for name,c in current['comparisons'].items() if name not in bases for r in c['regressions'] if r.get('region') in ('finger','thumb')]
    grip=[f for f in fails if str(f.get('region','')).startswith('grip_')]
    wrist=[r for r in regs if r['name']=='pushup_bottom' and r.get('region')=='hand']
    hip=[f for f in fails if f['pose'] in ('lunge','squat_bottom') and f.get('region') in ('pelvis','torso','leg')]
    phases['3']={'state':'active','reason':'Core deformation foundation still under repair.'}
    phases['3A']={'state':'blocked' if shoulders else 'complete','reason':'Development clear; active-epoch severity regressions remain separate.'}
    phases['3B']={'state':'active' if hand or hand_reg or rev=='r29' else 'complete','reason':'Recover finger minima without losing curl_peak clearance.'}
    phases['3C']={'state':'blocked' if grip else 'complete','reason':'Bilateral equipment penetration must satisfy unchanged gates.'}
    phases['3D']={'state':'refinement' if wrist else 'blocked' if any(f['pose']=='pushup_bottom' for f in fails) else 'complete','reason':'Local wrist-extension severity regression versus the active epoch baseline.'}
    phases['3E']={'state':'blocked' if hip else 'complete','reason':'Lunge pelvis/torso collapse and stretch; repair local hip transition.'}
    if not fails and not regs and all(phases[p]['state']=='complete' for p in ('3A','3B','3C','3D','3E')):
        phases['3']={'state':'complete','reason':'All development subphases clear; no unresolved strict regressions.'}
    for n in range(4,13): phases[str(n)]={'state':'not_started','reason':'Required ordered exit evidence has not been recorded.'}
    phase5_order=('5A','5B','5C','5D','5E','5F','5G')
    phase5_plan=read(root,'ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json')
    for p in phase5_order:
        phases[p]={'state':'not_started','reason':'Regional anatomy package prepared; modelling not executed.'}
    previous_checkpoint_depth = None
    for n in range(4,13):
        record=control.get('phase_completion_records',{}).get(str(n))
        if record:
            from verify_original_v1_production_promotion import safe_path
            packet_path=safe_path(root,record['evidence']['path'])
            if digest(packet_path)!=record['evidence']['sha256']:
                raise ValueError('stale phase completion record evidence: '+str(n))
            checkpoint = phase_checkpoint_on_lineage(entries, rev, record.get('candidate_sha256'))
            # Later phases must be recorded on the same or a NEWER descendant checkpoint
            # than the preceding phase (depth 0=current; larger depth=older ancestor).
            if previous_checkpoint_depth is not None and checkpoint['depth'] > previous_checkpoint_depth:
                raise ValueError('phase completion checkpoint order conflicts with candidate lineage: '+str(n))
            packet=read(root,record['evidence']['path'])
            from verify_original_v1_phase_exit import verify_exit
            exit_issues=verify_exit(root,n,packet,checkpoint['sha256'])
            if exit_issues:raise ValueError('invalid phase exit evidence '+str(n)+': '+'; '.join(exit_issues))
            # If Phase 4 is being recorded on the CURRENT candidate, the current
            # deformation state itself must still be freeze-clean. Descendants may
            # inherit the immutable Phase 4 checkpoint only through exact SHA lineage;
            # any new regression reopens Phase 3 independently.
            if n==4 and checkpoint['depth']==0 and (fails or regs):
                raise ValueError('development freeze requires zero blockers and unresolved regressions')
            if n>4 and phases[str(n-1)]['state']!='complete':
                raise ValueError('phase completion bypasses dependency')
            if n==12:
                raise ValueError('Phase 12 requires separate controlled promotion workflow')
            phases[str(n)]={'state':'complete',
                            'reason':'Candidate-bound phase checkpoint verified on current lineage.',
                            'checkpoint_revision':checkpoint['revision'],
                            'checkpoint_candidate_sha256':checkpoint['sha256'],
                            'evidence':record['evidence']}
            previous_checkpoint_depth = checkpoint['depth']

    # Phase 5 regional receipts are evidence checkpoints, separate from the Phase 5
    # exit record. They advance 5A->5G only when the exact verified receipt/report is
    # on the current candidate lineage and all prior region records are present.
    region_records=control.get('phase5_region_records',{})
    if not isinstance(region_records,dict) or any(k not in phase5_order for k in region_records):
        raise ValueError('invalid Phase 5 regional record map')
    if region_records and phases['4']['state']!='complete':
        raise ValueError('Phase 5 regional records require a verified Phase 4 checkpoint')
    phase5_plan_obj=None
    previous_region_depth=None
    gap_seen=False
    for region in phase5_order:
        record=region_records.get(region)
        if not record:
            gap_seen=True
            continue
        if gap_seen:
            raise ValueError('Phase 5 regional record order has a gap before '+region)
        checkpoint=phase_checkpoint_on_lineage(entries,rev,record.get('candidate_sha256'))
        if previous_region_depth is not None and checkpoint['depth']>previous_region_depth:
            raise ValueError('Phase 5 regional checkpoint order conflicts with candidate lineage: '+region)
        receipt_ref=record.get('receipt')
        if not isinstance(receipt_ref,dict):
            raise ValueError('Phase 5 regional receipt reference missing: '+region)
        from verify_original_v1_production_promotion import safe_path
        receipt_path=safe_path(root,receipt_ref.get('path',''))
        if digest(receipt_path)!=receipt_ref.get('sha256'):
            raise ValueError('Phase 5 regional receipt hash differs: '+region)
        receipt=read(root,receipt_ref['path'])
        if (receipt.get('schema_version')!=1 or receipt.get('phase')!=5 or receipt.get('region')!=region or
            receipt.get('contract_status')!='REGION_EVIDENCE_VERIFIED' or
            receipt.get('candidate_sha256')!=checkpoint['sha256'] or
            receipt.get('phase_complete') is not False or receipt.get('production_approved') is not False):
            raise ValueError('Phase 5 regional receipt identity/contract differs: '+region)
        report_ref=receipt.get('region_report')
        if not isinstance(report_ref,dict):
            raise ValueError('Phase 5 regional report reference missing: '+region)
        report_path=safe_path(root,report_ref.get('path',''))
        if digest(report_path)!=report_ref.get('sha256'):
            raise ValueError('Phase 5 regional report hash differs: '+region)
        if phase5_plan_obj is None:
            from original_v1_phase5_anatomy import load_plan,verify_region_report
            phase5_plan_obj=load_plan(root)
        report=read(root,report_ref['path'])
        pin_name=pin_of(checkpoint['revision'])
        freeze_record=(control.get('phase_completion_records',{}).get('4') or {})
        region_issues=verify_region_report(
            root,report,phase5_plan_obj,region,
            expected_freeze_sha=freeze_record.get('candidate_sha256'),
            expected_epoch_revision=pin_name,
            expected_epoch_sha=bases[pin_name]['baseline']['candidate_sha256'])
        if region_issues:
            raise ValueError('invalid Phase 5 regional evidence '+region+': '+'; '.join(region_issues))
        phases[region]={'state':'complete',
                        'reason':'Candidate-bound regional anatomy evidence verified on current lineage.',
                        'work_package':phase5_plan['regions'][region]['work_package'],
                        'checkpoint_revision':checkpoint['revision'],
                        'checkpoint_candidate_sha256':checkpoint['sha256'],
                        'evidence':receipt_ref}
        previous_region_depth=checkpoint['depth']
    if phases['5']['state']=='complete' and any(phases[p]['state']!='complete' for p in phase5_order):
        raise ValueError('Phase 5 exit record exists without all regional evidence records')
    if phases['3']['state']=='complete' and phases['4']['state']=='complete' and phases['5']['state']!='complete':
        for region in phase5_order:
            if phases[region]['state']!='complete':
                phases[region]['state']='active'
                phases[region]['reason']='Next ordered Phase 5 anatomy region; modelling/evidence not yet verified.'
                phases[region]['work_package']=phase5_plan['regions'][region]['work_package']
                break

    refs=[evidence(root,current['evidence_location']),current['manifest'],evidence(root,'ORIGINAL_V1_CANDIDATE_STATUS.json')]
    if current.get('full_evidence_receipt'): refs.append(current['full_evidence_receipt'])
    for c in current['comparisons'].values(): refs.append(c['evidence'])
    diag=root/f'{RC}/remaining_diagnostics_{rev}'
    if diag.exists():
        for p in sorted(diag.glob('*.json')):
            d=json.loads(p.read_text()); source=d.get('source_candidate_sha256',d.get('candidate_sha256'))
            # Diagnostics lacking source identity are visible but cannot select edits.
            if source==current['sha256']: refs.append(evidence(root,p.relative_to(root).as_posix()))
    snapshot_reviews=[]
    for kind in ('visual','milestone'):
        snapshot=verified_review(root,rev,current['sha256'],kind)
        if snapshot:
            snapshot_reviews.append(snapshot); refs.append(snapshot['evidence'])
            current[kind+'_review_location']=snapshot['evidence']['path']
    status={'schema_version':1,'asset':'HomeGymPT_Male_ORIGINAL_v1','rig':'hgpt_canonical_v4_original',
        'branch':control['branch'],'current_phase':next((n for n in range(3,13) if phases[str(n)]['state']!='complete'),12),
        'current_subphase':(
            ('3B' if phases['3B']['state']=='active' else next((p for p in ('3D','3C','3E') if phases[p]['state']!='complete'),'4'))
            if phases['4']['state']!='complete' else
            (next((p for p in phase5_order if phases[p]['state']!='complete'),'5-exit')
             if phases['5']['state']!='complete' else
             next((str(n) for n in range(6,13) if phases[str(n)]['state']!='complete'),'12'))
        ),
        'current_candidate':rev,'candidate_state':current['state'],'candidate_classification':current['classification'],
        'pinned_baseline':{'revision':current['pinned_baseline_name'],'id':bases[current['pinned_baseline_name']]['baseline']['baseline_id'],'candidate_sha256':bases[current['pinned_baseline_name']]['baseline']['candidate_sha256'],'evidence':evidence(root,bases[current['pinned_baseline_name']]['file'])},
        'historical_pinned_baselines':[{'revision':n,'id':b['baseline']['baseline_id'],'first_candidate_number':b['first_rev'],'evidence':evidence(root,b['file'])} for n,b in bases.items()],
        'development_failure_count':ev['failure_count'],'development_failures':fails,
        'production_failure_count':evaluate(root,current['evidence_location'],'production_target')['failure_count'],
        'production_approved':False,'phases':phases,'unresolved_regressions':regs,
        'pending_owner_reviews':[x for x in control['owner_reviews'] if x['owner_review']=='pending']+snapshot_reviews,
        'latest_evidence':refs,'last_known_candidate_sha256':current['sha256'],
        'evidence_timestamp':current['evidence_timestamp'],'source_head':control['source_head'],
        'incomplete_candidates':sorted(set(incomplete),key=revision_key),
        'what_changed':f"{rev}: solution {current['weight_solution'] or 'geometry edit'} on {current['parent'] or 'original source'}; candidate remains experimental.",
        'what_passed':([p+' DEVELOPMENT CLEAR' for p in ('3A','3B','3C','3D','3E') if phases[p]['state']=='complete']
                       + [pose+' DEVELOPMENT CLEAR (severity comparisons remain separate)' for pose in ('curl_peak','pushup_bottom') if not any(f['pose']==pose for f in fails)]),
        'note':'Derived from complete committed evidence; no visual acceptance or production promotion inferred.'}
    status['next_action']=next_action(status,control)
    entries['R2']={'revision':'R2','sha256':baseline['candidate_sha256'],
        'parent':baseline.get('source_o2_blend_sha256'),'change_type':'Pinned original deformation baseline',
        'weight_solution':None,'topology_change':None,'development_failure_count':base_eval['failure_count'],
        'regression_count':0,'improvement_count':0,'comparison_baselines':[],
        'state':'experimental','reason':'Pinned baseline, not owner acceptance or production approval.',
        'owner_review':'pending','evidence_location':baseline_path,'visual_review_location':None,
        'manifest':evidence(root,CAND+'/DEFORMATION_BASELINE_R2.json')}
    for n,b in bases.items():
        if n=='R2': continue
        entries[n]={'revision':n,'sha256':b['baseline']['candidate_sha256'],'parent':None,'change_type':'Pinned deformation baseline for stress-pose epoch '+b['baseline'].get('epoch',''),
            'weight_solution':None,'topology_change':None,'development_failure_count':b['eval']['failure_count'],
            'regression_count':0,'improvement_count':0,'comparison_baselines':[],
            'state':'experimental','reason':'Pinned baseline, not owner acceptance or production approval.',
            'owner_review':'pending','evidence_location':b['path'],'visual_review_location':None,
            'manifest':evidence(root,b['file'])}
    ledger={'schema_version':1,'pinned_baseline':current['pinned_baseline_name'],'production_approved':False,
            'historical_disposition_source':control['historical_dispositions']['source'],
            'candidates':[entries[r] for r in sorted(entries,key=revision_key)]}
    return status,ledger
