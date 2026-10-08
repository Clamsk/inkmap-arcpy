"""Reproduce the public 0.2 Gulou theme after downloading and preparing example data."""
import argparse,json,os
from pathlib import Path
from inkmap_arcpy import compose_atlas

ROOT=Path(os.path.abspath(__file__)).parent

def gulou_job(project,map_name,output):
    layers={
        '居住区范围（OSM）':{'role':'buildings','fill_opacity':16,'outline_opacity':0},
        '建筑轮廓':'buildings','其他绿地与林地':'green',
        '公园与花园':{'role':'green','label_field':'label'},'河湖水面':'water',
        '内河水线':'roads_other','支路与步行路':'roads_other',
        '主要道路':{'role':'roads_main','label_field':'label'},
        '街道乡镇名称（OSM）':{'role':'buildings','label_field':'label','fill_opacity':0,'outline_opacity':0},
        '街道乡镇界（OSM）':'boundary','地铁站点':'station',
        '社区名称点（OSM）':{'role':'station','label_field':'label'}}
    legends=[('主要道路','主要道路'),('河湖水面','河湖水面'),('支路与步行路','支路步行'),
             ('公园与花园','公园花园'),('街道乡镇界（OSM）','街道界线'),('其他绿地与林地','其他绿地'),
             ('地铁站点','地铁站点'),('建筑轮廓','建筑轮廓'),('社区名称点（OSM）','社区名称点'),('居住区范围（OSM）','居住区范围')]
    job=dict(project=os.path.abspath(project),map=map_name,output_folder=os.path.abspath(output),layers=layers,
             center=[119.294,26.086],scale=21000,projection=32650,title='榕城 · 鼓楼',
             english_title='G U L O U   /   F U Z H O U',subtitle='福州鼓楼区水彩区位图',
             source_note='© OpenStreetMap contributors · ODbL  |  定位 GeoAtlas 2021 · 学习示例',
             legend=[dict(layer=name,label=label) for name,label in legends],locators=[])
    for code,caption,highlight,projection,step in [('100000','全国 · 福建','350000',102012,10),
                      ('350000','福建 · 福州','350100',32650,1),('350100','福州 · 鼓楼','350102',32650,.5)]:
        job['locators'].append(dict(geojson=str(ROOT/'data/locators'/f'{code}_full.json'),caption=caption,
                                   highlight=highlight,projection=projection,grid_degrees=step))
    return job

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('project',help='Input APRX from build_map.py, or existing matching source layers')
    parser.add_argument('output',help='New output directory')
    parser.add_argument('--map',default='福州中心城区水彩地图')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    print(json.dumps(compose_atlas(gulou_job(args.project,args.map,args.output),args.dry_run),ensure_ascii=False,indent=2))
