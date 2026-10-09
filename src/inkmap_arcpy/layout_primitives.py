"""Native, editable layout primitives, compatible with ArcGIS Pro 3.0 and CIM V3."""
import math
from .symbols import arcpy_module, cim, fill, stroke
INK=(66,83,77)
MUTED=(116,124,111)
PAPER=(249,247,239)

def ref(symbol):
    return cim("CIMSymbolReference", symbol=symbol)

def polygon(rgb, alpha=100, edge=None, width=0.35):
    layers = ([stroke(edge, width)] if edge else []) + [fill(rgb, alpha)]
    return cim("CIMPolygonSymbol", symbolLayers=layers)

def text_symbol(font, size, rgb=INK, align="Left", spacing=0):
    return cim("CIMTextSymbol", fontFamilyName=font, fontStyleName="Regular", height=size,
               horizontalAlignment=align, verticalAlignment="Top", letterSpacing=spacing,
               symbol=polygon(rgb))

def element(name, graphic, anchor="BottomLeftCorner"):
    return cim("CIMGraphicElement", name=name, visible=True, anchor=anchor, graphic=graphic)

def text(name, value, x, y, size=8, font="STSong", rgb=INK, align="Left", spacing=0):
    return element(name, cim("CIMTextGraphic", text=value, shape={"x": x, "y": y},
                            symbol=ref(text_symbol(font, size, rgb, align, spacing))), "TopLeftCorner")

def area(name, points, symbol):
    return element(name, cim("CIMPolygonGraphic", polygon={"rings": [points]}, symbol=ref(symbol)))

def rectangle(name, x, y, width, height, rgb=PAPER, alpha=96, edge=None):
    return area(name, [[x,y],[x+width,y],[x+width,y+height],[x,y+height],[x,y]],
                polygon(rgb, alpha, edge))

def line(name, points, rgb=MUTED, width=0.35, alpha=100):
    return element(name, cim("CIMLineGraphic", line={"paths": [points]},
                            symbol=ref(cim("CIMLineSymbol", symbolLayers=[stroke(rgb,width,alpha)]))))

def compass_symbol():
    """Small eight-point rose as a native marker, used by a true-north map surround."""
    graphics = []
    ring = [[8.5*math.cos(i*math.pi/48), 8.5*math.sin(i*math.pi/48)] for i in range(97)]
    graphics.append(cim("CIMMarkerGraphic", geometry={"rings":[ring]},
                        symbol=polygon(PAPER, 94, MUTED, 0.22)))
    for k in range(8):
        angle = k*math.pi/4
        length = 8.0 if k%2==0 else 4.8
        tip = [length*math.sin(angle), length*math.cos(angle)]
        left = [1.35*math.sin(angle-math.pi/2),1.35*math.cos(angle-math.pi/2)]
        right = [-left[0],-left[1]]
        for side, shade in [(left,INK),(right,(215,222,211))]:
            graphics.append(cim("CIMMarkerGraphic", geometry={"rings":[[[0,0],side,tip,[0,0]]]},
                                symbol=polygon(shade,100,INK,0.16)))
    marker = cim("CIMVectorMarker",enable=True,size=30,
                 frame={"xmin":-9,"ymin":-9,"xmax":9,"ymax":9},markerGraphics=graphics,
                 respectFrame=True,scaleSymbolsProportionally=True)
    return cim("CIMPointSymbol",symbolLayers=[marker])

def update_labels(layer, font, size, rgb, priority):
    if not layer.showLabels:
        return
    d = layer.getDefinition("V3")
    for label in d.labelClasses:
        ts = label.textSymbol.symbol
        ts.fontFamilyName = font
        ts.fontStyleName = "Regular"
        ts.height = size
        ts.symbol = polygon(rgb)
        ts.haloSymbol = polygon(PAPER,84)
        ts.haloSize = 0.4
        label.priority = priority
    layer.setDefinition(d)

def graticule(step, name):
    arcpy = arcpy_module()
    grid = cim("CIMGraticule",name=name,isVisible=True,isAutoScaled=False,
               geographicCoordinateSystem={"wkid":4326},customOrigin=arcpy.Point(0,0),useMapClipShape=False)
    grid.neatlineSymbol = ref(cim("CIMLineSymbol",symbolLayers=[stroke(MUTED,0.35,70)]))
    grid.gridLines = [cim("CIMGridLine",name=name+orientation,elementType="Line",
                          gridLineOrientation=orientation,
                          symbol=ref(cim("CIMLineSymbol",symbolLayers=[stroke((131,138,123),0.42,46,(5,4))])),
                          fromTick=cim("CIMExteriorTick",isVisible=False,length=0),
                          toTick=cim("CIMExteriorTick",isVisible=False,length=0),
                          pattern=cim("CIMGridPattern",interval=step,start=0,stop=1,gap=0))
                      for orientation in ("NorthSouth","EastWest")]
    return grid

def dms(value, direction):
    if value<0:
        direction = {"E":"W","N":"S"}.get(direction,direction)
    total = round(abs(value)*3600)
    degrees, remainder = divmod(total,3600)
    minutes,seconds = divmod(remainder,60)
    return f"{degrees}°{minutes:02d}′{seconds:02d}″{direction}"

def edge_labels(frame, step=1/120):
    """Labels/ticks at exact projected intersections of geographic meridians/parallels with the frame."""
    arcpy = arcpy_module()
    # Map.spatialReference is a native proxy on Pro 3.0; geometry constructors need a fresh ArcPy object.
    UTM = arcpy.SpatialReference()
    UTM.loadFromString(frame.map.spatialReference.exportToString())
    WGS = arcpy.SpatialReference(4326)
    ext = frame.camera.getExtent()
    x0,y0,w,h = frame.elementPositionX,frame.elementPositionY,frame.elementWidth,frame.elementHeight
    ring = arcpy.Array([arcpy.Point(ext.XMin,ext.YMin),arcpy.Point(ext.XMax,ext.YMin),
                        arcpy.Point(ext.XMax,ext.YMax),arcpy.Point(ext.XMin,ext.YMax),arcpy.Point(ext.XMin,ext.YMin)])
    clip = arcpy.Polygon(ring,UTM)
    corners = [arcpy.PointGeometry(point,UTM).projectAs(WGS).firstPoint for point in ring]
    lon_min,lon_max = min(p.X for p in corners),max(p.X for p in corners)
    lat_min,lat_max = min(p.Y for p in corners),max(p.Y for p in corners)
    graphics = []
    count = 0
    for axis,minimum,maximum in [("lon",lon_min,lon_max),("lat",lat_min,lat_max)]:
        indices = range(math.ceil(minimum/step),math.floor(maximum/step)+1)
        for index in indices:
            value = index*step
            if axis == "lon":
                coords = [(value,lat_min-0.1+i*(lat_max-lat_min+0.2)/100) for i in range(101)]
            else:
                coords = [(lon_min-0.1+i*(lon_max-lon_min+0.2)/100,value) for i in range(101)]
            geographic = arcpy.Polyline(arcpy.Array([arcpy.Point(*xy) for xy in coords]),WGS)
            projected = geographic.projectAs(UTM).intersect(clip,2)
            if projected.pointCount == 0:
                continue
            for point in (projected.firstPoint,projected.lastPoint):
                x = x0+(point.X-ext.XMin)/ext.width*w
                y = y0+(point.Y-ext.YMin)/ext.height*h
                count += 1
                if axis == "lon":
                    top = y > y0+h/2
                    end = y+(0.09 if top else -0.09)
                    graphics.append(line(f"Grid tick {count}",[[x,y],[x,end]],MUTED,0.3,65))
                    graphics.append(text(f"Grid label {count}",dms(value,"E"),x,y+(0.30 if top else -0.13),
                                         6.4,"Garamond",INK,"Center"))
                else:
                    right = x > x0+w/2
                    end = x+(0.09 if right else -0.09)
                    graphics.append(line(f"Grid tick {count}",[[x,y],[end,y]],MUTED,0.3,65))
                    label = text(f"Grid label {count}",dms(value,"N"),x+(0.30 if right else -0.13),y,
                                 6.4,"Garamond",INK,"Center")
                    label.graphic.symbol.symbol.angle = 90
                    graphics.append(label)
    return graphics,count
