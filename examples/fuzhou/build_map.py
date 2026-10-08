"""Render the prepared real Fuzhou data with native ArcGIS Pro / InkMap symbols."""
import argparse
import json
import os
from pathlib import Path
import arcpy
from inkmap_arcpy import apply_style, get_palette
from inkmap_arcpy.symbols import cim, fill, stroke, color

ROOT = Path(os.path.abspath(__file__)).parent
DATA = ROOT / "data"
SR = arcpy.SpatialReference(32650)
WGS = arcpy.SpatialReference(4326)
COLORS = get_palette("watercolor")
META = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))


def label_style(layer, rgb, size=8, bold=False, query=None, priority=5):
    cls = layer.listLabelClasses()[0]
    cls.expression = "$feature.label"
    cls.SQLQuery = query or "label <> ''"
    cls.visible = True
    layer.showLabels = True
    definition = layer.getDefinition("V3")
    for label in definition.labelClasses:
        text = label.textSymbol.symbol
        text.fontFamilyName = "Microsoft YaHei"
        text.fontStyleName = "Bold" if bold else "Regular"
        text.height = size
        text.symbol = cim("CIMPolygonSymbol",symbolLayers=[fill(rgb)])
        text.haloSymbol = cim("CIMPolygonSymbol",symbolLayers=[fill((255,255,255),95)])
        text.haloSize = 0.8
        if hasattr(label,"priority"):
            label.priority = priority
    layer.setDefinition(definition)


def main(output, resume=False):
    out = Path(os.path.abspath(output))
    if out.exists() and not resume:
        raise FileExistsError(f"Choose a new output directory: {out}")
    if resume and not (out / "fuzhou.gdb").is_dir():
        raise ValueError("Resume requires this example's previously generated fuzhou.gdb")
    out.mkdir(parents=True,exist_ok=True)
    gdb = str(out / "fuzhou.gdb")
    if not arcpy.Exists(gdb):
        arcpy.management.CreateFileGDB(str(out),"fuzhou.gdb")
    install = Path(arcpy.GetInstallInfo()["InstallDir"])
    project = arcpy.mp.ArcGISProject(str(install / "Resources/ArcToolBox/Services/routingservices/data/Blank.aprx"))
    project.homeFolder = str(out)
    project.defaultGeodatabase = gdb
    m = project.listMaps()[0]
    m.name = "福州中心城区水彩地图"
    m.spatialReference = SR
    for layer in m.listLayers():
        m.removeLayer(layer)
    layers = {}
    counts = {}

    def add(key, name, role=None):
        path = DATA / "geojson" / (key+".geojson")
        source = str(Path(gdb) / (key+"_wgs84"))
        target = str(Path(gdb) / key)
        doc = json.loads(path.read_text(encoding="utf-8"))
        counts[key] = len(doc["features"])
        geometry_type = "POLYLINE" if key in {"roads_main","roads_other","water_lines"} else "POINT" if key in {"stations","communities"} else "POLYGON"
        if not arcpy.Exists(source):
            arcpy.conversion.JSONToFeatures(str(path),source,geometry_type)
        # ArcGIS Pro 3.0 defaults GeoJSON import to polygons; specify geometry and CRS explicitly.
        arcpy.management.DefineProjection(source,WGS)
        imported = int(arcpy.management.GetCount(source)[0])
        if imported != counts[key]:
            raise RuntimeError(f"{key}: imported {imported}, expected {counts[key]}")
        if not arcpy.Exists(target):
            arcpy.management.Project(source,target,SR)
        layer = m.addDataFromPath(target)
        layer.name = name
        if role:
            apply_style(layer,role,texture_size=95)
        layers[key] = layer
        print(f"Imported {key}: {counts[key]}",flush=True)
        return layer

    # A paper rectangle in the projected data extent, under all geographic content.
    south,west,north,east = META["bbox_wgs84"]
    corners = [arcpy.PointGeometry(arcpy.Point(lon,lat),WGS).projectAs(SR).firstPoint
               for lon,lat in [(west,south),(east,south),(east,north),(west,north)]]
    bounds = arcpy.Extent(min(p.X for p in corners),min(p.Y for p in corners),
                          max(p.X for p in corners),max(p.Y for p in corners),spatial_reference=SR)
    paper_fc = str(Path(gdb)/"paper")
    if not arcpy.Exists(paper_fc):
        arcpy.management.CreateFeatureclass(gdb,"paper","POLYGON",spatial_reference=SR)
    ring = arcpy.Array([arcpy.Point(bounds.XMin,bounds.YMin),arcpy.Point(bounds.XMax,bounds.YMin),
                        arcpy.Point(bounds.XMax,bounds.YMax),arcpy.Point(bounds.XMin,bounds.YMax),
                        arcpy.Point(bounds.XMin,bounds.YMin)])
    if int(arcpy.management.GetCount(paper_fc)[0]) == 0:
        with arcpy.da.InsertCursor(paper_fc,["SHAPE@"]) as cur:
            cur.insertRow([arcpy.Polygon(ring,SR)])
    paper = m.addDataFromPath(paper_fc)
    paper.name = "纸纹背景"
    apply_style(paper,"paper",texture_size=95)
    residential = add("residential","居住区范围（OSM）","buildings")
    dc = residential.getDefinition("V3")
    dc.renderer.symbol.symbol.symbolLayers = [stroke((185,171,145),0.12,30),fill((224,214,193),24)]
    residential.setDefinition(dc)
    add("buildings","建筑轮廓","buildings")
    add("green","其他绿地与林地","green")
    parks = add("parks","公园与花园","green")
    label_style(parks,(42,99,66),8.0,bold=True,priority=2)
    add("water","河湖水面","water")
    waterways = add("water_lines","内河水线","roads_other")
    wc = waterways.getDefinition("V3")
    wc.renderer.symbol.symbol.symbolLayers = [stroke(COLORS.water,0.55,58)]
    waterways.setDefinition(wc)
    add("roads_other","支路与步行路","roads_other")
    roads = add("roads_main","主要道路","roads_main")
    label_style(roads,(102,130,148),6.2,priority=8)
    road_definition = roads.getDefinition("V3")
    for label in road_definition.labelClasses:
        placement = label.maplexLabelPlacementProperties
        placement.thinDuplicateLabels = True
        placement.thinningDistance = 80
        placement.thinningDistanceUnit = "Point"
    roads.setDefinition(road_definition)
    admin = add("subdistricts","街道乡镇名称（OSM）","buildings")
    dc = admin.getDefinition("V3")
    dc.renderer.symbol.symbol.symbolLayers = [fill((255,255,255),0)]
    admin.setDefinition(dc)
    label_style(admin,(119,104,84),8.0,priority=3)
    boundary_fc = str(Path(gdb)/"street_boundaries")
    if not arcpy.Exists(boundary_fc):
        arcpy.management.CreateFeatureclass(gdb,"street_boundaries","POLYLINE",spatial_reference=SR)
        with arcpy.da.SearchCursor(admin,["SHAPE@"]) as rows, arcpy.da.InsertCursor(boundary_fc,["SHAPE@"]) as insert:
            for row in rows:
                insert.insertRow([row[0].boundary()])
    boundary = m.addDataFromPath(boundary_fc)
    boundary.name = "街道乡镇界（OSM）"
    apply_style(boundary,"boundary")
    bc = boundary.getDefinition("V3")
    bc.renderer.symbol.symbol.symbolLayers = [stroke((143,130,108),0.40,50,(5,4))]
    boundary.setDefinition(bc)
    add("stations","地铁站点","station")
    communities = add("communities","社区名称点（OSM）","station")
    cc = communities.getDefinition("V3")
    graphic = cc.renderer.symbol.symbol.symbolLayers[0].markerGraphics[0]
    graphic.symbol.symbolLayers = [stroke((157,105,61),0.7,90),fill((255,252,247),90)]
    cc.renderer.symbol.symbol.symbolLayers[0].size = 5.0
    communities.setDefinition(cc)
    label_style(communities,(135,89,53),8,bold=True,priority=1)
    # Save named layer styles next to the project for inspection/reuse.
    for key, layer in layers.items():
        layer_file = out / (key+".lyrx")
        if resume and layer_file.exists():
            layer_file.unlink()
        layer.saveACopy(str(layer_file))

    project.importDocument(str(install / "Resources/ArcToolBox/Templates/ExportWebMapTemplates/A4 Portrait.pagx"))
    layout = project.listLayouts()[0]
    layout.name = "福州水彩地图 A4"
    frame = layout.listElements("MAPFRAME_ELEMENT")[0]
    frame.map = m
    frame.elementPositionX = 1.0
    frame.elementPositionY = 3.2
    frame.elementWidth = 19.0
    frame.elementHeight = 24.4
    frame.camera.setExtent(bounds)
    frame.camera.scale *= 1.012
    definition = layout.getDefinition("V3")
    keep = {frame.name,"Title","North Arrow","Scale bar","Credits"}
    definition.elements = [e for e in definition.elements if e.name in keep]
    for e in definition.elements:
        if e.name in {"Title","Credits"}:
            e.anchor = "TopLeftCorner"
            e.graphic.symbol.symbol.horizontalAlignment = "Left"
            e.graphic.symbol.symbol.fontFamilyName = "Microsoft YaHei"
            e.graphic.symbol.symbol.verticalAlignment = "Top"
        if e.name == "North Arrow":
            e.visible = True
        if e.name == "Scale bar":
            e.elements = [child for child in e.elements if child.name == "Scale Line 1"]
            for child in e.elements:
                child.units = {"uwkid":9001}
                child.unitLabel = "m"
    layout.setDefinition(definition)
    # Use Pro's native clone: CIM deepcopy fails on native geoprocessing Point objects in 3.0.
    credit_element = layout.listElements("TEXT_ELEMENT","Credits")[0]
    title_element = layout.listElements("TEXT_ELEMENT","Title")[0]
    title_element.clone("_Subtitle").name = "Subtitle"
    for name in ("Source","Coverage"):
        credit_element.clone("_"+name).name = name

    def text(name, content, x, y, size):
        elm = layout.listElements("TEXT_ELEMENT",name)[0]
        elm.text = content
        elm.textSize = size
        elm.elementPositionX = x
        elm.elementPositionY = y
        return elm

    text("Title","福州中心城区水彩地图",1,28.9,18)
    text("Subtitle","道路 · 街道乡镇 · 社区名称点 · 公园与水系",1,28.05,8.5)
    text("Credits","© OpenStreetMap contributors · ODbL · openstreetmap.org/copyright",1,0.78,6.5)
    text("Source","数据提取 2026-10-08 ｜ WGS 84 / UTM 50N ｜ 公园名称参考市园林中心 2026 名录",1,0.43,6.0)
    text("Coverage","中心城区局部；社区为 OSM 名称点，街道界与建筑覆盖未经官方测绘核验。",1,1.15,6.3)
    # Fixed native graphic swatches avoid Pro 3.0's mixed-geometry legend fitting defect.
    legend_specs = [(communities,"社区名称点"),(layers["stations"],"地铁站点"),
                    (boundary,"街道乡镇界"),(roads,"主要道路"),(layers["roads_other"],"支路与步行路"),
                    (layers["water"],"河湖水面"),(parks,"公园与花园"),(layers["green"],"其他绿地"),
                    (layers["buildings"],"建筑轮廓"),(residential,"居住区范围")]
    patches = []
    for i,(layer,name) in enumerate(legend_specs):
        x,y = 1.0+(i%5)*3.8, 2.80-(i//5)*0.70
        label_name = f"Legend text {i}"
        title_element.clone("_legend"+str(i)).name = label_name
        text(label_name,name,x+0.73,y,7.2)
        symbol = layer.getDefinition("V3").renderer.symbol
        shape_type = arcpy.Describe(layer).shapeType
        if shape_type == "Point":
            graphic = cim("CIMPointGraphic",location={"x":x+0.28,"y":y-0.16},symbol=symbol)
        elif shape_type == "Polyline":
            graphic = cim("CIMLineGraphic",line={"paths":[[[x,y-0.16],[x+0.55,y-0.16]]]},symbol=symbol)
        else:
            graphic = cim("CIMPolygonGraphic",polygon={"rings":[[[x,y-0.30],[x+0.55,y-0.30],
                           [x+0.55,y-0.02],[x,y-0.02],[x,y-0.30]]]},symbol=symbol)
        patches.append(cim("CIMGraphicElement",name=f"Legend patch {i}",visible=True,
                           anchor="BottomLeftCorner",graphic=graphic))
    definition = layout.getDefinition("V3")
    definition.elements += patches
    layout.setDefinition(definition)
    north = layout.listElements("MAPSURROUND_ELEMENT","North Arrow")[0]
    north.elementWidth = 0.7
    north.elementHeight = 1.1
    north.elementPositionX = 19.4
    north.elementPositionY = 28.35
    scale = layout.listElements("MAPSURROUND_ELEMENT","Scale Line 1")[0]
    scale.elementWidth = 4.5
    scale.elementPositionX = 14.0
    scale.elementPositionY = 3.8
    definition = layout.getDefinition("V3")
    for element in definition.elements:
        if element.name == "Scale bar":
            for child in element.elements:
                child.division = 1000
                child.divisions = 2
                child.subdivisions = 2
                child.fittingStrategy = "AdjustFrame"
    layout.setDefinition(definition)
    project_path = out / "fuzhou_watercolor.aprx"
    if resume and project_path.exists():
        project_path.unlink()
    project.saveACopy(str(project_path))
    layout.exportToPNG(str(out / "fuzhou_watercolor.png"),resolution=200)
    layout.exportToPDF(str(out / "fuzhou_watercolor.pdf"),resolution=300,image_quality="BEST",
                       output_as_image=True,image_compression="ADAPTIVE",jpeg_compression_quality=90)
    # A second export of the same map at an urban detail scale makes the texture easier to assess.
    center = arcpy.PointGeometry(arcpy.Point(119.301,26.049),WGS).projectAs(SR).firstPoint
    frame.camera.setExtent(arcpy.Extent(center.X-1900,center.Y-2450,center.X+1900,center.Y+2450,spatial_reference=SR))
    definition = layout.getDefinition("V3")
    for element in definition.elements:
        if element.name == "Scale bar":
            for child in element.elements:
                child.division = 500
    layout.setDefinition(definition)
    text("Title","福州台江—闽江沿岸水彩细节",1,28.9,18)
    text("Subtitle","上下杭 · 茶亭 · 烟台山周边 ｜ 同一真实数据图层的局部放大",1,28.05,8.5)
    layout.exportToPNG(str(out / "fuzhou_detail.png"),resolution=200)
    layout.exportToPDF(str(out / "fuzhou_detail.pdf"),resolution=300,image_quality="BEST",
                       output_as_image=True,image_compression="ADAPTIVE",jpeg_compression_quality=90)
    detail_project = out / "fuzhou_detail.aprx"
    if resume and detail_project.exists():
        detail_project.unlink()
    project.saveACopy(str(detail_project))
    report = {"project":str(project_path),"preview":str(out/"fuzhou_watercolor.png"),
              "pdf":str(out/"fuzhou_watercolor.pdf"),"detail":str(out/"fuzhou_detail.png"),
              "layers":counts,"projection":SR.name,"source":META}
    (out / "render_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--resume",action="store_true",help="Reuse this example's generated GDB during layout repair")
    args = parser.parse_args()
    main(args.output,args.resume)
