"""Draw city-themed framing as editable CIM vectors; never repaint geographic pixels."""
import argparse,json,math,os
from pathlib import Path
import arcpy,arcpy.cim
from inkmap_arcpy.layout_primitives import text,line,rectangle,area,polygon,edge_labels,PAPER
from cities import CITIES

ROOT=Path(os.path.abspath(__file__)).parent
JADE=(42,81,76); BRASS=(164,139,91); TERRA=(156,86,64); SAND=(196,151,101)

def render_folder(city):
    return ROOT/(os.environ.get('INKMAP_RENDER_PREFIX','render-')+city)

def circle_points(cx,cy,r,start=0,end=2*math.pi,count=96):
    return [[cx+r*math.cos(start+(end-start)*i/count),cy+r*math.sin(start+(end-start)*i/count)] for i in range(count+1)]

def shanghai_motif(cx,cy,scale=1,prefix='City deco'):
    graphics=[]
    for k,r in enumerate((.42,.68,.94)):
        graphics.append(line(f'{prefix} fan arc {k}',circle_points(cx,cy,r*scale,0,math.pi,48),BRASS,.35,76))
    for k in range(9):
        a=k*math.pi/8
        graphics.append(line(f'{prefix} fan ray {k}',[[cx,cy],[cx+.94*scale*math.cos(a),cy+.94*scale*math.sin(a)]],JADE,.32,75))
    graphics.append(line(f'{prefix} fan base',[[cx-1.03*scale,cy],[cx+1.03*scale,cy]],BRASS,.7,85))
    return graphics

def palm(cx,cy,scale=1,prefix='City palm'):
    tip=(cx+.26*scale,cy+1.52*scale)
    stem=[[cx+.26*scale*(i/20)**1.25,cy+1.52*scale*i/20] for i in range(21)]
    graphics=[line(prefix+' trunk',stem,TERRA,.72,80)]
    for k,(dx,dy) in enumerate([(-.92,.12),(-.8,.57),(-.40,.85),(.46,.8),(.88,.42),(1.0,-.12),(-.60,-.38),(.58,-.44)]):
        end=(tip[0]+dx*scale,tip[1]+dy*scale)
        control=(tip[0]+dx*scale*.55,tip[1]+(.46 if dy<.3 else .65)*scale)
        curve=[]
        for i in range(25):
            t=i/24
            curve.append([(1-t)**2*tip[0]+2*(1-t)*t*control[0]+t*t*end[0],
                          (1-t)**2*tip[1]+2*(1-t)*t*control[1]+t*t*end[1]])
        graphics.append(line(prefix+f' leaf {k}',curve,TERRA,.45,65))
    return graphics

def sunset(cx,cy,scale=1,prefix='City sun'):
    r=.62*scale
    points=circle_points(cx,cy,r,0,math.pi,48)+[[cx+r,cy]]
    graphics=[area(prefix+' disc',points,polygon(SAND,28)),
              line(prefix+' arch',circle_points(cx,cy,r,0,math.pi,48),TERRA,.55,85),
              line(prefix+' horizon',[[cx-1.18*scale,cy],[cx+1.18*scale,cy]],TERRA,.48,70)]
    for i in range(9):
        angle=.12+i*(math.pi-.24)/8
        graphics.append(line(prefix+f' ray {i}',[[cx+.83*scale*math.cos(angle),cy+.83*scale*math.sin(angle)],
                             [cx+1.04*scale*math.cos(angle),cy+1.04*scale*math.sin(angle)]],SAND,.4,75))
    for k in range(2):
        graphics.append(line(prefix+f' horizon below {k}',[[cx-(.88-.22*k)*scale,cy-(.12+.12*k)*scale],
                         [cx+(.88-.22*k)*scale,cy-(.12+.12*k)*scale]],SAND,.35,55))
    return graphics

def rounded_outline(x,y,w,h,r):
    coords=[]
    for cx,cy,a,b in [(x+w-r,y+r,-math.pi/2,0),(x+w-r,y+h-r,0,math.pi/2),
                       (x+r,y+h-r,math.pi/2,math.pi),(x+r,y+r,math.pi,1.5*math.pi)]:
        coords+=circle_points(cx,cy,r,a,b,18)
    return coords+[coords[0]]

def frame_graphics(city):
    spec=CITIES[city]; color=JADE if city=='shanghai' else TERRA
    graphics=[rectangle('Page paper',0,0,21,28,PAPER,100),
          text('Title',spec['title'],10.5,27.19,29.5,'STSong',color,'Center',2),
          text('English title',spec['english'],10.5,25.90,11 if city=='shanghai' else 10.5,
               'Garamond' if city=='shanghai' else 'Bahnschrift',color,'Center',1.2),
          text('Subtitle',spec['subtitle'],10.5,25.34,10,'STKaiti' if city=='shanghai' else 'Garamond',color,'Center'),
          text('City issue',('CITY ATLAS   /   01' if city=='shanghai' else 'CITY ATLAS   /   02'),1.07,1.15,7.2,'Garamond',color),
          text('City footer caption',spec['caption'],19.9,1.16,8,'STKaiti',color,'Right')]
    if city=='shanghai':
        graphics.extend([line('City outer border',[[.34,.35],[20.66,.35],[20.66,27.65],[.34,27.65],[.34,.35]],BRASS,.52,80),
                         line('City inner border',[[.5,.51],[20.5,.51],[20.5,27.49],[.5,27.49],[.5,.51]],JADE,.25,66),
                         line('City header left',[[1.18,25.12],[8.5,25.12]],BRASS,.35,72),
                         line('City header right',[[12.5,25.12],[19.82,25.12]],BRASS,.35,72)])
        graphics+=shanghai_motif(2.75,25.82,.83,'City left deco')
        graphics+=shanghai_motif(18.25,25.82,.83,'City right deco')
        for k,(cx,cy,sx,sy) in enumerate([(.67,.69,1,1),(20.33,.69,-1,1),(.67,27.30,1,-1),(20.33,27.30,-1,-1)]):
            graphics.append(line(f'City stepped corner {k}',[[cx,cy+.42*sy],[cx,cy],[cx+.42*sx,cy],
                                  [cx+.42*sx,cy+.14*sy],[cx+.14*sx,cy+.14*sy],[cx+.14*sx,cy+.42*sy]],BRASS,.42,80))
        for k in range(2):
            graphics.append(line(f'City river wave {k}',[[8.3+i*.085,.89+k*.065+.04*math.sin(i*.38)] for i in range(53)],JADE,.3,50))
    else:
        graphics.extend([line('City outer border',rounded_outline(.34,.35,20.32,27.30,.30),TERRA,.55,74),
                         line('City inner border',rounded_outline(.50,.51,20,26.98,.23),SAND,.25,55),
                         line('City header left',[[1.18,25.12],[7.9,25.12]],SAND,.35,60),
                         line('City header right',[[13.1,25.12],[19.82,25.12]],SAND,.35,60)])
        graphics+=palm(2.3,25.5,.78)
        graphics+=sunset(18.3,25.83,.83)
        graphics.append(line('City footer sun',circle_points(10.5,.87,.22,0,math.pi,30),SAND,.5,75))
    return graphics

def suppress_neighborhood_markers(project):
    m=next(m for m in project.listMaps() if m.listLayers('neighborhoods'))
    layer=m.listLayers('neighborhoods')[0]
    d=layer.getDefinition('V3')
    for marker in d.renderer.symbol.symbol.symbolLayers:
        for graphic in marker.markerGraphics:
            for symbol in graphic.symbol.symbolLayers:
                if getattr(symbol,'color',None): symbol.color.values[-1]=0
    layer.setDefinition(d)

def decorate(city):
    out=render_folder(city); spec=CITIES[city]
    p=arcpy.mp.ArcGISProject(str(out/'atlas.aprx'))
    suppress_neighborhood_markers(p)
    full=p.listLayouts('Watercolor atlas · full')[0]
    full.pageHeight=28
    main=full.listElements('MAPFRAME_ELEMENT','Atlas main frame')[0]
    main.elementHeight=22.75
    for inset in full.listElements('MAPFRAME_ELEMENT','Locator frame*'):
        inset.elementPositionY-=1.25
    for caption in full.listElements('TEXT_ELEMENT','Locator caption*'):
        caption.elementPositionY-=1.25
    for name,kind in [('Compass N','TEXT_ELEMENT'),('North Arrow','MAPSURROUND_ELEMENT')]:
        e=full.listElements(kind,name)[0]; e.elementPositionY-=1.25
    definition=full.getDefinition('V3')
    remove={'Page paper','Title','English title','Subtitle','Header rule','Header rule right','Header caption','Source'}
    definition.elements=[e for e in definition.elements if e.name not in remove and not e.name.startswith('Grid ')]
    graphics=frame_graphics(city)
    attribution='© OpenStreetMap contributors · ODbL  |  '+('Locator: GeoAtlas 2021' if city=='shanghai' else 'Locator: US Census 2024')
    definition.elements=[graphics[0]]+definition.elements+graphics[1:]+[text('Source',attribution,1.07,.80,5.8,'Garamond',(116,124,111))]
    labels,count=edge_labels(main,spec['grid_seconds']/3600)
    definition.elements+=labels; full.setDefinition(definition)
    full.name=city+' · city edition'
    full.exportToPNG(str(out/(city+'_full.png')),resolution=240)
    full.exportToPDF(str(out/(city+'_full.pdf')),resolution=300,image_quality='BEST',output_as_image=True,
                     image_compression='ADAPTIVE',jpeg_compression_quality=90)
    pagx=out/'city_full.pagx'; full.exportToPAGX(str(pagx))
    names={l.name for l in p.listLayouts()}; p.importDocument(str(pagx),reuse_existing_maps=True)
    frame=next(l for l in p.listLayouts() if l.name not in names); frame.name=city+' · frame edition'
    d=frame.getDefinition('V3')
    d.elements=[e for e in d.elements if e.name not in remove and not e.name.startswith('City ')]
    d.elements.append(rectangle('Frame crop padding',.5,1,20,24.05,PAPER,0)); frame.setDefinition(d)
    frame.exportToPNG(str(out/(city+'_frame.png')),resolution=240,clip_to_elements=True)
    frame.exportToPDF(str(out/(city+'_frame.pdf')),resolution=300,image_quality='BEST',output_as_image=True,
                      image_compression='ADAPTIVE',jpeg_compression_quality=90,clip_to_elements=True)
    main.exportToPNG(str(out/(city+'_map_only.png')),resolution=240,world_file=True)
    p.saveACopy(str(out/(city+'_city.aprx')))
    report=dict(city=city,framing='Shanghai geometric Art Deco' if city=='shanghai' else 'California sun and palm linework',
         page_cm=[21,28],grid_labels=count,map_frame_cm=[19,22.75],center_marker=False,
         geographic_source='OpenStreetMap',decoration_note='Framing motifs are decorative, not mapped features')
    (out/'city_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('city',choices=CITIES); args=parser.parse_args(); decorate(args.city)
