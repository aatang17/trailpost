#!/usr/bin/env python3
"""Build Trailpost HK into dist/: one self-contained index.html plus the 3D assets in dist/l3/.
Usage: python3 build.py   then serve dist/ with any static web server (e.g. python3 -m http.server -d dist 8000)."""
import os, re, shutil
ROOT = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(ROOT, *a)
css = open(p('app/vendor/leaflet.css')).read().replace('behavior: url(#default#VML);', 'behavior: none;')
css = re.sub(r'background-image: url\(images/[^)]*\);', 'background-image: none;', css)
html = open(p('app/src.html')).read()
html = html.replace('/*LEAFLET_CSS*/', css).replace('/*DATA*/', open(p('data/geo/data.js')).read()).replace('/*V3D*/', open(p('app/v3d.js')).read())
os.makedirs(p('dist'), exist_ok=True)
head = '<!doctype html>\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
open(p('dist/index.html'), 'w').write(head + html)
if os.path.exists(p('dist/l3')): shutil.rmtree(p('dist/l3'))
shutil.copytree(p('app/l3'), p('dist/l3'))
print('built dist/index.html', round(os.path.getsize(p('dist/index.html')) / 1e6, 2), 'MB')
