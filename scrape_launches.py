"""Extract launch rows from the archived Wikipedia page, not narrative rows."""
from pathlib import Path
import re
import pandas as pd
from bs4 import BeautifulSoup
from dateutil.parser import parse

ROOT = Path(__file__).resolve().parent

def scrape():
    soup = BeautifulSoup((ROOT/'data/wikipedia_snapshot.html').read_text(), 'html.parser')
    rows = []
    for table in soup.find_all('table'):
        first = table.find('tr')
        if not first or 'Flight No.' not in first.get_text(' ',strip=True) or 'Booster landing' not in first.get_text(' ',strip=True):
            continue
        for tr in table.find_all('tr')[1:]:
            cells = tr.find_all(['td','th'], recursive=False)
            if len(cells) != 10:
                continue
            for c in cells:
                for sup in c.find_all('sup'):
                    sup.decompose()
            v = [re.sub(r'\s+',' ',c.get_text(' ',strip=True)).strip() for c in cells]
            if not re.fullmatch(r'\d+',v[0]):
                continue  # Falcon Heavy and non-numbered anomalies are separate.
            try:
                date = parse(v[1], fuzzy=True).date().isoformat()
            except ValueError:
                continue
            mass = re.search(r'([\d,]+(?:\.\d+)?)\s*kg',v[5])
            rows.append(dict(FlightNumber=int(v[0]),Date=date,BoosterVersion=v[2],LaunchSite=v[3],
                             Payload=v[4],PayloadMass=float(mass.group(1).replace(',','')) if mass else None,
                             Orbit=v[6],Customer=v[7],MissionOutcome=v[8],LandingOutcome=v[9]))
    df = pd.DataFrame(rows).sort_values('FlightNumber').drop_duplicates('FlightNumber')
    df['SiteGroup']=df.LaunchSite.map(lambda s: 'KSC LC-39A' if '39A' in s else ('VAFB SLC-4E' if 'VAFB' in s else 'Cape Canaveral LC-40'))
    df.to_csv(ROOT/'data/web_scraped_launches.csv',index=False)
    assert len(df)>90 and df.FlightNumber.is_unique
    return df

if __name__=='__main__':
    df=scrape()
    print(df.shape, df.Date.min(), df.Date.max())
    print(df.head().to_string(index=False))
