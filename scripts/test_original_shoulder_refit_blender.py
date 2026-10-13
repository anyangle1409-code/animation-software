"""Native candidate gates: fail on old runtime, pass only the separate trial."""
import bpy,json,sys,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import original_shoulder_joint_authority as authority
class RefitTests(unittest.TestCase):
    def test_joint_heads_follow_source_centres(self):
        arm=bpy.data.objects.get('HGPT_SHOULDER_JOINT_REFIT_TRIAL')
        self.assertIsNotNone(arm,'Separate source-joint runtime not installed')
        rec=json.loads((Path(__file__).resolve().parents[1]/authority.RECORD).read_text())
        for key,j in authority.extract(rec)['joints'].items():
            side=key.split('_')[1];suffix='r' if side=='left' else 'l'
            name={'SC':'clavicle','AC':'scapula','GH':'upperarm'}[key.split('_')[0]]+'_'+suffix
            centre=[j['world_frame_row_major'][r][3] for r in range(3)]
            self.assertLess(math.dist(centre,arm.matrix_world@arm.data.bones[name].head_local),2e-6)
    def test_original_body_is_retained_separately(self):
        original=bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
        trial=bpy.data.objects.get('HGPT_BODY_SHOULDER_REFIT_TRIAL')
        self.assertIsNotNone(trial)
        self.assertEqual(len(trial.data.vertices),17946)
        self.assertTrue(all(a.co==b.co for a,b in zip(original.data.vertices,trial.data.vertices)))
        self.assertEqual([m.object.name for m in trial.modifiers if m.type=='ARMATURE'],['HGPT_SHOULDER_JOINT_REFIT_TRIAL'])
suite=unittest.defaultTestLoader.loadTestsFromTestCase(RefitTests)
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():raise RuntimeError('Native shoulder-refit gate failed')
