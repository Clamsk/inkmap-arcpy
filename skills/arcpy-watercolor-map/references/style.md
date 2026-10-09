# 样式参数与视觉判断

`watercolor` 对应参考图蓝绿水彩；`ink` 是柔和灰墨配色变体，保留相同水彩纹理，并非重新绘制国画山水。

| 角色 | 几何 | 作用 |
|---|---|---|
| water | Polygon | 蓝色水体，五层符号 |
| green | Polygon | 绿色绿地，五层符号 |
| buildings | Polygon | 薄墨灰填色23%，轮廓0.065pt/10% |
| paper | Polygon | 研究范围纸底，需要用户自己的范围面 |
| roads_main | Polyline | 纸白内线1.08pt/100%，灰青外沿1.85pt/78% |
| roads_other | Polyline | 淡暖灰支路0.44pt/44%，连续线 |
| walk | Polyline | 淡暖灰步道0.22pt/25%，连续线 |
| water_line | Polyline | 浅青河沟0.85pt/65% |
| residential | Polygon | 极淡暖灰填色5% |
| plaza / heritage | Polygon | 真实广场淡赭34% / 历史建筑灰褐36%，五层洗染 |
| community | Point | 小空心墨圈2.8pt |
| place_label | Point | 不可见点，保留地名标注 |
| buffer | Polyline | 蓝色虚线距离圈；先把缓冲面转为边界线 |
| boundary | Polyline | 灰色虚线边界 |
| station | Point | 空心灰青圈4pt，圈线0.40pt/88%，纸白中心 |
| site | Point | 暖墨圈6.5pt与暗朱砂中心 |

水体/绿地的 `CIMPolygonSymbol.symbolLayers` 从上至下：

1. `CIMSolidStroke`，0.16 pt，24% 不透明度。
2. `CIMGradientStroke`，1.7 pt，连续跨线渐变，颜色从 34% 不透明度到 0%。
3. `CIMPictureFill`，纯白 RGB、变化 alpha 的柔和湿墨纹理 generated-wet-ink.png，100% tint alpha。
4. `CIMSolidFill`，72% 不透明度，蓝或绿。
5. `CIMPictureFill`，独立纸纹 generated-white-paper.png，100% tint alpha；纸纹尺度为墨纹的0.64倍。

CIM RGBA 的第四项是 0–100 的不透明度；PNG alpha 是 0–255。它们不是同一个单位。所选透明白材质的 RGB 全为255，浓淡只编码在alpha中：浓墨对应较少白色覆盖。两张图均为512×512；透明墨纹在黑底观察，地图里由半透明颜色与独立纸纹托底。100%的CIM图像不透明度保留PNG自身的alpha变化，不表示该层每个像素都不透明。

默认审美重点是柔和湿墨铺染、浓淡相融与大块过渡。边界若隐若现，纸纹轻微；不能因想强调水墨而主动画闭合圈、加密颗粒或锐化。微调优先改变地图底色、层不透明度和铺排尺度。用户需要明确积墨、飞白等其他风格时再采用相应处理。替换素材先看单层、叠放色块与真实面要素，确认后批量更新。实际检查铺排接缝，不宣称未经验证的无缝效果；保持道路与地名可读。

`texture_size=72` 是每块墨纹72 pt的高度，在页面上约25.4 mm；`atlas` 默认112 pt，以保留较大的墨色过渡，纸纹约72 pt。112 pt在300 dpi约467像素，可利用512素材；提高导出dpi不增加原材质细节。纸底的图片不透明度为35%。`wash_path` 可替换方形透明PNG，`paper_path` 可替换方形纸纹PNG/JPEG。包把图片作为base64写入CIM，移动APRX/LYRX无需查找材质路径，GIS数据仍须搬移或打包。

素材由Washes湿媒体引擎的已保存沉积量和纸面高度分别提取，非实物扫描。源码materials/selected-wet-ink保存来源、参数、原始场和第三方署名；scripts/extract_selected_materials.py可复现提取。Agent制图使用预生成PNG，运行时不安装Node或任何仿真依赖。模型未按特定墨汁的实测黏度与表面张力标定。

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
