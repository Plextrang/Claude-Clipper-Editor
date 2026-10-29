import React from 'react';
import {AbsoluteFill} from 'remotion';
import {C, SANS, SERIF} from '../theme';
import {EASE_OUT, EASE_IN_OUT, clamp01, prog} from '../lib/anim';

/* ---------- Scene text: word-by-word blur pop, mixed sans + serif accent ---------- */
export type STWord = {t: string; f: number; serif?: boolean; accent?: boolean; weight?: number};
export const SceneText: React.FC<{
  words: STWord[];
  frame: number;
  size: number;
  serifScale?: number;
  color?: string;
  align?: 'center' | 'left' | 'right';
  maxWidth?: number;
  lineHeight?: number;
  weight?: number;
  glow?: boolean;
  gap?: number;
  dark?: boolean; // dark text on white scene
}> = ({words, frame, size, serifScale = 1.25, color = C.ink, align = 'center', maxWidth = 900, lineHeight = 1.05, weight = 600, glow = true, gap, dark = true}) => (
  <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: align === 'center' ? 'center' : align === 'left' ? 'flex-start' : 'flex-end', alignItems: 'baseline', columnGap: gap ?? size * 0.24, rowGap: size * 0.14, maxWidth, lineHeight}}>
    {words.map((w, i) => {
      const p = prog(frame, w.f, w.serif ? 12 : 9, EASE_OUT);
      const isSerif = !!w.serif;
      const col = w.accent ? C.accent : color;
      return (
        <span
          key={i}
          style={{
            display: 'inline-block',
            fontFamily: isSerif ? SERIF : SANS,
            fontStyle: isSerif ? 'italic' : 'normal',
            fontWeight: isSerif ? 400 : w.weight ?? weight,
            fontSize: isSerif ? size * serifScale : size,
            letterSpacing: isSerif ? '-0.01em' : '-0.035em',
            color: col,
            WebkitTextStroke: isSerif ? '1.2px ' + col : undefined,
            backgroundImage: !isSerif && !w.accent && dark ? 'linear-gradient(180deg, #2A2A2C 0%, #1A1A1C 100%)' : undefined,
            WebkitBackgroundClip: !isSerif && !w.accent && dark ? 'text' : undefined,
            WebkitTextFillColor: !isSerif && !w.accent && dark ? 'transparent' : undefined,
            // background-clip:text only paints inside the span box -> pad it so descenders are not cut (can shift wrapped baseline rows ~5px)
            ...(!isSerif && !w.accent && dark ? {paddingTop: '0.06em', marginTop: '-0.06em', paddingBottom: '0.28em', marginBottom: '-0.28em'} : {}),
            textShadow: w.accent && glow ? '0 0 22px rgba(' + C.accentRgb + ',' + (0.45 * p).toFixed(3) + '), 0 0 6px rgba(' + C.accentRgb + ',' + (0.3 * p).toFixed(3) + ')' : undefined,
            opacity: clamp01(p * 1.7),
            transform: 'translateY(' + ((1 - p) * size * 0.32).toFixed(2) + 'px)',
            filter: p < 1 ? 'blur(' + ((1 - p) * 9).toFixed(2) + 'px)' : undefined,
            padding: isSerif ? '0 0.05em' : undefined,
          }}
        >
          {w.t}
        </span>
      );
    })}
  </div>
);

/* ---------- Mouse cursor (design-tool motif) ---------- */
export const Cursor: React.FC<{x: number; y: number; scale?: number; press?: number; opacity?: number}> = ({x, y, scale = 1, press = 0, opacity = 1}) => (
  <div style={{position: 'absolute', left: x, top: y, transform: 'scale(' + scale * (1 - press * 0.12) + ')', transformOrigin: '0 0', opacity, filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.28))'}}>
    <svg width="46" height="56" viewBox="0 0 23 28">
      <path d="M1.5 1.5 L1.5 22.5 L7 17.3 L10.6 26 L14.2 24.4 L10.7 15.9 L18.2 15.9 Z" fill="#111" stroke="#fff" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  </div>
);

/* ---------- Dotted selection box with corner handles (Figma-style) ---------- */
export const SelectBox: React.FC<{x: number; y: number; w: number; h: number; p: number; color?: string; label?: string}> = ({x, y, w, h, p, color = '#1F1F1F', label}) => {
  const hs = 14;
  const dash = clamp01(p);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: clamp01(p * 2)}}>
      <svg width={w} height={h} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
        <rect x={0.75} y={0.75} width={w - 1.5} height={h - 1.5} fill="none" stroke={color} strokeWidth={2} strokeDasharray="7 6" pathLength={1000} strokeDashoffset={(1 - dash) * 1000} style={{strokeDasharray: (dash * 1000).toFixed(0) + ' 1000'}} />
        <rect x={0.75} y={0.75} width={w - 1.5} height={h - 1.5} fill="none" stroke={color} strokeWidth={2} strokeDasharray="7 6" opacity={dash >= 1 ? 1 : 0} />
      </svg>
      {[
        [0, 0],
        [1, 0],
        [0, 1],
        [1, 1],
      ].map(([cx, cy], i) => (
        <div key={i} style={{position: 'absolute', left: cx * w - hs / 2, top: cy * h - hs / 2, width: hs, height: hs, background: '#fff', border: '2px solid ' + color, transform: 'scale(' + EASE_OUT(clamp01(p * 1.4 - 0.2)) + ')'}} />
      ))}
      {label ? (
        <div style={{position: 'absolute', left: 0, top: -34, fontFamily: SANS, fontSize: 18, fontWeight: 600, color: '#fff', background: color, padding: '3px 8px', borderRadius: 4, opacity: clamp01(p * 2 - 0.6)}}>{label}</div>
      ) : null}
    </div>
  );
};

/* ---------- Barcode label ---------- */
export const Barcode: React.FC<{x: number; y: number; w?: number; h?: number; opacity?: number; seed?: number; label?: string}> = ({x, y, w = 150, h = 34, opacity = 0.75, seed = 3, label = 'REF-2.0 / 0427'}) => {
  const bars: number[] = [];
  let s = seed;
  for (let i = 0; i < 46; i++) {
    s = (s * 9301 + 49297) % 233280;
    bars.push(1 + Math.floor((s / 233280) * 3.2));
  }
  let acc = 0;
  const total = bars.reduce((a, b) => a + b + 1.4, 0);
  return (
    <svg style={{position: 'absolute', left: x, top: y, opacity}} width={w} height={h + 16} viewBox={'0 0 ' + total + ' ' + (h + 16)} preserveAspectRatio="none">
      {bars.map((b, i) => {
        const r = <rect key={i} x={acc} y={0} width={b} height={h} fill={i % 2 ? '#1a1a1a' : 'transparent'} />;
        acc += b + 1.4;
        return r;
      })}
      <text x={0} y={h + 13} fontFamily="monospace" fontSize={11} fill="#333" letterSpacing={2}>
        {label}
      </text>
    </svg>
  );
};

/* ---------- Crop marks / frame corners ---------- */
export const CropMarks: React.FC<{x: number; y: number; w: number; h: number; len?: number; color?: string; p?: number}> = ({x, y, w, h, len = 34, color = 'rgba(20,20,20,0.55)', p = 1}) => {
  const L = len * EASE_OUT(clamp01(p));
  const st = {position: 'absolute' as const, background: color};
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h}}>
      <div style={{...st, left: 0, top: 0, width: L, height: 2}} />
      <div style={{...st, left: 0, top: 0, width: 2, height: L}} />
      <div style={{...st, right: 0, top: 0, width: L, height: 2}} />
      <div style={{...st, right: 0, top: 0, width: 2, height: L}} />
      <div style={{...st, left: 0, bottom: 0, width: L, height: 2}} />
      <div style={{...st, left: 0, bottom: 0, width: 2, height: L}} />
      <div style={{...st, right: 0, bottom: 0, width: L, height: 2}} />
      <div style={{...st, right: 0, bottom: 0, width: 2, height: L}} />
    </div>
  );
};

/* ---------- Reveals: circle reveal + square reveal ---------- */
export const CircleReveal: React.FC<{p: number; cx?: number; cy?: number; children: React.ReactNode}> = ({p, cx = 540, cy = 960, children}) => {
  const r = EASE_IN_OUT(clamp01(p)) * 2250;
  return <AbsoluteFill style={{clipPath: 'circle(' + r.toFixed(1) + 'px at ' + cx + 'px ' + cy + 'px)'}}>{children}</AbsoluteFill>;
};
export const SquareReveal: React.FC<{p: number; cx?: number; cy?: number; radius?: number; children: React.ReactNode}> = ({p, cx = 540, cy = 960, radius = 36, children}) => {
  const e = EASE_IN_OUT(clamp01(p));
  const hw = 20 + e * 1100;
  const hh = 20 + e * 1600;
  const top = Math.max(0, cy - hh), bottom = Math.max(0, 1920 - (cy + hh)), left = Math.max(0, cx - hw), right = Math.max(0, 1080 - (cx + hw));
  return <AbsoluteFill style={{clipPath: 'inset(' + top + 'px ' + right + 'px ' + bottom + 'px ' + left + 'px round ' + radius * (1 - e) + 'px)'}}>{children}</AbsoluteFill>;
};

/* ---------- Edge depth blur (1-2 barely visible elements at the edge) ---------- */
export const DepthBlob: React.FC<{x: number; y: number; size: number; color?: string; blur?: number; opacity?: number; shape?: 'circle' | 'square'}> = ({x, y, size, color = '#1d1d1f', blur = 26, opacity = 0.85, shape = 'circle'}) => (
  <div style={{position: 'absolute', left: x, top: y, width: size, height: size, borderRadius: shape === 'circle' ? '50%' : size * 0.16, background: color, filter: 'blur(' + blur + 'px)', opacity}} />
);

/* ---------- Pill / tag ---------- */
export const Tag: React.FC<{text: string; p: number; x?: number; y?: number; dark?: boolean; style?: React.CSSProperties}> = ({text, p, x, y, dark = false, style}) => (
  <div
    style={{
      position: x !== undefined ? 'absolute' : 'relative',
      left: x,
      top: y,
      fontFamily: SANS,
      fontWeight: 700,
      fontSize: 22,
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      color: dark ? '#fff' : C.ink,
      background: dark ? '#1b1b1d' : 'rgba(255,255,255,0.85)',
      border: dark ? 'none' : '1.5px solid rgba(20,20,20,0.12)',
      padding: '9px 18px',
      borderRadius: 999,
      boxShadow: '0 8px 22px rgba(0,0,0,0.10)',
      opacity: clamp01(p * 1.6),
      transform: 'translateY(' + (1 - EASE_OUT(clamp01(p))) * 16 + 'px)',
      ...style,
    }}
  >
    {text}
  </div>
);

/* ---------- Soft casted shadow under a floating object ---------- */
export const ContactShadow: React.FC<{x: number; y: number; w: number; opacity?: number}> = ({x, y, w, opacity = 0.35}) => (
  <div style={{position: 'absolute', left: x - w / 2, top: y, width: w, height: w * 0.16, borderRadius: '50%', background: 'radial-gradient(closest-side, rgba(0,0,0,' + opacity + '), rgba(0,0,0,0))', filter: 'blur(6px)'}} />
);

export {SERIF};
