import sys
sys.path.insert(0, '/home/user/r97/tools')
import bpy, numpy as np
argv = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = argv[1]; groups = argv[2].split(','); plane, th = argv[3], float(argv[4])
from hgpt_pose import *
P = Poser(); P.set_correctives(0.0); cam = setup_render(500)
for o in bpy.data.objects:
    if o.type=='MESH' and 'SHORTS' in o.name: o.hide_render=True
for m in P.body.modifiers:
    if m.type=='MASK': m.show_render=False
me = P.body.data; n=len(me.vertices); idx = {g.name: g.index for g in P.body.vertex_groups}
def weights(name):
    w = np.zeros(n); gi = idx[name]
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi: w[v.index] = g.weight
    return w
ca = me.color_attributes.get('WV') or me.color_attributes.new('WV', 'FLOAT_COLOR', 'POINT')
bpy.context.scene.display.shading.color_type = 'VERTEX'; me.color_attributes.active_color = ca
def ramp(w):
    w = np.clip(w,0,1); c = np.ones((len(w),4)); c[:,0]=np.clip(2*w,0,1); c[:,1]=np.clip(1-abs(w-0.5)*2,0,1); c[:,2]=np.clip(1-2*w,0,1)
    c[w<1e-4] = (0.55,0.55,0.55,1); return c
P.reset()
for s in 'lr': P.elevate(s, plane, th)
c = np.array(P.pb('upperarm_l').head)
for g in groups:
    ca.data.foreach_set('color', ramp(weights(g)).ravel())
    for view,(az,el) in {'front':(25,8),'axilla':(75,-20),'rear':(150,10)}.items():
        look(cam, c+np.array([0.02,0,-0.06]), az, el, 0.95); render(f'{out}/{plane}{int(th)}_{g}_{view}.png')
