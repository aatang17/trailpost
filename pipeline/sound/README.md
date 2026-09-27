# Walk sounds

`app/l3/snd_wind.mp3`, `snd_forest.mp3` and `snd_steps.mp3` were generated with ElevenLabs Sound Effects v2 (flow GdgvkE3nvSn0K6YnqzrF in Aaron's ElevenLabs workspace), then processed with ffmpeg + numpy:

- **wind / forest**: 20 s seamless loops (ElevenLabs `loop: true`), mono 44.1 kHz, loudness-matched, with the first 0.5 s appended to the end so MP3 decoder padding never leaves a gap. The app loops from `off` to `off + 20 s`.
- **steps**: 10 single footsteps cut from an 8 s "footsteps on a gravel mountain path" clip at detected onsets (60 ms pre-roll, 0.42 s long, fades), laid out in one sprite. Start times and lengths are in `snd.json` and hard-coded in `SND.meta` in `app/v3d.js`; keep the two in sync if you regenerate.

Prompts used:
- Wind: "Steady mountain wind blowing across an open grassy ridge high above the sea, soft gusts rustling tall dry grass, natural outdoor ambience"
- Forest: "Subtropical hillside forest ambience in Hong Kong in late summer: steady chorus of cicadas, occasional distant birdsong, light breeze in leaves"
- Steps: "Close-up footsteps of one hiker walking steadily on a dry dirt and gravel mountain path, hiking boots, clear separate steps about two per second, quiet background"
