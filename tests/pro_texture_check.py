"""Verify saved atlas symbols contain the two approved materials in native layer order."""
import base64,hashlib,json,os,sys
from pathlib import Path
import arcpy
from inkmap_arcpy.symbols import image_url

assets=Path(os.path.abspath(__file__)).parents[1]/'src/inkmap_arcpy/assets'
ink=image_url(assets/'generated-wet-ink.png');paper=image_url(assets/'generated-white-paper.png')
result=[]
for name in sys.argv[1:]:
    out=Path(name);p=arcpy.mp.ArcGISProject(str(out/'atlas.aprx'))
    m=p.listLayouts('Watercolor atlas · full')[0].listElements('MAPFRAME_ELEMENT','Atlas main frame')[0].map
    checked=[]
    for layer in m.listLayers():
        if not layer.isFeatureLayer:continue
        d=layer.getDefinition('V3')
        if d.renderer.__class__.__name__!='CIMSimpleRenderer':continue
        sym=d.renderer.symbol.symbol
        if sym.__class__.__name__!='CIMPolygonSymbol':continue
        parts=sym.symbolLayers
        if len(parts)==5:
            assert [s.__class__.__name__ for s in parts]==['CIMSolidStroke','CIMGradientStroke','CIMPictureFill','CIMSolidFill','CIMPictureFill'],layer.name
            assert parts[2].url==ink and parts[4].url==paper,layer.name
            assert parts[2].url!=parts[4].url
            checked.append(layer.name)
    assert len(checked)>=3,checked
    assert not p.listBrokenDataSources()
    result.append(dict(folder=str(out),two_independent_images='passed',layers=checked,broken=[]))
print(json.dumps(result,ensure_ascii=False,indent=2))
