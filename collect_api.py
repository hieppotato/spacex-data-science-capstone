"""Optional live SpaceX community API collector. IBM snapshot supports offline runs.

The live API failed during this run. This file is provided for a future refresh,
not represented as a successfully executed source of the report's observations.
"""
from pathlib import Path
from functools import lru_cache
import json
import requests
import pandas as pd

BASE='https://api.spacexdata.com/v4'
ROOT=Path(__file__).resolve().parent

@lru_cache(None)
def lookup(kind, ident):
    response=requests.get(f'{BASE}/{kind}/{ident}',timeout=30)
    response.raise_for_status()
    return response.json()

def collect():
    response=requests.get(f'{BASE}/launches/past',timeout=45)
    response.raise_for_status()
    raw=response.json()
    (ROOT/'data/api_launches_raw.json').write_text(json.dumps(raw))
    result=[]
    for launch in raw:
        if len(launch['cores'])!=1 or len(launch['payloads'])!=1:
            continue
        rocket=lookup('rockets',launch['rocket'])
        if rocket['name']!='Falcon 9' or launch['date_utc'][:10]>'2020-11-13':
            continue
        core=launch['cores'][0]
        payload=lookup('payloads',launch['payloads'][0])
        pad=lookup('launchpads',launch['launchpad'])
        details=lookup('cores',core['core']) if core['core'] else {}
        result.append(dict(Date=launch['date_utc'][:10],FlightNumber=launch['flight_number'],
                           PayloadMass=payload.get('mass_kg'),Orbit=payload.get('orbit'),
                           LaunchSite=pad['name'],Latitude=pad['latitude'],Longitude=pad['longitude'],
                           Outcome=f"{core.get('landing_success')} {core.get('landing_type')}",
                           Flights=core.get('flight'),Reused=core.get('reused'),
                           GridFins=core.get('gridfins'),Legs=core.get('legs'),Block=details.get('block')))
    df=pd.DataFrame(result).sort_values('Date')
    df.to_csv(ROOT/'data/api_refreshed.csv',index=False)
    return df

if __name__=='__main__':
    print(collect().shape)
