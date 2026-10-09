"""Check actual saved 0.4.0 symbols, including the faint-walk / readable-station balance."""
import json,sys
from pathlib import Path
import arcpy,arcpy.cim

results=[]
for directory in sys.argv[1:]:
    out=Path(directory)
    report=json.loads((out/'atlas_report.json').read_text('utf-8'))
    assert report['version']=='0.4.0'
    p=arcpy.mp.ArcGISProject(str(out/'atlas.aprx'))
    m=p.listLayouts('Watercolor atlas · full')[0].listElements('MAPFRAME_ELEMENT','Atlas main frame')[0].map
    for name,role in report['bindings'].items():
        layer=m.listLayers(name)[0]
        assert int(arcpy.management.GetCount(layer)[0])==report['feature_counts'][name],name
        parts=layer.getDefinition('V3').renderer.symbol.symbol.symbolLayers
        if role=='station':
            assert parts[0].size==4.0
            ring=parts[0].markerGraphics[0].symbol.symbolLayers
            assert ring[0].width==.40 and ring[0].color.values==[88,115,119,88]
            assert ring[1].color.values==[249,247,239,100]
        elif role=='walk':
            assert len(parts)==1 and parts[0].width==.22 and parts[0].color.values[-1]==25
            assert not parts[0].effects
        elif role=='roads_other':
            assert len(parts)==1 and parts[0].width==.44 and not parts[0].effects
        elif role=='roads_main':
            assert [s.width for s in parts]==[1.08,1.85]
            assert all(s.capStyle==s.joinStyle=='Round' for s in parts)
        elif role=='buildings':assert parts[1].color.values[-1]==23
        elif role=='residential':assert len(parts)==1 and parts[0].color.values[-1]==5
        elif role=='place_label':assert parts[0].markerGraphics[0].symbol.symbolLayers[0].color.values[-1]==0
    for layout in p.listLayouts():
        d=layout.getDefinition('V3')
        legend=next(e for e in d.elements if e.name=='Legend paper')
        assert legend.graphic.symbol.symbol.symbolLayers[-1].color.values[-1]==62
    assert not p.listBrokenDataSources()
    results.append({'city':out.parent.name,'status':'passed','roles':report['bindings'],'feature_counts':report['feature_counts']})
print(json.dumps(results,ensure_ascii=False,indent=2))
