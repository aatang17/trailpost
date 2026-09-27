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
        cv2.imwrite(f'app/lantau/h_{name}.jpg',hi,[cv2.IMWRITE_JPEG_QUALITY,80,cv2.IMWRITE_JPEG_PROGRESSIVE,1])
        lo=cv2.resize(hi,(cb-ca,rb-ra),interpolation=cv2.INTER_AREA)
        cv2.imwrite(f'app/lantau/l_{name}.jpg',lo,[cv2.IMWRITE_JPEG_QUALITY,82])
        pm=cv2.resize(paint[ra:rb+1,ca:cb+1],(cb-ca,rb-ra),interpolation=cv2.INTER_AREA)
        cv2.imwrite(f'app/lantau/m_{name}.jpg',pm,[cv2.IMWRITE_JPEG_QUALITY,84])
        chunks.append({'id':name,'c0':ca,'c1':cb,'r0':ra,'r1':rb})
        print(name,Wp,Hp,os.path.getsize(f'app/lantau/h_{name}.jpg')//1024,'KB')
json.dump({'chunks':chunks},open('app/lantau/chunks.json','w'))
tot=sum(os.path.getsize('app/lantau/'+f) for f in os.listdir('app/lantau'));print('total MB',tot/1e6)
