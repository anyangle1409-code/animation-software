"""First-party test suite for bone-only APP; no accepted anatomy is created."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'anatomy_fit'))
import pelvic_app_bone_frame as app
import replay_p004_coupled_thorax as p4

REGISTRY=HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/external_trunk_landmark_source_registry_20261009.json'


def synthetic():
    return {
        'asis_left':[.11,-.08,1.02],
        'asis_right':[-.11,-.08,1.02],
        'pubic_tubercle_left':[.015,-.08,.92],
        'pubic_tubercle_right':[-.015,-.08,.92],
        's1_endplate_centre':[0,.04,1.046],
        'hip_centre_left':[.083,-.019,.930],
        'hip_centre_right':[-.083,-.019,.930],
    }


def transform(points,rotate_x_deg=0,translation=(0,0,0)):
    theta=math.radians(rotate_x_deg)
    cc,ss=math.cos(theta),math.sin(theta)
    result={}
    for key,(x,y,z) in points.items():
        result[key]=[x+translation[0],cc*y-ss*z+translation[1],
                      ss*y+cc*z+translation[2]]
    return result


class AppGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=json.loads(REGISTRY.read_text())
        cls.base=json.loads(p4.C004.read_text())

    def test_axis_semantics_exact_orthogonal_demo(self):
        x=app.app_frame(synthetic())
        for key,desired in (('left',[1,0,0]),('posterior',[0,1,0]),('superior',[0,0,1])):
            for a,b in zip(x['axis_world_unit'][key],desired):
                self.assertAlmostEqual(a,b,places=11)
        self.assertAlmostEqual(x['axis_handedness_determinant'],1,places=11)
        self.assertFalse(x['canonical_promotion_allowed'])

    def test_original_synthetic_hip_s1_ap_and_up_signs(self):
        p=synthetic()
        x=app.app_frame(p)
        h=app._mid(p['hip_centre_left'],p['hip_centre_right'])
        d=app.world_to_app_delta_mm(x,p['s1_endplate_centre'],h)
        self.assertAlmostEqual(d['posterior'],59,places=10)
        self.assertAlmostEqual(d['superior'],116,places=10)
        self.assertAlmostEqual(d['left'],0,places=10)

    def test_global_translation_invariant(self):
        p=synthetic()
        q=transform(p,translation=(.34,-.9,1.2))
        a=app.audit(p,self.src)
        b=app.audit(q,self.src)
        self.assertEqual(a['S1_relative_to_hip_in_APP_mm'],
                         b['S1_relative_to_hip_in_APP_mm'])

    def test_global_pelvis_tilt_about_x_invariant(self):
        p=synthetic()
        q=transform(p,rotate_x_deg=19)
        a=app.audit(p,self.src)
        b=app.audit(q,self.src)
        self.assertEqual(a['S1_relative_to_hip_in_APP_mm'],
                         b['S1_relative_to_hip_in_APP_mm'])

    def test_nontrivial_app_frame_is_right_handed_and_orthonormal(self):
        frame=app.app_frame(transform(synthetic(),rotate_x_deg=23))
        basis=frame['axis_world_unit']
        for u in basis.values():
            self.assertAlmostEqual(app._length(u),1,places=10)
        self.assertAlmostEqual(app._dot(app._cross(basis['left'],basis['posterior']),
                                         basis['superior']),1,places=10)

    def test_noncollinear_app_rejects_vertically_missing_pubic_points(self):
        p=synthetic()
        p['pubic_tubercle_left']=[.015,-.08,1.02]
        p['pubic_tubercle_right']=[-.015,-.08,1.02]
        with self.assertRaisesRegex(ValueError,'collinear'):
            app.app_frame(p)

    def test_asises_too_close_rejected(self):
        p=synthetic()
        p['asis_left']=[.009,-.08,1.02]
        p['asis_right']=[-.009,-.08,1.02]
        with self.assertRaisesRegex(ValueError,'ASIS separation'):
            app.app_frame(p)

    def test_nan_asis_rejected(self):
        p=synthetic()
        p['asis_left'][1]=float('nan')
        with self.assertRaisesRegex(ValueError,'invalid finite'):
            app.app_frame(p)

    def test_side_mirror_swap_rejected(self):
        p=synthetic()
        p['asis_left'],p['asis_right']=p['asis_right'],p['asis_left']
        with self.assertRaisesRegex(ValueError,'left/right labels'):
            app.audit(p,self.src)

    def test_mirrored_pubis_rejected(self):
        p=synthetic()
        p['pubic_tubercle_left'],p['pubic_tubercle_right']=(
            p['pubic_tubercle_right'],p['pubic_tubercle_left'])
        with self.assertRaisesRegex(ValueError,'left/right labels'):
            app.audit(p,self.src)

    def test_wrong_inverted_superior_axis_rejected(self):
        p=synthetic()
        p['pubic_tubercle_left'][2]=1.16
        p['pubic_tubercle_right'][2]=1.16
        with self.assertRaisesRegex(ValueError,'upright world'):
            app.audit(p,self.src)

    def test_provenance_missing_is_blocking(self):
        r=app.audit(synthetic(),self.src)
        self.assertEqual(r['status'],'PROVENANCE_INCOMPLETE')
        self.assertIn('no bone-landmark provenance record',r['evidence_blockers'])
        self.assertFalse(r['source_bone_surfaces_independently_validated'])

    def test_skin_mesh_tag_rejected_even_with_sha(self):
        provenance={k:{'source_kind':'old_r95_skin_mesh',
                       'feature_identity_verified':True,
                       'source_asset_sha256':'a'*64,
                       'extraction_method':'nearest skin vertex'}
                    for k in app.REQUIRED_BONY}
        r=app.audit(synthetic(),self.src,provenance)
        self.assertEqual(r['status'],'PROVENANCE_INCOMPLETE')
        self.assertTrue(any('skin or unsourced' in s for s in r['evidence_blockers']))

    def test_declared_bony_surfaces_never_automatically_accepted(self):
        provenance={k:{'source_kind':'independently_segmented_bone_surface',
                       'feature_identity_verified':True,
                       'source_asset_sha256':'a'*64,
                       'extraction_method':'anatomical specialist CT segmentation'}
                    for k in app.REQUIRED_BONY}
        r=app.audit(synthetic(),self.src,provenance)
        self.assertEqual(r['status'],'EVIDENCE_DECLARED_INDEPENDENT_REVIEW_REQUIRED')
        self.assertFalse(r['canonical_promotion_allowed'])
        self.assertFalse(r['source_bone_surfaces_independently_validated'])
        self.assertFalse(r['world_to_study_cohort_endpoints_registered'])

    def test_mislabelled_corrupt_bone_hash_rejected(self):
        provenance={k:{'source_kind':'independently_segmented_bone_surface',
                       'feature_identity_verified':True,
                       'source_asset_sha256':'not-a-real-hash',
                       'extraction_method':'manual checked'} for k in app.REQUIRED_BONY}
        r=app.audit(synthetic(),self.src,provenance)
        self.assertEqual(r['status'],'PROVENANCE_INCOMPLETE')
        self.assertTrue(any('content hash missing' in s for s in r['evidence_blockers']))

    def test_legacy_control_identifies_wrong_landmark_class(self):
        points=app.legacy_controls(self.base)
        r=app.audit(points,self.src,legacy=True)
        self.assertEqual(r['status'],'LEGACY_SKIN_FRAME_REJECTED')
        self.assertIn('skin inguinal groove',r['evidence_blockers'][0])
        self.assertFalse(r['canonical_promotion_allowed'])
        self.assertEqual(r['legacy_landmark_uncertainty_stress_test']['number_of_scenarios'],8)

    def test_legacy_asis_skin_provenance_uncertainty_persists(self):
        raw=self.base['landmarks_and_joint_centres']['sides']['left']['hip']['asis_skin']
        self.assertEqual(raw['confidence'],'low')
        self.assertIn('20 mm',raw['uncertainty'])
        r=app.audit(app.legacy_controls(self.base),self.src,legacy=True)
        self.assertGreater(r['legacy_landmark_uncertainty_stress_test']['max_APP_axis_change_deg'],1)

    def test_legacy_perturbation_not_literature_value(self):
        r=app.audit(app.legacy_controls(self.base),self.src,legacy=True)
        self.assertFalse(r['Imai_2019_APP_study_comparison']['anatomical_target_selected'])
        self.assertFalse(r['Imai_2019_APP_study_comparison']['source_stature_compatible_with_model'])

    def test_candidate_untouched(self):
        a=synthetic()
        b=json.loads(json.dumps(a))
        src_before=json.dumps(self.src,sort_keys=True)
        app.audit(a,self.src)
        self.assertEqual(a,b)
        self.assertEqual(json.dumps(self.src,sort_keys=True),src_before)

    def test_source_registry_never_promotable(self):
        s=copy.deepcopy(self.src)
        s['canonical_promotion_allowed']=True
        with self.assertRaisesRegex(ValueError,'must not permit promotion'):
            app.audit(synthetic(),s)

    def test_pubis_out_of_anatomical_plane_reported_not_silently_corrected(self):
        a=synthetic()
        a['pubic_tubercle_left'][1]+=.004
        a['pubic_tubercle_right'][1]-=.004
        f=app.app_frame(a)
        self.assertAlmostEqual(f['pubic_landmark_plane_normal_spread_mm'],8,places=4)
        self.assertFalse(f['source_landmark_identity_verified'])

    def test_study_2sd_not_relabelled(self):
        r=app.audit(synthetic(),self.src)
        self.assertTrue(r['Imai_2019_APP_study_comparison']['published_spreads_two_sd'])
        self.assertEqual(r['Imai_2019_APP_study_comparison']['published_male_DYp_mm'],18.8)
        self.assertEqual(r['Imai_2019_APP_study_comparison']['published_male_DZp_mm'],104.7)

    def test_malformed_s1_rejected(self):
        a=synthetic()
        del a['s1_endplate_centre']
        with self.assertRaises(KeyError):
            app.audit(a,self.src)


if __name__=='__main__':
    unittest.main()
