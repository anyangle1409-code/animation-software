import bpy,json,math,os,sys
from pathlib import Path
from mathutils import Vector,Matrix,Euler
R=Path(__file__).resolve().parents[1];version=os.environ.get('RENDER_VERSION','v3');poseRoot=R/f'reports/poses_{version}';renderRoot=R/f'renders_{version}';renderRoot.mkdir(exist_ok=True)
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
def build(p):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 d=json.loads(p.read_text());skin=material('Skin review clay',(.53,.34,.25));shorts=material('Frozen shorts',(.035,.045,.065));metal=material('Handle',(.38,.42,.47));rubber=material('Equipment',(.04,.05,.065))
 for item in d['meshes']:
  me=bpy.data.meshes.new(item['name']);verts=[(x,-z,y) for x,y,z in item['positions']];idx=item['indices'];me.from_pydata(verts,[],[idx[i:i+3] for i in range(0,len(idx),3)]);me.update();ob=bpy.data.objects.new(item['name'],me);bpy.context.collection.objects.link(ob);ob.data.materials.append(shorts if 'short' in item['name'].lower() else skin)
  for f in me.polygons:f.use_smooth=True
 for eq in d['equipment']:
  em=Matrix([eq['matrix'][i:i+4] for i in range(0,16,4)]).transposed()
  for part in eq.get('parts',[]):
   if part['shape']=='cylinder':
    bpy.ops.mesh.primitive_cone_add(vertices=part.get('segments',32),radius1=part['radius'],radius2=part.get('radiusTop',part['radius']),depth=part['length']);shape=Matrix.Rotation(-math.pi/2,4,'X')
   elif part['shape']=='box':
    bpy.ops.mesh.primitive_cube_add(size=1);shape=Matrix.Diagonal((*part['size'],1))
   elif part['shape']=='sphere':bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=part['radius']);shape=Matrix.Identity(4)
   else:continue
   ob=bpy.context.object;ob['review_equipment']=True;local=Matrix.Translation(Vector(part.get('position',[0,0,0])))@Euler(part.get('rotation',[0,0,0]),'XYZ').to_matrix().to_4x4();ob.matrix_world=C@em@local@shape;ob.data.materials.append(metal if part['material']=='metal' else rubber)
   for f in ob.data.polygons:f.use_smooth=True
 sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Review world');sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1100;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sh=sc.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.4;sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.1;sh.curvature_valley_factor=.7;sh.background_type='WORLD';sc.world.color=(.19,.21,.24);sc.view_settings.view_transform='Standard';sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
 ca=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',ca);bpy.context.collection.objects.link(cam);sc.camera=cam;ca.type='ORTHO'
 return d,sc,cam
def render(p,views):
 d,sc,cam=build(p)
 positions=d['meshes'][0]['positions'];lo=min(v[1] for v in positions);hi=max(v[1] for v in positions);mid=(lo+hi)/2;extent=max(hi-lo,1.0)
 for name in views:
  focus=Vector((0,0,mid));scale=extent*1.2
  direction=Vector({'front':(0,-5,.12),'side':(5,0,.12),'three_quarter':(4,-6,1),'back':(0,5,.12),'shoulder_side':(5,0,.12),'shoulder_three_quarter':(4,-6,.5),'hand':(4,-6,.5),'knee_front':(0,-5,.12),'knee_side':(5,0,.12),'knee_three_quarter':(4,-6,.5)}[name])
  if name.startswith('shoulder'):
   joint_near=d['meshes'][0]['positions'][3913]
   focus=Vector((joint_near[0]-.02,-joint_near[2],joint_near[1]));scale=.50
  if name=='hand':
   ownership=json.loads((R/'reports/sculpt_reference.json').read_text())['ownership']
   ids=[i for i,w in enumerate(ownership) if w['hand']>.8 and positions[i][0]>0]
   n=len(ids);focus=Vector((sum(positions[i][0] for i in ids)/n,-sum(positions[i][2] for i in ids)/n,sum(positions[i][1] for i in ids)/n));scale=.34
  if name.startswith('knee'):
   joint=json.loads((R/'reports/squat_sculpt_reference_v5.json').read_text())['knees']['L']
   focus=Vector((joint[0],-joint[2],joint[1]));scale=.38
  if d['exercise']=='Push-Up' and name!='hand':focus=Vector((0,-.55,.48));scale=1.85
  for ob in sc.objects:
   if ob.get('review_equipment'):ob.hide_render=name.startswith('shoulder')
  cam.location=focus+direction;cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  nameOut=f'{p.stem}_{name}';sc.render.filepath=str(renderRoot/f'{nameOut}.png');bpy.ops.render.render(write_still=True);print('RENDER',nameOut,flush=True)
 # Save the exact posed scene separately from the editable rigged candidate.
 if 'candidate' in p.stem and d['label']=='peak':bpy.ops.wm.save_as_mainfile(filepath=str(R/'checkpoints'/f'{version.upper()}_{p.stem}_REVIEW_POSE.blend'))
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'initial'
if mode=='initial':
 for who in ['baseline','candidate']:render(poseRoot/f'dumbbell_bicep_curl_bottom_{who}.json',['side','shoulder_side','shoulder_three_quarter'])
elif mode=='target':
 for exercise in ['dumbbell_shoulder_press','pull_up']:
  render(poseRoot/f'{exercise}_peak_candidate.json',['shoulder_side','shoulder_three_quarter'])
elif mode=='hands':
 for exercise,label in [('dumbbell_bicep_curl','bottom'),('push_up','bottom'),('pull_up','peak')]:
  render(poseRoot/f'{exercise}_{label}_candidate.json',['hand'])
elif mode=='knees':
 render(poseRoot/'air_squat_peak_candidate.json',['knee_front','knee_side','knee_three_quarter'])
elif mode=='overhead':
 for exercise in ['dumbbell_shoulder_press','pull_up']:
  for label in ['bottom','sample_12','peak']:
   for who in ['baseline','candidate']:
    p=poseRoot/f'{exercise}_{label}_{who}.json'
    if p.exists():render(p,['shoulder_side','shoulder_three_quarter'])
else:
 for p in sorted(poseRoot.glob('*candidate.json')):
  d=json.loads(p.read_text())
  if d['label']=='return':continue
  views=['three_quarter']
  if d['exercise']=='Dumbbell Bicep Curl' and d['label']=='bottom':views=['front','side','three_quarter','back','shoulder_side','shoulder_three_quarter']
  elif d['label']=='peak':views=['front','side','three_quarter']
  render(p,views)


