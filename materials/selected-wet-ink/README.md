# 所选柔和湿墨材质

用户选定的视觉目标：柔和湿墨铺染，浓淡自然交融，纸感隐约，边缘藏在墨色里。三遍独立洗染的沉积层用于形成浓淡底稿，原选图没有追加咖啡环强化或后续圆弧增量。默认材质为512×512，透明白 RGB 与 alpha 单独保存，纸纹独立。

`selected-fields.npz` 保存所选版本的原始总沉积量和纸面高度；`provenance.json` 保存实际 Washes 引擎 SHA、种子、参数、落墨与再润湿位置及最终素材 SHA。原引擎源地址：https://github.com/castavridis/washes-js，原始文件SHA256为 `3e3281bd3c4eafbdba2c8c143a23e73c80f9d7b3dd89570f6f4a2945f0ee983e`。许可见 `WASHES-LICENSE`。

开发者需要复现素材提取时，普通 Python 安装 NumPy/Pillow，然后在仓库根目录运行：

```powershell
python scripts/extract_selected_materials.py output-materials
```

两张输出的像素与默认素材一致。此步骤从保存场提取图像，不重跑或重建仿真；地图使用者不需要执行它。保留原选画布，未宣称它完全无缝。112点墨纹在300dpi下约467像素，可利用512像素素材，增加页面输出dpi不增加原始材质的细节。

默认地图样式仅微调符号的外缘、墨纹铺排尺度与纸感可见度，底色保持原蓝绿配色。湿媒体引擎未按某款墨汁的实测物性标定。

0.4.0 开放两张可直接使用的 `white-ink.png` / `paper.png`、三遍 `dry-stage-*.png` 原预览和 `dry-glazes.npz`（各遍沉积 layer_1..3、累积 stage_1..3）。文件说明、叠层规则和处理思路见 [完整教程](../../docs/ink-materials.md)。默认素材与0.3.0字节一致；新的地图表达保留了该墨纹。许可见本目录 LICENSE 与 WASHES-LICENSE。
