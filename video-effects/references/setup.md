# Runtime setup

Python 3.10+, Node 20+, FFmpeg/FFprobe, Chrome, GSAP and HyperFrames are external
requirements. No node_modules, browser, model or runtime license is bundled.
The inherited renderer was exercised with HyperFrames 0.7.109 on macOS; another
version/OS needs a fresh smoke render. Core Python tests also run on Linux.
Optional segmentation/hand tracking require macOS Vision and existing swiftc.

Point to installed runtime files:

```sh
python3 video-effects/scripts/effects.py configure \
  --gsap /path/to/gsap/dist/gsap.min.js \
  --hyperframes /path/to/hyperframes/dist/cli.js \
  --browser /path/to/chrome
python3 video-effects/scripts/effects.py doctor
```

These paths are examples, not downloads. The command creates private
`runtime.local.json` in the installed skill; ignored by Git and refused by release
packaging. Existing configuration is never overwritten. Environment overrides:
`VIDEO_EFFECTS_GSAP`, `VIDEO_EFFECTS_HYPERFRAMES`, `HYPERFRAMES_BROWSER_PATH`.

If missing, tell the operator exactly which runtime is missing and use the
provider's current official installation instructions with their authorization.
Do not copy a licensed personal kit or invoke an auto-downloading npx command.

- HyperFrames: https://github.com/heygen-com/hyperframes
- GSAP: https://gsap.com/docs/v3/Installation/
- FFmpeg: https://ffmpeg.org/download.html

Native check precedes encoding. Source/config/compiler files are hashed; any
changed compiled dependency or compiler invalidates the render receipt. Keep
failed output diagnostics and rebuild into a new folder.
