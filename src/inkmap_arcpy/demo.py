"""Offline demonstration: all geography is synthetic, with no downloaded basemap."""
import math
import os
import random
from pathlib import Path
from .symbols import arcpy_module, apply_style, cim, fill
from .geometry import distance_rings
from .palettes import get_palette


def create_demo(output, palette="watercolor"):
    a = arcpy_module()
    out = Path(os.path.abspath(output))
    if out.exists():
        raise ValueError(f"Demo output must be a new directory: {out}")
    install = Path(a.GetInstallInfo()["InstallDir"])
    blank = install / "Resources/ArcToolBox/Services/routingservices/data/Blank.aprx"
    template = install / "Resources/ArcToolBox/Templates/ExportWebMapTemplates/A4 Portrait.pagx"
    if not blank.is_file() or not template.is_file():
        raise RuntimeError("Bundled Pro demo templates were not found; style an existing APRX with the JSON workflow")
    out.mkdir(parents=True)
    gdb = str(out / "demo.gdb")
    a.management.CreateFileGDB(str(out), "demo.gdb")
    p = a.mp.ArcGISProject(str(blank))
    m = p.listMaps()[0]
    m.name = "InkMap Demo"
    sr = a.SpatialReference(32651)
    colors = get_palette(palette)
    m.spatialReference = sr
    for layer in m.listLayers():
        m.removeLayer(layer)
    x0, y0, w, h = 350000, 3450000, 4000, 5400

    def polygon(coords):
        return a.Polygon(a.Array([a.Point(x0+x, y0+y) for x,y in coords]), sr)

    def rect(x,y,dx,dy):
        return polygon([(x,y),(x+dx,y),(x+dx,y+dy),(x,y+dy),(x,y)])

    def line(coords):
        return a.Polyline(a.Array([a.Point(x0+x, y0+y) for x,y in coords]), sr)

    def point(x,y):
        return a.PointGeometry(a.Point(x0+x,y0+y),sr)

    def feature(name, shape, geometries, role, labels=None):
        path = str(Path(gdb) / name)
        a.management.CreateFeatureclass(gdb, name, shape, spatial_reference=sr)
        a.management.AddField(path, "label", "TEXT", field_length=64)
        with a.da.InsertCursor(path, ["SHAPE@", "label"]) as cursor:
            for i, geom in enumerate(geometries):
                cursor.insertRow([geom, labels[i] if labels else ""])
        layer = m.addDataFromPath(path)
        layer.name = name.replace("_", " ")
        apply_style(layer, role, palette)
        layer.saveACopy(str(out / (name + ".lyrx")))
        if labels:
            cls = layer.listLabelClasses()[0]
            cls.expression = "$feature.label"
            cls.visible = True
            layer.showLabels = True
            label_style(layer)
        return layer

    def label_style(layer):
        definition = layer.getDefinition("V3")
        for cls in definition.labelClasses:
            text = cls.textSymbol.symbol
            text.fontFamilyName = "Arial"
            text.fontStyleName = "Bold"
            text.height = 10
            text.symbol = cim("CIMPolygonSymbol", symbolLayers=[fill(colors.accent)])
            text.haloSymbol = cim("CIMPolygonSymbol", symbolLayers=[fill((255,255,255))])
            text.haloSize = 1.1
        layer.setDefinition(definition)

    extent = rect(0,0,w,h)
    feature("Paper", "POLYGON", [extent], "paper")
    river_axis = line([(1850+630*math.sin(y/950),y) for y in range(-500,6001,60)])
    river = river_axis.buffer(310).intersect(extent,4)
    feature("Water", "POLYGON", [river], "water")
    rng = random.Random(20261008)
    buildings, greens = [], []
    for ix in range(22):
        for iy in range(29):
            x,y = 65+ix*178, 65+iy*183
            block = rect(x,y,105,112)
            if not block.disjoint(river):
                continue
            if rng.random() < 0.08:
                greens.append(block)
            else:
                for k in range(3):
                    buildings.append(rect(x+k*34,y,25,45+rng.random()*48))
                buildings.append(rect(x,y+96,103,15))
    feature("Buildings", "POLYGON", buildings, "buildings")
    feature("Green_Space", "POLYGON", greens, "green")
    minor, major = [], []
    for ix in range(23):
        road = line([(35+ix*178,0),(35+ix*178,h)]).difference(river)
        (major if ix % 6 == 0 else minor).append(road)
    for iy in range(30):
        road = line([(0,35+iy*183),(w,35+iy*183)]).difference(river)
        (major if iy % 7 == 0 else minor).append(road)
    major += [line([(0,y),(w,y)]) for y in (1320,3450,4550)]
    feature("Other_Roads", "POLYLINE", minor, "roads_other")
    feature("Main_Roads", "POLYLINE", major, "roads_main")
    site = point(2420,2700)
    rings = distance_rings(site)
    feature("Distance_Rings", "POLYLINE", list(rings.values()), "buffer")
    feature("Subway_Stations", "POINT", [point(x,y) for x,y in [(600,850),(850,2000),(1200,3500),(3000,1200),(3400,4150)]], "station")
    feature("Site", "POINT", [site], "site", ["Site"])
    # Labels anchored on the north arc, independent of automatic line-label repetition.
    label_path = str(Path(gdb) / "Distance_Labels")
    a.management.CreateFeatureclass(gdb, "Distance_Labels", "POINT", spatial_reference=sr)
    a.management.AddField(label_path, "label", "TEXT", field_length=64)
    with a.da.InsertCursor(label_path, ["SHAPE@", "label"]) as cursor:
        for d in rings:
            cursor.insertRow([point(2420,2700+d), f"{d} m"])
    labels = m.addDataFromPath(label_path)
    labels.name = "Distance labels"
    sym = labels.symbology
    sym.renderer.symbol.color = {"RGB": [255,255,255,0]}
    sym.renderer.symbol.outlineColor = {"RGB": [255,255,255,0]}
    labels.symbology = sym
    labels.listLabelClasses()[0].expression = "$feature.label"
    labels.showLabels = True
    label_style(labels)
    p.importDocument(str(template))
    l = p.listLayouts()[0]
    l.name = "InkMap A4"
    mf = l.listElements("MAPFRAME_ELEMENT")[0]
    mf.map = m
    mf.elementPositionX = 1.0
    mf.elementPositionY = 3.0
    mf.elementWidth = 19.0
    mf.elementHeight = 24.5
    mf.camera.setExtent(a.Extent(x0,y0,x0+w,y0+h,spatial_reference=sr))
    mf.camera.scale *= 1.02
    # Keep the native frame, compass and scale-bar group; give the legend room below the map.
    c = l.getDefinition("V3")
    keep = {mf.name, "Title", "Legend", "North Arrow", "Scale bar", "Credits"}
    c.elements = [e for e in c.elements if e.name in keep]
    for e in c.elements:
        if e.name in {"Title", "Credits"}:
            e.anchor = "TopLeftCorner"
            e.graphic.symbol.symbol.horizontalAlignment = "Left"
        if e.name == "North Arrow":
            e.visible = True
        if e.name == "Scale bar":
            e.elements = [child for child in e.elements if child.name == "Scale Line 1"]
            for child in e.elements:
                child.units = {"uwkid": 9001}
                child.unitLabel = "m"
    l.setDefinition(c)
    title = l.listElements("TEXT_ELEMENT", "Title")[0]
    title.text = "水彩区位图示例" if palette == "watercolor" else "灰墨区位图示例"
    title.elementPositionX = 1.0
    title.elementPositionY = 28.2
    title.textSize = 18
    credit = l.listElements("TEXT_ELEMENT", "Credits")[0]
    credit.text = "InkMap ArcPy | 合成演示数据 · 非真实地理底图 | WGS 84 / UTM 51N"
    credit.elementPositionX = 1.0
    credit.elementPositionY = 0.55
    credit.textSize = 6.5
    legend = l.listElements("LEGEND_ELEMENT")[0]
    legend.title = "图例"
    legend.elementPositionX = 1.0
    legend.elementPositionY = 2.6
    legend.elementWidth = 19.0
    legend.elementHeight = 1.8
    c = l.getDefinition("V3")
    lc = next(e for e in c.elements if e.name == legend.name)
    lc.autoAdd = False
    lc.columns = 4
    lc.makeColumnsSameWidth = True
    lc.horizontalItemGap = 10
    lc.fittingStrategy = "AdjustFontSize"
    lc.excludedLayers = [layer.getDefinition("V3").uRI for layer in m.listLayers()
                         if layer.name in {"Paper", "Distance labels"}]
    lc.items = [item for item in lc.items if item.name not in {"Paper", "Distance labels"}]
    for item in lc.items:
        item.showLayerName = True
        item.showHeading = False
        item.showLabels = False
    l.setDefinition(c)
    north = l.listElements("MAPSURROUND_ELEMENT", "North Arrow")[0]
    north.elementPositionX = 1.7
    north.elementPositionY = 25.4
    north.elementWidth = 0.9
    north.elementHeight = 1.5
    scale = l.listElements("MAPSURROUND_ELEMENT", "Scale Line 1")[0]
    scale.elementPositionX = 14.0
    scale.elementPositionY = 3.8
    scale.elementWidth = 5.0
    # Move the existing native scale-bar group without reconstructing its linked surrounds.
    c = l.getDefinition("V3")
    for e in c.elements:
        if e.name == "Scale bar":
            for child in e.elements:
                if hasattr(child, "mapFrame"):
                    child.mapFrame = mf.name
                    child.division = 500
                    child.divisions = 2
                    child.subdivisions = 2
                    child.fittingStrategy = "AdjustFrame"
    l.setDefinition(c)
    p.saveACopy(str(out / "demo.aprx"))
    l.exportToPNG(str(out / "demo.png"), resolution=160)
    l.exportToPDF(str(out / "demo.pdf"), resolution=300, image_quality="BEST")
    return {"project": str(out / "demo.aprx"), "preview": str(out / "demo.png"),
            "pdf": str(out / "demo.pdf"), "palette": palette, "data": "synthetic"}
