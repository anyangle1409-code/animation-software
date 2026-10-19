"""Package existing native evidence only. No model synthesis or cosmetic correction."""
from pathlib import Path
import sys,json,subprocess
import numpy as np
from PIL import Image,ImageDraw
from original_review_r53_diagnostics import verify_clip_identity

def main(root):
    root=Path(root);reports={m:json.loads((root/m/'diagnosis.json').read_text()) for m in ('r41','r52')}
    clips={m:np.load(root/m/'clip.npz') for m in reports}
    difference=verify_clip_identity(reports,{m:c['bone_matrices'] for m,c in clips.items()})
    summary=dict(diagnostic_only=True,model_saved=False,repair_complete=False,approved=False,bone_matrix_difference=difference,modes={})
    for m,r in reports.items():
        c=clips[m];metrics={}
        for v in r['muted_names']:
            d=c[v];step=np.diff(d,axis=0);acc=np.diff(d,n=2,axis=0)
            metrics[v]=dict(maximum_shoulder_displacement_from_baseline_mm=float(np.linalg.norm(d,axis=-1).max()*1000),
                maximum_added_step_mm=float(np.linalg.norm(step,axis=-1).max()*1000),
                maximum_added_second_difference_mm=float(np.linalg.norm(acc,axis=-1).max()*1000),
                family_present=bool(r['muted_names'][v]),note='Diagnostic ablation, not a proposed correction or acceptance result')
        summary['modes'][m]=dict(protected_identity=r['protected_identity'],modifiers=r['modifiers'],
            relative_bone_motion={n:{k:v for k,v in x.items() if k!='samples_deg'} for n,x in r['relative_bone_motion'].items()},
            ablation=metrics)
    views=('front','rear','side','three_quarter')
    def canvas(frame,scale):
        w=512*scale; header=42;label=24;im=Image.new('RGB',(2*w,header+4*(w+label)+32),'#202020');draw=ImageDraw.Draw(im)
        draw.text((8,8),f'R53 investigation: R41 / R52 | t={frame/160:.3f} | no repaired model',fill='white')
        for row,view in enumerate(views):
            for col,m in enumerate(reports):
                p=Image.open(root/m/f'baseline_{frame:03d}_{view}.png').convert('RGBA')
                p=p.resize((w,w));im.paste(p,(col*w,header+row*(w+label)+label),p)
                draw.text((col*w+8,header+row*(w+label)+4),f'{m.upper()} | {view}',fill='white')
        draw.text((8,im.height-24),'Actual Blender skin. Diagnostic comparison; no owner approval or saved repair.',fill='white')
        return im
    for frame in (80,100,128,160):canvas(frame,1).save(root/f'R41_R52_R53_diagnostic_t{frame:03d}_four_views.jpg',quality=94)
    video=root/'video_frames';video.mkdir(exist_ok=True)
    for i,frame in enumerate(range(0,161,4)):canvas(frame,1).save(video/f'{i:03d}.png')
    subprocess.run(['ffmpeg','-y','-framerate','10','-i',str(video/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20',str(root/'R53_R41_R52_diagnostic_press.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    (root/'r53_diagnostic_review.json').write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':main(sys.argv[1])
