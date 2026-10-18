"""R51 source and unsafe search seed must be exact immutable reviewed inputs."""
import hashlib,os,unittest
from pathlib import Path
class Preparation(unittest.TestCase):
 def test_immutable_source_and_seed(self):
  for env,expected in [('HGPT_R51_RESPONSE','2a6c01cf7eacd3d1ceb47ae9f131f76dd0487fce5d3518d5cd1df65bc059fa8d'),('HGPT_R51_SEED','c777f0dd05e7866c0f56b64af68edb6441ce2f1799069f00bf09bce5c3690241')]:
   with self.subTest(env=env):self.assertEqual(hashlib.sha256(Path(os.environ[env]).read_bytes()).hexdigest(),expected)
if __name__=='__main__':unittest.main()
