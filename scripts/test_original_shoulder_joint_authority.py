"""Catch column transposition, joint substitution, and approval promotion."""
import copy
import json
from pathlib import Path
import unittest
import original_shoulder_joint_authority as authority

class JointAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((Path(__file__).resolve().parents[1]/authority.RECORD).read_text())
    def test_columns_are_converted_to_world_rows(self):
        result=authority.extract(self.record)
        marker=self.record['joint_markers']['sternoclavicular_left']
        frame=result['joints']['SC_left']['world_frame_row_major']
        for axis in range(3):
            for coordinate in range(3):
                self.assertEqual(frame[coordinate][axis],marker['frame_axes_columns_XYZ'][axis][coordinate])
        self.assertEqual(len(result['joints']),6)
        self.assertFalse(result['anatomical_approval'])
    def test_ac_cannot_be_substituted_by_scapular_glenoid_head(self):
        self.record['joint_markers']['acromioclavicular_left']['centre_m']=self.record['bones']['scapula_left']['head_m']
        with self.assertRaisesRegex(ValueError,'anchor mismatch'):authority.extract(self.record)
    def test_unverified_source_status_cannot_be_promoted(self):
        self.record['joint_markers']['glenohumeral_left']['fit_status']='APPROVED'
        with self.assertRaisesRegex(ValueError,'status'):authority.extract(self.record)
    def test_nonrigid_marker_axes_are_rejected(self):
        self.record['joint_markers']['sternoclavicular_left']['frame_axes_columns_XYZ'][0][0]*=2
        with self.assertRaises(ValueError):authority.extract(self.record)

if __name__=='__main__':unittest.main()
