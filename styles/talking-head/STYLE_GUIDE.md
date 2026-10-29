# STYLE GUIDE - talking-head (ready-made style; overrides work/plan/CRAFT_DEFAULTS.md)

For one person speaking to camera: a creator's own recording, a lesson, an opinion, a story. The look is premium and
minimal: the speaker's own colours everywhere, a hook headline on frame 0, small clean captions with one emphasised word
in an accent font, camera punch-ins that hide every jump cut, full-screen inserts (real B-roll, a wall of examples, a
big real logo, a big number) on the lines that deserve a visual, and one full-screen text "slam" on the biggest line.
Never UI cards or boxes over the speaker. Free fonts (Inter, Montserrat), bundled CC0 sounds and music.

## 0. How an edit in this style runs (reel kit; the short-form-edit skill, section 4)
- Built with the **reel kit**: you write `work/plan/reel.json`; `python work/scripts/reel_build.py` writes the scenes,
  captions, camera, band and sound design. No scene workflow. Target: 15-25 min per reel (measured: 17).
- **Cut** (step 2) is a real cut: raw recordings have retakes. Read `work/transcript/whisper_small.en.json` and keep the
  best complete take of each sentence (usually the last), drop false starts, "let me say that again", the opening breath
  and the reach for the camera at the end (`work/plan/keep.json`, skill step 2). Pauses over 0.24 s are tightened.
  For a clip the router cut from a long video, start from `python work/scripts/keep_all.py` instead.
- **Palette** (step 2.6): `palette.py` takes this video's colours from the speaker's clothing first, then the set and its
  lights. Check `work/frames/palette.png`; steer with `--accent "#hex"` when it picked a prop or skin.
- **Shots**: `python work/scripts/face_track.py` (camera origin = the face; usually one shot).
- **B-roll**: pick the 2-4 lines that deserve a visual and fetch real pictures/clips for them
  (`.claude/skills/short-form-edit/references/BROLL.md`: Wikimedia Commons via `broll_fetch.py`, Pexels via the Claude
  in Chrome extension when connected).
- **Plan** `reel.json` → `reel_build.py` → `integrate.py` → `npx tsc`.
- **Music**: Epidemic Sound if connected, else `input/music/`, else `python work/scripts/music_fit.py` (energetic by
  default: upbeat, confident, modern). `--mood calm` ONLY for a genuinely sad or serious story; a creator talking about
  business, editing, growth or tips always gets energetic music, never slow piano or a melancholy bed.
- **Render and QA**: `bash work/scripts/finalize.sh draft1`, strips, one fix pass through `reel.json`, deliver.

## 1. Design
### 1a. Captions (`captions` in style.json)
- Inter SemiBold/Bold, sentence case, 2-5 words per group (max ~26 characters, up to two lines), centred at y 1300
  Warm white with a soft shadow; small text reads as quality.
- Words rise in on their spoken frame with a light blur-in (fast then slow).
- `emphasis`: the ONE word that carries the line (a number, the topic, the fear or the desire), about one per 2-4 s,
  never two in a group: drawn ~1.3x bigger in Montserrat ExtraBold Italic, in the accent colour with a soft glow.
- No captions while a slam covers the frame (the slam shows the words).

### 1b. Hook headline (frame 0 to the end of the hook sentence, 2.5-4 s)
- Two lines at the top third (y 230), no box: a white setup line (~58 px) and a big accent payoff line (up to 112 px),
  Montserrat Black with a soft dark outline. It is visible on frame 0 and settles in over the first 12 frames.
- Write it from the video's own promise: the gap, the result, the number, the mistake ("Most editors" / "WASTE THEIR
  FIRST HOUR"). Max ~5 words per line, no lies, no emoji.

### 1c. Full-screen inserts (NEVER UI cards)
- No boxes, panels or widgets over the speaker (`card.enabled` is false; cards in reel.json are ignored): they read as a
  website, not an edit.
- 2-4 per 60 s, 1.5-4 s each, on the lines that deserve a visual (kinds, sourcing and licences: `references/BROLL.md`):
  - `wall` when the speaker says "tons of / so many / all these": a moving wall of 6-9 real pictures, optionally with
    the big word ("REFERENCES");
  - `image` / `video` for a concrete thing or scene: real photos (cut on beat words) or a real clip;
  - `logo` when an app, tool or brand is the subject ("Claude edits in your style"): the real logo, big, the words
    popping in under it;
  - `number` for a striking figure: it counts up full-screen.
- The insert zooms in from the speaker (8 frames) and cuts back with a framing change; the music keeps playing.
  Captions stay over photos, clips and an untitled wall; logo, number and titled-wall inserts carry their own words.
- **A call to action at the end** ("DM me", "follow for part 2", "link in bio"): a `logo` insert of the platform it points
  to (`instagram_icon`, `youtube_icon`, `tiktok_icon`) with the speaker's own words as its `text`, on the CTA. Never
  invent a keyword or an offer.

### 1d. Full-screen slams
- 1-2 per 60 s, on the money line(s): the claim, the reveal, the rule. 1.5-3 s each, never in the first 3 s (the hook
  shows the speaker), never back to back (at least 1 s of speaker between).
- The frame opens from the speaker's face with a circle reveal (9 frames) onto the style's paper (`PaperBG` tinted to the
  footage palette, grid, cast shadow) - or a dark stage with `"dark": true` for a serious line. The spoken words pop in
  on their frames in 1-3 lines: Montserrat Black in ink, the accent line (`accentLine`) in Montserrat ExtraBold Italic in
  the accent colour. Optional small kicker above ("RULE #1"). A slow push throughout.
- It ends on a hard cut back to the speaker with a short white flash and a framing change.
- `split` = the number of words per line before the last line (e.g. 6 words, `"split": [3]` → 3 + 3).

Density is given per 60 s: scale it to the clip (a 30 s reel gets about half: 1-2 inserts and at most one slam).

## 2. Motion
- **Camera = slow spanning zooms only** (style.json `camera.mode: smooth`, automatic): opens 1.12 → 1.00 over 18 frames,
  then eases between gentle framings (1.00 / 1.07 / 1.02 / 1.10) over ~4.5 s each, so the shot is always slowly moving and
  jump cuts simply happen inside a move. NO punch-ins, NO sudden zooms, no rhythm cuts, and the camera holds still for the
  last ~0.8 s before every full-screen moment. Don't set `punchWords` in this style.
- Inserts and slams start exactly on the jump cut before their line (the kit snaps them), so no frame of a new take
  (the speaker looking at notes) shows before an animation.
- Something moves in every second; entrances fast-then-slow; no spins, swoops or sideways slides.

## 3. Sound (files in `sound_map.json`, pack = `assets/sfx/pack/`)
- Music: one instrumental bed (calm by default) under the speaker, measured per track and set to -18 LUFS before the mix
  (style.json `music.lufs`); it keeps playing under everything, inserts and slams included.

| Event | Role in sound_map.json | Family, level |
|---|---|---|
| opening zoom-out | `open` | whoosh, -13 dB |
| hook headline in / out | `hook`, `hook_out` | texture -10 / whoosh -15 |
| camera punch (at most one per 1.5 s) | `punch` | whoosh, -15 dB |
| full-screen insert zooms in, lands / next picture, counter lands, back to the speaker | `insert_in`, `insert_pop`, `count`, `insert_out` | whoosh -13, texture -12, texture -11, whoosh -16 |
| slam: riser into it, hit as it lands, reveal, flash back | `riser`, `hit`, `slam_in`, `slam_out` | riser -10, hit -9, whoosh -14, whoosh -15 |
| every other emphasis word | `accent` | texture, -14 dB |

## 4. Caption layouts
- The kit's `pop` layout only. Engine `CAPTIONS = []`.

## 5. Not covered, and the defaults chosen
- No person cut-outs, no AI images, no drawn logos. B-roll is real, freely licensed photos/clips (credits in
  EDIT_NOTES.md) and real logos via `Brand.tsx`.
- A second person on camera: no name tags unless the user gives the name.
- Landscape recordings are reframed to 9:16 around the face by the router before the edit.
