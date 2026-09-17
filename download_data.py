"""Download IBM Skills Network teaching snapshots, preserving source hashes."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
BASE = 'https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/'
SOURCES = {
    'dataset_part_1.csv': BASE + 'datasets/dataset_part_1.csv',
    'dataset_part_2.csv': BASE + 'datasets/dataset_part_2.csv',
    'Spacex.csv': BASE + 'Spacex.csv',
    'spacex_launch_dash.csv': BASE + 'datasets/spacex_launch_dash.csv',
    'spacex_launch_geo.csv': BASE + 'datasets/spacex_launch_geo.csv',
    'spacex_launches.json': 'https://api.spacexdata.com/v4/launches/past',
    'wikipedia_snapshot.html': 'https://en.wikipedia.org/w/index.php?title=List_of_Falcon_9_and_Falcon_Heavy_launches&oldid=1027686922',
}

def download(item):
    name, url = item
    path = ROOT / 'data' / name
    path.parent.mkdir(exist_ok=True)
    try:
        if path.exists():
            payload = path.read_bytes()
            return dict(file=name, url=url, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), status='cached')
        request = urllib.request.Request(url, headers={'User-Agent': 'CapstoneStudy/1.0 (educational analysis)'})
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
        path.write_bytes(payload)
        return dict(file=name, url=url, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), status='downloaded')
    except Exception as exc:
        return dict(file=name, url=url, status='unavailable', error=str(exc))

if __name__ == '__main__':
    records = list(ThreadPoolExecutor(max_workers=7).map(download, SOURCES.items()))
    (ROOT / 'data' / 'sources.json').write_text(json.dumps(records, indent=2))
    print(json.dumps(records, indent=2))
