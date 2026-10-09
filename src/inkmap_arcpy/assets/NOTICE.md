0.3.0 使用用户在 2026-10-09 选定的柔和湿墨底稿。generated-wet-ink.png 是纯白 RGB、变化 alpha 的透明墨色通道；generated-white-paper.png 是独立纸纹。两张图片均为 512×512，未放大后冒称原生高清。素材逐字节保留所选版本，没有加入后续咖啡环增强、圆弧描线或新的颗粒场。

墨纹来自现成 Washes 湿媒体引擎的三遍洗染与干燥沉积；透明白通道由其沉积量反向映射。纸纹由同次计算的纸面高度场独立提取，是生成纸纹，并非实物扫描。模型参数属于艺术系数，不代表某款墨汁经实测标定的黏度、表面张力或真实时间。

Washes：https://github.com/castavridis/washes-js，MIT，Copyright (c) 2026 Stephanie。原始引擎摘要、实际参数、沉积场及提取程序保存在源码 materials/selected-wet-ink 与 scripts/extract_selected_materials.py。wheel 的 material.json 保存素材摘要及通道信息。制图端仅读取预生成 PNG，不依赖 Node、Washes、NumPy、SciPy 或流体仿真。

本项目程序与生成图片以 MIT 分发。外部引擎代码仍保留其独立 MIT 署名，第三方论文插图与参考截图没有用作发布素材。图片原始画布未被声明为完全无缝；应在实际地图比例下检查铺排边界，必要时更换自有素材。

旧 0.1.0 私人示例曾使用用户《素材.docx》图片，旧 0.2.0 使用程序噪声。那些参考图片、旧安装包及私人项目不属于本次默认素材；被否定的 imagegen、颗粒高清和积墨增强试样也不进入默认 wheel。自定义 wash_path/paper_path 的许可由素材来源决定。

第三方署名（Washes）：

MIT License

Copyright (c) 2026 Stephanie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
