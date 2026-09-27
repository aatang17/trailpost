# Trailpost HK — notes for Claude Code

A Hong Kong hiking web app, meant to be "better than AllTrails for HK". The owner is Aaron. He wants plain English: short sentences, everyday words, and concrete numbers with worked examples. All user-facing text is bilingual, English and Traditional Chinese.

It was built in claude.ai and published there as an artifact ("Trailpost HK", https://claude.ai/artifact/4CDNWQhVJzo62eqavzU5BB). This repo is the move to normal hosting and Claude Code.

## Build and run
```
python3 build.py                        # writes dist/index.html + dist/l3/
python3 -m http.server -d dist 8000     # open http://localhost:8000
```
- `build.py` inlines three things into `app/src.html`: Leaflet CSS, `data/geo/data.js` and `app/v3d.js`. The result is one HTML file.
- `app/l3/` holds the 3D assets. They are served next to the page.
- There is no bundler and no npm step for the app itself.
- Libraries come from CDNs:
  - Leaflet 1.9.4 (cdnjs);
  - three.js r128 (cdnjs);
  - OrbitControls and Sky.js from jsdelivr `three@0.128.0/examples/js/`.

## What is where
- **`app/src.html`** — the whole app except the 3D engine:
  - trail list, stage detail, the 999 / distance-post finder, the map and the conditions card;
  - CSS, plus the markup for the 3D dialog (`#v3d`).
  - Helpers: `T(en,zh)` picks the language, `ZH()` tells you whether Chinese is on, `$` is querySelector. Do not name anything `L`, because Leaflet uses that name.
- **`app/v3d.js`** — the 3D Lantau viewer, plain three.js r128. Main parts:
  - **Terrain:** a 5 m grid split into chunks, with a finer mesh near the camera (strides 1/2/4/8). Sharp aerial-photo chunks (`h_r_c.webp`) load only when on screen.
  - **Heights:** `hAt(x,z)` gives ground height from the LiDAR DTM. `Hs()` / `sAt()` give ground plus tree canopy.
  - **Local coordinates:** `x = E − x0hk` and `z = ytophk − N`, in HK1980 grid metres (EPSG:2326). Three.js world = local minus `(G.cx, G.cz)`.
  - **Wider area:** `loadFar` covers Chek Lap Kok, the Hong Kong–Zhuhai–Macao Bridge (`buildBridge`), Zhuhai and Macau.
  - **Clouds and sky:** a live cloud layer (`buildClouds`), a sun set by time of day (`applySun`), height fog (patched ShaderChunk) and Sky.js with a `skyGain` uniform.
  - **Fly mode:** `startFly` / `stepFly`.
  - **Walk mode:** `startWalk` / `stepWalk` / `walkDress` / `walkGrass`. It adds:
    - slope-based pace (Tobler's formula, scaled so the stage takes the official AFCD time): `walkPace`, `paceAt`, `timeLeft`;
    - trail markers: `walkMarks`, `walkCard`, `walkPins`;
    - phone-motion look-around: `gyroDir`, `toggleGyro`;
    - sound: `SND`, `sndStart`, `sndStep`.
- **`app/l3/`** — 3D data:
  - `meta.json`: grid size, stages, distance posts and labels.
  - `dem5/10.webp`: ground heights, stored as R·256 + G − 10.
  - `can5/10.webp`: canopy height, grey value / 4 = metres.
  - `h_*.webp`: aerial photo chunks.
  - `far*`: the wider area, heights stored as R·256 + G − 100.
  - `bridge.json`, `extras.json` (buildings, cable car), `walkpoi.json`, and the `snd_*.mp3` sounds.
- **`data/geo/data.js`** — `window.HK_ROUTES` (trails, stages, posts, transport, safety), `HK_BASE` (map outline) and `HK_COND` (a baked copy of the weather conditions).
- **`data/research/*.json`** — researched stage data: transport, water, exits, safety and sources.
- **`pipeline/`** — the one-off scripts that made the data. Most still hold the original claude.ai working-folder paths (`/tmp/claude-0/.../scratchpad/`), so fix those paths before re-running. Main ones:
  - `geo/build.py`, `geo/finalize.py`: routes from AFCD GPX and OSM distance posts, then `data.js`;
  - `dsm/`: CEDD 2020 LiDAR DSM/DTM (LERC tiles from the Esri China HK ArcGIS service), canopy = DSM − DTM;
  - `far/`: AWS terrarium heights and LandsD satellite imagery;
  - `hzmb/`: the bridge;
  - `cloud/live.py`: live HKO and airport METAR/TAF feed; writes `out/conditions.json` and `out/cams.json`;
  - `poi/build_walkpoi.py`: walk markers;
  - `sound/`: how the sounds were made;
  - `photo3d/`: the LandsD 3D Tiles test pipeline;
  - `video/`: the frame capture used for the AI fly-through video;
  - `scratch/`: older experiments.
- **`photo3d/index.html`** — the LandsD photo-realistic 3D test page. Its data packs are gitignored because they are 47 MB. Rebuild them with `pipeline/photo3d`: `select.py`, then `convert.py`, then `node ktx2raw.js`, then the WebP step, then `decimate.py`.
- **`tools/`** — Playwright checks and screenshots. They run headless Chromium with SwiftShader:
  - launch args: `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`;
  - they expect a copy of the built page as `cap.html`, with `window.__G`, `__V` and `__X` hooks injected after `let D3=null,CH=null,EX=null,G={};`.

## Data sources and credits (these must stay visible in the app)
- **Hong Kong Observatory** open data: weather, warnings and camera photos.
- **Airport METAR/TAF** for VHHH, from aviationweather.gov.
- **Lands Department:**
  - aerial photos: needs the LandsD logo plus "Aerial Photograph from Lands Department";
  - GBA "Satellite Image 2024 (Landsat)";
  - the 5 m DTM.
- **CEDD 2020 LiDAR.**
- **AFCD** trail GPX files and walking times.
- **OpenStreetMap** contributors.
- **AWS Terrain Tiles.**
- **LandsD 3D Visualisation Map** (3D Tiles, `https://data.map.gov.hk/api/3d-data/3dtiles/f2/tileset.json?key=…`):
  - free for commercial and non-commercial use, with credit: "3D Visualisation Map © Lands Department, HKSAR Government. Source: CSDI Portal";
  - get our own free key from 3dmap@landsd.gov.hk. The test used CSDI's published example key;
  - the tiles are b3dm with a Y-up glTF inside. Vertices convert as (x, −z, y), then the tile transform, then ECEF. Textures are KTX2/Basis, but the glTF does not declare `KHR_texture_basisu`;
  - the server echoes CORS for any origin and returns `no-store` headers. There is a 100-concurrent-user cap.

## Differences from the claude.ai artifact
- **Live conditions.** In the artifact, a scheduled task ran `pipeline/cloud/live.py` and wrote the results into the artifact's database (`window.claude.use('db')`, collections `conditions/current` and `conditions/cams`). Outside Claude that API is missing, so the app falls back to the baked `HK_COND`. It needs a replacement: for example, run `live.py` on a schedule (GitHub Actions cron) and have the page fetch `conditions.json`.
- **External data.** Artifacts can only load files published with the page, which is why the 3D data is pre-baked into `app/l3/`. With normal hosting the app can stream LandsD 3D Tiles and imagery directly.

## Known limits
- The 3D view covers only Lantau Stages 2–4. Everything else is 2D.
- Up close in walk mode, the ground is 1.25 m/pixel aerial photo plus drawn grass. The LandsD photo mesh (see `photo3d/`) is the fix, but it needs streaming.
- Mesh decimation with `fast-simplification` scrambled the photo UVs on the LandsD tiles, so it is off (`RED={}`).
- Phone motion was tested only with simulated `deviceorientation` events, not a real phone.

## Likely next steps
1. Host `dist/` on a static host (GitHub Pages or Cloudflare Pages) and set up a scheduled `conditions.json` refresh.
2. Get a LandsD key and stream the photo 3D map along the whole trail in walk mode.
3. Extend 3D and walk mode to more trails, starting with the MacLehose Trail near Tai Mo Shan and the Dragon's Back.
