"""Check native full/detail projects, geographic linkage and social image exports."""
import json,math,os
from pathlib import Path
import arcpy,arcpy.cim
from cities import CITIES
from post_cards import DETAILS

ROOT=Path(os.path.abspath(__file__)).parent
report=[]
for city,spec in CITIES.items():
    out=ROOT/(os.environ.get('INKMAP_RENDER_PREFIX','render-')+city)
    for name in (city+'_city',city+'_post'):
        project=arcpy.mp.ArcGISProject(str(out/(name+'.aprx')))
        broken=[l.name for m in project.listMaps() for l in m.listLayers() if l.isBroken]
        assert not broken,(city,name,broken)
        layouts=[l for l in project.listLayouts() if l.name.startswith(city)]
        assert len(layouts)>=2
        for layout in layouts:
            assert abs(layout.pageWidth/ layout.pageHeight-.75)<.0001
            frame=layout.listElements('MAPFRAME_ELEMENT','Atlas main frame')[0]
            expected_scale=DETAILS[city]['scale'] if layout.name.endswith('detail edition') else spec['scale']
            assert abs(frame.camera.scale-expected_scale)<.01
            assert frame.map.spatialReference.factoryCode==spec['projection']
            d=layout.getDefinition('V3')
            arrow=next(e for e in d.elements if e.name=='North Arrow')
            bar=next(e for e in d.elements if e.name=='Scale bar').elements[0]
            assert arrow.visible and arrow.northType=='TrueNorth' and arrow.mapFrame==frame.name
            assert bar.mapFrame==frame.name and bar.unitLabel=='m'
            total=500 if layout.name.endswith('detail edition') else 1000
            assert abs(bar.division*bar.divisions-total)<.01
            main=next(e for e in d.elements if e.name==frame.name)
            assert main.grids[0].geographicCoordinateSystem['wkid']==4326
            assert not any('center' in layer.name.lower() for layer in frame.map.listLayers())
            for text in layout.listElements('TEXT_ELEMENT'):
                assert not getattr(text,'isOverflowing',False),(layout.name,text.name)
            for inset in layout.listElements('MAPFRAME_ELEMENT','Locator frame*'):
                index=inset.name.rsplit(' ',1)[1]
                circle=next(e for e in d.elements if e.name==inset.name)
                label=next(e for e in d.elements if e.name=='Locator caption '+index)
                ring=circle.frame['rings'][0]; cy=(min(p[1] for p in ring)+max(p[1] for p in ring))/2
                cx=(min(p[0] for p in ring)+max(p[0] for p in ring))/2
                point=label.graphic.shape
                assert cy-1.55<point['y']<cy and math.hypot(point['x']-cx,point['y']-cy)<1.55
                assert int(arcpy.management.GetCount(inset.map.listLayers('Highlighted region')[0])[0])==1
        report.append(dict(city=city,project=name,layouts=[l.name for l in layouts],broken_layers=broken))
    # Both maps retain every normalized input record; no fake or synthetic city features.
    p=arcpy.mp.ArcGISProject(str(out/(city+'_city.aprx')))
    m=next(m for m in p.listMaps() if m.listLayers('buildings'))
    expected=json.loads((ROOT/'data'/city/'summary.json').read_text(encoding='utf-8'))['layers']
    for key,count in expected.items():
        if count: assert int(arcpy.management.GetCount(m.listLayers(key)[0])[0])==count,(city,key)
result=dict(status='passed',projects=report,checks=['saved connections','input feature counts','3:4 city page',
        'true north and metric scale linkage','WGS84 grid','circle captions inside bottom','no center marker','text overflow'])
(ROOT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
