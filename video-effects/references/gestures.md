# Align effects to visible action

Measure preparation, peak and recovery in the actual selected take. A cue is
not a keyword: an expanding hand can invite a push-in; a pinch returning to the
body can invite a pullback. Use local frame numbers after the source trim.
Leave complete speech and a readable effect hold. A freeze starts after the pose
is ready, not on the word 'freeze' by default.

Default Snap Zoom is a genuine one-frame step. For a measured push/pull use:

```json
{"refinement":"gesture-v3", "zoomKeys":[
  {"frame":0,"scale":1},{"frame":18,"scale":1.72},
  {"frame":32,"scale":0.94},{"frame":40,"scale":1}
], "cueFrames":{"snap1":18,"snap2":32},"motionFrames":[18,32]}
```

These values are examples, never timings to apply blindly to a new performer.
See [template details](scene-craft.md) for all validated cue names and bounds.
Studio reveal should meet the look/gesture; a B-roll insert needs time to read;
Frame Break should meet the impact. Textured fragments need `breakStill` from
that exact local break frame. Current templates share a whole-scene camera;
video, titles and graphics move together.

## Optional source preparation

```sh
python3 video-effects/scripts/prepare_media.py segment --input clip.mp4 --output new-matte --fps 30
python3 video-effects/scripts/prepare_media.py track --input clip.mp4 --output new-track --fps 30
```

macOS only. Uses installed Swift + Vision, no downloaded model or uploads.
Produces cached cutout.webm or tracking.json with source hashes and raw landmarks
under processed/. The tracker follows hand position, not semantic gesture intent.
Check hair, glasses, hands, occlusion and confidence. A cache for another source
or range must not be reused.

## Finger-following timer

With refinement gesture-v3, supply `timerTrack` containing one `{x,y}` point per
local frame. Each point is the panel's top-center in the1080x1920 scene before
the shared scene-camera transform. The person is translatedY(-80) and scaled.75:
for already normalized1080x1920 source landmarks x/y in0..1, convert as
`panelX=135+810*x`, `panelY=160+1440*y+gap`. An approximately30px gap is a starting
point. Select the same actual index fingertip consistently; do not switch hands
or interpolate long confidence gaps. Cue visibility only during a reliable
tracked interval, or choose a static timer placement/reframe the source.

Validated panel bounds:x200–880,y500–1260. Do not clamp an offscreen finger to
invent a visible association. Review actual video across the complete interval.
The template plays coordinates; it does not discover or approve them itself.
It shows elapsed seconds after the timer cue, not a compressed fake countdown.
