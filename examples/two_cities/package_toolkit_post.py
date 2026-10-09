"""Package a data/package/skill-first post and a separate reusable resource bundle."""
import hashlib,json,os,shutil,zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(os.path.abspath(__file__)).parents[2]
OUT=Path(os.environ.get('INKMAP_DELIVERY',str(ROOT/'deliverables/inkmap-toolkit-three-cities-2026-10-08')))
IMAGES=OUT/'发布图片';RES=OUT/'复用资源'
for d in (IMAGES,RES):d.mkdir(parents=True,exist_ok=True)
for city,name in [('shanghai','07_上海_外滩案例'),('losangeles','08_洛杉矶_回声湖案例')]:
    folder=ROOT/'examples/two_cities'/(os.environ.get('INKMAP_RENDER_PREFIX','render-')+city)
    shutil.copyfile(folder/(city+'_full.png'),IMAGES/(name+'.png'))
    shutil.copyfile(folder/(city+'_full.pdf'),OUT/'原图与PDF'/(name+'.pdf'))

release=ROOT/'releases/0.3.0'
for name in ['inkmap_arcpy-0.3.0-py3-none-any.whl','arcpy-watercolor-map.zip','inkmap-source.zip','checksums.json']:
    shutil.copyfile(release/name,RES/name)
shutil.copyfile(ROOT/'LICENSE',RES/'LICENSE-code-MIT.txt')
shutil.copyfile(ROOT/'examples/two_cities/import_sample_data.py',RES/'import_sample_data.py')
if (OUT/'资源导入检查.json').is_file():shutil.copyfile(OUT/'资源导入检查.json',RES/'资源导入检查.json')
entries={}
for city,source,epsg in [('fuzhou',ROOT/'examples/fuzhou/data',32650),
                         ('shanghai',ROOT/'examples/two_cities/data/shanghai',32651),
                         ('losangeles',ROOT/'examples/two_cities/data/losangeles',32611)]:
    dest=RES/'data'/city;geo=dest/'geojson';geo.mkdir(parents=True,exist_ok=True)
    summary=json.loads((source/'summary.json').read_text(encoding='utf-8'))
    counts={}
    for path in sorted((source/'geojson').glob('*.geojson')):
        value=json.loads(path.read_text(encoding='utf-8'))
        assert value['type']=='FeatureCollection'
        counts[path.stem]=len(value['features'])
        assert counts[path.stem]==summary['layers'][path.stem],path
        # Keep this database purely OSM-derived; official name comparison is separate.
        for f in value['features']:f['properties'].pop('official_match',None)
        (geo/path.name).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    assert counts==summary['layers'],city
    normalized=dict(city=city,layers=counts,projection=epsg,retrieval_date='2026-10-08',
                    source='OpenStreetMap',license='ODbL 1.0',
                    copyright='https://www.openstreetmap.org/copyright',
                    coordinate_system='WGS84 longitude/latitude, EPSG:4326',
                    semantics='Community/neighborhood names are point labels, not complete administrative boundaries.')
    (dest/'summary.json').write_text(json.dumps(normalized,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copyfile(source/'metadata.json',dest/'metadata.json')
    shutil.copyfile(source/'query.overpassql',dest/'query.overpassql') if (source/'query.overpassql').is_file() else None
    entries[city]=normalized

data_notice='''# 三城样例数据 · 来源与许可

© OpenStreetMap contributors。这里的归一化 GIS 数据是 OSM 的派生数据库，按 Open Database License 1.0（ODbL）提供。代码与原创纹理的 MIT 许可不适用于这些地理数据。

数据署名：https://www.openstreetmap.org/copyright
ODbL 1.0 全文：https://opendatacommons.org/licenses/odbl/1-0/
获取日期：2026-10-08。数据为各城市局部，不能代表全城或正式测绘成果；道路是路段记录，社区或街区名称点不是完整社区行政边界。共享派生数据库时保留署名并遵循 ODbL。

数据坐标为 WGS84 经度、纬度（EPSG:4326）。本地制图建议：福州 EPSG:32650，上海 EPSG:32651，洛杉矶 EPSG:32611。

常用字段：osm_type / osm_id 是源标识；name 是地物名称；label 是制图标签；category 是图层类别；area_m2 是投影后计算的面积。图层按制图用途分类，没有补画社区边界。获取范围、时间戳和数量见各城市 metadata.json、summary.json。

福州原来的官方公园名称核对字段没有纳入此份 OSM 数据包。DataV 的宏观定位边界及公园名录不随此资源包分发。定位圈示例保留原来源说明；需要定位圈时按各案例 README 的来源另行获取、确认使用条件并绑定。
'''
(RES/'数据来源与许可.md').write_text(data_notice,encoding='utf-8')
resource_readme='''# 水墨地图复用资源

## 包含什么

- inkmap-arcpy 0.3.0 wheel：原生 ArcPy 水彩符号、布局与导出。
- arcpy-watercolor-map.zip：独立 AI Agent Skill，内含对应 wheel、参考配置及验收流程。
- inkmap-source.zip：已发布 0.3.0 源码；仓库 https://github.com/Clamsk/inkmap-arcpy 。
- data：福州 11 层、上海 10 层、洛杉矶 10 层归一化 GeoJSON，附元数据；这些三城数据另在本资源包内提供。
- import_sample_data.py：在 Pro 中导入样例、创建 APRX/GDB 和相对路径的 job.json。
- city_examples：本次上海、洛杉矶装帧与复现脚本。这是包之外的示例扩展，包默认 atlas 布局仍为 A4。

## 先安装，再导入

需要 Windows、已授权的 ArcGIS Pro 3.x。已在本机 Pro 3.0 Advanced 实测。使用 Pro 的 Python Command Prompt 或克隆环境；普通 Python 无法执行 ArcPy 制图。

```powershell
python -m pip install --no-deps .\\inkmap_arcpy-0.3.0-py3-none-any.whl
python -m inkmap_arcpy doctor
python import_sample_data.py --city fuzhou --output .\\work-fuzhou
python -m inkmap_arcpy atlas .\\work-fuzhou\\job.json --dry-run
python -m inkmap_arcpy atlas .\\work-fuzhou\\job.json
```

`--city` 可改为 `shanghai` 或 `losangeles`，同时换一个新的 output 目录。可从任意工作目录执行此脚本，默认 data 在脚本同级。输出目录不能已经存在。导入的数据源保存在新 GDB，后续 atlas 再复制到独立输出 GDB。移交项目时一起带上 GDB。

简易导入配置包含主图、图例、经纬网、比例尺与真北，定位圈初始为空。要复现全国—省市定位圈，先按公开案例说明获取真实边界，再设置 job.json 的 locators；不能根据截图补画边界。导入脚本保留三城所有 GeoJSON，主图配置选择适合通用角色的图层；福州 subdistricts 范围另在数据包内，社区点按名称点解释。

## 给 Agent 安装 Skill

解压 arcpy-watercolor-map.zip，将整个 arcpy-watercolor-map 文件夹复制到 Agent 的 skills 目录；Codex 例如 ~/.codex/skills/。内附 wheel，环境可用后按照 SKILL.md 执行。

示例指令：使用 $arcpy-watercolor-map，把我的道路、水体、公园和建筑做成水墨区位图。中心只用于取景，定位文字放在圈内下部，导出全图和地图框版，并检查保存项目的数据连接。

Skill 负责流程与验收；ArcPy 与 Python 包负责执行。换城市时检查真实数据、标签字段、当地投影、比例和布局。上海、洛杉矶的装帧是独立示例脚本中的原生 CIM 扩展，不能仅修改 atlas 配置就自动获得任意城市装饰。

需要运行城市装帧扩展时，先将 inkmap-source.zip 解压到一个新目录，把 city_examples 的内容复制进该目录 examples/two_cities，再按其中 README 执行。下载步骤可重新获取数据；要使用本资源包的缓存，把 data/shanghai 和 data/losangeles 复制到 examples/two_cities/data 的对应子目录，定位数据仍按下载脚本独立获取。脚本中的目录结构以源码工作区为基准。资源包入口 import_sample_data.py 则可直接在资源包目录中运行。

## 许可与来源

程序、Skill 和默认生成纹理为 MIT；三城 OSM 派生数据库为 ODbL，详见“数据来源与许可.md”。资源包采用明确文件清单，仅包含 0.3.0 发布文件及本次公开数据、脚本。字体由本机合法环境提供，不打包字体。
'''
(RES/'README.md').write_text(resource_readme,encoding='utf-8')
code=RES/'city_examples';code.mkdir(exist_ok=True)
for name in ['cities.py','download_data.py','download_la_tiles.py','prepare_data.py','build_maps.py','city_frames.py','post_cards.py','validate_maps.py','README.md']:
    shutil.copyfile(ROOT/'examples/two_cities'/name,code/name)

title='水墨地图包＋AI制图Skill'
body='''把之前的水墨区位图流程，整理成了可以复用的数据、Python 包和 AI 制图 Skill。🗺️

这次分享的重点，是拿到工具后怎样做自己的地图。

① 三城样例数据
福州鼓楼、上海外滩、洛杉矶回声湖，共 31 个 GeoJSON 图层文件。道路、水体、公园、建筑和地名点按角色整理，附来源、获取日期、范围与要素数量。也可以替换成自己的 GIS 数据。

② inkmap-arcpy Python 包
把独立泼墨图片、独立纸纹与颜色叠层符号、图框内图例、米制比例尺、真北指针、虚线经纬网和定位圈做成可复用流程。用配置绑定图层，输出完整图、地图框版、纯地图以及可编辑的 APRX＋GDB。

③ arcpy-watercolor-map AI Skill
让 Agent 按顺序确认环境与数据、选择投影、绑定样式、设计布局、导出并检查。Skill 管流程，ArcPy 执行制图；装帧可以再按城市气质调整。

图1—5介绍工具和使用流程；图6—8是福州、上海、洛杉矶的应用案例。

使用环境：Windows＋已授权的 ArcGIS Pro 3.x，本机 Pro 3.0 实测。
Python 包与 Skill 仓库：https://github.com/Clamsk/inkmap-arcpy
三城 GeoJSON、导入脚本与复用资源包也可在仓库 releases/0.3.0 下载。

代码和新生成纹理采用 MIT；样例地理数据 © OpenStreetMap contributors，遵循 ODbL。社区名称点是标注资料，不代表完整社区行政边界。

#GIS #ArcPy #ArcGISPro #AI制图 #AISkill #Python #水墨地图 #开源工具 #地图设计
'''
(OUT/'标题.txt').write_text(title,encoding='utf-8-sig')
(OUT/'正文与话题.txt').write_text(body,encoding='utf-8-sig')
(OUT/'发布文案.md').write_text('# 标题\n\n'+title+'\n\n# 正文与话题\n\n'+body,encoding='utf-8')
instructions='''# 发布顺序与附件

上传“发布图片”中的 8 张编号 PNG，按 01—08 排序。封面和前五张围绕数据包、Python 包及 AI Skill；三城地图作为应用案例。

| 顺序 | 内容 |
|---|---|
| 01 | 水墨地图工具包：数据、Python 包、AI Skill |
| 02 | 三城数据图层、来源、字段与地名点语义 |
| 03 | Python 包的样式、布局、检查与安装入口 |
| 04 | Skill 流程与给 Agent 的示例指令 |
| 05 | 资源包、导入、制图与导出流程 |
| 06 | 原来的福州鼓楼案例，重新导出为同系列 3:4 |
| 07 | 上海外滩案例 |
| 08 | 洛杉矶回声湖案例 |

“小红书发布包_水墨地图工具与三城案例.zip”仅装图片与可复制文案。“复用资源包_inkmap-arcpy_三城数据与AI-Skill.zip”另含安装包、Skill、源码、三城 GeoJSON 与使用说明，可作为资源附件。GitHub 的 releases/0.3.0 同时提供核心包、Skill 与三城复用资源包。

主图道路、公园、河湖、建筑与街区信息采用真实 OSM 数据。三城图复用0.3.0选定的柔和湿墨与独立纸纹，制图直接读取素材，无需运行流体仿真。图内保留 OSM 与定位边界署名。地图定位中心只用于取景；蓝色十字是实际城市地标。

三城完整页 PDF 与原来的福州 A4 图、地图框版另放“原图与PDF”。PNG 为 1984×2646，保持一致的 3:4 竖版页面比例。
'''
(OUT/'图片顺序与使用说明.md').write_text(instructions,encoding='utf-8')
for src,name in [(ROOT/'docs/images/gulou-full.png','福州_原A4完整图.png'),
                 (ROOT/'docs/images/gulou-frame.png','福州_原地图框.png')]:
    shutil.copyfile(src,OUT/'原图与PDF'/name)
manifest={}
for path in sorted(IMAGES.glob('*.png')):
    with Image.open(path) as im:
        assert im.size==(1984,2646),path.name
        size=list(im.size)
    manifest[path.name]=dict(pixels=size,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert len(manifest)==8,manifest.keys()
(OUT/'图片校验清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
resource_manifest={str(p.relative_to(RES)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RES.rglob('*')) if p.is_file() and p.name!='资源校验清单.json'}
(RES/'资源校验清单.json').write_text(json.dumps(resource_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT/'复用资源包_inkmap-arcpy_三城数据与AI-Skill.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(RES.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(RES).as_posix())
with zipfile.ZipFile(OUT/'小红书发布包_水墨地图工具与三城案例.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in list(IMAGES.glob('*.png'))+[OUT/n for n in ['标题.txt','正文与话题.txt','发布文案.md','图片顺序与使用说明.md','图片校验清单.json']]:
        z.write(p,p.relative_to(OUT).as_posix())
print(json.dumps(dict(images=len(manifest),geojson_files=sum(len(e['layers']) for e in entries.values()),
                     archives=[dict(name=p.name,bytes=p.stat().st_size) for p in OUT.glob('*.zip')]),ensure_ascii=False,indent=2))
