"""Package native ablation evidence; no shape repair or acceptance claims."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from original_arm_back_audit import MODES,temporal_metrics,pose_difference_mm
root=Path(sys.argv[-1]);baseline=np.load(root/'r41/motion.npz');reference=json.loads((root/'r41/state.json').read_text());report={'diagnostic_only':True,'model_saved':False,'repair_complete':False,'modes':{},'unrun':['new geometry feasibility','new candidate safety checks','new candidate13 benchmarks','owner visual approval']}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for mode in MODES:
 z=np.load(root/mode/'motion.npz');state=json.loads((root/mode/'state.json').read_text())
 if state['bone_names']!=reference['bone_names']:raise RuntimeError('Different bone inventory')
 delta_matrix=float(np.max(np.abs(z['bone_matrices']-baseline['bone_matrices'])))
 end_error=pose_difference_mm(z['bone_endpoints'],baseline['bone_endpoints'])
 row=temporal_metrics(baseline['back_points'],z['back_points']);row.update(bone_endpoint_difference_mm=end_error,bone_matrix_max_abs_difference=delta_matrix,identical_pose=bool(delta_matrix<=1e-8 and end_error<=1e-5),protected_identity=state['protected_identity'],muted_keys=state['muted_names'])
 report['modes'][mode]=row
report['all_poses_identical']=all(x['identical_pose'] for x in report['modes'].values());report['all_protected_identities']=all(all(x['protected_identity'].values()) for x in report['modes'].values())
(root/'ablation_review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if not report['all_poses_identical'] or not report['all_protected_identities']:raise RuntimeError('Read-only diagnostic identity failed')

for mode in MODES:
 state=json.loads((root/mode/'state.json').read_text())
 for view in ('back','three_quarter'):
  for frame in (64,80,100,128,160):
   name=f'f{frame:03d}_{view}';im=Image.open(root/mode/(name+'.png')).convert('RGBA');bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im);im=bg.convert('RGB');draw=ImageDraw.Draw(im)
   for bone,ends in state['projections'][name].items():draw.line([tuple(p) for p in ends],fill=(70,235,235),width=2)
   draw.text((8,8),f'{mode} | t={frame/160:.3f}',font=small,fill='white');im.save(root/mode/(name+'_bone_overlay.jpg'),quality=94)
# Side-by-side native skin and bone overlay at the marked time.
canvas=Image.new('RGB',(1024,1120),'white');d=ImageDraw.Draw(canvas);d.text((10,8),'Same pose, actual skeleton and skin: R41 / R52',font=font,fill='black')
for row,view in enumerate(('back','three_quarter')):
 for col,mode in enumerate(('r41','r52')):
  canvas.paste(Image.open(root/mode/f'f128_{view}_bone_overlay.jpg'),(col*512,45+row*512))
d.text((10,1075),'Bone lines project actual runtime endpoints; shown through skin for inspection.',font=small,fill='black');d.text((10,1095),'Read-only diagnostic. No repaired or saved model. t=0.800 in both panels.',font=small,fill='black');canvas.save(root/'skeleton_skin_t0800.jpg',quality=95)
# All family ablations at mid-press and the owner-marked time, rear view.
canvas=Image.new('RGB',(5*360,2*400+70),'white');d=ImageDraw.Draw(canvas);d.text((12,8),'Temporary skin-family switches: diagnostics, not proposed models',font=font,fill='black')
for row,frame in enumerate((80,128)):
 for col,mode in enumerate(MODES):
  im=Image.open(root/mode/f'f{frame:03d}_back.png').convert('RGBA');bg=Image.new('RGBA',im.size,(27,27,27,255));bg.alpha_composite(im);canvas.paste(bg.convert('RGB').resize((360,360)),(col*360,70+row*400));d.text((col*360+6,45+row*400),f'{mode} | t={frame/160:.3f}',font=small,fill='black')
canvas.save(root/'family_ablation_comparison.jpg',quality=95)
