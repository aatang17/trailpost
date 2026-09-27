import json,urllib.request,sys
from concurrent.futures import ThreadPoolExecutor
def get(u):
    return json.load(urllib.request.urlopen(u,timeout=20))['data']
routes=sys.argv[1:]
rs={}
def load(rb):
    r,b=rb
    try: return rb,get(f"https://rt.data.gov.hk/v2/transport/citybus/route-stop/CTB/{r}/{b}")
    except Exception as e: return rb,[]
with ThreadPoolExecutor(16) as ex:
    for rb,d in ex.map(load,[(r,b) for r in routes for b in ['inbound','outbound']]): rs[rb]=d
stops=set(x['stop'] for d in rs.values() for x in d)
def nm(s):
    try:
        d=get(f"https://rt.data.gov.hk/v2/transport/citybus/stop/{s}"); return s,d['name_en']
    except Exception: return s,'?'
with ThreadPoolExecutor(32) as ex:
    names=dict(ex.map(nm,stops))
for (r,b),d in rs.items():
    seq=[names[x['stop']] for x in d]
    hits=[n for n in seq if any(k in n for k in ['Wilson','Wong Nai Chung Reservoir','Tai Tam Reservoir Road','Stanley Gap'])]
    print(r,b,len(seq),hits)
