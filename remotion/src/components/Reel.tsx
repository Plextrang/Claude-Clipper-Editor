import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {fitText} from '@remotion/layout-utils';
import {C, SANS, SERIF, SERIF_UPRIGHT, accentGlow, alpha, mix} from '../theme';
import {EASE_IN, EASE_OUT, clamp01, prog} from '../lib/anim';
import {PaperBG} from './PaperBG';
import {BrandLogo, Glyph} from './Brand';

/**
 * REEL KIT: the building blocks of the kit styles (styles/podcast, styles/talking-head). work/scripts/reel_build.py
 * writes the per-video scene files (OS00_Reel, OS<n>_Card*, FS<n>_Slam*) from work/plan/reel.json and the style's
 * style.json; they only pass data into these components. Colours are theme tokens (the footage palette applies),
 * fonts are the style's: SANS = UI/body text, SERIF = the accent font, SERIF_UPRIGHT = the display font.
 */

export type RWord = {t: string; f: number; e: number; accent?: boolean};
export type RGroup = {from: number; to: number; words: RWord[]; y?: number};
export type CapLook = {
  mode: 'karaoke' | 'pop'; // karaoke: bold words, the spoken word lights up | pop: words rise in, accent words in the accent font
  upper: boolean;
  size: number; // max font size (px); long groups shrink to fit maxW
  weight: number;
  font: 'display' | 'sans';
  stroke: number; // dark outline width (px), 0 = none
  maxW: number;
  y: number; // default block centre
  accentScale: number; // accent words relative size
  active: boolean; // light up the word being spoken
};

const fam = (f: 'display' | 'sans') => (f === 'display' ? SERIF_UPRIGHT : SANS);
const dark = (a: number) => alpha(C.ink, a);
const outline = (w: number) =>
  w <= 0
    ? '0 3px 12px ' + dark(0.55)
    : [
        `${w}px 0 0 ${dark(0.92)}`, `-${w}px 0 0 ${dark(0.92)}`, `0 ${w}px 0 ${dark(0.92)}`, `0 -${w}px 0 ${dark(0.92)}`,
        `${w * 0.7}px ${w * 0.7}px 0 ${dark(0.92)}`, `-${w * 0.7}px ${w * 0.7}px 0 ${dark(0.92)}`,
        `${w * 0.7}px -${w * 0.7}px 0 ${dark(0.92)}`, `-${w * 0.7}px -${w * 0.7}px 0 ${dark(0.92)}`,
        `0 ${w + 4}px 14px ${dark(0.6)}`,
      ].join(', ');

const fitSize = (text: string, family: string, weight: number, maxW: number, max: number) => {
  try {
    // 12% margin: the measure can run before the web font has loaded (a fallback font is narrower), and the spans add gaps
    const s = fitText({text, withinWidth: maxW * 0.88, fontFamily: family, fontWeight: weight, validateFontIsLoaded: false}).fontSize;
    return Math.max(44, Math.min(max, s));
  } catch {
    return max;
  }
};

/** One caption group. The whole layout is reserved from the first frame, so lines never re-centre as words appear. */
const Group: React.FC<{g: RGroup; frame: number; look: CapLook}> = ({g, frame, look}) => {
  const text = g.words.map((w) => (look.upper ? w.t.toUpperCase() : w.t)).join(' ');
  const family = fam(look.font);
  const twoLines = look.mode === 'pop' && text.length > 22;
  const size = twoLines ? look.size : fitSize(text, family, look.weight, look.maxW, look.size);
  const exit = prog(frame, g.to - 4, 4, EASE_IN);
  return (
    <div
      style={{
        position: 'absolute', left: (1080 - look.maxW) / 2, width: look.maxW, top: (g.y ?? look.y) - size * (twoLines ? 1.1 : 0.6),
        display: 'flex', justifyContent: 'center', alignItems: 'baseline', columnGap: size * 0.26,
        rowGap: size * 0.05, opacity: 1 - exit, flexWrap: twoLines ? 'wrap' : 'nowrap',
      }}
    >
      {g.words.map((w, i) => {
        const start = w.f - 2;
        const p = prog(frame, start, look.mode === 'karaoke' ? 5 : 8, EASE_OUT);
        const speaking = frame >= w.f && frame < Math.max(w.e, w.f + 4);
        const hot = w.accent || (look.active && speaking);
        const t = look.upper ? w.t.toUpperCase() : w.t;
        const accentFont = look.mode === 'pop' && w.accent;
        const s = w.accent ? size * look.accentScale : size;
        return (
          <span
            key={i}
            style={{
              fontFamily: accentFont ? SERIF : family,
              fontStyle: accentFont ? 'italic' : 'normal',
              fontWeight: look.weight,
              fontSize: s,
              lineHeight: 1.04,
              letterSpacing: look.upper ? '0.005em' : '-0.015em',
              color: hot ? C.accent : C.white,
              textShadow: hot && look.mode === 'pop' ? accentGlow(0.8) : outline(look.stroke),
              opacity: clamp01(p * 1.8),
              transform:
                look.mode === 'karaoke'
                  ? `scale(${0.82 + 0.18 * p + (speaking && look.active ? 0.04 : 0)})`
                  : `translateY(${(1 - p) * 22}px)`,
              filter: p >= 1 ? 'none' : `blur(${(1 - p) * (look.mode === 'pop' ? 8 : 3)}px)`,
              display: 'inline-block',
              whiteSpace: 'nowrap',
            }}
          >
            {t}
          </span>
        );
      })}
    </div>
  );
};

export const ReelCaptions: React.FC<{groups: RGroup[]; look: CapLook; hidden?: [number, number][]}> = ({groups, look, hidden = []}) => {
  const f = useCurrentFrame();
  if (hidden.some(([a, b]) => f >= a && f < b)) return null;
  const g = groups.find((x) => f >= x.from && f < x.to);
  return g ? <Group g={g} frame={f} look={look} /> : null;
};

/** Hook headline: on screen from frame 0 (moving from frame 1), exits upward at `to`. Line `accent` is the big one. */
export const HookHeadline: React.FC<{lines: string[]; accent: number; to: number; y: number; boxed: boolean; upper: boolean;
  size?: number; accentSize?: number; stroke?: number}> = ({lines, accent, to, y, boxed, upper, size = 58, accentSize = 112, stroke = 4}) => {
  const f = useCurrentFrame();
  if (f >= to) return null;
  const pin = prog(f, -3, 12, EASE_OUT); // already ~40% in on frame 0
  const out = prog(f, to - 9, 9, EASE_IN);
  const sizes = lines.map((l, i) =>
    fitSize(upper ? l.toUpperCase() : l, SERIF_UPRIGHT, 900, boxed ? 840 : 940, i === accent ? accentSize : size),
  );
  return (
    <div
      style={{
        position: 'absolute', left: 0, right: 0, top: y, display: 'flex', justifyContent: 'center',
        opacity: clamp01(pin * 1.4) * (1 - out), transform: `translateY(${-out * 60}px) scale(${1.06 - 0.06 * pin})`,
        filter: pin >= 1 && out <= 0 ? 'none' : `blur(${(1 - pin) * 10 + out * 8}px)`,
      }}
    >
      <div
        style={{
          padding: boxed ? '26px 40px 30px' : 0, borderRadius: 34, textAlign: 'center',
          background: boxed ? alpha(C.ink, 0.84) : 'transparent',
          boxShadow: boxed ? '0 18px 50px ' + dark(0.45) + ', inset 0 1px 0 rgba(255,255,255,0.10)' : 'none',
          border: boxed ? '1.5px solid ' + alpha(C.accent, 0.45) : 'none',
        }}
      >
        {lines.map((l, i) => {
          const pl = prog(f, i * 3 - 2, 10, EASE_OUT);
          return (
            <div
              key={i}
              style={{
                fontFamily: SERIF_UPRIGHT, fontWeight: 900, fontSize: sizes[i], lineHeight: 1.0,
                letterSpacing: upper ? '0.01em' : '-0.02em', color: i === accent ? C.accent : C.white,
                textShadow: boxed ? (i === accent ? accentGlow(0.7) : 'none') : (i === accent ? outline(stroke) + ', ' + accentGlow(0.6) : outline(stroke)),
                transform: `translateY(${(1 - pl) * 18}px)`, opacity: clamp01(0.4 + pl),
                marginTop: i ? 8 : 0, whiteSpace: 'nowrap',
              }}
            >
              {upper ? l.toUpperCase() : l}
            </div>
          );
        })}
      </div>
    </div>
  );
};

/** Lower-third name tag (two-speaker podcasts only; real names from the video's own title/description). */
export const NameTag: React.FC<{name: string; role?: string; from: number; to: number; y: number; right?: boolean}> = ({
  name, role, from, to, y, right,
}) => {
  const f = useCurrentFrame();
  if (f < from || f >= to) return null;
  const pin = prog(f, from, 10, EASE_OUT);
  const out = prog(f, to - 8, 8, EASE_IN);
  const dx = (right ? 1 : -1) * ((1 - pin) * 60 + out * 60);
  return (
    <div
      style={{
        position: 'absolute', top: y, [right ? 'right' : 'left']: 64, display: 'flex', alignItems: 'stretch', gap: 16,
        transform: `translateX(${dx}px)`, opacity: clamp01(pin * 1.5) * (1 - out), flexDirection: right ? 'row-reverse' : 'row',
      }}
    >
      <div style={{width: 8, borderRadius: 4, background: C.accent, boxShadow: accentGlow(0.6), transform: `scaleY(${pin})`}} />
      <div style={{padding: '14px 24px 16px', borderRadius: 18, background: alpha(C.ink, 0.82), textAlign: right ? 'right' : 'left'}}>
        <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 800, fontSize: 44, color: C.white, lineHeight: 1.05}}>{name}</div>
        {role ? (
          <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 27, color: mix(C.accent, '#FFFFFF', 0.35), marginTop: 4, letterSpacing: '0.04em', textTransform: 'uppercase'}}>
            {role}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export type CardSpec =
  | {type: 'number'; value: number; prefix?: string; suffix?: string; label: string; countFrom?: number; decimals?: number}
  | {type: 'keyword'; kicker?: string; text: string}
  | {type: 'logo'; brand: string; label?: string; glyph?: string}
  | {type: 'list'; title?: string; items: {t: string; f: number}[]}
  | {type: 'quote'; text: string; by?: string};

const fmt = (v: number, d = 0) => v.toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});

/** On-screen card over the talking head (lower third, under the hook / over the band). Enters at `from`, exits at `to`. */
export const ReelCard: React.FC<{spec: CardSpec; from: number; to: number; top: number; land?: number}> = ({spec, from, to, top, land}) => {
  const f = useCurrentFrame() + from; // scenes mount in a Sequence: local frame + FROM = absolute frame
  const pin = prog(f, from, 11, EASE_OUT);
  const out = prog(f, to - 8, 8, EASE_IN);
  const drift = 1 + 0.025 * clamp01((f - from) / Math.max(1, to - from));
  const body = (() => {
    switch (spec.type) {
      case 'number': {
        const c0 = spec.countFrom ?? 0;
        const k = prog(f, (land ?? from) - 6, 22, EASE_OUT);
        const v = c0 + (spec.value - c0) * k;
        return (
          <>
            <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 900, fontSize: 132, color: C.accent, textShadow: accentGlow(0.8), lineHeight: 1}}>
              {(spec.prefix ?? '') + fmt(v, spec.decimals) + (spec.suffix ?? '')}
            </div>
            <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 38, color: C.white, marginTop: 12}}>{spec.label}</div>
          </>
        );
      }
      case 'keyword':
        return (
          <>
            {spec.kicker ? (
              <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 28, letterSpacing: '0.16em', color: mix(C.accent, '#FFFFFF', 0.3), textTransform: 'uppercase'}}>
                {spec.kicker}
              </div>
            ) : null}
            <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 900, fontSize: fitSize(spec.text, SERIF_UPRIGHT, 900, 760, 104), color: C.white, lineHeight: 1.02, marginTop: spec.kicker ? 10 : 0}}>
              {spec.text}
            </div>
          </>
        );
      case 'logo':
        return (
          <div style={{display: 'flex', alignItems: 'center', gap: 34}}>
            <div style={{transform: `scale(${0.6 + 0.4 * prog(f, from + 3, 12, EASE_OUT)})`}}>
              {spec.glyph ? (
                <div style={{width: 170, height: 170, borderRadius: 40, background: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 10px 30px ' + dark(0.35)}}>
                  <Glyph brand={spec.glyph} size={108} />
                </div>
              ) : (
                <BrandLogo name={spec.brand} height={150} style={{maxWidth: 300}} />
              )}
            </div>
            {spec.label ? (
              <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 800, fontSize: spec.label.length > 22 ? 44 : spec.label.length > 12 ? 52 : 62, color: C.white, lineHeight: 1.08, textAlign: 'left', maxWidth: 460}}>
                {spec.label}
              </div>
            ) : null}
          </div>
        );
      case 'list':
        return (
          <div style={{textAlign: 'left', minWidth: 640}}>
            {spec.title ? (
              <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 30, letterSpacing: '0.14em', color: mix(C.accent, '#FFFFFF', 0.3), textTransform: 'uppercase', marginBottom: 14}}>
                {spec.title}
              </div>
            ) : null}
            {spec.items.map((it, i) => {
              const p = prog(f, it.f - 3, 9, EASE_OUT);
              return (
                <div key={i} style={{display: 'flex', alignItems: 'center', gap: 20, margin: '12px 0', opacity: clamp01(p * 1.6), transform: `translateY(${(1 - p) * 18}px)`}}>
                  <div style={{width: 46, height: 46, borderRadius: 23, background: C.accent, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: accentGlow(0.5)}}>
                    <Glyph name="check" size={32} color={C.ink} />
                  </div>
                  <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 800, fontSize: 52, color: C.white}}>{it.t}</div>
                </div>
              );
            })}
          </div>
        );
      case 'quote':
        return (
          <>
            <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 900, fontSize: 120, color: C.accent, lineHeight: 0.6, height: 56}}>“</div>
            <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 800, fontSize: fitSize(spec.text, SERIF_UPRIGHT, 800, 1500, 60), color: C.white, lineHeight: 1.12, maxWidth: 780}}>
              {spec.text}
            </div>
            {spec.by ? <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 30, color: mix(C.accent, '#FFFFFF', 0.35), marginTop: 14}}>{'- ' + spec.by}</div> : null}
          </>
        );
    }
  })();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', left: 0, right: 0, top, display: 'flex', justifyContent: 'center'}}>
        <div
          style={{
            padding: '34px 46px 38px', borderRadius: 38, textAlign: 'center', maxWidth: 900,
            background: `linear-gradient(180deg, ${alpha(mix(C.ink, '#FFFFFF', 0.08), 0.9)} 0%, ${alpha(C.ink, 0.9)} 100%)`,
            border: '1.5px solid rgba(255,255,255,0.10)',
            boxShadow: `0 24px 60px ${dark(0.5)}, inset 0 1px 0 rgba(255,255,255,0.12), 0 0 46px ${alpha(C.accent, 0.18)}`,
            opacity: clamp01(pin * 1.6) * (1 - out),
            transform: `translateY(${(1 - pin) * 70 + out * 40}px) scale(${(0.9 + 0.1 * pin) * drift})`,
            filter: pin >= 1 && out <= 0 ? 'none' : `blur(${(1 - pin) * 10 + out * 10}px)`,
          }}
        >
          {body}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export type SlamWord = {t: string; f: number; line: number};
/** Full-screen text slam on the style's paper: circle reveal in from the face, words pop on their spoken frames,
 *  slow push; hard cut out (Main's FLASHES give the white flash on the way back). */
export const Slam: React.FC<{words: SlamWord[]; accentLine: number; from: number; to: number; cx: number; cy: number; kicker?: string; dark?: boolean; onCut?: boolean}> = ({
  words, accentLine, from, to, cx, cy, kicker, dark: isDark, onCut,
}) => {
  const f = useCurrentFrame() + from;
  const rev = prog(f, from - (onCut ? 5 : 0), 9, EASE_OUT); // on a jump cut the reveal is already full on frame 1
  const r = rev * 2300;
  const push = 1 + 0.045 * clamp01((f - from) / Math.max(1, to - from));
  const lines: SlamWord[][] = [];
  for (const w of words) (lines[w.line] = lines[w.line] || []).push(w);
  const ink = isDark ? C.white : C.ink;
  return (
    <AbsoluteFill style={{clipPath: rev >= 1 ? undefined : `circle(${r}px at ${cx}px ${cy}px)`}}>
      {isDark ? (
        <AbsoluteFill style={{background: `radial-gradient(110% 80% at 50% 35%, ${mix(C.ink, C.accentDeep, 0.25)} 0%, ${C.ink} 70%)`}} />
      ) : (
        <PaperBG tone="palette" />
      )}
      <AbsoluteFill style={{transform: `scale(${push})`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 80px'}}>
        {kicker ? (
          <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 30, letterSpacing: '0.2em', color: isDark ? mix(C.accent, '#FFFFFF', 0.3) : C.accentDeep, textTransform: 'uppercase', marginBottom: 26, opacity: prog(f, from + 2, 8)}}>
            {kicker}
          </div>
        ) : null}
        {lines.map((ln, li) => {
          const text = ln.map((w) => w.t).join(' ');
          const acc = li === accentLine;
          const size = fitSize(text, acc ? SERIF : SERIF_UPRIGHT, acc ? 800 : 900, 900, acc ? 150 : 96);
          return (
            <div key={li} style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: size * 0.25, lineHeight: 1.02, margin: '6px 0'}}>
              {ln.map((w, wi) => {
                const p = prog(f, Math.max(from + 4, w.f - 3), 9, EASE_OUT);
                return (
                  <span
                    key={wi}
                    style={{
                      fontFamily: acc ? SERIF : SERIF_UPRIGHT, fontStyle: acc ? 'italic' : 'normal', fontWeight: acc ? 800 : 900,
                      fontSize: size, color: acc ? C.accent : ink, letterSpacing: '-0.02em',
                      textShadow: acc ? accentGlow(0.6) : 'none', opacity: clamp01(p * 1.7),
                      transform: `translateY(${(1 - p) * 26}px) scale(${0.94 + 0.06 * p})`,
                      filter: p >= 1 ? 'none' : `blur(${(1 - p) * 9}px)`, display: 'inline-block',
                      paddingBottom: '0.1em',
                    }}
                  >
                    {w.t}
                  </span>
                );
              })}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Thin progress bar along the top edge (podcast look). */
export const ProgressBar: React.FC<{total: number}> = ({total}) => {
  const f = useCurrentFrame();
  return (
    <div style={{position: 'absolute', left: 0, top: 0, height: 9, width: 1080 * clamp01(f / Math.max(1, total - 1)), background: C.accent, boxShadow: accentGlow(0.5)}} />
  );
};

/* ---------------------------------------------------------------------------------------------------------------
 * FULL-SCREEN INSERTS (they replace on-screen UI cards): real B-roll stills or video, a moving wall of images, a big real
 * logo, or a big number. Media live in remotion/public/broll/ (fetched per video by work/scripts/broll_fetch.py, never
 * in git). They are drawn inside OS00_Reel under the captions, so the music keeps playing and the words stay readable.
 * ------------------------------------------------------------------------------------------------------------- */
export type InsertSpec =
  | {kind: 'image'; media: string[]; beats?: number[]}
  | {kind: 'video'; media: string[]}
  | {kind: 'wall'; media: string[]; title?: string; titleAt?: number}
  | {kind: 'logo'; brand: string; glyph?: string; lines: {t: string; f: number}[]}
  | {kind: 'number'; value: number; prefix?: string; suffix?: string; label: string; land: number; decimals?: number};
export type InsertDef = {from: number; to: number; spec: InsertSpec};

const media = (m: string) => staticFile('broll/' + m.split('#')[0]);
const isVideo = (m: string) => /\.(mp4|mov|webm)$/i.test(m.split('#')[0]);
// 'gopro.jpg#x=0.3': which part of a wide picture stays in the 9:16 frame (0 left .. 1 right)
// 'clip.mp4#t=2.5': start a B-roll clip 2.5 s into the file
const startAt = (m: string) => {
  const x = /#.*?t=([\d.]+)/.exec(m);
  return x ? Math.round(Number(x[1]) * 30) : 0;
};
const focusX = (m: string) => {
  const x = /#x=([\d.]+)/.exec(m);
  return x ? Math.max(0, Math.min(1, Number(x[1]))) * 100 : 50;
};

const Still: React.FC<{src: string; t: number; seed: number}> = ({src, t, seed}) => {
  // slow Ken Burns: 1.06 -> 1.16 with a small diagonal drift (its direction changes per picture)
  const s = 1.06 + 0.1 * t;
  const dx = (seed % 2 ? 1 : -1) * 24 * t;
  const dy = (seed % 3 ? -1 : 1) * 18 * t;
  return isVideo(src) ? (
    <OffthreadVideo src={media(src)} muted trimBefore={startAt(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${focusX(src)}% 50%`, transform: `scale(${1.02 + 0.06 * t})`}} />
  ) : (
    <Img src={media(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${focusX(src)}% 50%`, transform: `translate(${dx}px, ${dy}px) scale(${s})`}} />
  );
};

const Stage: React.FC<{children: React.ReactNode}> = ({children}) => (
  <AbsoluteFill style={{background: `radial-gradient(120% 85% at 50% 38%, ${mix(C.ink, C.accentDeep, 0.28)} 0%, ${C.ink} 72%)`}}>
    {children}
    <AbsoluteFill style={{background: `radial-gradient(130% 90% at 50% 45%, transparent 55%, ${alpha('#000000', 0.45)} 100%)`}} />
  </AbsoluteFill>
);

export const Insert: React.FC<{d: InsertDef}> = ({d}) => {
  const f = useCurrentFrame();
  if (f < d.from || f >= d.to) return null;
  const len = Math.max(1, d.to - d.from);
  const t = (f - d.from) / len;
  const pin = prog(f, d.from - 3, 8, EASE_OUT); // zoom-through entrance, pre-rolled: the first frame is already covered
  const enter: React.CSSProperties = {transform: `scale(${1.14 - 0.14 * pin})`, filter: pin >= 1 ? 'none' : `blur(${(1 - pin) * 14}px)`, opacity: clamp01(pin * 3)};
  const sp = d.spec;
  let body: React.ReactNode = null;
  if (sp.kind === 'image' || sp.kind === 'video') {
    const beats = sp.kind === 'image' ? sp.beats ?? [] : [];
    let k = 0;
    for (let i = 0; i < beats.length; i++) if (f >= beats[i] - 1) k = i + 1;
    k = Math.min(k, sp.media.length - 1);
    const kStart = k === 0 ? d.from : beats[k - 1] - 1;
    const pop = k === 0 ? 1 : prog(f, kStart, 6, EASE_OUT);
    body = (
      <AbsoluteFill style={{background: C.ink, overflow: 'hidden'}}>
        <AbsoluteFill style={{transform: `scale(${1.05 - 0.05 * pop})`}}>
          <Still src={sp.media[k]} t={t} seed={k + 1} />
        </AbsoluteFill>
        {/* keeps the captions readable over any picture */}
        <AbsoluteFill style={{background: `linear-gradient(180deg, transparent 52%, ${alpha('#000000', 0.55)} 100%)`}} />
      </AbsoluteFill>
    );
  } else if (sp.kind === 'wall') {
    const cols = 3;
    const tileW = 330;
    const tileH = 440;
    const gap = 22;
    const tiles: string[] = [];
    while (tiles.length < 21) tiles.push(...sp.media);
    const drift = -260 * t; // the wall keeps moving: endless references
    const titleP = sp.title ? prog(f, sp.titleAt ?? d.from + 10, 10, EASE_OUT) : 0;
    body = (
      <Stage>
        <AbsoluteFill style={{perspective: 1600}}>
          <div
            style={{
              position: 'absolute', left: 540 - (cols * tileW + (cols - 1) * gap) / 2, top: -260 + drift,
              transform: 'rotateX(14deg) rotateZ(-7deg) scale(1.08)', transformOrigin: '50% 40%',
              display: 'grid', gridTemplateColumns: `repeat(${cols}, ${tileW}px)`, gap,
            }}
          >
            {tiles.slice(0, 21).map((m, i) => {
              const p = prog(f, d.from - 5 + (i % 9) * 1, 8, EASE_OUT); // tiles already arriving on the first frame
              return (
                <div
                  key={i}
                  style={{
                    width: tileW, height: tileH, borderRadius: 22, overflow: 'hidden', background: C.inkSoft,
                    boxShadow: '0 18px 40px ' + alpha('#000000', 0.5), opacity: clamp01(p * 1.5),
                    transform: `translateY(${(1 - p) * 60}px) scale(${0.86 + 0.14 * p})`, marginTop: i % cols === 1 ? 120 : 0,
                  }}
                >
                  {isVideo(m) ? (
                    <OffthreadVideo src={media(m)} muted trimBefore={startAt(m)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                  ) : (
                    <Img src={media(m)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                  )}
                </div>
              );
            })}
          </div>
        </AbsoluteFill>
        {sp.title ? (
          <AbsoluteFill style={{display: 'flex', alignItems: 'center', justifyContent: 'center', background: alpha(C.ink, 0.3 * titleP)}}>
            <div
              style={{
                fontFamily: SERIF_UPRIGHT, fontWeight: 900, fontSize: fitSize(sp.title.toUpperCase(), SERIF_UPRIGHT, 900, 900, 150),
                color: C.white, textShadow: outline(6) + ', ' + accentGlow(0.8), opacity: clamp01(titleP * 1.6),
                transform: `scale(${1.25 - 0.25 * titleP})`, whiteSpace: 'nowrap',
              }}
            >
              {sp.title.toUpperCase()}
            </div>
          </AbsoluteFill>
        ) : null}
      </Stage>
    );
  } else if (sp.kind === 'logo') {
    const lp = prog(f, d.from - 4, 12, EASE_OUT); // the logo is already there on the first frame
    const ring = 0.5 + 0.5 * Math.sin((f - d.from) / 7);
    body = (
      <Stage>
        <AbsoluteFill style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${1 + 0.05 * t})`}}>
          <div
            style={{
              width: 420, height: 420, borderRadius: 999, display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: `0 0 ${80 + 40 * ring}px ${alpha(C.accent, 0.35)}`, background: alpha(C.accent, 0.08),
              transform: `scale(${0.55 + 0.45 * lp})`, opacity: clamp01(lp * 2),
            }}
          >
            {sp.glyph ? (
              <div style={{width: 300, height: 300, borderRadius: 72, background: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <Glyph brand={sp.glyph} size={200} />
              </div>
            ) : (
              <BrandLogo name={sp.brand} height={280} style={{maxWidth: 380}} />
            )}
          </div>
          <div style={{marginTop: 70, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: 22, maxWidth: 920}}>
            {sp.lines.map((w, i) => {
              const p = prog(f, Math.max(d.from + 3, w.f - 3), 9, EASE_OUT);
              const last = i === sp.lines.length - 1;
              return (
                <span
                  key={i}
                  style={{
                    fontFamily: SERIF_UPRIGHT, fontWeight: 900, fontSize: 92, color: last ? C.accent : C.white,
                    textShadow: last ? accentGlow(0.7) : 'none', opacity: clamp01(p * 1.7), transform: `translateY(${(1 - p) * 28}px)`,
                    filter: p >= 1 ? 'none' : `blur(${(1 - p) * 8}px)`, display: 'inline-block',
                  }}
                >
                  {w.t}
                </span>
              );
            })}
          </div>
        </AbsoluteFill>
      </Stage>
    );
  } else if (sp.kind === 'number') {
    const k = prog(f, sp.land - 6, 22, EASE_OUT);
    const v = sp.value * k;
    const lp = prog(f, sp.land + 6, 10, EASE_OUT);
    const full = (sp.prefix ?? '') + fmt(sp.value, sp.decimals) + (sp.suffix ?? '');
    body = (
      <Stage>
        <AbsoluteFill style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${1 + 0.05 * t})`}}>
          <div style={{fontFamily: SERIF_UPRIGHT, fontWeight: 900, fontSize: fitSize(full, SERIF_UPRIGHT, 900, 940, 260), color: C.accent, textShadow: accentGlow(1), lineHeight: 1}}>
            {(sp.prefix ?? '') + fmt(v, sp.decimals) + (sp.suffix ?? '')}
          </div>
          <div
            style={{
              fontFamily: SERIF_UPRIGHT, fontWeight: 800, fontSize: 64, color: C.white, marginTop: 30, maxWidth: 900, textAlign: 'center',
              opacity: clamp01(lp * 1.5), transform: `translateY(${(1 - lp) * 24}px)`,
            }}
          >
            {sp.label}
          </div>
        </AbsoluteFill>
      </Stage>
    );
  }
  // The Sequence starts every B-roll clip at its own first frame when the insert opens (inside OS00_Reel the time would
  // otherwise be the reel's absolute frame: a short clip would show its frozen last frame).
  return (
    <Sequence from={d.from} durationInFrames={len} layout="none">
      <AbsoluteFill style={enter}>{body}</AbsoluteFill>
    </Sequence>
  );
};
