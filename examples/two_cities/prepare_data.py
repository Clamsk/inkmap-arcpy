"""Normalize city OSM geometry without inventing administrative or neighborhood boundaries."""
import argparse,collections,json,os,re
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import LineString,Point,Polygon,box,mapping
from shapely.ops import polygonize,unary_union,transform
from cities import CITIES

ROOT=Path(os.path.abspath(__file__)).parent

def prepare(city):
    spec=CITIES[city]; data=ROOT/'data'/city
    raw=json.loads((data/'osm_raw.json').read_text(encoding='utf-8'))
    south,west,north,east=spec['bbox']; clip=box(west,south,east,north)
    project=Transformer.from_crs(4326,spec['projection'],always_xy=True).transform
    warnings=[]
    def title(tags):
        return (tags.get('name:en') or tags.get('name') or '') if spec['language']=='en' else (
                tags.get('name:zh-Hans') or tags.get('name:zh') or tags.get('name') or '')
    def category(tags):
        if tags.get('natural')=='water' or tags.get('waterway')=='riverbank': return 'water'
        if tags.get('leisure') in {'park','garden','nature_reserve'}: return 'parks'
        if tags.get('leisure')=='pitch' or tags.get('landuse') in {'forest','grass','meadow','recreation_ground','village_green','orchard'} or tags.get('natural') in {'wood','scrub','grassland'}: return 'green'
        if tags.get('building'): return 'buildings'
    def coords(items): return [(v['lon'],v['lat']) for v in items if v and 'lon' in v]
    def area(e):
        if e['type']=='way':
            points=coords(e.get('geometry',[]))
            if len(points)<4 or points[0]!=points[-1]: return None
            geometry=Polygon(points)
        elif e['type']=='relation':
            outers,inners=[],[]
            for member in e.get('members',[]):
                points=coords(member.get('geometry',[]))
                if member.get('type')!='way' or len(points)<2: continue
                (inners if member.get('role')=='inner' else outers).append(LineString(points))
            if not outers: return None
            polygons=list(polygonize(unary_union(outers)))
            if not polygons:
                warnings.append(dict(osm_id=e['id'],issue='Unclosed relation outer rings')); return None
            geometry=unary_union(polygons)
            if inners: geometry=geometry.difference(unary_union(list(polygonize(unary_union(inners)))))
        else: return None
        if not geometry.is_valid: geometry=geometry.buffer(0)
        geometry=geometry.intersection(clip)
        return geometry if not geometry.is_empty and geometry.geom_type in {'Polygon','MultiPolygon'} else None
    def feature(e,geometry,kind,label=''):
        tags=e.get('tags',{})
        return dict(type='Feature',geometry=mapping(geometry),properties=dict(osm_id=str(e['id']),osm_type=e['type'],
                       name=title(tags),label=label,category=kind,area_m2=round(transform(project,geometry).area,2)))
    layers={key:[] for key in ('buildings','green','parks','water','water_lines','roads_other','roads_main','stations','neighborhoods','landmarks')}
    members=collections.defaultdict(set); cached={}
    for e in raw['elements']:
        if e['type']=='relation' and category(e.get('tags',{})):
            geometry=area(e); cached[e['id']]=geometry
            if geometry is not None:
                members[category(e['tags'])].update(m['ref'] for m in e.get('members',[]) if m['type']=='way')
    label_seen=set(); poi_seen=set(); station_seen=set()
    important={'shanghai':('东方明珠','人民广场','外白渡桥','上海中心大厦','上海环球金融中心','外滩源'),
               'losangeles':('Dodger Stadium','Union Station','Walt Disney Concert Hall','Los Angeles City Hall','The Broad')}
    for e in raw['elements']:
        tags=e.get('tags',{}); kind=category(tags); name=title(tags)
        geometry=cached.get(e['id']) if e['type']=='relation' else None
        if kind and not (e['type']=='way' and e['id'] in members[kind]):
            geometry=geometry if geometry is not None else area(e)
            if geometry is not None:
                label=name if kind=='parks' and transform(project,geometry).area>=15000 and name not in label_seen else ''
                if label: label_seen.add(label)
                layers[kind].append(feature(e,geometry,kind,label))
        if e['type']=='way' and tags.get('highway') and tags.get('area')!='yes':
            points=coords(e.get('geometry',[]))
            if len(points)>1:
                road=LineString(points).intersection(clip)
                if not road.is_empty and road.geom_type in {'LineString','MultiLineString'}:
                    kind='roads_main' if tags['highway'] in {'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link'} else 'roads_other'
                    label=name if kind=='roads_main' and tags['highway'] not in {'motorway','motorway_link'} else ''
                    if city=='losangeles':
                        for word,short in [('North','N'),('South','S'),('East','E'),('West','W'),('Street','St'),('Avenue','Ave'),('Boulevard','Blvd')]:
                            label=re.sub(r'\b'+word+r'\b',short,label)
                    layers[kind].append(feature(e,road,kind,label))
        if e['type']=='way' and tags.get('waterway') in {'river','canal','stream'}:
            points=coords(e.get('geometry',[]))
            if len(points)>1:
                water=LineString(points).intersection(clip)
                if not water.is_empty and water.geom_type in {'LineString','MultiLineString'}:
                    layers['water_lines'].append(feature(e,water,'water_lines'))
        is_neighborhood=e['type']=='node' and tags.get('place') in {'suburb','quarter'}
        # One station symbol per name; entrance nodes are not independent station records.
        is_station=tags.get('railway')=='station'
        is_landmark=(name in {'外滩源','上海中心大厦','上海环球金融中心','外白渡桥','东方明珠电视塔','东方明珠塔','人民广场'}) if city=='shanghai' else name in important[city]
        if is_neighborhood or is_station or is_landmark:
            point=Point(e['lon'],e['lat']) if e['type']=='node' else (
                    geometry.representative_point() if geometry is not None else None)
            if point is None and e['type']=='way':
                points=coords(e.get('geometry',[]))
                if len(points)>1: point=LineString(points).interpolate(.5,normalized=True)
            if point is None or not clip.covers(point): continue
            if is_neighborhood and name:
                layers['neighborhoods'].append(feature(e,point,'neighborhoods',name))
            if is_station and name and name not in station_seen:
                station_seen.add(name); layers['stations'].append(feature(e,point,'stations'))
            if is_landmark and name not in poi_seen:
                poi_seen.add(name); layers['landmarks'].append(feature(e,point,'landmarks',name))
    out=data/'geojson'; out.mkdir(exist_ok=True)
    for kind,features in layers.items():
        (out/(kind+'.geojson')).write_text(json.dumps(dict(type='FeatureCollection',features=features),ensure_ascii=False),encoding='utf-8')
    summary=dict(city=city,layers={k:len(v) for k,v in layers.items()},warnings=warnings,
                 named_parks=[f['properties']['label'] for f in layers['parks'] if f['properties']['label']],
                 landmarks=[f['properties']['label'] for f in layers['landmarks']],
                 neighborhood_semantics='OSM names at point locations; no administrative or neighborhood boundaries inferred')
    (data/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('city',choices=CITIES); args=parser.parse_args(); prepare(args.city)
