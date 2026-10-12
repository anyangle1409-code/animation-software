import unittest,math,copy
import original_shoulder_bind_semantics as bind

I=((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1))
def frame(x=0,y=0,z=0,a=0):
 c,s=math.cos(a),math.sin(a)
 return ((c,-s,0,x),(s,c,0,y),(0,0,1,z),(0,0,0,1))
class BindSemanticsTests(unittest.TestCase):
 def close(self,a,b):
  self.assertLess(max(abs(a[r][c]-b[r][c]) for r in range(4) for c in range(4)),1e-9)
 def test_preserves_target_rest_without_moving_either_starting_frame(self):
  s,t=frame(1,2,3,.6),frame(-.2,.3,1.5,-.8)
  original=copy.deepcopy((s,t))
  offset=bind.bind_offset(s,t)
  self.close(bind.transfer_world(s,offset),t)
  self.assertEqual((s,t),original)
 def test_offset_rotates_around_source_pivot_and_does_not_snap_joint_centres(self):
  offset=bind.bind_offset(I,frame(.1,0,0))
  posed=bind.transfer_world(frame(a=math.pi/2),offset)
  self.assertAlmostEqual(posed[0][3],0)
  self.assertAlmostEqual(posed[1][3],.1)
  self.assertAlmostEqual(bind.separation_m(frame(a=math.pi/2),posed),.1)
 def test_common_world_frame_change_preserves_bind_offset(self):
  s,t,g=frame(1,2,3,.2),frame(-1,3,1,-.4),frame(3,-2,1,.9)
  o=bind.bind_offset(s,t)
  self.close(o,bind.bind_offset(bind.multiply(g,s),bind.multiply(g,t)))
 def test_coincident_pivots_can_preserve_distinct_axes(self):
  s,t=frame(1,2,3,.2),frame(1,2,3,-.4)
  p=frame(1,2,3,.8)
  q=bind.transfer_world(p,bind.bind_offset(s,t))
  self.assertAlmostEqual(bind.separation_m(p,q),0)
  self.close(q,frame(1,2,3,.2))
 def test_reflection_scale_shear_non_affine_nonfinite_and_bool_are_refused(self):
  bad=[]
  for row,col,val in [(0,0,-1),(1,1,2),(0,1,.2),(3,0,.1),(0,3,float('nan')),(0,0,True)]:
   m=[list(r) for r in I];m[row][col]=val;bad.append(m)
  bad.extend([[],[[1,0],[0,1]]])
  for m in bad:
   with self.subTest(m=m),self.assertRaises(ValueError):bind.bind_offset(m,I)
 def test_posed_world_frame_is_validated_too(self):
  m=[list(r) for r in I];m[0][0]=0
  with self.assertRaises(ValueError):bind.transfer_world(m,I)
 def test_nonfinite_distance_from_extreme_finite_frames_is_refused(self):
  with self.assertRaises(ValueError):bind.separation_m(frame(1e308),frame(-1e308))

if __name__=='__main__':unittest.main()
