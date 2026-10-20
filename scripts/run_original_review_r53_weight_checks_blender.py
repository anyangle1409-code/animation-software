"""Run unchanged checks, applying the trial after each runner creates helpers."""
import sys,runpy,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
import original_review_r52_native as native
import original_v1_review_candidate_drives as drives
from original_review_r53_weights import install_patch
target=sys.argv[-4];sys.argv=sys.argv[:-4]+sys.argv[-3:]
assert target in ('validate_original_review_r52_benchmarks_blender.py','measure_original_review_r52_dense_motion_blender.py')
def patch(res):
 result=install_patch(res)
 if os.environ.get('HGPT_R53_EXPECTED_PATCH'):
  expected=np.load(os.environ['HGPT_R53_EXPECTED_PATCH'])
  assert np.array_equal(result['before'],expected['before']) and np.array_equal(result['after'],expected['after']),'Benchmark replay changed tested weights'
if target=='validate_original_review_r52_benchmarks_blender.py':
 original_setup=drives.setup
 def setup(res):
  result=original_setup(res);patch(res);return result
 drives.setup=setup
else:
 original=native.install
 def install(*args,**kwargs):
  result=original(*args,**kwargs);patch(args[0]);return result
 native.install=install
runpy.run_path(str(ROOT/'scripts'/target),run_name='__main__')
