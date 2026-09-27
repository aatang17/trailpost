import numpy as np
from PIL import Image
from scipy import ndimage as nd
a=np.array(Image.open('/mnt/user-data/uploads/1790412952600_image.png').convert('RGB')).astype(int)
r,g,b=a[...,0],a[...,1],a[...,2]
water=(b-r>40)&(b>200)&(g>190)          # sea blue ~ (160,215,234)
water|=(abs(r-160)<25)&(abs(g-215)<25)&(abs(b-234)<20)
water=nd.binary_opening(water,iterations=1)
land=~water
# cut thin bridges/roads/tunnel lines across water
landc=nd.binary_opening(land,iterations=6)
lab,n=nd.label(landc)
seed=lab[380,470]  # The Peak
isl=lab==seed
isl=nd.binary_fill_holes(isl)
green=(g-r>=12)&(g>=b)&(g>150)
print('island px',isl.sum(),'green px',(isl&green).sum(),'pct',(isl&green).sum()/isl.sum()*100)
ys,xs=np.where(isl);print('bbox',xs.min(),xs.max(),ys.min(),ys.max())
out=np.full(a.shape,255,np.uint8)
out[isl&green]=[40,150,60]; out[isl&~green]=[150,150,150]; out[~isl&land]=[230,200,200]; out[water]=[200,225,245]
Image.fromarray(out).save('mask.png')
