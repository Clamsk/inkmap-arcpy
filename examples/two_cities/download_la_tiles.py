"""Small bounded Overpass tiles, deduplicated by OSM type and id; reject partial responses."""
import hashlib,json
from datetime import datetime,timezone
from urllib.parse import urlencode
from download_data import ROOT,fetch
from cities import CITIES

spec=CITIES['losangeles']; folder=ROOT/'data/losangeles'; folder.mkdir(parents=True,exist_ok=True)
south,west,north,east=spec['bbox']; midlat=(south+north)/2; midlon=(west+east)/2
tiles=[(south,west,midlat,midlon),(south,midlon,midlat,east),(midlat,west,north,midlon),(midlat,midlon,north,east)]
elements={}; records=[]
for i,bbox in enumerate(tiles):
    box=','.join(map(str,bbox))
    query=f'''[out:json][timeout:90][maxsize:100663296];
    (way["highway"]({box});
     nwr["natural"="water"]({box}); nwr["waterway"="riverbank"]({box});
     way["waterway"~"^(river|canal|stream)$"]({box});
     nwr["leisure"~"^(park|garden|nature_reserve|pitch)$"]({box});
     nwr["landuse"~"^(forest|grass|meadow|recreation_ground|village_green|orchard)$"]({box});
     nwr["natural"~"^(wood|scrub|grassland)$"]({box});
     way["building"]({box}); relation["building"]({box});
     node["place"~"^(suburb|quarter|neighbourhood)$"]({box});
     nwr["railway"="station"]({box}););
     out body geom;'''
    path=folder/f'tile_{i}.json'; queryfile=folder/f'tile_{i}.overpassql'
    queryfile.write_text(query,encoding='utf-8')
    for endpoint in ['https://overpass.private.coffee/api/interpreter','https://overpass-api.de/api/interpreter']:
        try:
            raw=fetch(endpoint,path,urlencode({'data':query}).encode()); document=json.loads(raw)
            if document.get('remark') or not document.get('elements'):
                path.unlink(); raise ValueError(document.get('remark','Empty extract'))
            records.append(dict(tile=i,bbox=bbox,endpoint=endpoint,timestamp=document.get('osm3s',{}).get('timestamp_osm_base'),
                                sha256=hashlib.sha256(raw).hexdigest(),elements=len(document['elements'])))
            for e in document['elements']: elements[e['type'],e['id']]=e
            print(f'Los Angeles tile {i}: {len(document["elements"])} elements',flush=True); break
        except Exception as exc:
            print(f'Tile {i}: {endpoint}: {type(exc).__name__}: {exc}',flush=True)
    else: raise RuntimeError(f'No complete response for tile {i}')
document=dict(version=.6,generator='InkMap merged complete bounded Overpass tiles',elements=list(elements.values()))
payload=json.dumps(document).encode('utf-8')
(folder/'osm_raw.json').write_bytes(payload)
metadata=dict(source='OpenStreetMap',copyright='https://www.openstreetmap.org/copyright',license='ODbL 1.0',
              bbox_wgs84=spec['bbox'],retrieved=datetime.now(timezone.utc).isoformat(),tile_records=records,
              elements=len(elements),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
(folder/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(json.dumps(metadata,indent=2),flush=True)
