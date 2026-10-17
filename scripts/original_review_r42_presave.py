"""Run fixed owner/legacy contour tests on native unsaved post-guard geometry."""
import os,sys,json,subprocess
from pathlib import Path
import numpy as np
def check(res,out,root):
 import build_original_movement_benchmarks_blender as bench
 import build_original_sculpt_corrective_blender as sculpt
 import original_v1_review_candidate_drives as drives
 body,rig=res['body'],res['runtime'];data={}
 for ht in (120.,130.,135.625,145.,156.,166.):
  bench._reset(rig);sculpt.press_pose(res,ht);drives.drive(rig,body)
  points,faces=bench._evaluated(body);data['faces']=np.asarray(faces)
  data[f'all_{ht}']=np.asarray([tuple(v) for v in points])
  for side in ('l','r'):
   data[f'gh_{side}_{ht}']=np.array(tuple(rig.matrix_world@rig.pose.bones['upperarm_'+side].head))
   data[f'elbow_{side}_{ht}']=np.array(tuple(rig.matrix_world@rig.pose.bones['forearm_'+side].head))
 dest=Path('/tmp/r42-response');path=dest/'pre_save_probe.npz';np.savez_compressed(path,**data)
 env=os.environ.copy();env['HGPT_CONTOUR_NPZ']=str(path)
 env['HGPT_LINE_PARENT_NPZ']=str(root/'ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017/probe/r35_contour_surfaces.npz')
 rows=[]
 for name in ('r37_contour','r38_marks','r41_line','r41_front','r42_profile'):
  result=subprocess.run(['/usr/bin/python3',str(root/f'scripts/tests/test_original_review_{name}.py')],env=env,capture_output=True,text=True)
  log=result.stdout+result.stderr;(dest/f'pre_save_{name}.txt').write_text(log)
  rows.append(dict(test=name,exit_code=result.returncode));print(log,flush=True)
 (dest/'pre_save_tests.json').write_text(json.dumps(rows,indent=2)+'\n')
 if any(r['exit_code'] for r in rows):raise RuntimeError(('Native post-guard contour tests failed before saving',rows))
 return rows
