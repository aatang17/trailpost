import numpy as np
from PIL import Image
from scipy import ndimage as nd
a=np.array(Image.open('/mnt/user-data/uploads/1790412952600_image.png').convert('RGB')).astype(int)
r,g,b=a[...,0],a[...,1],a[...,2]
mx,mn=a.max(-1),a.min(-1)
cls=np.zeros(r.shape,int)   # 0 unknown,1 water,2 green,3 urban
water=((b-r>40)&(b>200)&(g>190)) | ((b-r>=5)&(b>=g)&(mn>225))       # sea + bluish-white label halos
green=(g-r>=8)&(g>=b-2)&(g>150)&~water
urban=(mn>180)&~water&~green&(mx-mn<45)                              # light neutral/grey/beige = built-up + roads
cls[water]=1;cls[green]=2;cls[urban]=3
# unknown (text, icons) -> nearest known class
idx=nd.distance_transform_edt(cls==0,return_distances=False,return_indices=True)
cls=cls[idx[0],idx[1]]
land=cls!=1
st=nd.generate_binary_structure(2,1)
R=6
core=nd.binary_opening(land,structure=st,iterations=R)
lab,n=nd.label(core); comp=lab==lab[380,470]
isl=nd.binary_dilation(comp,structure=st,iterations=R+2)&land
isl=nd.binary_fill_holes(isl)
res=isl&(cls==1); gr=isl&(cls==2); ur=isl&(cls==3); T=isl.sum()
print('green%',round(gr.sum()/T*100,1),'reservoir%',round(res.sum()/T*100,1),'urban%',round(ur.sum()/T*100,1))
out=np.full(a.shape,255,np.uint8); out[cls==1]=[200,225,245]; out[land&~isl]=[230,200,200]
out[gr]=[40,150,60]; out[ur]=[150,150,150]; out[res]=[30,90,200]
Image.fromarray(out).save('mask3.png')
