# 运行工作流

## 检查与现有项目制图

```powershell
python -m inkmap_arcpy doctor
python -m inkmap_arcpy inspect 'D:\GIS\input.aprx'
python -m inkmap_arcpy style 'D:\GIS\job.json' --dry-run
python -m inkmap_arcpy style 'D:\GIS\job.json'
```

`python` 必须是 Pro 的 Python。路径可含空格和中文，应正确引用。示例 JSON：

```json
{
  "project": "input.aprx",
  "map": "Map",
  "palette": "watercolor",
  "texture_size": 72,
  "layers": {"Water": "water", "Green Space": "green", "Roads": "roads_main"},
  "output_project": "output/watercolor.aprx",
  "layout": "Layout",
  "export": {"path": "output/map.png", "dpi": 300}
}
```

相对文件路径基于 JSON 所在目录。布局和 export 可同时省略，只保存项目副本。组内图层用完整 `longName`，如 `Basemap\\Water`。输出不覆盖现有文件；重复运行改用新路径。`replace_renderer: true` 将指定图层的分类/分级渲染替换为单符号，只有用户确实希望取消分类时才使用。

包不设置研究范围、不创建定位插图、不获取在线底图、不生成真实业务标签、不调整已有图层顺序。Agent 应根据实际 GIS 数据和用户要求完成这些操作。不要把 demo 项目的合成几何当成真实数据。

## 单层样式

```python
import arcpy
from inkmap_arcpy import apply_style
p = arcpy.mp.ArcGISProject('CURRENT')
maps = [m for m in p.listMaps() if m.name == 'Map']
assert len(maps) == 1
layers = [l for l in maps[0].listLayers() if l.longName == 'Water']
assert len(layers) == 1
apply_style(layers[0], 'water', 'watercolor')
layers[0].saveACopy(r'D:\GIS\output\water.lyrx')
p.saveACopy(r'D:\GIS\output\watercolor.aprx')
```

`apply_style` 修改内存中的图层；`CURRENT` 会立即显示在 Pro 中。项目副本只复制项目结构，不复制 GDB、SHP 等数据源。需要交付给另一台机器时由 Agent 打包数据并检查断链。

## 合成演示与距离圈

```powershell
python -m inkmap_arcpy demo 'D:\GIS\demo-new' --palette watercolor
```

demo 依赖 Pro 安装目录中的 Blank.aprx 和 A4 Portrait.pagx 模板；找不到模板时用现有项目工作流，不能宣称 demo 成功。

```python
from inkmap_arcpy.geometry import distance_rings
rings = distance_rings(point_geometry, (500, 1000, 1500))
# point_geometry 已转换为适用于当地的投影 CRS。
# 把返回的 Polyline 写入 Agent 自建要素类，再用 buffer 角色制图。
```

距离计算是当地投影平面距离，不代表交通可达性。方法使用 metresPerUnit 转换米，不要求投影单位恰好是米。方法拒绝经纬度/Web Mercator；其他投影的适用范围仍需由 Agent 根据数据地区判断。
