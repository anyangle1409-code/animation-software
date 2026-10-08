"""Verify source-projected neutral lines, not carpal placement or motion acceptance."""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_carpal_axis_targets_v1.json'
def validate(data):
 errors=[]
 angles=data['source_angles_deg'];vectors=data['HGPT_axis_unit_vectors']
 if len(angles)!=7 or 'pisiform' in angles:errors.append('expected seven reported carpal axes; pisiform remains unresolved')
 for side,ulnar_sign in [('left',-1),('right',1)]:
  side_vectors=vectors.get(side,{})
  if set(side_vectors)!=set(angles):errors.append(f'{side}: missing or extra source axes')
  for bone,a in angles.items():
   v=side_vectors.get(bone)
   if v is None or len(v)!=3 or not all(math.isfinite(x) for x in v):
    errors.append(f'{side}/{bone}: finite XYZ required');continue
   x,y,z=v
   if abs(math.sqrt(x*x+y*y+z*z)-1)>1e-10 or z<=0:errors.append(f'{side}/{bone}: unit proximal-positive line required')
   sagittal=math.degrees(math.atan2(-y,z));coronal=math.degrees(math.atan2(ulnar_sign*x,z))
   if abs(sagittal-a['sagittal_mean'])>1e-9:errors.append(f'{side}/{bone}: palmar projection differs from source')
   if abs(coronal-a['coronal_mean'])>1e-9:errors.append(f'{side}/{bone}: ulnar projection differs from source')
 return errors
if __name__=='__main__':
 errors=validate(json.loads(PATH.read_text()))
 print(json.dumps({'scope':'source angle/frame conversion only; centres, envelopes, contact and motion remain open','errors':errors,'passed':not errors},indent=2))
 raise SystemExit(bool(errors))
