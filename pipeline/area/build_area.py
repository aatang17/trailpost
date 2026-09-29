#!/usr/bin/env python3
"""Build the 3D data for one area of Hong Kong, in the same format the viewer uses for Lantau.

Usage:
  python3 pipeline/area/build_area.py drag --stages hktrail-7,hktrail-8 --margin 1500

Writes app/l3/<area>/ :
  meta.json, chunks.json          grid, trail stages, distance posts, labels; photo chunk layout
  dem5/dem10.webp                  ground height (LiDAR DTM) : R*256+G-10 = metres
  can5/can10.webp                  tree canopy height (DSM - DTM) : grey/4 = metres
  ao.webp                          valley shading (sky view)
  h_<r>_<c>.webp, overview.webp    aerial photos (LandsD), sharp chunks + one overview
  map.webp                         painted map look (height tint, hillshade, contours, trails)
  extras.json                      OSM buildings as simple blocks
  far.json, farh.webp, fartex.webp the wider area (40 m grid, ~14 km radius)
  walkpoi.json                     shelters, toilets, viewpoints, peaks, bus stops, exits
Downloads are cached in $TP_CACHE (default: ~/.cache/trailpost).

Sources: CEDD 2020 LiDAR DSM/DTM (Esri China HK ArcGIS tiles), LandsD 5 m DTM (for the far view and gaps),
LandsD aerial imagery (mapapi.geodata.gov.hk), OpenStreetMap (Overpass), AFCD routes (data/geo/data.js).
"""
import argparse, json, math, os, re, subprocess, urllib.parse, urllib.request, concurrent.futures as cf
import numpy as np, cv2, lerc, pyproj
from PIL import Image, ImageDraw
from scipy import ndimage as nd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ap = argparse.ArgumentParser()
ap.add_argument('area'); ap.add_argument('--stages', required=True); ap.add_argument('--margin', type=float, default=1500)
ap.add_argument('--far', type=float, default=14000, help='radius of the wider view in metres')
ap.add_argument('--peak-min', type=float, default=120, help='label peaks at least this high (m)')
ap.add_argument('--peak-keep', default='', help='comma-separated peak names to label whatever their height')
ap.add_argument('--dtm-asc', default=os.environ.get('HK_DTM_ASC', os.path.expanduser('~/.cache/trailpost/Whole_HK_DTM_5m.asc')))
A = ap.parse_args()
CACHE = os.environ.get('TP_CACHE', os.path.expanduser('~/.cache/trailpost')); os.makedirs(CACHE, exist_ok=True)
OUT = os.path.join(ROOT, 'app', 'l3', A.area); os.makedirs(OUT, exist_ok=True)
to_hk = pyproj.Transformer.from_crs(4326, 2326, always_xy=True); to_ll = pyproj.Transformer.from_crs(2326, 4326, always_xy=True)
to_3857 = pyproj.Transformer.from_crs(2326, 3857, always_xy=True)
CS = 5.0; XLL, YLL, NC, NR = 799997.5, 799997.5, 12751, 9601; YTOP_HK = YLL + NR * CS

def log(*a): print('[area]', *a, flush=True)
def curl(url, path, tries=3):
    if os.path.exists(path) and os.path.getsize(path) > 0: return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for _ in range(tries):
        r = subprocess.run(['curl', '-s', '-m', '60', '-o', path, '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.stdout == '200': return True
        if r.stdout == '404': open(path, 'wb').close(); return False
    if os.path.exists(path): os.remove(path)
    return False
def tile_xy(lon, lat, z):
    n = 2 ** z; return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n

# ---------- routes and the area box ----------
s = open(os.path.join(ROOT, 'data/geo/data.js')).read(); i = s.index('window.HK_ROUTES='); j = s.index(';\n', i)
ROUTES = json.loads(s[i + len('window.HK_ROUTES='):j])['routes']; byid = {r['id']: r for r in ROUTES}
want = A.stages.split(',')
segs_of = lambda r: r.get('segs') or ([r['line']] if 'line' in r else [])
pts = [p for k in want for seg in segs_of(byid[k]) for p in seg]
E, N = to_hk.transform([p[1] for p in pts], [p[0] for p in pts])
c0 = int(math.floor((min(E) - A.margin - XLL) / CS)); c1 = int(math.ceil((max(E) + A.margin - XLL) / CS))
r0 = int(math.floor((YTOP_HK - (max(N) + A.margin)) / CS)); r1 = int(math.ceil((YTOP_HK - (min(N) - A.margin)) / CS))
C, R = c1 - c0, r1 - r0; X0 = XLL + c0 * CS; YTOP = YTOP_HK - r0 * CS
log(f'grid {C}x{R} cells ({C*CS/1000:.1f} x {R*CS/1000:.1f} km), x0 {X0} ytop {YTOP}')
Ec = X0 + (np.arange(C) + 0.5) * CS; Nc = YTOP - (np.arange(R) + 0.5) * CS; EE, NN = np.meshgrid(Ec, Nc)
LON, LAT = to_ll.transform(EE, NN)
lon0, lat0 = to_ll.transform(X0, YTOP - R * CS); lon1, lat1 = to_ll.transform(X0 + C * CS, YTOP)
def px(lat, lon): e, n = to_hk.transform(lon, lat); return ((e - X0) / CS, (YTOP - n) / CS)

# ---------- 1. LandsD 5 m DTM (asc) for gaps and the far view ----------
def read_asc_rows(rows, cols):
    """rows, cols: arrays of asc row/col indices; returns values (nan outside)"""
    need = {}
    for k, r in enumerate(rows):
        if 0 <= r < NR: need.setdefault(int(r), []).append(k)
    out = np.full((len(rows), len(cols)), np.nan, np.float32); ok = (cols >= 0) & (cols < NC)
    with open(A.dtm_asc) as f:
        for _ in range(6): f.readline()
        for r, line in enumerate(f):
            if r in need:
                a = np.array(line.split(), dtype=np.float32); v = np.full(len(cols), np.nan, np.float32); v[ok] = a[cols[ok]]
                for k in need[r]: out[k] = v
            if r > max(need): break
    out[out <= -9000] = np.nan; return out
cache_asc = os.path.join(CACHE, f'asc_{A.area}.npy')
if os.path.exists(cache_asc): ASC = np.load(cache_asc)
else: ASC = read_asc_rows(np.arange(r0, r1), np.arange(c0, c1)); np.save(cache_asc, ASC)
log('asc read', ASC.shape)

# ---------- 2. CEDD 2020 LiDAR DSM / DTM (LERC tiles, web mercator z15) ----------
U = 'https://tiles.arcgis.com/tiles/6j1KwZfY2fZrfNMR/arcgis/rest/services'; Z = 15
tx0, ty1 = tile_xy(lon0, lat0, Z); tx1, ty0 = tile_xy(lon1, lat1, Z); tx0, tx1, ty0, ty1 = int(tx0), int(tx1), int(ty0), int(ty1)
jobs = [(sv, x, y) for sv in ('DSM', 'DTM') for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
def get_lerc(j):
    sv, x, y = j; return curl(f'{U}/{sv}_2020_5m_WEL/ImageServer/tile/{Z}/{y}/{x}', os.path.join(CACHE, 'lidar', f'{sv}_{x}_{y}.lerc'))
with cf.ThreadPoolExecutor(10) as ex: list(ex.map(get_lerc, jobs))
RES = 4.77731426794937; O = 20037508.342787
def mosaic(sv):
    M = np.full(((ty1 - ty0 + 1) * 256 + 1, (tx1 - tx0 + 1) * 256 + 1), np.nan, np.float32)
    for x in range(tx0, tx1 + 1):
        for y in range(ty0, ty1 + 1):
            p = os.path.join(CACHE, 'lidar', f'{sv}_{x}_{y}.lerc')
            if not os.path.exists(p) or os.path.getsize(p) == 0: continue
            r = lerc.decode(open(p, 'rb').read()); a = r[1].astype(np.float32)
            if len(r) > 2 and r[2] is not None and np.size(r[2]) == a.size: a[np.asarray(r[2]).reshape(a.shape) == 0] = np.nan
            a[(a < -100) | (a > 2000)] = np.nan
            j0, i0 = (y - ty0) * 256, (x - tx0) * 256; sub = M[j0:j0 + a.shape[0], i0:i0 + a.shape[1]]
            M[j0:j0 + a.shape[0], i0:i0 + a.shape[1]] = np.where(np.isnan(a), sub, a)
    return M
MX, MY = to_3857.transform(EE, NN); fi = (MX + O) / RES - tx0 * 256; fj = (O - MY) / RES - ty0 * 256
def samp(M):
    i0 = np.clip(np.floor(fi).astype(int), 0, M.shape[1] - 2); j0 = np.clip(np.floor(fj).astype(int), 0, M.shape[0] - 2); a = fi - i0; b = fj - j0
    return (M[j0, i0] * (1 - a) * (1 - b) + M[j0, i0 + 1] * a * (1 - b) + M[j0 + 1, i0] * (1 - a) * b + M[j0 + 1, i0 + 1] * a * b).astype(np.float32)
DSM, DTM = samp(mosaic('DSM')), samp(mosaic('DTM'))
log('lidar coverage dtm', round(float(np.isfinite(DTM).mean()), 3))

# ---------- 3. land / reservoir masks from the app's base map ----------
base = json.load(open(os.path.join(ROOT, 'data/geo/basemap.json')))
def polys(g): return g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
def inbox(poly): return any(lat0 - 0.02 < la < lat1 + 0.02 and lon0 - 0.02 < lo < lon1 + 0.02 for lo, la in poly[0])
SS = 3; mimg = Image.new('L', (C * SS, R * SS), 0); md = ImageDraw.Draw(mimg)
ring = lambda co: [(px(la, lo)[0] * SS, px(la, lo)[1] * SS) for lo, la in co]
for poly in polys(base['land']):
    if inbox(poly):
        md.polygon(ring(poly[0]), fill=255)
        for h in poly[1:]: md.polygon(ring(h), fill=0)
rimg = Image.new('L', (C * SS, R * SS), 0); rd = ImageDraw.Draw(rimg)
for f in base.get('res', {}).get('features', []):
    for poly in polys(f['geometry']):
        if inbox(poly): rd.polygon(ring(poly[0]), fill=255)
LAND = np.asarray(mimg.resize((C, R), Image.LANCZOS)).astype(np.float32) / 255
RESV = np.asarray(rimg.resize((C, R), Image.LANCZOS)).astype(np.float32) / 255
sea = LAND < 0.5

# ---------- 4. OpenStreetMap: buildings, big roads, peaks, places people stop ----------
def overpass(q, name):
    p = os.path.join(CACHE, f'osm_{A.area}_{name}.json')
    if os.path.exists(p): return json.load(open(p))
    for url in ['https://overpass.private.coffee/api/interpreter', 'https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']:
        try:
            d = urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'TrailpostHK/1.0'}), timeout=180).read()
            json.dump(json.loads(d), open(p, 'w')); return json.loads(d)
        except Exception as e: log('overpass fail', url, e)
    raise SystemExit('Overpass unavailable')
bb = f'{lat0},{lon0},{lat1},{lon1}'
osm = overpass(f'[out:json][timeout:170];(way["building"]({bb});way["highway"~"motorway|trunk|primary|secondary"]({bb});way["bridge"]({bb});'
               f'node["natural"="peak"]({bb});node["tourism"~"viewpoint|camp_site|picnic_site"]({bb});node["amenity"~"shelter|toilets|drinking_water"]({bb});'
               f'way["amenity"~"shelter|toilets"]({bb});node["highway"="bus_stop"]({bb});node["amenity"="ferry_terminal"]({bb}););out geom tags;', 'main')['elements']
log('osm elements', len(osm))

# ---------- 5. ground, canopy, masks ----------
ground = np.where(np.isfinite(DTM), DTM, np.nan_to_num(ASC, nan=0.0)).astype(np.float32)
ground[sea] = -6.0; ground[(~sea) & (ground < 0.3)] = 0.3
can = np.nan_to_num(DSM - DTM, nan=0.0); can[sea] = 0; can = np.clip(can, 0, 60); can[can < 1.2] = 0
bimg = Image.new('L', (C, R), 0); bd = ImageDraw.Draw(bimg); nb = 0
for e in osm:
    if e['type'] == 'way' and 'building' in e.get('tags', {}) and 'geometry' in e and len(e['geometry']) > 2:
        bd.polygon([px(p['lat'], p['lon']) for p in e['geometry']], fill=255); nb += 1
bmask = nd.binary_dilation(np.asarray(bimg) > 0, iterations=2)
wimg = Image.new('L', (C, R), 0); wd = ImageDraw.Draw(wimg)
for e in osm:
    t = e.get('tags', {})
    if e['type'] == 'way' and 'geometry' in e and ('highway' in t or t.get('bridge')):
        wd.line([px(p['lat'], p['lon']) for p in e['geometry']], fill=255, width=5)
for r in ROUTES:
    for seg in segs_of(r):
        q = [px(a, b) for a, b in seg]
        if any(0 <= x < C and 0 <= y < R for x, y in q): wd.line(q, fill=255, width=2)
can[bmask | (np.asarray(wimg) > 0)] = 0
can = nd.median_filter(can, size=3)
# ease tree heights down towards the hiking trails (0 within 4 m, full from 20 m), so walk mode shows a bank of
# vegetation beside the path rather than a sheer 5 m wall at its edge
timg = Image.new('L', (C, R), 0); td = ImageDraw.Draw(timg)
for r in ROUTES:
    for seg in segs_of(r):
        q = [px(a, b) for a, b in seg]
        if any(0 <= x < C and 0 <= y < R for x, y in q): td.line(q, fill=255, width=1)
tdist = nd.distance_transform_edt(np.asarray(timg) == 0) * CS
ramp = np.clip((tdist - 4) / 16, 0, 1); can *= (ramp * ramp * (3 - 2 * ramp)).astype(np.float32)
log('buildings', nb, 'trees >3 m on land %', round(float(((can > 3) & ~sea).sum() / max(1, (~sea).sum()) * 100), 1))

# ---------- 6. valley shading (sky-view factor) ----------
S = np.where(sea, 0, ground + can).astype(np.float32); dirs = 16; steps = [5, 10, 15, 25, 35, 50, 70, 100, 140, 200, 280, 400]; acc = np.zeros((R, C), np.float32)
for k in range(dirs):
    a = 2 * math.pi * k / dirs; dx, dy = math.cos(a), math.sin(a); best = np.zeros((R, C), np.float32)
    for st in steps:
        ox, oy = int(round(dx * st / CS)), int(round(dy * st / CS))
        if ox == 0 and oy == 0: continue
        sh = np.full((R, C), -1e4, np.float32)
        ys = slice(max(0, -oy), R - max(0, oy)); yd = slice(max(0, oy), R - max(0, -oy)); xs = slice(max(0, -ox), C - max(0, ox)); xd = slice(max(0, ox), C - max(0, -ox))
        sh[ys, xs] = S[yd, xd]; best = np.maximum(best, (sh - S) / (math.hypot(ox, oy) * CS))
    acc += np.sin(np.arctan(np.maximum(best, 0)))
ao = 0.30 + 0.70 * np.clip(1 - acc / dirs, 0, 1) ** 1.3; ao[sea] = 1.0

# ---------- 7. write height, canopy and shading images ----------
def enc_dem(G, path):
    v = np.clip(np.round(G) + 10, 0, 65535).astype(np.int64)
    Image.fromarray(np.stack([(v >> 8) & 255, v & 255, np.zeros_like(v)], -1).astype(np.uint8), 'RGB').save(path, 'WEBP', lossless=True, method=6)
def enc_can(Cn, path, q=80):
    g = np.clip(np.round(Cn * 4), 0, 255).astype(np.uint8); Image.fromarray(g, 'L').convert('RGB').save(path, 'WEBP', quality=q, method=6)
enc_dem(ground, f'{OUT}/dem5.webp'); enc_dem(ground[::2, ::2], f'{OUT}/dem10.webp')
enc_can(can, f'{OUT}/can5.webp'); enc_can(nd.uniform_filter(can, 2)[::2, ::2], f'{OUT}/can10.webp')
Image.fromarray((ao * 255).astype(np.uint8), 'L').convert('RGB').save(f'{OUT}/ao.webp', 'WEBP', quality=80, method=6)

# ---------- 8. aerial photos (LandsD imagery, z17 ≈ 1.1 m/pixel) ----------
ZI = 17; ix0, iy1 = tile_xy(lon0, lat0, ZI); ix1, iy0 = tile_xy(lon1, lat1, ZI); ix0, ix1, iy0, iy1 = int(ix0), int(ix1), int(iy0), int(iy1)
ijobs = [(x, y) for x in range(ix0, ix1 + 1) for y in range(iy0, iy1 + 1)]
with cf.ThreadPoolExecutor(12) as ex:
    list(ex.map(lambda t: curl(f'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{ZI}/{t[0]}/{t[1]}.png', os.path.join(CACHE, 'img17', f'{t[0]}_{t[1]}.png')), ijobs))
mos = np.zeros(((iy1 - iy0 + 1) * 256, (ix1 - ix0 + 1) * 256, 3), np.uint8)
for x, y in ijobs:
    t = cv2.imread(os.path.join(CACHE, 'img17', f'{x}_{y}.png'), cv2.IMREAD_COLOR)
    if t is not None: mos[(y - iy0) * 256:(y - iy0 + 1) * 256, (x - ix0) * 256:(x - ix0 + 1) * 256] = t
log('imagery tiles', len(ijobs))
colb = list(range(0, C - 1, 380)) + [C - 1]; rowb = list(range(0, R - 1, 360)) + [R - 1]
if colb[-1] - colb[-2] < 60 and len(colb) > 2: colb.pop(-2)
if rowb[-1] - rowb[-2] < 60 and len(rowb) > 2: rowb.pop(-2)
chunks = []; full = np.zeros(((R - 1) * 2, (C - 1) * 2, 3), np.uint8)
for ri in range(len(rowb) - 1):
    for ci in range(len(colb) - 1):
        ca, cb, ra, rb = colb[ci], colb[ci + 1], rowb[ri], rowb[ri + 1]
        xs, xe = (ca + 0.5) * CS, (cb + 0.5) * CS; zs, ze = (ra + 0.5) * CS, (rb + 0.5) * CS; Wp, Hp = (cb - ca) * 4, (rb - ra) * 4
        GX, GZ = np.meshgrid(xs + (np.arange(Wp) + 0.5) * (xe - xs) / Wp, zs + (np.arange(Hp) + 0.5) * (ze - zs) / Hp)
        lo, la = to_ll.transform(X0 + GX, YTOP - GZ); n = 2 ** ZI
        mx = ((lo + 180) / 360 * n - ix0) * 256 - 0.5; my = ((1 - np.arcsinh(np.tan(np.radians(la))) / math.pi) / 2 * n - iy0) * 256 - 0.5
        hi = cv2.remap(mos, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        name = f'{ri}_{ci}'; cv2.imwrite(f'{OUT}/h_{name}.webp', hi, [cv2.IMWRITE_WEBP_QUALITY, 74])
        full[ra * 2:rb * 2, ca * 2:cb * 2] = cv2.resize(hi, ((cb - ca) * 2, (rb - ra) * 2), interpolation=cv2.INTER_AREA)
        chunks.append({'id': name, 'c0': ca, 'c1': cb, 'r0': ra, 'r1': rb})
OVW = min(2048, full.shape[1]); ov = cv2.resize(full, (OVW, round(OVW * full.shape[0] / full.shape[1])), interpolation=cv2.INTER_AREA)
cv2.imwrite(f'{OUT}/overview.webp', ov, [cv2.IMWRITE_WEBP_QUALITY, 78])
json.dump({'chunks': chunks, 'uvw': (C - 1) * CS, 'uvh': (R - 1) * CS}, open(f'{OUT}/chunks.json', 'w'))

# ---------- 9. painted map look ----------
Hm = np.maximum(ground, 0); stops = [(0, (122, 168, 104)), (120, (140, 180, 112)), (300, (176, 190, 132)), (500, (201, 191, 146)), (700, (196, 174, 140)), (950, (184, 164, 146))]
col = np.zeros(Hm.shape + (3,), np.float32)
for (h0, k0), (h1, k1) in zip(stops, stops[1:]):
    m = (Hm >= h0) & ((Hm < h1) if h1 < 950 else True); t = np.clip((Hm - h0) / (h1 - h0), 0, 1)[m][:, None]; col[m] = np.array(k0) * (1 - t) + np.array(k1) * t
gy, gx = np.gradient(Hm, CS); sl = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
hs = np.clip(math.sin(math.radians(40)) * np.cos(sl) + math.cos(math.radians(40)) * np.sin(sl) * np.cos(math.radians(315) - asp), 0, 1); col *= (0.72 + 0.4 * hs)[..., None]
for stp, f in ((50, 0.86), (100, 0.72)):
    b = np.floor(Hm / stp); m = np.zeros(Hm.shape, bool); m[:, 1:] |= b[:, 1:] != b[:, :-1]; m[1:, :] |= b[1:, :] != b[:-1, :]; col[m & (Hm > 2)] *= f
col[sea] = (150, 196, 218); col = col * (1 - RESV[..., None]) + np.array([120, 172, 206]) * RESV[..., None]
big = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((C * 2, R * 2), Image.BICUBIC); bdw = ImageDraw.Draw(big)
TRC = {'lantau': (214, 84, 24), 'maclehose': (178, 60, 30), 'wilson': (120, 80, 160), 'hktrail': (30, 100, 170)}
for r in ROUTES:
    for seg in segs_of(r):
        q = [(px(a, b)[0] * 2, px(a, b)[1] * 2) for a, b in seg]
        if any(0 <= x < C * 2 and 0 <= y < R * 2 for x, y in q):
            bdw.line(q, fill=(255, 255, 255), width=7, joint='curve'); bdw.line(q, fill=TRC.get(r.get('trail'), (200, 90, 30)), width=4, joint='curve')
pm = cv2.cvtColor(np.asarray(big.resize(((C - 1), (R - 1)), Image.LANCZOS)), cv2.COLOR_RGB2BGR)
cv2.imwrite(f'{OUT}/map.webp', cv2.resize(pm, (ov.shape[1], ov.shape[0]), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_WEBP_QUALITY, 82])

# ---------- 10. meta: stages, posts, labels ----------
def hat(x, z):
    c = min(max(x / CS - 0.5, 0), C - 1.001); r = min(max(z / CS - 0.5, 0), R - 1.001); i, j = int(r), int(c); fr, fc = r - i, c - j
    return float(ground[i, j] * (1 - fr) * (1 - fc) + ground[i, j + 1] * (1 - fr) * fc + ground[i + 1, j] * fr * (1 - fc) + ground[i + 1, j + 1] * fr * fc)
def w(lat, lon): c, r = px(lat, lon); return [round(c * CS, 1), round(r * CS, 1), round(hat(c * CS, r * CS), 1)]
inside = lambda lat, lon: 0 <= px(lat, lon)[0] < C and 0 <= px(lat, lon)[1] < R
meta = {'cols': C, 'rows': R, 'cs': CS, 'maxH': float(ground.max()), 'source': 'CEDD 2020 LiDAR and Lands Department 5 m Digital Terrain Model',
        'stages': {}, 'posts': [], 'labels': [], 'x0hk': X0, 'ytophk': YTOP, 'area': A.area, 'main': want}
for r in ROUTES:
    sg = segs_of(r)
    if not sg or not all(inside(a, b) for seg in sg for a, b in seg[::5]): continue
    q = []; last = None
    for seg in sg:
        for a, b in seg:
            p = w(a, b)
            if last is None or math.hypot(p[0] - last[0], p[1] - last[1]) >= 8: q.append(p); last = p
    meta['stages'][r['id']] = {'pts': q, **{k: r.get(k) for k in ('n', 'start_en', 'start_zh', 'end_en', 'end_zh', 'km', 'hours', 'trail')}}
    for p in r.get('post_list', []):
        if inside(p[1], p[2]) and not any(x[0] == p[0] for x in meta['posts']): meta['posts'].append([p[0]] + w(p[1], p[2]))
for e in osm:
    t = e.get('tags', {})
    if e['type'] == 'node' and t.get('natural') == 'peak' and t.get('name') and inside(e['lat'], e['lon']):
        nm = t['name']; en = t.get('name:en') or ' '.join(x for x in re.split(r'([一-鿿]+)', nm) if x and not re.match(r'[一-鿿]', x)).strip() or nm
        zh = t.get('name:zh') or (re.findall(r'[一-鿿]+', nm)[:1] or [en])[0]
        p = w(e['lat'], e['lon']); ele = t.get('ele'); h = round(float(ele)) if ele and re.match(r'^[\d.]+$', ele) else round(p[2])
        keep = [k.strip() for k in A.peak_keep.split(',') if k.strip()]
        if en == zh and en not in keep: continue  # no English name in OSM: leave it out rather than show Chinese twice
        if h >= A.peak_min or en in keep: meta['labels'].append({'en': en, 'zh': zh, 'p': p, 'kind': 'peak', 'h': h, 'dem': round(p[2])})
for k in want:
    r = byid[k]; sg = segs_of(r)
    for p, en, zh in ((sg[0][0], r.get('start_en'), r.get('start_zh')), (sg[-1][-1], r.get('end_en'), r.get('end_zh'))):
        if en and not any(l['en'] == en for l in meta['labels']): meta['labels'].append({'en': en, 'zh': zh, 'p': w(*p), 'kind': 'place'})
json.dump(meta, open(f'{OUT}/meta.json', 'w'), ensure_ascii=False, separators=(',', ':'))
log('stages', list(meta['stages']), 'posts', len(meta['posts']), 'labels', [l['en'] for l in meta['labels']])

# ---------- 11. buildings as simple blocks ----------
blds = []
for e in osm:
    t = e.get('tags', {})
    if e['type'] != 'way' or 'building' not in t or 'geometry' not in e or len(e['geometry']) < 4: continue
    q = [px(p['lat'], p['lon']) for p in e['geometry']][:-1]
    if not all(0 <= x < C and 0 <= y < R for x, y in q): continue
    lv = t.get('building:levels'); ht = t.get('height')
    try: h = float(re.findall(r'[\d.]+', ht)[0]) if ht else (float(lv) * 3.2 if lv else 7.0)
    except Exception: h = 7.0
    xs = [x * CS for x, y in q]; zs = [y * CS for x, y in q]; base = min(hat(x, z) for x, z in zip(xs, zs))
    blds.append([round(base, 1), round(min(h, 250), 1), 1 if h >= 30 else 0] + [round(v, 1) for xz in zip(xs, zs) for v in xz])
json.dump({'buildings': blds, 'cable': [], 'towers': []}, open(f'{OUT}/extras.json', 'w'), separators=(',', ':'))

# ---------- 12. walk markers ----------
TY = {('natural', 'peak'): 'peak', ('tourism', 'viewpoint'): 'view', ('amenity', 'shelter'): 'shelter', ('amenity', 'toilets'): 'wc', ('amenity', 'drinking_water'): 'water',
      ('tourism', 'camp_site'): 'camp', ('highway', 'bus_stop'): 'bus', ('amenity', 'ferry_terminal'): 'ferry'}
poi = []
for e in osm:
    t = e.get('tags', {}); ty = next((v for (a, b), v in TY.items() if t.get(a) == b), None)
    if not ty: continue
    if e['type'] == 'node': la, lo = e['lat'], e['lon']
    elif 'geometry' in e: la = sum(p['lat'] for p in e['geometry']) / len(e['geometry']); lo = sum(p['lon'] for p in e['geometry']) / len(e['geometry'])
    else: continue
    if not inside(la, lo) or (ty == 'peak' and not t.get('name')): continue
    nm = t.get('name', ''); en = t.get('name:en') or (nm if nm and not re.search(r'[一-鿿]', nm) else '')
    zh = t.get('name:zh') or (re.findall(r'[一-鿿]+', nm)[:1] or [''])[0]
    if ty == 'bus' and en.startswith('#'): en = ''
    p = w(la, lo); ele = t.get('ele'); poi.append([ty, p[0], p[1], en, zh, float(ele) if ele and re.match(r'^[\d.]+$', ele) else None])
ded = []
for o in poi:
    same = [q for q in ded if q[0] == o[0] and math.hypot(q[1] - o[1], q[2] - o[2]) < 40]
    if same:
        if not same[0][3] and o[3]: same[0][3], same[0][4] = o[3], o[4]
        continue
    ded.append(o)
res_dir = os.path.join(ROOT, 'data/research'); exits = []
for fn in os.listdir(res_dir):
    try: rj = json.load(open(os.path.join(res_dir, fn)))
    except Exception: continue
    for st in (rj.get('stages', []) if isinstance(rj, dict) else []):
        for en, zh in zip(st.get('exits_en', []), st.get('exits_zh', [])):
            for ref in re.findall(r'\b[MWHL]\d{3}\b', en):
                q = [x for x in meta['posts'] if x[0] == ref]
                if q: exits.append(['exit', q[0][1], q[0][2], en, zh, None])
json.dump({'poi': ded + exits, 'src': '© OpenStreetMap contributors; exits: AFCD / Trailpost research'}, open(f'{OUT}/walkpoi.json', 'w'), ensure_ascii=False, separators=(',', ':'))
log('walk markers', len(ded), 'exits', len(exits))

# ---------- 13. the wider view (40 m grid) ----------
FS = 40.0; cx, cz = X0 + C * CS / 2, YTOP - R * CS / 2
FE0 = math.floor((cx - A.far) / FS) * FS; FE1 = math.ceil((cx + A.far) / FS) * FS; FN0 = math.floor((cz - A.far) / FS) * FS; FN1 = math.ceil((cz + A.far) / FS) * FS
FC = int((FE1 - FE0) / FS) + 1; FR = int((FN1 - FN0) / FS) + 1
fE = FE0 + np.arange(FC) * FS; fN = FN1 - np.arange(FR) * FS
cache_far = os.path.join(CACHE, f'farasc_{A.area}_{int(A.far)}.npy')
if os.path.exists(cache_far): FH = np.load(cache_far)
else: FH = read_asc_rows(np.round((YTOP_HK - fN) / CS - 0.5).astype(int), np.round((fE - XLL) / CS - 0.5).astype(int)); np.save(cache_far, FH)
FEE, FNN = np.meshgrid(fE, fN); FLON, FLAT = to_ll.transform(FEE, FNN)
# outside HK (Shenzhen, open sea): AWS terrarium z12
tz = 12; a0, b1 = tile_xy(FLON.min(), FLAT.min(), tz); a1, b0 = tile_xy(FLON.max(), FLAT.max(), tz); a0, a1, b0, b1 = int(a0), int(a1), int(b0), int(b1)
tjobs = [(x, y) for x in range(a0, a1 + 1) for y in range(b0, b1 + 1)]
with cf.ThreadPoolExecutor(8) as ex: list(ex.map(lambda t: curl(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{tz}/{t[0]}/{t[1]}.png', os.path.join(CACHE, 'ter12', f'{t[0]}_{t[1]}.png')), tjobs))
tm = np.zeros(((b1 - b0 + 1) * 256, (a1 - a0 + 1) * 256), np.float32)
for x, y in tjobs:
    p = os.path.join(CACHE, 'ter12', f'{x}_{y}.png')
    if os.path.exists(p) and os.path.getsize(p):
        a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32); tm[(y - b0) * 256:(y - b0 + 1) * 256, (x - a0) * 256:(x - a0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
n = 2 ** tz; tmx = ((FLON + 180) / 360 * n - a0) * 256 - 0.5; tmy = ((1 - np.arcsinh(np.tan(np.radians(FLAT))) / math.pi) / 2 * n - b0) * 256 - 0.5
TER = cv2.remap(tm, tmx.astype(np.float32), tmy.astype(np.float32), cv2.INTER_LINEAR)
inHK = np.isfinite(FH)
FHH = np.where(inHK, FH, TER).astype(np.float32)
fsea = (inHK & (FH <= 0.05)) | (~inHK & (TER <= 1.0))
FHH[fsea] = -6.0; FHH[~fsea & (FHH < 1.5)] = 2.5
inD = (FEE > X0 + CS) & (FEE < X0 + (C - 1) * CS) & (FNN < YTOP - CS) & (FNN > YTOP - (R - 1) * CS); FHH[inD] = -60
v = np.round(FHH + 100).astype(np.int64)
Image.fromarray(np.stack([(v >> 8) & 255, v & 255, np.zeros_like(v)], -1).astype(np.uint8), 'RGB').save(f'{OUT}/farh.webp', 'WEBP', lossless=True, method=6)
zi = 13; c_0, d_1 = tile_xy(FLON.min(), FLAT.min(), zi); c_1, d_0 = tile_xy(FLON.max(), FLAT.max(), zi); c_0, c_1, d_0, d_1 = int(c_0), int(c_1), int(d_0), int(d_1)
fjobs = [(x, y) for x in range(c_0, c_1 + 1) for y in range(d_0, d_1 + 1)]
with cf.ThreadPoolExecutor(12) as ex: list(ex.map(lambda t: curl(f'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{zi}/{t[0]}/{t[1]}.png', os.path.join(CACHE, 'img13', f'{t[0]}_{t[1]}.png')), fjobs))
im = np.zeros(((d_1 - d_0 + 1) * 256, (c_1 - c_0 + 1) * 256, 3), np.uint8)
for x, y in fjobs:
    t = cv2.imread(os.path.join(CACHE, 'img13', f'{x}_{y}.png'), cv2.IMREAD_COLOR)
    if t is not None: im[(y - d_0) * 256:(y - d_0 + 1) * 256, (x - c_0) * 256:(x - c_0 + 1) * 256] = t
TW, TH = (FC - 1) * 2, (FR - 1) * 2
GX, GY = np.meshgrid(FE0 + (np.arange(TW) + 0.5) * (FE1 - FE0) / TW, FN1 - (np.arange(TH) + 0.5) * (FN1 - FN0) / TH); lo, la = to_ll.transform(GX, GY); n = 2 ** zi
tex = cv2.remap(im, (((lo + 180) / 360 * n - c_0) * 256 - 0.5).astype(np.float32), (((1 - np.arcsinh(np.tan(np.radians(la))) / math.pi) / 2 * n - d_0) * 256 - 0.5).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite(f'{OUT}/fartex.webp', tex, [cv2.IMWRITE_WEBP_QUALITY, 72])
json.dump({'E0': FE0, 'N1': FN1, 'fs': FS, 'cols': FC, 'rows': FR, 'dx0': X0, 'dytop': YTOP, 'tex': [TW, TH]}, open(f'{OUT}/far.json', 'w'))
tot = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
log(f'done: {len(os.listdir(OUT))} files, {tot/1e6:.1f} MB in app/l3/{A.area}/')
