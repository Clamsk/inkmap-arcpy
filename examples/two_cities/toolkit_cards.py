"""Native 3:4 cards that introduce the data, ArcPy package and Agent skill."""
import json,sys,os
from pathlib import Path
import arcpy,arcpy.cim
from post_cards import new_layout
from city_frames import JADE,BRASS,TERRA,rounded_outline
from inkmap_arcpy.layout_primitives import text,line,rectangle,edge_labels,PAPER,INK

ROOT=Path(os.path.abspath(__file__)).parents[2]
OUT=Path(os.environ.get('INKMAP_DELIVERY',str(ROOT/'deliverables/inkmap-toolkit-three-cities-2026-10-08')))

def base(title,subtitle,issue):
    p,l=new_layout(); l.name=issue
    g=[rectangle('Paper',0,0,21,28,PAPER,100),
       line('Border',rounded_outline(.42,.42,20.16,27.16,.25),BRASS,.45,65),
       text('Eyebrow','INKMAP  /  ARCPY + AI AGENT SKILL',10.5,27,9,'Garamond',JADE,'Center'),
       text('Title',title,10.5,25.8,28,'STSong',JADE,'Center'),
       text('Subtitle',subtitle,10.5,24.35,11.5,'STKaiti',INK,'Center'),
       line('Rule',[[1.45,23.5],[19.55,23.5]],BRASS,.45,70),
       text('Issue',issue,1.45,1.2,7.4,'Garamond',JADE),
       text('Repo','github.com/Clamsk/inkmap-arcpy',19.55,1.2,8.4,'Garamond',JADE,'Right')]
    return p,l,g

def row(g,y,n,title,lines,color=JADE):
    g.extend([text(f'N{n}',str(n).zfill(2),1.7,y,21,'Garamond',BRASS),
              text(f'H{n}',title,3.4,y,16,'STSong',color)])
    for i,s in enumerate(lines):
        g.append(text(f'L{n}-{i}',s,3.4,y-1.13-i*.68,10.5,'STSong',INK))

def foot(g,s):
    g.append(text('Foot',s,10.5,2.35,8.8,'STKaiti',INK,'Center'))

def finish(p,l,g,name):
    d=l.getDefinition('V3');d.elements=g;l.setDefinition(d)
    bad=[e.name for e in l.listElements('TEXT_ELEMENT') if getattr(e,'isOverflowing',False)]
    assert not bad,bad
    (OUT/'发布图片').mkdir(parents=True,exist_ok=True)
    (OUT/'原图与PDF').mkdir(parents=True,exist_ok=True)
    l.exportToPNG(str(OUT/'发布图片'/(name+'.png')),resolution=240)
    l.exportToPDF(str(OUT/'原图与PDF'/(name+'.pdf')),resolution=300,output_as_image=True)
    p.saveACopy(str(OUT/'原图与PDF'/(name+'.aprx')))
    print('Exported '+name,flush=True)

def cover():
    p,l,g=base('水墨地图工具包','把真实数据，交给 ArcPy 与 AI Agent。','01  /  TOOLKIT')
    g+=[text('Hero','GIS 数据 + Python 包 + AI Skill',10.5,21.6,17,'STSong',JADE,'Center'),
        text('Hero sub','从图层绑定到可编辑工程，整理成可复用流程。',10.5,20.1,11,'STKaiti',INK,'Center')]
    row(g,17.8,1,'三城样例数据',['福州鼓楼 / 上海外滩 / 洛杉矶回声湖','道路、水体、公园、建筑及地名点 · GeoJSON'])
    row(g,13.35,2,'inkmap-arcpy · 0.3.0',['独立泼墨层与纸纹层、图例、定位圈及经纬网','完整图 / 地图框 / 纯地图 · APRX + GDB'])
    row(g,8.9,3,'arcpy-watercolor-map Skill',['让 Agent 按流程检查数据、绑定样式、设计与导出','统一底图表达，装帧可以随城市调整'])
    foot(g,'本机 ArcGIS Pro 3.0 实测 · 预存柔和湿墨材质 · 项目可编辑')
    finish(p,l,g,'01_封面_水墨地图工具包')

def data():
    p,l,g=base('先把数据整理好','三城样例数据包 · 每个图层都有来源和角色','02  /  DATA')
    row(g,21.6,1,'按制图角色拆成图层',['主要道路 / 支路步行 / 河湖水面 / 公园绿地','建筑轮廓 / 轨道站点 / 社区或街区名称点'])
    row(g,17.15,2,'三城 GeoJSON，可直接导入',['福州 11 层 / 上海 10 层 / 洛杉矶 10 层','WGS84 数据 + 本地米制投影配置 + 要素数量'])
    row(g,12.7,3,'保留元数据与可追溯标识',['获取日期、范围、OSM id、名称和字段说明','OSM 数据采用 ODbL；来源和许可随数据附带'])
    row(g,8.25,4,'地名点有明确含义',['社区名称点用于标注，不能当作完整社区边界','宏观定位边界另按来源获取、配置和署名'])
    foot(g,'有自己的 GIS 数据，也可以直接绑定到同一套制图角色。')
    finish(p,l,g,'02_数据包_三城图层与来源')

def package():
    p,l,g=base('Python 包负责执行','inkmap-arcpy · 在 ArcGIS Pro Python 环境中运行','03  /  PACKAGE')
    row(g,21.6,1,'复用符号与配色',['水墨图片与纸纹分别叠放；道路与建筑保持清淡','可切换水彩 / 灰墨；也可使用有授权的自有纹理'])
    row(g,17.15,2,'从配置生成完整布局',['绑定真实图层，设置中心、投影、比例与定位边界','原生图例、真北指针、米制比例尺和经纬网'])
    row(g,12.7,3,'有检查，再正式制图',['doctor → inspect → atlas --dry-run → atlas','输入数据复制到新 GDB，输出新项目和检查报告'])
    row(g,8.25,4,'安装入口',['在 Pro Python 中安装 0.3.0 wheel','python -m inkmap_arcpy doctor'])
    foot(g,'Windows + 已授权的 ArcGIS Pro 3.x；ArcPy 由 Pro 提供。')
    finish(p,l,g,'03_Python包_能力与入口')

def skill():
    p,l,g=base('AI Skill 负责流程','arcpy-watercolor-map · 让 Agent 按步骤制图','04  /  AI SKILL')
    row(g,21.6,1,'先确认环境与真实数据',['检查 Pro、地图名、图层名、标签字段和几何','根据当地选择投影，保持输入项目与数据'])
    row(g,17.15,2,'再选择制图路径',['atlas：生成完整典雅布局；style：调整既有项目','参考文件明确符号、配置、版式与验收规则'])
    row(g,12.7,3,'最后看图并检查工程',['检查标签裁切、定位说明、比例尺和真北关联','同时导出完整图、地图框版，保存 APRX 与 GDB'])
    g+=[rectangle('Prompt panel',1.65,4.45,17.7,4.65,PAPER,100,BRASS),
        text('Prompt title','给 Agent 的示例指令',2.25,8.50,12,'STKaiti',JADE)]
    for i,s in enumerate(['使用 $arcpy-watercolor-map，把我的道路、水体、',
                           '公园和建筑做成水墨区位图。中心只用于取景，',
                           '定位文字放在圈内下部，导出全图和地图框版。']):
        g.append(text('Prompt'+str(i),s,2.25,7.48-i*.75,10.1,'STSong',INK))
    foot(g,'Skill 是工作指引；制图执行依赖 Python 包、ArcPy 和真实数据。')
    finish(p,l,g,'04_AI_Skill_流程与提示词')

def outputs():
    p,l,g=base('拿到手，怎样复用','发布包看案例 · 资源包开始做自己的地图','05  /  START HERE')
    row(g,21.6,1,'下载复用资源包',['0.3.0 wheel + 独立 Skill ZIP + 源码 ZIP','三城样例 GeoJSON + 导入脚本 + 数据说明'])
    row(g,17.15,2,'导入样例，生成任务配置',['用 Pro Python 运行 import_sample_data.py','得到 input.aprx、input.gdb、job.json'])
    row(g,12.7,3,'运行与验收',['先 dry-run，再 atlas；打开导出图检查排版','换城市时调整真实图层、投影、取景和定位边界'])
    row(g,8.25,4,'交付完整的可编辑成果',['完整图 / 地图框 PNG、PDF / 纯地图 PNG、PGW','APRX + GDB + PAGX + 检查报告'])
    foot(g,'后面三张：福州、上海、洛杉矶，作为同一流程的应用案例。')
    finish(p,l,g,'05_复用入口_导入与导出')

def fuzhou():
    source=Path(os.environ.get('INKMAP_GULOU_SOURCE',str(ROOT/'examples/fuzhou/render-atlas/atlas.aprx')))
    p=arcpy.mp.ArcGISProject(str(source));l=p.listLayouts('Watercolor atlas · full')[0]
    l.pageHeight=28
    main=l.listElements('MAPFRAME_ELEMENT','Atlas main frame')[0]
    center=(main.camera.X,main.camera.Y,main.camera.scale)
    main.elementHeight=22.75
    main.camera.X,main.camera.Y,main.camera.scale=center
    for kind,pattern in [('MAPFRAME_ELEMENT','Locator frame*'),('TEXT_ELEMENT','Locator caption*'),
                          ('TEXT_ELEMENT','Compass N'),('MAPSURROUND_ELEMENT','North Arrow')]:
        for e in l.listElements(kind,pattern):e.elementPositionY-=1.25
    d=l.getDefinition('V3')
    remove={'Page paper','Title','English title','Subtitle','Header rule','Header rule right','Header caption','Source'}
    d.elements=[e for e in d.elements if e.name not in remove and not e.name.startswith('Grid ')]
    g=[rectangle('Page paper',0,0,21,28,PAPER,100),
       text('Title','榕城 · 鼓楼',10.5,27.19,29.5,'STSong',JADE,'Center'),
       text('English title','G U L O U   /   F U Z H O U',10.5,25.90,10.5,'Garamond',JADE,'Center'),
       text('Subtitle','样例 01 · 福州鼓楼 · 水墨区位图',10.5,25.34,10,'STKaiti',INK,'Center'),
       text('Source','© OpenStreetMap contributors · ODbL  |  定位 GeoAtlas 2021 · 学习示例',1.07,.80,5.8,'Garamond',INK)]
    labels,count=edge_labels(main,30/3600)
    d.elements=[g[0]]+d.elements+g[1:]+labels;l.setDefinition(d)
    assert not p.listBrokenDataSources()
    for e in l.listElements('TEXT_ELEMENT'):assert not getattr(e,'isOverflowing',False),e.name
    l.name='Fuzhou · toolkit example'
    (OUT/'发布图片').mkdir(parents=True,exist_ok=True);(OUT/'原图与PDF').mkdir(parents=True,exist_ok=True)
    l.exportToPNG(str(OUT/'发布图片/06_福州_鼓楼案例.png'),resolution=240)
    l.exportToPDF(str(OUT/'原图与PDF/06_福州_鼓楼案例.pdf'),resolution=300,output_as_image=True)
    p.saveACopy(str(OUT/'原图与PDF/fuzhou_post.aprx'))
    print(json.dumps(dict(city='fuzhou',grid_labels=count,scale=main.camera.scale,broken=[])),flush=True)

if __name__=='__main__':
    tasks={'cover':cover,'data':data,'package':package,'skill':skill,'outputs':outputs,'fuzhou':fuzhou}
    if sys.argv[1]=='all':
        for f in tasks.values():f()
    else:tasks[sys.argv[1]]()
