"""The Lantau Link and Ting Kau Bridge for the Lantau 3D area -> app/l3/links.json

  Tsing Ma Bridge (suspension): towers 206 m above sea, main span 1,377 m, side spans 355.5 m, deck 41 m wide.
      The Tsing Yi side span hangs from the cables; the Ma Wan side span sits on piers.
  Kap Shui Mun Bridge (cable-stayed): H-shaped towers 150 m, main span 430 m, 22 stays per fan (176 in all).
  Ma Wan Viaduct: 503 m across Ma Wan between the two.
  Ting Kau Bridge (cable-stayed): three single-leg towers 173.30 / 201.55 / 163.30 m (Ting Kau / main / Tsing Yi),
      spans 448 m and 475 m, two separate decks either side of the towers.
Sources: Highways Department fact sheet (Kap Shui Mun), Structurae and Wikipedia (Tsing Ma, Ting Kau).
Route: OpenStreetMap bridge ways. Deck height: the LandsD 5 m DTM, which records the road surface on bridges.
Tower positions: from the span lengths, anchored on where the water crossing starts or ends along each bridge.

Usage: python3 pipeline/bridges/lantau_link.py   (needs ~/.cache/trailpost/far/lantau_link_osm.json and the DTM asc)
"""
import json, os, math, numpy as np
from pyproj import Transformer
from PIL import Image

CACHE = os.environ.get('TP_CACHE', os.path.expanduser('~/.cache/trailpost'))
OUT = 'app/l3'
meta = json.load(open(f'{OUT}/meta.json')); X0, YTOP = meta['x0hk'], meta['ytophk']
to = Transformer.from_crs(4326, 2326, always_xy=True)
def xz(E, N): return (E - X0, YTOP - N)
osm = json.load(open(f'{CACHE}/far/lantau_link_osm.json'))['elements']

# ---- LandsD DTM rows (5 m), read only the rows we need
XLL, YLL, CS, NC, NR = 799997.5, 799997.5, 5, 12751, 9601; YT = YLL + NR * CS
def dtm_sampler(points):
    rows = {int(round((YT - n) / CS - 0.5)) for e, n in points for n in (n - 30, n, n + 30)}
    data = {}
    with open(f'{CACHE}/Whole_HK_DTM_5m.asc') as f:
        for _ in range(6): f.readline()
        for r, line in enumerate(f):
            if r in rows: data[r] = np.array(line.split(), dtype=np.float32)
            if r > max(rows): break
    def h(E, N):
        r = int(round((YT - N) / CS - 0.5)); c = int(round((E - XLL) / CS - 0.5))
        return float(data[r][c]) if r in data and 0 <= c < NC else -9999.0
    return h

# ---- far grid (40 m): land/sea along each bridge, ground under piers
fm = json.load(open(f'{OUT}/far.json'))
fh = np.asarray(Image.open(f'{OUT}/farh.webp').convert('RGB')).astype(np.int64); FH = (fh[..., 0] * 256 + fh[..., 1] - 100).astype(np.float32)
def far_ground(E, N):
    c = (E - fm['E0']) / fm['fs']; r = (fm['N1'] - N) / fm['fs']
    if 0 <= c < fm['cols'] - 1 and 0 <= r < fm['rows'] - 1: return float(FH[int(round(r)), int(round(c))])
    return -6.0

def ways_named(name):
    out = []
    for w in osm:
        t = w['tags']; n = t.get('bridge:name:en') or t.get('bridge:name') or t.get('name:en') or t.get('name')
        if n == name and 'geometry' in w: out.append(w)
    return out
def axis_of(ws):
    P = np.array([to.transform(p['lon'], p['lat']) for w in ws for p in w['geometry']])
    c = P.mean(0); _, _, vt = np.linalg.svd(P - c); ax = vt[0]
    if ax[0] < 0: ax = -ax
    t = (P - c) @ ax
    return c, ax, float(t.min()), float(t.max())
def water_runs(c, ax, t0, t1):
    ts = np.arange(t0 - 200, t1 + 200, 10.0); w = np.array([far_ground(*(c + ax * t)) < 0 for t in ts])
    runs = []; i = 0
    while i < len(ts):
        if w[i]:
            j = i
            while j < len(ts) and w[j]: j += 1
            runs.append((float(ts[i]), float(ts[j - 1]))); i = j
        else: i += 1
    return [r for r in runs if r[1] - r[0] > 60]

deck, piers, towers, cables, mains, labels = [], [], [], [], [], []
def add_deck(c, ax, t0, t1, width, th, off=0.0, step=20.0, hfn=None, style=None, did=None):
    nr = np.array([-ax[1], ax[0]]); pts = []
    for t in list(np.arange(t0, t1, step)) + [t1]:
        E, N = c + ax * t + nr * off; y = hfn(t); x, z = xz(E, N); pts.append([round(x, 1), round(z, 1), round(y, 1)])
    d = {'pts': pts, 'w': width, 'br': 1, 'main': 1, 'th': th}
    if style: d['style'] = style
    if did: d['id'] = did
    deck.append(d)
def deck_height_fn(c, ax, t0, t1, h):
    """road level along the bridge from the DTM (highest value across the deck), smoothed; gaps interpolated"""
    ts = np.arange(t0, t1 + 1, 10.0); nr = np.array([-ax[1], ax[0]]); ys = []
    for t in ts:
        v = [h(*(c + ax * t + nr * o)) for o in (-12, -6, 0, 6, 12)]; v = [a for a in v if a > 5]
        ys.append(max(v) if v else np.nan)
    ys = np.array(ys); ok = np.isfinite(ys)
    ys = np.interp(ts, ts[ok], ys[ok]) if ok.any() else np.full_like(ts, 60.0)
    k = np.ones(7) / 7; ys = np.convolve(np.pad(ys, 3, mode='edge'), k, 'valid')
    return lambda t: float(np.interp(t, ts, ys))
def add_piers(c, ax, t0, t1, hfn, skip, every=70.0, width=14.0):
    for t in np.arange(t0 + every / 2, t1, every):
        if any(a - 15 < t < b + 15 for a, b in skip): continue
        E, N = c + ax * t; g = max(0.0, far_ground(E, N)); y = hfn(t)
        if y - g < 8: continue
        x, z = xz(E, N); piers.append([round(x, 1), round(z, 1), round(g, 1), round(y - 7, 1), round(math.atan2(-ax[1], ax[0]), 3), width])
def pt(c, ax, t, off=0.0):
    nr = np.array([-ax[1], ax[0]]); E, N = c + ax * t + nr * off; return xz(E, N)
def lab(en, zh, x, z, y, kind='place'): labels.append({'en': en, 'zh': zh, 'x': round(x, 1), 'z': round(z, 1), 'y': y, 'kind': kind})
def axl(ax): return [round(float(ax[0]), 4), round(float(-ax[1]), 4)]  # axis in local x/z (z points south)

# ================= Tsing Ma =================
ws = ways_named('Tsing Ma Bridge'); c, ax, t0, t1 = axis_of(ws)
allpts = [c + ax * t for t in np.arange(t0 - 50, t1 + 50, 10)]
h = dtm_sampler([tuple(p) for p in allpts] + [tuple(c + ax * t) for t in np.arange(-3000, 2000, 10)])
runs = water_runs(c, ax, t0, t1); main_run = max(runs, key=lambda r: r[1] - r[0])
tTY = main_run[1]; tMW = tTY - 1377.0   # Tsing Yi tower at the Tsing Yi shore; Ma Wan tower 1,377 m west (on its islet off Ma Wan)
print('Tsing Ma: deck', round(t0), round(t1), 'water', [(round(a), round(b)) for a, b in runs], 'towers at', round(tMW), round(tTY))
hf = deck_height_fn(c, ax, t0, t1, h)
add_deck(c, ax, t0, t1, 41.0, 7.3, hfn=hf, style='truss', did='tm')
add_piers(c, ax, t0, t1, hf, [(tMW, tTY + 355.5)], width=30.0)
HW = 18.0; TOP = 206.0
for t in (tMW, tTY):
    x, z = pt(c, ax, t); towers.append({'n': 'Tsing Ma', 'kind': 'h', 'x': round(x, 1), 'z': round(z, 1), 'top': TOP, 'deck': round(hf(t), 1), 'ax': axl(ax), 'hw': HW + 4,
        'leg': [13.0, 7.0], 'taper': [0.68, 0.85], 'beams': [round(hf(t) - 12, 1), 118.0, 158.0, TOP - 6], 'saddle': 1, 'lights': 1,
        'islet': [150, 90] if t == tMW else None})  # the Ma Wan tower stands on a man-made island with a rock sea wall
# main cables: Ma Wan anchorage -> towers (sag 1/11 of the span) -> Tsing Yi anchorage; hangers every 18 m where the deck hangs
tA0, tA1 = tMW - 355.5, tTY + 355.5
def cable_y(t):
    if t < tMW: u = (t - tA0) / (tMW - tA0); return hf(t) + 6 + (TOP - 3 - hf(t) - 6) * u - 12 * 4 * u * (1 - u)
    if t > tTY: u = (tA1 - t) / (tA1 - tTY); return hf(t) + 6 + (TOP - 3 - hf(t) - 6) * u - 12 * 4 * u * (1 - u)
    u = (t - tMW) / 1377.0; return TOP - 3 - 4 * 125.0 * u * (1 - u)
for side in (-1, 1):
    line = []
    for t in np.arange(tA0, tA1 + 1, 15.0):
        x, z = pt(c, ax, t, side * HW); line.append([round(x, 1), round(z, 1), round(cable_y(t), 1)])
    mains.append({'pts': line, 'r': 0.7})
    for t in np.arange(tMW + 18, min(tA1, t1) - 10, 18.0):
        x, z = pt(c, ax, t, side * HW); cy, dy = cable_y(t), hf(t) + 1
        if cy - dy > 1.5: cables.append([round(x, 1), round(z, 1), round(cy, 1), round(x, 1), round(z, 1), round(dy, 1)])
anchorages = []  # 250,000 t of concrete on Ma Wan, 200,000 t on Tsing Yi
for tA, nm in ((tA0, 'Ma Wan'), (tA1, 'Tsing Yi')):
    E, N = c + ax * tA; g = max(0.0, far_ground(E, N)); x, z = pt(c, ax, tA)
    anchorages.append({'n': nm, 'x': round(x, 1), 'z': round(z, 1), 'g': round(g, 1), 'top': round(cable_y(tA) + 8, 1), 'ax': axl(ax), 'len': 70.0, 'w': 56.0})
x, z = pt(c, ax, (tMW + tTY) / 2); lab('Tsing Ma Bridge · main span 1,377 m', '青馬大橋 · 主跨1,377米', x, z, 250, 'bridge')

# ================= Kap Shui Mun =================
ws = ways_named('Kap Shui Mun Bridge'); c2, ax2, s0, s1 = axis_of(ws)
h2 = dtm_sampler([tuple(c2 + ax2 * t) for t in np.arange(s0 - 50, s1 + 50, 10)])
runs = water_runs(c2, ax2, s0, s1); run = max(runs, key=lambda r: r[1] - r[0]); mid = (run[0] + run[1]) / 2
tk0, tk1 = mid - 215.0, mid + 215.0
print('Kap Shui Mun: deck', round(s0), round(s1), 'water', [(round(a), round(b)) for a, b in runs], 'towers at', round(tk0), round(tk1))
hf2 = deck_height_fn(c2, ax2, s0, s1, h2)
add_deck(c2, ax2, s0, s1, 35.0, 7.5, hfn=hf2, style='truss', did='ksm')
add_piers(c2, ax2, s0, s1, hf2, [(tk0, tk1)], every=80.0, width=26.0)
for t in (tk0, tk1):
    x, z = pt(c2, ax2, t); d = hf2(t)
    towers.append({'n': 'Kap Shui Mun', 'kind': 'h', 'x': round(x, 1), 'z': round(z, 1), 'top': 150.0, 'deck': round(d, 1), 'ax': axl(ax2), 'hw': 19.5,
                   'leg': [7.0, 5.0], 'beams': [round(d - 11, 1), 145.0]})
    for side in (-1, 1):
        for plane in (-17.0, 17.0):
            for k in range(22):
                ta = t + side * (18 + k * (160 - 25) / 21 if (side < 0) == (t == tk0) else 18 + k * (215 - 25) / 21)
                ax_, az_ = pt(c2, ax2, ta, plane); tx, tz = pt(c2, ax2, t, plane)
                cables.append([round(tx, 1), round(tz, 1), round(145 - k * 2.6, 1), round(ax_, 1), round(az_, 1), round(hf2(ta) + 1, 1)])
x, z = pt(c2, ax2, mid); lab('Kap Shui Mun Bridge · towers 150 m', '汲水門大橋 · 塔高150米', x, z, 190, 'bridge')

# ================= Ma Wan Viaduct =================
ws = ways_named('Ma Wan Viaduct')
if ws:
    c3, ax3, v0, v1 = axis_of(ws); h3 = dtm_sampler([tuple(c3 + ax3 * t) for t in np.arange(v0 - 50, v1 + 50, 10)])
    hf3 = deck_height_fn(c3, ax3, v0, v1, h3); add_deck(c3, ax3, v0, v1, 35.0, 7.0, hfn=hf3, style='truss', did='mwv'); add_piers(c3, ax3, v0, v1, hf3, [], every=65.0, width=24.0)

# ================= Ting Kau =================
ws = ways_named('Ting Kau Bridge'); c4, ax4, u0, u1 = axis_of(ws)
# the axis must run from Ting Kau (north) to Tsing Yi (south)
if (c4 + ax4 * 100)[1] > c4[1]: ax4 = -ax4; u0, u1 = -u1, -u0
h4 = dtm_sampler([tuple(c4 + ax4 * t) for t in np.arange(u0 - 50, u1 + 50, 10)])
runs = water_runs(c4, ax4, u0, u1)
# spans 448 m (Ting Kau side) and 475 m (Tsing Yi side): centre the 923 m between the flanking towers on the whole
# crossing, shore to shore (the main tower then stands on the small island in the channel)
mid = (runs[0][0] + runs[-1][1]) / 2; tT = mid - 923 / 2; tM = tT + 448; tY = tM + 475
print('Ting Kau: deck', round(u0), round(u1), 'water', [(round(a), round(b)) for a, b in runs], 'towers at', round(tT), round(tM), round(tY))
hf4 = deck_height_fn(c4, ax4, u0, u1, h4)
for off in (-12.0, 12.0): add_deck(c4, ax4, u0, u1, 18.8, 1.8, off=off, hfn=hf4, did='tk' + ('s' if off > 0 else 'n'))
add_piers(c4, ax4, u0, u1, hf4, [(tT, tY)], every=60.0, width=40.0)
for t, top, nm in ((tT, 173.3, 'Ting Kau'), (tM, 201.55, 'main'), (tY, 163.3, 'Tsing Yi')):
    x, z = pt(c4, ax4, t); d = hf4(t)
    towers.append({'n': 'Ting Kau', 'kind': 'mast', 'x': round(x, 1), 'z': round(z, 1), 'top': top, 'deck': round(d, 1), 'ax': axl(ax4), 'hw': 3.0})
    for side in (-1, 1):
        reach = 127 if (t == tT and side < 0) or (t == tY and side > 0) else (448 if (t == tT or (t == tM and side < 0)) else 475) / 2
        for plane in (-12.0 + -8.0, 12.0 + 8.0):  # outer edge of each deck
            for k in range(12):
                ta = t + side * (20 + k * (reach - 30) / 11); ax_, az_ = pt(c4, ax4, ta, plane); tx, tz = pt(c4, ax4, t)
                cables.append([round(tx, 1), round(tz, 1), round(top - 8 - k * (top - d - 50) / 12, 1), round(ax_, 1), round(az_, 1), round(hf4(ta) + 1, 1)])
# the long stabilising cables from the top of the main tower down to the deck beside the flanking towers
for tf in (tT, tY):
    for plane in (-20.0, 20.0):
        ax_, az_ = pt(c4, ax4, tf, plane); tx, tz = pt(c4, ax4, tM)
        cables.append([round(tx, 1), round(tz, 1), 199.0, round(ax_, 1), round(az_, 1), round(hf4(tf) + 1, 1)])
x, z = pt(c4, ax4, tM); lab('Ting Kau Bridge · main tower 202 m', '汀九橋 · 主塔202米', x, z, 240, 'bridge')

# ================= place labels towards the city =================
def plab(en, zh, lon, lat, lift, kind='place'):
    E, N = to.transform(lon, lat); x, z = xz(E, N); g = max(0.0, far_ground(E, N)); lab(en, zh, x, z, round(g + lift), kind)
plab('Hong Kong Island', '香港島', 114.185, 22.262, 120, 'city')
plab('Victoria Peak 552 m', '太平山 552米', 114.1455, 22.2759, 40, 'peak')
plab('Kowloon', '九龍', 114.172, 22.318, 120, 'city')
plab('Tai Mo Shan 957 m', '大帽山 957米', 114.1244, 22.4106, 40, 'peak')
plab('Tsing Yi', '青衣', 114.100, 22.352, 60)
plab('Ma Wan', '馬灣', 114.058, 22.352, 60)
plab('Lamma Island', '南丫島', 114.120, 22.215, 60)
# traffic routes: the Lantau Link as one road (Kap Shui Mun -> Ma Wan Viaduct -> Tsing Ma), Ting Kau as another
byid = {d.get('id'): d for d in deck}
link = [p for k in ('ksm', 'mwv', 'tm') if k in byid for p in byid[k]['pts']]
routes = [{'n': 'Lantau Link', 'pts': link, 'lanes': 3, 'lw': 3.7, 'rail': 1}]
if 'tkn' in byid and 'tks' in byid:
    routes.append({'n': 'Ting Kau', 'pts': [[round((a[0] + b[0]) / 2, 1), round((a[1] + b[1]) / 2, 1), a[2]] for a, b in zip(byid['tkn']['pts'], byid['tks']['pts'])], 'lanes': 3, 'lw': 3.7, 'split': 12.0})
out = {'anchorages': anchorages, 'routes': routes, 'deck': deck, 'piers': piers, 'towers': towers, 'cables': cables, 'mains': mains, 'labels': labels,
       'notes': 'Lantau Link and Ting Kau Bridge. Route: OpenStreetMap. Deck heights: LandsD 5 m DTM. Tower heights and spans: '
                'Highways Department, Structurae, Wikipedia (Tsing Ma 206 m / 1,377 m, Kap Shui Mun 150 m / 430 m, Ting Kau 173.3, 201.55, 163.3 m). '
                'Tower positions derived from span lengths; detail approximate.'}
json.dump(out, open(f'{OUT}/links.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('decks', len(deck), 'piers', len(piers), 'towers', len(towers), 'cables', len(cables), 'mains', len(mains), 'labels', len(labels), os.path.getsize(f'{OUT}/links.json') // 1024, 'KB')
