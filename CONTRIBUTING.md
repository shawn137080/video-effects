# Contributing

Keep contributions focused on the 25 effect families, source alignment and
portable installation. Describe the visible change, provide reproduction steps
with synthetic or explicitly licensed material, and run the tests. Never commit
customer recordings, mattes, runtime settings, credentials or commercial vendor
templates. Preserve notices. New generated previews must have new filenames.

Run `python3 -m unittest discover -s tests -v` and `python3 tools/release.py
--check`. If runtime files change, refresh the manifest using
`python3 tools/release.py --manifest` before the check. Use Python3.10+ and
FFmpeg. A passing unit suite is not visual acceptance; inspect encoded frames.
