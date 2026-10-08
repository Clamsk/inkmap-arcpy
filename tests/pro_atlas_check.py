"""Validate a rendered atlas using licensed ArcGIS Pro Python; no writes to input."""
import json,sys,math
from pathlib import Path
import arcpy
import arcpy.cim

out=Path(sys.argv[1])
report=json.loads((out/'atlas_report.json').read_text(encoding='utf-8'))
p=arcpy.mp.ArcGISProject(str(out/'atlas.aprx'))
assert len(p.listLayouts())==2
assert not [l.name for m in p.listMaps() for l in m.listLayers() if l.isBroken]
for layout in p.listLayouts():
    frame=layout.listElements('MAPFRAME_ELEMENT','Atlas main frame')[0]
    assert abs(frame.camera.scale-report['scale'])<.01
    assert not any('制图中心' in l.name or l.name=='case_center' for l in frame.map.listLayers())
    d=layout.getDefinition('V3')
    fd=next(e for e in d.elements if e.name==frame.name)
    assert fd.grids[0].geographicCoordinateSystem['wkid']==4326
    for grid in fd.grids:
        for gl in grid.gridLines:
            assert not gl.fromTick.isVisible and not gl.toTick.isVisible
    arrow=next(e for e in d.elements if e.name=='North Arrow')
    assert arrow.visible and arrow.mapFrame==frame.name and arrow.northType=='TrueNorth'
    bar=next(e for e in d.elements if e.name=='Scale bar').elements[0]
    assert bar.__class__.__name__=='CIMDoubleFillScaleBar' and bar.mapFrame==frame.name
    assert abs(bar.division*bar.divisions-report['scale_bar_meters'])<.01
    assert bar.unitLabel=='m'
    for i in range(report['locator_count']):
        circle=next(e for e in d.elements if e.name==f'Locator frame {i}')
        caption=next(e for e in d.elements if e.name==f'Locator caption {i}')
        ring=circle.frame['rings'][0]
        cx=(max(pt[0] for pt in ring)+min(pt[0] for pt in ring))/2
        cy=(max(pt[1] for pt in ring)+min(pt[1] for pt in ring))/2
        loc=caption.graphic.shape
        xy=(loc['x'],loc['y']) if isinstance(loc,dict) else (loc.X,loc.Y)
        assert cy-1.55<xy[1]<cy and math.hypot(xy[0]-cx,xy[1]-cy)<1.55
        inset=layout.listElements('MAPFRAME_ELEMENT',f'Locator frame {i}')[0]
        assert int(arcpy.management.GetCount(inset.map.listLayers('Highlighted region')[0])[0])==1
    if layout.name.endswith('frame'):
        assert not layout.listElements('TEXT_ELEMENT','Title')
    else:
        assert layout.listElements('TEXT_ELEMENT','Title')
for name in report['exports']:
    assert (out/name).stat().st_size>10000
assert (out/'atlas_map_only.pgw').is_file()
print(json.dumps({'status':'passed','layouts':2,'locator_captions':'inside lower circle',
                  'checks':['reloaded connections','grid CRS and disabled ticks','true north linkage',
                            'metric scale linkage','no center marker','full and frame exports']},indent=2))
