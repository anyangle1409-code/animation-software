"""Synthetic pinned-edge contracts; fixtures are not native anatomy evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).resolve().parents[2]/'phone_blender'/'row_pinned_edges.py'
S=importlib.util.spec_from_file_location('row_edges',P)
m=importlib.util.module_from_spec(S);S.loader.exec_module(m)


def geometry():
    points=[(0.,0.,0.)]*(max(max(x[1]) for x in m.TARGETS)+1)
    faces=[]
    for i,(_,pair,*_) in enumerate(m.TARGETS):
        a,b=pair;points[a]=(i*3.,0.,0.);points[b]=(i*3.+1.,0.,0.)
        faces.append((a,b,0))
    return points,faces


def evidence():
    v,f=geometry();ref=m.reference(v,f,len(v),f)
    return m.report(ref,[m.snapshot(v,f,ref,i) for i in range(9)])


class RowPinnedEdgeTests(unittest.TestCase):
    def test_native_iterable_vectors_are_supported(self):
        class NativeVector:
            def __init__(self, values): self.values=values
            def __iter__(self): return iter(self.values)
        v,f=geometry()
        for _,pair,*_ in m.TARGETS:
            for i in pair:v[i]=NativeVector(v[i])
        ref=m.reference(v,f,len(v),f)
        self.assertEqual(m.snapshot(v,f,ref,0)['edges'][0]['length_ratio_to_neutral'],1.)

    def test_valid_report_replays_with_limitations(self):
        d=evidence();self.assertEqual(m.validate_report(d),[])
        self.assertIn('not tissue strain',m.markdown(d));self.assertIn('different reference',m.markdown(d))

    def test_independent_half_double_lengths(self):
        v,f=geometry();ref=m.reference(v,f,len(v),f);v=list(v)
        a,b=m.TARGETS[0][1];v[b]=(v[a][0]+0.5,0.,0.)
        a,b=m.TARGETS[1][1];v[b]=(v[a][0]+2.,0.,0.)
        row=m.snapshot(v,f,ref,1)
        self.assertEqual([r['length_ratio_to_neutral'] for r in row['edges']][:2],[0.5,2.0])
        self.assertEqual([r['posed_length_mm'] for r in row['edges']][:2],[500.,2000.])

    def test_rigid_transform_does_not_change_ratio(self):
        v,f=geometry();ref=m.reference(v,f,len(v),f)
        changed=[(5-y,7+x,3+z) for x,y,z in v]
        row=m.snapshot(changed,f,ref,1)
        self.assertEqual([r['length_ratio_to_neutral'] for r in row['edges']],[1.]*4)

    def test_zero_posed_length_is_recorded_not_hidden(self):
        v,f=geometry();ref=m.reference(v,f,len(v),f);v=list(v)
        a,b=m.TARGETS[0][1];v[b]=v[a]
        row=m.snapshot(v,f,ref,1)
        self.assertEqual(row['edges'][0]['posed_length_mm'],0.)
        self.assertEqual(row['edges'][0]['length_ratio_to_neutral'],0.)

    def test_negative_near_zero_lengths_or_ratios_are_rejected(self):
        v,f=geometry();ref=m.reference(v,f,len(v),f);v=list(v)
        a,b=m.TARGETS[0][1];v[b]=v[a]
        rows=[m.snapshot(v,f,ref,i) for i in range(9)]
        for field in ['posed_length_mm','length_ratio_to_neutral']:
            with self.subTest(field=field):
                d=m.report(ref,copy.deepcopy(rows));d['samples'][0]['edges'][0][field]=-1e-12
                self.assertTrue(m.validate_report(d),field)

    def test_source_and_evaluated_topology_must_match(self):
        v,f=geometry()
        for count,faces in [(len(v)-1,f),(len(v),list(reversed(f)))]:
            with self.assertRaises(ValueError):m.reference(v,f,count,faces)
        with self.assertRaises(ValueError):m.reference(v,[(0,1,2)],len(v),[(0,1,2)])

    def test_pose_topology_or_vertex_count_drift_fails(self):
        v,f=geometry();ref=m.reference(v,f,len(v),f)
        for vertices,faces in [(v[:-1],f),(v,list(reversed(f)))]:
            with self.assertRaises(ValueError):m.snapshot(vertices,faces,ref,0)

    def test_degenerate_neutral_or_nonfinite_points_fail(self):
        v,f=geometry();a,b=m.TARGETS[0][1]
        for point in [v[a],(float('nan'),0.,0.),(1e308,0.,0.)]:
            bad=list(v);bad[b]=point
            with self.assertRaises(ValueError):m.reference(bad,f,len(bad),f)

    def test_derived_ratio_and_length_tampering_fails(self):
        for field in ['posed_length_mm','length_ratio_to_neutral']:
            d=evidence();d['samples'][0]['edges'][0][field]+=0.1
            self.assertTrue(m.validate_report(d))
        d=evidence();d['reference']['edges'][0]['neutral_length_mm']+=1
        self.assertTrue(m.validate_report(d))

    def test_false_float_and_reordered_ids_rejected(self):
        for value in [False,0.0]:
            d=evidence();d['samples'][0]['sample']=value;self.assertTrue(m.validate_report(d))
        d=evidence();d['samples'][0]['edges'][0]['vertex_ids']=[15645.,53019]
        self.assertTrue(m.validate_report(d))
        d=evidence();d['samples'][0]['edges'].reverse();self.assertTrue(m.validate_report(d))

    def test_malformed_nested_data_returns_errors(self):
        d=evidence();d['reference']=None;self.assertTrue(m.validate_report(d))
        d=evidence();d['samples']=None;self.assertTrue(m.validate_report(d))
        for value in [None,[],{'edges':None},{'edges':[None]*4}]:
            d=evidence();d['samples'][0]=value;self.assertTrue(m.validate_report(d))

    def test_scope_and_reference_labels_cannot_drift(self):
        for field,value in [('anatomy_approved',True),('plain_keys_zero',False),('reference_kind','historical_press'),('source_sha256','0'*64),('complete_elbow_region',True)]:
            d=evidence();d[field]=value;self.assertTrue(m.validate_report(d))
        d=evidence();d['limitations'].pop();self.assertTrue(m.validate_report(d))

    def test_invalid_topology_and_digest_rejected(self):
        v,f=geometry()
        for bad in [[(True,1,2)],[(0,0,1)],[(0,1,len(v))]]:
            with self.assertRaises(ValueError):m.reference(v,bad,len(v),bad)
        d=evidence();d['reference']['topology_sha256']='invalid';self.assertTrue(m.validate_report(d))
        d=evidence();d['samples'][0]['topology_sha256']='0'*64;self.assertTrue(m.validate_report(d))


if __name__=='__main__':unittest.main()
