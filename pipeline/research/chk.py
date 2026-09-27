exec(open('posts.py').read().split("print('---- cumulative")[0].replace('print(','(lambda *a,**k:None)('))
import xml.etree.ElementTree as ET
G='{http://www.topografix.com/GPX/1/1}'
def trk(s):
    r=ET.parse(f's{s}.gpx').getroot()
    return [(float(p.get('lat')),float(p.get('lon')),float(p.find(G+'ele').text)) for p in r.iter(G+'trkpt')]
for s,idxs in ((2,None),):
    pts=trk(s); c=0
    for i in range(1,len(pts)):
        c+=dist(pts[i-1][:2],pts[i][:2])
        if i%150==0 and c<2500: print(round(c),pts[i], 'dStart=%d'%dist(pts[0][:2],pts[i][:2]), 'dM21=%d'%dist(ll[21],pts[i][:2]),'dM22=%d'%dist(ll[22],pts[i][:2]))
print('M20',ll[20],'M21',ll[21],'M22',ll[22])
