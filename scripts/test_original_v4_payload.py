import json
import unittest
from pathlib import Path

from validate_original_v4_payload import validate


DATA = json.loads((Path(__file__).resolve().parents[1] / 'ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json').read_text())


class V4PayloadTests(unittest.TestCase):
    def test_committed_payload(self):
        self.assertEqual(validate(DATA), [])

    def test_rejects_mirror_drift(self):
        copy = json.loads(json.dumps(DATA))
        next(b for b in copy['bones'] if b['name'] == 'forearm_r')['head'][0] += .01
        self.assertIn('forearm_l mirror', validate(copy))

    def test_rejects_bad_parent_and_count(self):
        copy = json.loads(json.dumps(DATA))
        next(b for b in copy['bones'] if b['name'] == 'upperarm_l')['parent'] = 'pelvis'
        self.assertIn('upperarm_l parent', validate(copy))
        copy['bones'].pop()
        self.assertIn('bone count', validate(copy))


if __name__ == '__main__':
    unittest.main()
