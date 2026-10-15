import unittest
from pathlib import Path
from tracelens import analyze, load_events
from tracelens.core import percentile

ROOT = Path(__file__).resolve().parents[1]

class TestTraceLens(unittest.TestCase):
    def test_load_csv(self):
        self.assertEqual(len(load_events(ROOT/'samples'/'requests.csv')), 12)
    def test_findings(self):
        report = analyze(load_events(ROOT/'samples'/'requests.csv'))
        self.assertEqual(report['summary']['requests'], 12)
        self.assertTrue(any(f['issue']=='Elevated 5xx error rate' for f in report['findings']))
        self.assertTrue(any(f['issue']=='High p95 latency' for f in report['findings']))
    def test_empty(self):
        self.assertEqual(analyze([])['summary']['requests'], 0)
    def test_percentile(self):
        self.assertEqual(percentile([10,20,30],50),20)
    def test_invalid(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'bad.jsonl'
            p.write_text('{"timestamp":"2026-10-15T12:00:00Z","method":"GET","path":"/","status":700,"latency_ms":1}\n')
            with self.assertRaises(ValueError):
                load_events(p)

if __name__=='__main__':
    unittest.main()
