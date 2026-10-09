"""Two bounded, real-data city examples. Coordinates are WGS84, not geocoded labels."""
CITIES={
 'shanghai':dict(title='上海 · 外滩',english='S H A N G H A I',subtitle='外滩 — 苏州河口',
                 caption='江河相会 · 海派街巷',center=[121.490,31.240],scale=21000,projection=32651,
                 bbox=[31.209,121.460,31.273,121.520],language='zh',grid_seconds=30),
 'losangeles':dict(title='洛城 · 回声湖',english='L O S   A N G E L E S',subtitle='Echo Park — Downtown',
                  caption='湖光 · 街网 · 加州日光',center=[-118.255,34.073],scale=23000,projection=32611,
                  bbox=[34.039,-118.285,34.107,-118.223],language='en',grid_seconds=30)
}
