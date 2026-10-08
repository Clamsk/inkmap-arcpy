"""Normalize the Overpass extract into WGS84 GeoJSON, preserving OSM identity."""
import collections
import csv
import json
import os
import re
from pathlib import Path
import xlrd
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import polygonize, unary_union, transform

ROOT = Path(os.path.abspath(__file__)).parent
DATA = ROOT / "data"
RAW = json.loads((DATA / "osm_raw.json").read_text(encoding="utf-8"))
META = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))
south, west, north, east = META["bbox_wgs84"]
CLIP = box(west,south,east,north)
PROJECT = Transformer.from_crs(4326,32650,always_xy=True).transform
OUT = DATA / "geojson"
OUT.mkdir(exist_ok=True)
WARNINGS = []


def title(tags):
    return tags.get("name:zh-Hans") or tags.get("name:zh") or tags.get("name") or ""


def poly_category(tags):
    if tags.get("natural") == "water" or tags.get("waterway") == "riverbank":
        return "water"
    if tags.get("leisure") in {"park","garden","nature_reserve"}:
        return "parks"
    if tags.get("landuse") in {"forest","grass","meadow","recreation_ground","village_green","orchard"} or tags.get("natural") in {"wood","scrub","grassland"}:
        return "green"
    if tags.get("building"):
        return "buildings"
    if tags.get("landuse") == "residential":
        return "residential"


def coords(items):
    return [(round(v["lon"],7),round(v["lat"],7)) for v in items if v and "lon" in v]


def area_geometry(element):
    if element["type"] == "way":
        ring = coords(element.get("geometry",[]))
        if len(ring) < 4 or ring[0] != ring[-1]:
            return None
        geometry = Polygon(ring)
    elif element["type"] == "relation":
        outers, inners = [], []
        for member in element.get("members",[]):
            points = coords(member.get("geometry",[]))
            if member.get("type") != "way" or len(points) < 2:
                continue
            (inners if member.get("role") == "inner" else outers).append(LineString(points))
        if not outers:
            return None
        outer_polys = list(polygonize(unary_union(outers)))
        if not outer_polys:
            WARNINGS.append({"id":element["id"],"name":title(element.get("tags",{})),"issue":"Outer boundary cannot form closed polygons"})
            return None
        geometry = unary_union(outer_polys)
        if inners:
            geometry = geometry.difference(unary_union(list(polygonize(unary_union(inners)))))
    else:
        return None
    if not geometry.is_valid:
        geometry = geometry.buffer(0)
    geometry = geometry.intersection(CLIP)
    return geometry if not geometry.is_empty and geometry.geom_type in {"Polygon","MultiPolygon"} else None


def feature(element, geom, category):
    tags = element.get("tags",{})
    return {"type":"Feature", "geometry":mapping(geom), "properties":{
        "osm_id":str(element["id"]), "osm_type":element["type"], "name":title(tags),
        "category":category, "area_m2":round(transform(PROJECT,geom).area,2),
        "label":"", "tags_json":json.dumps(tags,ensure_ascii=False)}}


layers = collections.defaultdict(list)
members_by_category = collections.defaultdict(set)
for e in RAW["elements"]:
    if e["type"] == "relation":
        cat = poly_category(e.get("tags",{}))
        if cat and area_geometry(e) is not None:
            members_by_category[cat].update(m["ref"] for m in e.get("members",[]) if m["type"] == "way")

for e in RAW["elements"]:
    tags = e.get("tags",{})
    category = poly_category(tags)
    if category and not (e["type"] == "way" and e["id"] in members_by_category[category]):
        geometry = area_geometry(e)
        if geometry is not None:
            layers[category].append(feature(e,geometry,category))
    if e["type"] == "way" and tags.get("highway") and tags.get("area") != "yes":
        points = coords(e.get("geometry",[]))
        if len(points) > 1:
            geometry = LineString(points).intersection(CLIP)
            if not geometry.is_empty and geometry.geom_type in {"LineString","MultiLineString"}:
                highway = tags["highway"]
                roadcat = "roads_main" if highway in {"motorway","trunk","primary","secondary","motorway_link","trunk_link","primary_link","secondary_link"} else "roads_other"
                item = feature(e,geometry,roadcat)
                item["properties"]["label"] = item["properties"]["name"] if roadcat == "roads_main" else ""
                layers[roadcat].append(item)
    if e["type"] == "way" and tags.get("waterway") in {"river","canal","stream"}:
        points = coords(e.get("geometry",[]))
        if len(points) > 1:
            geometry = LineString(points).intersection(CLIP)
            if not geometry.is_empty and geometry.geom_type in {"LineString","MultiLineString"}:
                layers["water_lines"].append(feature(e,geometry,"water_lines"))
    if tags.get("boundary") == "administrative" and e["type"] == "relation":
        geometry = area_geometry(e)
        if geometry is not None:
            layers["subdistricts"].append(feature(e,geometry,"subdistricts"))
    if e["type"] == "node" and tags.get("place") in {"quarter","neighbourhood"} and "社区" in title(tags):
        geometry = Point(e["lon"],e["lat"])
        if CLIP.covers(geometry):
            item = feature(e,geometry,"communities")
            item["properties"]["label"] = title(tags)
            layers["communities"].append(item)
    if tags.get("railway") == "station" and tags.get("station") == "subway":
        geometry = Point(e["lon"],e["lat"]) if e["type"] == "node" else area_geometry(e)
        if geometry is not None:
            geometry = geometry.representative_point()
            if CLIP.covers(geometry):
                layers["stations"].append(feature(e,geometry,"stations"))

# Verify park names against the official catalog without changing OSM coordinates or names.
book = xlrd.open_workbook(str(DATA / "fuzhou_parks_2026.xls"))
sheet = book.sheet_by_index(0)
catalog = [sheet.row_values(r) for r in range(3,sheet.nrows) if isinstance(sheet.cell_value(r,0),(float,int))]
def normalized(name):
    return re.sub(r"[\s（）()·]","",name)
official = {normalized(row[1]):row[1] for row in catalog}
for item in layers["parks"]:
    name = item["properties"]["name"]
    match = official.get(normalized(name),"")
    item["properties"]["official_match"] = match
    item["properties"]["label"] = name if name not in {"公园","Fuzhou Panda World"} and item["properties"]["area_m2"] >= 12000 else ""

for item in layers["subdistricts"]:
    # Name placement uses clipped OSM polygons; it is not a new administrative boundary.
    if item["properties"]["area_m2"] >= 180000:
        item["properties"]["label"] = item["properties"]["name"]

for name, features in layers.items():
    (OUT / (name+".geojson")).write_text(json.dumps({"type":"FeatureCollection","features":features},ensure_ascii=False),encoding="utf-8")
with (DATA / "official_park_name_check.csv").open("w",encoding="utf-8-sig",newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["OSM公园名称","官方名录精确匹配","OSM标识"])
    writer.writerows((i["properties"]["name"],i["properties"]["official_match"],i["properties"]["osm_type"]+"/"+i["properties"]["osm_id"]) for i in layers["parks"] if i["properties"]["name"])
summary = {"layers":{name:len(features) for name,features in layers.items()},
           "official_catalog_count":len(catalog),
           "exact_park_name_matches":sum(bool(i["properties"].get("official_match")) for i in layers["parks"]),
           "warnings":WARNINGS, "bbox_wgs84":META["bbox_wgs84"], "projection":"EPSG:32650",
           "community_coverage":"OSM named community points; no complete community administrative boundaries"}
(DATA / "summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
