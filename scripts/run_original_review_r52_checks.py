"""Run original tests unchanged, labeling source-projection and actual checks."""
from pathlib import Path
import os,sys,subprocess,json
ROOT=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]);stage=sys.argv[2];out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,HGPT_R52_RESPONSE=str(out/'source.npz'),HGPT_R52_SOLUTION=str(out/'solved.npz'),HGPT_R52_REPORT_DIR=str(out),
 HGPT_R43_RESPONSE=str(out/'source.npz'),HGPT_R43_SOLUTION=str(out/'solved.npz'),HGPT_R47_RESPONSE=str(out/'source.npz'),HGPT_R47_SOLUTION=str(out/'solved.npz'),
 HGPT_R48_RESPONSE=str(out/'source.npz'),HGPT_R48_SOLUTION=str(out/'solved.npz'),HGPT_R48_PARENT_RESPONSE='/tmp/r47-previous/tmp/r47-response/source.npz',HGPT_R48_APPROVED_SOLUTION='/tmp/r47-previous/tmp/r47-response/solved.npz',
 HGPT_CONTOUR_NPZ='/tmp/r52-study/R52/native_probe.npz',HGPT_LINE_PARENT_NPZ=str(ROOT/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017/probe/r35_contour_surfaces.npz'))
if stage=='unit':names=['r52_temporal','r52_projection','r52_study','r52_envelope','r48_preparation','r48_outline_derivative']
elif stage=='projection':names=['r47_authorized_scope','r43_motion','r43_back_surface','r48_marked_surface','r48_approved_outline','r52_preservation']
elif stage=='native':names=['r52_actual_native','r42_profile','r37_contour','r38_marks','r41_line','r41_front']
else:raise ValueError('Unknown check stage')
results={}
for name in names:
 log=out/(name+'_test.txt')
 with log.open('w') as f:r=subprocess.run([sys.executable,str(ROOT/'scripts/tests'/('test_original_review_'+name+'.py')),'-v'],env=env,stdout=f,stderr=subprocess.STDOUT)
 results[name]=r.returncode;(out/(name+'_test_exit.txt')).write_text(str(r.returncode)+'\n');print('R52_RETAINED_TEST',stage,name,r.returncode,flush=True)
(out/(stage+'_check_status.json')).write_text(json.dumps(dict(stage=stage,tests=results,note='projection stage original seven-control outcomes are legacy diagnostics, not actual dense-model certification' if stage=='projection' else 'unchanged original or additional direct check'),indent=2)+'\n')
if stage=='unit' and any(results.values()):raise SystemExit(1)
