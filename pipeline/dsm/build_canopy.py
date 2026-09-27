import numpy as np,json,math,os
from PIL import Image,ImageDraw
from pyproj import Transformer
from scipy import ndimage as nd
B='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/'
meta=json.load(open(B+'dem/lantau_meta.json'));x0,ytop,cs=meta['x0'],meta['ytop'],meta['cs'];R,C=meta['shape']
dsm=np.load(B+'dsm/dsm_grid.npy');dtm=np.load(B+'dsm/dtm_grid.npy')
old=np.asarray(Image.open(B+'app/lantau-dem.png').convert('RGB')).astype(np.int64)
hold=(-10000+(old[...,0]*65536+old[...,1]*256+old[...,2])*0.1).astype(np.float32)
sea=hold<=-5.5
ground=np.where(np.isnan(dtm),hold,dtm).astype(np.float32)
ground[sea]=-6.0
ground[(~sea)&(ground<0.3)]=0.3
can=np.nan_to_num(dsm-dtm,nan=0.0);can[sea]=0
can=np.clip(can,0,60);can[can<1.2]=0
# masks
tf=Transformer.from_crs(4326,2326,always_xy=True)
def px(lat,lon):E,N=tf.transform(lon,lat);return ((E-x0)/cs,(ytop-N)/cs)
m=Image.new('L',(C,R),0);d=ImageDraw.Draw(m)
osm=json.load(open(B+'b3d/osm.json'))['elements']
nb=0
for e in osm:
    if e['type']=='way' and 'building' in e.get('tags',{}):
        d.polygon([px(p['lat'],p['lon']) for p in e['geometry']],fill=255);nb+=1
bmask=nd.binary_dilation(np.asarray(m)>0,iterations=2)
m2=Image.new('L',(C,R),0);d2=ImageDraw.Draw(m2)
rd=json.load(open(B+'hzmb/roads.json'))['elements'];nr=0
for e in rd:
    t=e['tags']
    if t.get('bridge') or t.get('highway') in ('motorway','motorway_link','trunk'):
        d2.line([px(p['lat'],p['lon']) for p in e['geometry']],fill=255,width=7);nr+=1
routes=json.load(open(B+'geo/routes.json'))['routes']
for r in routes:
    for seg in (r.get('segs') or ([r['line']] if 'line' in r else [])):
        pts=[px(a,b) for a,b in seg]
        if any(0<=x<C and 0<=y<R for x,y in pts): d2.line(pts,fill=255,width=2)
rmask=np.asarray(m2)>0
can[bmask|rmask]=0
# light speckle clean
can=nd.median_filter(can,size=3)
print('buildings',nb,'roads',nr,'canopy>3m share of land %',round(((can>3)&~sea).sum()/(~sea).sum()*100,1),'p90',np.percentile(can[can>0],90))
# ---- ambient occlusion (sky view) on the surface
S=np.where(sea,0,ground+can).astype(np.float32)
dirs=16;steps=[5,10,15,25,35,50,70,100,140,200,280,400]
hz=np.zeros((dirs,R,C),np.float32)
for k in range(dirs):
    a=2*math.pi*k/dirs;dx,dy=math.cos(a),math.sin(a)
    best=np.zeros((R,C),np.float32)
    for s in steps:
        ox,oy=int(round(dx*s/cs)),int(round(dy*s/cs))
        if ox==0 and oy==0: continue
        sh=np.full((R,C),-1e4,np.float32)
        ys=slice(max(0,-oy),R-max(0,oy));yd=slice(max(0,oy),R-max(0,-oy))
        xs=slice(max(0,-ox),C-max(0,ox));xd=slice(max(0,ox),C-max(0,-ox))
        sh[ys,xs]=S[yd,xd]
        dist=math.hypot(ox,oy)*cs
        best=np.maximum(best,(sh-S)/dist)
    hz[k]=best
sinh=np.sin(np.arctan(np.maximum(hz,0)))
svf=1-sinh.mean(0)
ao=np.clip(svf,0,1)**1.3
ao=0.30+0.70*ao
ao[sea]=1.0
print('ao p5/p50',np.percentile(ao[~sea],[5,50]))
def enc(G,Cn,path,lossless=True):
    v=np.round((G+10)*10).astype(np.int64);c8=np.clip(np.round(Cn*4),0,255).astype(np.uint8)
    Image.fromarray(np.stack([(v>>8)&255,v&255,c8],-1).astype(np.uint8),'RGB').save(path,'WEBP',lossless=True,quality=100,method=6)
enc(ground,can,B+'app/l3/dem5.webp')
g10=ground[::2,::2];c10=nd.uniform_filter(can,2)[::2,::2]
enc(g10,c10,B+'app/l3/dem10.webp')
Image.fromarray((ao*255).astype(np.uint8),'L').convert('RGB').save(B+'app/l3/ao.webp','WEBP',quality=80,method=6)
np.save(B+'dsm/ground.npy',ground);np.save(B+'dsm/canopy.npy',can)
for f in ['dem5.webp','dem10.webp','ao.webp']: print(f,os.path.getsize(B+'app/l3/'+f)//1024,'KB')
Image.fromarray((ao*255).astype(np.uint8)).resize((1136,711)).save(B+'dsm/ao_prev.png')
Image.fromarray(np.clip(can*8,0,255).astype(np.uint8)).resize((1136,711)).save(B+'dsm/can_prev.png')
