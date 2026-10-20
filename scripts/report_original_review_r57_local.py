"""Keep complete failures and classify R57 native evidence without model promotion."""
import json
import sys
from pathlib import Path
import numpy as np

def report(folder):
    p=Path(folder)
    required=('candidate.npz','candidate.npz.json','native_final.json',
              'native_final.json.points.npz','dense_motion.json','benchmarks.json')
    missing=[s for s in required if not (p/s).exists()]
    exits={}
    for stage in ('generate','native','benchmarks','dense','R52_original_render','R57_local_study_render'):
        f=p/(stage+'_exit.txt')
        try:
            exits[stage]=int(f.read_text().strip())
        except (FileNotFoundError,ValueError):
            exits[stage]=None
    failures=[]
    if missing:
        failures.append("Missing outputs: "+", ".join(missing))
    failures.extend(str(k)+" execution="+str(v) for k,v in exits.items() if v!=0)
    outcome=dict(status='R57_EVIDENCE_INCOMPLETE',model_saved=False,approved=False,
                 production_ready=False,original_thresholds_unchanged=True,
                 execution_exits=exits,missing=missing,failures=failures)
    if not missing:
        from pathlib import Path as P
        import os
        sys.path.insert(0,str(P(__file__).resolve().parent/'tests'))
        from test_original_review_r48_approved_outline import outline
        with np.load(p/'source.npz') as source:
            f=source['faces']
            parent=source['base'][25]
            target=source['r48_profile_target_points']
            with np.load(p/'native_final.json.points.npz') as actual:
                marked=actual['points'][25]
            outline_error=float(abs(outline(marked,f)-outline(target,f)).max()*1000)
            base_cross=np.cross(parent[f][:,1]-parent[f][:,0],
                                parent[f][:,2]-parent[f][:,0])
            now_cross=np.cross(marked[f][:,1]-marked[f][:,0],
                               marked[f][:,2]-marked[f][:,0])
            reversed_normals=int(((base_cross*now_cross).sum(1)<=0).sum())
        native=json.loads((p/'native_final.json').read_text())
        dense=json.loads((p/'dense_motion.json').read_text())
        benchmark=json.loads((p/'benchmarks.json').read_text())
        checks={
            'R47_marked_outline_le_1mm':bool(outline_error<=1.),
            'R48_marked_normal_reversals_zero':bool(reversed_normals==0),
            'R52_native_83_safety':bool(len(native.get('samples',[]))==83 and
                                        all(r.get('passed',False) for r in native['samples']) and
                                        not native['contacts']),
            'R43_original_native_motion_le_0_5mm':bool(native['back_motion_excess_mm']<=.5),
            'R43_posterior_crease_le_2deg':bool(native['posterior_crease_excess_degrees']<=2),
            'R52_dense_161_motion_le_0_5mm':bool(dense['original40_step_equivalent_excess_mm']<=.5),
            'R52_early_outward_le_0_05mm':bool(dense['early_outward_increment_mm']<=.05),
            'R52_adjacent_step_le_3mm':bool(dense['oscillation']['passed']),
            '13_original_benchmarks_no_regression':bool(benchmark['passed'] and
                                      len(benchmark['report']['benchmarks'])==13)
        }
        failures.extend(name for name,good in checks.items() if not good)
        outcome.update(
            status=('R57_SCREEN_ONLY_ALL_NATIVE_NUMERICAL_GATES_PASSED_OWNER_REVIEW_REQUIRED'
                    if not failures else 'R57_REJECTED_OR_INCOMPLETE_NATIVE_GATES'),
            checks=checks,marked_outline_error_mm=outline_error,
            marked_reversed_normals=reversed_normals,
            actual_83_new_contacts=len(native['contacts']),
            actual_native_motion_excess_mm=native['back_motion_excess_mm'],
            posterior_crease_excess_deg=native['posterior_crease_excess_degrees'],
            dense161_motion_excess_mm=dense['original40_step_equivalent_excess_mm'],
            dense161_early_outward_mm=dense['early_outward_increment_mm'],
            benchmark_regressions=len(benchmark['regressions']),
            failures=failures)
    outcome['limitations']=[
        'An experimental improvement in motion cannot independently establish lifelike anatomy.',
        'Original R47 marked-pose outline approval does not validate all 161 movement poses.',
        'No Blender model was saved/promoted/merged or production PT app changed.',
        'Visual owner approval remains separate even if all numerical checks pass.',
        'R57 spatial/temporal kernel is a first-party diagnostic hypothesis, not a verified physiological soft-tissue model.']
    (p/'r57_result.json').write_text(json.dumps(outcome,indent=2)+chr(10))
    print(json.dumps(outcome,indent=2))
    return outcome

if __name__=='__main__':
    report(sys.argv[1])
