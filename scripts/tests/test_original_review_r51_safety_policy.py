"""Unsafe internal search must preserve every final nonlinear gate and limit."""
import ast,os,unittest
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parents[1]

def tree(path):return ast.parse(Path(path).read_text())
def node_dump(node):return ast.dump(node,include_attributes=False)

class SafetyPolicy(unittest.TestCase):
    def test_final_nonlinear_gate_and_limits_match_r50(self):
        old=tree(SCRIPTS/'solve_original_review_r50.py')
        new=tree(SCRIPTS/'solve_original_review_r51.py')
        for name in ['nonprofile_ok','fail']:
            a=next(n for n in ast.walk(old) if isinstance(n,ast.FunctionDef) and n.name==name)
            b=next(n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(node_dump(a),node_dump(b),name)
        for name in ['upper','lower','motion_limit','rear_limits','rear_needed']:
            def assignments(t):
                return [node_dump(n.value) for n in ast.walk(t) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id==name for v in n.targets)]
            self.assertEqual(assignments(old),assignments(new),name)

if __name__=='__main__':unittest.main()

