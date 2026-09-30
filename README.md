# Trailpost HK

A Hong Kong hiking app. It shows live Observatory weather and hill-cloud conditions, the bus, ferry and minibus to and from every trailhead, and a distance-post finder for 999 calls. It covers all stages of the MacLehose, Wilson, Hong Kong and Lantau trails, plus a 3D Lantau Peak view where you can walk the trail. The app is bilingual, English and 繁體中文.

```
python3 build.py
python3 -m http.server -d dist 8000
```

It works offline once loaded, and can be added to an iPhone home screen from Safari (Share → Add to Home Screen). Both need the app to be served over https, or from localhost.

See `CLAUDE.md` for how the code is organised, where the data comes from, and the credits that must stay in the app.
