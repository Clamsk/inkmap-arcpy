import argparse
import json
import sys
from .workflow import inspect_project, load_config, style_project


def main(argv=None):
    parser = argparse.ArgumentParser(description="Native ArcGIS Pro watercolor / ink maps")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check ArcGIS Pro Python and license")
    inspect = sub.add_parser("inspect", help="List map names, layer longNames and layouts")
    inspect.add_argument("project")
    style = sub.add_parser("style", help="Apply a JSON job to a project copy")
    style.add_argument("config")
    style.add_argument("--dry-run", action="store_true")
    demo = sub.add_parser("demo", help="Create a synthetic demonstration project and map")
    demo.add_argument("output")
    demo.add_argument("--palette", choices=["watercolor", "ink"], default="watercolor")
    atlas = sub.add_parser("atlas", help="Compose elegant full/frame maps, grids and native locator circles")
    atlas.add_argument("config")
    atlas.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            from .symbols import arcpy_module
            a = arcpy_module()
            result = {"version": a.GetInstallInfo()["Version"], "license": a.ProductInfo(), "cim": "V3"}
        elif args.command == "inspect":
            result = inspect_project(args.project)
        elif args.command == "style":
            result = style_project(load_config(args.config), args.dry_run)
        elif args.command == "atlas":
            from .atlas import compose_atlas, load_atlas_config
            result = compose_atlas(load_atlas_config(args.config), args.dry_run)
        else:
            from .demo import create_demo
            result = create_demo(args.output, args.palette)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"inkmap: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
