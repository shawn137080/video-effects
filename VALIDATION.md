# Release validation

Validated on 2026-10-25 with HyperFrames 0.7.109, existing Chrome and FFmpeg on macOS.

- 39 standalone unit/distribution tests passed.
- Skill format validation passed.
- All 25 synthetic fixture configurations compiled and rendered from a clean installed skill.
- Each MP4 passed native layout/contrast checks, geometry/frame-count checks, full decode and per-frame white-band screening.
- All outputs are 1080x1920 at 30fps: 24 are 108 frames; Through Cut includes its incoming shot and is 132 frames.
- Encoded midpoint contact sheets were inspected for all 25. The four adjusted text treatments (Frame Escape, Paper Cutout, Phone, Text Behind) also had start/mid/end images inspected.
- Optional Vision track and segment commands completed on a 4-frame synthetic source; tracking correctly returned no visible hands.

[Render result hashes](tests/render-smoke-results.json) bind the smoke results to the effect compiler. Generated media is intentionally excluded from the repository. Font-source hashes were also checked against their bundled manifests.

## Reproduce

Configure the external runtime first using the setup guide, then:

```sh
python3 -m unittest discover -s tests -v
python3 tools/release.py --check
python3 examples/make_fixture.py --output outputs/fixture-v1
for config in outputs/fixture-v1/[0-9][0-9]-*.json; do
  name=$(basename "$config" .json)
  python3 video-effects/scripts/effects.py build --params "$config" --output "outputs/compiled-v1/$name"
  python3 video-effects/scripts/effects.py render --project "outputs/compiled-v1/$name" --output "outputs/rendered-v1/$name"
done
```

Use new directories for another run. CI runs the unit suite and distribution-manifest check; it does not install Chrome/HyperFrames or claim a native render on Linux.

## Limits

This is a synthetic English layout/runtime smoke test, not proof of polished motion on arbitrary footage. Geometry mattes cannot certify hair, faces or hand edges; synthetic timer coordinates do not prove tracking accuracy. The background fixtures deliberately contain geometry, not realistic clean plates. Audio is silent in these fixture renders. Check real speech, Chinese typography, chosen colors, matte alignment, tracking gaps and every input-specific composition before delivery. Native motion heuristics are not enabled by this check route. White-band screening is not a production source-preservation audit or user approval.

## v1.0.1 portability correction

The first GitHub Python 3.11 run exposed a nested f-string quote accepted by newer Python. v1.0.1 fixes that syntax, adds a Python 3.10 grammar regression check and a 3.10/3.11/3.12 CI matrix. All 25 scene HTML bodies, animation commands and camera samples compare identically before/after this syntax-only fix. The render hashes above remain bound to the original smoke compiler; they were not rebound to the corrected source.
