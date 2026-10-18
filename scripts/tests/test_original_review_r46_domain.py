"""R46 refines the fit without expanding the editable material domain."""
import os,hashlib,unittest
import numpy as np
EXPECTED={'free': '7f3d7c22627cbc4388f6d15a2586ad329b2e1f2f6347454c4463f765493b3ce9', 'frozen_arm': '0aed9a8b1878655f7b273134c0d90f17fecef50961f3d32b5fe3eef1f57ae0d0', 'rest': '0435a7a9791664834747f06f8ece1ece5e6ba96b6ae985ec796bc5fc9a526c36', 'faces': '99fd2373bc340c8d35138e53bb44098f5437ad00cb8bf94b1855388696318869'}
class FixedDomain(unittest.TestCase):
 def test_same_material_scope_as_r43(self):
  with np.load(os.environ['HGPT_R46_RESPONSE']) as z:
   for key,digest in EXPECTED.items():
    with self.subTest(key=key):self.assertEqual(hashlib.sha256(z[key].tobytes()).hexdigest(),digest)
if __name__=='__main__':unittest.main()
