import re, math, xml.etree.ElementTree as ET
txt=open('posts.txt').read()
posts={}
cur={}
for line in txt.splitlines():
    toks=re.findall(r'(\d+)\s+(?:([A-Z]{2})\s+)?(\d{3})\s+(\d{3})',line)
    for col,(n,sq,e,nn) in enumerate(toks):
        if sq: cur[col]=sq
        posts[int(n)]=(cur[col],int(e),int(nn))
assert len(posts)==200, len(posts)
a=6378137.0; f=1/298.257223563; k0=0.9996
e2=f*(2-f); ep2=e2/(1-e2)
def utm_inv(zone,E,N):
    x=E-500000; y=N
    M=y/k0; mu=M/(a*(1-e2/4-3*e2**2/64-5*e2**3/256))
    e1=(1-math.sqrt(1-e2))/(1+math.sqrt(1-e2))
    phi1=mu+(3*e1/2-27*e1**3/32)*math.sin(2*mu)+(21*e1**2/16-55*e1**4/32)*math.sin(4*mu)+(151*e1**3/96)*math.sin(6*mu)
    N1=a/math.sqrt(1-e2*math.sin(phi1)**2); T1=math.tan(phi1)**2; C1=ep2*math.cos(phi1)**2
    R1=a*(1-e2)/(1-e2*math.sin(phi1)**2)**1.5; D=x/(N1*k0)
    lat=phi1-(N1*math.tan(phi1)/R1)*(D**2/2-(5+3*T1+10*C1-4*C1**2-9*ep2)*D**4/24+(61+90*T1+298*C1+45*T1**2-252*ep2-3*C1**2)*D**6/720)
    lon=(D-(1+2*T1+C1)*D**3/6+(5-2*C1+28*T1-3*C1**2+8*ep2+24*T1**2)*D**5/120)/math.cos(phi1)
    lon0=math.radians((zone-1)*6-180+3)
    return math.degrees(lat), math.degrees(lon0+lon)
sqmap={'KK':(50,200000,2400000),'JK':(50,100000,2400000),'HE':(49,800000,2400000)}
ll={}
for n,(sq,e,nn) in posts.items():
    z,E0,N0=sqmap[sq]
    ll[n]=utm_inv(z,E0+e*100+50,N0+nn*100+50)
def dist(p,q):
    dy=(p[0]-q[0])*111320; dx=(p[1]-q[1])*111320*math.cos(math.radians(22.4))
    return math.hypot(dx,dy)
ns={'g':'http://www.topografix.com/GPX/1/1'}
tracks={}
for s in range(1,11):
    r=ET.parse(f's{s}.gpx').getroot()
    pts=[(float(p.get('lat')),float(p.get('lon'))) for p in r.iter('{http://www.topografix.com/GPX/1/1}trkpt')]
    eles=[float(p.find('g:ele',ns).text) for p in r.iter('{http://www.topografix.com/GPX/1/1}trkpt') if p.find('g:ele',ns) is not None]
    tracks[s]=pts
    L=sum(dist(pts[i],pts[i+1]) for i in range(len(pts)-1))
    print(f"S{s}: {len(pts)} pts len={L/1000:.2f}km start={pts[0]} end={pts[-1]} maxele={max(eles) if eles else None}")
# assign posts
assign={}
for n,p in ll.items():
    best=None
    for s,pts in tracks.items():
        d=min(dist(p,q) for q in pts[::2])
        if best is None or d<best[1]: best=(s,d)
    assign[n]=best
for s in range(1,11):
    ps=[n for n in assign if assign[n][0]==s]
    far=[(n,round(assign[n][1])) for n in ps if assign[n][1]>150]
    print(s, min(ps), max(ps), len(ps), 'far:',far)
# nearest posts to each section start/end
for s,pts in tracks.items():
    for lab,pt in (('start',pts[0]),('end',pts[-1])):
        near=sorted(((round(dist(pt,ll[n])),n) for n in ll))[:3]
        print(s,lab,near)
print('---- cumulative along full track')
full=[];cum=[];bounds=[0];c=0
for s in range(1,11):
    pts=tracks[s]
    for i,p in enumerate(pts):
        if full: c+=dist(full[-1],p)
        full.append(p);cum.append(c)
    bounds.append(c)
print('bounds km',[round(b/1000,2) for b in bounds])
for n in [1,19,20,21,22,48,49,50,51,67,68,69,70,93,94,95,96,114,115,116,117,123,124,125,126,136,137,138,139,154,155,156,157,167,168,169,170,199,200]:
    i=min(range(len(full)),key=lambda j:dist(ll[n],full[j]))
    sec=max(k for k in range(10) if bounds[k]<=cum[i])+1
    print(n, 'at %.2f km'%(cum[i]/1000), 'sec',sec, 'off %dm'%dist(ll[n],full[i]), 'to next bound %.0fm'%(bounds[sec]-cum[i]))
