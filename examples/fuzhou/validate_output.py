"""Check the saved Fuzhou projects with the ArcGIS Pro Python runtime."""
import argparse
import json
import os
from pathlib import Path
import arcpy


def main(output):
    folder = Path(os.path.abspath(output))
    expected = json.loads((folder.parent / "data/summary.json").read_text(encoding="utf-8"))["layers"]
    checks = {}
    for key, count in expected.items():
        fc = str(folder / "fuzhou.gdb" / key)
        actual = int(arcpy.management.GetCount(fc)[0])
        assert actual == count, (key, actual, count)
        assert arcpy.Describe(fc).spatialReference.factoryCode == 32650, key
        checks[key] = actual
    projects = []
    for name in ("fuzhou_watercolor", "fuzhou_detail"):
        project = arcpy.mp.ArcGISProject(str(folder / (name + ".aprx")))
        broken = [layer.name for m in project.listMaps() for layer in m.listLayers() if layer.isBroken]
        assert not broken, broken
        assert project.listMaps()[0].spatialReference.factoryCode == 32650
        layout = project.listLayouts()[0]
        legend = layout.listElements("TEXT_ELEMENT", "Legend text*")
        assert len(legend) == 10, len(legend)
        for element in layout.listElements("TEXT_ELEMENT"):
            assert not getattr(element, "isOverflowing", False), element.name
        for suffix in (".png", ".pdf"):
            assert (folder / (name + suffix)).stat().st_size > 10000
        projects.append({"name": name, "broken_layers": broken, "legend_labels": len(legend),
                         "scale": layout.listElements("MAPFRAME_ELEMENT")[0].camera.scale})
        del project
    report = {"status": "passed", "feature_counts": checks, "projects": projects,
              "note": "Visual inspection of both PNGs additionally checks typography and map margins."}
    (folder / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    main(parser.parse_args().output)
