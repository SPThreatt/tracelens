import unittest
from backend.app import parse_bytes, build_dashboard

class ApiTests(unittest.TestCase):
    def test_csv_parsing(self):
        data = b'timestamp,method,path,status,latency_ms\n2026-10-15T12:00:00Z,GET,/health,200,42\n'
        result = parse_bytes('test.csv', data)
        self.assertEqual(result[0]['path'], '/health')
        self.assertEqual(build_dashboard(result)['summary']['requests'], 1)

    def test_jsonl_parsing(self):
        data = b'{"timestamp":"2026-10-15T12:00:00Z","method":"GET","path":"/a","status":503,"latency_ms":2000}\n'
        result = build_dashboard(parse_bytes('test.jsonl', data))
        self.assertEqual(result['summary']['error_rate'], 1)
        self.assertTrue(result['findings'])

    def test_invalid_file(self):
        with self.assertRaises(ValueError):
            parse_bytes('invalid.txt', b'hello')

    def test_bad_csv(self):
        with self.assertRaises(ValueError):
            parse_bytes('invalid.csv', b'wrong,headers\na,b\n')

    def test_empty_file(self):
        report = build_dashboard(parse_bytes('empty.jsonl', b''))
        self.assertEqual(report['summary']['requests'], 0)
        self.assertEqual(report['timeline'], [])
