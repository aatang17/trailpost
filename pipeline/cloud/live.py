#!/usr/bin/env python3
"""Trailpost HK live conditions feed.
Writes out/conditions.json (weather, warnings, cloud layers, peak cloud status) and out/cams.json (camera photos as data URIs).
Sources: Hong Kong Observatory open data + weather photos; airport METAR/TAF (VHHH) from aviationweather.gov.
Standard library only."""
import json, urllib.request, csv, io, base64, datetime, math, os, re
HKT = datetime.timezone(datetime.timedelta(hours=8))
os.makedirs('out', exist_ok=True)
def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'TrailpostHK/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        b = r.read()
    return b if binary else b.decode('utf-8', 'replace')
def js(url):
    try: return json.loads(get(url))
    except Exception as e: print('WARN', url, e); return {}
B = 'https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType='
ws, wi, wit = js(B+'warnsum&lang=en'), js(B+'warningInfo&lang=en'), js(B+'warningInfo&lang=tc')
rh, fe, ft, le, lt = js(B+'rhrread&lang=en'), js(B+'fnd&lang=en'), js(B+'fnd&lang=tc'), js(B+'flw&lang=en'), js(B+'flw&lang=tc')
warn = [ (v.get('code') or k) for k, v in (ws or {}).items() if isinstance(v, dict) and v.get('actionCode') != 'CANCEL']
temps = {x['place']: x['value'] for x in rh.get('temperature', {}).get('data', [])}
uv = None
try: uv = rh['uvindex']['data'][0]['value']
except Exception: pass
fc = []
for a, b in zip(fe.get('weatherForecast', [])[:3], ft.get('weatherForecast', [])[:3]):
    fc.append({'date': a['forecastDate'], 'max': a['forecastMaxtemp']['value'], 'min': a['forecastMintemp']['value'], 'rhmax': a['forecastMaxrh']['value'],
               'psr': a['PSR'], 'wx_en': a['forecastWeather'], 'wx_zh': b['forecastWeather'], 'wind_en': a['forecastWind'], 'wind_zh': b['forecastWind']})
# regional station readings (hill stations)
def regional(name):
    try:
        rows = list(csv.reader(io.StringIO(get('https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/' + name + '.csv'))))
        return {r[1]: r[2:] for r in rows[1:] if len(r) > 2}
    except Exception as e:
        print('WARN', name, e); return {}
rt, rw, rv = regional('latest_1min_temperature'), regional('latest_10min_wind'), regional('latest_10min_visibility')
hill = {k: float(v[0]) for k, v in rt.items() if k in ('Ngong Ping', 'Tai Mo Shan', 'The Peak', 'Chek Lap Kok') and v and v[0] not in ('', 'N/A')}
wind_np = rw.get('Ngong Ping')
# airport cloud observation and forecast
COV = {'FEW': 0.19, 'SCT': 0.44, 'BKN': 0.75, 'OVC': 1.0, 'VV': 1.0}
met = js('https://aviationweather.gov/api/data/metar?ids=VHHH&format=json&hours=2')
m = met[0] if isinstance(met, list) and met else {}
layers = [{'cover': c.get('cover'), 'base_m': round(c['base'] * 0.3048), 'frac': COV.get(c.get('cover'), 0)} for c in m.get('clouds', []) if c.get('base') is not None and c.get('cover') in COV]
if m.get('vertVis'): layers.insert(0, {'cover': 'VV', 'base_m': round(m['vertVis'] * 0.3048), 'frac': 1.0})
T, Td = m.get('temp'), m.get('dewp')
lcl = round(125 * (T - Td)) if T is not None and Td is not None else None
vis = m.get('visib')
taf = js('https://aviationweather.gov/api/data/taf?ids=VHHH&format=json')
tafc = []
if isinstance(taf, list) and taf:
    for g in taf[0].get('fcsts', []):
        cl = [{'cover': c.get('cover'), 'base_m': round(c['base'] * 0.3048), 'frac': COV.get(c.get('cover'), 0)} for c in (g.get('clouds') or []) if c.get('base') is not None and c.get('cover') in COV]
        tafc.append({'from': g.get('timeFrom'), 'to': g.get('timeTo'), 'change': g.get('fcstChange'), 'prob': g.get('probability'), 'clouds': cl, 'wx': g.get('wxString')})
PEAKS = [('Lantau Peak', '鳳凰山', 934), ('Sunset Peak', '大東山', 869), ('Tai Mo Shan', '大帽山', 957), ('Ma On Shan', '馬鞍山', 702), ('Victoria Peak', '扯旗山', 552), ('Lion Rock', '獅子山', 495)]
def peak_status(h):
    for L in sorted(layers, key=lambda x: x['base_m']):
        if L['base_m'] <= h:
            if L['frac'] >= 0.75: return 'in'      # broken/overcast base below the summit
            return 'patches'                       # few/scattered cloud at or below summit height
    return 'clear'
peaks = [{'en': e, 'zh': z, 'm': h, 'status': peak_status(h)} for e, z, h in PEAKS]
cloud = {'obsTime': m.get('reportTime'), 'raw': m.get('rawOb'), 'layers': layers, 'temp': T, 'dewp': Td, 'lcl_m': lcl, 'vis': vis,
         'wdir': m.get('wdir'), 'wspd_kt': m.get('wspd'), 'hill_temps': hill, 'wind_ngongping': wind_np, 'peaks': peaks, 'taf': tafc,
         'source': 'Hong Kong International Airport METAR/TAF (VHHH)'}
out = {'fetchedAt': datetime.datetime.now(HKT).isoformat(timespec='minutes'), 'obsTime': rh.get('updateTime'), 'warnings': warn,
       'detail_en': [' '.join(d.get('contents', [])) for d in wi.get('details', [])], 'detail_zh': [' '.join(d.get('contents', [])) for d in wit.get('details', [])],
       'temps': temps, 'humidity': (rh.get('humidity', {}).get('data') or [{}])[0].get('value'), 'uv': uv,
       'today_en': le.get('forecastDesc', ''), 'today_zh': lt.get('forecastDesc', ''), 'outlook_en': le.get('outlook', ''), 'outlook_zh': lt.get('outlook', ''),
       'situation_en': fe.get('generalSituation', ''), 'situation_zh': ft.get('generalSituation', ''), 'forecast': fc, 'cloud': cloud,
       'source': 'Hong Kong Observatory open data'}
json.dump(out, open('out/conditions.json', 'w'), ensure_ascii=False)
# camera photos (HKO weather photos refresh every few minutes)
CAMS = [('CS2', 'Cheung Sha, looking north to Lantau Peak and Sunset Peak', '長沙向北望鳳凰山及大東山'),
        ('TLC', 'Tai Lam Chung, looking across to north Lantau', '大欖涌望北大嶼山'),
        ('TM2', 'Tai Mo Shan, looking south-west', '大帽山向西南望'),
        ('VPA', 'Victoria Peak, looking east', '山頂向東望')]
cams = []
for code, en, zh in CAMS:
    try:
        b = get(f'https://www.hko.gov.hk/wxinfo/aws/hko_mica/{code.lower()}/latest_{code}.jpg', binary=True)
        if len(b) > 2000: cams.append({'id': code, 'en': en, 'zh': zh, 'img': 'data:image/jpeg;base64,' + base64.b64encode(b).decode()})
    except Exception as e: print('WARN cam', code, e)
json.dump({'fetchedAt': out['fetchedAt'], 'credit': 'Photos: Hong Kong Observatory', 'cams': cams}, open('out/cams.json', 'w'))
print('OK', out['fetchedAt'], 'warnings', warn, 'layers', layers, 'lcl', lcl, 'peaks', [(p['en'], p['status']) for p in peaks], 'cams', len(cams),
      'sizes', os.path.getsize('out/conditions.json'), os.path.getsize('out/cams.json'))
