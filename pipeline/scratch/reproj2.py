import numpy as np,cv2,json,math,os
from pyproj import Transformer
z,X0,X1,Y0,Y1=map(int,open('img/range.txt').read().split());n=2**z
W=(X1-X0+1)*256;H=(Y1-Y0+1)*256
mos=np.zeros((H,W,3),np.uint8)
for x in range(X0,X1+1):
    for y in range(Y0,Y1+1):
        t=cv2.imread(f'img/{z}/{x}_{y}.png',cv2.IMREAD_COLOR)
        if t is not None: mos[(y-Y0)*256:(y-Y0+1)*256,(x-X0)*256:(x-X0+1)*256]=t
print('mosaic',mos.shape)
meta=json.load(open('dem/lantau_meta.json'));x0,ytop,cs=meta['x0'],meta['ytop'],meta['cs']
R,C=meta['shape']
inv=Transformer.from_crs(2326,4326,always_xy=True)
colb=list(range(0,C-1,380))+[C-1];rowb=list(range(0,R-1,360))+[R-1]
paint=cv2.imread('app/lantau-tex.jpg')
chunks=[]
for ri in range(len(rowb)-1):
    for ci in range(len(colb)-1):
        ca,cb,ra,rb=colb[ci],colb[ci+1],rowb[ri],rowb[ri+1]
        xs,xe=(ca+0.5)*cs,(cb+0.5)*cs;zs,ze=(ra+0.5)*cs,(rb+0.5)*cs
        Wp,Hp=(cb-ca)*4,(rb-ra)*4
        gx=xs+(np.arange(Wp)+0.5)*(xe-xs)/Wp;gz=zs+(np.arange(Hp)+0.5)*(ze-zs)/Hp
        GX,GZ=np.meshgrid(gx,gz)
        lon,lat=inv.transform(x0+GX,ytop-GZ)
        mx=((lon+180)/360*n-X0)*256-0.5
        my=((1-np.arcsinh(np.tan(np.radians(lat)))/math.pi)/2*n-Y0)*256-0.5
        hi=cv2.remap(mos,mx.astype(np.float32),my.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        name=f'{ri}_{ci}'
        cv2.imwrite(f'app/l3/h_{name}.webp',hi,[cv2.IMWRITE_WEBP_QUALITY,74])
        np.save(f'/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/img/hi_{name}.npy',cv2.resize(hi,((cb-ca)*2,(rb-ra)*2),interpolation=cv2.INTER_AREA))
        chunks.append({'id':name,'c0':ca,'c1':cb,'r0':ra,'r1':rb})
        print(name,os.path.getsize(f'app/l3/h_{name}.webp')//1024,'KB')
# overview: stitch 2.5 m versions then downscale
full=np.zeros(((R-1)*2,(C-1)*2,3),np.uint8)
for c in chunks:
    a=np.load(f"/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/img/hi_{c['id']}.npy");full[c['r0']*2:c['r1']*2,c['c0']*2:c['c1']*2]=a
ov=cv2.resize(full,(2048,round(2048*full.shape[0]/full.shape[1])),interpolation=cv2.INTER_AREA)
cv2.imwrite('app/l3/overview.webp',ov,[cv2.IMWRITE_WEBP_QUALITY,78])
pm=cv2.resize(paint[:R-1,:C-1],(2048,ov.shape[0]),interpolation=cv2.INTER_AREA);cv2.imwrite('app/l3/map.webp',pm,[cv2.IMWRITE_WEBP_QUALITY,82])
json.dump({'chunks':chunks,'uvw':(C-1)*cs,'uvh':(R-1)*cs},open('app/l3/chunks.json','w'))
tot=sum(os.path.getsize('app/l3/'+f) for f in os.listdir('app/l3'));print('total MB',tot/1e6)
