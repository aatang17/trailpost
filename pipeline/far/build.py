import numpy as np,json,math,os,cv2
from PIL import Image,ImageDraw
from pyproj import Transformer
from shapely.geometry import LineString,box,Point,mapping
from shapely.ops import linemerge,unary_union,polygonize
from shapely.strtree import STRtree
B='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/'
meta=json.load(open(B+'dem/lantau_meta.json'));dx0,dytop,cs=meta['x0'],meta['ytop'],meta['cs'];dR,dC=meta['shape']
L=(113.50,114.07,22.08,22.38)
to=Transformer.from_crs(4326,2326,always_xy=True);inv=Transformer.from_crs(2326,4326,always_xy=True)
Es,Ns=zip(*[to.transform(a,b) for a in L[:2] for b in L[2:]])
FS=40.0
E0=math.floor(min(Es)/FS)*FS;E1=math.ceil(max(Es)/FS)*FS;N0=math.floor(min(Ns)/FS)*FS;N1=math.ceil(max(Ns)/FS)*FS
C=int((E1-E0)/FS)+1;R=int((N1-N0)/FS)+1
print('far grid',C,R,'km',(E1-E0)/1000,(N1-N0)/1000)
E=E0+np.arange(C)*FS;N=N1-np.arange(R)*FS;EE,NN=np.meshgrid(E,N)
LON,LAT=inv.transform(EE,NN)
# 1. HK DTM (whole HK asc) sampled at grid nodes (nearest)
hk=np.full((R,C),np.nan,np.float32)
xll,yll,hcs,ncols,nrows=799997.5,799997.5,5,12751,9601;ytopHK=yll+nrows*hcs
colidx=np.round((E-xll)/hcs-0.5).astype(int);rowidx=np.round((ytopHK-N)/hcs-0.5).astype(int)
need={}
for i,r in enumerate(rowidx):
    if 0<=r<nrows: need.setdefault(r,[]).append(i)
cvalid=(colidx>=0)&(colidx<ncols)
with open(B+'dem/Whole_HK_DTM_5m.asc') as f:
    for _ in range(6): f.readline()
    for r,line in enumerate(f):
        if r in need:
            a=np.array(line.split(),dtype=np.float32)
            vals=np.full(C,np.nan,np.float32);vals[cvalid]=a[colidx[cvalid]]
            for i in need[r]: hk[i]=vals
hk[hk<=-9000]=np.nan
print('hk coverage',np.isfinite(hk).mean())
# 2. terrarium z12
z,tx0,tx1,ty0,ty1=map(int,open(B+'far/ter_range.txt').read().split());n=2**z
mos=np.zeros(((ty1-ty0+1)*256,(tx1-tx0+1)*256),np.float32)
for x in range(tx0,tx1+1):
    for y in range(ty0,ty1+1):
        a=np.asarray(Image.open(B+f'far/ter/{x}_{y}.png').convert('RGB')).astype(np.float32)
        mos[(y-ty0)*256:(y-ty0+1)*256,(x-tx0)*256:(x-tx0+1)*256]=a[...,0]*256+a[...,1]+a[...,2]/256-32768
mx=((LON+180)/360*n-tx0)*256-0.5;my=((1-np.arcsinh(np.tan(np.radians(LAT)))/math.pi)/2*n-ty0)*256-0.5
ter=cv2.remap(mos,mx.astype(np.float32),my.astype(np.float32),cv2.INTER_LINEAR)
H=np.where(np.isfinite(hk),hk,ter).astype(np.float32)
# 3. land mask from coastline (east + west downloads)
ways=json.load(open(B+'geo/coast.json'))['elements']+json.load(open(B+'hzmb/coast_w.json'))['elements']
seen=set();lines=[]
for w in ways:
    if w['id'] in seen or len(w['geometry'])<2: continue
    seen.add(w['id']);lines.append(LineString([(p['lon'],p['lat']) for p in w['geometry']]))
BB=box(L[0],L[2],L[1],L[3])
m=linemerge(lines);ml=list(m.geoms) if hasattr(m,'geoms') else [m]
clipped=[]
for l in ml:
    x=l.intersection(BB)
    for g in (x.geoms if hasattr(x,'geoms') else [x]):
        if g.geom_type=='LineString' and len(g.coords)>1: clipped.append(g)
faces=list(polygonize(unary_union(clipped+[BB.exterior])));tree=STRtree(faces);score=[0]*len(faces);eps=1e-6
for l in clipped:
    cs_=list(l.coords);step=max(1,len(cs_)//20)
    for i in range(0,len(cs_)-1,step):
        (x1,y1),(x2,y2)=cs_[i],cs_[i+1];ddx,ddy=x2-x1,y2-y1;nn=(ddx*ddx+ddy*ddy)**.5
        if nn==0: continue
        mxx,myy=(x1+x2)/2,(y1+y2)/2
        for pt,v in ((Point(mxx-ddy/nn*eps,myy+ddx/nn*eps),1),(Point(mxx+ddy/nn*eps,myy-ddx/nn*eps),-1)):
            for j in tree.query(pt):
                if faces[j].contains(pt): score[j]+=v
land=[f for f,s in zip(faces,score) if s>0];print('land faces',len(land))
mimg=Image.new('L',(C,R),0);d=ImageDraw.Draw(mimg)
def ring(co):
    e,nn_=to.transform(np.array([c[0] for c in co]),np.array([c[1] for c in co]));return list(zip((e-E0)/FS,(N1-nn_)/FS))
for p in land:
    for g in (p.geoms if hasattr(p,'geoms') else [p]):
        d.polygon(ring(g.exterior.coords),fill=255)
        for h in g.interiors: d.polygon(ring(h.coords),fill=0)
landm=np.asarray(mimg)>127
H[~landm]=-6.0
H[landm&(H<1.5)]=2.5
# hide under the detailed area (5 m) : cells whose centre is inside it
inD=(EE>dx0+cs)&(EE<dx0+(dC-1)*cs)&(NN<dytop-cs)&(NN>dytop-(dR-1)*cs)
H[inD]=-60
print('land share',landm.mean(),'max',H.max())
v=np.round(H+100).astype(np.int64)
Image.fromarray(np.stack([(v>>8)&255,v&255,np.zeros_like(v)],-1).astype(np.uint8),'RGB').save(B+'app/l3/farh.webp','WEBP',lossless=True,method=6)
# 4. satellite texture at 20 m
zi,ix0,ix1,iy0,iy1=map(int,open(B+'far/img_range.txt').read().split());ni=2**zi
imos=np.zeros(((iy1-iy0+1)*256,(ix1-ix0+1)*256,3),np.uint8)
for x in range(ix0,ix1+1):
    for y in range(iy0,iy1+1):
        t=cv2.imread(B+f'far/img/{x}_{y}.png',cv2.IMREAD_COLOR)
        if t is not None: imos[(y-iy0)*256:(y-iy0+1)*256,(x-ix0)*256:(x-ix0+1)*256]=t
TW,TH=(C-1)*2,(R-1)*2
gx=E0+(np.arange(TW)+0.5)*(E1-E0)/TW;gy=N1-(np.arange(TH)+0.5)*(N1-N0)/TH;GX,GY=np.meshgrid(gx,gy)
lo,la=inv.transform(GX,GY)
tmx=((lo+180)/360*ni-ix0)*256-0.5;tmy=((1-np.arcsinh(np.tan(np.radians(la)))/math.pi)/2*ni-iy0)*256-0.5
tex=cv2.remap(imos,tmx.astype(np.float32),tmy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite(B+'app/l3/fartex.webp',tex,[cv2.IMWRITE_WEBP_QUALITY,72])
fm={'E0':E0,'N1':N1,'fs':FS,'cols':C,'rows':R,'dx0':dx0,'dytop':dytop,'tex':[TW,TH]}
json.dump(fm,open(B+'app/l3/far.json','w'))
print(fm,os.path.getsize(B+'app/l3/farh.webp')//1024,'KB h',os.path.getsize(B+'app/l3/fartex.webp')//1024,'KB tex')
cv2.imwrite(B+'far/tex_prev.jpg',cv2.resize(tex,(1400,int(1400*TH/TW))))
