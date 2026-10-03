import copy
import importlib
import unittest


class DiagnosticBriefTests(unittest.TestCase):
    def fixture(self):
        module=importlib.import_module('build_original_v1_diagnostic_brief')
        weight=[{'bone':'thumb_01_l','weight':1.0}]
        sample={'max_penetration_mm':5.93,'inside_vertices':2,'contact_vertices_within_2mm':25,
            'finger_vertices':30,'deepest':[{'vertex':12,'signed_distance_mm':-5.93,
                'penetration_mm':5.93,'region':'thumb','rest_position':[0.1,0,1], 'top_weights':weight}]}
        grip={'schema_version':1,'source_candidate_sha256':'a'*64,'pose_script_sha256':'b'*64,'acceptance_gate_mm':2,
            'poses':{name:{'pre_close':{side:copy.deepcopy(sample) for side in 'lr'},
                'post_close':{side:copy.deepcopy(sample) for side in 'lr'},
                'handle':{side:{'centre':[0,0,1],'axis':[1,0,0],'radius_m':0.018} for side in 'lr'}}
                for name in ('curl_handle','pullup_bar')}}
        edges={'schema_version':1,'source_candidate_sha256':'a'*64,'targets':[]}
        primary=[{'pose':name,**{'grip_'+s:{'max_penetration_mm':5.93} for s in 'lr'}} for name in grip['poses']]
        for pose,region,direction in module.TARGETS:
            ratio=0.12 if direction=='min' else 7.2
            edges['targets'].append({'pose':pose,'region':region,'direction':direction,'extreme_ratio':ratio,
                'edge_count_in_region':10,'edges':[{'rank':1,'edge_index':2,'vertices':[10,11],
                    'ratio':ratio,'rest_length_m':0.01,'posed_length_m':0.01*ratio,'rest_midpoint':[0,0,1],
                    'posed_midpoint':[0,0,1],'vertex_a_weights':weight,'vertex_b_weights':weight,
                    'mirror_edge_index':3,'mirror_ratio':ratio}]})
            row=next((r for r in primary if r['pose']==pose),None)
            if row is None:row={'pose':pose,'by_region':{}};primary.append(row)
            row['by_region'].setdefault(region,{})[direction+'_ratio']=ratio
        profile={'grip_max_penetration_mm':2,'grip_min_contact_vertices_within_2mm':20,
            'region_min_ratio_min':0.15,'region_max_ratio_max':5}
        return module,grip,edges,primary,profile

    def test_exact_observations_do_not_authorise_edits_or_approval(self):
        c,g,e,p,s=self.fixture();r=c.summarize(g,e,p,'a'*64,'b'*64,s)
        self.assertEqual(len(r['grip_observations']),4);self.assertEqual(len(r['edge_observations']),4)
        self.assertTrue(r['grip_observations'][0]['penetration_present_before_close'])
        self.assertEqual(r['grip_observations'][0]['closing_delta_mm'],0)
        self.assertFalse(r['edit_authorised']);self.assertFalse(r['production_approved'])
        self.assertEqual(r['edge_observations'][0]['inspection_vertex_ids'],[10,11])
        self.assertTrue(any('strict active-epoch regressions' in x for x in r['limits']))
    def test_markdown_uses_active_epoch_not_hardcoded_r29(self):
        c,g,e,p,s=self.fixture();r=c.summarize(g,e,p,'a'*64,'b'*64,s)
        r.update(candidate_revision='r55',active_epoch_baseline_revision='P3B1',source_evidence=[])
        md=c.markdown(r)
        self.assertIn('P3B1',md)
        self.assertIn('Do not hard-code R2/r28/r29',md)

    def test_missing_side_or_pose_refused(self):
        c,g,e,p,s=self.fixture();del g['poses']['curl_handle']['post_close']['r']
        with self.assertRaises(ValueError):c.summarize(g,e,p,'a'*64,'b'*64,s)
    def test_wrong_source_or_script_refused(self):
        for key in ('source_candidate_sha256','pose_script_sha256'):
            c,g,e,p,s=self.fixture();g[key]='c'*64
            with self.assertRaises(ValueError):c.summarize(g,e,p,'a'*64,'b'*64,s)
    def test_probe_disagrees_with_primary_refused(self):
        c,g,e,p,s=self.fixture();g['poses']['curl_handle']['post_close']['l']['max_penetration_mm']=6.5
        with self.assertRaisesRegex(ValueError,'primary'):c.summarize(g,e,p,'a'*64,'b'*64,s)
    def test_edge_disagrees_with_primary_refused(self):
        c,g,e,p,s=self.fixture();e['targets'][0]['extreme_ratio']=6
        with self.assertRaises(ValueError):c.summarize(g,e,p,'a'*64,'b'*64,s)
    def test_missing_duplicate_targets_refused(self):
        for duplicate in (False,True):
            c,g,e,p,s=self.fixture()
            if duplicate:e['targets'].append(copy.deepcopy(e['targets'][0]))
            else:e['targets'].pop()
            with self.assertRaises(ValueError):c.summarize(g,e,p,'a'*64,'b'*64,s)
    def test_nonfinite_or_invalid_counts_refused(self):
        for key,value in (('max_penetration_mm',float('nan')),('contact_vertices_within_2mm',-1),('finger_vertices',True)):
            c,g,e,p,s=self.fixture();g['poses']['curl_handle']['pre_close']['l'][key]=value
            with self.assertRaises(ValueError):c.summarize(g,e,p,'a'*64,'b'*64,s)
    def test_changed_gate_refused(self):
        c,g,e,p,s=self.fixture();g['acceptance_gate_mm']=3
        with self.assertRaisesRegex(ValueError,'gate'):c.summarize(g,e,p,'a'*64,'b'*64,s)
    def test_closing_added_penetration_is_observation_not_cause(self):
        c,g,e,p,s=self.fixture();pre=g['poses']['curl_handle']['pre_close']['l'];pre['max_penetration_mm']=0
        pre['deepest'][0].update(signed_distance_mm=0,penetration_mm=0)
        r=c.summarize(g,e,p,'a'*64,'b'*64,s)['grip_observations'][0]
        self.assertFalse(r['penetration_present_before_close']);self.assertEqual(r['closing_delta_mm'],5.93)
    def test_invalid_handle_or_vertex_refused(self):
        c,g,e,p,s=self.fixture();g['poses']['curl_handle']['handle']['l']['axis']=[0,0,0]
        with self.assertRaises(ValueError):c.summarize(g,e,p,'a'*64,'b'*64,s)
        c,g,e,p,s=self.fixture();e['targets'][0]['edges'][0]['vertices']=[-1,11]
        with self.assertRaises(ValueError):c.summarize(g,e,p,'a'*64,'b'*64,s)

if __name__=='__main__':unittest.main()
