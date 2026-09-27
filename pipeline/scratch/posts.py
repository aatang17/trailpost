import re,math
# forward UTM WGS84 zone 50
a=6378137.0;f=1/298.257223563;e2=f*(2-f);k0=0.9996;lon0=math.radians(117)
def fwd(lat,lon):
    phi=math.radians(lat);lam=math.radians(lon)
    N=a/math.sqrt(1-e2*math.sin(phi)**2);T=math.tan(phi)**2;ep2=e2/(1-e2);C=ep2*math.cos(phi)**2
    A=math.cos(phi)*(lam-lon0)
    M=a*((1-e2/4-3*e2**2/64-5*e2**3/256)*phi-(3*e2/8+3*e2**2/32+45*e2**3/1024)*math.sin(2*phi)+(15*e2**2/256+45*e2**3/1024)*math.sin(4*phi)-(35*e2**3/3072)*math.sin(6*phi))
    x=k0*N*(A+(1-T+C)*A**3/6+(5-18*T+T*T+72*C-58*ep2)*A**5/120)+500000
    y=k0*(M+N*math.tan(phi)*(A*A/2+(5-T+9*C+4*C*C)*A**4/24+(61-58*T+T*T+600*C-330*ep2)*A**6/720))
    return x,y
import sys
txt=open('raw/dp.txt').read()
posts={}
for no,e,n in re.findall(r'(H\d{3})\s+KK\s+(\d{3})\s+(\d{3})',txt):
    posts[no]=(int(e)*100+50,int(n)*100+50)  # metres within 100km square
# establish square offsets from a known point: stage1 start
x0,y0=fwd(22.2712927825,114.1494947398)
E0=int(x0//100000)*100000;N0=int(y0//100000)*100000
print('square offset',E0,N0,'start utm',x0,y0)
def P(no):
    e,n=posts[no];return E0+e,N0+n
for s in range(1,9):
    t=open(f'raw/s{s}.gpx').read()
    pts=[(float(a),float(b)) for a,b in re.findall(r'lat="([\d.]+)" lon="([\d.]+)"',t)]
    xy=[fwd(*p) for p in pts]
    cum=[0]
    for i in range(1,len(xy)): cum.append(cum[-1]+math.dist(xy[i-1],xy[i]))
    # for each post, nearest track point distance
    near=[]
    for no in sorted(posts):
        px,py=P(no)
        d,i=min((math.dist((px,py),q),i) for i,q in enumerate(xy))
        if d<200: near.append((no,round(d),round(cum[i]/1000,2)))
    print('stage',s,'len %.2f'%(cum[-1]/1000), near)
