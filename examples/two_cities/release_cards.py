"""0.4.0 teaching cards, rendered as native ArcGIS layouts; no map raster edits."""
import os,shutil
from pathlib import Path
import arcpy,arcpy.cim
import toolkit_cards as cards
from inkmap_arcpy.symbols import cim,picture,fill,polygon_symbol
from inkmap_arcpy.layout_primitives import text,rectangle,element,ref,INK,PAPER
from city_frames import JADE,BRASS

ROOT=Path(os.path.abspath(__file__)).parents[2]
OUT=ROOT/'deliverables/release-0.4.0/post'
cards.OUT=OUT
M=ROOT/'materials/selected-wet-ink'

def panel(g,name,x,y,side,kind):
    if kind in {'water','green','plaza'}:
        symbol=polygon_symbol(kind,'watercolor',side/2.54*72)
    else:
        path=M/(kind if kind.endswith('.png') else 'white-ink.png')
        symbol=cim('CIMPolygonSymbol',symbolLayers=[picture(path,side/2.54*72),fill((20,23,23) if kind=='black' else PAPER)])
    ring=[[x,y],[x+side,y],[x+side,y+side],[x,y+side],[x,y]]
    g.append(element(name,cim('CIMPolygonGraphic',polygon={'rings':[ring]},symbol=ref(symbol))))

def cover():
    p,l,g=cards.base('水墨地图，开源分享','墨纹素材 / Python 包 / AI 制图 Skill','01  /  VERSION 0.4.0')
    for x,kind,title in [(2.0,'water','青蓝水墨'),(11.3,'green','松绿水墨')]:
        panel(g,kind,x,14.9,7.7,kind)
        g.append(text(kind+' label',title,x+3.85,14.2,12,'STKaiti',JADE,'Center'))
    cards.row(g,12.2,1,'直接用材质，开始制图',['透明白墨与纸纹分别保存，换底色即可复用','无需运行流体仿真；原选墨纹保持不变'])
    cards.row(g,7.6,2,'从图层到交付，整理成流程',['42 个三城 GeoJSON 图层 + 导入脚本','完整图 / 地图框 / 可编辑工程 + 验收'])
    cards.foot(g,'福州 · 上海 · 洛杉矶  /  案例在后，素材与方法先分享')
    cards.finish(p,l,g,'01_封面_墨纹素材与AI制图')

def layers():
    p,l,g=cards.base('两张图，一套墨韵','透明白墨在上，底色居中，纸纹托底','02  /  MATERIAL LAYERS')
    for x,kind,title in [(1.65,'black','透明白墨 · 黑底查看'),(7.8,'water','白墨 + 青蓝底色'),(13.95,'paper.png','独立纸纹')]:
        panel(g,kind,x,15.8,5.4,kind)
        g.append(text(kind+' label',title,x+2.7,15.0,10.4,'STKaiti',JADE,'Center'))
    cards.row(g,12.9,1,'白色负责“遮”，底色负责“显”',['浓墨处白色覆盖较少，露出较深的底色','淡墨处白色覆盖较多，形成柔和亮部'])
    cards.row(g,8.45,2,'纸纹独立，颗粒感可单独控制',['墨纹不烘焙纸底，也不锁定蓝色或绿色','两张 PNG 可直接下载；实际尺寸 512 × 512'])
    cards.foot(g,'透明白图在白底上不易看见，请叠在黑底或有色底上检查。')
    cards.finish(p,l,g,'02_分层素材_白墨底色纸纹')

def drying():
    p,l,g=cards.base('三遍洗染，保留层次','淡墨铺底 → 半干回流 → 干燥 → 再叠染','03  /  WET MEDIA WORKFLOW')
    for i,x in enumerate([1.65,7.8,13.95],1):
        panel(g,'stage'+str(i),x,15.8,5.4,f'dry-stage-{i}.png')
        g.append(text('Stage label'+str(i),f'第 {i} 遍干燥后',x+2.7,15.0,11,'STKaiti',JADE,'Center'))
    cards.row(g,12.9,1,'先记录每遍沉积，再看叠加结果',['不同位置与浓度的墨层，形成大块浓淡交融','使用 Washes 湿媒体引擎，保存原始计算场'])
    cards.row(g,8.45,2,'验收干燥结果与叠染层次',['保留自然过渡，边缘融入墨色','本次默认不追加强咖啡环或密集细颗粒'])
    cards.foot(g,'艺术性湿媒体近似，非某款墨汁的实测物性标定；阶段文件随素材分享。')
    cards.finish(p,l,g,'03_制作思路_三遍干燥叠染')

def extraction():
    p,l,g=cards.base('从浓度场，提取白墨','保存的是可换底色的透明度通道','04  /  EXTRACTION')
    cards.row(g,21.6,1,'RGB 恒白，浓淡写进 alpha',['alpha = 0.74 × exp(-1.6 × D / s)','D 是沉积浓度，s 是保存的归一化尺度'])
    cards.row(g,17.15,2,'纸纹另由纸面高度提取',['同一套白墨叠青蓝、松绿、灰墨或淡赭色','纸感过强时只调纸层，不锐化墨纹'])
    cards.row(g,12.7,3,'素材文件与提取脚本一起分享',['PNG + 三遍预览 + 总场 / 分层场 + 参数','extract_selected_materials.py 可精确提取'])
    cards.row(g,8.25,4,'普通用户直接复用 PNG',['开发提取需 NumPy / Pillow，制图运行不需要','材质512像素，导出更高dpi不增加素材细节'])
    cards.foot(g,'完整教程：仓库 docs/ink-materials.md  /  原始场与第三方许可一并保留')
    cards.finish(p,l,g,'04_处理教程_浓度到透明白')

def design():
    p,l,g=cards.base('让整张图，也像水墨','纹理之外，统一线条、建筑和地标','05  /  MAP DESIGN')
    cards.row(g,21.6,1,'主路留白，外沿用灰青',['纸白路带保留清楚的城市骨架','支路淡暖灰；步道更细的连续线'])
    cards.row(g,17.15,2,'建筑薄墨，少量暖色呼应',['建筑低浓度灰墨；居住面极淡暖灰','有真实数据时，广场淡赭、历史建筑灰褐'])
    cards.row(g,12.7,3,'点符号统一，也保留辨识度',['站点：4点空心灰青圈 + 纸白中心','地标：暖墨圈 + 暗朱砂；社区：小墨圈'])
    cards.row(g,8.25,4,'文字与装帧，共用一张纸',['宋体标题 / 楷体地名 / Garamond 数字','框内三列图例，真北与米制比例尺关联主框'])
    cards.foot(g,'墨纹保持原选版；道路、建筑与符号已更新为包和 Skill 的默认方案。')
    cards.finish(p,l,g,'05_全图风格_道路建筑与地标')

def agent():
    p,l,g=cards.base('包执行，Skill 管流程','inkmap-arcpy 0.4.0 / arcpy-watercolor-map','06  /  PACKAGE + AI SKILL')
    cards.row(g,21.6,1,'安装 wheel，检查 Pro 环境',['Windows + 已授权的 ArcGIS Pro 3.x','doctor → inspect → atlas --dry-run → atlas'])
    cards.row(g,17.15,2,'安装 Skill，绑定真实图层',['将完整 Skill 文件夹放入 Agent 的 skills 目录','内附对应 wheel、配置说明与视觉验收规则'])
    cards.row(g,12.7,3,'导出并检查，可编辑交付',['完整图 / 地图框 PNG、PDF / 纯地图、世界文件','APRX + GDB + PAGX；重载检查数据连接'])
    for i,s in enumerate(['提示词：使用 $arcpy-watercolor-map 制作我的区位图。','中心只用于取景，定位文字放在圆内下部，','保留纸感和墨韵，导出全图与地图框版并验收。']):
        g.append(text('Prompt'+str(i),s,2.0,7.9-i*.85,10.5,'STKaiti',JADE))
    cards.foot(g,'Skill 需要 Agent 支持技能目录；ArcPy 由 ArcGIS Pro 提供。')
    cards.finish(p,l,g,'06_包与Skill_安装执行验收')

def resources():
    p,l,g=cards.base('素材、数据、工具一起拿','GitHub：Clamsk / inkmap-arcpy','07  /  DOWNLOADS')
    cards.row(g,21.6,1,'独立素材包 + 处理教程',['白墨、纸纹、阶段预览与保存场','MIT 许可，保留 Washes 第三方署名'])
    cards.row(g,17.15,2,'三城局部样例数据，共42层',['福州15层 / 上海13层 / 洛杉矶14层','OSM 派生数据库按 ODbL 提供，附数量与来源'])
    cards.row(g,12.7,3,'导入脚本 + Python 包 + AI Skill',['下载 releases/0.4.0 中的复用资源包','import_sample_data.py → job.json → atlas'])
    cards.row(g,8.25,4,'更换数据，也能做自己的地图',['社区点是名称点，历史面是建筑，不冒充边界','字体与宏观定位边界不随数据包分发'])
    cards.foot(g,'后三张是福州、上海、洛杉矶的应用案例；旧版保留在版本历史中。')
    cards.finish(p,l,g,'07_下载清单_素材数据与教程')

def cases():
    approved=ROOT/'deliverables/readable-stations-v4-2026-10-09'
    os.environ['INKMAP_GULOU_SOURCE']=str(approved/'可编辑工程/fuzhou/map.aprx')
    cards.fuzhou()
    for folder,old,new in [('发布图片','06_福州_鼓楼案例.png','08_福州_鼓楼案例.png'),('原图与PDF','06_福州_鼓楼案例.pdf','08_福州_鼓楼案例.pdf')]:
        (OUT/folder/old).rename(OUT/folder/new)
    for city,chinese,prefix in [('shanghai','上海外滩','09_上海_外滩案例'),('losangeles','洛杉矶回声湖','10_洛杉矶_回声湖案例')]:
        for ext,folder in [('png','发布图片'),('pdf','原图与PDF')]:
            shutil.copyfile(approved/'高清图'/(chinese+'_完整图.'+ext),OUT/folder/(prefix+'.'+ext))

if __name__=='__main__':
    for task in (cover,layers,drying,extraction,design,agent,resources,cases):task()
