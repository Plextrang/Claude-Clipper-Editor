// Fonts, colours, text shadow and accent glow come from the ACTIVE client style:
// clients/<client>/<style>/style/theme.ts, copied to src/data/style_theme.ts by work/scripts/use_style.py
// (a neutral placeholder from work/templates/ until a style is selected). Don't put client values in this file.
//
// FOOTAGE PALETTE: work/scripts/palette.py samples this video's footage (clothing, set, light) and writes
// src/data/palette.ts. When it is set, its colours replace the style's colour tokens (accent, accentDeep, accentSoft,
// warm, ink, paper, grid, ...) for this video, so captions, cards and scenes match the footage. Fonts, sizes and the
// caption white stay the style's. PALETTE = null (template default, or `palette.py --off`) keeps the style's colours.
import * as S from './data/style_theme';
import {PALETTE} from './data/palette';

export {SANS, SERIF, SERIF_UPRIGHT, MONO, sansShadow} from './data/style_theme';
export {alpha, mix, rgbOf} from './lib/color';

// warm / warmDeep = an optional second colour (e.g. a lamp's glow). Styles without one fall back to their accent tints.
const BASE = {warm: S.C.accentSoft, warmDeep: S.C.accent, ...S.C};
export const C: typeof BASE = PALETTE ? {...BASE, ...PALETTE} : BASE;
export const PALETTE_ACTIVE = PALETTE !== null;

// The style's glow, re-tinted to the palette accent (styles write their glow with the accent's "r,g,b").
export const accentGlow = (a = 1): string => {
  const g = S.accentGlow(a);
  return PALETTE ? g.split(S.C.accentRgb).join(C.accentRgb) : g;
};

export const FPS = 30;
export const W = 1080;
export const H = 1920;
