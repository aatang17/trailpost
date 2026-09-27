import numpy as np,json,math
from PIL import Image,ImageDraw
from pyproj import Transformer
H=np.load('dem/lantau5m.npy').astype(np.float32);meta=json.load(open('dem/lantau_meta.json'))
R,C=H.shape;x0,ytop,cs=meta['x0'],meta['ytop'],meta['cs']
tf=Transformer.from_crs(4326,2326,always_xy=True)
def loc(lat,lon):E,N=tf.transform(lon,lat);return (E-x0,ytop-N)
def hat(x,z):
    c=min(max(x/cs-.5,0),C-1.001);r=min(max(z/cs-.5,0),R-1.001);i,j=int(r),int(c);fr,fc=r-i,c-j
    return float(H[i,j]*(1-fr)*(1-fc)+H[i,j+1]*(1-fr)*fc+H[i+1,j]*fr*(1-fc)+H[i+1,j+1]*fr*fc)
# --- sea mask from coastline at 1x (cell centres)
base=json.load(open('geo/basemap.json'));S=2
m=Image.new('L',(C*S,R*S),0);d=ImageDraw.Draw(m)
land=base['land']
def ring(co): return [((loc(la,lo)[0]/cs-.5)*S+S/2,(loc(la,lo)[1]/cs-.5)*S+S/2) for lo,la in co]
for poly in land['coordinates']:
    if not any(22.18<la<22.33 and 113.84<lo<114.04 for lo,la in poly[0]): continue
    d.polygon(ring(poly[0]),fill=255)
    for h in poly[1:]: d.polygon(ring(h),fill=0)
mask=np.asarray(m.resize((C,R),Image.BILINEAR))>127
Hs=H.copy();sea=(~mask)&(H<3)
Hs[sea]=-6.0
Hs[(H<=0.2)]=np.minimum(Hs[(H<=0.2)],-6.0)
print('sea cells %',round(sea.mean()*100,1))
v=np.round((Hs+10000)*10).astype(np.int64)
Image.fromarray(np.stack([(v>>16)&255,(v>>8)&255,v&255],-1).astype(np.uint8),'RGB').save('app/lantau-dem.png',optimize=True)
# --- buildings
osm=json.load(open('b3d/osm.json'))['elements']
defaults={'house':8.2,'detached':8.2,'terrace':8.2,'cabin':3.0,'roof':4.0,'yes':6.0,'residential':8.2,'school':15,'service':4,'construction':None,'toilets':3.5,'temple':8,'marketplace':6,'industrial':8,'kindergarten':8,'substation':4,'parking':8,'bridge':None,'dormitory':12,'retail':6}
B=[];skipped=0
for e in osm:
    t=e.get('tags',{})
    if e['type']!='way' or 'building' not in t: continue
    kind=t['building'];h=None
    try:
        if 'height' in t: h=float(str(t['height']).split()[0])
        elif 'building:levels' in t: h=float(t['building:levels'])*3.0+(1.5 if kind in('apartments','residential') else 0)
    except: h=None
    if h is None: h=defaults.get(kind,6.0)
    if h is None: skipped+=1;continue
    pts=[loc(p['lat'],p['lon']) for p in e['geometry']]
    if len(pts)<4: continue
    if pts[0]==pts[-1]: pts=pts[:-1]
    ground=[hat(x,z) for x,z in pts]
    if min(ground)<0.2 and max(ground)<0.5: pass
    base_h=min(ground)-0.5
    # ensure CCW in x,z (z south): compute signed area
    a=sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))
    if a<0: pts=pts[::-1]
    top=max(ground)+h if kind!='roof' else max(ground)+h
    B.append([round(base_h,1),round(top-base_h,1),1 if h>=20 else 0]+[round(v,1) for p in pts for v in p])
print('buildings',len(B),'skipped',skipped,'towers',sum(b[2] for b in B))
# --- cable car
gond=[e for e in osm if e['type']=='way' and e.get('tags',{}).get('aerialway')=='gondola'][0]
pyl={e['id']:e['tags'] for e in osm if e['type']=='node' and e.get('tags',{}).get('aerialway')=='pylon'}
stations=[e for e in osm if e.get('tags',{}).get('aerialway') in ('station','service_station')]
nodes=[]
for nid,g in zip(gond['nodes'],gond['geometry']):
    x,z=loc(g['lat'],g['lon']);gr=hat(x,z)
    if nid in pyl: hh=float(pyl[nid].get('height',40));kind='pylon'
    else: hh=12.0;kind='station'
    nodes.append({'x':x,'z':z,'g':gr,'top':gr+hh,'kind':kind,'h':hh,'ref':pyl.get(nid,{}).get('ref','')})
# keep only nodes near/inside area (+ one beyond on each side for continuity)
inside=[i for i,nd in enumerate(nodes) if -200<nd['x']<C*cs+200 and -200<nd['z']<R*cs+200]
i0,i1=max(0,min(inside)-1),min(len(nodes)-1,max(inside)+1);nodes=nodes[i0:i1+1]
cable=[]  # samples [x,z,clearance]
for a,b in zip(nodes,nodes[1:]):
    L=math.hypot(b['x']-a['x'],b['z']-a['z']);n=max(2,int(L/25))
    for k in range(n):
        t=k/n;x=a['x']+(b['x']-a['x'])*t;z=a['z']+(b['z']-a['z'])*t
        y=a['top']+(b['top']-a['top'])*t-4*0.035*L*t*(1-t)   # parabolic sag ~3.5% of span
        g=hat(x,z) if (0<=x<=C*cs and 0<=z<=R*cs) else max(0,min(a['g'],b['g']))
        y=max(y,g+15);cable.append([round(x,1),round(z,1),round(y-g,1),round(y,1)])
cable.append([round(nodes[-1]['x'],1),round(nodes[-1]['z'],1),round(nodes[-1]['h'],1),round(nodes[-1]['top'],1)])
towers=[[round(nd['x'],1),round(nd['z'],1),nd['h'],nd['kind'],nd['ref']] for nd in nodes]
print('cable samples',len(cable),'towers',[(t[3],t[2],t[4]) for t in towers])
json.dump({'buildings':B,'cable':cable,'towers':towers},open('app/lantau/extras.json','w'),separators=(',',':'))
import os;print('extras KB',os.path.getsize('app/lantau/extras.json')//1024,'dem KB',os.path.getsize('app/lantau-dem.png')//1024)
