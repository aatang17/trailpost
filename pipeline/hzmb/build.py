import json,math,numpy as np
from pyproj import Transformer
from PIL import Image
B='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/'
meta=json.load(open(B+'dem/lantau_meta.json'));x0,ytop=meta['x0'],meta['ytop']
to=Transformer.from_crs(4326,2326,always_xy=True)
def xz(lon,lat):E,N=to.transform(lon,lat);return (E-x0,ytop-N)
fm=json.load(open(B+'app/l3/far.json'))
fh=np.asarray(Image.open(B+'app/l3/farh.webp').convert('RGB')).astype(np.int64);FH=(fh[...,0]*256+fh[...,1]-100).astype(np.float32)
g5=np.load(B+'dsm/ground.npy')
def ground(x,z):
    c=x/5-0.5;r=z/5-0.5
    if 0<=c<g5.shape[1]-1 and 0<=r<g5.shape[0]-1: return max(0.0,float(g5[int(r),int(c)]))
    E=x+x0;N=ytop-z;cc=(E-fm['E0'])/fm['fs'];rr=(fm['N1']-N)/fm['fs']
    if 0<=cc<fm['cols']-1 and 0<=rr<fm['rows']-1: return max(0.0,float(FH[int(round(rr)),int(round(cc))]))
    return 0.0
rd=json.load(open(B+'hzmb/roads.json'))['elements']
ways=[e for e in rd if 'Zhuhai-Macao Bridge' in (e['tags'].get('name:en') or e['tags'].get('name') or '')]
print('ways',len(ways))
# anchors: ends of at-grade or tunnel segments (where the viaduct must come down)
anch=[]
for e in ways:
    t=e['tags']
    if not t.get('bridge'):
        for p in (e['geometry'][0],e['geometry'][-1]):
            x,z=xz(p['lon'],p['lat']);anch.append((x,z,ground(x,z)+(0 if t.get('tunnel') else 0.5),bool(t.get('tunnel'))))
anch=np.array([(a[0],a[1],a[2]) for a in anch])
CH={'Qingzhou':(113.7262,113.7374,49.0),'Jianghai':(113.6448,113.6541,45.0),'Jiuzhou':(113.5938,113.5994,45.0)}
def profile(lon,main):
    if not main: return 15.0
    h=25.0
    for a,b,top in CH.values():
        d=0 if a<=lon<=b else min(abs(lon-a),abs(lon-b))*103000  # metres
        h=max(h,top-max(0,d)*0.022)
    return h
deck=[];piers=[]
for e in ways:
    t=e['tags'];n=t.get('name:en') or t.get('name')
    if t.get('tunnel'): continue
    main='Link Road' not in n
    lanes=int(t.get('lanes','3')) if str(t.get('lanes','3')).isdigit() else 3
    w=min(max(lanes,2),5)*3.75+3.0
    pts=[];prev=None;acc=0.0
    geo=e['geometry']
    for i,p in enumerate(geo):
        x,z=xz(p['lon'],p['lat'])
        if t.get('bridge'):
            y=profile(p['lon'],main)
            if len(anch):
                d=np.hypot(anch[:,0]-x,anch[:,1]-z);k=np.argmin(d)
                y=min(y,anch[k,2]+2.0+d[k]*0.035)
            y=max(y,ground(x,z)+1.0)
        else: y=ground(x,z)+0.6
        pts.append([round(x,1),round(z,1),round(y,1)])
    deck.append({'pts':pts,'w':round(w,1),'br':1 if t.get('bridge') else 0,'main':1 if main else 0})
# piers: along bridge decks every 110 m (main) / 70 m (link road), from resampled polylines
for dk in deck:
    if not dk['br']: continue
    P=np.array(dk['pts']);seg=np.hypot(np.diff(P[:,0]),np.diff(P[:,1]));cum=np.concatenate([[0],np.cumsum(seg)])
    sp=110 if dk['main'] else 70
    for s in np.arange(sp/2,cum[-1],sp):
        i=min(np.searchsorted(cum,s),len(P)-1);i=max(i,1);f=(s-cum[i-1])/max(cum[i]-cum[i-1],1e-6)
        x=P[i-1,0]+(P[i,0]-P[i-1,0])*f;z=P[i-1,1]+(P[i,1]-P[i-1,1])*f;y=P[i-1,2]+(P[i,2]-P[i-1,2])*f
        g=ground(x,z)
        if y-g<5: continue
        ang=math.atan2(P[i,1]-P[i-1,1],P[i,0]-P[i-1,0])
        piers.append([round(x,1),round(z,1),round(g,1),round(y-3.5,1),round(ang,3)])
# channel bridges: axis from the cable-stayed carriageways
towers=[];cables=[]
spec={'青州航道桥':('Qingzhou',[-229,229],163.0,'portal'),'江海直达航道桥':('Jianghai',[-258,0,258],150.0,'dolphin'),'九洲航道桥':('Jiuzhou',[-134,134],120.0,'sail')}
for zhname,(en,offs,top,kind) in spec.items():
    ws=[e for e in rd if e['tags'].get('bridge:name')==zhname]
    pts=np.array([xz(p['lon'],p['lat']) for e in ws for p in e['geometry']])
    c=pts.mean(0)
    # axis direction via PCA
    u,s,vt=np.linalg.svd(pts-c);ax=vt[0]
    if ax[0]<0: ax=-ax
    nrm=np.array([-ax[1],ax[0]])
    halfw=np.abs((pts-c)@nrm).max()+8.5
    deckY=CH[en][2]
    for o in offs:
        p=c+ax*o;towers.append({'n':en,'kind':kind,'x':round(p[0],1),'z':round(p[1],1),'top':top,'deck':deckY,'ax':[round(ax[0],4),round(ax[1],4)],'hw':round(halfw,1)})
        # fan cables: anchors along deck each side of the tower
        planes=[-halfw+3,halfw-3] if kind=='portal' else [0.0]
        ncab={'portal':14,'dolphin':9,'sail':8}[kind];sp_=15.0 if kind=='portal' else 13.0
        for pl in planes:
            for side in (-1,1):
                for k in range(ncab):
                    a=p+ax*side*(24+k*sp_)+nrm*pl
                    ht=top-8-k*(top-deckY-40)/ncab*0.9 if kind=='portal' else deckY+ (top-deckY)*(0.55+0.4*k/ncab)
                    tp=p+nrm*pl
                    cables.append([round(tp[0],1),round(tp[1],1),round(ht,1),round(a[0],1),round(a[1],1),round(deckY+1,1)])
labels=[{'en':'Hong Kong–Zhuhai–Macao Bridge','zh':'港珠澳大橋','x':None}]
L=[]
def lab(en,zh,lon,lat,y,kind='place'):
    x,z=xz(lon,lat);L.append({'en':en,'zh':zh,'x':round(x,1),'z':round(z,1),'y':y,'kind':kind})
for t in towers:
    pass
q=[t for t in towers if t['n']=='Qingzhou'];j=[t for t in towers if t['n']=='Jianghai'];u=[t for t in towers if t['n']=='Jiuzhou']
for grp,en,zh in ((q,'Qingzhou Channel Bridge · towers 163 m','青州航道橋 · 塔高163米'),(j,'Jianghai Channel Bridge · "dolphin" towers','江海直達船航道橋 · 海豚塔'),(u,'Jiuzhou Channel Bridge · "sail" towers 120 m','九洲航道橋 · 風帆塔120米')):
    x=np.mean([t['x'] for t in grp]);z=np.mean([t['z'] for t in grp]);L.append({'en':en,'zh':zh,'x':round(x,1),'z':round(z,1),'y':grp[0]['top']+25,'kind':'bridge'})
lab('Undersea tunnel · 6.7 km','海底隧道 · 6.7公里',113.8055,22.2845,30,'bridge')
lab('Zhuhai','珠海',113.556,22.262,60,'city');lab('Macau','澳門',113.553,22.180,60,'city')
lab('Hong Kong International Airport','香港國際機場',113.915,22.310,40,'place');lab('HK Boundary Crossing Facilities','香港口岸',113.945,22.3195,30,'place')
lab('Tung Chung','東涌',113.943,22.288,40,'place')
out={'deck':deck,'piers':piers,'towers':towers,'cables':cables,'labels':L,
     'notes':'Route from OpenStreetMap. Tower heights from published figures (Qingzhou 163 m, Jiuzhou 120 m, Jianghai steel towers 105 m). Deck heights approximate.'}
json.dump(out,open(B+'app/l3/bridge.json','w'),ensure_ascii=False,separators=(',',':'))
import os;print('decks',len(deck),'piers',len(piers),'towers',len(towers),'cables',len(cables),os.path.getsize(B+'app/l3/bridge.json')//1024,'KB')
print([(t['n'],t['x'],t['z'],t['hw']) for t in towers])
