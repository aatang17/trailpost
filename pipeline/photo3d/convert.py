# Download the selected tiles, move vertices into a local east-north-up frame at Lantau Peak, quantise, and pull out the KTX2 textures.
import json, os, struct, subprocess, urllib.parse, math
import numpy as np, pyproj
S='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/'
CACHE=S+'tiles3d/meshmodel/WGS84/';OUT=S+'t3d/out/';os.makedirs(OUT+'ktx',exist_ok=True)
BASE='https://data.map.gov.hk/api/3d-data/3dtiles/f2/';KEY='3967f8f365694e0798af3e7678509421'
sel=json.load(open(S+'t3d/sel.json'));path=json.load(open(S+'t3d/path.json'))
# origin: highest path point (Lantau Peak)
i0=int(np.argmax(path['h']));lat0,lon0,h0=path['lat'][i0],path['lon'][i0],0.0
to_ecef=pyproj.Transformer.from_crs(4979,4978,always_xy=True)
O=np.array(to_ecef.transform(lon0,lat0,h0))
la,lo=math.radians(lat0),math.radians(lon0)
R=np.array([[-math.sin(lo),math.cos(lo),0],[-math.sin(la)*math.cos(lo),-math.sin(la)*math.sin(lo),math.cos(la)],[math.cos(la)*math.cos(lo),math.cos(la)*math.sin(lo),math.sin(la)]])
def enu(P): return (P-O)@R.T
# path in ENU (ellipsoid height = HK height + ~ -2 m; the viewer snaps the walker to the mesh anyway)
PX,PY,PZ=to_ecef.transform(np.array(path['lon']),np.array(path['lat']),np.array(path['h']))
pe=enu(np.c_[PX,PY,PZ])
json.dump({'lat0':lat0,'lon0':lon0,'path':np.round(pe,2).tolist(),'d':path['d']},open(OUT+'path.json','w'))
CT={5126:('f',4),5123:('H',2),5125:('I',4),5121:('B',1)}
def acc(gj,binc,i):
    a=gj['accessors'][i];bv=gj['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];f,sz=CT[a['componentType']]
    off=bv.get('byteOffset',0)+a.get('byteOffset',0);stride=bv.get('byteStride',0) or sz*n
    dt=np.dtype('<'+f)
    if stride==sz*n: return np.frombuffer(binc,dtype=dt,count=a['count']*n,offset=off).reshape(a['count'],n)
    raw=np.frombuffer(binc,dtype=np.uint8,count=stride*a['count'],offset=off).reshape(a['count'],stride)[:,:sz*n].copy()
    return raw.view(dt).reshape(a['count'],n)
index=[];geo=bytearray();tot_in=0
for k,s in enumerate(sel):
    p=os.path.normpath(os.path.join(CACHE,s['rel']))
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p),exist_ok=True);subprocess.run(['curl','-sS','-m','120','-o',p,BASE+urllib.parse.quote(s['rel'])+'?key='+KEY])
    b=open(p,'rb').read();tot_in+=len(b)
    magic,ver,L,ftj,ftb,btj,btb=struct.unpack('<4sIIIIII',b[:28]);o=28+ftj+ftb+btj+btb;g=b[o:]
    cl=struct.unpack('<I',g[12:16])[0];gj=json.loads(g[20:20+cl]);bo=20+cl;bl=struct.unpack('<I',g[bo:bo+4])[0];binc=g[bo+8:bo+8+bl]
    M=np.array(s['M']).reshape(4,4).T
    parts=[]
    for mesh in gj['meshes']:
        for pr in mesh['primitives']:
            pos=acc(gj,binc,pr['attributes']['POSITION']).astype(np.float64);uv=acc(gj,binc,pr['attributes']['TEXCOORD_0']).astype(np.float32)
            idx=acc(gj,binc,pr['indices']).reshape(-1).astype(np.uint32) if 'indices' in pr else np.arange(len(pos),dtype=np.uint32)
            zup=np.c_[pos[:,0],-pos[:,2],pos[:,1]];ec=(np.c_[zup,np.ones(len(zup))]@M.T)[:,:3];e=enu(ec)
            three=np.c_[e[:,0],e[:,2],-e[:,1]]  # x=east, y=up, z=south
            mat=gj['materials'][pr.get('material',0)];ti=mat['pbrMetallicRoughness']['baseColorTexture']['index'];img=gj['images'][gj['textures'][ti]['source']]
            bv=gj['bufferViews'][img['bufferView']];tex=binc[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
            parts.append((three,uv,idx,tex))
    for j,(v,uv,idx,tex) in enumerate(parts):
        mn=v.min(0);mx=v.max(0);sc=np.maximum(mx-mn,1e-3)
        q=np.round((v-mn)/sc*65535).astype(np.uint16)
        umin=uv.min(0);umax=uv.max(0);us=np.maximum(umax-umin,1e-6);qu=np.round((uv-umin)/us*65535).astype(np.uint16)
        i32=len(v)>65535;ib=idx.astype(np.uint32 if i32 else np.uint16)
        tid=f'{k}_{j}';open(OUT+'ktx/'+tid+'.ktx2','wb').write(tex)
        off=len(geo);geo+=q.tobytes()+qu.tobytes()+ib.tobytes()
        while len(geo)%4:geo+=b'\0'
        lv=s['rel'].split('_L')[-1].split('_')[0].split('.')[0]
        index.append({'id':tid,'lv':int(lv) if lv.isdigit() else 0,'dist':s['dist'],'nv':len(v),'ni':len(ib),'i32':i32,'off':off,'min':np.round(mn,3).tolist(),'sc':np.round(sc,4).tolist(),'umin':umin.tolist(),'us':us.tolist(),
                      'cx':float((mn[0]+mx[0])/2),'cz':float((mn[2]+mx[2])/2),'r':float(np.linalg.norm(mx-mn)/2)})
open(OUT+'geo.bin','wb').write(geo)
json.dump(index,open(OUT+'index.json','w'))
print('tiles',len(sel),'parts',len(index),'input MB',round(tot_in/1e6,1),'geometry MB',round(len(geo)/1e6,1),'ktx MB',round(sum(os.path.getsize(OUT+'ktx/'+f) for f in os.listdir(OUT+'ktx'))/1e6,1))
print('uv range',min(min(i['umin']) for i in index),max(max(a+b for a,b in zip(i['umin'],i['us'])) for i in index))
print('path start/end',np.round(pe[0],1),np.round(pe[-1],1),'summit',np.round(pe[i0],1))
