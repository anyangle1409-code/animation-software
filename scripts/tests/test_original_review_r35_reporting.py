import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from original_review_r35_reports import validate_samples

class CompleteSampleTests(unittest.TestCase):
    def fixtures(self):
        press={'press':[{'t':i/40} for i in range(41)]}
        benchmarks={'benchmarks':{str(i):{'frames':[{'t':j/8} for j in range(9)]} for i in range(13)}}
        return press,benchmarks

    def test_complete_matching_reports_pass(self):
        p,b=self.fixtures();validate_samples(p,p,b,b)

    def test_truncated_press_rejected(self):
        p,b=self.fixtures();q={'press':p['press'][:-1]}
        with self.assertRaises(ValueError):validate_samples(p,q,b,b)

    def test_mismatched_press_time_rejected(self):
        p,b=self.fixtures();q={'press':[dict(x) for x in p['press']]};q['press'][10]['t']=.26
        with self.assertRaises(ValueError):validate_samples(p,q,b,b)

    def test_missing_benchmark_rejected(self):
        p,b=self.fixtures();q={'benchmarks':dict(b['benchmarks'])};q['benchmarks'].pop('12')
        with self.assertRaises(ValueError):validate_samples(p,p,b,q)

    def test_truncated_benchmark_rejected(self):
        p,b=self.fixtures();q={'benchmarks':dict(b['benchmarks'])};q['benchmarks']['0']={'frames':[{'t':0}]}
        with self.assertRaises(ValueError):validate_samples(p,p,b,q)

    def test_mismatched_benchmark_time_rejected(self):
        p,b=self.fixtures();q={'benchmarks':dict(b['benchmarks'])};q['benchmarks']['0']={'frames':[{'t':j/9} for j in range(9)]}
        with self.assertRaises(ValueError):validate_samples(p,p,b,q)

if __name__=='__main__':unittest.main()
