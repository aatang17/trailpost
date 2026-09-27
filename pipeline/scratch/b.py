import numpy as np
from PIL import Image
from scipy import ndimage as nd
a=np.array(Image.open('/mnt/user-data/uploads/1790412952600_image.png').convert('RGB')).astype(int)
r,g,b=a[...,0],a[...,1],a[...,2]
water=((b-r>40)&(b>200)&(g>190))|((abs(r-160)<25)&(abs(g-215)<25)&(abs(b-234)<20))
water=nd.binary_opening(water,iterations=1)
land=~water
st=nd.generate_binary_structure(2,1)
for R in (8,10,12):
    core=nd.binary_opening(land,structure=st,iterations=R)
    lab,n=nd.label(core); comp=lab==lab[380,470]
    isl=nd.binary_dilation(comp,structure=st,iterations=R+2)&land
    isl=nd.binary_fill_holes(isl)
    inland_water=isl&water
    green=(g-r>=12)&(g>=b)&(g>150)&isl
    urban=isl&~green&~water
    T=isl.sum()
    print(R,'total',T,'green%',round(green.sum()/T*100,1),'reservoir%',round(inland_water.sum()/T*100,1),'urban%',round(urban.sum()/T*100,1))
    if R==10:
        out=np.full(a.shape,255,np.uint8); out[water]=[200,225,245]; out[land&~isl]=[230,200,200]
        out[green]=[40,150,60]; out[urban]=[150,150,150]; out[inland_water]=[30,90,200]
        Image.fromarray(out).save('mask2.png')
