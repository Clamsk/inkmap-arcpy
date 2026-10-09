"""Five native CIM layers, from top to bottom: outline, bleed, wash, tint, paper."""
import base64
import math
from pathlib import Path
from .palettes import ROLES, get_palette


def arcpy_module():
    try:
        import arcpy
        import arcpy.cim  # Pro 3.0 does not expose this until explicitly imported.
    except ImportError as exc:
        raise RuntimeError("Run with ArcGIS Pro's Python environment; ArcPy is not a pip dependency.") from exc
    version = arcpy.GetInstallInfo()["Version"]
    if int(version.split(".")[0]) != 3:
        raise RuntimeError(f"This release targets ArcGIS Pro 3.x (CIM V3); found {version}")
    return arcpy


def cim(kind, **properties):
    obj = arcpy_module().cim.CreateCIMObjectFromClassName(kind, "V3")
    for name, value in properties.items():
        if not hasattr(obj, name):
            raise RuntimeError(f"CIM {kind} does not support {name} on this ArcGIS version")
        setattr(obj, name, value)
    return obj


def color(rgb, opacity=100):
    return cim("CIMRGBColor", values=[*rgb, opacity])  # CIM alpha is 0..100, not 0..255.


def fill(rgb, opacity=100):
    return cim("CIMSolidFill", enable=True, color=color(rgb, opacity))


def stroke(rgb, width, opacity=100, dash=None):
    obj = cim("CIMSolidStroke", enable=True, width=width, color=color(rgb, opacity),
              capStyle="Round", joinStyle="Round")
    if dash:
        obj.effects = [cim("CIMGeometricEffectDashes", dashTemplate=list(dash),
                           lineDashEnding="NoConstraint", controlPointEnding="NoConstraint")]
    return obj


def image_url(path):
    path = Path(path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(path.suffix.lower())
    if mime is None or not path.is_file():
        raise ValueError(f"Texture must be an existing PNG or JPEG: {path}")
    return "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def picture(path, height, opacity=100):
    return cim("CIMPictureFill", enable=True, url=image_url(path), height=height,
               scaleX=1.0, tintColor=color((255, 255, 255), opacity))


def polygon_symbol(role, palette, texture_size=112, wash_path=None, paper_path=None):
    assets = Path(__file__).parent / "assets"
    wash_path = wash_path or assets / "generated-wet-ink.png"
    paper_path = paper_path or assets / "generated-white-paper.png"
    p = get_palette(palette)
    if role == "paper":
        return cim("CIMPolygonSymbol", symbolLayers=[picture(paper_path, texture_size * .64, 30), fill(p.paper)])
    if role == "buildings":
        return cim("CIMPolygonSymbol", symbolLayers=[stroke(p.building, 0.10, 30), fill(p.building, 48)])
    rgb = p.water if role == "water" else p.green
    ramp = cim("CIMLinearContinuousColorRamp", fromColor=color(rgb, 34),
               toColor=color(rgb, 0), colorSpace=cim("CIMICCColorSpace", url="Default RGB"))
    bleed = cim("CIMGradientStroke", enable=True, width=1.7, colorRamp=ramp,
                gradientMethod="AcrossLine", gradientType="Continuous",
                gradientSize=100.0, gradientSizeUnits="Relative", capStyle="Round", joinStyle="Round")
    # First symbol layer is drawn above subsequent layers. Keep wet ink ABOVE tint.
    # Ink and paper are independent images; retain the approved PNG's real alpha.
    return cim("CIMPolygonSymbol", symbolLayers=[
        stroke(rgb, 0.16, 24), bleed, picture(wash_path, texture_size, 100),
        fill(rgb, 72), picture(paper_path, texture_size * .64, 100)])


def line_symbol(role, palette):
    p = get_palette(palette)
    if role == "roads_main":
        layers = [stroke((255, 255, 255), 1.0, 100), stroke(p.road, 1.85, 74)]
    elif role == "roads_other":
        layers = [stroke((255, 255, 255), 0.55, 95), stroke(p.road, 1.0, 42)]
    elif role == "buffer":
        layers = [stroke(p.accent, 0.9, 85, (7, 4))]
    else:
        layers = [stroke(p.ink, 0.65, 65, (4, 3))]
    return cim("CIMLineSymbol", symbolLayers=layers)


def point_symbol(role, palette):
    p = get_palette(palette)
    if role == "site":
        ring = [(-1,-4),(1,-4),(1,-1),(4,-1),(4,1),(1,1),(1,4),(-1,4),(-1,1),(-4,1),(-4,-1),(-1,-1),(-1,-4)]
        layers = [stroke((255,255,255), 0.45), fill(p.accent)]
        size = 13
    else:
        ring = [(3*math.cos(t*math.pi/24),3*math.sin(t*math.pi/24)) for t in range(49)]
        layers = [stroke(p.accent, 0.5, 75), fill(p.road, 78)]
        size = 4.5
    graphic = cim("CIMMarkerGraphic", geometry={"rings": [ring]},
                  symbol=cim("CIMPolygonSymbol", symbolLayers=layers))
    marker = cim("CIMVectorMarker", enable=True, size=size,
                 frame={"xmin": -4, "ymin": -4, "xmax": 4, "ymax": 4},
                 markerGraphics=[graphic], respectFrame=True, scaleSymbolsProportionally=True)
    return cim("CIMPointSymbol", symbolLayers=[marker])


def validate_layer(layer, role, replace_renderer=False):
    if role not in ROLES:
        raise ValueError(f"Unknown role {role!r}; choose {', '.join(ROLES)}")
    if not layer.isFeatureLayer:
        raise ValueError(f"{layer.name}: expected a feature layer")
    shape = arcpy_module().Describe(layer).shapeType
    if shape != ROLES[role]:
        raise ValueError(f"{layer.name}: {role} requires {ROLES[role]}, found {shape}")
    if layer.symbology.renderer.type != "SimpleRenderer" and not replace_renderer:
        raise ValueError(f"{layer.name}: categorized/graduated renderer; set replace_renderer=True only if intentional")


def apply_style(layer, role, palette="watercolor", texture_size=112,
                wash_path=None, paper_path=None, replace_renderer=False):
    """Style one layer; retains data, filters and labels. Replaces a single symbol."""
    p = get_palette(palette)
    if not isinstance(texture_size, (int, float)) or not math.isfinite(texture_size) or texture_size <= 0:
        raise ValueError("texture_size must be a positive finite number of points")
    validate_layer(layer, role, replace_renderer)
    shape = ROLES[role]
    if shape == "Polygon":
        symbol = polygon_symbol(role, p, texture_size, wash_path, paper_path)
    elif shape == "Polyline":
        symbol = line_symbol(role, p)
    else:
        symbol = point_symbol(role, p)
    definition = layer.getDefinition("V3")
    reference = cim("CIMSymbolReference", symbol=symbol)
    if layer.symbology.renderer.type == "SimpleRenderer":
        definition.renderer.symbol = reference
    else:
        definition.renderer = cim("CIMSimpleRenderer", symbol=reference)
    layer.setDefinition(definition)
    return layer
