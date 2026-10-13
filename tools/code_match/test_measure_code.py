"""Run with: python3 -m unittest discover -s tools/code_match -p 'test_*.py'."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measure_code import measure


class CoverageChecks(unittest.TestCase):
    def test_missing_method_keeps_weight(self):
        original = {'large': dict(identity='large', scope='game', code_bytes='90', sha256='a'),
                    'small': dict(identity='small', scope='game', code_bytes='10', sha256='b')}
        result = measure(original, {'small': original['small']}, {'game'})
        self.assertEqual(result['total_code_bytes'], 100)
        self.assertEqual(result['matched_code_bytes'], 10)
        self.assertEqual(result['missing_methods'], 1)
        self.assertEqual(result['code_matched_percent'], 10)

    def test_extra_code_does_not_earn_credit(self):
        row = dict(identity='original', scope='game', code_bytes='10', sha256='a')
        result = measure({'original': row}, {'original': row, 'extra': row}, {'game'})
        self.assertEqual(result['total_code_bytes'], 10)
        self.assertEqual(result['matched_code_bytes'], 10)
        self.assertEqual(result['extra_methods'], 1)
