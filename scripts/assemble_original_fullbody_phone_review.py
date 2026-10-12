"""Label and assemble existing authentic Blender PNGs; no generative changes."""
from PIL import Image, ImageDraw, ImageFont, ImageChops
from pathlib import Path
import json, hashlib, sys, math
import numpy as np
out=Path(sys.argv[1]).resolve()
manifest=json.loads((out/'review_manifest.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in manifest['export_hashes'].items(): assert sha(out/name)==h,name
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,30)
small=ImageFont.truetype(fontpath,23)
titlefont=ImageFont.truetype(fontpath,38)
def save_image(im,path):
    tmp=path.with_suffix('.tmp')
    im.save(tmp,format='PNG')
    tmp.replace(path)
overlays=[]
for view in ('front','rear','left_side','right_side'):
    body=Image.open(out/('neutral_'+view+'.png')).convert('RGB')
    skeleton=Image.open(out/('source_206_guides_'+view+'.png')).convert('RGB')
    assert body.size==skeleton.size
    a=np.asarray(skeleton).astype(int)
    bg=a[0,0,:]
    mask=(np.max(np.abs(a-bg),axis=2)>12).astype('uint8')*255
    muted=Image.blend(Image.new('RGB',body.size,tuple(bg)),body,0.30)
    overlay=Image.composite(skeleton,muted,Image.fromarray(mask))
    name='skeleton_overlay_'+view+'.png'
    save_image(overlay,out/name)
    overlays.append(name)
full=['neutral_'+n+'.png' for n in ('front','rear','left_side','right_side','left_three_quarter','right_three_quarter')]
details=[r['file'] for r in manifest['renders'] if r['file'].startswith('detail_')]
def sheet(names,filename,title,tile_height=1040):
    width=1600; rows=math.ceil(len(names)/2)
    result=Image.new('RGB',(width,210+rows*tile_height),(19,26,36))
    draw=ImageDraw.Draw(result)
    draw.text((30,22),title,font=titlefont,fill='white')
    draw.text((30,78),'ACTUAL ORIGINAL_v1 r95 body | provisional | 12 Oct 2026',font=font,fill='#e5b86a')
    draw.text((30,126),'Work source commit 2af63aedc3ff | skeleton unchanged | neutral rest',font=small,fill='#b4c1d1')
    draw.text((30,164),'Guide overlays show source control rods; no anatomical acceptance.',font=small,fill='#b4c1d1')
    for i,name in enumerate(names):
        x=(i%2)*800; y=210+(i//2)*tile_height
        label=name.removesuffix('.png').replace('_',' ').title()
        draw.text((x+22,y+12),label,font=font,fill='white')
        im=Image.open(out/name).convert('RGB')
        im.thumbnail((770,tile_height-74),Image.Resampling.LANCZOS)
        result.paste(im,(x+(800-im.width)//2,y+60+(tile_height-74-im.height)//2))
    save_image(result,out/filename)
    return filename
sheet(full,'ORIGINAL_v1_FULL_BODY_CONTACT_SHEET.png','Home Gym PT | full-body review')
sheet(details,'ORIGINAL_v1_JOINT_DETAIL_CONTACT_SHEET.png','Home Gym PT | joint details',860)
sheet(overlays,'ORIGINAL_v1_SKELETON_OVERLAY_CONTACT_SHEET.png','Home Gym PT | source skeleton guides')
sheet(full+['neutral_rear_three_quarter.png']+details+overlays,
    'ORIGINAL_v1_ALL_VIEWS_PHONE_CONTACT_SHEET.png','Home Gym PT | complete visual review',900)
manifest['derived_images']={p.name:sha(p) for p in out.glob('*.png') if p.name not in manifest['export_hashes']}
manifest['visual_findings']=[
 {'id':'VIS-001','region':'neck/shoulder','finding':'Visible planar/faceted neck-to-trapezius transitions and angular deltoid silhouette.'},
 {'id':'VIS-002','region':'hands','finding':'Rounded tubular digits and simplified palm/thumb web; fine joint, nail and skin detail remains incomplete.'},
 {'id':'VIS-003','region':'feet','finding':'Faceted heel/ankle transition, simplified toes and shallow visible arch; anatomical proportion acceptance still open.'},
 {'id':'VIS-004','region':'head/torso/knees','finding':'Simplified face and broad stylised torso/knee surfaces; not finished high-detail human skin.'},
 {'id':'VIS-005','region':'whole body','finding':'Neutral standing views alone cannot verify deformation, loaded motion, skeleton-to-skin registration or contact.'}]
(out/'review_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('VERIFIED',len(manifest['export_hashes']),'original exports;',len(manifest['derived_images']),'derived PNGs')
