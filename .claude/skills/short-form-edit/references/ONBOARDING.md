# Onboarding a style (once per style, ~20-30 min)

Run this when `python work/scripts/use_style.py <style>` prints NEEDS ONBOARDING, or when the user asks to set up or
refresh a style. It turns whatever the user dropped into the style's `source/` and `sound-pack/` into the files the edit reads.
Two layouts (see `work/scripts/client_style.py`): `styles/<name>/` (files at the folder root: write `STYLE_GUIDE.md` and
`theme.ts` there, pages render to `board/`) and `clients/<client>/<style>/` (write them in `style/`, pages in `style/board/`).
Below, `style/` means "the folder root" for a styles/ style.
**Reel-kit style** (the user asks for one, or for a style "like podcast / talking-head"): also copy `style.json` and
`sound_map.json` from the closest ready-made style (`styles/podcast` or `styles/talking-head`) and adjust caption look,
hook, card and camera values to the reference; write the guide in the same structure as that style's STYLE_GUIDE.md. Then
`use_style.py` prints `reel kit` and the edit follows the skill's section 4. The user is away: don't ask questions; make sensible choices and list them in the report.

Never edit the engine (`remotion/src/components/*`, `theme.ts`, `Main.tsx`, `work/scripts/*`, `work/plan/*`) to fit a client.
Everything style-specific goes in the style's folder.

## Inputs (what the user provides)
- styles/ layout: `styles/<name>/source/`, `styles/<name>/sound-pack/` (optional) and `styles/<name>/notes.md` (optional).
  Client layout:
- `clients/<client>/<style>/source/`: the creative direction. A PDF, PNG/JPG exports, notes (.md/.txt), reference links or
  frames. Figma `.fig` files can't be read: if only a `.fig` is there, stop and report "export the Figma board as PDF or PNG
  into source/".
- `clients/<client>/sound-pack/`: the client's sound effects (.mp3/.wav), in any folder layout.
- Optional: `clients/<client>/client.md` (brand notes) and `clients/<client>/docs/` (any extra client docs, e.g. a sound-design
  or editing guide). Read them: they often hold rules the PDF doesn't.

## Steps
1. **Read the creative direction.**
   - `python work/scripts/source_pages.py <client>/<style>` renders every PDF page into `style/board/` (overviews + tiles).
     Read the overviews first, then only the tiles you need. Read PNG/JPG exports and text notes in `source/` directly.
   - Extract: caption look (fonts, sizes, colours, placement, effects, how words animate, emphasis rules), the hook rules,
     on-screen (over the speaker) graphics, full-screen scenes (backgrounds, palette, composition, recurring motifs),
     transitions, pacing/density, camera behaviour, music and sound preferences, and anything the client says never to do.
2. **Write `style/STYLE_GUIDE.md`** with these sections (cite the board tile or page for each rule):
   1. *Design*: 1a captions and typography; 1b on-screen animations; 1c full-screen animations (backgrounds, palette, scene
      types, text treatment, composition, motifs). Include the hex colours and the chosen Google Fonts.
   2. *Motion*: only where it differs from or adds to `work/plan/CRAFT_DEFAULTS.md` §2 (e.g. the hook is captions-only,
      specific transitions, density such as "about 10 full-screen scenes per 60 s").
   3. *Sound*: overrides of CRAFT_DEFAULTS §3, plus a **mapping table from on-screen event to actual files in this client's
      sound pack** (e.g. text pop -> `textures/pops/<file>`; scene entry -> `<file>`; camera flash -> `<file>`). Note any
      required recipe (e.g. "a riser into the body after the hook").
   4. *Caption layouts*: which of the engine's caption layouts to use (`tier3`, `line`, `stack2`; see the skill, step 5) and
      the default `y`.
   5. *Not in the source*: what the creative direction didn't cover, and the default you chose.
   Keep it under ~150 lines: it is read at the start of every edit and by every scene agent.
3. **Write `style/theme.ts`**: copy `work/templates/style_theme.ts` and change only the values. Keep every export name.
   - Fonts: use the client's fonts if they exist in Google Fonts (check
     `remotion/node_modules/@remotion/google-fonts/dist/esm/<Family>.mjs`); otherwise the closest Google Font, noted in the guide.
   - `C.accent` and `C.accentRgb` must be the same colour. `C.white` is the caption colour over the footage.
4. **Sound pack.**
   - Sort the files into `whoosh/`, `textures/` (subfolders allowed, e.g. `textures/pops`, `textures/UI`) and
     `risers and hits/`, by what each sound does (CRAFT_DEFAULTS §3). Move files; never delete or rename them.
     If the pack is already sorted this way, leave it.
   - If the pack is empty, continue without sound effects and say so in the final report.
5. Run `python work/scripts/use_style.py <client>/<style>` (it must print ONBOARDED), then
   `python work/scripts/sfx_catalog.py` (builds the catalogue in `sound-pack/_catalogue/`) and
   `cd remotion && npx tsc --noEmit -p .`. The first edit's QA (skill step 8) checks the look on real footage.

## Adding another style for the same client
Make `clients/<client>/<new-style>/source/`, drop the creative direction in, and onboard it. The client's sound pack is shared;
give the style its own `sound-pack/` only if it uses different sounds.

## Refreshing a style
When the user updates `source/`, re-run the steps and update `STYLE_GUIDE.md` and `theme.ts` in place. Keep earlier notes that
the client approved.

## Footage palette and real brand assets (applies to every style)
- Write `theme.ts` so its colours are the style's DEFAULT palette: keep every key of the template's `C` (add `warm` /
  `warmDeep` if the style has a second colour) and build `accentGlow` from `C.accentRgb` (or the accent's literal "r,g,b",
  which the engine re-tints). Per video, `work/scripts/palette.py` replaces these colours with the footage's own palette, so
  name colours in `STYLE_GUIDE.md` by ROLE ("the accent", "near-black ink", "paper") next to the default hex; never make a
  design rule depend on one specific hue.
- If the client's brand demands fixed colours on every video (strict brand guidelines), add the line `Palette: fixed` to the
  style guide: palette.py then keeps the style's colours.
- Note in the style guide which real products, apps and platforms this client's videos usually mention, so planners reach for
  the real logos and UIs (`remotion/public/brand/README.md`; add missing ones to `work/brand_assets.json`).
