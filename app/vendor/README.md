# Saved libraries and font

These are copies of files the app used to load from CDNs. They are kept here so the app works offline.
`build.py` copies them to `dist/vendor/` (except `leaflet.css`, which it inlines into the page).

| File | Source | Licence |
| --- | --- | --- |
| `leaflet.js`, `leaflet.css` | Leaflet 1.9.4, cdnjs | BSD-2-Clause |
| `three.min.js` | three.js r128, cdnjs | MIT |
| `OrbitControls.js`, `Sky.js` | three.js r128 examples (`three@0.128.0/examples/js/`), jsdelivr | MIT |
| `inter-latin.woff2` | Inter variable font, weights 400–700, Latin subset, Google Fonts | SIL Open Font License 1.1 |

Chinese text uses the phone's own font (PingFang HK on iPhone), so no Chinese font is bundled.
