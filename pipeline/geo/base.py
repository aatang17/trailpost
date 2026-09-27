import json
from shapely.geometry import LineString, Polygon, box, Point, mapping, MultiPolygon
from shapely.ops import linemerge, unary_union, polygonize
BB=box(113.82,22.14,114.45,22.57)
c=json.load(open('coast.json'))['elements']
lines=[LineString([(p['lon'],p['lat']) for p in w['geometry']]) for w in c if len(w['geometry'])>1]
m=linemerge(lines)
ml=list(m.geoms) if hasattr(m,'geoms') else [m]
print('merged',len(ml),'closed',sum(l.is_closed for l in ml))
clipped=[]
for l in ml:
    x=l.intersection(BB)
    if x.is_empty: continue
    for g in (x.geoms if hasattr(x,'geoms') else [x]):
        if g.geom_type=='LineString' and len(g.coords)>1: clipped.append(g)
U=unary_union(clipped+[BB.exterior])
faces=list(polygonize(U))
print('faces',len(faces))
from shapely.strtree import STRtree
tree=STRtree(faces)
score=[0]*len(faces)
eps=1e-6
for l in clipped:
    cs=list(l.coords)
    step=max(1,len(cs)//20)
    for i in range(0,len(cs)-1,step):
        (x1,y1),(x2,y2)=cs[i],cs[i+1]
        dx,dy=x2-x1,y2-y1; n=(dx*dx+dy*dy)**.5
        if n==0: continue
        mx,my=(x1+x2)/2,(y1+y2)/2
        L=Point(mx-dy/n*eps,my+dx/n*eps); R=Point(mx+dy/n*eps,my-dx/n*eps)
        for pt,v in ((L,1),(R,-1)):
            for j in tree.query(pt):
                if faces[j].contains(pt): score[j]+=v
land=[f for f,s in zip(faces,score) if s>0]
print('land faces',len(land),'unknown',sum(1 for s in score if s==0))
landU=unary_union(land)
print('land area deg2',landU.area)
json.dump(mapping(landU),open('land_raw.geojson','w'))
