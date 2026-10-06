import sys; sys.path.insert(0,'/home/user/r97/tools')
import bpy, numpy as np, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
from hgpt_pose import *
P=Poser()
def local_q(n):
    pb=P.pb(n); return pb.matrix_basis.to_quaternion() if not pb.constraints else (P.rig.data.bones[n].matrix_local.inverted() @ P.rig.data.bones[n].parent.matrix_local @ (P.pb(P.rig.data.bones[n].parent.name).matrix.inverted() @ pb.matrix)).to_quaternion()
def swing_twist(q):
    tw = math.degrees(2*math.atan2(q.y, q.w)); 
    from mathutils import Quaternion
    qt = Quaternion((math.cos(math.radians(tw)/2),0,math.sin(math.radians(tw)/2),0)); sw = q @ qt.inverted()
    return math.degrees(sw.angle), tw
for plane,th,ax in (('abduction',90,0),('flexion',150,30),(5,80,55)):
    P.reset(); P.elevate('l',plane,th,axial=ax, horizontal=(-30 if plane==5 else 0)); bpy.context.view_layer.update()
    print(plane, th, ax, 'upperarm swing/twist %.1f/%.1f'%swing_twist(local_q('upperarm_l')), ' helper %.1f/%.1f'%swing_twist(local_q('glenohumeral_half_l')))
