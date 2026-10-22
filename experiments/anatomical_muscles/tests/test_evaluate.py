import unittest
from experiments.anatomical_muscles.evaluate import evaluate
I=((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1))

class EvaluationTests(unittest.TestCase):
    def spec(self):
        return {'id':'synthetic.L','side':'L','depth':'superficial',
          'binding':{'anchors':[{'bone':'a','local_m':[-2,0,0]},{'bone':'b','local_m':[2,0,0]}],
          'review':{'reviewer':'fixture','evidence':'synthetic only'},'source_sha256':'a'*64,
          'anatomical_side':'L','wrap_reviewed':True,'skin_mask':'fixture','direct_skin_weight':.5},
          'tissue':{'rest_volume_m3':.001,'tendon_lengths_m':[.1,.1]}}
    def test_safe_evaluation_and_source_not_mutated(self):
        spec=self.spec()
        result=evaluate(spec,{'a':I,'b':I},.5,[], 'a'*64)
        self.assertEqual(result['status'],'PROXY_EVALUATED_NOT_ANATOMY_VALIDATED')
        self.assertEqual(result['path_length_m'],4)
        self.assertAlmostEqual(result['belly_length_m'],3.8)
        self.assertEqual(spec['binding']['anchors'][0]['local_m'],[-2,0,0])
    def test_collision_unresolved_and_source_mismatch_fail_closed(self):
        spec=self.spec()
        with self.assertRaises(ValueError): evaluate(spec,{'a':I,'b':I},0,[{'bone':'a','center_local_m':[0,0,0],'radius_m':1}], 'a'*64)
        with self.assertRaises(ValueError): evaluate(spec,{'a':I,'b':I},0,[], 'b'*64)
        spec['binding']=None
        with self.assertRaises(ValueError): evaluate(spec,{'a':I,'b':I},0,[], 'a'*64)
    def test_tendon_longer_than_path_rejected(self):
        spec=self.spec();spec['tissue']['tendon_lengths_m']=[3,3]
        with self.assertRaises(ValueError): evaluate(spec,{'a':I,'b':I},0,[], 'a'*64)
    def test_return_to_neutral_has_no_state_drift(self):
        spec=self.spec(); poses=[]
        for dx in (0,.1,.2,.1,0):
            m=((1,0,0,dx),(0,1,0,0),(0,0,1,0),(0,0,0,1))
            poses.append(evaluate(spec,{'a':I,'b':m},.5,[], 'a'*64))
        self.assertEqual(poses[0],poses[-1])
        self.assertGreater(poses[2]['path_length_m'],poses[0]['path_length_m'])

if __name__=='__main__': unittest.main()
