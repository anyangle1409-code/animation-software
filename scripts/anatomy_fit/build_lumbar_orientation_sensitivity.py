"""Compare source-separated body wedge families against the same provisional P1."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('wedges',Path(__file__).with_name('lumbar_wedge_decomposition.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def build():
 b=ROOT/'ORIGINAL_V1_WORK/anatomy'
 p=json.loads((b/'canonical_spine_reference_pose_p1.json').read_text())
 a=json.loads((b/'canonical_lumbar_wedge_evidence_v1.json').read_text())
 c=json.loads((b/'canonical_lumbar_wedge_independent_crosscheck_v1.json').read_text())
 families={}
 for label,angles in [('Bailey_male_pooled_body',{k:v['mean_deg'] for k,v in a['male_body_wedges'].items()}),('Been_mixed_sex_standing_body',{k:v['mean'] for k,v in c['body_wedges_deg'].items()})]:
  families[label]=m.derive(p['global_male_reference_deg']['sacral_slope'],p['lumbar_distribution']['provisional_scaled_levels_deg'],angles)
 differences={k:families['Bailey_male_pooled_body']['inferior_frames'][k]['slope_deg']-families['Been_mixed_sex_standing_body']['inferior_frames'][k]['slope_deg'] for k in m.BODIES}
 return {'schema_version':1,'status':'PROVISIONAL_SOURCE_SEPARATED_ORIENTATION_SENSITIVITY','freeze_ready':False,'families':families,'Bailey_minus_Been_inferior_slope_deg':differences,'maximum_abs_difference_deg':max(abs(v) for v in differences.values()),'limitations':['Both constructions retain P1 superior orientations. Only body/inferior orientation and derived disc angle differ.','Source separation is preserved; neither mean is selected or averaged into a frozen target.','Maximum difference across these means is not a population uncertainty bound or SD.','No centres, endplate surfaces or disc heights inferred.']}
if __name__=='__main__':
 report=build();out=ROOT/'ORIGINAL_V1_WORK/anatomy/canonical_lumbar_orientation_sensitivity_p1.json'
 out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(report['maximum_abs_difference_deg'])
