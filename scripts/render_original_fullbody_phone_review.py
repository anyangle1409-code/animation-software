"""Read-only, source-pinned ORIGINAL-v1 neutral review. Never saves native source."""
import bpy, sys, json, hashlib, math, time
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import original_v1_functional_fullbody as bridge
OUT = Path(sys.argv[sys.argv.index('--')+1]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
SOURCE_SHA = '670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56'
COMMIT = '2af63aedc3ff1c8c5de4974b4e826ec6ce26d81b'
source = Path(bpy.data.filepath).resolve()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source) == SOURCE_SHA, 'Wrong native model bytes'
scene = bpy.context.scene
assert scene.get('hgpt_asset_id') == 'HomeGymPT_Male_ORIGINAL_v1'
assert scene.get('hgpt_legacy_geometry_imported') is False
body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
anatomy = bpy.data.objects['HGPT_ANATOMICAL_MASTER']
inventory = bridge.validate_blender_bridge(anatomy, rig, body)
assert not inventory['errors'], inventory['errors']
def skeleton_record():
    return {o.name:{'world':list(sum((list(r) for r in o.matrix_world),[])),
        'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),
        'matrix':list(sum((list(r) for r in b.matrix_local),[]))} for b in o.data.bones}}
        for o in (rig, anatomy)}
before = skeleton_record()
base_vertex_hash = hashlib.sha256(json.dumps([list(v.co) for v in body.data.vertices]).encode()).hexdigest()
# Same neutral definition as existing source pose tests: identity runtime basis.
for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
neutral_keys = {}
if body.data.shape_keys:
    for k in body.data.shape_keys.key_blocks:
        neutral_keys[k.name] = k.value
        if k.name.startswith('HGPT_SHOULDER_'): k.value = 0
for o in scene.objects:
    if o.type in {'MESH','CURVE','ARMATURE','EMPTY'} and o is not body: o.hide_render = True
body.hide_render = False
body.hide_set(False)
bpy.context.view_layer.update()
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
points = [ev.matrix_world @ v.co for v in ev.data.vertices]
lo = [min(p[i] for p in points) for i in range(3)]
hi = [max(p[i] for p in points) for i in range(3)]
target, scale = bridge.frame_from_bounds(lo,hi,1.15)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_percentage = 100
scene.render.resolution_x = 1600
scene.render.resolution_y = 2400
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
sh = scene.display.shading
sh.light = 'STUDIO'
sh.studiolight_rotate_z = 0.35
sh.color_type = 'SINGLE'
sh.single_color = (0.63,0.66,0.69)
sh.show_shadows = True
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.show_specular_highlight = True
sh.background_type = 'WORLD'
if scene.world is None: scene.world = bpy.data.worlds.new('REVIEW_ONLY_WORLD')
scene.world.color = (0.055,0.065,0.085)
camdata = bpy.data.cameras.new('REVIEW_ONLY_CAMERA')
camdata.type = 'ORTHO'
cam = bpy.data.objects.new('REVIEW_ONLY_CAMERA',camdata)
scene.collection.objects.link(cam)
scene.camera = cam
# +X is anatomical left, front is -Y in source Z-up frame.
views = {'front':(0,-4,0),'rear':(0,4,0),'left_side':(4,0,0),
         'right_side':(-4,0,0),'left_three_quarter':(3,-3,0),
         'right_three_quarter':(-3,-3,0),'rear_three_quarter':(3,3,0)}
records = []
def render(name, centre, ortho, offset, width=1600, height=2400):
    scene.render.resolution_x,scene.render.resolution_y = width,height
    camdata.ortho_scale = ortho
    c = Vector(centre)
    cam.location = c + Vector(offset)
    cam.rotation_euler = (c-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = str(OUT/(name+'.png'))
    image_path=Path(scene.render.filepath)
    complete = image_path.exists() and image_path.read_bytes().endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82')
    if not complete:
        temporary_path=image_path.with_name(image_path.stem+'.tmp.png')
        scene.render.filepath=str(temporary_path)
        bpy.ops.render.render(write_still=True)
        for attempt in range(50):
            if temporary_path.read_bytes().endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'): break
            time.sleep(0.1)
        else: raise RuntimeError('PNG not fully written: '+name)
        temporary_path.replace(image_path)
        scene.render.filepath=str(image_path)
    records.append({'file':name+'.png','target':list(c),'ortho_scale':ortho,
                    'camera_world':list(sum((list(r) for r in cam.matrix_world),[])),
                    'resolution':[width,height],'source_body':body.name})
for name, offset in views.items(): render('neutral_'+name,target,scale,offset)
# Detail crops use the same unmodified posed vertices; no anatomical shape edits.
def detail(name, pred, offset):
    pts=[p for p in points if pred(p)]
    assert len(pts)>20, name
    ll=[min(p[i] for p in pts) for i in range(3)]
    hh=[max(p[i] for p in pts) for i in range(3)]
    cc,ss=bridge.frame_from_bounds(ll,hh,1.3)
    render(name,cc,ss,offset,2000,2000)
detail('detail_shoulders_armpits_front',lambda p:1.25<p.z<1.6,(0,-4,0))
detail('detail_shoulders_armpits_rear',lambda p:1.25<p.z<1.6,(0,4,0))
for side, sign, suffix in [('left',1,'r'),('right',-1,'l')]:
    hh = rig.matrix_world @ rig.data.bones['hand_'+suffix].head_local
    tt = rig.matrix_world @ rig.data.bones['middle_03_'+suffix].tail_local
    centre = (hh+tt)/2
    render('detail_'+side+'_hand',centre,0.30,(sign*4,0,0),2000,2000)
    render('detail_'+side+'_hand_front',centre,0.30,(0,-4,0),2000,2000)
detail('detail_knees_front',lambda p:0.38<p.z<0.66,(0,-4,0))
detail('detail_knees_side',lambda p:0.38<p.z<0.66,(4,0,0))
detail('detail_feet_front',lambda p:p.z<0.18,(0,-4,0))
detail('detail_feet_side',lambda p:p.z<0.18,(4,0,0))
# Separate review-only GLB: actual original body and its existing runtime, no diagnostics.
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True); rig.hide_set(False); rig.hide_render=False; rig.select_set(True)
bpy.context.view_layer.objects.active=body
glb=OUT/'HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,
    export_animations=False,export_extras=True,export_cameras=False,export_lights=False)
# Source bone control display generated from unchanged anatomical head/tail records.
# These are control guides, explicitly not anatomical bone surface meshes.
body.hide_render=True
rig.hide_render=True
guides=[]
for b in anatomy.data.bones:
    h=anatomy.matrix_world@b.head_local; t=anatomy.matrix_world@b.tail_local
    if (t-h).length<1e-6: continue
    curve=bpy.data.curves.new('REVIEW_GUIDE_'+b.name,'CURVE')
    curve.dimensions='3D'; curve.bevel_depth=0.002; curve.bevel_resolution=2
    sp=curve.splines.new('POLY'); sp.points.add(1)
    sp.points[0].co=(*h,1); sp.points[1].co=(*t,1)
    obj=bpy.data.objects.new(curve.name,curve); scene.collection.objects.link(obj); guides.append(obj)
sh.single_color=(0.88,0.72,0.26)
for name in ('front','rear','left_side','right_side'):
    render('source_206_guides_'+name,target,scale,views[name])
assert before==skeleton_record(), 'Skeleton geometry changed'
assert sha(source)==SOURCE_SHA
assert base_vertex_hash==hashlib.sha256(json.dumps([list(v.co) for v in body.data.vertices]).encode()).hexdigest()
manifest={'source_branch':'codex/functional-original-fullbody-bridge-20261011',
 'source_commit':COMMIT,'source_model_filename':source.name,'source_model_sha256':SOURCE_SHA,
 'asset_id':scene['hgpt_asset_id'],'candidate_revision':scene['hgpt_candidate_revision'],
 'blender_version':bpy.app.version_string,'inventory':inventory,'body_vertex_coordinate_sha256':base_vertex_hash,
 'neutral_definition':'Identity runtime pose basis; existing HGPT_SHOULDER corrective keys zero; original mesh unchanged',
 'original_key_values':neutral_keys,'world_bounds':[lo,hi],'fullbody_camera_scale':scale,
 'anatomical_left_axis':'+X','character_forward_axis':'-Y','skeleton_geometry_unchanged':before==skeleton_record(),
 'renders':records,'export_hashes':{p.name:sha(p) for p in OUT.iterdir() if p.suffix in ('.png','.glb')},
 'anatomically_validated':False,'production_ready':False,
 'limitations':['Complete body coverage, not a completed production character.',
 'Static separate 206-bone anatomical armature does not drive body; existing 67-bone runtime does.',
 '206-bone overlay shows unchanged control endpoints, not qualified anatomical bone surfaces.',
 'Neutral renders do not validate motion, contact, proportions or deformation.',
 'Workbench neutral clay lighting used for shape review; not final skin material or clothing.',
 'Original r95 shoulder/axilla corrections and unresolved source registration remain provisional.']}
(OUT/'review_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('REVIEW_COMPLETE',len(records),'renders; source and skeleton unchanged')
