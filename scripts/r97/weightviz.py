import sys
sys.path.insert(0, '/home/user/r97/tools')
import bpy, numpy as np
argv = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = argv[1]; groups = argv[2].split(',')
from hgpt_pose import *
P = Poser(); P.set_correctives(0.0); cam = setup_render(600)
me = P.body.data
idx = {g.name: g.index for g in P.body.vertex_groups}
n = len(me.vertices)
def weights(name):
    w = np.zeros(n); gi = idx[name]
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi: w[v.index] = g.weight
    return w
ca = me.color_attributes.get('WV') or me.color_attributes.new('WV', 'FLOAT_COLOR', 'POINT')
sc = bpy.context.scene; sc.display.shading.color_type = 'VERTEX'; me.color_attributes.active_color = ca
def ramp(w):
    w = np.clip(w,0,1); c = np.zeros((len(w),4)); c[:,3]=1
    c[:,0] = np.clip(2*w,0,1); c[:,1] = np.clip(2-2*abs(2*w-1)-1+ (w<0.5)*0,0,1)*0+np.clip(1-abs(w-0.5)*2,0,1); c[:,2]=np.clip(1-2*w,0,1)
    c[w<1e-4] = (0.55,0.55,0.55,1)
    return c
for g in groups:
    w = weights(g); ca.data.foreach_set('color', ramp(w).ravel())
    for view,(az,el,tgt,dist) in {'front':(25,5,(-0.18,0,1.38),1.0),'rear':(155,5,(-0.18,0,1.38),1.0),'side':(90,0,(-0.18,0,1.38),1.0),'under':(70,-35,(-0.18,0,1.38),1.0)}.items():
        look(cam, tgt, az, el, dist); render(f'{out}/w_{g}_{view}.png')
