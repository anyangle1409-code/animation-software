import sys; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out=argv[1]
from hgpt_pose import *
P=Poser(); P.set_correctives(0); cam=setup_render(600)
for o in bpy.data.objects:
    if o.type=='MESH' and 'SHORTS' in o.name: o.hide_render=True
for m in P.body.modifiers:
    if m.type=='MASK': m.show_render=False
P.reset()
c=np.array([-0.17,0.02,1.33])
for v,(az,el,d) in {'below':(85,-55,0.45),'front':(20,0,0.55),'rear':(160,0,0.55)}.items():
    look(cam,c,az,el,d); render(f'{out}_{v}.png')
P.elevate('l','abduction',60); P.elevate('r','abduction',60)
for v,(az,el,d) in {'abd60_axilla':(80,-30,0.6)}.items():
    look(cam,c+np.array([-0.03,0,0.03]),az,el,d); render(f'{out}_{v}.png')
