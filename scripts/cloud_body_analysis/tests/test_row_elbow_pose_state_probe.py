"""Synthetic row-control contract tests, never anatomical evidence."""
import copy
import importlib.util
import math
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[2] / 'phone_blender' / 'row_elbow_pose_state_probe.py'
SPEC = importlib.util.spec_from_file_location('row_probe', MODULE)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def control(head, tail, angle=0.0):
    a=math.radians(angle)/2
    return {'control_present':True,'pose_rotation_mode':'XYZ',
            'matrix_basis_quaternion_wxyz':[math.cos(a),math.sin(a),0.,0.],
            'local_delta_angle_deg_not_anatomical':angle,
            'head_world_m_not_anatomical_joint_centre':head,'tail_world_m':tail}


def controls():
    return {'upperarm':control([0.,0.,1.],[0.,0.,0.]),
            'forearm':control([0.,0.,0.],[1.,0.,0.]),
            'hand':control([1.,0.,0.],[2.,0.,0.])}


def report():
    return {**probe.scope(), 'samples':[
        {'sample':i,'t':i/8,'authored_targets_deg_not_anatomical':probe.authored_targets(i/8),
         'whole_body_benchmark_flags_not_elbow_local':{'collapse_lt_0_1':0,'stretch_gt_2':3,'self_intersecting_pairs':2},
         'sides':{s:{'controls':controls(),'included_control_elbow_angle_deg_not_anatomical':90.} for s in ['l','r']}}
        for i in range(9)]}


class RowElbowProbeTests(unittest.TestCase):
    def test_valid_report_and_markdown_scope(self):
        self.assertEqual(probe.validate_report(report()),[])
        text=probe.markdown(report())
        self.assertIn('coupled shoulder/elbow',text)
        self.assertIn('not elbow-local',text)
        self.assertIn('does not test return to neutral',text)

    def test_hand_derived_authored_targets(self):
        targets=[probe.authored_targets(i/8) for i in range(9)]
        self.assertEqual([r['elbow_flexion'] for r in targets],[0,0,0,0,0,15.625,50,84.375,100])
        self.assertEqual([targets[i]['shoulder_flexion_signed'] for i in [0,4,6,8]],[0,45,2.5,-40])

    def test_included_geometry_uses_head_points_independently(self):
        c=controls();self.assertAlmostEqual(probe.included_elbow_angle_deg(c),90)
        c['hand']['head_world_m_not_anatomical_joint_centre']=[2.,0.,2.]
        self.assertAlmostEqual(probe.included_elbow_angle_deg(c),45)
        c['hand']['head_world_m_not_anatomical_joint_centre']=[0.,0.,-3.]
        self.assertAlmostEqual(probe.included_elbow_angle_deg(c),180)

    def test_rigid_transform_preserves_included_angle(self):
        c=controls()
        for r in c.values():
            x,y,z=r['head_world_m_not_anatomical_joint_centre']
            r['head_world_m_not_anatomical_joint_centre']=[7-z,3+y,2+x]
        self.assertAlmostEqual(probe.included_elbow_angle_deg(c),90)

    def test_tampered_included_angle_is_rejected(self):
        d=report();d['samples'][3]['sides']['l']['included_control_elbow_angle_deg_not_anatomical']=100.
        self.assertIn('included geometry mismatch',probe.validate_report(d))

    def test_commanded_angle_is_not_required_to_equal_included_geometry(self):
        self.assertEqual(probe.validate_report(report()),[])
        self.assertNotEqual(report()['samples'][8]['authored_targets_deg_not_anatomical']['elbow_flexion'],90)

    def test_invalid_nested_values_return_errors(self):
        for location,value in [('samples',None),('samples',{}),('samples',[None]*9)]:
            d=report();d[location]=value;self.assertTrue(probe.validate_report(d))
        for field in ['sides','whole_body_benchmark_flags_not_elbow_local','authored_targets_deg_not_anatomical']:
            d=report();d['samples'][0][field]=None;self.assertTrue(probe.validate_report(d))
        d=report();d['samples'][0]['sides']['r']=[];self.assertTrue(probe.validate_report(d))
        d=report();d['samples'][0]['sides']['r']['controls']=None;self.assertTrue(probe.validate_report(d))

    def test_degenerate_or_extreme_geometry_fails_closed(self):
        for point in [[0.,0.,0.],[float('nan'),0.,0.],[1e308,1e308,1e308]]:
            d=report();c=d['samples'][0]['sides']['l']['controls']
            c['upperarm']['head_world_m_not_anatomical_joint_centre']=point
            if point[0]==1e308:c['forearm']['head_world_m_not_anatomical_joint_centre']=[-1e308]*3
            self.assertTrue(probe.validate_report(d))

    def test_strict_sample_and_flag_types(self):
        for bad in [False,0.0,'0']:
            d=report();d['samples'][0]['sample']=bad;self.assertTrue(probe.validate_report(d))
        for bad in [True,1.0,-1,float('inf')]:
            d=report();d['samples'][0]['whole_body_benchmark_flags_not_elbow_local']['stretch_gt_2']=bad
            self.assertTrue(probe.validate_report(d))

    def test_source_and_scope_guards(self):
        for field,value in [('source_sha256','0'*64),('saved_blend',True),('anatomical_motion_approved',True),('return_to_neutral_tested',True),('plain_benchmark_correctives_cleared',False)]:
            d=report();d[field]=value;self.assertTrue(probe.validate_report(d))
        d=report();d['limitations'].pop();self.assertTrue(probe.validate_report(d))

    def test_target_drift_quaternion_drift_and_missing_side(self):
        d=report();d['samples'][5]['authored_targets_deg_not_anatomical']['elbow_flexion']+=1
        self.assertTrue(probe.validate_report(d))
        d=report();d['samples'][0]['sides']['l']['controls']['forearm']['matrix_basis_quaternion_wxyz']=[0.,1.,0.,0.]
        self.assertTrue(probe.validate_report(d))
        d=report();del d['samples'][0]['sides']['l'];self.assertTrue(probe.validate_report(d))

    def test_quaternion_sign_equivalence(self):
        d=report();c=d['samples'][0]['sides']['l']['controls']['forearm'];c['matrix_basis_quaternion_wxyz']=[-x for x in c['matrix_basis_quaternion_wxyz']]
        self.assertEqual(probe.validate_report(d),[])


if __name__=='__main__':unittest.main()
