# 完整典雅版式（0.3.0）

Pro Python 中安装附带 wheel，运行 `doctor`、`inspect`。所有文件相对 JSON 所在目录解析。

```json
{
  "project": "input.aprx",
  "map": "Map",
  "output_folder": "atlas-new",
  "layers": {
    "Buildings": "buildings",
    "Parks": {"role": "green", "label_field": "name"},
    "Water": "water",
    "Roads": {"role": "roads_main", "label_field": "name"}
  },
  "center": [119.294, 26.086],
  "projection": 32650,
  "scale": 21000,
  "title": "榕城 · 鼓楼",
  "subtitle": "福州鼓楼区水彩区位图",
  "english_title": "G U L O U   /   F U Z H O U",
  "source_note": "填入真实数据署名与日期",
  "grid_seconds": 30,
  "legend_transparency": 34,
  "scale_transparency": 40,
  "legend": [{"layer": "Water", "label": "河湖水面"}],
  "locators": [
    {"geojson": "province-boundaries.json", "caption": "全国 · 福建", "highlight": "350000", "projection": 102012, "grid_degrees": 10}
  ]
}
```

```powershell
python -m inkmap_arcpy atlas job.json --dry-run
python -m inkmap_arcpy atlas job.json
```

绑定列表按底到顶绘制。角色几何检查、唯一名、有效坐标系、标签字段、定位代码与输出目录检查通过后才写数据。输出目录不能已存在，包括失败残留目录；修复后选择新目录。

可选：`palette`（watercolor / ink），`dpi`（默认240），`texture_size`（默认112点），`caption`（标题下小注）。描述项可设 `fill_opacity`、`outline_opacity`（0..100为不透明度）、`label_font`、`label_size`、`label_color`（RGB）、`label_priority`。默认不提供纸层时自动添加纸底。`legend_transparency` / `scale_transparency` 为透明度，越高越透明。图例最多十项。

定位 GeoJSON 需 FeatureCollection、真实 Polygon/MultiPolygon、唯一高亮代码。字段默认 `adcode` / `name`，可改 `code_field` / `name_field`；坐标按 WGS84 GeoJSON 读取。默认定位投影为102012。最多三个定位圈；福建/福州案例使用32650，省网格1度、市0.5度。说明文字固定在圆心下方1.07厘米处，圆内下部；不存在圈外副标题。

主图要求当地米制投影、无旋转。主题固定 A4、主框19×24厘米，适合街区尺度；较大范围需相应调网格，边缘标注密度仍须视觉检查。比例尺从可读的米制距离中选择并关联主框；指北针为真北。模板默认从 Pro 安装目录读取，可显式指定 `project_template` / `layout_template`；布局模板需保留默认的 Map Frame、North Arrow、Scale bar / Scale Line 1 元素。

实现通过布局级 CIM，禁用网格默认 fromTick/toTick 防止 Pro 3.0 的长黑线；不能深拷贝带原生 Point 的 CIM，需重新读取定义。国家定位使用适合全幅的投影与所有边界顶点计算包围半径；不用只按矩形宽高匹配圆框。

导出：`atlas_full`完整页，`atlas_frame`去页外标题与来源但保留框内署名及布局要素，`atlas_map_only`只有地理内容与世界文件；PNG/PDF前两套，最后一套PNG。PDF按300dpi图像输出，原生编辑使用APRX。交付APRX/GDB及报告。

验收重载 APRX 无坏连接；原始要素数量等于复制数量；两套布局各有主框和定位圈；圈内说明在下部；没有自动中心标记；图例实际符号与图层一致；网格/比例尺/真北对应主框；裁切只去页面外围。宏观定位数据、精确街区数据及社区名称点的语义分开说明。
