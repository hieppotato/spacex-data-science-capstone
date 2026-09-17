"""Folium site locations, individual records and measured pad-to-pad proximity."""
from pathlib import Path
import json
from math import radians, sin, cos, sqrt, atan2
import pandas as pd
import folium
from folium.plugins import MarkerCluster, MousePosition

ROOT=Path(__file__).resolve().parent

def km(a,b):
    lat1,lon1,lat2,lon2=map(radians,[*a,*b])
    h=sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 6371.0088*2*atan2(sqrt(h),sqrt(1-h))

def build_map():
    d=pd.read_csv(ROOT/'data/spacex_launch_geo.csv')
    sites=d.groupby('Launch Site')[['Lat','Long']].first()
    m=folium.Map(location=[34,-98],zoom_start=4,tiles='OpenStreetMap')
    marker_layer=folium.FeatureGroup(name='Launch site markers',show=True).add_to(m)
    for name,r in sites.iterrows():
        count=int((d['Launch Site']==name).sum())
        folium.Marker([r.Lat,r.Long],tooltip=name,popup=f'{name}: {count} launch records',icon=folium.Icon(color='blue',icon='info-sign')).add_to(marker_layer)
    records=folium.FeatureGroup(name='Launch outcomes (green=class 1, red=class 0)',show=False).add_to(m)
    cluster=MarkerCluster().add_to(records)
    for _,r in d.iterrows():
        folium.Marker([r.Lat,r.Long],tooltip=f"Flight {r['Flight Number']} - {r.Date}",
                      popup=f"{r['Launch Site']}<br>{r['Landing Outcome']}<br>{r['Payload Mass (kg)']} kg",
                      icon=folium.Icon(color='green' if r['class']==1 else 'red',icon='info-sign')).add_to(cluster)
    folium.LayerControl(collapsed=False).add_to(m)
    MousePosition().add_to(m)
    m.save(ROOT/'results/launch_sites.html')
    rmap=folium.Map(location=[28.57,-80.58],zoom_start=11,tiles='OpenStreetMap')
    for _,r in d[d['Launch Site'].str.startswith(('CC','KSC'))].iterrows():
        # Deterministic visual offset separates records at the same pad. Popups
        # expose actual coordinates, not the display offsets.
        n=int(r['Flight Number']); lat=r.Lat+(n%7-3)*.001;lon=r.Long+(n//7%7-3)*.001
        folium.CircleMarker([lat,lon],radius=5,color='#087f8c' if r['class']==1 else '#c84b40',fill=True,fill_opacity=.85,
                            popup=f"Flight {n}, {r.Date}<br>{r['Landing Outcome']}<br>Actual location: {r.Lat}, {r.Long}").add_to(rmap)
    folium.Marker([28.60,-80.63],icon=folium.DivIcon(html='<div style="width:330px;background:white;padding:8px">Launch records: green=success, red=other.<br>Dots offset for visibility; coordinates in popups.</div>')).add_to(rmap)
    rmap.save(ROOT/'results/launch_records.html')
    a=sites.loc['CCAFS LC-40'].tolist();b=sites.loc['KSC LC-39A'].tolist()
    distance=km(a,b)
    close=folium.Map(location=[28.585,-80.59],zoom_start=12,tiles='OpenStreetMap')
    for name,point in [('CCAFS LC-40',a),('KSC LC-39A',b)]:
        folium.Marker(point,tooltip=name,popup=name).add_to(close)
    folium.PolyLine([a,b],color='#087f8c',weight=4,tooltip=f'{distance:.2f} km geodesic approximation').add_to(close)
    folium.Marker([(a[0]+b[0])/2,(a[1]+b[1])/2],icon=folium.DivIcon(html=f'<div style="background:white;width:180px;padding:8px">Pad-to-pad: {distance:.2f} km<br>Haversine distance</div>')).add_to(close)
    MousePosition().add_to(close)
    close.save(ROOT/'results/proximity.html')
    result={'sites':sites.reset_index().to_dict('records'),'cape_to_ksc_km':distance,'geo_records':len(d)}
    (ROOT/'results/geo_summary.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    print(build_map())
