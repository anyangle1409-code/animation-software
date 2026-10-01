import copy
import importlib
import json
from pathlib import Path
import tempfile
import unittest


class SurfaceAuditTests(unittest.TestCase):
    def module(self):return importlib.import_module('audit_original_v1_surface')
    def tetra(self):
        from test_original_v1_change_audit import AuditTests
        s=AuditTests().snapshot()
        s.update(vertices=[[-1,0,0],[1,0,0],[0,1,0],[0,0,1]],
            faces=[[0,2,1],[0,1,3],[1,2,3],[2,0,3]],regions=['hand','hand','torso','torso'],
            weights=[{'hand_l':1},{'hand_r':1},{'spine_02':1},{'spine_02':1}],
            mirror_pairs=[[0,1],[2,2],[3,3]],ambiguous_mirror_vertex_ids=[])
        return s
    def test_closed_oriented_tetra_is_evidence_not_phase_pass(self):
        r=self.module().audit_surface(self.tetra())
        self.assertEqual(r['boundary_edges'],[]);self.assertEqual(r['nonmanifold_edges'],[])
        self.assertEqual(r['nonmanifold_vertex_ids'],[]);self.assertEqual(r['winding_conflict_edges'],[])
        self.assertEqual(r['components'][0]['orientation_hint'],'POSITIVE_SIGNED_VOLUME')
        self.assertAlmostEqual(r['components'][0]['signed_volume_m3'],1/3)
        self.assertFalse(r['production_approved']);self.assertFalse(r['phase_complete'])
        self.assertEqual(r['symmetry']['unmatched_face_ids'],[])
    def test_open_surface_boundary_and_valid_vertex_links(self):
        s=self.tetra();s['faces'].pop();r=self.module().audit_surface(s)
        self.assertEqual(len(r['boundary_edges']),3);self.assertEqual(r['nonmanifold_vertex_ids'],[])
        self.assertIsNone(r['components'][0]['orientation_hint'])
    def test_flipped_face_winding_detected(self):
        s=self.tetra();s['faces'][0].reverse();r=self.module().audit_surface(s)
        self.assertEqual(len(r['winding_conflict_edges']),3)
        self.assertIsNone(r['components'][0]['orientation_hint'])
    def test_entire_inward_shell_signed_volume_retained(self):
        s=self.tetra();s['faces']=[list(reversed(f)) for f in s['faces']]
        r=self.module().audit_surface(s);self.assertEqual(r['components'][0]['orientation_hint'],'NEGATIVE_SIGNED_VOLUME')
        self.assertAlmostEqual(r['components'][0]['signed_volume_m3'],-1/3)
    def test_three_face_edge_detected(self):
        s=self.tetra();s['faces'].append([0,1,2]);r=self.module().audit_surface(s)
        self.assertEqual(len(r['nonmanifold_edges']),3);self.assertTrue(r['nonmanifold_vertex_ids'])
    def test_touching_closed_shells_detect_vertex_link_defect(self):
        s=self.tetra();s['vertices'] += [[5,0,0],[2,1,0],[2,0,1]]
        s['weights'] += [{'spine_02':1}]*3;s['regions'] += ['torso']*3
        mapping={0:0,1:4,2:5,3:6};s['faces'] += [[mapping[v] for v in f] for f in list(s['faces'])]
        r=self.module().audit_surface(s)
        self.assertEqual(r['nonmanifold_edges'],[]);self.assertIn(0,r['nonmanifold_vertex_ids'])
        self.assertEqual(len(r['components']),2)
    def test_orphan_and_duplicate_coordinates_are_reported(self):
        s=self.tetra();s['vertices'].append(list(s['vertices'][0]));s['weights'].append({'hand_l':1});s['regions'].append('hand')
        r=self.module().audit_surface(s);self.assertEqual(r['isolated_vertex_ids'],[4])
        self.assertIn([0,4],r['coincident_coordinate_groups']);self.assertFalse(r['symmetry']['full_vertex_coverage'])
    def test_cyclic_reverse_duplicate_faces_detected(self):
        s=self.tetra();s['faces'].append([1,2,0]);r=self.module().audit_surface(s)
        self.assertEqual(r['duplicate_face_groups'],[[0,4]])
    def test_repeated_indices_excluded_from_manifold_calculation(self):
        s=self.tetra();s['faces'].append([0,0,1]);r=self.module().audit_surface(s)
        self.assertEqual(r['repeated_vertex_face_ids'],[4]);self.assertEqual(r['excluded_face_ids'],[4])
    def test_vertices_in_excluded_faces_are_not_called_raw_orphans(self):
        s=self.tetra();s['faces']=[[0,0,1]];r=self.module().audit_surface(s)
        self.assertEqual(r['isolated_vertex_ids'],[2,3]);self.assertEqual(r['vertices_only_in_excluded_faces'],[0,1])
    def test_collinear_and_declared_near_degenerate_faces(self):
        s=self.tetra();s.update(vertices=[[0,0,0],[1,0,0],[2,0,0]],weights=s['weights'][:3],regions=s['regions'][:3],faces=[[0,1,2]])
        r=self.module().audit_surface(s);self.assertEqual(r['exact_zero_area_face_ids'],[0])
        s['vertices'][2][1]=1e-13;r=self.module().audit_surface(s)
        self.assertEqual(r['near_degenerate_face_ids'],[0]);self.assertEqual(r['exact_zero_area_face_ids'],[])
        r=self.module().audit_surface(s,area_epsilon_m2=0);self.assertEqual(r['near_degenerate_face_ids'],[])
    def test_nonplanar_ngon_detected_without_claiming_triangulation(self):
        s=self.tetra();s['vertices']=[[0,0,0],[1,0,0],[1,1,0.1],[0,1,0]];s['faces']=[[0,1,2,3]]
        r=self.module().audit_surface(s);self.assertEqual(r['nonplanar_face_ids'],[0])
        self.assertTrue(any('triangulation' in x for x in r['limits']))
    def test_symmetry_missing_faces_are_visible(self):
        s=self.tetra();s['faces'].pop();r=self.module().audit_surface(s)
        self.assertTrue(r['symmetry']['unmatched_face_ids'])
    def test_invalid_precision_or_coordinate_refused(self):
        for epsilon in (-1,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):self.module().audit_surface(self.tetra(),area_epsilon_m2=epsilon)
        s=self.tetra();s['vertices'][0][0]='bad'
        with self.assertRaises(ValueError):self.module().audit_surface(s)
    def test_deterministic_report(self):
        c=self.module();s=self.tetra();self.assertEqual(c.audit_surface(s),c.audit_surface(copy.deepcopy(s)))
    def cli(self,root,args):
        from unittest.mock import patch
        import contextlib,io
        c=self.module()
        with patch.object(c,'ROOT',root),patch('sys.argv',['audit_original_v1_surface.py',*map(str,args)]),patch.object(c.subprocess,'check_output',return_value='b'*40),contextlib.redirect_stdout(io.StringIO()):
            return c.main()
    def inputs(self,root):
        snapshot=root/'snapshot.json';manifest=root/'candidate.json'
        snapshot.write_text(json.dumps(self.tetra()));manifest.write_text(json.dumps({'candidate_sha256':'a'*64}))
        (root/'scripts').mkdir()
        for name in ('audit_original_v1_surface.py','audit_original_v1_changes.py'):
            (root/'scripts'/name).write_bytes((Path(__file__).parent/name).read_bytes())
        return [snapshot,'--candidate-manifest',manifest]
    def test_cli_binds_actual_source_files_and_writes_no_approval(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);args=self.inputs(root);out=root/'surface.json';md=root/'surface.md'
            self.assertEqual(self.cli(root,args+['--json-out',out,'--markdown-out',md]),0)
            result=json.loads(out.read_text());self.assertEqual(result['status'],'EVIDENCE_ONLY')
            self.assertFalse(result['phase_complete']);self.assertFalse(result['production_approved'])
            for ref in result['source_evidence']:self.assertEqual(hashlib.sha256((root/ref['path']).read_bytes()).hexdigest(),ref['sha256'])
            self.assertIn('Unresolved domain checks',md.read_text())
    def test_cli_preserves_existing_output_and_refuses_alias(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);args=self.inputs(root);out=root/'preserve.json';out.write_text('keep')
            self.assertEqual(self.cli(root,args+['--json-out',out]),2);self.assertEqual(out.read_text(),'keep')
            out=root/'new.json';self.assertEqual(self.cli(root,args+['--json-out',out,'--markdown-out',out]),2)
            self.assertFalse(out.exists())
    def test_cli_refuses_manifest_mismatch_and_external_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);args=self.inputs(root);out=root/'surface.json'
            (root/'candidate.json').write_text(json.dumps({'candidate_sha256':'c'*64}))
            self.assertEqual(self.cli(root,args+['--json-out',out]),2);self.assertFalse(out.exists())
            self.assertEqual(self.cli(root,args+['--json-out',root.parent/'outside-surface.json']),2)
    def test_cli_invalid_json_shape_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);args=self.inputs(root);(root/'snapshot.json').write_text('[]');out=root/'surface.json'
            self.assertEqual(self.cli(root,args+['--json-out',out]),2);self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
