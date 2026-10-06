import sys; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out=argv[1]
from hgpt_pose import *
P=Poser(); cam=setup_render(800)
for o in bpy.data.objects:
    if o.type=='MESH' and 'SHORTS' in o.name: o.hide_render=True
for m in P.body.modifiers:
    if m.type=='MASK': m.show_render=False
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
# overlay wireframe: duplicate body with wireframe modifier, dark
dup=P.body.copy(); dup.data=P.body.data; sc.collection.objects.link(dup)
w=dup.modifiers.new('W','WIREFRAME'); w.thickness=0.0012; w.use_replace=True
mat=bpy.data.materials.new('dark'); mat.diffuse_color=(0.05,0.05,0.08,1); dup.data.materials.append(mat) if False else None
dup.color=(0.05,0.05,0.1,1)
sc.display.shading.color_type='OBJECT'; P.body.color=(0.75,0.7,0.65,1)
for th,name in ((0,'rest'),(170,'flex170'),(150,'abd150')):
    P.reset()
    if th: [P.elevate(s,'flexion' if name.startswith('flex') else 'abduction',th) for s in 'lr']
    c=np.array(P.pb('upperarm_l').head)
    for v,(az,el) in {'front':(30,5),'axilla':(80,-25),'rear':(150,8)}.items():
        look(cam, c+np.array([0.04,0,-0.08]), az, el, 0.7); render(f'{out}/wire_{name}_{v}.png')
