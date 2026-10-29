// PLACEHOLDER theme (no client style selected yet). It only exists so the engine typechecks.
// Each client style has its own copy at clients/<client>/<style>/style/theme.ts, written at onboarding from this file;
// work/scripts/use_style.py copies the active one over remotion/src/data/style_theme.ts. Keep every export below:
// the engine components and the scenes import them.
import {loadFont as loadSans} from '@remotion/google-fonts/Inter';
import {loadFont as loadSerif} from '@remotion/google-fonts/PlayfairDisplay';
import {loadFont as loadMono} from '@remotion/google-fonts/DMMono';

// Main text font (captions + scene text). Any @remotion/google-fonts family works.
export const SANS = loadSans('normal', {weights: ['300', '400', '500', '600', '700', '800'], subsets: ['latin']}).fontFamily;
// Accent font for highlighted words (often a script or italic serif).
export const SERIF = loadSerif('italic', {weights: ['400'], subsets: ['latin']}).fontFamily;
export const SERIF_UPRIGHT = loadSerif('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
// Small technical labels.
export const MONO = loadMono('normal', {weights: ['400', '500'], subsets: ['latin']}).fontFamily;

export const C = {
  white: '#F5F5F5', // caption text over the talking head
  accent: '#9A9A9A', // the ONE highlight colour (accent words, glows, active UI)
  accentRgb: '154,154,154', // the same colour as "r,g,b" (used inside rgba())
  accentDeep: '#6E6E6E',
  accentSoft: '#D6D6D6',
  ink: '#1D1D1F', // dark text on light scenes
  inkSoft: '#3A3A3C',
  grey: '#8E8E93',
  paper: '#F4F4F4', // light scene background
  paperCool: '#EEF0F2',
  grid: 'rgba(30,30,30,0.07)',
};

export const sansShadow = '0 2px 10px rgba(0,0,0,0.45), 0 1px 2px rgba(0,0,0,0.35)';
export const accentGlow = (a = 1) =>
  '0 0 ' + 26 * a + 'px rgba(' + C.accentRgb + ',' + 0.55 * a + '), 0 0 ' + 8 * a + 'px rgba(' + C.accentRgb + ',' + 0.4 * a + '), 0 3px 8px rgba(0,0,0,0.35)';
