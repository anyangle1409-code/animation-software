"""Synthetic-only feature extraction and legacy bone/skin provenance rejection."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'anatomy_fit'))
import bone_feature_observation_packet as features
import pelvic_app_bone_frame as app

REGISTRY=HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/external_trunk_landmark_source_registry_20261009.json'


def sphere_pts(c,r=.025):
    return [[c[0]+r,c[1],c[2]],[c[0]-r,c[1],c[2]],
            [c[0],c[1]+r,c[2]],[c[0],c[1]-r,c[2]],
            [c[0],c[1],c[2]+r],[c[0],c[1],c[2]-r]]


def example_packet():
    coordinates={
        'asis_left':[.11,-.08,1.02],
        'asis_right':[-.11,-.08,1.02],
        'pubic_tubercle_left':[.015,-.08,.92],
        'pubic_tubercle_right':[-.015,-.08,.92],
        's1_endplate_centre':[0,.04,1.046],
        'hip_centre_left':[.083,-.019,.930],
        'hip_centre_right':[-.083,-.019,.930],
    }
    data={
        'schema_version':1,'kind':'SOURCE_BONE_FEATURE_OBSERVATION_PACKET',
        'status':'AUDIT_ONLY','canonical_promotion_allowed':False,
        'units':'m','world_convention':'HGPT_LEFT_POSITIVE_X_POSTERIOR_Y_SUPERIOR_Z',
        'features':{}
    }
    for key,(bone,method) in features.FEATURES.items():
        p=coordinates[key]
        f={'source_bone_id':bone,'extraction_method':method,
           'source_asset_class':'independently_segmented_bone_surface',
           'source_asset_sha256':'a'*64,
           'source_asset_uri':'https://example.invalid/SYNTHETIC_TEST_ONLY',
           'reported_world_point_m':p}
        if method=='surface_vertex':
            f['selected_bony_surface_vertex_m']=p[:]
        if method=='articular_sphere_fit':
            f['articular_points_world_m']=sphere_pts(p)
        if method=='endplate_four_rim_midpoint':
            f['rim_points_world_m']={
                'left':[-.04,.04,1.046], 'right':[.04,.04,1.046],
                'anterior':[0,.01,1.046], 'posterior':[0,.07,1.046],
            }
        data['features'][key]=f
    return data


class FeaturePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=json.loads(REGISTRY.read_text())

    def test_7_synthetic_features_fit_but_never_accepted(self):
        result=features.extract(example_packet())
        self.assertEqual(set(result['points_m']),set(features.FEATURES))
        self.assertEqual(result['status'],'NUMERIC_GEOMETRY_ONLY_SOURCE_IDENTITY_UNVERIFIED')
        self.assertFalse(result['canonical_promotion_allowed'])
        self.assertFalse(result['source_surface_identity_verified'])
        self.assertTrue(result['independent_anatomy_review_required'])

    def test_fit_both_femoral_centres_numerically(self):
        record=features.extract(example_packet())
        for side in ('left','right'):
            info=record['feature_diagnostics'][f'hip_centre_{side}']
            self.assertAlmostEqual(info['fitted_sphere_radius_m'],.025,places=10)
            self.assertLess(info['sphere_surface_rms_mm'],1e-6)
            self.assertFalse(info['clinical_head_centre_verified'])

    def test_s1_midpoint_is_derived_from_four_rim_landmarks(self):
        packet=example_packet()
        result=features.extract(packet)
        self.assertEqual(result['points_m']['s1_endplate_centre'],[0,.04,1.046])
        row=result['feature_diagnostics']['s1_endplate_centre']
        self.assertAlmostEqual(row['endplate_rim_lateral_span_mm'],80)
        self.assertAlmostEqual(row['endplate_rim_AP_span_mm'],60)

    def test_packet_feeds_app_but_cannot_certify_anatomy(self):
        packet=features.extract(example_packet())
        r=app.audit(packet['points_m'],self.registry,packet['provenance'])
        self.assertEqual(r['status'],'PROVENANCE_INCOMPLETE')
        self.assertTrue(any('physical bony feature identity unverified' in b
                            for b in r['evidence_blockers']))
        self.assertFalse(r['canonical_promotion_allowed'])

    def test_model_owner_cannot_say_verified_without_independent_review(self):
        r=features.extract(example_packet())
        for obj in r['provenance'].values():
            self.assertFalse(obj['feature_identity_verified'])
            self.assertEqual(obj['evidence_decision'],'COMPUTED_NOT_ANATOMICAL_ACCEPTANCE')

    def test_reported_femur_centre_20mm_off_fails(self):
        packet=example_packet()
        packet['features']['hip_centre_left']['reported_world_point_m'][0]+=.02
        with self.assertRaisesRegex(ValueError,'differs from feature-derived centre'):
            features.extract(packet)

    def test_synthetic_asis_claim_far_from_source_vertex_fails(self):
        packet=example_packet()
        packet['features']['asis_left']['reported_world_point_m'][0]+=.02
        with self.assertRaisesRegex(ValueError,'differs from feature-derived centre'):
            features.extract(packet)

    def test_r95_skin_source_cannot_be_used_as_bony_landmark(self):
        packet=example_packet()
        packet['features']['asis_left']['source_asset_class']='r95_skin_mesh'
        with self.assertRaisesRegex(ValueError,'skin, legacy proxy'):
            features.extract(packet)

    def test_unknown_bone_identity_rejected(self):
        packet=example_packet()
        packet['features']['asis_left']['source_bone_id']='sternum'
        with self.assertRaisesRegex(ValueError,'wrong source bone'):
            features.extract(packet)

    def test_wrong_extraction_method_rejected(self):
        packet=example_packet()
        packet['features']['hip_centre_left']['extraction_method']='hand_chosen_stick'
        with self.assertRaisesRegex(ValueError,'physical extraction method'):
            features.extract(packet)

    def test_pelvic_asises_must_not_be_reused_as_pubic_points(self):
        packet=example_packet()
        packet['features']['pubic_tubercle_left']['source_bone_id']='femur_left'
        with self.assertRaisesRegex(ValueError,'wrong source bone'):
            features.extract(packet)

    def test_invalid_sha_rejected(self):
        packet=example_packet()
        packet['features']['asis_left']['source_asset_sha256']='deadbeef'
        with self.assertRaisesRegex(ValueError,'invalid source asset SHA256'):
            features.extract(packet)

    def test_missing_source_link_rejected(self):
        packet=example_packet()
        del packet['features']['asis_left']['source_asset_uri']
        with self.assertRaisesRegex(ValueError,'stable source asset link'):
            features.extract(packet)

    def test_millimetres_rejected(self):
        packet=example_packet()
        packet['units']='mm'
        with self.assertRaisesRegex(ValueError,'world metres'):
            features.extract(packet)

    def test_mismatched_world_convention_rejected(self):
        packet=example_packet()
        packet['world_convention']='Y_FORWARD'
        with self.assertRaisesRegex(ValueError,'world convention'):
            features.extract(packet)

    def test_promotable_data_rejected(self):
        packet=example_packet()
        packet['canonical_promotion_allowed']=True
        with self.assertRaisesRegex(ValueError,'cannot authorize'):
            features.extract(packet)

    def test_exact_feature_set_required(self):
        packet=example_packet()
        del packet['features']['hip_centre_right']
        with self.assertRaisesRegex(ValueError,'seven physical'):
            features.extract(packet)

    def test_coplanar_femur_samples_rejected(self):
        packet=example_packet()
        centre=packet['features']['hip_centre_left']['reported_world_point_m']
        packet['features']['hip_centre_left']['articular_points_world_m']=[
            [centre[0]+.025*math.cos(i*math.pi/4),
             centre[1]+.025*math.sin(i*math.pi/4),centre[2]] for i in range(8)]
        with self.assertRaisesRegex(ValueError,'degenerate/non-spatial'):
            features.extract(packet)

    def test_too_few_femur_samples_rejected(self):
        packet=example_packet()
        packet['features']['hip_centre_left']['articular_points_world_m']=[
            [0,0,0],[1,0,0],[0,1,0]]
        with self.assertRaisesRegex(ValueError,'at least six'):
            features.extract(packet)

    def test_tiny_fake_femoral_head_rejected(self):
        packet=example_packet()
        c=packet['features']['hip_centre_left']['reported_world_point_m']
        packet['features']['hip_centre_left']['articular_points_world_m']=sphere_pts(c,.0002)
        with self.assertRaisesRegex(ValueError,'radius outside'):
            features.extract(packet)

    def test_missing_s1_rim_feature_rejected(self):
        packet=example_packet()
        del packet['features']['s1_endplate_centre']['rim_points_world_m']['posterior']
        with self.assertRaisesRegex(ValueError,'four labelled S1'):
            features.extract(packet)

    def test_fake_s1_flat_rim_rejected(self):
        packet=example_packet()
        packet['features']['s1_endplate_centre']['rim_points_world_m']['anterior']=[0,.04,1.046]
        packet['features']['s1_endplate_centre']['rim_points_world_m']['posterior']=[0,.04,1.046]
        with self.assertRaisesRegex(ValueError,'degenerate S1 rim'):
            features.extract(packet)

    def test_tampered_s1_reported_centre_rejected(self):
        packet=example_packet()
        packet['features']['s1_endplate_centre']['reported_world_point_m'][2]+=.02
        with self.assertRaisesRegex(ValueError,'differs from feature-derived centre'):
            features.extract(packet)

    def test_input_never_mutated(self):
        packet=example_packet()
        before=json.dumps(packet,sort_keys=True)
        first=features.extract(packet)
        self.assertEqual(first,features.extract(packet))
        self.assertEqual(json.dumps(packet,sort_keys=True),before)


if __name__=='__main__':
    unittest.main()
