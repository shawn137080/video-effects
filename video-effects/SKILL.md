---
name: video-effects
description: Build reusable vertical-video effects on supplied footage, including scene motion, overlays, cutouts, gesture-timed zooms and 3D phone mockups. Use to choose, parameterize, render or refine one of 25 effects; not for a full editorial or publishing workflow.
---

# Video Effects

Use this folder as the skill root. The agent chooses and authors parameters;
the user supplies footage and feedback, not a JSON form. Run
`python3 <skill>/scripts/effects.py doctor` before rendering. Configure existing
GSAP, HyperFrames and Chrome paths with `configure`; see
[setup](references/setup.md). Dependencies are external and never auto-installed.

## Choose by content and action

Read [selection](references/selection.md) and [catalog](references/catalog.md).
Choose no effect if movement obscures the point. Ask for missing material only
when it changes execution. Inspect the source and any reference before coding;
track the whole scene when the request is camera shake, not only a single object.
One dominant treatment with restrained accents is usually enough.

For a chosen effect, read [parameters](references/parameters.md), then its
`effects/<id-slug>/effect.json`. Inputs must be the user's actual footage and
matching assets. Do not substitute previous demonstrations or someone else's
matte. Reference videos can inform observable behavior, not provide code/assets.

## Build a source-bound preview

1. Inspect the source frames and spoken phrase. Find the action's preparation,
   peak and recovery. Keep complete words and time to read the effect. `startTime`
   is the source in-point; cues are local integer frames after that trim.
2. Author parameters and run `effects.py build --params CONFIG --output NEW_DIR`.
   Use `showHeader`/`demo` only for an intentional title/card or showcase label.
   Default exported scenes have no demo counter or promotional header.
3. Run `effects.py render --project NEW_DIR --output NEW_RENDER`. Inspect actual
   encoded start/impact/return/end frames, audio joins, face/text clearance and
   alpha edges. Rendering and numeric checks do not establish creative approval.
4. Revise source parameters and use NEW directories/filenames. Never overwrite
   previews, edit compiled HTML behind receipts, or mark user approval yourself.

## Gesture and compositing details

Use [gesture timing](references/gestures.md) for measured zoom curves, trigger
frames, freeze poses and fingertip-following timers. `prepare_media.py segment`
and `track` offer optional local macOS Vision processing; they do not interpret
gesture intent. Hidden/low-confidence fingers must not produce guessed anchors.
Trim raw/matte ranges identically and inspect hair, hands and occlusion.

`scene_craft.py` contains the live effect templates, shared scene camera and
parameter validation. The optional `gesture-v3` treatments include push/pull zoom,
studio lamps/sweep, larger B-roll window, through-cut gate, textured fragments and
a tracked timer. They require fresh measurements for each new take.

## Boundaries

25 effect families, including an outgoing/incoming pair for through-cut. This
package does not include Creator Kit's full edit planner, automatic transcription,
music registry, carousel builder, publication queue or customer media. Original
voice is preserved by default for the selected clip. No cloning or uploads.
If used inside another production system, preserve that system's approval/audit
gates. Standalone previews are not a bypass for final delivery checks.

Original code is MIT; bundled Three.js/fonts retain their notices. See
[third-party notices](references/third-party.md).
