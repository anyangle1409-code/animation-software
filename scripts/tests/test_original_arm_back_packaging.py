"""A failed identity check must not leave an affirmative comparison graphic."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
from PIL import Image

class Packaging(unittest.TestCase):
 def test_mismatched_bones_cannot_produce_same_pose_montage(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for mode in ('r41','r41_no_s5','r41_no_s7','r41_no_s5_s7','r52'):
    p=root/mode;p.mkdir();bones=np.zeros((161,1,2,3));mat=np.broadcast_to(np.eye(4),(161,1,4,4)).copy()
    if mode=='r52':bones[128,0,0,0]=.001;mat[128,0,0,3]=.001
    np.savez_compressed(p/'motion.npz',back_points=np.zeros((161,1,3)),bone_endpoints=bones,bone_matrices=mat)
    frames=(64,80,100,128,160);views=('back','three_quarter')
    (p/'state.json').write_text(json.dumps(dict(bone_names=['spine_03'],protected_identity={'bones':True},muted_names=[],projections={f'f{i:03d}_{v}':{'spine_03':[[250,50],[250,450]]} for i in frames for v in views})))
    for i in frames:
     for v in views:Image.new('RGBA',(512,512)).save(p/f'f{i:03d}_{v}.png')
   result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'package_original_arm_back_audit.py'),str(root)],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0)
   self.assertFalse((root/'skeleton_skin_t0800.jpg').exists(),'Failed identity must not create a graphic claiming the same pose')

if __name__=='__main__':unittest.main(verbosity=2)
