// talking-head style theme (styles/talking-head). use_style.py copies this to remotion/src/data/style_theme.ts.
// Keep every export name. Free fonts only (SIL OFL): Inter (captions, UI) and Montserrat (accent + display).
// These colours are the DEFAULTS: on every video work/scripts/palette.py replaces them with the footage's own palette
// (the speaker's clothing, the set, its lights). The default accent only shows on neutral black/white/grey footage.
import {loadFont as loadMontserrat} from '@remotion/google-fonts/Montserrat';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';

// SANS = captions (sentence case) and UI text.
export const SANS = loadInter('normal', {weights: ['400', '500', '600', '700', '800'], subsets: ['latin']}).fontFamily;
// SERIF = the accent slot: Montserrat ExtraBold Italic for the one emphasised word of a caption and the slam's accent line.
export const SERIF = loadMontserrat('italic', {weights: ['700', '800'], subsets: ['latin']}).fontFamily;
// SERIF_UPRIGHT = the display slot: hook headline, card numbers and words, slam lines.
export const SERIF_UPRIGHT = loadMontserrat('normal', {weights: ['700', '800', '900'], subsets: ['latin']}).fontFamily;
export const MONO = SANS;

export const C = {
  white: '#F7F7F5', // caption text over the speaker (warm white, not pure)
  accent: '#5B8CFF', // default accent (neutral footage only; otherwise the footage palette's accent)
  accentRgb: '91,140,255',
  accentDeep: '#2F5FD0',
  accentSoft: '#C9D8FF',
  ink: '#14161C', // card glass, text on paper
  inkSoft: '#353946',
  grey: '#8B8F99',
  paper: '#F3F2EE', // full-screen slam paper
  paperCool: '#ECEEF2',
  grid: 'rgba(20,22,28,0.07)',
};

export const sansShadow = '0 2px 10px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.4)';
export const accentGlow = (a = 1) =>
  '0 0 ' + 24 * a + 'px rgba(' + C.accentRgb + ',' + 0.5 * a + '), 0 0 ' + 7 * a + 'px rgba(' + C.accentRgb + ',' + 0.38 * a + '), 0 3px 8px rgba(0,0,0,0.35)';
