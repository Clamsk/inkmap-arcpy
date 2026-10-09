"""Fetch bounded OSM extracts and published locator boundaries; preserve provenance."""
import argparse,hashlib,json,os,zipfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from cities import CITIES

ROOT=Path(os.path.abspath(__file__)).parent
ENDPOINTS=['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']

def fetch(url,path,data=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): return path.read_bytes()
    req=Request(url,data=data,headers={'User-Agent':'InkMap real-data watercolor cartography example',
                  'Content-Type':'application/x-www-form-urlencoded'} if data else
                  {'User-Agent':'InkMap real-data watercolor cartography example'})
    with urlopen(req,timeout=230 if data else 90) as response: raw=response.read()
    path.write_bytes(raw)
    return raw

def download_osm(city):
    spec=CITIES[city]; out=ROOT/'data'/city
    box=','.join(map(str,spec['bbox']))
    query=f'''[out:json][timeout:180][maxsize:134217728];
(
 way["highway"]({box});
 nwr["natural"="water"]({box}); nwr["waterway"="riverbank"]({box});
 way["waterway"~"^(river|canal|stream)$"]({box});
 nwr["leisure"~"^(park|garden|nature_reserve|pitch)$"]({box});
 nwr["landuse"~"^(forest|grass|meadow|recreation_ground|village_green|orchard)$"]({box});
 nwr["natural"~"^(wood|scrub|grassland)$"]({box});
 way["building"]({box}); relation["building"]({box});
 nwr["place"~"^(suburb|quarter|neighbourhood)$"]({box});
 nwr["railway"="station"]({box}); nwr["railway"="subway_entrance"]({box});
 nwr["tourism"~"^(attraction|museum)$"]({box}); nwr["historic"]({box});
);
out body geom;'''
    out.mkdir(parents=True,exist_ok=True)
    (out/'query.overpassql').write_text(query,encoding='utf-8')
    target=out/'osm_raw.json'
    if target.exists():
        print(f'{city}: using cached extract',flush=True); return
    for endpoint in ENDPOINTS:
        try:
            raw=fetch(endpoint,target,urlencode({'data':query}).encode())
            document=json.loads(raw)
            if document.get('remark') or not document.get('elements'):
                target.unlink()
                raise RuntimeError('Incomplete Overpass result: '+document.get('remark','no elements'))
            meta=dict(source='OpenStreetMap',copyright='https://www.openstreetmap.org/copyright',license='ODbL 1.0',
                       endpoint=endpoint,bbox_wgs84=spec['bbox'],retrieved=datetime.now(timezone.utc).isoformat(),
                       osm_timestamp=document.get('osm3s',{}).get('timestamp_osm_base'),
                       elements=len(document['elements']),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            (out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(dict(city=city,**meta),ensure_ascii=False),flush=True); return
        except Exception as error:
            print(f'{city}: {endpoint}: {type(error).__name__}: {error}',flush=True)
    raise RuntimeError('No complete OSM extract downloaded')

def download_locators():
    out=ROOT/'data/locators'; records=[]
    for code in ('100000','310000'):
        url=f'https://geo.datav.aliyun.com/areas_v3/bound/{code}_full.json'
        raw=fetch(url,out/f'{code}_full.json')
        document=json.loads(raw)
        assert document['type']=='FeatureCollection'
        records.append(dict(url=url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),features=len(document['features'])))
    for kind,filename in [('states','cb_2024_us_state_20m.zip'),('counties','cb_2024_us_county_5m.zip')]:
        url='https://www2.census.gov/geo/tiger/GENZ2024/shp/'+filename
        path=out/filename; raw=fetch(url,path)
        folder=out/kind; folder.mkdir(exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                # No archive member may escape the explicitly named output directory.
                if Path(name).name!=name: raise ValueError('Unexpected nested archive member')
                archive.extract(name,folder)
        records.append(dict(url=url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    metadata=dict(retrieved=datetime.now(timezone.utc).isoformat(),records=records,
         china_source='DataV GeoAtlas / Amap areas_v3, publisher 2021-05, learning/exchange',
         us_source='US Census Bureau 2024 Cartographic Boundary Files; generalized locator geography',
         mainland_note='US national circle depicts contiguous 48 states plus DC, labeled 美国本土; Alaska, Hawaii and territories excluded from this viewport')
    (out/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(metadata,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('target',choices=list(CITIES)+['locators'])
    args=parser.parse_args()
    download_locators() if args.target=='locators' else download_osm(args.target)
