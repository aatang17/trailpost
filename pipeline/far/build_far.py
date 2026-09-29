"""Wider-area terrain for a 3D area: 40 m heights + 20 m satellite texture around the detailed (5 m) area.

Usage: python3 pipeline/far/build_far.py <area dir, e.g. app/l3> <lon0> <lon1> <lat0> <lat1>
  Lantau (reaches Macau in the west and Chai Wan / Tai Mo Shan in the east):
  python3 pipeline/far/build_far.py app/l3 113.50 114.27 22.08 22.43

Heights: LandsD 5 m DTM (Hong Kong) where it exists, AWS terrarium z12 elsewhere.
Sea: OpenStreetMap coastline (downloaded once for the box). Texture: LandsD imagery z13 (~19 m/pixel).
Cells under the detailed area are pushed to -60 m so they never show through it.
Downloads are cached in $TP_CACHE (default ~/.cache/trailpost)."""
import numpy as np, json, math, os, sys, subprocess, urllib.parse, concurrent.futures as cf, cv2
from PIL import Image, ImageDraw
from pyproj import Transformer
from shapely.geometry import LineString, box, Point
from shapely.ops import linemerge, unary_union, polygonize
from shapely.strtree import STRtree

OUT = sys.argv[1]; L = tuple(float(v) for v in sys.argv[2:6])  # lon0, lon1, lat0, lat1
CACHE = os.environ.get('TP_CACHE', os.path.expanduser('~/.cache/trailpost')); FC = os.path.join(CACHE, 'far'); os.makedirs(FC, exist_ok=True)
meta = json.load(open(os.path.join(OUT, 'meta.json'))); dx0, dytop, cs, dC, dR = meta['x0hk'], meta['ytophk'], meta['cs'], meta['cols'], meta['rows']
log = lambda *a: print('[far]', *a, flush=True)

def tiles(z, lon0, lon1, lat0, lat1):
    n = 2 ** z; tx = lambda lon: int((lon + 180) / 360 * n); ty = lambda lat: int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return tx(lon0), tx(lon1), ty(lat1), ty(lat0)
def get(job):
    u, f = job
    if os.path.exists(f) and os.path.getsize(f) > 200: return 0
    for _ in range(3):
        r = subprocess.run(['curl', '-s', '-m', '40', '-o', f, '-w', '%{http_code}', u], capture_output=True, text=True)
        if r.stdout == '200': return 0
    return 1
IZ, TZ = 13, 12
ix0, ix1, iy0, iy1 = tiles(IZ, *L); tx0, tx1, ty0, ty1 = tiles(TZ, *L)
jobs = [(f'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{IZ}/{x}/{y}.png', f'{FC}/img{IZ}_{x}_{y}.png') for x in range(ix0, ix1 + 1) for y in range(iy0, iy1 + 1)]
jobs += [(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{TZ}/{x}/{y}.png', f'{FC}/ter{TZ}_{x}_{y}.png') for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
with cf.ThreadPoolExecutor(10) as ex: fails = sum(ex.map(get, jobs))
log('tiles', len(jobs), 'fails', fails)

# coastline for the whole box (one Overpass query, cached)
cf_ = f'{FC}/coast_{L[0]}_{L[1]}_{L[2]}_{L[3]}.json'
if not os.path.exists(cf_):
    q = f'[out:json][timeout:180];way["natural"="coastline"]({L[2]},{L[0]},{L[3]},{L[1]});out geom;'
    for mirror in ['https://overpass.private.coffee/api/interpreter', 'https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']:
        r = subprocess.run(['curl', '-s', '-m', '240', '-o', cf_ + '.tmp', '-w', '%{http_code}', '--data-urlencode', 'data=' + q, mirror], capture_output=True, text=True)
        if r.stdout == '200':
            try: json.load(open(cf_ + '.tmp')); os.replace(cf_ + '.tmp', cf_); break
            except Exception: pass
ways = json.load(open(cf_))['elements']; log('coastline ways', len(ways))

to = Transformer.from_crs(4326, 2326, always_xy=True); inv = Transformer.from_crs(2326, 4326, always_xy=True)
Es, Ns = zip(*[to.transform(a, b) for a in L[:2] for b in L[2:]])
FS = 40.0
E0 = math.floor(min(Es) / FS) * FS; E1 = math.ceil(max(Es) / FS) * FS; N0 = math.floor(min(Ns) / FS) * FS; N1 = math.ceil(max(Ns) / FS) * FS
C = int((E1 - E0) / FS) + 1; R = int((N1 - N0) / FS) + 1
log('grid', C, R, 'km', (E1 - E0) / 1000, (N1 - N0) / 1000)
E = E0 + np.arange(C) * FS; N = N1 - np.arange(R) * FS; EE, NN = np.meshgrid(E, N); LON, LAT = inv.transform(EE, NN)

# 1. Hong Kong DTM (asc), nearest sample at grid nodes
hk = np.full((R, C), np.nan, np.float32)
xll, yll, hcs, ncols, nrows = 799997.5, 799997.5, 5, 12751, 9601; ytopHK = yll + nrows * hcs
colidx = np.round((E - xll) / hcs - 0.5).astype(int); rowidx = np.round((ytopHK - N) / hcs - 0.5).astype(int)
need = {}
for i, r in enumerate(rowidx):
    if 0 <= r < nrows: need.setdefault(r, []).append(i)
cvalid = (colidx >= 0) & (colidx < ncols)
with open(os.path.join(CACHE, 'Whole_HK_DTM_5m.asc')) as f:
    for _ in range(6): f.readline()
    for r, line in enumerate(f):
        if r in need:
            a = np.array(line.split(), dtype=np.float32); vals = np.full(C, np.nan, np.float32); vals[cvalid] = a[colidx[cvalid]]
            for i in need[r]: hk[i] = vals
hk[hk <= -9000] = np.nan
log('HK DTM coverage', round(float(np.isfinite(hk).mean()), 3))
# 2. terrarium z12
n = 2 ** TZ; mos = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
for x in range(tx0, tx1 + 1):
    for y in range(ty0, ty1 + 1):
        a = np.asarray(Image.open(f'{FC}/ter{TZ}_{x}_{y}.png').convert('RGB')).astype(np.float32)
        mos[(y - ty0) * 256:(y - ty0 + 1) * 256, (x - tx0) * 256:(x - tx0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
mx = ((LON + 180) / 360 * n - tx0) * 256 - 0.5; my = ((1 - np.arcsinh(np.tan(np.radians(LAT))) / math.pi) / 2 * n - ty0) * 256 - 0.5
ter = cv2.remap(mos, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR)
H = np.where(np.isfinite(hk), hk, ter).astype(np.float32)
# 3. land mask from the coastline (land is on the left of each coastline way)
seen = set(); lines = []
for w in ways:
    if w['id'] in seen or len(w.get('geometry', [])) < 2: continue
    seen.add(w['id']); lines.append(LineString([(p['lon'], p['lat']) for p in w['geometry']]))
BB = box(L[0], L[2], L[1], L[3]); m = linemerge(lines); ml = list(m.geoms) if hasattr(m, 'geoms') else [m]; clipped = []
for l in ml:
    x = l.intersection(BB)
    for g in (x.geoms if hasattr(x, 'geoms') else [x]):
        if g.geom_type == 'LineString' and len(g.coords) > 1: clipped.append(g)
faces = list(polygonize(unary_union(clipped + [BB.exterior]))); tree = STRtree(faces); score = [0] * len(faces); eps = 1e-6
for l in clipped:
    cs_ = list(l.coords); step = max(1, len(cs_) // 20)
    for i in range(0, len(cs_) - 1, step):
        (x1, y1), (x2, y2) = cs_[i], cs_[i + 1]; ddx, ddy = x2 - x1, y2 - y1; nn = (ddx * ddx + ddy * ddy) ** .5
        if nn == 0: continue
        mxx, myy = (x1 + x2) / 2, (y1 + y2) / 2
        for pt, v in ((Point(mxx - ddy / nn * eps, myy + ddx / nn * eps), 1), (Point(mxx + ddy / nn * eps, myy - ddx / nn * eps), -1)):
            for j in tree.query(pt):
                if faces[j].contains(pt): score[j] += v
land = [f for f, s in zip(faces, score) if s > 0]; log('land faces', len(land), 'of', len(faces))
mimg = Image.new('L', (C, R), 0); d = ImageDraw.Draw(mimg)
def ring(co):
    e, nn_ = to.transform(np.array([c[0] for c in co]), np.array([c[1] for c in co])); return list(zip((e - E0) / FS, (N1 - nn_) / FS))
for p in land:
    for g in (p.geoms if hasattr(p, 'geoms') else [p]):
        d.polygon(ring(g.exterior.coords), fill=255)
        for h in g.interiors: d.polygon(ring(h.coords), fill=0)
landm = np.asarray(mimg) > 127
# the DTM includes bridge decks as if they were ground: cut them out along OSM bridge ways and fill from the land around
bf = os.environ.get('FAR_BRIDGES')  # an Overpass JSON of bridge ways, e.g. ~/.cache/trailpost/far/lantau_link_osm.json
if bf and os.path.exists(bf):
    bimg = Image.new('L', (C, R), 0); bd = ImageDraw.Draw(bimg); nbw = 0
    for w in json.load(open(bf))['elements']:
        if 'geometry' not in w or not w.get('tags', {}).get('bridge'): continue
        e_, n_ = to.transform(np.array([p['lon'] for p in w['geometry']]), np.array([p['lat'] for p in w['geometry']]))
        bd.line(list(zip((e_ - E0) / FS, (N1 - n_) / FS)), fill=255, width=2); nbw += 1
    bm = cv2.dilate(np.asarray(bimg), np.ones((3, 3), np.uint8)) > 0
    Hf = H.copy(); Hf[bm] = np.nan
    for _ in range(12):  # grow the surrounding ground inwards
        nanm = np.isnan(Hf)
        if not nanm.any(): break
        pad = np.pad(Hf, 1, constant_values=np.nan); nb = np.stack([pad[1:-1, :-2], pad[1:-1, 2:], pad[:-2, 1:-1], pad[2:, 1:-1]])
        with np.errstate(all='ignore'): fill = np.nanmin(nb, 0)
        Hf[nanm] = fill[nanm]
    Hf[np.isnan(Hf)] = 0; H = np.where(bm, Hf, H).astype(np.float32); log('bridge ways flattened', nbw, 'cells', int(bm.sum()))
H[~landm] = -6.0; H[landm & (H < 1.5)] = 2.5
inD = (EE > dx0 + cs) & (EE < dx0 + (dC - 1) * cs) & (NN < dytop - cs) & (NN > dytop - (dR - 1) * cs); H[inD] = -60  # hidden under the detailed area
log('land share', round(float(landm.mean()), 3), 'max height', float(H.max()))
v = np.round(H + 100).astype(np.int64)
Image.fromarray(np.stack([(v >> 8) & 255, v & 255, np.zeros_like(v)], -1).astype(np.uint8), 'RGB').save(f'{OUT}/farh.webp', 'WEBP', lossless=True, method=6)
# 4. satellite texture at 20 m (2 texels per grid cell)
ni = 2 ** IZ; imos = np.zeros(((iy1 - iy0 + 1) * 256, (ix1 - ix0 + 1) * 256, 3), np.uint8)
for x in range(ix0, ix1 + 1):
    for y in range(iy0, iy1 + 1):
        t = cv2.imread(f'{FC}/img{IZ}_{x}_{y}.png', cv2.IMREAD_COLOR)
        if t is not None: imos[(y - iy0) * 256:(y - iy0 + 1) * 256, (x - ix0) * 256:(x - ix0 + 1) * 256] = t
TW, TH = min(4096, (C - 1) * 2), min(4096, (R - 1) * 2)  # 4096 is the largest texture most phones accept
gx = E0 + (np.arange(TW) + 0.5) * (E1 - E0) / TW; gy = N1 - (np.arange(TH) + 0.5) * (N1 - N0) / TH; GX, GY = np.meshgrid(gx, gy); lo, la = inv.transform(GX, GY)
tmx = ((lo + 180) / 360 * ni - ix0) * 256 - 0.5; tmy = ((1 - np.arcsinh(np.tan(np.radians(la))) / math.pi) / 2 * ni - iy0) * 256 - 0.5
tex = cv2.remap(imos, tmx.astype(np.float32), tmy.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite(f'{OUT}/fartex.webp', tex, [cv2.IMWRITE_WEBP_QUALITY, 72])
fm = {'E0': E0, 'N1': N1, 'fs': FS, 'cols': C, 'rows': R, 'dx0': dx0, 'dytop': dytop, 'tex': [TW, TH]}
json.dump(fm, open(f'{OUT}/far.json', 'w'))
cv2.imwrite(f'{FC}/tex_prev.jpg', cv2.resize(tex, (1600, int(1600 * TH / TW))))
log(fm, os.path.getsize(f'{OUT}/farh.webp') // 1024, 'KB heights', os.path.getsize(f'{OUT}/fartex.webp') // 1024, 'KB texture')
