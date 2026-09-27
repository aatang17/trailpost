import json
from shapely.geometry import shape, mapping, Polygon, LineString, box
from shapely.ops import unary_union, polygonize, linemerge
BB=box(113.82,22.14,114.45,22.57)
from shapely.geometry import MultiPolygon
def polys(g):
    if g.geom_type=='Polygon': return g
    if g.geom_type=='MultiPolygon': return g
    ps=[x for x in getattr(g,'geoms',[]) if x.geom_type in('Polygon','MultiPolygon')]
    return unary_union(ps)
def rnd(g,n=4):
    g=polys(g)
    def r(c): return [round(c[0],n),round(c[1],n)]
    gj=mapping(g)
    def walk(x):
        if isinstance(x[0],(float,int)): return r(x)
        return [walk(y) for y in x]
    return {'type':gj['type'],'coordinates':walk(gj['coordinates'])}
land=shape(json.load(open('land_raw.geojson')))
# drop tiny islets < 0.01 km2
km2=111.32*103.0
land=unary_union([p for p in land.geoms if p.area*km2>0.004])
landS=land.simplify(0.00012,preserve_topology=True)
def rel_polys(e):
    ways=[LineString([(p['lon'],p['lat']) for p in m['geometry']]) for m in e.get('members',[]) if m.get('type')=='way' and m.get('geometry') and m.get('role','outer') in ('outer','')]
    inner=[LineString([(p['lon'],p['lat']) for p in m['geometry']]) for m in e.get('members',[]) if m.get('type')=='way' and m.get('geometry') and m.get('role')=='inner']
    po=unary_union(list(polygonize(linemerge(ways)))) if ways else None
    if po is not None and inner:
        pi=list(polygonize(linemerge(inner)))
        if pi: po=po.difference(unary_union(pi))
    return po
parks=[]
for e in json.load(open('parks.json'))['elements']:
    g=rel_polys(e)
    if g is None or g.is_empty: continue
    g=g.intersection(land).simplify(0.00015,preserve_topology=True)
    t=e['tags'];nm=t.get('name','');en=t.get('name:en') or nm;zh=t.get('name:zh') or nm
    parks.append({'type':'Feature','properties':{'en':en,'zh':zh},'geometry':rnd(g)})
res=[]
for e in json.load(open('res.json'))['elements']:
    if e['type']=='way':
        c=[(p['lon'],p['lat']) for p in e['geometry']]
        if len(c)<4 or c[0]!=c[-1]: continue
        g=Polygon(c)
    else: g=rel_polys(e)
    if g is None or g.is_empty or not g.is_valid and not (g:=g.buffer(0)): continue
    if g.area*km2<0.08: continue
    t=e['tags'];res.append({'type':'Feature','properties':{'en':t.get('name:en',''),'zh':t.get('name:zh',t.get('name',''))},'geometry':rnd(g.simplify(0.0001,preserve_topology=True))})
out={'land':rnd(landS),'parks':{'type':'FeatureCollection','features':parks},'res':{'type':'FeatureCollection','features':res}}
s=json.dumps(out,separators=(',',':'),ensure_ascii=False)
open('basemap.json','w').write(s)
print('land polys',len(landS.geoms),'parks',len(parks),'res',len(res),'bytes',len(s))
