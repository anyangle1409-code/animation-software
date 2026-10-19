"""Before/after of a controlled helper pose experiment. Never call it a repair."""
import sys,json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def main(capture,root):
    capture,root=Path(capture),Path(root);summary=dict(diagnostic_only=True,model_saved=False,repair_complete=False,modes={})
    base41=np.load(capture/'r41/clip.npz')['back_points']
    acceleration=lambda p:np.linalg.norm(np.diff(p.astype(float),n=2,axis=0),axis=2)
    ba=acceleration(base41)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    for mode in ('r41','r52'):
        report=json.loads((root/mode/'origin_probe.json').read_text());data=np.load(root/mode/'probe.npz');old=np.load(capture/mode/'clip.npz')
        expected={'runtime_rest','anatomy_rest','weights','groups','polygons','all_key_geometry'}
        if report['samples']!=161 or set(report['protected_identity'])!=expected or not all(report['protected_identity'].values()) or report['maximum_nonlat_pose_difference']!=0:
            raise ValueError('Incomplete protected probe identity')
        p=data['back_points'];q=old['back_points']
        if p.shape!=base41.shape or q.shape!=base41.shape or not np.isfinite(p).all():raise ValueError('Incomplete probe movement')
        metrics=dict(actual_approved_outline=report['actual_approved_outline'],
            baseline_original_grid_equivalent_motion_excess_mm=float(np.maximum(acceleration(q)-ba,0).max()*16000),
            probe_original_grid_equivalent_motion_excess_mm=float(np.maximum(acceleration(p)-ba,0).max()*16000),
            original_motion_guard_mm=.5,maximum_baseline_replay_error_mm=report['maximum_baseline_replay_error_mm'],protected_identity=report['protected_identity'],
            full_acceptance_and_benchmarks_run=False,limitations=report['limitations'])
        summary['modes'][mode]=metrics
        def panel(frame,views):
            im=Image.new('RGB',(1024,50+len(views)*540+34),'#202020');d=ImageDraw.Draw(im)
            d.text((8,8),f'{mode.upper()} | original / lat-origin probe | t={frame/160:.3f}',font=font,fill='white')
            for row,view in enumerate(views):
                for col,(folder,prefix,label) in enumerate(((capture/mode,'baseline','Original'),(root/mode,'probe','Origin-motion probe'))):
                    p=Image.open(folder/f'{prefix}_{frame:03d}_{view}.png').convert('RGBA');im.paste(p,(col*512,50+row*540+28),p)
                    d.text((col*512+8,50+row*540+4),f'{label} | {view}',font=font,fill='white')
            d.text((8,im.height-26),'Diagnostic only. Video: forward / reverse replay. No saved repair.',font=font,fill='white')
            return im
        for frame in (80,100,128,160):
            panel(frame,('front','rear','side','three_quarter')).save(root/f'{mode.upper()}_R53_origin_probe_t{frame:03d}_four_views.jpg',quality=94)
            panel(frame,('rear','three_quarter')).save(root/f'{mode.upper()}_R53_origin_probe_t{frame:03d}_rear_3q.jpg',quality=94)
        folder=root/f'{mode}_video_frames';folder.mkdir(exist_ok=True)
        sequence=list(range(0,161,4))+list(range(156,0,-4))
        for i,frame in enumerate(sequence):panel(frame,('rear','three_quarter')).save(folder/f'{i:03d}.png')
        subprocess.run(['ffmpeg','-y','-framerate','10','-i',str(folder/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20',str(root/f'{mode.upper()}_R53_origin_probe_press.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    (root/'r53_origin_probe_review.json').write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':main(*sys.argv[1:3])
