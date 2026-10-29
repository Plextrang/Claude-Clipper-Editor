# STYLE GUIDE - podcast (ready-made style; overrides work/plan/CRAFT_DEFAULTS.md)

For clips cut from podcasts and interviews: one or two people talking at a table or on a couch, filmed by one or more
cameras. The look is the clean, high-retention podcast clip: a hook headline in the first seconds, bold word-by-word
captions where the spoken word lights up, a camera that follows whoever is on screen, name tags when two people talk,
full-screen real B-roll on the strongest lines (never UI cards), a quiet music bed and light sound design. Free fonts (Montserrat, Inter), bundled CC0
sounds and music.

Palette: fixed
(The yellow highlight is part of the look and has to read over any studio. Fonts, layout and motion never change.)

## 0. How an edit in this style runs (reel kit; the short-form-edit skill, section 4)
- This style is built with the **reel kit**: you write one small plan, `work/plan/reel.json`, and
  `python work/scripts/reel_build.py` writes the scenes, captions, camera, band and sound design from it. No scene
  workflow, no per-scene agents. Target: 10-20 min per clip (measured: 10-15).
- **Cut** (step 2): the clip is already one moment, so keep everything: `python work/scripts/keep_all.py`, then delete
  only a false start, a retake or a dangling half sentence at either end. `build_edl.py` reads `maxPause` 0.7 from
  `style.json`: only pauses longer than 0.7 s are tightened, so the conversation keeps its rhythm and few jump cuts appear.
- **Shots**: `python work/scripts/face_track.py`, then Read `work/frames/shots.png`. Each numbered shot has a `look`
  letter (A, B, ...): shots that look alike. Decide who is who from the picture and the transcript.
- **B-roll**: pick the 3-5 lines that deserve a visual and fetch real pictures/clips for them
  (`.claude/skills/short-form-edit/references/BROLL.md`: Wikimedia Commons via `broll_fetch.py`, Pexels via the Claude
  in Chrome extension when connected).
- **Plan** (`reel.json`, schema in the `reel_build.py` docstring), then `reel_build.py` → `integrate.py` → `npx tsc`.
- **Music**: Epidemic Sound connector if connected (skill step 4), else `input/music/`, else
  `python work/scripts/music_fit.py --mood energetic` (or `calm` for a slow, emotional or serious moment). The bed is
  QUIET: music_fit measures the exact stretch used and sets it to -24 LUFS (style.json `music.lufs`), so every track sits
  well under the conversation whatever its own mastering.
- **Render and QA**: `bash work/scripts/finalize.sh draft1`, read the strips, one fix pass by editing `reel.json` and
  re-running `reel_build.py` (never hand-edit the generated scene files), deliver.

## 1. Design
### 1a. Captions (`captions` in style.json; the kit draws them)
- Montserrat Black, UPPERCASE, 1-3 words per group (max ~18 characters), centred, block centre y 1340. White with a dark outline and soft shadow, so they read over any shirt or table.
- Each word pops in on its spoken frame (fast scale-up, slight blur-in). **The word being spoken lights up in the
  accent yellow**; emphasis words stay yellow for the whole group.
- `emphasis`: about one word per 2-3 seconds: numbers, money, names, the strong verb or the key noun of the moment.
  Never more than one per caption group. The router's `clip_brief.md` lists the words picked with the moment.
- Groups break at punctuation, at pauses over 0.35 s and at cuts; the kit handles timing (no blinking, no holding
  across a cut).

### 1b. Hook headline (the first 2.5-4.5 s)
- Frame 0 already shows it: NO box or background, just two lines of Montserrat Black, uppercase, at the top (y 190): a
  white setup line (~70 px) and a big yellow payoff line (up to ~134 px), both with a heavy dark outline and shadow (and a
  soft glow on the yellow line) so they stand out on any footage. It exits upward when the hook sentence ends (`untilWord`).
- Write it like a title a viewer would stop for, from the clip's own idea: a curiosity gap, a bold claim, a number, a
  question (e.g. "HE HID GOPROS" / "IN WALMART"). Setup line up to ~5 words; the yellow line 1-3 words (<= ~12
  characters) so it renders BIG: the size fits the line to the width, so a long yellow line comes out small. Never a lie
  about what is said.
- It does not repeat the first caption word for word; it frames it.

### 1c. Name tags (only when TWO or more people are on camera)
- Only when the shots show two different people AND their real names are known from the video's title, channel or what is
  said in the clip (e.g. "MrBeast" in the title, the host's own show). Never invent a name or guess from a face. One
  person on camera, or names unknown: no name tags.
- In `reel.json`: `"speakers": {"A": {"name": "Real Name", "role": "Guest"}, "B": {"name": "...", "role": "Host"}}`,
  keyed by the shot `look` letters. The kit shows each tag once, on that person's first long shot: a yellow bar + a dark
  label (name in Montserrat ExtraBold, role in small Inter caps), lower third y 1120, ~2.8 s, sliding in from the side.

### 1d. Full-screen inserts (real B-roll; NEVER UI cards)
- No boxes, panels or widgets over the speaker (`card.enabled` is false; cards in reel.json are ignored).
- On the 3-5 strongest lines of a 60 s clip (about one every 10-15 s), cut to a FULL-SCREEN insert for 1.5-4 s:
  `image` (1-3 real photos of what is said: the store, the object, the event, cut on beat words), `video` (a real clip),
  `wall` (a moving wall of pictures for "tons of / so many"), `logo` (the real brand logo, big, when a brand is the
  subject) or `number` (a big figure counting up). Kinds, sourcing and licences: `references/BROLL.md`.
- The insert zooms in from the speaker (8 frames) and cuts back with a framing change. Captions stay on top of photos and
  clips; logo and number inserts carry their own words. The music keeps playing under them.
- Every picture shows exactly what the speaker is talking about; real media only, never AI images or drawn stand-ins.

### 1e. Full-screen text scenes
- None (`slam.enabled` is false): podcast visuals are real B-roll.

### 1f. Progress bar
- A thin yellow bar fills along the top edge over the clip (retention cue). Automatic.

Density is given per 60 s: scale it to the clip (a 30 s reel gets about half: 2-3 inserts).

## 2. Motion
- **Speaker-aware camera** (automatic, from `faces.json`): every framing scales around the face of whoever is on
  screen. A new camera angle starts wide on the new face; every jump cut inside a shot switches wide (1.00) and
  punched-in (1.18) as a hard cut; a rhythm punch lands on sentence ends every ~3-4.5 s; a slow push (+1% per second)
  in between. Opening: 1.16 → 1.00 snap over 9 frames.
- `punchWords`: 1-3 extra snap zooms on the biggest words of the clip (the reveal, the number, the punchline).
- Inserts and tags enter fast-then-slow (8-10 frames); a still drifts slowly (Ken Burns), a wall keeps scrolling.
  Nothing bounces or spins; only the name tag slides.

## 3. Sound (overrides CRAFT_DEFAULTS section 3; files in `sound_map.json`, pack = `assets/sfx/pack/`)
- Music: one instrumental bed under the whole clip, kept low (-24 LUFS before the mix, measured per track: the voice
  always clearly on top). Energetic by default; calm for slow, serious or emotional moments.
- Sound design is light, so the conversation stays on top:

| Event | Role in sound_map.json | Family, level |
|---|---|---|
| opening zoom-out | `open` | whoosh, -14 dB |
| hook headline pops in / exits | `hook`, `hook_out` | texture -10 / whoosh -16 |
| camera punch (at most one per 1.5 s) | `punch` | whoosh, -17 dB |
| name tag slides in | `nametag` | texture, -12 dB |
| full-screen insert zooms in, lands / next picture, counter lands, back to the speaker | `insert_in`, `insert_pop`, `count`, `insert_out` | whoosh -13, texture -12, texture -11, whoosh -16 |
| every other emphasis word | `accent` | texture, -15 dB |

## 4. Caption layouts
- The kit's `karaoke` layout only (style.json). The engine's tier3 / line / stack2 captions are not used: `CAPTIONS = []`.

## 5. Not covered, and the defaults chosen
- Speaker on the left/right of a two-shot (one wide camera): the clipper's reframe follows the bigger face; the camera
  stays on it. If the other person speaks for long, the clip still shows the first one (a known limit of a single
  crop; name tags then label only the person seen).
- Swearing is captioned as spoken. Sponsor reads and "like and subscribe" never become clips (the picking step drops them).
- B-roll: real, freely licensed photos and clips with their credits in EDIT_NOTES.md; real logos; never AI images.
