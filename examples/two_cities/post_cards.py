"""Render native ArcGIS layouts for a six-image social post. All maps retain real geometry."""
import argparse,json,math,os
from pathlib import Path
import arcpy,arcpy.cim
from inkmap_arcpy.symbols import cim
from inkmap_arcpy.layout_primitives import text,line,rectangle,area,polygon,ref,graticule,edge_labels,PAPER,INK
from city_frames import frame_graphics,shanghai_motif,palm,sunset,rounded_outline,JADE,BRASS,TERRA,SAND,render_folder
from cities import CITIES

ROOT=Path(os.path.abspath(__file__)).parent
WORKSPACE=ROOT.parent.parent
DELIVERY=Path(os.environ.get('INKMAP_DELIVERY',str(WORKSPACE/'deliverables/shanghai-losangeles-2026-10-08')))
DETAILS={
 'shanghai':dict(center=[121.491,31.243],scale=10500,title='上海 · 江河细节',english='T H E   B U N D   /   S U Z H O U   C R E E K',subtitle='外白渡桥附近 · 1:10,500',caption='桥梁 · 河岸 · 街巷'),
 'losangeles':dict(center=[-118.26062,34.07297],scale=10000,title='洛城 · 湖光细节',english='E C H O   P A R K   L A K E',subtitle='回声湖周边 · 1:10,000',caption='水面 · 公园 · 居住街区')}

def export(layout,name,folder=None,pdf=False):
    out=folder or DELIVERY/'发布图片'; out.mkdir(parents=True,exist_ok=True)
    layout.exportToPNG(str(out/(name+'.png')),resolution=240)
    if pdf:
        layout.exportToPDF(str(DELIVERY/'原图与PDF'/(name+'.pdf')),resolution=300,image_quality='BEST',output_as_image=True,
                           image_compression='ADAPTIVE',jpeg_compression_quality=90)
    print(f'Exported {name}',flush=True)

def detail(city):
    folder=render_folder(city); p=arcpy.mp.ArcGISProject(str(folder/(city+'_city.aprx')))
    p.importDocument(str(folder/'city_full.pagx'),reuse_existing_maps=True)
    layout=p.listLayouts()[-1]
    # listLayouts is not insertion-ordered; locate the newly imported copy by map and name suffix.
    layout=next(l for l in p.listLayouts() if l.name.startswith(city+' · city edition') and l.name!=city+' · city edition')
    layout.name=city+' · detail edition'; spec=DETAILS[city]
    frame=layout.listElements('MAPFRAME_ELEMENT','Atlas main frame')[0]
    sr=arcpy.SpatialReference(CITIES[city]['projection'])
    point=arcpy.PointGeometry(arcpy.Point(*spec['center']),arcpy.SpatialReference(4326)).projectAs(sr).firstPoint
    frame.camera.X,frame.camera.Y,frame.camera.scale=point.X,point.Y,spec['scale']
    d=layout.getDefinition('V3')
    d.elements=[e for e in d.elements if not e.name.startswith(('Locator frame','Locator caption','Grid '))]
    main=next(e for e in d.elements if e.name==frame.name); main.grids=[graticule(15/3600,'Detail WGS84 dashed graticule')]
    for e in d.elements:
        if e.name in {'Title','English title','Subtitle','City footer caption','City issue'}:
            e.graphic.text={'Title':spec['title'],'English title':spec['english'],'Subtitle':spec['subtitle'],
                            'City footer caption':spec['caption'],'City issue':'CITY DETAIL   /   '+('01' if city=='shanghai' else '02')}[e.name]
            if e.name=='English title': e.graphic.symbol.symbol.height=8.7
            if e.name=='Subtitle': e.graphic.symbol.symbol.fontFamilyName='STKaiti'
        if e.name=='Scale bar':
            e.elements[0].division=250
            e.elements[0].divisions=2
    layout.setDefinition(d)
    labels,count=edge_labels(frame,15/3600)
    d=layout.getDefinition('V3'); d.elements+=labels; layout.setDefinition(d)
    name='03_上海_江河细节' if city=='shanghai' else '05_洛杉矶_湖光细节'
    export(layout,name,pdf=True)
    p.saveACopy(str(folder/(city+'_post.aprx')))
    return dict(city=city,center=spec['center'],scale=spec['scale'],grid_seconds=15,grid_labels=count)

def new_layout():
    install=Path(arcpy.GetInstallInfo()['InstallDir'])
    p=arcpy.mp.ArcGISProject(str(install/'Resources/ArcToolBox/Services/routingservices/data/Blank.aprx'))
    p.importDocument(str(install/'Resources/ArcToolBox/Templates/ExportWebMapTemplates/A4 Portrait.pagx'))
    layout=p.listLayouts()[0]; layout.pageWidth=21; layout.pageHeight=28
    return p,layout

def cover():
    p,layout=new_layout(); layout.name='Two cities · cover'
    frame_template=next(e for e in layout.getDefinition('V3').elements if e.__class__.__name__=='CIMMapFrame')
    graphics=[rectangle('Page paper',0,0,21,28,PAPER,100),
        line('Cover border',rounded_outline(.42,.42,20.16,27.16,.25),(153,147,126),.42,62),
        text('Cover eyebrow','C I T Y   W A T E R C O L O U R   A T L A S',10.5,27.02,8.6,'Garamond',INK,'Center'),
        text('Cover title','把城市画成水彩',10.5,25.80,32,'STSong',JADE,'Center',1),
        text('Cover subtitle','上海的江河  /  洛杉矶的湖光',10.5,24.12,12.6,'STKaiti',(112,115,100),'Center'),
        text('Cover Shanghai','上 海',5.30,22.82,20,'STSong',JADE,'Center',2),
        text('Cover LA','洛 杉 矶',15.70,22.82,20,'STSong',TERRA,'Center',2),
        text('Cover Shanghai en','S H A N G H A I',5.30,21.90,8.5,'Garamond',JADE,'Center'),
        text('Cover LA en','L O S   A N G E L E S',15.70,21.90,8.2,'Bahnschrift',TERRA,'Center'),
        text('Cover bottom lead','同一套水彩底图 · 两种城市装帧',10.5,5.35,13.5,'STKaiti',JADE,'Center'),
        text('Cover tech','ArcGIS Pro  ×  ArcPy  ×  AI Agent Skill',10.5,4.42,10.7,'Garamond',INK,'Center'),
        text('Cover series','真实地理数据 / 原生符号 / 可编辑工程',10.5,3.43,9.1,'STSong',(116,124,111),'Center'),
        text('Cover attribution','© OpenStreetMap contributors · ODbL',10.5,1.01,6.4,'Garamond',(116,124,111),'Center')]
    maps=[]
    for city,x,color in [('shanghai',1.12,JADE),('losangeles',11.18,TERRA)]:
        source=arcpy.mp.ArcGISProject(str(render_folder(city)/(city+'_city.aprx')))
        m=next(m for m in source.listMaps() if m.listLayers('water'))
        mapx=render_folder(city)/'social_seed.mapx'; m.exportToMAPX(str(mapx))
        old={m.URI for m in p.listMaps()}; p.importDocument(str(mapx)); imported=next(m for m in p.listMaps() if m.URI not in old)
        fd=next(e for e in layout.getDefinition('V3').elements if e.__class__.__name__=='CIMMapFrame')
        fd.name=city+' cover frame'; fd.uRI=imported.URI
        fd.frame={'rings':[[[x,6.17],[x+8.70,6.17],[x+8.70,21.28],[x,21.28],[x,6.17]]]}
        fd.grids=[]; fd.graphicFrame.borderSymbol=ref(polygon(PAPER,0,color,.35))
        fd.graphicFrame.backgroundSymbol=ref(polygon(PAPER)); fd.graphicFrame.shadowSymbol=None
        maps.append((fd,imported,city))
        graphics.append(fd)
    d=layout.getDefinition('V3'); d.elements=graphics; layout.setDefinition(d)
    for fd,m,city in maps:
        frame=layout.listElements('MAPFRAME_ELEMENT',fd.name)[0]; frame.map=m
        sr=arcpy.SpatialReference(CITIES[city]['projection'])
        pt=arcpy.PointGeometry(arcpy.Point(*CITIES[city]['center']),arcpy.SpatialReference(4326)).projectAs(sr).firstPoint
        frame.camera.X,frame.camera.Y=pt.X,pt.Y
        frame.camera.scale=CITIES[city]['scale']*19/8.7
    export(layout,'01_封面_把城市画成水彩',pdf=True)
    p.saveACopy(str(DELIVERY/'原图与PDF/cover.aprx'))

def style_card():
    p,layout=new_layout(); layout.name='Two cities · style guide'
    source=arcpy.mp.ArcGISProject(str(render_folder('shanghai')/'shanghai_city.aprx'))
    m=next(m for m in source.listMaps() if m.listLayers('water'))
    g=[rectangle('Page paper',0,0,21,28,PAPER,100),
       line('Guide border',rounded_outline(.42,.42,20.16,27.16,.25),(153,147,126),.42,62),
       text('Guide eyebrow','DESIGN NOTES   /   CITY ATLAS',10.5,27.0,8.6,'Garamond',INK,'Center'),
       text('Guide title','同一套水彩',10.5,25.7,30,'STSong',JADE,'Center'),
       text('Guide subtitle','两种城市装帧',10.5,24.25,20,'STKaiti',INK,'Center'),
       text('Shared heading','底 图 统 一',10.5,22.36,11.8,'STKaiti',INK,'Center'),
       text('Shanghai label','上海 · 海派几何',5.60,18.44,16,'STSong',JADE,'Center'),
       text('LA label','洛杉矶 · 加州日光',15.40,18.44,16,'STSong',TERRA,'Center'),
       line('Shanghai box',[[1.35,9.02],[9.85,9.02],[9.85,19.34],[1.35,19.34],[1.35,9.02]],BRASS,.48,80),
       line('LA box',rounded_outline(11.15,9.02,8.5,10.32,.3),TERRA,.48,70)]
    for kind,label,x in [('water','海蓝水体',4.8),('parks','水彩绿地',10.5),('buildings','淡灰建筑',16.2)]:
        symbol=m.listLayers(kind)[0].getDefinition('V3').renderer.symbol
        patch=cim('CIMPolygonGraphic',polygon={'rings':[[[x-.73,20.47],[x+.73,20.47],[x+.73,21.50],[x-.73,21.50],[x-.73,20.47]]]},symbol=symbol)
        g.append(cim('CIMGraphicElement',name=kind+' sample',visible=True,anchor='BottomLeftCorner',graphic=patch))
        g.append(text(kind+' label',label,x,20.20,9.3,'STSong',INK,'Center'))
    g+=shanghai_motif(5.60,15.13,1.23,'Guide deco')
    g+=palm(14.7,13.8,.75,'Guide palm')
    g+=sunset(16.6,15.14,.62,'Guide sun')
    for color,cx,lines in [(JADE,5.60,['墨绿 × 黄铜','几何折线与扇形装饰','宋体与衬线字的秩序感']),
                           (TERRA,15.40,['暖沙 × 日落橙','圆角线框与棕榈线描','明亮、舒展的加州气质'])]:
        for i,value in enumerate(lines): g.append(text(f'{cx} note {i}',value,cx,12.99-i*.9,10.2 if i==0 else 8.8,'STSong',color,'Center'))
    g.append(text('Workflow title','从数据到成图',10.5,7.97,13.5,'STKaiti',INK,'Center'))
    for i,label in enumerate(['真实取数','ArcPy 符号','原生布局','检查与导出']):
        x=1.6+i*4.63
        g.extend([rectangle(f'Step {i}',x,5.63,3.95,1.20,PAPER,100,(184,185,167)),
                  text(f'Step text {i}',label,x+1.975,6.48,9.7,'STSong',INK,'Center')])
        if i<3:
            g.append(text(f'Step arrow {i}','→',x+4.30,6.40,10,'Garamond',BRASS,'Center'))
    g.extend([text('Guide final','地图表达统一，装帧呼应城市气质。',10.5,4.29,10.5,'STKaiti',INK,'Center'),
              text('Guide package','inkmap-arcpy 0.3.0  /  arcpy-watercolor-map skill',10.5,3.26,8.7,'Garamond',INK,'Center'),
              text('Guide source','github.com/Clamsk/inkmap-arcpy',10.5,2.43,8.8,'Garamond',INK,'Center'),
              text('Guide notice','样例使用 OpenStreetMap；图框纹样为装饰设计。',10.5,1.20,7.4,'STSong',(116,124,111),'Center')])
    d=layout.getDefinition('V3'); d.elements=g; layout.setDefinition(d)
    export(layout,'06_风格与流程说明',pdf=True)
    p.saveACopy(str(DELIVERY/'原图与PDF/style_guide.aprx'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('target',choices=['shanghai','losangeles','cover','style'])
    args=parser.parse_args(); (DELIVERY/'原图与PDF').mkdir(parents=True,exist_ok=True)
    if args.target in CITIES:
        print(json.dumps(detail(args.target),ensure_ascii=False,indent=2))
    elif args.target=='cover': cover()
    else: style_card()
