"""Validate public 0.4.0 bundles, checksums, material channels and extraction."""
import hashlib,json,os,zipfile
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(os.path.abspath(__file__)).parents[1]
release=ROOT/'releases/0.4.0'
manifest=json.loads((release/'checksums.json').read_text('utf-8'))
for name,record in manifest.items():
    p=release/name
    assert p.stat().st_size==record['bytes']<100_000_000
    assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
    if p.suffix in {'.zip','.whl'}:
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            assert not any('0.1.0' in n or 'codex-clipboard' in n or n.endswith('.docx') for n in z.namelist())
with zipfile.ZipFile(release/'arcpy-watercolor-map.zip') as z:
    names=z.namelist()
    assert len([n for n in names if n.endswith('.whl')])==1
    assert 'arcpy-watercolor-map/references/materials.md' in names
    assert '0.4.0' in z.read('arcpy-watercolor-map/SKILL.md').decode('utf-8')
for a,b in [('white-ink.png','generated-wet-ink.png'),('paper.png','generated-white-paper.png')]:
    selected=ROOT/'materials/selected-wet-ink'/a
    asset=ROOT/'src/inkmap_arcpy/assets'/b
    assert selected.read_bytes()==asset.read_bytes()
    with Image.open(selected) as im:arr=np.asarray(im);assert im.size==(512,512)
    if a=='white-ink.png':assert np.all(arr[:,:,:3]==255) and arr[:,:,3].min()<arr[:,:,3].max()<255
    extracted=ROOT/'.temp/material-check-v040'/b
    with Image.open(extracted) as im:assert np.array_equal(arr,np.asarray(im))
with zipfile.ZipFile(release/'inkmap-toolkit-three-cities.zip') as z:
    layers=[n for n in z.namelist() if '/geojson/' in n and n.endswith('.geojson')]
    assert len(layers)==42
    assert not any(n.endswith(('.ttf','.otf')) or '.gdb/' in n or 'locators/' in n for n in z.namelist())
    counts={}
    for city in ('fuzhou','shanghai','losangeles'):
        summary=json.loads(z.read(f'data/{city}/summary.json'))
        for key,value in summary['layers'].items():
            assert len(json.loads(z.read(f'data/{city}/geojson/{key}.geojson'))['features'])==value
        counts[city]=len(summary['layers'])
with zipfile.ZipFile(release/'xiaohongshu-post.zip') as z:
    assert len([n for n in z.namelist() if n.endswith('.png')])==10
    title=z.read('标题.txt').decode('utf-8-sig')
    body=z.read('正文与话题.txt').decode('utf-8-sig')
    assert len(title)<=20,(len(title),title)
    assert len(body)<=1000,len(body)
print(json.dumps(dict(status='passed',archives=len(manifest),data_layers=counts,images=10,title_characters=len(title),body_characters=len(body),materials='unchanged and extraction pixel-identical'),ensure_ascii=False,indent=2))
