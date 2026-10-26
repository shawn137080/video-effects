# Standalone effect parameters

Commands use `python3 <skill>/scripts/effects.py`. Build one effect at a time:
`build --params effect.json --output new-composition`; then
`render --project new-composition --output new-render`.

```json
{
  "effect": 4,
  "inputFile": "clip.mp4",
  "startTime": 0,
  "duration": 3.6,
  "mainText": "Look closer",
  "subText": "Follow the gesture",
  "accentColor": "#efe282",
  "cueFrames": {"snap1": 18, "snap2": 36},
  "motionFrames": [18, 36],
  "sourceAudio": true
}
```

Paths are relative to the JSON file, or absolute local paths. No URLs, downloads,
paid APIs or automatic external calls. Output is always1080x1920/30fps. Inputs
normalize by centered cover crop; preframe your source if its subject is off-center.
`startTime` and `duration` use seconds on the30fps grid; cue frames are local to
that selection. The output starts at0. Duration range0.6–30s. `sourceAudio` defaults
true; it preserves selected source voice at1x with no background music added.

| Parameter | Meaning |
|---|---|
| effect | Stable family ID from catalog, not display position |
| mainText/subText | Content authored for this effect; limits28/52characters |
| accentColor | Six-digit hex; common accent, not a global recolor of all materials |
| mediaFile | Required secondary image/video for Portal, B-roll, Dolly, Green Screen, Before/After; optional through-cut surface |
| mediaStartTime | Secondary video in-point, default0 |
| cutoutFile | Matching alpha video (or transparent still for a still subject) |
| cutoutStartTime | Default startTime; set0 for a cutout already trimmed to the selected clip |
| cardFiles | 3–6 supplied images for Orbit or Media Wall |
| items/payoff | Short real statements:1–4 for Chat/Checklist,1–3 plus payoff for Headline Storm |
| dataPoints/dataSource | 2–8 finite numbers and their genuine provenance for Growth |
| freezeFrame | Local pose frame for Magazine or Freeze; default freeze extraction occurs on the current source |
| freezeFile | Optional explicitly source-matched still; never a previous presenter's image |
| nextFile/nextStartTime | Required incoming video for Through Cut |
| nextDuration | Incoming hold, default0.8s; appended to effect duration, minimum0.6s |
| cueFrames/motionFrames | Measured local effect events/shared-scene impulses; see gestures.md |
| timerSeconds | Default timer countdown target; use actual relevant duration |
| locale | en or zh-Hans for built-in text; user-authored text is never translated automatically |
| showTitles | true by default; false hides bottom effect/content title |
| showHeader/header/headerSub | Optional top hierarchy; showHeader defaults false |
| demo | false by default; true displays the showcase counter |

Original numeric IDs include gaps after deduplication. Digital push-in and full
checklist are variations, not duplicate counted families. See each descriptor.

`refinement: "gesture-v3"` supports4,9,10,15,17,21. `zoomKeys`, `timerTrack`,
`breakStill` and `destinationMatte` are advanced source-bound parameters described
in [gestures](gestures.md) and [template details](scene-craft.md). A refined
through-cut destination matte must correspond to the next scene; the generic
next video must already match that composite if a visually continuous join is
required. Inspect the last/first pair; a geometric transition alone does not
promise a seamless shot match.

Keep short text out of the top10% and bottom20%. Existing layouts are starting
points; inspect each new speaker's position. No automatic face-clearance claim.
