# pixelate_me

A single-file, browser-based live-visuals studio built on [Hydra](https://hydra.ojack.xyz)
plus a few in-browser ML models. Capture a browser tab or window, use your webcam,
or play a local video, and run it through one of several real-time effect modes.
Nothing is uploaded; all processing happens locally in the browser.

It also runs on the web at
[artificialnouveau.com/smalltools/pixelate_me](https://www.artificialnouveau.com/smalltools/pixelate_me/).

Everything is in `run.html`. No build step.

Click the **&#9432; info** button (top-left, next to Hide) for a per-mode explainer:
what the mode does, what the on-screen boxes / links / labels ("nodes") mean, and a
one-line description of every slider. Each slider also shows the same text on hover.

## Run

```bash
python3 -m http.server 8000
# open http://localhost:8000/run.html
```

Pick a **mode** from the dropdown, set any sliders, click **Run**, and (for capture
modes) choose the tab/screen to capture. Press **Hide** to clear the UI; the small
toggle in the top-left brings it back.

## Modes

- **Melting** — captured stream pushed through a heavy Hydra glitch; detected faces
  "melt" as distorted ellipses with thin frames and curvy links. Optional webcam
  blend, and an optional OCR pass that floats copies of any on-screen text/numbers.
- **PixelCrash glitch** — segments people out of the captured video and renders them
  as ASCII characters (body-part labels, or your own text). Optional webcam-body overlay.
- **Karaoke (local)** — plays a downloaded file: auto-synced lyrics from
  [lrclib.net](https://lrclib.net), face-multiply copies (incl. webcam),
  volume-reactive lyric size.
- **Karaoke (capture)** — tab-capture variant with multiply + volume; manual sync.
- **Focal points** — the stream melts into soft colour blobs; labelled boxes track
  the image's focal points with a dashed, curvy web.

A shared **FPS** slider throttles any mode for a clean, slower frame-stepped look.

## Karaoke library (local mode)

Local karaoke plays downloaded files. Add songs with the helper (needs `yt-dlp` + `ffmpeg`):

```bash
./add-song.sh "https://www.youtube.com/watch?v=..."
```

It downloads the video next to `run.html` and updates `karaoke-videos.json`, so the
song shows up in the **Library** dropdown. Video files (`*.mp4`) are gitignored.

## Dependencies

Loaded from CDNs at runtime (no install): Hydra (`hydra-synth`),
MediaPipe Tasks Vision (face detection + selfie segmentation), Tesseract.js (OCR).
The karaoke helper uses `yt-dlp` and `ffmpeg` locally.

## Notes / browser limits

- Effects that read pixels (Melting, PixelCrash, focal, karaoke) need a same-origin
  or capturable source. Local karaoke uses a downloaded file (same-origin), so pixel
  effects + audio analysis + exact lyric sync all work.
- Camera/screen capture and audio require a user gesture and permission.
