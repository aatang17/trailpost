import json, os, sys, urllib.parse, subprocess, math
sys.path.insert(0, os.path.dirname(__file__))
from obb import *
import numpy as np
BASE="https://data.map.gov.hk/api/3d-data/meshmodel/WGS84/"
KEY=os.environ.get("LANDSD_KEY","3967f8f365694e0798af3e7678509421")  # CSDI public example key; use your own
OUT=os.path.join(os.path.dirname(__file__),"tiles3d/meshmodel/WGS84/")
log=[]
def fetch(rel):
    path=os.path.normpath(os.path.join(OUT,rel))
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path),exist_ok=True)
        url=BASE+urllib.parse.quote(rel)+"?key="+KEY
        r=subprocess.run(["curl","-sS","-m","120","-o",path,"-w","%{http_code}",url],capture_output=True,text=True)
        if r.stdout!="200": print("FAIL",rel,r.stdout,r.stderr); os.remove(path); return None
    return path
def mat(t): return np.array(t,dtype=float).reshape(4,4).T if t else np.eye(4)
def inside(bv,M,pw,latlon):
    Minv=np.linalg.inv(M); pl=(Minv@np.append(pw,1))[:3]
    if 'box' in bv: return inbox(bv['box'],pl)
    return contains(bv,pl,latlon)
def colhit(bv,M,ps):
    Minv=np.linalg.inv(M); pl=(np.c_[ps,np.ones(len(ps))]@Minv.T)[:,:3]
    b=np.array(bv['box']); c=b[:3]; A=b[3:].reshape(3,3)
    d=pl-c; ok=np.ones(len(ps),bool)
    for ax in A:
        L2=ax@ax
        if L2==0: continue
        ok&=np.abs(d@ax/L2)<=1
    return ok.any()
pts={k:(np.array([ecef(v[0],v[1],h) for h in np.arange(0,1100,0.5)]),v[:2]) for k,v in PTS.items()}
contents=[]  # (depth, ge, uri, which points)
def walk_node(n,M,basedir,depth,chain):
    M=M@mat(n.get('transform'))
    hit=[k for k,(ps,ll) in pts.items() if colhit(n['boundingVolume'],M,ps)]
    if not hit: return
    c=n.get('content') or {}
    uri=c.get('uri') or c.get('url')
    if uri:
        rel=os.path.normpath(os.path.join(basedir,uri))
        if rel.endswith('.json'):
            p=fetch(rel)
            if p:
                t=json.load(open(p))
                walk_node(t['root'],M,os.path.dirname(rel),depth+1,chain+[rel])
        else:
            contents.append((depth,n.get('geometricError'),rel,hit,chain[-1],n['boundingVolume']))
    for ch in n.get('children',[]): walk_node(ch,M,basedir,depth+1,chain)
t=json.load(open(OUT+"9/tileset.json"))
walk_node(t['root'],np.eye(4),"9",0,["9/tileset.json"])
json.dump([[d,g,u,h,ch] for d,g,u,h,ch,bv in contents],open(os.path.join(os.path.dirname(__file__),"contents.json"),"w"),indent=0)
for d,g,u,h,ch,bv in contents: print(d,g,u,h,"from",ch)
