"""Native regression for a separate source-station toe-control prototype."""
import bpy,sys,math,unittest
from mathutils import Matrix

class ToeArticulationTests(unittest.TestCase):
    def test_hallux_root_does_not_reverse_triangles_at_15_degrees(self):
        rig=bpy.data.objects.get('HGPT_TOE_SEGMENT_RUNTIME_TRIAL')
        body=bpy.data.objects.get('HGPT_BODY_TOE_SEGMENT_TRIAL')
        self.assertIsNotNone(rig,'Missing independent toe runtime trial')
        for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
        bpy.context.view_layer.update()
        def pts():
            ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            return [ev.matrix_world@v.co for v in ev.data.vertices]
        neutral=pts();body.data.calc_loop_triangles()
        for suffix in ('l','r'):
            rig.pose.bones[f'trial_toe1_01_{suffix}'].matrix_basis=Matrix.Rotation(math.radians(15),4,'X')
            bpy.context.view_layer.update();posed=pts();flips=0
            for t in body.data.loop_triangles:
                i,j,k=t.vertices
                n=(neutral[j]-neutral[i]).cross(neutral[k]-neutral[i])
                m=(posed[j]-posed[i]).cross(posed[k]-posed[i])
                if n.length>1e-12 and n.dot(m)<0:flips+=1
            self.assertEqual(flips,0,f'Hallux root triangle reversals on {suffix}')
            for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
            bpy.context.view_layer.update()

    def test_individual_source_station_controls_exist(self):
        rig=bpy.data.objects.get('HGPT_TOE_SEGMENT_RUNTIME_TRIAL')
        self.assertIsNotNone(rig,'Missing independent toe runtime trial')
        self.assertEqual(len(rig.data.bones),95)
        self.assertEqual(len([b for b in rig.data.bones if b.name.startswith('trial_toe')]),28)
        original=bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
        for source in original.data.bones:
            copied=rig.data.bones[source.name]
            self.assertLess((copied.head_local-source.head_local).length,2e-6)
            self.assertLess((copied.tail_local-source.tail_local).length,2e-6)
            self.assertEqual(copied.parent.name if copied.parent else None,source.parent.name if source.parent else None)
            self.assertLess(max(abs(copied.matrix_local[i][j]-source.matrix_local[i][j]) for i in range(4) for j in range(4)),2e-6)

    def test_new_controls_use_unchanged_source_stations(self):
        rig=bpy.data.objects.get('HGPT_TOE_SEGMENT_RUNTIME_TRIAL')
        self.assertIsNotNone(rig,'Missing independent toe runtime trial')
        anatomy=bpy.data.objects['HGPT_ANATOMICAL_MASTER']
        for bone in rig.data.bones:
            if not bone.name.startswith('trial_toe'):continue
            ref=anatomy.data.bones[bone['source_anatomical_bone']]
            self.assertLess((rig.matrix_world@bone.head_local-anatomy.matrix_world@ref.head_local).length,2e-6)
            self.assertLess((rig.matrix_world@bone.tail_local-anatomy.matrix_world@ref.tail_local).length,2e-6)

    def test_clone_has_no_remaining_shared_toe_influence(self):
        body=bpy.data.objects.get('HGPT_BODY_TOE_SEGMENT_TRIAL')
        self.assertIsNotNone(body,'Missing independent toe skin trial')
        shared={body.vertex_groups[n].index for n in ('toe_l','toe_r')}
        for v in body.data.vertices:
            self.assertLess(abs(sum(g.weight for g in v.groups)-1),2e-6)
            self.assertFalse(any(g.group in shared and g.weight>1e-8 for g in v.groups))

    def test_single_digit_moves_without_distal_other_digit_motion(self):
        rig=bpy.data.objects.get('HGPT_TOE_SEGMENT_RUNTIME_TRIAL')
        body=bpy.data.objects.get('HGPT_BODY_TOE_SEGMENT_TRIAL')
        self.assertIsNotNone(rig,'Missing independent toe runtime trial')
        def reset():
            for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
            bpy.context.view_layer.update()
        def points():
            ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            return [ev.matrix_world@v.co for v in ev.data.vertices]
        reset();rest=points()
        for suffix in ('l','r'):
            for digit in range(1,6):
                name=f'trial_toe{digit}_01_{suffix}'
                own={g.index for g in body.vertex_groups if g.name.startswith(f'trial_toe{digit}_') and g.name.endswith('_'+suffix)}
                other={g.index for g in body.vertex_groups if g.name.startswith('trial_toe') and g.name.endswith('_'+suffix) and g.index not in own}
                ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in own)>.5]
                other_ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in other)>.5]
                reset();rig.pose.bones[name].matrix_basis=Matrix.Rotation(math.radians(15),4,'X')
                bpy.context.view_layer.update();posed=points()
                self.assertTrue(ids)
                self.assertGreater(max((posed[i]-rest[i]).length for i in ids),.001)
                self.assertLess(max((posed[i]-rest[i]).length for i in other_ids),2e-6)
                self.assertTrue(all(math.isfinite(x) for p in posed for x in p))
        reset()
        self.assertLess(max((p-q).length for p,q in zip(points(),rest)),2e-6)

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ToeArticulationTests))
    if not r.wasSuccessful():raise RuntimeError('Toe articulation regression failed')
