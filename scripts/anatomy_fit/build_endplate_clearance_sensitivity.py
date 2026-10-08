"""Synthetic footprint sweep: no disc height is converted to a centre target."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('clearance',Path(__file__).with_name('endplate_clearance.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def build():
 b=ROOT/'ORIGINAL_V1_WORK/anatomy';families=json.loads((b/'canonical_lumbar_orientation_sensitivity_p1.json').read_text())['families'];result={}
 for name,f in families.items():
  segments={}
  for segment in f['disc_wedges_deg']:
   upper,lower=segment.split('/');un=f['inferior_frames'][upper]['normal'];ln=f['superior_frames'][lower]['normal']
   # Fixture projection radii and centre gaps are sensitivity inputs, not targets.
   segments[segment]=[{'synthetic_XY_radii_mm':[25.,radius],'synthetic_centre_gap_mm':gap,'clearance':m.clearance([0,0,gap],un,[0,0,0],ln,[0,0],[25.,radius])} for radius in [12.,18.,24.] for gap in [6.,9.,12.]]
  result[name]=segments
 return {'schema_version':1,'status':'SYNTHETIC_PLANAR_CLEARANCE_SENSITIVITY_NOT_ANATOMICAL_PLACEMENT','freeze_ready':False,'orientation_source':'canonical_lumbar_orientation_sensitivity_p1.json','families':result,'limitations':['All footprint radii and centre gaps here are explicitly synthetic sweep inputs, not population means or selected anatomy.','HGPT XY projected ellipse is not a measured native endplate envelope.','Normals are P1 provisional; upper and lower centres are fixture origins only.','Analytic clearance proves only separation of planes over supplied common domain; actual curved surfaces and footprint overlap still required.','No anatomical target or gate acceptance follows from a positive result.']}
if __name__=='__main__':
 r=build();(ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_endplate_clearance_sensitivity_v1.json').write_text(json.dumps(r,indent=2,allow_nan=False)+'\n');print(json.dumps({'fixture_cases':90,'intersect_or_touch_cases':sum(not c['clearance']['separated_everywhere'] for f in r['families'].values() for cases in f.values() for c in cases)}))
