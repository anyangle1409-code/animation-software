"""Preserve all containment findings and label provisional anatomical-guide views."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path(sys.argv[-1]);modes=('r41','r52');reports={m:json.loads((root/m/'containment.json').read_text()) for m in modes}
a,b=[np.load(root/m/'scapula_matrices.npz')['matrices'] for m in modes]
error=float(np.max(np.abs(a-b)));summary=dict(diagnostic_only=True,model_saved=False,repair_complete=False,scapula_pose_matrix_max_abs_difference=error,same_scapula_pose=bool(error<=1e-8),modes={})
for mode,d in reports.items():
 if len(d['rows'])!=161 or not all(d['protected_identity'].values()):raise RuntimeError('Incomplete/protected identity failure')
 rows=[]
 for row in d['rows']:
  item=dict(frame=row['frame'],t=row['t'],sides={})
  for side,s in row['sides'].items():
   outside=[q['nearest_skin_distance_mm'] for q in s['guide_samples'] if q['classification']=='outside']
   item['sides'][side]=dict(guide_sample_counts=s['sample_counts'],maximum_sampled_guide_outside_distance_mm=max(outside,default=0.),landmarks={k:{kk:v for kk,v in q.items() if kk in ('classification','nearest_skin_distance_mm','signed_clearance_mm')} for k,q in s['landmarks'].items()},runtime_control_only=s['runtime_control_only'])
  rows.append(item)
 summary['modes'][mode]=dict(skin_topology_closed=d['skin_topology_closed'],protected_identity=d['protected_identity'],rows=rows,limitations=d['limitations'])
(root/'containment_review.json').write_text(json.dumps(summary,indent=2)+'\n')
if not summary['same_scapula_pose']:raise RuntimeError('Different poses: no comparison montage generated')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
colors={'inside':(75,225,140),'outside':(255,80,80),'on_skin':(210,210,210),'ambiguous':(255,190,60),'unreliable_open_skin':(255,190,60)}
for frame in (0,80,128,160):
 canvas=Image.new('RGB',(1280,1390),'white');draw=ImageDraw.Draw(canvas)
 draw.text((12,8),'Project shoulder-blade guide and landmarks — not rig-control lines',font=font,fill='black')
 draw.text((12,34),'Existing provisional geometry; diagnostic only. Green inside / red outside / amber uncertain.',font=small,fill='black')
 for col,mode in enumerate(modes):
  for row,view in enumerate(('back','three_quarter')):
   key=f'f{frame:03d}_{view}';raw=Image.open(root/mode/(key+'.png')).convert('RGBA');bg=Image.new('RGBA',raw.size,(27,27,27,255));bg.alpha_composite(raw);im=bg.convert('RGB');pen=ImageDraw.Draw(im)
   for side,p in reports[mode]['projections'][key].items():
    for a,b in p['edges']:pen.line([tuple(p['vertices'][a]),tuple(p['vertices'][b])],fill=(70,210,235),width=1)
    for xy,status in zip(p['vertices'],p['classification']):x,y=xy;pen.ellipse((x-2,y-2,x+2,y+2),fill=colors[status])
    for name,lm in p['landmarks'].items():x,y=lm['pixel'];pen.ellipse((x-3,y-3,x+3,y+3),fill=colors[lm['classification']]);pen.text((x+4,y),name,font=small,fill=colors[lm['classification']])
   pen.text((8,8),f'{mode} | t={frame/160:.3f} | {view}',font=small,fill='white');canvas.paste(im,(col*640,70+row*640))
 draw.text((12,1355),'Guide wires shown through skin for inspection. Sampled containment is not full anatomical validation.',font=small,fill='black')
 canvas.save(root/f'scapula_containment_t{frame:03d}.jpg',quality=95)
print('CONTAINMENT_PACKAGED',summary['same_scapula_pose'],flush=True)
