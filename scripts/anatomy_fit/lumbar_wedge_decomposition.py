"""Provisional orientation decomposition; +X left, +Y posterior, +Z superior."""
import importlib.util
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('upper_frames',Path(__file__).with_name('lumbar_endplate_orientations.py'))
upper_frames=importlib.util.module_from_spec(spec);spec.loader.exec_module(upper_frames)
BODIES=['L1','L2','L3','L4','L5']
def derive(sacral_slope_deg, segment_angles, body_wedges):
 if set(body_wedges)!=set(BODIES):raise ValueError('five separate vertebral body wedges required')
 if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in body_wedges.values()):raise ValueError('finite numeric body angles required')
 superior=upper_frames.derive(sacral_slope_deg,segment_angles)
 inferior={};discs={}
 for segment in upper_frames.LEVELS:
  body=segment.split('/')[0];wedge=body_wedges[body]
  a=superior[body]['slope_deg']+wedge
  d=segment_angles[segment]-wedge
  if abs(a)>=90 or not 0<d<45:raise ValueError('outside provisional standing lordotic orientation family')
  s,c=math.sin(math.radians(a)),math.cos(math.radians(a))
  inferior[body]={'slope_deg':a,'left_axis':[1.,0.,0.],'AP_axis':[0.,c,s],'normal':[0.,-s,c],'centre_m':None,'endplate':'inferior'}
  discs[segment]=d
 return {'superior_frames':superior,'inferior_frames':inferior,'body_wedges_deg':body_wedges,'disc_wedges_deg':discs}
if __name__=='__main__':
 p=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_spine_reference_pose_p1.json').read_text())
 e=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_wedge_evidence_v1.json').read_text())
 report={'schema_version':1,'status':'PROVISIONAL_CROSS_COHORT_ORIENTATION_DECOMPOSITION','freeze_ready':False,'source_files':['canonical_spine_reference_pose_p1.json','canonical_lumbar_wedge_evidence_v1.json'],'axis_convention':'+X left; +Y posterior; +Z superior. AP_axis points posterior. Positive lordotic body wedge = inferior slope minus superior slope.','geometry':derive(p['global_male_reference_deg']['sacral_slope'],p['lumbar_distribution']['provisional_scaled_levels_deg'],{k:v['mean_deg'] for k,v in e['male_body_wedges'].items()}),'limitations':['Cross-cohort provisional construction, not one measured subject or frozen anatomy.','Derived disc angles are P1 segment minus body angle; they are not the Bailey standing disc means.','No vertebral centres, endplate envelope or non-bone disc thickness inferred.','Source SE is not a population corridor; no SD is inferred.','Need compatible body/disc height and surface definitions plus independent angle corroboration before global placement.']}
 (ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_body_disc_frames_p1.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 print(report['status'])
