#!/usr/bin/env python3
"""Regenerate roadmap status, candidate ledger and deterministic phone dashboard."""
import argparse
import json
import sys
from original_v1_production_control import ROOT, build

LABELS = [('0','Provenance'),('1','Base body'),('2','Rig'),('3A','Shoulders'),
          ('3B','Hands/fingers'),('3C','Grip'),('3D','Wrist'),('3E','Hip/lunge'),
          ('4','Development freeze'),('5','High-detail anatomy'),('6','Final topology'),
          ('7','Clothing'),('8','Materials'),('9','Production deformation'),
          ('10','Runtime integration'),('11','Automatic QA'),('12','Production freeze')]

def dashboard(s):
    nxt=s['next_action']
    lines=['# ORIGINAL v1 daily status (generated)', '',
           'CURRENT PHASE',f"Phase {s['current_phase']} / {s['current_subphase']}",'',
           'CURRENT CANDIDATE',f"{s['current_candidate']} — {s['candidate_classification']}; EXPERIMENTAL. {s['pinned_baseline']['revision']} stays pinned.",
           f"SHA-256: `{s['last_known_candidate_sha256']}`",'',
           'DEVELOPMENT BLOCKERS',f"{s['development_failure_count']} failures; {len(s['unresolved_regressions'])} separate strict severity regressions versus {s['pinned_baseline']['revision']}.",'']
    for f in s['development_failures']: lines.append(f"- {f['pose']} / {f.get('region') or 'whole body'} / {f['metric']}: {f['value']} ({f['rule']})")
    lines += ['', 'WHAT CHANGED',s['what_changed'],'','WHAT PASSED']
    lines += ['- '+p for p in s['what_passed']] or ['- No newly clear subphase.']
    lines += ['', 'PENDING OWNER REVIEWS']
    lines += ['- '+('['+r['checkpoint']+'](../'+r['review_index']+')' if r.get('review_index') else r['checkpoint'])+' — pending, NON-BLOCKING.' for r in s['pending_owner_reviews']]
    lines += ['- Latest candidate snapshot remains pending; images must come from real renders.','',
              'NEXT EXACT TASK',nxt['action']+' — '+nxt['reason']]
    if nxt.get('command'): lines.append('`'+nxt['command']+'`')
    if nxt.get('work_package'): lines.append('Read `'+nxt['work_package']+'`.')
    lines += ['', 'REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Production approved: NO.', '']
    for phase,label in LABELS:
        state=s['phases'][phase]['state']
        symbol='✅' if state=='complete' else '🟡' if state=='refinement' else '🔴' if phase=='3E' and state=='blocked' else '🟠' if state in ('active','blocked','pending_owner_review') else ' '
        lines.append(f'[{symbol}] Phase {phase} {label}')
    lines += ['', 'Evidence timestamp: '+str(s['evidence_timestamp']),
              'Evidence references (exact content hashes are in machine status):','']
    lines += ['- `'+x['path']+'`' for x in s['latest_evidence']]
    lines += ['', 'The older candidate-status contract and committed GLBs verify the R2/export checkpoint, not this latest revision.',
              'Inherited shoulder/torso regressions remain visible; DEVELOPMENT CLEAR is not strict acceptance.',
              'No model geometry, weights, rig, thresholds or baseline changes are made by this generator.','']
    return '\n'.join(lines)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    try:
        s,l=build(ROOT)
        outputs={'ORIGINAL_V1_HIGH_DETAIL_STATUS.json':json.dumps(s,indent=2)+'\n',
                 'ORIGINAL_V1_CANDIDATE_LEDGER.json':json.dumps(l,indent=2)+'\n',
                 'docs/ORIGINAL_V1_DAILY_STATUS.md':dashboard(s)}
        for name,value in outputs.items():
            p=ROOT/name
            if args.check:
                if not p.exists() or p.read_text(encoding='utf-8')!=value: raise ValueError('stale generated output: '+name)
            else: p.write_text(value,encoding='utf-8')
        print('STATUS VERIFIED' if args.check else 'STATUS GENERATED',s['current_candidate'],s['development_failure_count'],'development failures')
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print('STOP — '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
