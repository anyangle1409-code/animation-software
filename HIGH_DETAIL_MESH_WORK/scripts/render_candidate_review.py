"""Generic topology-tolerant Blender renderer for candidate review pose JSON."""

from __future__ import annotations
import bpy,json,math,os,sys
from pathlib import Path
from mathutils import Vector,Matrix,Euler

R=Path(__file__).resolve().parents[1]
version=os.environ.get("RENDER_VERSION","v6_knee_seam")
poseRoot=R/f"reports/poses_{version}"
renderRoot=R/f"renders_{version}"
renderRoot.mkdir(exist_ok=True)
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))

def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m

def paired_baseline(path):
    q=Path(str(path).replace("_candidate.json","_baseline.json"))
    return json.loads(q.read_text()) if q.is_file() else None

def build(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    d=json.loads(p.read_text())
    skin=material("Skin review clay",(.53,.34,.25))
    shorts=material("Frozen shorts",(.035,.045,.065))
    metal=material("Handle",(.38,.42,.47));rubber=material("Equipment",(.04,.05,.065))
    for item in d["meshes"]:
        me=bpy.data.meshes.new(item["name"])
        verts=[(x,-z,y) for x,y,z in item["positions"]]
        idx=item["indices"];me.from_pydata(verts,[],[idx[i:i+3] for i in range(0,len(idx),3)]);me.update()
        ob=bpy.data.objects.new(item["name"],me);bpy.context.collection.objects.link(ob)
        ob.data.materials.append(shorts if "short" in item["name"].lower() else skin)
        for f in me.polygons:f.use_smooth=True
    for eq in d["equipment"]:
        em=Matrix([eq["matrix"][i:i+4] for i in range(0,16,4)]).transposed()
        for part in eq.get("parts",[]):
            if part["shape"]=="cylinder":
                bpy.ops.mesh.primitive_cone_add(vertices=part.get("segments",32),radius1=part["radius"],radius2=part.get("radiusTop",part["radius"]),depth=part["length"]);shape=Matrix.Rotation(-math.pi/2,4,"X")
            elif part["shape"]=="box":
                bpy.ops.mesh.primitive_cube_add(size=1);shape=Matrix.Diagonal((*part["size"],1))
            elif part["shape"]=="sphere":
                bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=part["radius"]);shape=Matrix.Identity(4)
            else: continue
            ob=bpy.context.object;ob["review_equipment"]=True
            ob["review_vertical_support"]=part["shape"]=="box" and part["size"][1]>1.0
            local=Matrix.Translation(Vector(part.get("position",[0,0,0])))@Euler(part.get("rotation",[0,0,0]),"XYZ").to_matrix().to_4x4()
            ob.matrix_world=C@em@local@shape
            ob.data.materials.append(metal if part["material"]=="metal" else rubber)
            for f in ob.data.polygons:f.use_smooth=True
    sc=bpy.context.scene;sc.world=bpy.data.worlds.new("Review world")
    sc.render.engine="BLENDER_WORKBENCH";sc.render.resolution_x=1100;sc.render.resolution_y=1200;sc.render.resolution_percentage=100
    sh=sc.display.shading;sh.light="STUDIO";sh.studiolight_rotate_z=.4;sh.color_type="MATERIAL";sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type="BOTH";sh.curvature_ridge_factor=1.1;sh.curvature_valley_factor=.7;sh.background_type="WORLD"
    sc.world.color=(.19,.21,.24);sc.view_settings.view_transform="Standard";sc.render.image_settings.file_format="PNG";sc.render.film_transparent=False
    ca=bpy.data.cameras.new("Review camera");cam=bpy.data.objects.new("Review camera",ca);bpy.context.collection.objects.link(cam);sc.camera=cam;ca.type="ORTHO"
    return d,sc,cam

def reference_focus(p,kind):
    base=paired_baseline(p)
    source=base if base else json.loads(p.read_text())
    positions=source["meshes"][0]["positions"]
    if kind=="hand":
        ownership=json.loads((R/"reports/sculpt_reference.json").read_text())["ownership"]
        ids=[i for i,w in enumerate(ownership) if w["hand"]>.8 and positions[i][0]>0 and i<len(positions)]
    elif kind=="knee":
        seam=json.loads((R/"reports/knee_seam_v5.json").read_text())["knees"]["L"]["paths"]
        ids=[i for path in seam for i in path if i<len(positions)]
    elif kind=="shoulder":
        ids=[3913] if len(positions)>3913 else []
    else:
        ids=[]
    if not ids:return None
    x=sum(positions[i][0] for i in ids)/len(ids)
    y=sum(positions[i][1] for i in ids)/len(ids)
    z=sum(positions[i][2] for i in ids)/len(ids)
    return Vector((x,-z,y))

def render(p,views):
    d,sc,cam=build(p);positions=d["meshes"][0]["positions"]
    lo=min(v[1] for v in positions);hi=max(v[1] for v in positions);mid=(lo+hi)/2;extent=max(hi-lo,1.0)
    for name in views:
        focus=Vector((0,0,mid));scale=extent*1.2
        direction=Vector({"front":(0,-5,.12),"side":(5,0,.12),"three_quarter":(4,-6,1),"back":(0,5,.12),"shoulder_side":(5,0,.12),"shoulder_three_quarter":(4,-6,.5),"hand":(4,-6,.5),"hand_back":(4,6,.8),"hand_side":(5,0,.5),"hand_web":(5,-5,3),"knee_front":(0,-5,.12),"knee_side":(5,0,.12),"knee_three_quarter":(4,-6,.5)}[name])
        if name.startswith("shoulder"):
            focus=reference_focus(p,"shoulder") or focus;scale=.50
        elif name.startswith("hand"):
            focus=reference_focus(p,"hand") or focus;scale=.20 if name=="hand_web" else .34
        elif name.startswith("knee"):
            focus=reference_focus(p,"knee") or focus;scale=.38
        if d["exercise"]=="Push-Up" and name!="hand":focus=Vector((0,-.55,.48));scale=1.85
        for ob in sc.objects:
            if ob.get("review_equipment"):ob.hide_render=name.startswith("shoulder") or (d["exercise"]=="Pull-Up" and name.startswith("hand") and ob.get("review_vertical_support"))
        cam.location=focus+direction;cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler();cam.data.ortho_scale=scale
        out=f"{p.stem}_{name}";sc.render.filepath=str(renderRoot/f"{out}.png");bpy.ops.render.render(write_still=True);print("RENDER",out,flush=True)
    if "candidate" in p.stem and d["label"]=="peak":
        (R/"checkpoints").mkdir(exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(R/"checkpoints"/f"{version.upper()}_{p.stem}_REVIEW_POSE.blend"))

mode=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "all"
if mode=="hands":
    for exercise,label in [("dumbbell_bicep_curl","bottom"),("push_up","bottom"),("pull_up","peak")]:
        p=poseRoot/f"{exercise}_{label}_candidate.json"
        if p.exists():render(p,["hand"])
elif mode=="hands_compare":
    for exercise,label in [("dumbbell_bicep_curl","bottom"),("push_up","bottom"),("pull_up","peak")]:
        for kind in ("baseline","candidate"):
            p=poseRoot/f"{exercise}_{label}_{kind}.json"
            if p.exists():render(p,["hand","hand_back"] if exercise=="pull_up" else ["hand"])
elif mode=="hand_studies":
    for label,views in (("open_hand",["hand","hand_back","hand_web"]),
                        ("closed_fist",["hand","hand_back","hand_side"])):
        for kind in ("baseline","candidate"):
            p=poseRoot/f"{label}_review_{kind}.json"
            if p.exists():render(p,views)
elif mode=="knees":
    p=poseRoot/"air_squat_peak_candidate.json"
    if p.exists():render(p,["knee_front","knee_side","knee_three_quarter"])
elif mode=="target":
    for exercise in ["dumbbell_shoulder_press","pull_up"]:
        p=poseRoot/f"{exercise}_peak_candidate.json"
        if p.exists():render(p,["shoulder_side","shoulder_three_quarter"])
elif mode=="pullup_hands":
    p=poseRoot/"pull_up_peak_candidate.json"
    if p.exists():render(p,["hand","hand_back","hand_side"])
else:
    for p in sorted(poseRoot.glob("*candidate.json")):
        d=json.loads(p.read_text())
        if d["label"]=="return":continue
        views=["three_quarter"]
        if d["exercise"]=="Dumbbell Bicep Curl" and d["label"]=="bottom":
            views=["front","side","three_quarter","back","shoulder_side","shoulder_three_quarter"]
        elif d["label"]=="peak":views=["front","side","three_quarter"]
        render(p,views)
