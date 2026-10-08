"""Download a bounded OSM extract for the Fuzhou cartographic example."""
import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

BBOX = (26.020, 119.258, 26.110, 119.338)  # south, west, north, east; WGS84
box = ",".join(map(str, BBOX))
QUERY = f'''[out:json][timeout:180][maxsize:134217728];
(
  way["highway"]({box});
  nwr["natural"="water"]({box});
  nwr["waterway"="riverbank"]({box});
  way["waterway"~"^(river|canal|stream)$"]({box});
  nwr["leisure"~"^(park|garden|nature_reserve)$"]({box});
  nwr["landuse"~"^(forest|grass|meadow|recreation_ground|village_green|orchard)$"]({box});
  nwr["natural"~"^(wood|scrub|grassland)$"]({box});
  way["building"]({box});
  relation["building"]({box});
  nwr["place"~"^(suburb|quarter|neighbourhood)$"]({box});
  nwr["landuse"="residential"]["name"]({box});
  relation["boundary"="administrative"]["admin_level"~"^(8|9|10|11|12)$"]({box});
  nwr["railway"="station"]["station"="subway"]({box});
);
out body geom;
'''


def download(output, endpoint):
    out = Path(os.path.abspath(output))
    out.mkdir(parents=True, exist_ok=True)
    target = out / "osm_raw.json"
    if target.exists():
        raise FileExistsError(f"Refusing to replace cached extract: {target}")
    (out / "query.overpassql").write_text(QUERY, encoding="utf-8")
    req = urllib.request.Request(endpoint, data=urllib.parse.urlencode({"data":QUERY}).encode(),
                                 headers={"User-Agent":"InkMap-ArcPy-Fuzhou-Example/0.1 (bounded cartographic extract)",
                                          "Content-Type":"application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=230) as response:
        payload = response.read()
    data = json.loads(payload)
    if data.get("remark"):
        raise RuntimeError(f"Overpass reported an incomplete extract: {data['remark']}")
    if not data.get("elements"):
        raise RuntimeError("The extract contains no elements")
    target.write_bytes(payload)
    metadata = {"source":"OpenStreetMap", "endpoint":endpoint, "bbox_wgs84":list(BBOX),
                "retrieval_date":datetime.now(timezone.utc).isoformat(), "osm_timestamp":data.get("osm3s",{}).get("timestamp_osm_base"),
                "element_count":len(data["elements"]), "bytes":len(payload),
                "copyright":"https://www.openstreetmap.org/copyright", "license":"ODbL 1.0"}
    (out / "metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(metadata,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--endpoint", default="https://overpass-api.de/api/interpreter")
    args = parser.parse_args()
    download(args.output, args.endpoint)
