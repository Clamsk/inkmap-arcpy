import json
import math
import os
from pathlib import Path
from .palettes import get_palette
from .symbols import arcpy_module, apply_style, validate_layer


def unique(items, name, kind):
    matches = [item for item in items if getattr(item, "longName", item.name) == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one {kind} named {name!r}; found {len(matches)}. Use exact names / layer longName.")
    return matches[0]


def inspect_project(project):
    p = arcpy_module().mp.ArcGISProject(str(project))
    return {"maps": [{"name": m.name, "spatial_reference": m.spatialReference.name,
                      "layers": [{"name": l.longName, "feature": l.isFeatureLayer,
                                  "broken": l.isBroken} for l in m.listLayers()]} for m in p.listMaps()],
            "layouts": [l.name for l in p.listLayouts()]}


def style_project(config, dry_run=False):
    """Validate a JSON job, style only selected layers, save a new APRX and optional export."""
    if not isinstance(config, dict):
        raise TypeError("config must be a dictionary")
    allowed = {"project", "map", "layers", "output_project", "palette", "texture_size",
               "replace_renderer", "layout", "export", "wash_path", "paper_path"}
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"Unsupported job keys: {', '.join(sorted(unknown))}")
    p = arcpy_module().mp.ArcGISProject(str(config["project"]))
    m = unique(p.listMaps(), config["map"], "map")
    if m.mapType != "MAP":
        raise ValueError("Use a 2D map; 3D scenes are not supported")
    palette = get_palette(config.get("palette", "watercolor"))
    roles = config["layers"]
    if not roles or not isinstance(roles, dict):
        raise ValueError("layers must map exact layer longName to a role")
    texture_size = config.get("texture_size", 112)
    if not isinstance(texture_size, (float, int)) or not math.isfinite(texture_size) or texture_size <= 0:
        raise ValueError("texture_size must be positive and finite")
    replace = config.get("replace_renderer", False)
    if not isinstance(replace, bool):
        raise ValueError("replace_renderer must be true or false")
    from .symbols import image_url
    for key in ("wash_path", "paper_path"):
        if config.get(key):
            image_url(config[key])
    pairs = [(unique(m.listLayers(), name, "layer"), role) for name, role in roles.items()]
    for layer, role in pairs:
        if layer.isBroken:
            raise ValueError(f"Broken data source: {layer.longName}")
        validate_layer(layer, role, replace)
    output = Path(os.path.abspath(config["output_project"]))
    if output.suffix.lower() != ".aprx" or output.exists():
        raise ValueError(f"output_project must be a NEW .aprx path: {output}")
    export = config.get("export")
    layout = None
    if export:
        if not isinstance(export, dict) or set(export) - {"path", "dpi"}:
            raise ValueError("export must be a dictionary containing path and optional dpi")
        layout = unique(p.listLayouts(), config["layout"], "layout")
        target = Path(os.path.abspath(export["path"]))
        if target.suffix.lower() not in {".png", ".pdf"} or target.exists():
            raise ValueError(f"export path must be a NEW .png or .pdf: {target}")
        dpi = export.get("dpi", 300)
        if isinstance(dpi, bool) or not isinstance(dpi, int) or not 72 <= dpi <= 1200:
            raise ValueError("dpi must be an integer in 72..1200")
        if not any(f.map and f.map.name == m.name for f in layout.listElements("MAPFRAME_ELEMENT")):
            raise ValueError(f"Layout {layout.name} has no map frame referencing {m.name}")
    report = {"project": str(output), "map": m.name, "palette": palette.name,
              "layers": {l.longName: role for l, role in pairs},
              "export": str(target) if export else None, "dry_run": dry_run}
    if dry_run:
        return report
    for layer, role in pairs:
        apply_style(layer, role, palette, texture_size, config.get("wash_path"),
                    config.get("paper_path"), replace)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Export first: a rendering error cannot leave a seemingly successful APRX deliverable.
    if export:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix.lower() == ".png":
            layout.exportToPNG(str(target), resolution=dpi)
        else:
            layout.exportToPDF(str(target), resolution=dpi, image_quality="BEST")
    p.saveACopy(str(output))
    return report


def load_config(path):
    """Relative filesystem paths are relative to the JSON file, not the shell cwd."""
    path = Path(os.path.abspath(path))
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    for key in ("project", "output_project", "wash_path", "paper_path"):
        if key in config and config[key] != "CURRENT":
            config[key] = os.path.abspath(path.parent / config[key])
    if config.get("export"):
        config["export"]["path"] = os.path.abspath(path.parent / config["export"]["path"])
    return config
