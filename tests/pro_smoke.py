"""Run in Pro Python: python tests/pro_smoke.py <demo.aprx> <new-output-folder>."""
import hashlib
import json
import os
import sys
from pathlib import Path
import arcpy
from inkmap_arcpy import apply_style
from inkmap_arcpy.geometry import distance_rings
from inkmap_arcpy.workflow import style_project

project, output = (Path(os.path.abspath(value)) for value in sys.argv[1:3])
output.mkdir(parents=True, exist_ok=False)
original = hashlib.sha256(project.read_bytes()).hexdigest()
p = arcpy.mp.ArcGISProject(str(project))
m = p.listMaps("InkMap Demo")[0]
water = m.listLayers("Water")[0]
for palette in ("watercolor", "ink"):
    apply_style(water, "water", palette)
    path = output / (palette + ".lyrx")
    water.saveACopy(str(path))
    document = json.loads(path.read_text(encoding="utf-8"))
    symbol = document["layerDefinitions"][0]["renderer"]["symbol"]["symbol"]
    assert [s["type"] for s in symbol["symbolLayers"]] == [
        "CIMSolidStroke", "CIMGradientStroke", "CIMPictureFill", "CIMSolidFill", "CIMPictureFill"]
    assert symbol["symbolLayers"][2]["url"].startswith("data:image/png;base64,")
    reloaded = arcpy.mp.LayerFile(str(path)).listLayers()[0]
    assert len(reloaded.getDefinition("V3").renderer.symbol.symbol.symbolLayers) == 5

try:
    apply_style(water, "site")
    raise AssertionError("Wrong geometry role accepted")
except ValueError:
    pass
sym = water.symbology
sym.updateRenderer("UniqueValueRenderer")
sym.renderer.fields = ["label"]
water.symbology = sym
try:
    apply_style(water, "water")
    raise AssertionError("Categorized renderer was silently replaced")
except ValueError:
    pass
assert water.symbology.renderer.type == "UniqueValueRenderer"
apply_style(water, "water", replace_renderer=True)
assert water.symbology.renderer.type == "SimpleRenderer"
sr = arcpy.SpatialReference(32651)
point = arcpy.PointGeometry(arcpy.Point(350000,3450000), sr)
for d, ring in distance_rings(point).items():
    assert abs(ring.extent.width / 2 - d) < 0.1
    assert abs(ring.extent.height / 2 - d) < 0.1
try:
    distance_rings(arcpy.PointGeometry(arcpy.Point(121,31), arcpy.SpatialReference(4326)))
    raise AssertionError("Geographic CRS accepted")
except ValueError:
    pass
config = {"project": os.path.abspath(project), "map":"InkMap Demo", "layers":{"Water":"water"},
          "output_project":str(output / "styled.aprx"), "layout":"InkMap A4",
          "export":{"path":str(output / "styled.png"), "dpi":100}}
style_project(config, dry_run=True)
assert not (output / "styled.aprx").exists()
style_project(config)
assert (output / "styled.png").stat().st_size > 10000
assert hashlib.sha256(project.read_bytes()).hexdigest() == original
try:
    style_project(config)
    raise AssertionError("Existing output was overwritten")
except ValueError:
    pass
print(json.dumps({"status":"passed", "checks":["CIM layer order", "embedded texture", "lyrx reload",
      "geometry-role rejection", "metric rings", "geographic rejection", "dry-run", "PNG export",
      "categorized renderer protection", "explicit renderer replacement", "source unchanged", "overwrite rejection"]}, indent=2))
