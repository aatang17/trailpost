import re,json
exec(open('posts.py').read().split("print('---- cumulative")[0].replace('print(','(lambda *a,**k:None)('))
for s in range(1,11):
    h=open(f's{s}.html',encoding='utf-8').read()
    for var in re.findall(r'var (locations\w*) = (\[\[.*?\]\]);',h):
        name,arr=var
        try: L=json.loads(arr)
        except Exception as e: print('ERR',s,name,e); continue
        print(f'== S{s} {name}')
        for m in L:
            lab,lat,lon=m[0],m[1],m[2]
            if lab in ('起點','終點'): continue
            near=min(ll,key=lambda n:dist((lat,lon),ll[n]))
            d=dist((lat,lon),ll[near])
            if lab:
                print(f'  {lab} ({lat:.5f},{lon:.5f}) near M{near:03d} {d:.0f}m')
