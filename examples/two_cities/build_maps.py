"""Use inkmap-arcpy 0.3.0 for real city content, then add native city-specific framing."""
import argparse,json,os,sys
from pathlib import Path
import arcpy
import arcpy.cim
from inkmap_arcpy import compose_atlas
from cities import CITIES

ROOT=Path(os.path.abspath(__file__)).parent

def census_locators():
    folder=ROOT/'data/locators'; wgs=arcpy.SpatialReference(4326)
    for kind,output,where in [('states','us_contiguous.geojson',lambda state:state not in {'02','15','60','66','69','72','78'}),
                              ('counties','california_counties.geojson',lambda state:state=='06')]:
        path=folder/output
        if path.exists(): continue
        shp=next((folder/kind).glob('*.shp')); features=[]
        with arcpy.da.SearchCursor(str(shp),['SHAPE@','GEOID','NAME','STATEFP']) as rows:
            for geometry,code,name,state in rows:
                if not where(state): continue
                projected=geometry.projectAs(wgs)
                # ArcPy JSON is Esri rings; convert each multipart exterior and its holes to GeoJSON.
                # Shapefile-to-JSON writes valid GeoJSON and preserves the real boundary topology.
                features.append(dict(code=code,name=name))
        view='census_'+kind
        arcpy.management.MakeFeatureLayer(str(shp),view)
        sql="STATEFP NOT IN ('02','15','60','66','69','72','78')" if kind=='states' else "STATEFP = '06'"
        arcpy.management.SelectLayerByAttribute(view,'NEW_SELECTION',sql)
        arcpy.conversion.FeaturesToJSON(view,str(path),format_json='NOT_FORMATTED',geoJSON='GEOJSON',outputToWGS84='WGS84')
        assert len(json.loads(path.read_text(encoding='utf-8'))['features'])==len(features)
        print(f'Prepared {output}: {len(features)} boundaries',flush=True)

def source_map(city):
    spec=CITIES[city]; out=ROOT/('render-source-'+city)
    if (out/'source.aprx').is_file(): return out/'source.aprx'
    out.mkdir(parents=True,exist_ok=True); gdb=str(out/'source.gdb')
    if not arcpy.Exists(gdb): arcpy.management.CreateFileGDB(str(out),'source.gdb')
    install=Path(arcpy.GetInstallInfo()['InstallDir'])
    p=arcpy.mp.ArcGISProject(str(install/'Resources/ArcToolBox/Services/routingservices/data/Blank.aprx'))
    p.homeFolder=str(out); p.defaultGeodatabase=gdb
    m=p.listMaps()[0]; m.name=city+' OSM'; m.spatialReference=arcpy.SpatialReference(spec['projection'])
    types={'buildings':'POLYGON','green':'POLYGON','parks':'POLYGON','water':'POLYGON',
           'water_lines':'POLYLINE','roads_other':'POLYLINE','roads_main':'POLYLINE',
           'stations':'POINT','neighborhoods':'POINT','landmarks':'POINT'}
    for kind,shape in types.items():
        path=ROOT/'data'/city/'geojson'/(kind+'.geojson')
        expected=len(json.loads(path.read_text(encoding='utf-8'))['features'])
        if not expected: continue
        fc=str(Path(gdb)/kind)
        if not arcpy.Exists(fc): arcpy.conversion.JSONToFeatures(str(path),fc,shape)
        arcpy.management.DefineProjection(fc,arcpy.SpatialReference(4326))
        assert int(arcpy.management.GetCount(fc)[0])==expected,kind
        layer=m.addDataFromPath(fc); layer.name=kind
        print(f'{city}: imported {kind}, {expected}',flush=True)
    p.saveACopy(str(out/'source.aprx'))
    return out/'source.aprx'

def make_job(city,source,output):
    spec=CITIES[city]; p=arcpy.mp.ArcGISProject(str(source)); available={l.name for l in p.listMaps()[0].listLayers()}
    language_font='Garamond' if city=='losangeles' else 'STKaiti'
    descriptors={
       'buildings':'buildings','green':'green',
       'parks':dict(role='green',label_field='label',label_font=language_font,label_size=9),
       'water':'water','water_lines':'roads_other','roads_other':'roads_other',
       'roads_main':dict(role='roads_main',label_field='label',label_font='Garamond' if city=='losangeles' else 'STSong',label_size=6.6),
       'stations':'station',
       'neighborhoods':dict(role='station',label_field='label',label_font=language_font,label_size=10.2,label_color=[143,130,105]),
       'landmarks':dict(role='site',label_field='label',label_font=language_font,label_size=8.6,label_color=[65,84,95])}
    layers={name:desc for name,desc in descriptors.items() if name in available}
    legends=[('roads_main','主要道路'),('water','河湖水面'),('roads_other','支路步行'),('parks','公园花园'),
             ('stations','轨道站点'),('green','其他绿地'),('landmarks','城市地标'),('buildings','建筑轮廓')]
    loc=ROOT/'data/locators'
    if city=='shanghai':
        locators=[dict(geojson=str(loc/'100000_full.json'),caption='全国 · 上海',highlight='310000',projection=102012,grid_degrees=10),
                  dict(geojson=str(loc/'310000_full.json'),caption='上海 · 黄浦',highlight='310101',projection=32651,grid_degrees=.25)]
        source_note='© OpenStreetMap contributors · ODbL | 定位 GeoAtlas 2021'
    else:
        locators=[dict(geojson=str(loc/'us_contiguous.geojson'),caption='美国本土 · 加州',highlight='06',code_field='GEOID',name_field='NAME',projection=5070,grid_degrees=10),
                  dict(geojson=str(loc/'california_counties.geojson'),caption='加州 · 洛杉矶县',highlight='06037',code_field='GEOID',name_field='NAME',projection=3310,grid_degrees=2)]
        source_note='© OpenStreetMap contributors · ODbL | Locator: US Census 2024'
    return dict(project=str(source),map=city+' OSM',output_folder=str(output),center=spec['center'],scale=spec['scale'],
                projection=spec['projection'],title=spec['title'],english_title=spec['english'],subtitle=spec['subtitle'],
                caption=spec['caption'],source_note=source_note,grid_seconds=spec['grid_seconds'],dpi=240,
                layers=layers,legend=[dict(layer=key,label=label) for key,label in legends if key in layers],locators=locators)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('city',choices=CITIES)
    parser.add_argument('--output'); parser.add_argument('--dry-run',action='store_true'); args=parser.parse_args()
    if args.city=='losangeles': census_locators()
    source=source_map(args.city)
    out=Path(os.path.abspath(args.output)) if args.output else ROOT/('render-'+args.city)
    job=make_job(args.city,source,out)
    (ROOT/'data'/args.city/'atlas-job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(compose_atlas(job,args.dry_run),ensure_ascii=False,indent=2))
