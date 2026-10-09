# InkMap ArcPy · 水墨水彩区位图

ArcGIS Pro 的 Python 制图包与 AI Agent skill。使用原生 CIM 叠层符号、真实要素数据和可编辑布局，复用蓝绿水彩、纸底、宋体标题、楷体地名与 Garamond 数字的风格。Agent 指使用 ArcPy 的 AI Agent。

![福州鼓楼示例](docs/images/gulou-full.png)

**0.4.0** 更新道路、建筑与地标的统一墨色表达，轨道站点采用4点空心灰青圈，步道使用细实线。沿用0.3.0选定的柔和湿墨底稿与独立纸纹，保留大块浓淡过渡和轻微纸感。透明白墨图片、半透明底色与纸纹分层保存；制图直接复用 PNG，用户无需运行湿媒体引擎或流体仿真。

`atlas`：配置图层、取景范围与定位边界，输出完整布局、地图框版和纯地图。定位文字放在圆形下部内部；中心坐标只用于取景。框内三列图例底板38%透明，比例尺底板40%透明。虚线经纬网、真北指针和米制比例尺关联真实地图框；墨纹默认112点、轻淡外缘。

[0.4.0 更新说明](docs/release-0.4.0.md) · [墨纹处理教程](docs/ink-materials.md) · [独立墨纹素材 ZIP](releases/0.4.0/inkmap-materials.zip) · [小红书图文](docs/xiaohongshu-0.4.0.md)

## 安装

下载：[Python wheel](releases/0.4.0/inkmap_arcpy-0.4.0-py3-none-any.whl) · [独立 Agent skill ZIP](releases/0.4.0/arcpy-watercolor-map.zip) · [源码 ZIP](releases/0.4.0/inkmap-source.zip) · [SHA256 清单](releases/0.4.0/checksums.json)。

[三城数据与复用资源包](releases/0.4.0/inkmap-toolkit-three-cities.zip) 提供福州鼓楼、上海外滩与洛杉矶回声湖共42个GeoJSON图层、导入脚本、安装包和使用说明。地理数据采用ODbL，与MIT程序许可分开；社区与街区名称点用于标注，不代表完整行政边界。解压后在Pro Python中运行 `python import_sample_data.py --city shanghai --output ./work-shanghai`，再用 `python -m inkmap_arcpy atlas ./work-shanghai/job.json --dry-run` 检查。

需要 Windows、已授权的 ArcGIS Pro 3.x 及其 Python 环境。已在 Pro **3.0 Advanced** 实际运行；其他小版本需要复测。包无额外运行依赖，ArcPy 由 Pro 提供。

```powershell
# 在 ArcGIS Pro Python Command Prompt 或其克隆环境中运行
python -m pip install --no-deps .\skills\arcpy-watercolor-map\assets\inkmap_arcpy-0.4.0-py3-none-any.whl
python -m inkmap_arcpy doctor
```

源码可设置 `PYTHONPATH` 为本项目的 `src` 目录运行。普通 Python 可读配置，不能执行 ArcPy 制图。

## 自动生成完整地图

先查确切地图名与图层 `longName`，再修改 [examples/atlas-job.json](examples/atlas-job.json)。相对路径以 JSON 所在目录为基准。

```powershell
python -m inkmap_arcpy inspect 'D:\GIS\input.aprx'
python -m inkmap_arcpy atlas .\examples\atlas-job.json --dry-run
python -m inkmap_arcpy atlas .\examples\atlas-job.json
```

`layers` 按配置顺序从底到顶绘制；每项可写角色字符串或带 `label_field` 的描述。输入项目和原数据保持原样，筛选后的要素复制进新 GDB，分类渲染有意统一为本主题。输出目录必须不存在。已绑定的图例最多十五项，定位圈最多三个。默认 A4 竖版，可调配色、比例、网格间距与底板透明度；不支持任意页面尺寸。已有分类专题图仅需换样式时，使用下面的 `style` 接口。

```python
from inkmap_arcpy import compose_atlas, load_atlas_config
report = compose_atlas(load_atlas_config('atlas-job.json'))
```

| 输出 | 内容 |
|---|---|
| `atlas.aprx` / `atlas.gdb` | 可编辑项目、主图和定位地图、两套布局及本地要素 |
| `atlas_full.png` / `.pdf` | 标题、主图、图例、定位圈及页脚 |
| `atlas_frame.png` / `.pdf` | 去掉页外标题与页脚，保留地图框、网格标注、图例和定位圈 |
| `atlas_map_only.png` / `.pgw` | 只有地理内容，带世界文件，不含布局图例、定位圈或经纬网 |
| `atlas.pagx` / `atlas_report.json` | 布局模板与数量、连接、比例尺检查报告 |

PNG 默认 240 dpi；PDF 以 300 dpi 图像方式输出，编辑请使用 APRX。GDB 应随项目移动。定位圈接收带代码字段的真实 Polygon/MultiPolygon GeoJSON，不能从截图推测边界。主题要求适合当地、以米为单位的投影。字体为华文宋体、华文楷体与 Garamond，缺字体时需安装合法字体或在布局中替换。

## 直接换图层样式

```python
import arcpy
from inkmap_arcpy import apply_style
p = arcpy.mp.ArcGISProject('CURRENT')  # 仅 Pro 内部 Python 窗口 / Notebook
m = next(m for m in p.listMaps() if m.name == 'Map')
water = next(l for l in m.listLayers() if l.longName == 'Water')
apply_style(water, 'water', palette='watercolor', texture_size=112)
p.saveACopy(r'D:\GIS\watercolor.aprx')
```

`apply_style` 保留定义查询、标签与数据源；分类或分级渲染默认拒绝，有意替换时传 `replace_renderer=True`。在 CURRENT 中操作会立即改变内存图层。既有项目批处理运行 `python -m inkmap_arcpy style examples/style-job.json --dry-run`，再去掉 `--dry-run` 保存副本；该接口保留已有布局。

| 角色 | 几何 | 样式 |
|---|---|---|
| water / green | 面 | 水彩水面 / 绿地 |
| buildings / residential / paper | 面 | 薄墨建筑 / 极淡居住用地 / 纸纹底面 |
| plaza / heritage | 面 | 淡赭石广场 / 灰褐历史建筑洗染 |
| roads_main / roads_other / walk | 线 | 纸白主路配灰青外沿 / 淡暖灰支路 / 细实线步道 |
| water_line | 线 | 浅青河沟 |
| boundary / buffer | 线 | 边界虚线 / 距离圈虚线 |
| station / site / community / place_label | 点 | 空心站点 / 暗朱砂地标 / 社区墨圈 / 仅地名标注 |

水体与绿地使用淡描边、渐变外缘、纯白 RGB 与变化 alpha 的湿墨纹理、半透明底色及独立纸纹五层符号，图片以 base64 嵌入。墨纹不主动追加咖啡环或细密颗粒；纸纹尺度为墨纹的0.64倍。尺寸单位是点。`palette='ink'` 切换灰墨配色；`wash_path` / `paper_path` 可指定自有方形无缝纹理。`distance_rings` 返回投影坐标系中的米制欧氏距离圈；不计算路网可达范围。

## 福州鼓楼案例

[复现步骤与数据说明](examples/fuzhou/README.md)；[地图框预览](docs/images/gulou-frame.png)。道路、公园、建筑与街道信息来自 OpenStreetMap，社区仅是名称点，居住区不代表正式社区边界。2026 年园林名录只用于核对公园名称。定位圈使用 DataV GeoAtlas 发布的 2021 年边界，仅作宏观定位与学习示例。

街区数据署名与许可见 [OpenStreetMap / ODbL](https://www.openstreetmap.org/copyright)；定位边界来源与使用说明见 [DataV GeoAtlas](https://datav.aliyun.com/portal/school/atlas/atlas_aigc)。仓库不包含这些源数据缓存，示例图保留来源说明。地图不是官方测绘成果。

## 上海与洛杉矶案例

[真实数据、城市装帧与复现流程](examples/two_cities/README.md)。包默认 A4；社交页面和上海几何、洛杉矶棕榈装帧在案例脚本中以原生 CIM 扩展。

## AI Agent skill

把整个 [skills/arcpy-watercolor-map](skills/arcpy-watercolor-map) 文件夹复制到 Agent 的 skills 目录，例如 Codex 的 `~/.codex/skills/`。内附 0.4.0 wheel 与配置、风格和检查流程，可独立使用。

> 使用 $arcpy-watercolor-map，按水墨泼染风格制作我的 ArcGIS Pro 区位图。水墨和纸纹独立叠放，定位说明放在圈内下部，导出完整图与地图框版。

## 验证与发布

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
# Pro Python：检查原生关联、定位文字位置、重载连接与导出
python tests/pro_atlas_check.py 'D:\GIS\atlas-output'
# 开发环境需 setuptools + wheel；默认使用已确认的 PNG 素材
python scripts/build_release.py
```

构建生成 0.4.0 wheel、独立 skill ZIP、源代码 ZIP 与 SHA256 清单。程序与所选预生成水墨、纸纹素材采用 MIT；实际尺寸为512×512，未冒称原生高清或完全无缝。源码保留沉积场和纸面高度，可用 `scripts/extract_selected_materials.py` 复现素材提取；此开发步骤不是制图依赖。来源、参数及第三方署名见 [素材说明](src/inkmap_arcpy/assets/NOTICE.md)。参考文档里的旧纹理、旧安装包与带旧纹理的私人示例不进入公开发布。外部 GIS 数据及自定义素材的许可独立于代码。

技术参考：[Esri Python CIM access](https://doc.esri.com/en/arcgis-pro/latest/arcpy/mapping/python-cim-access.html)、[CIM Symbols](https://github.com/Esri/cim-spec/blob/main/docs/v3/CIMSymbols.md)。不支持 ArcMap、三维场景、云端 ArcGIS API for Python 或 AgentPy 仿真库。
