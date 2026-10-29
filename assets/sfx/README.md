# Sound effects

The edit uses at most 2 whooshes per clip, all at low volume under the voice:

| File | Role | Used for |
|---|---|---|
| `whoosh-cinematic.mp3` | whoosh | opening zoom |
| `whoosh-heavy.mp3` | whoosh (pack of 8, split automatically) | emphasis zooms |
| `click.wav` | click | available for custom edits |

**Use your own:** drop any `.mp3`/`.wav` in this folder with `whoosh`, `hit` or `click`
in its name. `catalog.json` is rebuilt automatically when the folder changes.
Make sure you have the rights to any sound you add or publish.

## The premium pack (`pack/`)
`podcast` and `talking-head` use the CC0 pack in `pack/` (whooshes, pops, UI clicks, risers, hits; sources and licences in
`pack/LICENSES.md`; the synthesised ones were made for this repo, generator in `pack/_source/`). Which sound plays on which
event is set per style in `styles/<style>/sound_map.json`. To use your own sounds in a style, put them in
`styles/<style>/sound-pack/` (any layout) and point that style's `sound_map.json` at them. The clip style only scans the
files at the top of this folder, so `pack/` never changes it.
