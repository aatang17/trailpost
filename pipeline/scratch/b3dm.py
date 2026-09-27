import struct, json, sys, io
from PIL import Image
def info(path):
    b=open(path,'rb').read()
    magic,ver,L,ftj,ftb,btj,btb=struct.unpack('<4sIIIIII',b[:28])
    o=28; ft=json.loads(b[o:o+ftj]); o+=ftj+ftb; bt=b[o:o+btj]; o+=btj+btb
    g=b[o:]
    gm,gv,gl=struct.unpack('<4sII',g[:12])
    cl,ct=struct.unpack('<I4s',g[12:20]); gj=json.loads(g[20:20+cl])
    binoff=20+cl; bl,bty=struct.unpack('<I4s',g[binoff:binoff+8]); binc=g[binoff+8:binoff+8+bl]
    imgs=[]
    for im in gj.get('images',[]):
        bv=gj['bufferViews'][im['bufferView']]; data=binc[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
        try:
            I=Image.open(io.BytesIO(data)); imgs.append((im.get('mimeType'),I.format,I.size,len(data)))
        except Exception as e: imgs.append((im.get('mimeType'),'?',None,len(data)))
    tris=0;verts=0
    for m in gj['meshes']:
        for p in m['primitives']:
            if 'indices' in p: tris+=gj['accessors'][p['indices']]['count']//3
            verts+=gj['accessors'][p['attributes']['POSITION']]['count']
    pos=[gj['accessors'][p['attributes']['POSITION']] for m in gj['meshes'] for p in m['primitives']]
    return dict(magic=magic,ver=ver,len=L,ft=ft,glb=(gm,gv),ext=gj.get('extensionsUsed'),meshes=len(gj['meshes']),verts=verts,tris=tris,images=imgs,
                attrs=list(gj['meshes'][0]['primitives'][0]['attributes'].keys()),posmin=pos[0].get('min'),posmax=pos[0].get('max'),nodes=[{k:v for k,v in n.items() if k!='mesh'} for n in gj.get('nodes',[])][:2],
                samplers=gj.get('samplers'),mat=gj.get('materials',[{}])[0])
for p in sys.argv[1:]:
    print('==',p); 
    for k,v in info(p).items(): print('  ',k,':',v)
