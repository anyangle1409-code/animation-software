"""Export supported distal rib segments from published population means only."""
import argparse,hashlib,json,math
from pathlib import Path
from rib_spiral_reconstruction import physical_distal_curve
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'ORIGINAL_V1_WORK/anatomy/rib_demographic_model_holcombe2017_v1.json'
OUT=ROOT/'ORIGINAL_V1_WORK/anatomy/rib_distal_source_mean_curves_v1.json'
def build(source=SOURCE):
 model=json.loads(source.read_text())
 report={'schema_version':1,'status':'VERIFIED_SOURCE_MEAN_DISTAL_SEGMENTS_ONLY','freeze_ready':False,'source_model':str(source.relative_to(ROOT)),'source_model_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'definition':'Published mixed-population level mean parameter inputs; nonlinear reconstruction of parameter means, not a pointwise population mean curve. In-plane peak to anterior endpoint only. No age/weight or canonical reference is selected.','coordinates':'source normalized rib plane, millimetres; not HGPT thorax coordinates','source_equations':'Holcombe thesis Eqs 2.2–2.7; proximal Eq2.18 unresolved','levels':{}}
 for k,v in model['levels'].items():
  p=v['population_mean'];c=physical_distal_curve(p['Sx_mm'],p['Xpk'],p['Ypk'],p['Bd'],samples=101)
  chord=math.dist(c[-1],c[0]);arc=sum(math.dist(a,b) for a,b in zip(c,c[1:]))
  report['levels'][k]={'input':{x:p[x] for x in ['Sx_mm','Xpk','Ypk','Bd']},'points_mm':c,'distal_polyline_length_mm':arc,'distal_endpoint_chord_mm':chord,'relative_length_excess':arc/chord-1,'rib_head':None,'tubercle':None,'costotransverse_joint_permitted':int(k)<=10,'full_rib_reconstructed':False}
 return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=OUT);args=parser.parse_args()
 args.out.write_text(json.dumps(build(),indent=2,allow_nan=False)+'\n')
 print('12 source-mean distal segments; proximal curves/contacts/global mapping remain open')
