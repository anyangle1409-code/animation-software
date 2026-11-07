import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'fixed_measurement_triangles.py'

class FixedMeasurementTriangles(unittest.TestCase):
    def module(self):
        self.assertTrue(PATH.exists(), 'polygon measurements need a frozen native tessellation')
        spec=importlib.util.spec_from_file_location('fixed',PATH)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        return mod

    def test_quad_faces_are_measured_as_fixed_rest_triangles_without_source_edits(self):
        mod=self.module()
        source_faces=[(0,1,2,3)]
        state={'vertices':[(0,0,0),(1,0,0),(1,1,0),(0,1,0)],'tessellations':0}
        def original(body):return state['vertices'],source_faces
        def native(body):
            state['tessellations']+=1
            return [(0,1,2),(0,2,3)] if state['tessellations']==1 else [(0,1,3),(1,2,3)]
        evaluate,report=mod.freeze_evaluated(original,native)
        rest,faces=evaluate(None)
        state['vertices']=[(0,0,0),(1,0,0),(1,1,0.25),(0,1,0)]
        posed,again=evaluate(None)
        self.assertEqual(faces,[(0,1,2),(0,2,3)])
        self.assertEqual(faces,again)
        self.assertEqual(state['tessellations'],1)
        self.assertEqual(source_faces,[(0,1,2,3)])
        self.assertNotEqual(rest,posed)
        self.assertEqual(report['source_polygon_count'],1)
        self.assertEqual(report['measurement_triangle_count'],2)

    def test_triangle_inputs_keep_the_existing_face_order(self):
        mod=self.module();faces=[(2,0,1)]
        def forbid(body):raise AssertionError('triangles must not be retessellated')
        evaluate,report=mod.freeze_evaluated(lambda body:([(0,0,0)]*3,faces),forbid)
        self.assertEqual(evaluate(None)[1],faces)
        self.assertFalse(report['derived_tessellation'])

    def test_changed_vertex_count_or_invalid_triangle_indices_fail_closed(self):
        mod=self.module()
        vertices=[(0,0,0)]*4
        evaluate,_=mod.freeze_evaluated(lambda body:(vertices,[(0,1,2,3)]),lambda body:[(0,1,2),(0,2,3)])
        evaluate(None);vertices.pop()
        with self.assertRaises(ValueError):evaluate(None)
        for invalid in ([],[(0,1,5)],[(0,1,1)],[(0,1,2,3)]):
            evaluate,_=mod.freeze_evaluated(lambda body:([(0,0,0)]*4,[(0,1,2,3)]),lambda body:invalid)
            with self.assertRaises(ValueError):evaluate(None)
