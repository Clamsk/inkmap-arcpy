"""Package verified 0.4.0 resources and social images using an explicit allowlist."""
import hashlib,json,os,shutil,zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(os.path.abspath(__file__)).parents[1]
WORK=ROOT/'deliverables/release-0.4.0'
RELEASE=ROOT/'releases/0.4.0'

def archive(path,files,base):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            if p.is_file() and p.suffix not in {'.pyc'} and '__pycache__' not in p.parts:
                z.write(p,p.relative_to(base).as_posix())
    assert path.stat().st_size<100_000_000,path

def main():
    RELEASE.mkdir(parents=True,exist_ok=True)
    for name in ('inkmap_arcpy-0.4.0-py3-none-any.whl','arcpy-watercolor-map.zip','inkmap-source.zip'):
        shutil.copyfile(ROOT/'dist'/name,RELEASE/name)
    material=ROOT/'materials/selected-wet-ink'
    material_files=[p for p in material.iterdir() if p.is_file()]
    with zipfile.ZipFile(RELEASE/'inkmap-materials.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(material_files):z.write(p,p.name)
        z.write(ROOT/'scripts/extract_selected_materials.py','extract_selected_materials.py')
        z.write(ROOT/'docs/ink-materials.md','处理思路与教程.md')
    resources=WORK/'resources'
    for name in ('inkmap_arcpy-0.4.0-py3-none-any.whl','arcpy-watercolor-map.zip','inkmap-source.zip','inkmap-materials.zip'):
        shutil.copyfile(RELEASE/name,resources/name)
    shutil.copyfile(ROOT/'examples/two_cities/import_sample_data.py',resources/'import_sample_data.py')
    shutil.copyfile(ROOT/'LICENSE',resources/'LICENSE-code-MIT.txt')
    (resources/'README.md').write_text('''# InkMap 0.4.0 · 三城数据与 AI Skill

包含福州15层、上海13层、洛杉矶14层 GeoJSON、元数据、导入脚本、wheel、独立Skill、源码和墨纹素材包。旧支路数据依据原始OSM highway标签拆为支路与步道，合计数量保留。历史要素是OSM文化/历史建筑，不推测片区边界；社区/街区点仅用于名称标注。数量指查询范围，部分要素在图框之外。

在已授权的 ArcGIS Pro 3.x Python 中运行：
```powershell
python -m pip install --upgrade --no-deps ./inkmap_arcpy-0.4.0-py3-none-any.whl
python -m inkmap_arcpy doctor
python import_sample_data.py --city fuzhou --output ./work-fuzhou
python -m inkmap_arcpy atlas ./work-fuzhou/job.json --dry-run
python -m inkmap_arcpy atlas ./work-fuzhou/job.json
```
city 可改 shanghai / losangeles，同时使用新的输出目录。输入为WGS84；任务使用当地UTM米制投影。输出APRX及其GDB需一起移交。

解压Skill ZIP，把整个arcpy-watercolor-map文件夹放入Agent支持的skills目录（Codex示例 ~/.codex/skills/），重启或重新加载Agent后调用。Skill含对应wheel与配置参考，运行仍需ArcPy。用户直接复用PNG，不运行仿真。

导入脚本生成通用A4版式配置，定位圈为空。真实宏观边界按案例说明另行获取、确认许可并绑定；不根据截图补画。上海/洛杉矶城市装帧属于源码示例的CIM扩展，不由通用配置自动推断。

代码、Skill与生成材质为MIT。地理数据为OpenStreetMap派生数据库，按ODbL1.0分享，© OpenStreetMap contributors；来源 https://www.openstreetmap.org/copyright ，许可 https://opendatacommons.org/licenses/odbl/1-0/ 。获取日期2026-10-08；完整范围和处理数量见每城metadata、summary和source_audit。字体、DataV边界缓存、公园名录和私人参考截图不分发。
''',encoding='utf-8')
    checks={p.relative_to(resources).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in resources.rglob('*') if p.is_file() and p.name!='checksums.json'}
    (resources/'checksums.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    archive(RELEASE/'inkmap-toolkit-three-cities.zip',resources.rglob('*'),resources)
    post=WORK/'post';post.mkdir(exist_ok=True)
    copy=(ROOT/'docs/xiaohongshu-0.4.0.md').read_text('utf-8')
    title=copy.split('## 标题\n\n')[1].split('\n\n')[0]
    body=copy.split('## 正文（可直接复制）\n\n')[1].split('\n\n## 图片顺序')[0]
    (post/'标题.txt').write_text(title,encoding='utf-8-sig')
    (post/'正文与话题.txt').write_text(body,encoding='utf-8-sig')
    (post/'发布文案.md').write_text(copy,encoding='utf-8')
    images=list((post/'发布图片').glob('*.png'));assert len(images)==10,len(images)
    image_checks={}
    for p in images:
        with Image.open(p) as im:assert im.size==(1984,2646),(p.name,im.size)
        image_checks[p.name]={'pixels':[1984,2646],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    (post/'图片校验清单.json').write_text(json.dumps(image_checks,ensure_ascii=False,indent=2),encoding='utf-8')
    archive(RELEASE/'xiaohongshu-post.zip',images+[post/p for p in ('标题.txt','正文与话题.txt','发布文案.md','图片校验清单.json')],post)
    manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in RELEASE.iterdir() if p.is_file() and p.name!='checksums.json'}
    (RELEASE/'checksums.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    shutil.copyfile(RELEASE/'xiaohongshu-post.zip',WORK/'小红书发布包_墨纹素材与AI制图.zip')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
