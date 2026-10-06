import sys, json; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
from hgpt_pose import *
P=Poser(); rows={}
fb=[b.name for b in P.rig.data.bones if b.name.startswith('axfold_') and '_ins_' not in b.name and b.name.endswith('_l')]
rest={b:P.rig.data.bones[b].length for b in fb}
rd={b:np.array(P.rig.data.bones[b].tail_local-P.rig.data.bones[b].head_local) for b in fb}
for plane in ('abduction','flexion'):
  for th in (0,30,60,90,120,150,170):
    for ax in (-40,0,40):
      P.reset(); P.elevate('l',plane,th,axial=ax if th<=120 else ax*0.6); P.upd()
      r={}
      for b in fb:
        pb=P.pb(b); v=np.array(pb.tail-pb.head); r[b]=[round(float(np.linalg.norm(v)/rest[b]),3), round(float(np.degrees(np.arccos(np.clip(v@rd[b]/np.linalg.norm(v)/np.linalg.norm(rd[b]),-1,1)))),1)]
      rows[f'{plane}_{th:03d}_{ax:+d}']=r
json.dump(rows,open(argv[1],'w'),indent=0)
for k,v in rows.items():
  if k.endswith('+0'): print(k,v)
