"""Native candidate gates: fail on old runtime, pass only the separate trial."""
import bpy,json,sys,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import original_shoulder_joint_authority as authority
import build_functional_absolute_reach_blender as reach
from mathutils import Matrix
class RefitTests(unittest.TestCase):
    def test_front_shoulder_does_not_collapse_below_tenth_area_at_authored_160(self):
        self.assert_triangle_retains_tenth_area((4647,13572,4773))
    def test_rear_shoulder_does_not_collapse_below_tenth_area_at_authored_160(self):
        self.assert_triangle_retains_tenth_area((4865,13619,4748))
    def assert_triangle_retains_tenth_area(self,indices):
        # 10% is an engineering severe-collapse guard, not physiological authority.
        body=bpy.data.objects['HGPT_BODY_SHOULDER_REFIT_TRIAL']
        rig=bpy.data.objects['HGPT_SHOULDER_JOINT_REFIT_TRIAL']
        guide=next(o for o in bpy.data.objects if o.type=='ARMATURE' and len(o.data.bones)==6 and 'scapula_left' in o.data.bones)
        for arm in (guide,rig):
            for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
        bpy.context.view_layer.update()
        def area():
            bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            a,b,c=[ev.matrix_world@ev.data.vertices[i].co for i in indices]
            return (b-a).cross(c-a).length
        rec=json.loads((Path(__file__).resolve().parents[1]/authority.RECORD).read_text())
        mapping={part+'_'+side:runtime+'_'+suffix for side,suffix in [('left','r'),('right','l')] for part,runtime in [('clavicle','clavicle'),('scapula','scapula'),('humerus','upperarm')]}
        before=area();rest={n:rig.matrix_world@rig.data.bones[n].matrix_local for n in mapping.values()}
        guide_rest={n:guide.matrix_world@guide.data.bones[n].matrix_local for n in mapping}
        try:
            reach.pose_absolute(guide,rec,160)
            for n,target in mapping.items():
                rig.pose.bones[target].matrix=rig.matrix_world.inverted()@(guide.matrix_world@guide.pose.bones[n].matrix)@guide_rest[n].inverted()@rest[target]
                bpy.context.view_layer.update()
            self.assertGreaterEqual(area()/before,.1,'Known severe shoulder skin collapse; keep gate RED until refit')
        finally:
            for arm in (guide,rig):
                for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
            bpy.context.view_layer.update()
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
