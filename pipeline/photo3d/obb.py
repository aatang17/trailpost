import json, math, sys
def ecef(lat,lon,h):
    a=6378137.0; f=1/298.257223563; e2=f*(2-f)
    la,lo=math.radians(lat),math.radians(lon)
    N=a/math.sqrt(1-e2*math.sin(la)**2)
    return ((N+h)*math.cos(la)*math.cos(lo),(N+h)*math.cos(la)*math.sin(lo),(N*(1-e2)+h)*math.sin(la))
def inbox(box,p,tol=0.0):
    c=box[:3]; axes=[box[3:6],box[6:9],box[9:12]]
    d=[p[i]-c[i] for i in range(3)]
    for ax in axes:
        L2=sum(x*x for x in ax); 
        if L2==0: continue
        t=sum(d[i]*ax[i] for i in range(3))/L2
        if abs(t)>1+tol: return False
    return True
def contains(bv,p,latlon):
    if 'box' in bv: return inbox(bv['box'],p)
    if 'region' in bv:
        w,s,e,n,lo,hi=bv['region']; la,lo_=map(math.radians,latlon)
        return w<=lo_<=e and s<=la<=n
    if 'sphere' in bv:
        c=bv['sphere'][:3]; r=bv['sphere'][3]; return math.dist(c,p)<=r
PTS={'true_summit':(22.2492,113.9200,932),'ridge_1km_east':(22.2490,113.9297,633)}
