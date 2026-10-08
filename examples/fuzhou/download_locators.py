"""Cache published GeoAtlas boundaries for national/provincial/city locator circles."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request
from datetime import datetime,timezone

ROOT = Path(os.path.abspath(__file__)).parent / "data/locators"


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    records = []
    for code,level in [(100000,"national provinces"),(350000,"Fujian prefectures"),(350100,"Fuzhou counties")]:
        url = f"https://geo.datav.aliyun.com/areas_v3/bound/{code}_full.json"
        path = ROOT / f"{code}_full.json"
        if not path.exists():
            request = urllib.request.Request(url,headers={"User-Agent":"InkMap educational cartography example"})
            with urllib.request.urlopen(request,timeout=60) as response:
                raw = response.read()
            document = json.loads(raw)
            assert document["type"] == "FeatureCollection"
            path.write_bytes(raw)
        raw = path.read_bytes()
        features = json.loads(raw)["features"]
        records.append({"code":code,"level":level,"url":url,"features":len(features),
                        "sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
    metadata = {"source":"Alibaba Cloud DataV.GeoAtlas / Amap","version":"areas_v3",
                "source_page":"https://datav.aliyun.com/portal/school/atlas/atlas_aigc",
                "publisher_update":"2021-05","retrieved":datetime.now(timezone.utc).isoformat(),
                "usage":"Publisher states for learning/exchange; used only for the requested example locators",
                "coordinate_note":"Publisher coordinates retained in separate small-scale locator maps; not merged with OSM feature data",
                "records":records}
    (ROOT / "metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(metadata,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
