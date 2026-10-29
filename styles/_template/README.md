# Build your own style

A style is one folder in `styles/`. Copy this template, give Claude a reference, and it writes the style for you.

## 1. Copy the template
Copy `styles/_template/` to `styles/<your-style>/` (lowercase letters, digits and dashes, e.g. `styles/my-brand`).

```
styles/my-brand/
  notes.md        optional: who it's for, words to spell right, always / never
  source/         your reference: a PDF or PNG/JPG frames of edits you like, notes (.md/.txt). Figma: export as PDF/PNG.
  sound-pack/     optional: your own sound effects (.mp3/.wav). Empty = the shared pack in assets/sfx/pack/
  examples/       optional: approved past edits in this style (Claude copies their patterns)
```

## 2. Let Claude onboard it
Open Claude Code in this folder and say:

> Set up the style styles/my-brand from its reference.

Claude reads `source/`, writes `STYLE_GUIDE.md` (look, motion, sound, caption layout) and `theme.ts` (fonts and colours)
in the style folder, and sorts your sound pack. It takes 20-30 minutes, once.

**Fastest route:** ask for a *reel-kit* style ("make it a reel-kit style like podcast"). Claude then also writes
`style.json` (caption look, hook, cards, camera) and `sound_map.json`, copied from `styles/podcast/` or
`styles/talking-head/` and adjusted to your reference. Kit styles edit in 10-25 minutes per clip. Without them, Claude
designs every scene from scratch (the engine's full pipeline): richer, but about 3 hours per video.

## 3. Use it
> edit this: https://www.youtube.com/watch?v=... in my-brand style

or `edit clip 2 in my-brand`. Colours come from each video's footage unless your style guide says `Palette: fixed`.

## Agencies: one folder per client
The older layout still works and stays out of git: `clients/<client>/<style>/` with `source/`, and the client's sounds
in `clients/<client>/sound-pack/`. Select it as `<client>/<style>` (e.g. `edit this ... in acme/talking-head`).
Everything in `clients/` is git-ignored, so client material never reaches a public repo.
