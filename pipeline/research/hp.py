exec(open('posts.py').read().split("print('---- cumulative")[0].replace('print(','(lambda *a,**k:None)('))
import xml.etree.ElementTree as ET
G='{http://www.topografix.com/GPX/1/1}'
for s in range(1,11):
    r=ET.parse(f's{s}.gpx').getroot()
    pts=[(float(p.get('lat')),float(p.get('lon')),float(p.find(G+'ele').text)) for p in r.iter(G+'trkpt')]
    m=max(pts,key=lambda p:p[2])
    near=min(ll,key=lambda n:dist(m[:2],ll[n]))
    gain=sum(max(0,pts[i+1][2]-pts[i][2]) for i in range(len(pts)-1))
    print(s,'max',m,'near M%03d'%near, 'start ele',pts[0][2],'end ele',pts[-1][2],'gain~',round(gain))
