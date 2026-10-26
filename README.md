# Video Effects

**25 reusable vertical-video effects for Codex and Claude Code.**

[中文说明](README.zh-CN.md) · [Effect catalog](video-effects/references/catalog.md) ·
[MIT license](LICENSE) · [Validation](VALIDATION.md)

Give the agent your clip and describe what you want. It chooses an effect by
content, inspects the action, writes parameters and renders a new 1080x1920/30fps
MP4 using HTML/GSAP and headless Chrome through HyperFrames. Three.js powers the
procedural phone. This release contains the effect library only, not the full
Creator Kit editor or a publishing service.

## Install

```sh
git clone https://github.com/shawn137080/video-effects.git
cd video-effects
python3 install.py --agent codex
# Or: python3 install.py --agent claude
```

Installation copies the verified skill to `~/.codex/skills/video-effects` or
`~/.claude/skills/video-effects`. It does not install dependencies or change other
skills. Existing installs are preserved; explicit `--upgrade` creates a full
backup. `--root /path/to/test-skills` supports isolated installation. Remove the
installed folder to uninstall; restore its backup folder to roll back.

Requires Python 3.10+, Node 20+, FFmpeg/FFprobe, Chrome, locally installed GSAP and
HyperFrames. Configure paths using [setup](video-effects/references/setup.md).
Native render qualification is macOS; other OS/runtime versions need a smoke
test. Optional cutout and hand-landmark helpers use macOS Vision + installed Swift.
No paid services, API keys or downloaded models are required by this package.

## Ask your agent

> Use $video-effects on this clip. Follow my hand: push in as it opens and pull
> back when I pinch. Keep my original voice and show me a new MP4 preview.

> 用 video-effects 做个指尖下方的计时器，跟着我这段手势走。保留原声，先看预览。

The agent authors the JSON; users do not need to. Each family has a descriptor
under `video-effects/effects/`. Shared code lives in `scripts/scene_craft.py`.

## Effects

Orbit · Chat Takeover · Frame Escape · Snap Zoom / gesture zoom · Checklist ·
Headline Storm · Zoom Portal · Growth Metric · Studio Reveal · B-roll Overlay ·
Paper Cutout · Dolly Zoom · Magazine Cover · Liquid Glass · Zoom Through Cut ·
Green Screen · Frame Break · 3D Phone Mockup · Timer · Media Wall · Spotlight ·
Freeze Callout · Before / After · Text Behind · Doodle.

25 families, with stable numeric IDs that intentionally contain gaps after
merging duplicate modes. The catalog explains required mattes/media/data.

## Run a standalone effect

```sh
python3 video-effects/scripts/effects.py catalog
python3 video-effects/scripts/effects.py build --params effect.json --output outputs/zoom-v1
python3 video-effects/scripts/effects.py render --project outputs/zoom-v1 --output outputs/zoom-render-v1
```

See [parameters](video-effects/references/parameters.md) and
[gesture timing](video-effects/references/gestures.md). New output folders are
required. Render checks the compiled source/code receipt, invokes native check,
encodes MP4, decodes every frame, and saves start/mid/end inspection images.
These checks do not certify aesthetics, audio acceptance or another host's
production source-preservation audit. Inspect faces, text, hands and sound.

The camera moves the whole scene: subject, titles and graphics. Effects also
have their own motion. Manual cue frames and optional measured hand tracks align
the two. Tracking is not automatic understanding of gesture intent.

## Synthetic smoke example

```sh
python3 examples/make_fixture.py --output outputs/example-v1
python3 video-effects/scripts/effects.py build --params outputs/example-v1/14-liquid-glass.json --output outputs/glass-v1
python3 video-effects/scripts/effects.py render --project outputs/glass-v1 --output outputs/glass-render-v1
```

The fixture is abstract geometry, explicitly not a talking-head quality sample.
It creates source media and 25 input configs locally; no private recordings or
matte cache is in this repository. Use real source-bound assets for production.

## Development / distribution

```sh
python3 -m unittest discover -s tests -v
python3 tools/release.py --check
# After deliberate source changes:
python3 tools/release.py --manifest
python3 tools/release.py --output dist/video-effects-v1.0.0.zip
```

The manifest is an integrity inventory, not a cryptographic author signature.
MIT applies to our code; Three.js and fonts retain their notices. External
runtimes are not bundled. See [third-party notices](THIRD-PARTY.md).
