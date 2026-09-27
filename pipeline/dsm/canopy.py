import numpy as np,lerc,json,math,os
from pyproj import Transformer
z,X0,X1,Y0,Y1=map(int,open('range.txt').read().split())
res=4.77731426794937;O=20037508.342787
def mosaic(s):
    nx,ny=X1-X0+1,Y1-Y0+1;M=np.full((ny*256+1,nx*256+1),np.nan,np.float32)
    for x in range(X0,X1+1):
        for y in range(Y0,Y1+1):
            b=open(f'tiles/{s}_{x}_{y}.lerc','rb').read()
            if not b: continue
            r=lerc.decode(b);a=r[1].astype(np.float32)
            if len(r)>2 and r[2] is not None and np.size(r[2])==a.size: a[np.asarray(r[2]).reshape(a.shape)==0]=np.nan
            a[(a<-100)|(a>2000)]=np.nan
            j0,i0=(y-Y0)*256,(x-X0)*256
            M[j0:j0+257,i0:i0+257]=np.where(np.isnan(a),M[j0:j0+257,i0:i0+257],a)
    return M
DSM,DTM=mosaic('DSM'),mosaic('DTM')
print('mosaic',DSM.shape,np.isnan(DSM).mean(),np.isnan(DTM).mean())
meta=json.load(open('../dem/lantau_meta.json'));x0,ytop,cs=meta['x0'],meta['ytop'],meta['cs'];R,C=meta['shape']
E=x0+(np.arange(C)+0.5)*cs;N=ytop-(np.arange(R)+0.5)*cs;EE,NN=np.meshgrid(E,N)
t=Transformer.from_crs(2326,3857,always_xy=True);MX,MY=t.transform(EE,NN)
fi=(MX+O)/res-X0*256;fj=(O-MY)/res-Y0*256
def samp(M):
    i0=np.clip(np.floor(fi).astype(int),0,M.shape[1]-2);j0=np.clip(np.floor(fj).astype(int),0,M.shape[0]-2);a=fi-i0;b=fj-j0
    return (M[j0,i0]*(1-a)*(1-b)+M[j0,i0+1]*a*(1-b)+M[j0+1,i0]*(1-a)*b+M[j0+1,i0+1]*a*b).astype(np.float32)
dsm,dtm=samp(DSM),samp(DTM)
np.save('dsm_grid.npy',dsm);np.save('dtm_grid.npy',dtm)
old=np.load('../dem/lantau5m.npy').astype(np.float32)
ok=~np.isnan(dtm)&(old>1)
print('grid',dsm.shape,'nan dtm',np.isnan(dtm).mean(),'dtm-old on land: median',np.nanmedian((dtm-old)[ok]),'p5/p95',np.nanpercentile((dtm-old)[ok],[5,95]))
can=dsm-dtm;print('canopy p50/p90/p99/max',np.nanpercentile(can[ok],[50,90,99]),np.nanmax(can))
print('peak area max dtm',np.nanmax(dtm),'dsm',np.nanmax(dsm))
