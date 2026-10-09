"""Assemble original native exports, ready-to-copy Chinese copy, sources and checksums."""
import hashlib,json,os,shutil,zipfile
from pathlib import Path
from PIL import Image
from cities import CITIES

ROOT=Path(os.path.abspath(__file__)).parent
DELIVERY=ROOT.parent.parent/'deliverables/shanghai-losangeles-2026-10-08'
IMAGES=DELIVERY/'发布图片'; ORIGINAL=DELIVERY/'原图与PDF'
IMAGES.mkdir(parents=True,exist_ok=True); ORIGINAL.mkdir(parents=True,exist_ok=True)
for city,prefix in [('shanghai','02_上海_海派装帧'),('losangeles','04_洛杉矶_加州装帧')]:
    folder=ROOT/('render-'+city)
    shutil.copyfile(folder/(city+'_full.png'),IMAGES/(prefix+'.png'))
    for suffix in ('.png','.pdf'):
        shutil.copyfile(folder/(city+'_full'+suffix),ORIGINAL/(prefix+suffix))
        shutil.copyfile(folder/(city+'_frame'+suffix),ORIGINAL/(city+'_地图框'+suffix))
    for suffix in ('.png','.pgw'):
        shutil.copyfile(folder/(city+'_map_only'+suffix),ORIGINAL/(city+'_纯地图'+suffix))
for name in ('03_上海_江河细节','05_洛杉矶_湖光细节'):
    shutil.copyfile(IMAGES/(name+'.png'),ORIGINAL/(name+'.png'))

title='把上海和洛杉矶画成水彩地图'
body='''同一套 ArcPy 水彩样式，给两座城市做了不同的装帧。🗺️

上海选了外滩—苏州河口。黄浦江与苏州河的蓝色水彩，配上墨绿宋体、黄铜细线和扇形纹样，想保留一点海派装饰艺术的秩序感。

洛杉矶选了回声湖—市中心。底图沿用蓝绿水彩、淡灰建筑和浅色街网，图框换成日落橙、圆角和棕榈线描，画面也多了一点加州的温暖。

道路、水体、公园和建筑来自真实地理数据，使用 ArcGIS Pro + ArcPy 制图。图例、比例尺、真北指针、虚线经纬网和定位圈都保留在原生工程里，可以继续编辑。

制图流程也整理成了 Python 包和 AI Agent skill，换城市后可以复用。

图2、4是完整布局；图3、5看江河和湖光的细节；图6是配色、装帧与流程说明。

你更喜欢上海的海派几何，还是洛杉矶的加州日光？

数据：© OpenStreetMap contributors（ODbL），2026-10-08获取；上海定位参考 GeoAtlas 2021，美国定位参考 US Census 2024。两张均为城市局部的学习交流示例。

#水彩地图 #地图设计 #ArcGISPro #ArcPy #GIS制图 #城市地图 #上海外滩 #洛杉矶
'''
(DELIVERY/'标题.txt').write_text(title,encoding='utf-8-sig')
(DELIVERY/'正文与话题.txt').write_text(body,encoding='utf-8-sig')
(DELIVERY/'发布文案.md').write_text('# 标题\n\n'+title+'\n\n# 正文与话题\n\n'+body,encoding='utf-8')
instructions='''# 小红书发布顺序

上传“发布图片”文件夹中的六张PNG，按文件名前的数字排序。使用“标题.txt”和“正文与话题.txt”即可。

| 顺序 | 图片 | 内容 |
|---|---|---|
| 01 | 封面 | 双城水彩地图 |
| 02 | 上海全图 | 外滩—苏州河口，海派几何装帧 |
| 03 | 上海细节 | 外白渡桥附近，放大江河与街巷 |
| 04 | 洛杉矶全图 | 回声湖—市中心，加州日光装帧 |
| 05 | 洛杉矶细节 | Echo Park Lake周边，放大湖光与街区 |
| 06 | 风格说明 | 共享水彩底图表达、两种装帧和制图流程 |

六张图为同一3:4竖版布局的高分辨率导出。地图框版、纯地图和PDF放在“原图与PDF”，用于其他排版或印刷；发布时直接使用六张编号PNG。来源署名已放在图内。

深蓝十字表示真实城市地标，中心坐标仅用于取景。两座城市的道路与建筑由真实GIS要素绘制；扇形、棕榈、日落纹样属于装饰设计。

发布包包含图片与可复制文本，按上述顺序上传即可。
'''
(DELIVERY/'图片顺序与使用说明.md').write_text(instructions,encoding='utf-8')
sources='''# 数据与原生工程

## 主图数据

OpenStreetMap，经完整的有界Overpass查询取得。上海使用一次查询，洛杉矶使用四个完整小范围响应，按OSM类型和id去重；超时的残缺响应未用于制图。

署名与许可：https://www.openstreetmap.org/copyright
数据获取日期：2026-10-08。

| 城市 | 主图投影 | 主图比例 | 细节比例 |
|---|---|---|---|
| 上海 | WGS84 / UTM 51N，EPSG:32651 | 1:21,000 | 1:10,500 |
| 洛杉矶 | WGS84 / UTM 11N，EPSG:32611 | 1:23,000 | 1:10,000 |

以上均为原生相机比例；PNG屏幕显示尺寸会变化，图内比例尺保留真实地图框关联。地名点仅用于名称标注，不推断社区或片区边界。要素数量是下载边界内的数据记录，并非地图中可见地物数或完整普查数。

## 定位边界

上海：DataV GeoAtlas / Amap areas_v3，发布版本2021-05；供学习交流，仅用于全国—上海、上海—黄浦的宏观定位。主图覆盖黄浦、虹口与浦东的部分区域，不等于黄浦行政界。
来源：https://datav.aliyun.com/portal/school/atlas/atlas_aigc

洛杉矶：US Census Bureau 2024 Cartographic Boundary Files，美国州界（20m）与加州县界（5m）。美国本土圈显示相连48州及DC，文字明确标为“美国本土”；加州圈高亮洛杉矶县。源数据比例中的20m/5m表示1:20,000,000 / 1:5,000,000概化等级，不是20米/5米分辨率。
来源：https://www2.census.gov/geo/tiger/GENZ2024/shp/

## 城市参考与设计意图

外滩历史建筑与苏州河口景观参考上海市政府公开资料。上海装帧借用装饰艺术几何秩序，洛杉矶装帧借用加州日光和棕榈的视觉意象。它们是本次创作的装饰设计，不代表官方城市标识。
参考：https://english.shanghai.gov.cn/en-HeritageZones/20231208/f2ac293f546a4d32aba936f2e733a47c.html
Echo Park Lake名称参考洛杉矶市公园名录：https://www2.laparks.org/parks

## 原生制作

运行本机ArcGIS Pro3.0 Advanced，调用inkmap-arcpy0.3.0与arcpy-watercolor-map skill。地图符号、图框、城市装帧和社交排版均用ArcGIS原生CIM生成；默认水彩、纸纹为包内原创MIT纹理。

原生城市工程保存在项目examples/two_cities/render-shanghai及render-losangeles；*_city.aprx包含全图与地图框布局，*_post.aprx另含细节页。编辑或搬移时一同携带各目录atlas.gdb。复现代码在examples/two_cities。
'''
summaries={city:json.loads((ROOT/'data'/city/'summary.json').read_text(encoding='utf-8'))['layers'] for city in CITIES}
sources+='\n## 下载要素数量\n\n'+json.dumps(summaries,ensure_ascii=False,indent=2)+'\n'
(DELIVERY/'数据来源与制图说明.md').write_text(sources,encoding='utf-8')
if (ROOT/'validation.json').is_file(): shutil.copyfile(ROOT/'validation.json',DELIVERY/'原生工程检查.json')
manifest={}
images=sorted(IMAGES.glob('*.png'))
assert len(images)==6, [p.name for p in images]
for path in images:
    with Image.open(path) as image:
        assert abs(image.width/image.height-.75)<.002,path.name
        assert image.width>=1800
        size=[image.width,image.height]
    manifest[path.name]=dict(pixels=size,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
(DELIVERY/'图片校验清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
archive=DELIVERY/'小红书发布包_上海与洛杉矶.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
    files=images+[DELIVERY/name for name in ['标题.txt','正文与话题.txt','发布文案.md','图片顺序与使用说明.md','数据来源与制图说明.md','图片校验清单.json']]
    for path in files: output.write(path,path.relative_to(DELIVERY).as_posix())
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,images=manifest),ensure_ascii=False,indent=2))
