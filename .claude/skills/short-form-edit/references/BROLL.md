# Full-screen inserts and real B-roll (kit styles)

The kit styles never put UI cards (boxes, panels, widgets) over the speaker. When a line deserves a visual, the frame
cuts to a FULL-SCREEN insert for 1.5-4 s, then back to the speaker with a framing change. The kit draws inserts under
the captions, so the music keeps playing and B-roll keeps its captions.

## Which insert (reel.json `inserts`, schema in the `reel_build.py` docstring)
| The speaker says... | Insert | Example |
|---|---|---|
| a concrete thing, place, product, event or scene ("I hid GoPros in Walmart") | `image` (1-3 real photos, cut on beat words) or `video` (a real clip) | Walmart store + a GoPro photo, cut on "GoPros" |
| "tons of / so many / all these" examples, references, people, videos | `wall`: a moving wall of 6-9 real pictures, optional big title word | "tons of references" → wall of edits/photos + "REFERENCES" |
| a brand, app, tool or platform as the subject ("Claude edits in your style") | `logo`: the REAL logo, big, with the words popping in | Claude logo + "edits in your style" |
| a striking number ("100 million", "46%") | `number`: the figure counts up full-screen with a short label | "46%" / "of cocoa labour" |
Density: about one insert every 8-15 s (a 60 s clip: 3-5; a 30 s reel: 2-3), never in the first 2 s (the hook shows the
speaker), at least 0.6 s of speaker between two inserts. Each one illustrates the line; it never just repeats the
caption. Pick the strongest lines: the claim, the story's concrete details, the payoff.

## Getting real B-roll (per video; nothing is stored in the repo)
1. Search Wikimedia Commons (free licences, no key): `python work/scripts/broll_fetch.py search "walmart store"`
   (`--video` for clips). Read the contact sheet it saves (`work/frames/broll_<query>.png`); pick by number:
   `python work/scripts/broll_fetch.py get 3 --as walmart`. Use concrete search words (the object, the place, the
   activity), 2-4 words, in English.
2. If Commons has nothing good, or you need moving footage, and the **Claude in Chrome** extension is connected
   (ToolSearch "claude-in-chrome"): search Pexels (`https://www.pexels.com/search/videos/<words>/?orientation=portrait`,
   or `/search/<words>/` for photos) or Unsplash, open a result, and pass the file to the script:
   `python work/scripts/broll_fetch.py get "https://www.pexels.com/download/video/<id>/" --as crowd --source "<page URL>" --license "Pexels License" --author "<name>"`
   (photos: the image file URL, `--license "Pexels License"` / `"Unsplash License"`). Skip anything marked AI-generated or
   "aigc" ads, anything with a watermark, and anything whose page shows no reusable licence.
3. Logos come from the brand library (`remotion/public/brand`, `Brand.tsx`): `logo` inserts need no download
   (missing one: `python work/scripts/fetch_brand_assets.py --si <slug>`).
4. `python work/scripts/broll_fetch.py list` shows every file with its credit; `reel_build.py` copies the credits of the
   ones used into `work/plan/reel_summary.md`: put them in EDIT_NOTES.md (section 5, next to the music credit).

## Quality bar (the edit is only as good as its worst picture)
- Professional, high-production-value media that matches the speaker's world: clean modern studios, cinema cameras and
  lighting, polished screens and workspaces, well-lit products and places. Prefer one strong, simple subject per frame.
- Skip anything amateur-looking: cluttered rooms, handheld phone snapshots, dim or muddy light, awkward group shots,
  tourist photos, low-resolution or heavily compressed files. When nothing good turns up, use a `logo`, `number` or
  `wall` insert or no insert at all; a weak picture is worse than none.
- Clips: steady, well-exposed, with the action in the first 2-3 s (`clip.mp4#t=2` skips a slow start).

## Rules
- Real media only: real photos, real footage, real logos. Never AI images, never drawn stand-ins, never a screenshot of
  someone else's post or video, never a person who is not the subject (no stock "random face" as the speaker).
- Licences: CC0, public domain, CC BY, CC BY-SA, Pexels, Unsplash. Never NC / ND, "fair use" or unknown. The script
  refuses NC/ND and records the credit; CC BY / BY-SA need the credit line in EDIT_NOTES.md.
- Look before you use: open the contact sheet (or the Chrome screenshot) and check the picture really shows the thing,
  is not blurry, has no watermark or text overlay, and works cropped to 9:16. A wide picture whose subject is off-centre:
  give its focus in reel.json, `"gopro.jpg#x=0.3"` (0 = left edge, 1 = right edge); prefer portrait or square pictures.
- Check the inserts on the look sheet (step 6 of the kit path): one still at each insert's from + 12.
