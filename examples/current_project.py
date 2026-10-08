"""Run inside the ArcGIS Pro Python window or Notebook after installing inkmap-arcpy."""
import arcpy
from inkmap_arcpy import apply_style

project = arcpy.mp.ArcGISProject("CURRENT")
maps = [m for m in project.listMaps() if m.name == "Map"]
if len(maps) != 1:
    raise ValueError("Set an exact, unambiguous map name")
roles = {"Water": "water", "Green Space": "green", "Main Roads": "roads_main"}
for name, role in roles.items():
    layers = [l for l in maps[0].listLayers() if l.longName == name]
    if len(layers) != 1:
        raise ValueError(f"Set an exact, unambiguous layer longName: {name}")
    apply_style(layers[0], role)
# CURRENT changes are visible in the open project. Save a new copy to keep the original file.
project.saveACopy(r"C:\GIS\output\watercolor.aprx")
