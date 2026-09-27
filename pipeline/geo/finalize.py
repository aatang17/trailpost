import json,re
d=json.load(open('routes.json'));ex=json.load(open('extra_lines.json'))
daystars={'easy':1,'moderate':2,'demanding':3,'hard':4,'difficult':4,'very hard':5,'very difficult':5}
for r in d['routes']:
    if 'line' in r: r['segs']=[r.pop('line')]
    if r['id'] in ex:
        segs=ex[r['id']]
        if r['id']=='taitam' and segs[0][0][0]<segs[0][-1][0]: segs=[segs[0][::-1]]
        r['segs']=segs
    if r['id']=='taitam':
        for k in ('gpx_km','ascent','descent','max_ele','min_ele','profile'): r[k]=None
    if r['id']=='pengchau': r['segs']=[];r['pin']=[22.2855,114.0386]
    if r.get('stars') is None:
        s=str(r.get('difficulty','')).lower();m=re.search(r'(\d)',s)
        r['stars']=int(m.group(1)) if m else next((v for k,v in sorted(daystars.items(),key=lambda kv:-len(kv[0])) if k in s),2)
    txt=(r.get('safety_en') or '')+(r.get('safety_zh') or '')
    r['exposed']=bool(re.search(r"exposed|little shade|no shade|lack of shade|without shade|開揚|遮蔭",txt,re.I)) or (r.get('max_ele') or 0)>=500
    w=(r.get('water_en') or '').lower()
    r['nowater']=bool(re.search(r'^(none|no water|no )|no water|no supply|bring all|carry all|no shops|no kiosk',w))
    r['ferry']=any(t.get('mode') in('ferry','kaito') for t in r.get('to_start',[])+r.get('from_end',[]))
    r['notice']=bool(re.search(r'\bclos',r.get('safety_en','') ,re.I))
    r['coastal']=(r.get('max_ele') is not None and r['max_ele']<150) or r['id'] in ('lamma','pengchau','sharpisland','pingchau','highisland')
    r.pop('difficulty',None) if r['kind']=='stage' else None
print([(r['id'],r['stars'],r['exposed'],r['nowater'],r['ferry'],r['notice'],r['coastal']) for r in d['routes'] if r['kind']=='day'])
cond=json.load(open('conditions.json'))
base=json.load(open('basemap.json'))
js='window.HK_ROUTES='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\nwindow.HK_BASE='+json.dumps(base,ensure_ascii=False,separators=(',',':'))+';\nwindow.HK_COND='+json.dumps(cond,ensure_ascii=False,separators=(',',':'))+';\n'
open('data.js','w').write(js);print('data.js',len(js.encode()))
