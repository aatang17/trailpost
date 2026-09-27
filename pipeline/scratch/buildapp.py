import sys,re
css=open('package/dist/leaflet.css').read().replace('behavior: url(#default#VML);','behavior: none;')
css=re.sub(r'background-image: url\(images/[^)]*\);','background-image: none;',css)
s=open('app/src.html').read()
out=s.replace('/*LEAFLET_CSS*/',css).replace('/*DATA*/',open('geo/data.js').read()).replace('/*V3D*/',open('app/v3d.js').read())
open(sys.argv[1] if len(sys.argv)>1 else 'app/trailpost.html','w').write(out)
