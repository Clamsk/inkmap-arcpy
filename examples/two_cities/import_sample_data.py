"""Import a packaged city's real GeoJSON into Pro and write a portable atlas task."""
import argparse,json,os
from pathlib import Path
import arcpy

SPECS={'fuzhou':([119.294,26.086],32650,21000,'榕城 · 鼓楼'),
       'shanghai':([121.490,31.240],32651,21000,'上海 · 外滩'),
       'losangeles':([-118.255,34.073],32611,23000,'洛城 · 回声湖')}
ROLES={'residential':'residential','plazas':'plaza','buildings':'buildings','heritage':'heritage',
       'green':'green','parks':'green','water':'water','water_lines':'water_line','walks':'walk',
       'roads_other':'roads_other','roads_main':'roads_main',
       'stations':'station','communities':'community','neighborhoods':'place_label','landmarks':'site'}
LABELS={'roads_main':'主要道路','water':'河湖水面','roads_other':'支路街巷','walks':'步道小径','parks':'公园花园',
        'stations':'轨道站点','green':'其他绿地','buildings':'建筑轮廓','landmarks':'城市地标',
        'communities':'社区名称点','residential':'居住用地','plazas':'广场铺地','heritage':'历史要素'}

def main(city,data,output):
    data=Path(os.path.abspath(data))/city;out=Path(os.path.abspath(output))
    if out.exists():raise FileExistsError('Choose a new output folder: '+str(out))
    summary=json.loads((data/'summary.json').read_text(encoding='utf-8'))
    out.mkdir(parents=True)
    arcpy.management.CreateFileGDB(str(out),'input.gdb');gdb=out/'input.gdb'
    install=Path(arcpy.GetInstallInfo()['InstallDir'])
    p=arcpy.mp.ArcGISProject(str(install/'Resources/ArcToolBox/Services/routingservices/data/Blank.aprx'))
    p.importDocument(str(install/'Resources/ArcToolBox/Templates/ExportWebMapTemplates/A4 Portrait.pagx'))
    m=p.listMaps()[0];m.name=city
    for layer in m.listLayers():m.removeLayer(layer)
    layers={}
    ordered=list(ROLES)+[k for k in summary['layers'] if k not in ROLES]
    for key in ordered:
        role=ROLES.get(key)
        src=data/'geojson'/(key+'.geojson')
        if not src.is_file() or summary['layers'].get(key,0)==0:continue
        fc=gdb/key
        shape='POLYLINE' if key in {'water_lines','roads_main','roads_other','walks'} else 'POINT' if key in {'stations','communities','neighborhoods','landmarks'} else 'POLYGON'
        arcpy.conversion.JSONToFeatures(str(src),str(fc),shape)
        arcpy.management.DefineProjection(str(fc),arcpy.SpatialReference(4326))
        assert int(arcpy.management.GetCount(str(fc))[0])==summary['layers'][key],key
        added=m.addDataFromPath(str(fc));added.name=key
        fields={f.name for f in arcpy.ListFields(str(fc))}
        if role is None:continue
        bind={'role':role}
        if key in {'parks','roads_main','communities','neighborhoods','landmarks'} and 'label' in fields:
            bind['label_field']='label'
        layers[key]=bind
    center,epsg,scale,title=SPECS[city];m.spatialReference=arcpy.SpatialReference(epsg)
    p.defaultGeodatabase=str(gdb);p.saveACopy(str(out/'input.aprx'))
    job=dict(project='input.aprx',map=city,output_folder='atlas-output',layers=layers,
             center=center,projection=epsg,scale=scale,title=title,grid_seconds=30,
             source_note='© OpenStreetMap contributors · ODbL | 样例数据获取 2026-10-08',
             legend=[dict(layer=k,label=v) for k,v in LABELS.items() if k in layers],locators=[])
    (out/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(city=city,project=str(out/'input.aprx'),layers=len(layers),job=str(out/'job.json')),ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--city',choices=SPECS,required=True)
    ap.add_argument('--data',default=str(Path(os.path.abspath(__file__)).parent/'data'))
    ap.add_argument('--output',required=True);a=ap.parse_args();main(a.city,a.data,a.output)
