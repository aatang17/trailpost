# Pick a non-overlapping set of LandsD 3D tiles: fine along the Lantau Peak part of Stage 3, coarser further out.
import json, os, sys, math, subprocess, urllib.parse
import numpy as np, pyproj
from PIL import Image
S='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/'
BASE='https://data.map.gov.hk/api/3d-data/3dtiles/f2/'; KEY='3967f8f365694e0798af3e7678509421'
CACHE=S+'tiles3d/meshmodel/WGS84/'
K=float(sys.argv[1]) if len(sys.argv)>1 else 40; RMAX=float(sys.argv[2]) if len(sys.argv)>2 else 4000; DL=len(sys.argv)>3 and sys.argv[3]=='dl';MAXL=int(sys.argv[4]) if len(sys.argv)>4 else 21
D0,D1=[float(v) for v in os.environ.get('SPAN','2400,3000').split(',')]  # metres along Stage 3 (summit is near 2860)
def fetch(rel):
    p=os.path.normpath(os.path.join(CACHE,rel))
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p),exist_ok=True)
        r=subprocess.run(['curl','-sS','-m','120','-o',p,'-w','%{http_code}',BASE+urllib.parse.quote(rel)+'?key='+KEY],capture_output=True,text=True)
        if r.stdout!='200':
            print('FAIL',rel,r.stdout);os.path.exists(p) and os.remove(p);return None
    return p
# path points of Stage 3 with ground height
m=json.load(open(S+'app/l3/meta.json'));pts=np.array([p[:2] for p in m['stages']['lantau-3']['pts']])
cum=np.r_[0,np.cumsum(np.hypot(*np.diff(pts,axis=0).T))]
ds=np.arange(D0,D1,10.0);xs=np.interp(ds,cum,pts[:,0]);zs=np.interp(ds,cum,pts[:,1])
im=np.array(Image.open(S+'app/l3/dem5.webp').convert('RGB')).astype(float);H=im[:,:,0]*256+im[:,:,1]-10
hs=np.array([H[int(z/5-0.5),int(x/5-0.5)] for x,z in zip(xs,zs)])
E=xs+m['x0hk'];N=m['ytophk']-zs
t1=pyproj.Transformer.from_crs(2326,4979,always_xy=True);lon,lat,_=t1.transform(E,N,np.zeros_like(E))
t2=pyproj.Transformer.from_crs(4979,4978,always_xy=True);X,Y,Z=t2.transform(lon,lat,hs+2)  # HK heights ~ ellipsoid-2m; fine for distance
P=np.c_[X,Y,Z];ctr=P[np.argmax(hs)]
json.dump({'lat':list(lat),'lon':list(lon),'h':list(hs),'d':list(ds)},open(S+'t3d/path.json','w'))
def mat(t): return np.array(t,dtype=float).reshape(4,4).T if t else np.eye(4)
def boxdist(bv,M,Q):
    b=np.array(bv['box']);c=(M@np.append(b[:3],1))[:3];A=(M[:3,:3]@b[3:].reshape(3,3).T).T
    d=Q-c;out=np.zeros(len(Q))
    for ax in A:
        L=np.linalg.norm(ax)
        if L==0: continue
        u=ax/L;t=d@u;out+=np.maximum(0,np.abs(t)-L)**2
    return np.sqrt(out)
sel=[];stats={}
def visit(n,M,basedir,depth=0):
    M=M@mat(n.get('transform'));bv=n['boundingVolume']
    if boxdist(bv,M,ctr[None])[0]>RMAX: return
    dist=boxdist(bv,M,P).min();err=n.get('geometricError',0)
    c=(n.get('content') or {});uri=c.get('uri') or c.get('url')
    if uri and uri.endswith('.json'):
        rel=os.path.normpath(os.path.join(basedir,uri));p=fetch(rel)
        if p: t=json.load(open(p));visit(t['root'],M,os.path.dirname(rel),depth+1)
        return
    kids=n.get('children',[])
    lvl=int(uri.split('_L')[-1].split('_')[0].split('.')[0]) if uri and '_L' in uri else 0
    if lvl>=15 and lvl>=MAXL: kids=[]
    RD={15:float(os.environ.get('R15',400)),16:float(os.environ.get('R16',150)),17:float(os.environ.get('R17',60)),18:float(os.environ.get('R18',15))}
    lim=RD.get(lvl,err*K) if lvl>=15 else err*K
    if kids and dist<lim:
        for ch in kids: visit(ch,M,basedir,depth+1)
        return
    if uri:
        rel=os.path.normpath(os.path.join(basedir,uri));sel.append({'rel':rel,'err':err,'dist':round(float(dist),1),'M':M.T.flatten().tolist()})
        lv=rel.split('_L')[-1].split('_')[0].split('.')[0] if '_L' in rel else '?';stats[lv]=stats.get(lv,0)+1
    elif kids:
        for ch in kids: visit(ch,M,basedir,depth+1)
root=json.load(open(fetch('tileset.json')))
visit(root['root'],np.eye(4),'.')
print('K',K,'RMAX',RMAX,'tiles',len(sel),'by level',dict(sorted(stats.items())))
json.dump(sel,open(S+'t3d/sel.json','w'))
if DL:
    tot=0
    for s in sel:
        p=fetch(s['rel'])
        if p: tot+=os.path.getsize(p)
    print('downloaded MB',round(tot/1e6,1))
