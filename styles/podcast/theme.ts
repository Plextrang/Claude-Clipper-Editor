// podcast style theme (styles/podcast). use_style.py copies this to remotion/src/data/style_theme.ts.
// Keep every export name: the engine components and the reel kit import them. Free fonts only (SIL OFL):
// Montserrat (display + accent) and Inter (UI text), loaded through @remotion/google-fonts.
import {loadFont as loadMontserrat} from '@remotion/google-fonts/Montserrat';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';

// SANS = small UI text: name-tag roles, card labels, kickers.
export const SANS = loadInter('normal', {weights: ['500', '600', '700', '800'], subsets: ['latin']}).fontFamily;
// SERIF = the accent slot. In this style it is Montserrat Black Italic (used sparingly: a card's accent line).
export const SERIF = loadMontserrat('italic', {weights: ['800', '900'], subsets: ['latin']}).fontFamily;
// SERIF_UPRIGHT = the display slot: captions, hook headline, names, numbers. Montserrat ExtraBold/Black.
export const SERIF_UPRIGHT = loadMontserrat('normal', {weights: ['700', '800', '900'], subsets: ['latin']}).fontFamily;
// MONO = tiny technical labels (none by default). Inter keeps the style to two free families.
export const MONO = SANS;

export const C = {
  white: '#FFFFFF', // caption words
  accent: '#FFD43B', // the spoken word + emphasis words: classic podcast-clip yellow, readable over any studio
  accentRgb: '255,212,59',
  accentDeep: '#E0A800',
  accentSoft: '#FFF0B3',
  ink: '#0E0F12', // outlines, card glass, headline box
  inkSoft: '#2A2C33',
  grey: '#8E9099',
  paper: '#F4F2EC',
  paperCool: '#ECEEF1',
  grid: 'rgba(20,20,20,0.07)',
};

export const sansShadow = '0 3px 12px rgba(0,0,0,0.55), 0 1px 2px rgba(0,0,0,0.45)';
export const accentGlow = (a = 1) =>
  '0 0 ' + 22 * a + 'px rgba(' + C.accentRgb + ',' + 0.45 * a + '), 0 0 ' + 6 * a + 'px rgba(' + C.accentRgb + ',' + 0.35 * a + '), 0 3px 8px rgba(0,0,0,0.45)';
