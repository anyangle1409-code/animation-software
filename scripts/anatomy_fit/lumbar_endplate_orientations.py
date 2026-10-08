"""P1 superior-endplate orientations only; do not invent centres or disc wedges."""
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LEVELS=['L1/L2','L2/L3','L3/L4','L4/L5','L5/S1']
def derive(sacral_slope_deg, segment_angles):
 if set(segment_angles)!=set(LEVELS):raise ValueError('all five superior-to-superior levels required')
 if not all(math.isfinite(v) for v in [sacral_slope_deg,*segment_angles.values()]):raise ValueError('finite angles required')
 angles={'S1':sacral_slope_deg}
 lower='S1'
 for segment in reversed(LEVELS):
  upper=segment.split('/')[0];angles[upper]=angles[lower]-segment_angles[segment];lower=upper
 if any(abs(a)>=90 for a in angles.values()):raise ValueError('reference endplate normal must remain superior')
 result={}
 for level,a in angles.items():
  s,c=math.sin(math.radians(a)),math.cos(math.radians(a))
  result[level]={'slope_deg':a,'left_axis':[1.,0.,0.],'AP_axis':[0.,c,s],'normal':[0.,-s,c],'centre_m':None,'endplate':'superior'}
 return result
if __name__=='__main__':
 p=json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_spine_reference_pose_p1.json').read_text())
 report={'schema_version':1,'status':'PROVISIONAL_P1_SUPERIOR_ENDPLATE_ORIENTATIONS_ONLY','freeze_ready':False,'reference':'canonical_spine_reference_pose_p1.json','source_semantics':p['lumbar_distribution']['measurement_semantics'],'frames':derive(p['global_male_reference_deg']['sacral_slope'],p['lumbar_distribution']['provisional_scaled_levels_deg']),'limitations':['No absolute vertebral centres derived.','Each superior-to-superior angle includes upper vertebral body wedging and intervening disc; provisional inferior/disc orientation decomposition is now stored separately in canonical_lumbar_body_disc_frames_p1.json; exact targets remain unresolved.','No parallel-endplate assumption or body-height/disc-mean substitution is permitted.','P1 scaling combines separate cohorts as a provisional shape family, not an individual measured spine.']}
 out=ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_superior_endplate_frames_p1.json';out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'status':report['status'],'L1_slope_deg':report['frames']['L1']['slope_deg']}))
