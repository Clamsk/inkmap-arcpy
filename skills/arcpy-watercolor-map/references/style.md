# 样式参数与视觉判断

`watercolor` 对应参考图蓝绿水彩；`ink` 是柔和灰墨配色变体，保留相同水彩纹理，并非重新绘制国画山水。

| 角色 | 几何 | 作用 |
|---|---|---|
| water | Polygon | 蓝色水体，五层符号 |
| green | Polygon | 绿色绿地，五层符号 |
| buildings | Polygon | 低对比度淡灰建筑 |
| paper | Polygon | 研究范围纸底，需要用户自己的范围面 |
| roads_main | Polyline | 白色道路内线与浅蓝外沿 |
| roads_other | Polyline | 更细、更淡道路 |
| buffer | Polyline | 蓝色虚线距离圈；先把缓冲面转为边界线 |
| boundary | Polyline | 灰色虚线边界 |
| station | Point | 小圆形站点 |
| site | Point | 深蓝或深墨十字场地标记 |

水体/绿地的 `CIMPolygonSymbol.symbolLayers` 从上至下：

1. `CIMSolidStroke`，0.22 pt，38% 不透明度。
2. `CIMGradientStroke`，2.0 pt，连续跨线渐变，颜色从 46% 不透明度到 0%。
3. `CIMPictureFill`，半透明白色水彩纹理，82% tint alpha。
4. `CIMSolidFill`，72% 不透明度，蓝或绿。
5. `CIMPictureFill`，纸张纹理，100% tint alpha。

CIM RGBA 的第四项是 0–100 的不透明度；PNG alpha 是 0–255。它们不是同一个单位。水彩纹理 RGB 全白，但 alpha 有变化，叠在颜色上才显示。

`texture_size=72` 是每块纹理 72 pt 的高度，在页面上约 25.4 mm；放大值会使水彩块更大，不改变地图几何。`wash_path` 可替换正方形无缝透明 PNG；`paper_path` 可替换正方形无缝纸纹 PNG/JPEG。包把纹理作为 base64 写入 CIM，移动 `.aprx`/`.lyrx` 无须再寻找纹理路径，但 GIS 数据源仍须一同搬移或打包。

自定义配色：

```python
from inkmap_arcpy import Palette, apply_style
p = Palette('custom', water=(90,145,165), green=(90,135,105),
            road=(155,175,185), building=(223,223,220),
            ink=(100,110,115), accent=(35,75,105))
apply_style(water_layer, 'water', p, texture_size=90)
```

若需修改描边/晕染宽度，读包内 `symbols.py` 并通过 getDefinition/setDefinition 更新指定 CIM 属性；当前公共 API 没有暴露所有样式参数。不要把未支持的参数写进 JSON，误以为已生效。

技术依据：[Esri Python CIM access](https://doc.esri.com/en/arcgis-pro/latest/arcpy/mapping/python-cim-access.html)、[Esri CIM v3 symbols](https://github.com/Esri/cim-spec/blob/main/docs/v3/CIMSymbols.md)。
