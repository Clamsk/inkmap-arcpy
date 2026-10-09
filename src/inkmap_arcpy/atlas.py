"""Compose a portable, elegant watercolor atlas from an existing ArcGIS Pro map."""
import json
import math
import os
from pathlib import Path
from . import __version__
from .symbols import arcpy_module, apply_style, validate_layer, cim, stroke, fill
from .workflow import unique
from .layout_primitives import (INK, MUTED, PAPER, ref, polygon, text, line, rectangle,
                                text_symbol, element, compass_symbol, update_labels, graticule, edge_labels)


def load_atlas_config(path):
    path = Path(os.path.abspath(path))
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    for key in ("project","output_folder","project_template","layout_template"):
        if config.get(key):
            config[key] = os.path.abspath(path.parent/config[key])
    for locator in config.get("locators",[]):
        locator["geojson"] = os.path.abspath(path.parent/locator["geojson"])
    return config


def validate_atlas_config(config):
    allowed = {"project","map","layers","output_folder","center","scale","title","subtitle","english_title",
               "caption","source_note","projection","legend","locators","grid_seconds","dpi","palette",
               "texture_size","legend_transparency","scale_transparency","project_template","layout_template"}
    unknown = set(config)-allowed
    if unknown:
        raise ValueError(f"Unsupported atlas keys: {sorted(unknown)}")
    for key in ("project","map","layers","output_folder","center","scale","title"):
        if key not in config:
            raise ValueError(f"Missing atlas key: {key}")
    if not isinstance(config["layers"],dict) or not config["layers"]:
        raise ValueError("layers must map exact source layer longNames to roles or descriptors")
    center = config["center"]
    if (not isinstance(center,(list,tuple)) or len(center)!=2 or
        any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in center) or
        not -180<=center[0]<=180 or not -85<=center[1]<=85):
        raise ValueError("center must be finite WGS84 [longitude, latitude] within -180..180 / -85..85")
    for key,default,minimum,maximum in [("scale",None,100,1e8),("grid_seconds",30,1,3600),
                                       ("dpi",240,72,1200),("texture_size",112,1,1000),
                                       ("legend_transparency",38,0,90),("scale_transparency",40,0,90)]:
        value = config.get(key,default)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not minimum<=value<=maximum:
            raise ValueError(f"{key} must be finite in {minimum}..{maximum}")
    if not isinstance(config.get("dpi",240),int):
        raise ValueError("dpi must be an integer")
    if any(not isinstance(value,(str,dict)) for value in config["layers"].values()):
        raise ValueError("Layer descriptors must be roles or objects")
    legends = config.get("legend",[{"layer":name,"label":name} for name,value in config["layers"].items()
                                 if (value if isinstance(value,str) else value.get("role"))!="paper"])
    if not isinstance(legends,list) or len(legends)>15:
        raise ValueError("The three-column inset legend supports up to fifteen items")
    for item in legends:
        if not isinstance(item,dict) or set(item)!={"layer","label"} or item["layer"] not in config["layers"]:
            raise ValueError("Each legend item needs a bound layer and a label")
    for name,value in config["layers"].items():
        if not isinstance(value,(str,dict)):
            raise ValueError(f"Invalid layer descriptor: {name}")
        if isinstance(value,dict):
            if "role" not in value:
                raise ValueError(f"Layer descriptor needs role: {name}")
            for key in ("fill_opacity","outline_opacity"):
                if key in value and (isinstance(value[key],bool) or not isinstance(value[key],(int,float)) or
                                     not math.isfinite(value[key]) or not 0<=value[key]<=100):
                    raise ValueError(f"{name}: {key} must be finite in 0..100")
    if len(config.get("locators",[]))>3:
        raise ValueError("This A4 portrait theme supports up to three locator circles")
    for locator in config.get("locators",[]):
        if set(locator)-{"geojson","caption","highlight","code_field","name_field","projection","grid_degrees"}:
            raise ValueError("Unsupported locator options")
        for key in ("geojson","caption","highlight"):
            if key not in locator:
                raise ValueError(f"Locator needs {key}")
        step=locator.get("grid_degrees",1)
        if isinstance(step,bool) or not isinstance(step,(int,float)) or not math.isfinite(step) or not 0<step<=180:
            raise ValueError("Locator grid_degrees must be finite in (0,180]")
    return config


def _bind(config):
    arcpy = arcpy_module()
    source = arcpy.mp.ArcGISProject(config["project"])
    source_map = unique(source.listMaps(),config["map"],"map")
    bindings = []
    for name,value in config["layers"].items():
        descriptor = {"role":value} if isinstance(value,str) else dict(value)
        if set(descriptor)-{"role","label_field","label_font","label_size","label_color","label_priority","fill_opacity","outline_opacity"}:
            raise ValueError(f"Unsupported descriptor for {name}")
        layer = unique(source_map.listLayers(),name,"layer")
        if layer.isBroken:
            raise ValueError(f"Broken source: {name}")
        validate_layer(layer,descriptor["role"],True)
        if arcpy.Describe(layer).spatialReference.name == "Unknown":
            raise ValueError(f"Unknown CRS: {name}")
        field = descriptor.get("label_field")
        if field and field not in {f.name for f in arcpy.ListFields(layer)}:
            raise ValueError(f"Missing label field {field} in {name}")
        bindings.append((name,layer,descriptor))
    sr = arcpy.SpatialReference(config["projection"]) if config.get("projection") else arcpy.SpatialReference()
    if not config.get("projection"):
        sr.loadFromString(source_map.spatialReference.exportToString())
    if sr.type != "Projected" or abs(sr.metersPerUnit-1)>1e-6 or sr.factoryCode in {3857,102100,102113}:
        raise ValueError("The atlas theme requires a locally appropriate projected CRS in meters; set projection")
    for locator in config.get("locators",[]):
        document = json.loads(Path(locator["geojson"]).read_text(encoding="utf-8"))
        if document.get("type")!="FeatureCollection" or not document.get("features"):
            raise ValueError("Locator must be a nonempty GeoJSON FeatureCollection")
        key = locator.get("code_field","adcode")
        selected = [f for f in document["features"] if str(f["properties"].get(key))==str(locator["highlight"])]
        if len(selected)!=1:
            raise ValueError("Locator highlight must match exactly one published boundary feature")
        if any(f["geometry"]["type"] not in {"Polygon","MultiPolygon"} for f in document["features"]):
            raise ValueError("Locators require actual Polygon/MultiPolygon boundaries")
    return source,bindings,sr


def compose_atlas(config,dry_run=False):
    """Copy input features into a new GDB; create full/cropped layouts and native locators.

    Layer descriptors are drawn in configuration order, bottom to top. No center marker is added.
    A new output directory is required; a failed partial directory is never silently overwritten.
    """
    validate_atlas_config(config)
    arcpy = arcpy_module()
    source,bindings,sr = _bind(config)
    out = Path(os.path.abspath(config["output_folder"]))
    if out.exists():
        raise FileExistsError(f"Use a new output folder: {out}")
    report = {"version":__version__,"output_folder":str(out),"title":config["title"],
              "center_wgs84":config["center"],"center_marker":False,"scale":config["scale"],
              "projection":sr.name,"bindings":{name:d["role"] for name,layer,d in bindings},
              "locator_count":len(config.get("locators",[])),"dry_run":dry_run}
    if dry_run:
        return report
    install = Path(arcpy.GetInstallInfo()["InstallDir"])
    project_template = config.get("project_template",str(install/"Resources/ArcToolBox/Services/routingservices/data/Blank.aprx"))
    layout_template = config.get("layout_template",str(install/"Resources/ArcToolBox/Templates/ExportWebMapTemplates/A4 Portrait.pagx"))
    if not Path(project_template).is_file() or not Path(layout_template).is_file():
        raise FileNotFoundError("Pro templates not found; provide project_template and layout_template")
    out.mkdir(parents=True)
    gdb = str(out/"atlas.gdb")
    arcpy.management.CreateFileGDB(str(out),"atlas.gdb")
    project = arcpy.mp.ArcGISProject(project_template)
    project.homeFolder,project.defaultGeodatabase = str(out),gdb
    m = project.listMaps()[0]
    m.name = config["title"]
    m.spatialReference = sr
    for layer in m.listLayers():
        m.removeLayer(layer)
    layers,roles,counts = {},{},{}
    warm = (117,109,93)
    defaults = {"green":("STKaiti",9,warm,2),"roads_main":("STSong",6.2,warm,9),
                "station":("STKaiti",8.4,warm,2),"buildings":("STSong",7.8,warm,4),
                "site":("STKaiti",8.4,warm,2),"community":("STKaiti",7.5,warm,4),
                "place_label":("STKaiti",8,warm,4)}
    for i,(name,source_layer,descriptor) in enumerate(bindings):
        target = str(Path(gdb)/f"layer_{i:03d}")
        source_count = int(arcpy.management.GetCount(source_layer)[0])
        if arcpy.Describe(source_layer).spatialReference.exportToString()==sr.exportToString():
            arcpy.management.CopyFeatures(source_layer,target)
        else:
            arcpy.management.Project(source_layer,target,sr)
        counts[name] = int(arcpy.management.GetCount(target)[0])
        if counts[name]!=source_count:
            raise RuntimeError(f"Import lost features for {name}: {source_count} -> {counts[name]}")
        layer = m.addDataFromPath(target)
        layer.name = name
        role = descriptor["role"]
        apply_style(layer,role,config.get("palette","watercolor"),config.get("texture_size",112))
        if "fill_opacity" in descriptor or "outline_opacity" in descriptor:
            definition = layer.getDefinition("V3")
            for symbol in definition.renderer.symbol.symbol.symbolLayers:
                key = "fill_opacity" if symbol.__class__.__name__=="CIMSolidFill" else "outline_opacity"
                if key in descriptor and hasattr(symbol,"color") and symbol.color:
                    symbol.color.values[-1] = descriptor[key]
            layer.setDefinition(definition)
        field = descriptor.get("label_field")
        if field:
            cls = layer.listLabelClasses()[0]
            cls.expression = "$feature["+json.dumps(field)+"]"
            cls.SQLQuery = f"{arcpy.AddFieldDelimiters(target,field)} IS NOT NULL"
            cls.visible = True
            layer.showLabels = True
            font,size,rgb,priority = defaults.get(role,("STSong",7.5,INK,5))
            update_labels(layer,descriptor.get("label_font",font),descriptor.get("label_size",size),
                          descriptor.get("label_color",rgb),descriptor.get("label_priority",priority))
            if role=="roads_main":
                d=layer.getDefinition("V3")
                for cls in d.labelClasses:
                    cls.maplexLabelPlacementProperties.thinDuplicateLabels=True
                    cls.maplexLabelPlacementProperties.thinningDistance=80
                    cls.maplexLabelPlacementProperties.thinningDistanceUnit="Point"
                layer.setDefinition(d)
        layers[name],roles[name] = layer,role
    project.importDocument(layout_template)
    layout = project.listLayouts()[-1]
    layout.name = "Watercolor atlas · full"
    frame = layout.listElements("MAPFRAME_ELEMENT")[0]
    frame.map = m
    frame.name = "Atlas main frame"
    frame.elementPositionX,frame.elementPositionY = 1,1.65
    frame.elementWidth,frame.elementHeight = 19,24
    point = arcpy.PointGeometry(arcpy.Point(*config["center"]),arcpy.SpatialReference(4326)).projectAs(sr).firstPoint
    frame.camera.X,frame.camera.Y,frame.camera.scale = point.X,point.Y,config["scale"]
    frame.camera.heading = 0
    if "paper" not in roles.values():
        extent=frame.camera.getExtent()
        fc=str(Path(gdb)/"page_paper")
        arcpy.management.CreateFeatureclass(gdb,"page_paper","POLYGON",spatial_reference=sr)
        ring=arcpy.Array([arcpy.Point(extent.XMin,extent.YMin),arcpy.Point(extent.XMax,extent.YMin),
                          arcpy.Point(extent.XMax,extent.YMax),arcpy.Point(extent.XMin,extent.YMax),arcpy.Point(extent.XMin,extent.YMin)])
        with arcpy.da.InsertCursor(fc,["SHAPE@"]) as cursor:
            cursor.insertRow([arcpy.Polygon(ring,sr)])
        paper=m.addDataFromPath(fc)
        paper.name="Paper background"
        apply_style(paper,"paper",texture_size=config.get("texture_size",112))
        m.moveLayer(m.listLayers()[-1],paper,"AFTER")
    d=layout.getDefinition("V3")
    main_def=next(e for e in d.elements if e.name==frame.name)
    main_def.grids=[graticule(config.get("grid_seconds",30)/3600,"WGS84 dashed graticule")]
    main_def.graphicFrame.backgroundSymbol=ref(polygon(PAPER))
    main_def.graphicFrame.borderSymbol=ref(polygon(PAPER,0,MUTED,0.35))
    main_def.graphicFrame.shadowSymbol=None
    arrow=next(e for e in d.elements if e.name=="North Arrow")
    arrow.visible=True
    arrow.mapFrame=frame.name
    arrow.pointSymbol=ref(compass_symbol())
    arrow.northType="TrueNorth"
    surround=next(e for e in d.elements if e.name=="Scale bar")
    old_bar=next(e for e in surround.elements if e.name=="Scale Line 1")
    bar=cim("CIMDoubleFillScaleBar")
    for key,value in vars(old_bar).items():
        if hasattr(bar,key):
            setattr(bar,key,value)
    bar.name,bar.mapFrame,bar.style="Atlas scale bar",frame.name,"Alternating"
    bar.units,bar.unitLabel,bar.divisionsBeforeZero={"uwkid":9001},"m",0
    bar.divisions,bar.subdivisions,bar.barHeight=2,2,2.8
    # Aim for a 4.5 cm bar at the configured map scale; choose a readable metric distance.
    candidates=[50,100,200,250,500,1000,2000,5000,10000,20000,50000,100000,200000,500000,1000000]
    total=min(candidates,key=lambda v:abs(math.log(v/(config["scale"]*0.045))))
    bar.division,bar.fittingStrategy=total/2,"AdjustFrame"
    bar.fillSymbol1=ref(polygon(INK,100,INK,0.3))
    bar.fillSymbol2=ref(polygon(PAPER,100,INK,0.3))
    bar.labelSymbol=ref(text_symbol("Garamond",8.5,INK))
    bar.unitLabelSymbol=ref(text_symbol("Garamond",8.5,INK))
    bar.labelFrequency,bar.labelGap="DivisionsAndFirstMidpoint",3
    bar.graphicFrame.backgroundSymbol=None
    bar.graphicFrame.borderSymbol=None
    bar.graphicFrame.shadowSymbol=None
    surround.elements=[bar]
    legends=config.get("legend",[{"layer":name,"label":name} for name in layers if roles[name]!="paper"])
    legend_height = .95 + math.ceil(len(legends)/3)*.50
    legend_top = 2.82 + legend_height
    graphics=[rectangle("Page paper",0,0,21,29.7,PAPER,100),main_def,
              rectangle("Legend paper",1.45,2.82,9.60,legend_height,PAPER,100-config.get("legend_transparency",38),(183,177,160)),
              rectangle("Scale paper",13.7,2.08,5.8,1.62,PAPER,100-config.get("scale_transparency",40)),
              text("Title",config["title"],10.5,28.95,30,"STSong",INK,"Center",3),
              text("English title",config.get("english_title","W A T E R C O L O R   A T L A S"),10.5,27.46,8.5,"Garamond",MUTED,"Center"),
              text("Subtitle",config.get("subtitle","水彩区位图"),10.5,26.95,10.5,"STKaiti",INK,"Center",1.5),
              line("Header rule",[[1,26.30],[8.8,26.30]],MUTED,0.3,70),
              line("Header rule right",[[12.2,26.30],[20,26.30]],MUTED,0.3,70),
              text("Header caption",config.get("caption","街巷 · 园林 · 水脉"),10.5,26.52,7.2,"STSong",MUTED,"Center"),
              text("Legend title","图 例",1.85,legend_top-.33,12.5,"STKaiti"),
              text("Legend english","L E G E N D",10.65,legend_top-.43,7,"Garamond",MUTED,"Right"),
              line("Legend rule",[[1.85,legend_top-.70],[10.65,legend_top-.70]],MUTED,0.3,65),
              text("Compass N","N",2.05,25.24,10,"Garamond",INK,"Center"),
              text("Scale caption","米制比例尺",16.55,3.55,7.3,"STSong",MUTED,"Center"),
              text("Source",config.get("source_note",""),1,0.70,6.3,"STSong",MUTED),
              text("Frame attribution",config.get("source_note",""),1.13,1.91,5.8,"STSong",MUTED)]
    for i,item in enumerate(legends):
        layer=layers[item["layer"]]
        x,y=1.86+(i%3)*3.08,legend_top-.93-(i//3)*0.50
        symbol=layer.getDefinition("V3").renderer.symbol
        shape=arcpy.Describe(layer).shapeType
        if shape=="Point":
            graphic=cim("CIMPointGraphic",location={"x":x+0.24,"y":y-0.14},symbol=symbol)
        elif shape=="Polyline":
            graphic=cim("CIMLineGraphic",line={"paths":[[[x,y-0.14],[x+0.48,y-0.14]]]},symbol=symbol)
        else:
            graphic=cim("CIMPolygonGraphic",polygon={"rings":[[[x,y-0.27],[x+0.48,y-0.27],[x+0.48,y-0.01],[x,y-0.01],[x,y-0.27]]]},symbol=symbol)
        graphics.extend([element(f"Legend patch {i}",graphic),text(f"Legend text {i}",item["label"],x+0.65,y,8)])
    d.elements=graphics+[arrow,surround]
    layout.setDefinition(d)
    north=layout.listElements("MAPSURROUND_ELEMENT","North Arrow")[0]
    north.elementWidth=north.elementHeight=1.06
    north.elementPositionX,north.elementPositionY=2.05,24.42
    scale_element=layout.listElements("MAPSURROUND_ELEMENT","Atlas scale bar")[0]
    scale_element.elementPositionX,scale_element.elementPositionY=14.15,2.55
    if config.get("locators"):
        _add_locators(arcpy,project,layout,frame,gdb,out,config["locators"])
    labels,label_count=edge_labels(frame,config.get("grid_seconds",30)/3600)
    d=layout.getDefinition("V3")
    d.elements+=labels
    layout.setDefinition(d)
    dpi=config.get("dpi",240)
    layout.exportToPNG(str(out/"atlas_full.png"),resolution=dpi)
    layout.exportToPDF(str(out/"atlas_full.pdf"),resolution=300,image_quality="BEST",output_as_image=True,
                       image_compression="ADAPTIVE",jpeg_compression_quality=90)
    page=out/"atlas.pagx"
    layout.exportToPAGX(str(page))
    names={l.name for l in project.listLayouts()}
    project.importDocument(str(page),reuse_existing_maps=True)
    cropped=next(l for l in project.listLayouts() if l.name not in names)
    cropped.name="Watercolor atlas · frame"
    d=cropped.getDefinition("V3")
    outside={"Page paper","Title","English title","Subtitle","Header rule","Header rule right","Header caption","Source"}
    d.elements=[e for e in d.elements if e.name not in outside]
    # Native clip_to_elements underestimates rotated point-text bounds on Pro 3.0.
    # Include an invisible padding polygon so corner graticule labels stay complete.
    d.elements.append(rectangle("Frame crop padding",0.5,1.0,20,25.3,PAPER,0))
    cropped.setDefinition(d)
    cropped.exportToPNG(str(out/"atlas_frame.png"),resolution=dpi,clip_to_elements=True)
    cropped.exportToPDF(str(out/"atlas_frame.pdf"),resolution=300,image_quality="BEST",output_as_image=True,
                        image_compression="ADAPTIVE",jpeg_compression_quality=90,clip_to_elements=True)
    frame.exportToPNG(str(out/"atlas_map_only.png"),resolution=dpi,world_file=True)
    project.saveACopy(str(out/"atlas.aprx"))
    reloaded=arcpy.mp.ArcGISProject(str(out/"atlas.aprx"))
    broken=[layer.name for m in reloaded.listMaps() for layer in m.listLayers() if layer.isBroken]
    if broken:
        raise RuntimeError(f"Saved project has broken sources: {broken}")
    report.update({"feature_counts":counts,"grid_labels":label_count,"scale_bar_meters":total,
                   "project":str(out/"atlas.aprx"),"broken_layers":broken,
                   "exports":["atlas_full.png","atlas_full.pdf","atlas_frame.png","atlas_frame.pdf","atlas_map_only.png"],
                  "textures":"Selected soft wet-ink and independent paper PNG, MIT; see assets/material.json"})
    (out/"atlas_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report


def _add_locators(arcpy,project,layout,frame,gdb,out,specs):
    seed=out/"locator_seed.mapx"
    frame.map.exportToMAPX(str(seed))
    positions={1:[18.34],2:[14.72,18.34],3:[11.10,14.72,18.34]}[len(specs)]
    for i,(spec,cx) in enumerate(zip(specs,positions)):
        sr=arcpy.SpatialReference(spec.get("projection",102012))
        fc=str(Path(gdb)/f"locator_{i}")
        arcpy.management.CreateFeatureclass(gdb,f"locator_{i}","POLYGON",spatial_reference=sr)
        arcpy.management.AddField(fc,"code","TEXT",field_length=100)
        arcpy.management.AddField(fc,"label","TEXT",field_length=200)
        features=json.loads(Path(spec["geojson"]).read_text(encoding="utf-8"))["features"]
        with arcpy.da.InsertCursor(fc,["SHAPE@","code","label"]) as cursor:
            for f in features:
                cursor.insertRow([arcpy.AsShape(f["geometry"]).projectAs(sr),str(f["properties"][spec.get("code_field","adcode")]),
                                  str(f["properties"].get(spec.get("name_field","name"),""))])
        previous={m.URI for m in project.listMaps()}
        project.importDocument(str(seed))
        m=next(m for m in project.listMaps() if m.URI not in previous)
        m.name="Locator "+spec["caption"]
        m.spatialReference=sr
        for layer in m.listLayers():
            m.removeLayer(layer)
        base=m.addDataFromPath(fc)
        base.name="Published boundaries"
        d=base.getDefinition("V3")
        d.renderer.symbol=ref(polygon((185,211,220),95,(133,150,149),0.18))
        base.setDefinition(d)
        selected=m.addDataFromPath(fc)
        selected.name="Highlighted region"
        selected.definitionQuery="code = '"+str(spec["highlight"]).replace("'","''")+"'"
        d=selected.getDefinition("V3")
        d.renderer.symbol=ref(polygon((124,168,173),100,(162,102,87),0.48))
        selected.setDefinition(d)
        fd=next(e for e in layout.getDefinition("V3").elements if e.name==frame.name)
        name=f"Locator frame {i}"
        cy,diameter=23.72,3.1
        radius=diameter/2
        fd.name,fd.uRI,fd.anchor=name,m.URI,"CenterPoint"
        fd.frame={"rings":[[[cx+radius*math.cos(j*math.pi/96),cy+radius*math.sin(j*math.pi/96)] for j in range(193)]]}
        fd.rotationCenter=arcpy.Point(cx,cy)
        fd.graphicFrame.backgroundSymbol=ref(polygon(PAPER,96))
        fd.graphicFrame.borderSymbol=ref(polygon(PAPER,0,INK,0.4))
        fd.grids=[graticule(spec.get("grid_degrees",1),"Locator dashed graticule")]
        d=layout.getDefinition("V3")
        d.elements+=[fd,text(f"Locator caption {i}",spec["caption"],cx,22.65,7.4,"STSong",INK,"Center")]
        layout.setDefinition(d)
        inset=layout.listElements("MAPFRAME_ELEMENT",name)[0]
        inset.map=m
        extent=arcpy.Describe(fc).extent
        midx,midy=(extent.XMin+extent.XMax)/2,(extent.YMin+extent.YMax)/2
        maximum=max(math.hypot(p.X-midx,p.Y-midy) for row in arcpy.da.SearchCursor(fc,["SHAPE@"])
                    for part in row[0] for p in part if p)
        inset.camera.X,inset.camera.Y=midx,midy
        inset.camera.heading=0
        inset.camera.scale=2*maximum*1.06/(diameter/100)
