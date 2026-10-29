// Colour helpers for scenes: build translucent versions of theme tokens instead of typing rgba() literals.
//   alpha(C.ink, 0.3) -> 'rgba(43,29,42,0.300)'      mix(C.accent, C.white, 0.4) -> hex 40% of the way to white
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

export const rgbOf = (hex: string): [number, number, number] => {
  let h = hex.replace('#', '').trim();
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const n = parseInt(h.slice(0, 6), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};

export const alpha = (hex: string, a: number) => 'rgba(' + rgbOf(hex).join(',') + ',' + clamp01(a).toFixed(3) + ')';

export const mix = (hexA: string, hexB: string, t: number) => {
  const a = rgbOf(hexA);
  const b = rgbOf(hexB);
  const k = clamp01(t);
  return '#' + a.map((v, i) => Math.round(v + (b[i] - v) * k).toString(16).padStart(2, '0')).join('');
};
