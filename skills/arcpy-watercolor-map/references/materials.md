# 所选墨纹的处理与使用

0.4.0 沿用原选柔和湿墨与独立纸纹。制作依据：Washes 的三遍湿媒体洗染，淡墨铺底、半干局部再润湿、干燥、改变浓度与位置叠染。模型是艺术近似，未按特定墨汁物性标定。不要把素材说成实物扫描或标定流体结果。

浓度 D 反向映射为透明白通道：alpha = .74 × exp(-1.6 × D / s)。RGB 恒白，浓墨对应较少白色覆盖，显出底色。纸纹由独立纸面高度场提取，不烘焙进白墨。默认保留大块柔和过渡，不主动强化咖啡环、颗粒或闭合描线。

运行时直接使用 wheel 内 PNG，无需 Node、Washes、NumPy。素材实际512×512，未宣称完全无缝；按真实图幅查看铺排。先调底色、不透明度和图片高度，再考虑用户指定替换。

仓库 materials/selected-wet-ink 包含两张 PNG、三遍干燥预览、原始总场与分层场、provenance.json、许可。完整教程： https://github.com/Clamsk/inkmap-arcpy/blob/main/docs/ink-materials.md 。独立素材包：仓库 releases/0.4.0/inkmap-materials.zip。

开发者从保存场精确提取：`python scripts/extract_selected_materials.py output-materials`（需 NumPy/Pillow）。这是素材提取，不重建原始仿真。PNG alpha为0–255，CIM alpha为0–100不透明度，100%的图片不透明度仍保留PNG透明度。
