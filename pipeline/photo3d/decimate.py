# Reduce triangles by level (keep the path-side tiles detailed) and write the final packs.
import json, os, numpy as np, fast_simplification as fs
O='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/t3d/out/'
idx=json.load(open(O+'index.json'));geo=open(O+'geo.bin','rb').read()
RED={}
PACK=11_000_000;packs=[];cur=bytearray();tot_tri=[0,0]
os.makedirs(O+'pub',exist_ok=True)
def flush():
    global cur
    if cur: packs.append(bytes(cur));cur=bytearray()
# coarse and far first, so the page can show the whole area quickly, then refine toward the path
order=sorted(idx,key=lambda t:(t['lv'] if t['lv']>=15 else 0,-t['dist']))
out=[]
for t in order:
    nv,ni=t['nv'],t['ni'];o=t['off'];q=np.frombuffer(geo,np.uint16,nv*3,o).reshape(nv,3);o+=nv*6
    qu=np.frombuffer(geo,np.uint16,nv*2,o).reshape(nv,2);o+=nv*4
    ib=np.frombuffer(geo,np.uint32 if t['i32'] else np.uint16,ni,o).astype(np.int64).reshape(-1,3)
    mn=np.array(t['min']);sc=np.array(t['sc']);pos=q/65535.0*sc+mn
    tot_tri[0]+=len(ib);r=RED.get(t['lv'],0)
    if r>0 and len(ib)>200:
        try:
            p2,f2,coll=fs.simplify(pos.astype(np.float32),ib.astype(np.int32),target_reduction=r,return_collapses=True)
            p3,f3,mp=fs.replay_simplification(pos.astype(np.float32),ib.astype(np.int32),coll)
            uv2=np.zeros((len(p3),2),np.uint16);uv2[mp]=qu;pos,ib,qu=p3.astype(np.float64),f3.astype(np.int64),uv2
        except Exception as e: print('keep',t['id'],e)
    tot_tri[1]+=len(ib)
    mn=pos.min(0);sc=np.maximum(pos.max(0)-mn,1e-3);q2=np.round((pos-mn)/sc*65535).astype(np.uint16)
    i32=len(pos)>65535;ibb=ib.reshape(-1).astype(np.uint32 if i32 else np.uint16)
    blob=q2.tobytes()+qu.tobytes()+ibb.tobytes()
    while len(blob)%4: blob+=b'\0'
    tex=open(O+'tex/'+t['id']+'.webp','rb').read()
    if len(cur)+len(blob)+len(tex)>PACK: flush()
    e={'id':t['id'],'lv':t['lv'],'p':len(packs),'go':len(cur),'nv':len(pos),'ni':len(ibb),'i32':i32,'min':np.round(mn,3).tolist(),'sc':np.round(sc,4).tolist(),'umin':t['umin'],'us':t['us']}
    cur+=blob;e['to']=len(cur);e['tl']=len(tex);cur+=tex
    while len(cur)%4: cur+=b'\0'
    out.append(e)
flush()
for i,b in enumerate(packs): open(O+f'pub/pack{i}.bin','wb').write(b)
json.dump({'tiles':out,'packs':[len(b) for b in packs]},open(O+'pub/tiles.json','w'),separators=(',',':'))
print('tris',tot_tri,'packs',[round(len(b)/1e6,1) for b in packs],'total MB',round(sum(map(len,packs))/1e6,1))
