"""A sharper "patch" inside the wide area of a 3D area: 10 m ground, ~2.4 m aerial photo, OpenStreetMap buildings.

Usage: python3 pipeline/patch/build_patch.py <area dir> <id> <E0> <N0> <E1> <N1> [tiles]
  Lantau Link (Ma Wan, Tsing Yi west, Ting Kau, north-east Lantau):
  FAR_BRIDGES=~/.cache/trailpost/far/lantau_link_osm.json python3 pipeline/patch/build_patch.py app/l3 link 821500 819500 829000 827000 3

Writes into <area dir>:
  patch_<id>.json            grid, local position, buildings ([base, height, tall?, x, z, x, z, ...] like extras.json)
  patch_<id>_h.webp          heights at 10 m, R*256 + G - 100 (sea = -6)
  patch_<id>_t<r>_<c>.webp   aerial photo, one image per tile of the grid (tiles x tiles)
Sources: LandsD 5 m DTM (sea is stored as 0 m), LandsD imagery z16, OpenStreetMap buildings (height, building:levels).
The DTM records bridge decks as ground; with FAR_BRIDGES set, bridge ways are cut out and filled from the land around.
"""
import json, math, os, sys, subprocess, concurrent.futures as cf
import numpy as np, cv2
from PIL import Image, ImageDraw
from pyproj import Transformer

OUT, PID = sys.argv[1], sys.argv[2]; E0, N0, E1, N1 = (float(v) for v in sys.argv[3:7]); NT = int(sys.argv[7]) if len(sys.argv) > 7 else 3
CELL = 10.0; ZOOM = 16; TEXPX = 1024
CACHE = os.environ.get('TP_CACHE', os.path.expanduser('~/.cache/trailpost')); PC = os.path.join(CACHE, 'patch'); os.makedirs(PC, exist_ok=True)
meta = json.load(open(os.path.join(OUT, 'meta.json'))); X0, YTOP = meta['x0hk'], meta['ytophk']
to = Transformer.from_crs(4326, 2326, always_xy=True); inv = Transformer.from_crs(2326, 4326, always_xy=True)
log = lambda *a: print('[patch]', *a, flush=True)
C = int(round((E1 - E0) / CELL)) + 1; R = int(round((N1 - N0) / CELL)) + 1   # grid nodes (shared edges)
log('grid', C, R, 'nodes at', CELL, 'm;', (E1 - E0) / 1000, 'x', (N1 - N0) / 1000, 'km')

# 1. heights from the 5 m DTM: mean of the 5 m cells around each 10 m node; sea (0 m) kept apart
XLL, YLL, CS, NC, NR = 799997.5, 799997.5, 5, 12751, 9601; YT = YLL + NR * CS
cache = f'{PC}/dtm_{PID}.npy'
if os.path.exists(cache): D = np.load(cache)
else:
    r0 = int((YT - (N1 + 10)) / CS); r1 = int((YT - (N0 - 10)) / CS) + 1; c0 = int((E0 - 10 - XLL) / CS); c1 = int((E1 + 10 - XLL) / CS) + 1
    rows = []
    with open(os.path.join(CACHE, 'Whole_HK_DTM_5m.asc')) as f:
        for _ in range(6): f.readline()
        for r, line in enumerate(f):
            if r0 <= r < r1: rows.append(np.array(line.split(), dtype=np.float32)[c0:c1])
            if r >= r1: break
    D = np.array(rows); np.save(cache, D); np.save(f'{PC}/dtm_{PID}_org.npy', np.array([r0, c0]))
r0, c0 = np.load(f'{PC}/dtm_{PID}_org.npy')
E = E0 + np.arange(C) * CELL; N = N1 - np.arange(R) * CELL
ci = (E - XLL) / CS - 0.5 - c0; ri = (YT - N) / CS - 0.5 - r0
RR, CC = np.meshgrid(ri, ci, indexing='ij')
land5 = (D > 0).astype(np.float32); Dm = np.where(D > 0, D, 0).astype(np.float32)
sm = lambda A: cv2.remap(cv2.blur(A, (2, 2)), CC.astype(np.float32), RR.astype(np.float32), cv2.INTER_LINEAR)
lf = sm(land5); H = np.where(lf > 0.5, sm(Dm) / np.maximum(lf, 1e-3), -6.0).astype(np.float32)
# bridge decks out of the ground
bf = os.environ.get('FAR_BRIDGES')
if bf and os.path.exists(bf):
    bimg = Image.new('L', (C, R), 0); bd = ImageDraw.Draw(bimg); nb = 0
    for w in json.load(open(bf))['elements']:
        if 'geometry' not in w or not w.get('tags', {}).get('bridge'): continue
        e_, n_ = to.transform(np.array([p['lon'] for p in w['geometry']]), np.array([p['lat'] for p in w['geometry']]))
        bd.line(list(zip((e_ - E0) / CELL, (N1 - n_) / CELL)), fill=255, width=6); nb += 1
    # 60 m wide lines, grown by 20 m more each side: the deck is 41 m wide and can sit off the OSM line
    bm = cv2.dilate(np.asarray(bimg), np.ones((5, 5), np.uint8)) > 0
    Hf = H.copy(); Hf[bm] = np.nan
    for _ in range(80):  # fill inwards with the average of the known neighbours (smooth, no trench, no ridge)
        nanm = np.isnan(Hf)
        if not nanm.any(): break
        pad = np.pad(Hf, 1, constant_values=np.nan); nbs = np.stack([pad[1:-1, :-2], pad[1:-1, 2:], pad[:-2, 1:-1], pad[2:, 1:-1]])
        with np.errstate(all='ignore'): fill = np.nanmean(nbs, 0)
        Hf[nanm] = fill[nanm]
    Hf[np.isnan(Hf)] = -6; H = np.where(bm, Hf, H).astype(np.float32); log('bridge ways cut out', nb)
H[(H > -6) & (H < 0.5)] = 0.5
v = np.round(H + 100).astype(np.int64)
Image.fromarray(np.stack([(v >> 8) & 255, v & 255, np.zeros_like(v)], -1).astype(np.uint8), 'RGB').save(f'{OUT}/patch_{PID}_h.webp', 'WEBP', lossless=True, method=6)
log('land share', round(float((H > 0).mean()), 3), 'max', float(H.max()))

# 2. aerial photo, z16, one image per tile
def tiles(z, lon0, lon1, lat0, lat1):
    n = 2 ** z; tx = lambda lon: int((lon + 180) / 360 * n); ty = lambda lat: int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return tx(lon0), tx(lon1), ty(lat1), ty(lat0)
lon, lat = inv.transform(np.array([E0, E1, E0, E1]), np.array([N0, N0, N1, N1]))
x0, x1, y0, y1 = tiles(ZOOM, lon.min() - 0.002, lon.max() + 0.002, lat.min() - 0.002, lat.max() + 0.002)
def get(job):
    u, f = job
    if os.path.exists(f) and os.path.getsize(f) > 200: return 0
    for _ in range(3):
        r = subprocess.run(['curl', '-s', '-m', '40', '-o', f, '-w', '%{http_code}', u], capture_output=True, text=True)
        if r.stdout == '200': return 0
    return 1
jobs = [(f'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{ZOOM}/{x}/{y}.png', f'{PC}/img{ZOOM}_{x}_{y}.png') for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
with cf.ThreadPoolExecutor(10) as ex: fails = sum(ex.map(get, jobs))
log('photo tiles', len(jobs), 'fails', fails)
mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256, 3), np.uint8)
for x in range(x0, x1 + 1):
    for y in range(y0, y1 + 1):
        t = cv2.imread(f'{PC}/img{ZOOM}_{x}_{y}.png', cv2.IMREAD_COLOR)
        if t is not None: mos[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = t
n = 2 ** ZOOM; tw = (E1 - E0) / NT; thh = (N1 - N0) / NT; total = 0
for tr in range(NT):
    for tc in range(NT):
        ex0 = E0 + tc * tw; ny1 = N1 - tr * thh
        gx = ex0 + (np.arange(TEXPX) + 0.5) * tw / TEXPX; gy = ny1 - (np.arange(TEXPX) + 0.5) * thh / TEXPX; GX, GY = np.meshgrid(gx, gy); lo, la = inv.transform(GX, GY)
        mx = ((lo + 180) / 360 * n - x0) * 256 - 0.5; my = ((1 - np.arcsinh(np.tan(np.radians(la))) / math.pi) / 2 * n - y0) * 256 - 0.5
        tex = cv2.remap(mos, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        fn = f'{OUT}/patch_{PID}_t{tr}_{tc}.webp'; cv2.imwrite(fn, tex, [cv2.IMWRITE_WEBP_QUALITY, 78]); total += os.path.getsize(fn)
log('photo', NT * NT, 'images', round(total / 1e6, 2), 'MB,', round(tw / TEXPX, 2), 'm per pixel')

# 3. buildings from OpenStreetMap
bfile = f'{PC}/bld_{PID}.json'
if not os.path.exists(bfile):
    q = f'[out:json][timeout:180];way["building"]({lat.min()},{lon.min()},{lat.max()},{lon.max()});out geom tags;'
    for mirror in ['https://overpass.kumi.systems/api/interpreter', 'https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter']:
        r = subprocess.run(['curl', '-s', '-m', '240', '-o', bfile + '.tmp', '-w', '%{http_code}', '--data-urlencode', 'data=' + q, mirror], capture_output=True, text=True)
        if r.stdout == '200':
            try: json.load(open(bfile + '.tmp')); os.replace(bfile + '.tmp', bfile); break
            except Exception: pass
def ground5(e, nn):
    r = int(round((YT - nn) / CS - 0.5)) - r0; c = int(round((e - XLL) / CS - 0.5)) - c0
    return float(D[r, c]) if 0 <= r < D.shape[0] and 0 <= c < D.shape[1] else 0.0
bl = []; hs = []
for w in json.load(open(bfile))['elements']:
    g = w.get('geometry'); t = w.get('tags', {})
    if not g or len(g) < 4: continue
    ee, nn = to.transform(np.array([p['lon'] for p in g]), np.array([p['lat'] for p in g]))
    if ee.max() < E0 or ee.min() > E1 or nn.max() < N0 or nn.min() > N1: continue
    try: h = float(str(t.get('height', '')).replace('m', '').strip())
    except ValueError: h = None
    if not h:
        try: h = float(t.get('building:levels')) * 3.1 + 2
        except (TypeError, ValueError): h = None
    if not h: h = {'house': 7.0, 'detached': 7.0, 'hut': 3.5, 'roof': 4.0, 'garage': 3.5, 'industrial': 12.0, 'warehouse': 12.0, 'school': 16.0}.get(t.get('building'), 9.0)
    base = min(ground5(a, b) for a, b in zip(ee, nn)); base = max(base, 0.5)
    pts = []
    for a, b in zip(ee[:-1], nn[:-1]): pts += [round(a - X0, 1), round(YTOP - b, 1)]
    bl.append([round(base, 1), round(h, 1), 1 if h > 60 else 0] + pts); hs.append(h)
log('buildings', len(bl), 'tallest', max(hs) if hs else 0, 'over 60 m:', sum(1 for h in hs if h > 60))
json.dump({'id': PID, 'E0': E0, 'N0': N0, 'E1': E1, 'N1': N1, 'cell': CELL, 'cols': C, 'rows': R, 'tiles': NT, 'buildings': bl,
           'source': 'LandsD 5 m DTM; LandsD aerial photo z16; OpenStreetMap buildings'},
          open(f'{OUT}/patch_{PID}.json', 'w'), separators=(',', ':'))
log('done', f'{OUT}/patch_{PID}.json', os.path.getsize(f'{OUT}/patch_{PID}.json') // 1024, 'KB')
