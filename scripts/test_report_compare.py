import unittest

from report_compare import report_differences


class ReportCompareTests(unittest.TestCase):
    def test_last_digit_float_noise_is_accepted(self):
        self.assertEqual(report_differences({'a': [0.88187380379272]}, {'a': [0.8818738037927193]}), [])

    def test_real_differences_are_reported(self):
        base = {'n': 34, 'freeze_ready': False, 'x': 1.0, 's': 'LM15', 'v': [1.0, 2.0], 'g': None}
        for changed in ({**base, 'n': 35}, {**base, 'freeze_ready': True}, {**base, 'x': 1.000001}, {**base, 's': 'LM16'},
                        {**base, 'v': [1.0]}, {**base, 'g': 0.0}, {**base, 'extra': 1}, {**base, 'freeze_ready': 0}):
            self.assertNotEqual(report_differences(base, changed), [], changed)


if __name__ == '__main__':
    unittest.main()
