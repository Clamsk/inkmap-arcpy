# 透明白墨纹与独立纸纹：从湿媒体底稿到地图材质

这套素材保留了选定底稿的大块浓淡交融，适合清淡青绿区位图。0.4.0 沿用 0.3.0 的两张 PNG，像素和文件摘要均不变；变化集中在道路、建筑与点符号。素材不是参考截图截取，也不是实物扫描。

## 下载与文件

[独立素材 ZIP](../releases/0.4.0/inkmap-materials.zip)；也可直接下载 [透明白墨 PNG](../materials/selected-wet-ink/white-ink.png) 和 [纸纹 PNG](../materials/selected-wet-ink/paper.png)。透明白图片在白底上难以看见，需放在黑底或有色底上观察。

| 文件 | 内容 |
|---|---|
| white-ink.png | 512×512 RGBA；RGB 恒为白色，浓淡只在 alpha 中 |
| paper.png | 512×512 RGB；独立生成纸纹 |
| dry-stage-1/2/3.png | 每遍干燥后的原始预览，用于比较层次 |
| selected-fields.npz | 总沉积场 deposit 与纸面高度 paper_height |
| dry-glazes.npz | 三次独立干燥沉积 layer_1..3、累积 stage_1..3 |
| provenance.json / checksums.json | 实际原始参数、引擎摘要、落墨位置与 PNG SHA256 |
| WASHES-LICENSE / LICENSE | 第三方引擎与本项目 MIT 许可 |

## 底稿制作思路

湿媒体底稿由 [Washes 引擎](https://github.com/castavridis/washes-js) 生成。采用三遍独立洗染：**淡墨铺底 → 半干时局部再润湿和回流 → 干燥并记录沉积 → 改变位置与浓度再叠一遍**。每遍保留单独场，再组合累积场。检查的是干燥后的浓淡过渡与叠染层次，不能只截取湿润过程中的云雾图。

所选原始运行：512×512、种子 20261009、三遍共 990 帧；完整设置及位置记录见 provenance.json。这些帧是计算步数，不对应真实分钟；模型是艺术性湿媒体近似，未以某款墨汁的实测黏度、表面张力标定。原引擎与后来本地实验适配器的版本不同，发布的确定复现路径是从保存场提取素材，而不是宣称任意重跑均可生成同一图。

选择这个版本，是因为轻微积墨仍融入浓淡交汇处。较强咖啡环、刻意轮廓和细粒锐化会改变所选气质；它们没有加入默认材质。纸感留在独立图层，避免墨纹自带过强颗粒。

## 沉积场如何变成透明白

设沉积浓度为 D，保存的归一化尺度为 s，则：

```python
alpha = 0.74 * exp(-1.6 * D / s)
rgb = (255, 255, 255)
png_alpha = round(alpha * 255)
```

这是用于叠放的视觉通道，不是在仿真“白色墨汁”。浓墨处白色覆盖少，露出更多底色；淡墨处白色覆盖多，颜色较浅。保持一张通用白墨 PNG，换下面的底色就能得到青蓝、松绿、灰墨或淡赭石。

PNG alpha 为 0–255；CIM 颜色的第四项为 0–100 不透明度。CIM 图片设 100% 不透明度仍会保留 PNG 自身的 alpha。不要把两种单位混用。

纸纹由纸面高度 h 单独提取：`shade = clip(249 + (dx-dy)*65 + (h-.5)*5, 232, 255)`。因此墨纹无纸底，纸纹无底色；能够分别改变尺度和可见度。

## 精确提取

普通开发环境安装 NumPy、Pillow 后，在源码根目录执行：

```powershell
python scripts/extract_selected_materials.py output-materials
```

输出 generated-wet-ink.png / generated-white-paper.png，与发布 PNG 像素一致。独立素材 ZIP 内也附脚本；在解压目录执行 `python extract_selected_materials.py output --fields .`。普通制图用户直接用两张 PNG，不运行该命令，不安装仿真依赖。

## ArcGIS Pro 中叠放

面符号从上到下：淡实线轮廓 → 轻渐变外缘 → 透明白墨图片 → 半透明底色 → 纸纹图片。水体/绿地底色不透明度 72%；墨纹高度默认 112 pt，纸纹高度为其 0.64 倍；全图纸底图片为 35% 不透明度。道路与建筑保持轻薄，避免抢走纹理的层次。暖色广场与历史建筑仅在真实数据支持时使用。

112 pt 在 300 dpi 约为 467 像素，与 512 素材相匹配。导出高 dpi 不会增加素材本身细节。原选画布未宣称完全无缝，应在真实地图比例下查看铺排边界；纹理过密时先调图片高度，画面发白时先调白墨图片不透明度，纸感太强时只调纸层。

## 分享许可

本项目代码、Skill 与生成 PNG 按 MIT 分享，保留 LICENSE 与 Washes 的 MIT 署名。三城 OpenStreetMap 派生数据库另遵循 ODbL；字体与宏观定位边界不打包。参考图片、文档截图和未选试样不作为发布素材。
