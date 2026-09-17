import unittest
import json
import hashlib
from pathlib import Path
import pandas as pd
from analyze import wrangle
from dashboard import figures,app
from build_map import km

ROOT=Path(__file__).resolve().parent

class ProjectTests(unittest.TestCase):
    def test_labels(self):
        d=wrangle()
        self.assertEqual(len(d),90)
        self.assertEqual(int(d.Class.sum()),60)
    def test_dashboard(self):
        pie,scatter,count=figures('ALL',[0,10000])
        self.assertIn('56 launch records',count)
        self.assertEqual(int(sum(pie.data[0].values)),24)
        pie,scatter,count=figures('KSC LC-39A',[0,10000])
        self.assertIn('13 launch records',count)
        self.assertEqual(sorted(map(int,pie.data[0].values)),[3,10])
        self.assertIn('0 launch records',figures('ALL',[9900,10000])[2])
        client=app.server.test_client()
        self.assertEqual(client.get('/').status_code,200)
        self.assertEqual(client.get('/_dash-layout').status_code,200)
        self.assertEqual(len(app.callback_map),1)
    def test_sources(self):
        for item in json.loads((ROOT/'data/sources.json').read_text()):
            if 'sha256' in item:
                self.assertEqual(hashlib.sha256((ROOT/'data'/item['file']).read_bytes()).hexdigest(),item['sha256'])
    def test_proximity(self):
        self.assertAlmostEqual(km([0,0],[0,0]),0)
        self.assertAlmostEqual(km([0,0],[0,1]),111.195,places=2)
    def test_scraped(self):
        d=pd.read_csv(ROOT/'data/web_scraped_launches.csv')
        self.assertEqual(len(d),121)
        self.assertTrue(d.FlightNumber.is_unique)

if __name__=='__main__':
    unittest.main()
