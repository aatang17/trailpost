#!/usr/bin/env python3
"""Build Trailpost HK into dist/: one self-contained index.html plus the 3D assets in dist/l3/,
the saved libraries and font in dist/vendor/, the icons, the home-screen manifest and the offline service worker.
Usage: python3 build.py   then serve dist/ with any static web server (e.g. python3 -m http.server -d dist 8000)."""
import hashlib, json, os, re, shutil
ROOT = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(ROOT, *a)
css = open(p('app/vendor/leaflet.css')).read().replace('behavior: url(#default#VML);', 'behavior: none;')
css = re.sub(r'background-image: url\(images/[^)]*\);', 'background-image: none;', css)
html = open(p('app/src.html')).read()
html = html.replace('/*LEAFLET_CSS*/', css).replace('/*DATA*/', open(p('data/geo/data.js')).read()).replace('/*V3D*/', open(p('app/v3d.js')).read())
os.makedirs(p('dist'), exist_ok=True)
head = '<!doctype html>\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
open(p('dist/index.html'), 'w').write(head + html)

# folders served next to the page
for src, dst in [('app/l3', 'dist/l3'), ('app/icons', 'dist/icons')]:
    if os.path.exists(p(dst)): shutil.rmtree(p(dst))
    shutil.copytree(p(src), p(dst))
if os.path.exists(p('dist/vendor')): shutil.rmtree(p('dist/vendor'))
shutil.copytree(p('app/vendor'), p('dist/vendor'), ignore=shutil.ignore_patterns('*.css', '*.md'))  # leaflet.css is inlined above

# home-screen install (Add to Home Screen)
manifest = {
    'name': 'Trailpost HK', 'short_name': 'Trailpost',
    'description': "Hong Kong trails, checked against today's weather.",
    'lang': 'en', 'start_url': './', 'scope': './', 'display': 'standalone',
    'background_color': '#ffffff', 'theme_color': '#ffffff',
    'icons': [{'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
              {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}],
}
open(p('dist/manifest.webmanifest'), 'w').write(json.dumps(manifest, indent=1, ensure_ascii=False))

# offline support: the service worker saves the app shell on install, and 3D files as they are opened
def files(d):
    return sorted(os.path.relpath(os.path.join(a, f), p('dist')).replace(os.sep, '/') for a, _, fs in os.walk(p(d)) for f in fs if not f.startswith('.'))
def digest(paths):
    h = hashlib.sha256()
    for f in paths: h.update(f.encode()); h.update(open(p('dist', f), 'rb').read())
    return h.hexdigest()[:10]
core = ['index.html', 'manifest.webmanifest'] + files('dist/vendor') + files('dist/icons')
sw = open(p('app/sw.js')).read()
sw = sw.replace('__CORE__', digest(core)).replace('__DATA__', digest(files('dist/l3'))).replace('__PRECACHE__', json.dumps(['./'] + core))
open(p('dist/sw.js'), 'w').write(sw)
print('built dist/index.html', round(os.path.getsize(p('dist/index.html')) / 1e6, 2), 'MB · saved for offline on install:',
      round(sum(os.path.getsize(p('dist', f)) for f in core) / 1e6, 2), 'MB')
