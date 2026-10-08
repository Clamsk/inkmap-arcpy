"""Build wheel and self-contained skill/source archives without contacting a package index."""
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
import setuptools.build_meta

root = Path(os.path.abspath(__file__)).parent.parent
os.chdir(root)
dist = root / "dist"
dist.mkdir(exist_ok=True)
# Isolate the wheel build so stale 0.1 private assets cannot leak through build/lib.
(root/".temp").mkdir(exist_ok=True)
stage = Path(tempfile.mkdtemp(prefix="release-stage-",dir=root/".temp"))
for name in ("README.md","LICENSE","pyproject.toml"):
    shutil.copyfile(root/name,stage/name)
source = root / "src/inkmap_arcpy"
for file in source.rglob("*"):
    if file.is_file() and "__pycache__" not in file.parts and file.name not in {"wash.png","paper.jpeg"}:
        target=stage/"src/inkmap_arcpy"/file.relative_to(source)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(file,target)
os.chdir(stage)
wheel_name = setuptools.build_meta.build_wheel(str(dist))
os.chdir(root)
skill = root / "skills/arcpy-watercolor-map"
(skill / "assets").mkdir(exist_ok=True)
shutil.copyfile(dist / wheel_name, skill / "assets" / wheel_name)


def archive(path, files, base):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
        for file in sorted(set(files)):
            if (file.is_file() and "__pycache__" not in file.parts and file.suffix != ".pyc" and
                file.name not in {"wash.png","paper.jpeg"} and "0.1.0" not in file.name):
                output.write(file, file.relative_to(base).as_posix())


archive(dist / "arcpy-watercolor-map.zip", skill.rglob("*"), skill.parent)
files = [root / name for name in ("README.md", "LICENSE", "pyproject.toml", ".gitignore")]
for folder in ("src/inkmap_arcpy", "skills/arcpy-watercolor-map", "tests", "scripts","docs"):
    files.extend((root / folder).rglob("*"))
files.extend([root / "examples/current_project.py", root / "examples/style-job.json",root / "examples/atlas-job.json"])
files.extend(root/"examples/fuzhou"/name for name in ("download_osm.py","download_locators.py","download_parks.py",
              "prepare_data.py","build_map.py","build_atlas.py","validate_output.py"))
files.append(root/"examples/fuzhou/README.md")
archive(dist / "inkmap-source.zip", files, root)
manifest = {p.name: {"bytes":p.stat().st_size, "sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in (dist/wheel_name,dist/"arcpy-watercolor-map.zip",dist/"inkmap-source.zip")}
(dist / "checksums.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
