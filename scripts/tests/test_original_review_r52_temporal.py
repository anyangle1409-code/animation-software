import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
try:
 from original_review_r52_temporal import decode,blend,blend_adjoint,oscillation
except ImportError:
 decode=blend=blend_adjoint=oscillation=None
from original_review_r43_sampling import basis,hats,KEYS,DENSE
try:from original_review_r52_temporal import response_basis
except ImportError:response_basis=None
class Temporal(unittest.TestCase):
 def test_exact_old_cubic_including_negative_coefficients(self):
  self.assertIsNotNone(decode,'Independent temporal decoder not implemented')
  rng=np.random.default_rng(52);e=np.array([85,95,97.25,110,118,135.625,156.4,166]);old=hats(e,DENSE)@basis();w=np.repeat(old[:,:,None],5,axis=2)
  delta=rng.normal(size=(7,5,3));dense=np.concatenate([np.zeros((1,5,3)),np.einsum('dk,knj->dnj',basis(),delta)])
  mapped=blend(dense,decode(w));np.testing.assert_allclose(mapped,np.einsum('skn,knj->snj',w,delta),atol=1e-12)
 def test_forward_adjoint(self):
  self.assertIsNotNone(decode)
  rng=np.random.default_rng(521);old=hats(np.linspace(96,166,9),DENSE)@basis();w=np.repeat(old[:,:,None],4,axis=2);m=decode(w);x=rng.normal(size=(72,4,3));y=rng.normal(size=(9,4,3))
  self.assertAlmostEqual(float((blend(x,m)*y).sum()),float((x*blend_adjoint(y,m,72)).sum()),places=10)
 def test_reject_invalid_weights(self):
  self.assertIsNotNone(decode)
  for x in [np.full((2,7,3),np.nan),np.ones((2,7,3))]:
   with self.assertRaises(ValueError):decode(x)
 def test_reject_hidden_90mm_jump(self):
  self.assertIsNotNone(oscillation)
  x=np.zeros((72,2,3));x[20,0,0]=.045;x[21,0,0]=-.045
  z=oscillation(x,limit_mm=3.)
  self.assertFalse(z['passed']);self.assertEqual(z['maximum_adjacent_mm'],90.)
 def test_native_decoder_basis_needs_only_numpy(self):
  self.assertIsNotNone(response_basis,'Native decoder requires a SciPy-free basis')
  expected=basis()
  from unittest.mock import patch
  with patch.dict(sys.modules,{'scipy':None,'scipy.interpolate':None}):
   np.testing.assert_allclose(response_basis(),expected,atol=2e-15,rtol=0.)
   w=np.repeat(expected[::10,:,None],2,axis=2);decode(w)
if __name__=='__main__':unittest.main()
