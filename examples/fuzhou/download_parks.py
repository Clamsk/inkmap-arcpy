"""Download the official 2026 park-name catalog; it does not provide survey boundaries."""
import hashlib,json,os
from pathlib import Path
from urllib.request import Request,urlopen
from datetime import datetime,timezone

ROOT=Path(os.path.abspath(__file__)).parent/'data'
URL='https://ylj.fuzhou.gov.cn/zwgk/ztzl/gyjq/202607/P020260728403151673512.xls'

if __name__=='__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    path=ROOT/'fuzhou_parks_2026.xls'
    if path.exists(): raise FileExistsError('Catalog already cached; do not silently replace it')
    with urlopen(Request(URL,headers={'User-Agent':'InkMap educational cartography example'}),timeout=60) as response:
        raw=response.read()
    if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')): raise ValueError('Expected an XLS compound document')
    path.write_bytes(raw)
    (ROOT/'parks_metadata.json').write_text(json.dumps(dict(url=URL,retrieved=datetime.now(timezone.utc).isoformat(),
               sha256=hashlib.sha256(raw).hexdigest(),usage='Park names only; geometry from OSM'),indent=2),encoding='utf-8')
    print(f'Cached park catalog: {len(raw)} bytes')
