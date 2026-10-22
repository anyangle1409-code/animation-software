import copy
import json
from pathlib import Path
import unittest
from experiments.anatomical_muscles import registry as r

ROOT=Path(__file__).resolve().parents[3]
SEED=json.loads((ROOT/'docs/ORIGINAL_V1_MUSCLE_REGISTRY_SEED_20261022.json').read_text())

class RegistryTests(unittest.TestCase):
    def setUp(self): self.data=r.expand(SEED)
    def test_bilateral_seed_and_relations(self):
        self.assertEqual(len(self.data['muscles']),120)
        self.assertEqual(r.validate(self.data),[])
        self.assertEqual(len(self.data['interactions']),22)
        self.assertTrue(all(m['binding'] is None for m in self.data['muscles']))
    def test_pilot_includes_both_regions(self):
        ids={m['id'] for m in self.data['muscles'] if m['pilot']}
        self.assertIn('hgpt.muscle.deltoid_middle.L',ids)
        self.assertIn('hgpt.muscle.gluteus_maximus.R',ids)
        self.assertNotIn('hgpt.muscle.thenar_group.L',ids)
    def test_missing_side_duplicate_and_unknown_neighbor_rejected(self):
        self.data['muscles'].pop()
        self.assertTrue(r.validate(self.data))
        self.data=r.expand(SEED)
        self.data['muscles'][0]['neighbors']=['hgpt.muscle.unknown.L']
        self.assertTrue(r.validate(self.data))
        self.data=r.expand(SEED)
        self.data['muscles'][1]['id']=self.data['muscles'][0]['id']
        self.assertTrue(r.validate(self.data))
    def test_empty_registry_is_not_ready(self):
        with self.assertRaises(ValueError): r.readiness({"muscles":[]},[])

    def test_unresolved_registry_cannot_be_ready(self):
        self.assertEqual(len(r.readiness(self.data,[])),120)
    def test_binding_checks_real_ids_coordinates_review_and_deep_mask(self):
        m=next(m for m in self.data['muscles'] if m['id']=='hgpt.muscle.iliacus.L')
        m['binding']={'anchors':[{'bone':'pelvis','local_m':[0,0,0]},{'bone':'femur','local_m':[0,0,1]}],
                      'review':{'reviewer':'test','evidence':'synthetic fixture'},'skin_mask':None,'wrap_reviewed':True,
                      'direct_skin_weight':0,'source_sha256':'a'*64,'anatomical_side':'L'}
        self.assertEqual(r.binding_errors(m,{'pelvis','femur'}),[])
        self.assertTrue(r.binding_errors(m,{'pelvis'}))
        m['binding']['anchors'][0]['local_m'][0]=float('nan')
        self.assertTrue(r.binding_errors(m,{'pelvis','femur'}))
        m['binding']['anchors'][0]['local_m'][0]=0
        m['binding']['direct_skin_weight']=1
        self.assertTrue(r.binding_errors(m,{'pelvis','femur'}))
    def test_activation_is_never_inferred_from_action(self):
        self.assertTrue(all(m['activation']['mode']=='explicit_visual_channel' for m in self.data['muscles']))
        self.assertTrue(all(m['activation']['default']==0 for m in self.data['muscles']))

if __name__=='__main__': unittest.main()
