import json,math,re,xml.etree.ElementTree as ET
R='../research/'
NS='{http://www.topografix.com/GPX/1/1}'
def hav(a,b):
    la1,lo1=map(math.radians,a[:2]);la2,lo2=map(math.radians,b[:2])
    h=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*6371000*math.asin(math.sqrt(h))
def readgpx(f):
    r=ET.parse(f).getroot();out=[]
    for p in r.iter(NS+'trkpt'):
        e=p.find(NS+'ele');out.append((float(p.get('lat')),float(p.get('lon')),float(e.text) if e is not None else None))
    name=(r.find(f'{NS}metadata/{NS}name') or r.find(f'{NS}trk/{NS}name'))
    return out,(name.text if name is not None else '')
def rdp(pts,eps):
    # pts: list of (x,y) in metres
    if len(pts)<3: return list(range(len(pts)))
    keep=[0,len(pts)-1];stack=[(0,len(pts)-1)]
    while stack:
        i,j=stack.pop();ax,ay=pts[i];bx,by=pts[j];dx,dy=bx-ax,by-ay;L=math.hypot(dx,dy) or 1e-9
        dm,k=0,None
        for m in range(i+1,j):
            px,py=pts[m];d=abs(dy*(px-ax)-dx*(py-ay))/L
            if d>dm: dm,k=d,m
        if k is not None and dm>eps: keep.append(k);stack+=[(i,k),(k,j)]
    return sorted(keep)
def metrics(pts):
    cum=[0.0]
    for i in range(1,len(pts)): cum.append(cum[-1]+hav(pts[i-1],pts[i]))
    L=cum[-1]
    # resample elevation every 20 m
    es=[];j=0;d=0.0
    while d<=L:
        while j<len(cum)-2 and cum[j+1]<d: j+=1
        t=0 if cum[j+1]==cum[j] else (d-cum[j])/(cum[j+1]-cum[j]); t=max(0,min(1,t))
        es.append(pts[j][2]+(pts[j+1][2]-pts[j][2])*t); d+=20
    # smooth (moving average 5)
    sm=[sum(es[max(0,i-2):i+3])/len(es[max(0,i-2):i+3]) for i in range(len(es))]
    up=dn=0;ref=sm[0]
    for e in sm:
        if e-ref>=3: up+=e-ref;ref=e
        elif ref-e>=3: dn+=ref-e;ref=e
    n=120;prof=[round(sm[min(len(sm)-1,round(i*(len(sm)-1)/(n-1)))]) for i in range(n)]
    return cum,L,round(up),round(dn),round(max(sm)),round(min(sm)),prof
lat0=22.35;kx=111320*math.cos(math.radians(lat0));ky=110574
def xy(p): return ((p[1]-114.1)*kx,(p[0]-lat0)*ky)
def proj(pt,pts,cum):
    # project point onto polyline -> (dist_m, km_along)
    P=xy(pt);best=(1e18,0)
    for i in range(len(pts)-1):
        A=xy(pts[i]);B=xy(pts[i+1]);dx,dy=B[0]-A[0],B[1]-A[1];L2=dx*dx+dy*dy
        t=0 if L2==0 else max(0,min(1,((P[0]-A[0])*dx+(P[1]-A[1])*dy)/L2))
        qx,qy=A[0]+t*dx,A[1]+t*dy;d=math.hypot(P[0]-qx,P[1]-qy)
        if d<best[0]: best=(d,cum[i]+t*(cum[i+1]-cum[i]))
    return best
def along(pts,cum,d):
    for i in range(len(cum)-1):
        if cum[i+1]>=d:
            t=(d-cum[i])/((cum[i+1]-cum[i]) or 1);return (pts[i][0]+(pts[i+1][0]-pts[i][0])*t,pts[i][1]+(pts[i+1][1]-pts[i][1])*t)
    return pts[-1][:2]
# OSM posts
osm=json.load(open('posts_osm.json'))['elements']
POST={}
for e in osm:
    t=e['tags']
    if 'Distance' in (t.get('designation:en') or '') or t.get('marker')=='pedestal' or t.get('information')=='route_marker':
        POST[t['ref']]=(e['lat'],e['lon'])
WG=json.load(open('wgrid.json'))
def stars(s):
    m=re.search(r'(\d)\s*(?:/5|★)',s) or re.search(r'(\d)',s); return int(m.group(1))
routes=[];trails=[];report=[]
colors={'maclehose':'#B5541C','wilson':'#6A4C93','hktrail':'#1F6FA8','lantau':'#1B7F5C'}
for f in ['maclehose','wilson','hktrail','lantau']:
    d=json.load(open(R+f+'.json'));T=d['trail']
    tr={'id':f,'name_en':T['name_en'],'name_zh':T['name_zh'],'prefix':T['post_prefix'],'km':T['total_km'],'notes_en':T.get('notes',''),'notes_zh':T.get('notes_zh',''),'color':colors[f],'stages':[]}
    for s in d['stages']:
        pts,name=readgpx(f'gpx/{f}{s["n"]}.gpx')
        cum,L,up,dn,mx,mn,prof=metrics(pts)
        a,b=[int(x[1:]) for x in s['posts']]
        posts=[];far=[];missing=[]
        for n in range(a,b+1):
            code=f'{T["post_prefix"]}{n:03d}'
            if code in POST:
                dist,km=proj(POST[code],pts,cum)
                if dist>250: far.append((code,round(dist)));continue
                posts.append([code,round(POST[code][0],5),round(POST[code][1],5),round(km/1000,2),0])
            elif code in WG:
                dist,km=proj(WG[code],pts,cum);la,lo_=along(pts,cum,km)
                posts.append([code,round(la,5),round(lo_,5),round(km/1000,2),1])
            elif n==b and code=='L140':
                posts.append([code,round(pts[-1][0],5),round(pts[-1][1],5),round(cum[-1]/1000,2),1])
            else: missing.append(code)
        # interpolate missing along track between known neighbours by km
        if missing:
            known={int(p[0][1:]):p[3] for p in posts}
            for code in missing:
                n=int(code[1:]);lo=max([k for k in known if k<n],default=None);hi=min([k for k in known if k>n],default=None)
                if lo is None or hi is None: continue
                km=known[lo]+(known[hi]-known[lo])*(n-lo)/(hi-lo);la,lo_=along(pts,cum,km*1000)
                posts.append([code,round(la,5),round(lo_,5),round(km,2),1])
            posts.sort(key=lambda p:int(p[0][1:]))
        report.append((f,s['n'],name[:50],round(L/1000,2),s['km'],up,mx,len(posts),b-a+1,far,missing))
        xyp=[xy(p) for p in pts];keep=rdp(xyp,6)
        line=[[round(pts[i][0],5),round(pts[i][1],5)] for i in keep]
        r={k:v for k,v in s.items() if k not in('posts_estimated','sources')}
        r.update(id=f'{f}-{s["n"]}',trail=f,kind='stage',stars=stars(s['difficulty']),gpx_km=round(L/1000,2),ascent=up,descent=dn,max_ele=mx,min_ele=mn,profile=prof,line=line,post_list=posts,sources=s.get('sources',[]))
        routes.append(r);tr['stages'].append(r['id'])
    trails.append(tr)
# day hikes
dh=json.load(open(R+'dayhikes.json'))['hikes']
gmap={'taitam':'day_taitam_res','plovercove':'day_plovercove','highisland':'day_highisland_eastdam','pingchau':'day_pingchau','sharpisland':'day_sharpisland','patsinleng':'day_patsinleng','taimoshan':'day_taimoshan','lunghawan':'day_lunghawan'}
for h in dh:
    r={k:v for k,v in h.items()}
    r.update(trail='day',kind='day',stars=stars(str(h.get('difficulty','2'))) if re.search(r'\d',str(h.get('difficulty',''))) else None)
    if h['id'] in gmap:
        pts,name=readgpx(f'gpx/{gmap[h["id"]]}.gpx')
        noele=any(p[2] is None for p in pts)
        if noele: pts=[(p[0],p[1],0.0) for p in pts]
        cum,L,up,dn,mx,mn,prof=metrics(pts);keep=rdp([xy(p) for p in pts],6)
        if noele: up=dn=mx=mn=prof=None
        r.update(gpx_km=round(L/1000,2),ascent=up,descent=dn,max_ele=mx,min_ele=mn,profile=prof,line=[[round(pts[i][0],5),round(pts[i][1],5)] for i in keep])
        report.append(('day',h['id'],name[:50],round(L/1000,2),h.get('km'),up,mx))
    else: report.append(('day',h['id'],'NO GPX',h.get('km'),h.get('difficulty')))
    routes.append(r)
for x in report: print(x)
json.dump({'trails':trails,'routes':routes},open('routes.json','w'),ensure_ascii=False,separators=(',',':'))
import os;print('size',os.path.getsize('routes.json'))
