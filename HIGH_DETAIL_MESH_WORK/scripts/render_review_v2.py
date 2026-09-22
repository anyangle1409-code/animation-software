import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Euler
R=Path(__file__).resolve().parents[1];poseRoot=R/'reports/poses_v2';renderRoot=R/'renders_v2'
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
   ob=bpy.context.object;local=Matrix.Translation(Vector(part.get('position',[0,0,0])))@Euler(part.get('rotation',[0,0,0]),'XYZ').to_matrix().to_4x4();ob.matrix_world=C@em@local@shape;ob.data.materials.append(metal if part['material']=='metal' else rubber)
   for f in ob.data.polygons:f.use_smooth=True
 sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Review world');sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1100;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sh=sc.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.4;sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.1;sh.curvature_valley_factor=.7;sh.background_type='WORLD';sc.world.color=(.19,.21,.24);sc.view_settings.view_transform='Standard';sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
 ca=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',ca);bpy.context.collection.objects.link(cam);sc.camera=cam;ca.type='ORTHO'
 return d,sc,cam
def render(p,views):
 d,sc,cam=build(p)
 positions=d['meshes'][0]['positions'];lo=min(v[1] for v in positions);hi=max(v[1] for v in positions);mid=(lo+hi)/2;extent=max(hi-lo,1.0)
 for name in views:
  focus=Vector((0,0,mid));scale=extent*1.2
  direction=Vector({'front':(0,-5,.12),'side':(5,0,.12),'three_quarter':(4,-6,1),'back':(0,5,.12),'shoulder_side':(5,0,.12),'shoulder_three_quarter':(4,-6,.5),'hand':(4,-6,.5)}[name])
  if name.startswith('shoulder'):focus=Vector((.19,.025,1.405));scale=.50
  if name=='hand':focus=Vector((.21,-.30,1.10));scale=.45
  if d['exercise']=='Push-Up':focus=Vector((0,-.55,.48));scale=1.85
  cam.location=focus+direction;cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  nameOut=f'{p.stem}_{name}';sc.render.filepath=str(renderRoot/f'{nameOut}.png');bpy.ops.render.render(write_still=True);print('RENDER',nameOut,flush=True)
 # Save the exact posed scene separately from the editable rigged candidate.
 if 'candidate' in p.stem and d['label']=='peak':bpy.ops.wm.save_as_mainfile(filepath=str(R/'checkpoints'/f'V2_{p.stem}_REVIEW_POSE.blend'))
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'initial'
if mode=='initial':
 for who in ['baseline','candidate']:render(poseRoot/f'dumbbell_bicep_curl_bottom_{who}.json',['side','shoulder_side','shoulder_three_quarter'])
else:
 for p in sorted(poseRoot.glob('*candidate.json')):
  d=json.loads(p.read_text())
  if d['label']=='return':continue
  views=['three_quarter']
  if d['exercise']=='Dumbbell Bicep Curl' and d['label']=='bottom':views=['front','side','three_quarter','back','shoulder_side','shoulder_three_quarter']
  elif d['label']=='peak':views=['front','side','three_quarter']
  render(p,views)


