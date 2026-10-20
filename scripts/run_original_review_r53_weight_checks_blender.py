"""Run unchanged benchmark/dense algorithms with the authorised patch installed."""
import sys,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/anatomy_fit')]
import original_review_r52_native as native
from original_review_r53_weights import install_patch
original=native.install
def install(*args,**kwargs):
 result=original(*args,**kwargs);install_patch(args[0]);return result
native.install=install
target=sys.argv[-4];sys.argv=sys.argv[:-4]+sys.argv[-3:]
assert target in ('validate_original_review_r52_benchmarks_blender.py','measure_original_review_r52_dense_motion_blender.py')
runpy.run_path(str(ROOT/'scripts'/target),run_name='__main__')
