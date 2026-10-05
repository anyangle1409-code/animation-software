"""Pure-Python tests for shoulder deformation-layer diagnostics."""
import types
import unittest

import original_v1_deformation_layers as layers


class FakeKey:
    def __init__(self, value): self.value=value


class LayerDiagnosticTests(unittest.TestCase):
    def body(self, values):
        blocks={name:FakeKey(value) for name,value in values.items()}
        shape_keys=types.SimpleNamespace(key_blocks=blocks)
        return types.SimpleNamespace(data=types.SimpleNamespace(shape_keys=shape_keys))

    def test_missing_configuration_names_omitted_layer(self):
        values={name:0.0 for name in layers.REQUIRED_KEYS}; values.pop('HGPT_SHOULDER_SCAP_R')
        with self.assertRaisesRegex(ValueError, 'HGPT_SHOULDER_SCAP_R'):
            layers.activation_snapshot(None,self.body(values),None)

    def test_zero_one_and_combined_layer_activation(self):
        values={name:0.0 for name in layers.REQUIRED_KEYS}
        snap=layers.activation_snapshot(None,self.body(values),None)
        self.assertEqual(snap['active_layers'],[])
        values['HGPT_SHOULDER_CORR_L']=0.5
        snap=layers.activation_snapshot(None,self.body(values),None)
        self.assertEqual(snap['active_layers'],['abduction'])
        values['HGPT_SHOULDER_SCAP_L']=0.25
        snap=layers.activation_snapshot(None,self.body(values),None)
        self.assertEqual(snap['active_layers'],['abduction','scapular'])

    def test_displacement_summary_reports_each_state_and_zone(self):
        states={
            'rest':[(0,0,0),(1,0,0),(-1,0,0),(0,1,0)],
            'weights_only':[(0,0,0),(1.1,0,0),(-1.1,0,0),(0,1,0)],
            'combined':[(0,0,0),(1.05,0,0),(-1.04,0,0),(0,1,0)],
        }
        zones={'axilla':{'left':[1],'right':[2]}}
        summary=layers.summarize_zone_displacement(states,zones)
        self.assertAlmostEqual(summary['states']['weights_only']['zones']['axilla']['max_displacement'],0.1)
        self.assertAlmostEqual(summary['states']['combined']['zones']['axilla']['symmetry_error'],0.01)

    def test_invalid_zone_vertex_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'vertex index'):
            layers.summarize_zone_displacement({'rest':[(0,0,0)],'posed':[(0,0,0)]},{'axilla':{'left':[3],'right':[]}})

    def test_monotone_and_non_monotone_arc_detection(self):
        good=[{'angle_deg':0,'values':{'abduction':0}},{'angle_deg':60,'values':{'abduction':0.4}},{'angle_deg':120,'values':{'abduction':1.0}}]
        bad=[{'angle_deg':0,'values':{'abduction':0}},{'angle_deg':60,'values':{'abduction':0.7}},{'angle_deg':120,'values':{'abduction':0.5}}]
        self.assertTrue(layers.summarize_activation_arc(good)['layers']['abduction']['monotone_non_decreasing'])
        result=layers.summarize_activation_arc(bad)
        self.assertFalse(result['layers']['abduction']['monotone_non_decreasing'])
        self.assertEqual(result['layers']['abduction']['reversals'],[{'from_angle_deg':60,'to_angle_deg':120,'drop':0.2}])

    def test_left_right_activation_symmetry_is_reported(self):
        values={name:0.0 for name in layers.REQUIRED_KEYS}
        values['HGPT_SHOULDER_CORR_L']=0.8;values['HGPT_SHOULDER_CORR_R']=0.6
        snap=layers.activation_snapshot(None,self.body(values),None)
        self.assertAlmostEqual(snap['symmetry_error']['abduction'],0.2)


if __name__=='__main__':unittest.main()
