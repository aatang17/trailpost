"""Build app/l3/walkpoi.json: OpenStreetMap points of interest near the Lantau 3D stages, plus AFCD exit routes tied to distance posts.
Needs: pyproj. Downloads from the Overpass API (retries across mirrors)."""
import json, math, re, urllib.request, urllib.parse, os, pyproj
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
m = json.load(open(os.path.join(ROOT, 'app/l3/meta.json'))); R = json.load(open(os.path.join(ROOT, 'data/research/lantau.json')))
E0, NT = m['x0hk'], m['ytophk']
to_ll = pyproj.Transformer.from_crs(2326, 4326, always_xy=True); to_hk = pyproj.Transformer.from_crs(4326, 2326, always_xy=True)
xs = [p[0] for k in ['lantau-2', 'lantau-3', 'lantau-4'] for p in m['stages'][k]['pts']]; zs = [p[1] for k in ['lantau-2', 'lantau-3', 'lantau-4'] for p in m['stages'][k]['pts']]
lo1, la1 = to_ll.transform(min(xs) + E0 - 400, NT - max(zs) - 400); lo2, la2 = to_ll.transform(max(xs) + E0 + 400, NT - min(zs) + 400)
bb = f"{la1},{lo1},{la2},{lo2}"
q = f"""[out:json][timeout:60];(node["natural"="peak"]({bb});node["tourism"~"viewpoint|information|camp_site|picnic_site"]({bb});
node["amenity"~"shelter|toilets|drinking_water|bench"]({bb});way["amenity"~"shelter|toilets"]({bb});node["highway"="bus_stop"]({bb});node["aerialway"="station"]({bb}););out center tags;"""
d = None
for url in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter', 'https://overpass.private.coffee/api/interpreter']:
    try:
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'TrailpostHK/1.0'}), timeout=90).read()); break
    except Exception as e: print('fail', url, e)
TY = {('natural', 'peak'): 'peak', ('tourism', 'viewpoint'): 'view', ('amenity', 'shelter'): 'shelter', ('amenity', 'toilets'): 'wc', ('amenity', 'drinking_water'): 'water',
      ('tourism', 'camp_site'): 'camp', ('highway', 'bus_stop'): 'bus', ('aerialway', 'station'): 'cable'}
out = []
for e in d['elements']:
    t = e.get('tags', {}); ty = next((v for (a, b), v in TY.items() if t.get(a) == b), None)
    if not ty or (ty == 'peak' and not t.get('name') and not t.get('ele')): continue
    lat = e.get('lat') or e['center']['lat']; lon = e.get('lon') or e['center']['lon']; E, N = to_hk.transform(lon, lat)
    name = t.get('name', ''); en = t.get('name:en') or (name if name and not re.search(r'[一-鿿]', name) else None)
    zh = t.get('name:zh') or (re.findall(r'[一-鿿]+', name)[:1] or [None])[0]
    if en and ty == 'bus' and en.startswith('#'): en = None
    out.append([ty, round(E - E0, 1), round(NT - N, 1), en or '', zh or '', float(t['ele']) if t.get('ele') else None])
ded = []
for o in out:
    same = [p for p in ded if p[0] == o[0] and math.hypot(p[1] - o[1], p[2] - o[2]) < 40]
    if same:
        if not same[0][3] and o[3]: same[0][3], same[0][4] = o[3], o[4]
        continue
    ded.append(o)
exits = []
for s in R['stages']:
    for en, zh in zip(s.get('exits_en', []), s.get('exits_zh', [])):
        for ref in re.findall(r'L0\d\d', en):
            p = [q for q in m['posts'] if q[0] == ref]
            if p: exits.append(['exit', p[0][1], p[0][2], en, zh, None])
json.dump({'poi': ded + exits, 'src': '© OpenStreetMap contributors; exits: AFCD / Trailpost research'}, open(os.path.join(ROOT, 'app/l3/walkpoi.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(ded), 'places,', len(exits), 'exits')
