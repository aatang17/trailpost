import json,glob,re,sys
names={}
for f in glob.glob('ctb/stop/*.json'):
    try: d=json.load(open(f))['data']
    except Exception: continue
    if d: names[d['stop']]=(d['name_en'],d['name_tc'],float(d['lat']),float(d['long']))
routes=json.load(open('ctb/routes.json'))['data']
rinfo={r['route']:(r['orig_en'],r['dest_en'],r['orig_tc'],r['dest_tc']) for r in routes}
serve={}
for f in glob.glob('ctb/rs_*.json'):
    m=re.match(r'ctb/rs_(.+)_(outbound|inbound)\.json',f)
    try: d=json.load(open(f))['data']
    except Exception: continue
    for x in d: serve.setdefault(x['stop'],set()).add((m.group(1),m.group(2)))
for pat in sys.argv[1:]:
    print('====',pat)
    for s,(en,tc,la,lo) in sorted(names.items()):
        if re.search(pat,en,re.I) or re.search(pat,tc):
            rs=sorted(serve.get(s,[]))
            print(s,en,'|',tc,la,lo,'|',', '.join(f"{r}({'→'+rinfo[r][1] if d=='outbound' else '→'+rinfo[r][0]})" for r,d in rs))
