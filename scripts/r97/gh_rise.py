import sys; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
from hgpt_pose import *
P=Poser()
for plane in ('abduction','flexion'):
  for th in (0,90,150,170):
    P.reset(); P.elevate('l',plane,th)
    gh=np.array(P.pb('upperarm_l').head); ac=np.array(P.pb('clavicle_l').tail)
    print(plane, th, 'GH', gh.round(3), 'clav tip', ac.round(3))
