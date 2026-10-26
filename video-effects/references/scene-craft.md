# Template typography and refinement details

## Typography

Set `typography: "editorial-condensed"` for Barlow Condensed ExtraBold headings
and effect names, with Inter supporting titles and speech captions. This changes
font family, case, size, spacing and shadow only; camera, cuts, voice and effect
keyframes stay unchanged. Omit it or use `classic` to retain the original Manrope
hierarchy. Fonts and OFL notices are bundled in `effects/_assets/typography`;
`SOURCES.json` records upstream URLs and hashes. Inspect the longest labels and
small supporting text on the actual source before accepting a new render.

## Source gesture timing

For measured source gestures, `design.cueFrames` can override the local 30fps
(or plan fps) effect trigger: Orbit `orbit`; Chat `takeover`; Escape `escape`;
Snap `snap1`, `snap2`; Headlines `head0`–`head3`, `resolve`; Portal `open`,
`expand`; Magazine `cover`; Frame Break `break`; Timer `timer`; Wall `wall`;
Comparison `compare`; Doodle `draw`. Values are integer local frames, not seconds.
Use `design.motionFrames` for the matching whole-scene impulses and author sound
frames from the same measured cues. Empty motionFrames disables impulses for a
beat while retaining continuous scene drift. Unknown or out-of-shot cues fail.

Inspect the source gesture first. Magazine `freeze` must be a still extracted
from precisely its `cover` frame. A later trigger needs enough frames for the
result to settle; extend the same shot and aligned alpha if needed. Never delay
an effect beyond the shot or cut off speech to force a gesture into a template.
These cues are manually authored evidence, not automatic hand tracking.

## Opt-in source-led refinements

`design.refinement: "gesture-v3"` enables six alternate treatments, leaving
existing plans unchanged. Study the source before authoring parameters:

- 04: `zoomKeys` is an ordered array of local integer `frame` and `scale`
  values. Each scale must be 0.8–2; use 2–12 points. Follow both hand expansion
  and contraction, rather than assuming every gesture means another punch-in.
- 09: `cueFrames.reveal` synchronizes the studio sweep, lights and source matte.
  Extend the exact source and alpha together if a gaze arrives after speech.
- 10: `cueFrames.insert` / `exit` time a raised secondary-video window. Supply
  an actual `secondary` asset; inspect its crop and clearance from the face.
- 15: `cueFrames.approach` / `pass` time the depth gate and accelerating push.
  `destinationMatte` must identify the corresponding incoming scene subject.
  Inspect the final transition frame against the next scene at normal speed.
- 17: `breakStill` is a source-frame asset for textured flying fragments;
  extract it at `cueFrames.break`, not from an unrelated demo.
- 21: `timerTrack` contains exactly one `{x, y}` coordinate per local frame,
  in the untransformed 1080x1920 scene. These are the panel's top-center;
  validated ranges are x 200–880 / y 500–1260. The refined person uses
  translateY(-80px), scale(.75); transform source landmarks accordingly, add a
  visible finger-to-panel gap, and check the entire tracked range. Coordinates
  must come from the current source or explicit frame inspection. The template
  does not itself run a tracker. The counter shows elapsed time after its cue.

All six treatments inherit the shared scene camera. Author matching sound and
motion-frame anchors separately. Recompile into a new folder after changing
compiler code; old hash-bound receipts cannot authorize changed implementations.
