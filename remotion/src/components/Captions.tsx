import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {measureText} from '@remotion/layout-utils';
import {C, SANS, SERIF, accentGlow, sansShadow} from '../theme';
import {EASE_OUT, clamp01, prog} from '../lib/anim';

export type CapWord = {t: string; f: number; accent?: boolean; bold?: boolean};
export type CapGroup = {
  from: number;
  to: number;
  words: CapWord[];
  layout: 'tier3' | 'line' | 'stack2';
  y?: number; // vertical centre of the block (px)
  accentSize?: number; // max accent font size
  sansSize?: number;
  split?: number; // stack2: number of words on the first line
};

const SANS_SIZE = 50;
const MAX_W = 880;

const accentFontSize = (text: string, max: number) => {
  try {
    const w = measureText({text, fontFamily: SERIF, fontSize: 100, fontWeight: 400, additionalStyles: {fontStyle: 'italic'}, validateFontIsLoaded: false}).width;
    return Math.max(84, Math.min(max, (MAX_W / Math.max(1, w)) * 100));
  } catch {
    return max;
  }
};

const Word: React.FC<{w: CapWord; frame: number; kind: 'sans' | 'accent'; size: number}> = ({w, frame, kind, size}) => {
  const start = w.f - 1; // land on the spoken word
  const dur = kind === 'accent' ? 12 : 9;
  const p = prog(frame, start, dur, EASE_OUT);
  const rise = kind === 'accent' ? 34 : 20;
  const blur = kind === 'accent' ? 12 : 8;
  const glowA = kind === 'accent' ? 0.55 + 0.45 * p : 0;
  const style: React.CSSProperties =
    kind === 'accent'
      ? {
          fontFamily: SERIF,
          fontStyle: 'italic',
          fontWeight: 400,
          fontSize: size,
          lineHeight: 0.92,
          color: C.accent,
          WebkitTextStroke: '1.4px ' + C.accent, // thicken: the accent font reads bolder than the light sans
          letterSpacing: '-0.01em',
          textShadow: accentGlow(glowA),
          padding: '0 0.06em',
        }
      : {
          fontFamily: SANS,
          fontWeight: w.bold ? 700 : 500,
          fontSize: size,
          lineHeight: 1.08,
          color: C.white,
          letterSpacing: '-0.02em',
          textShadow: sansShadow,
        };
  // Not-yet-spoken words still render with their FULL style (invisible) so the block's layout never shifts.
  if (frame < start) return <span style={{...style, display: 'inline-block', opacity: 0}}>{w.t}</span>;
  return (
    <span
      style={{
        ...style,
        display: 'inline-block',
        opacity: clamp01(p * 1.7),
        transform: 'translateY(' + ((1 - p) * rise).toFixed(2) + 'px)' + (kind === 'accent' ? ' scale(' + (0.94 + 0.06 * p).toFixed(4) + ')' : ''),
        filter: p < 1 ? 'blur(' + ((1 - p) * blur).toFixed(2) + 'px)' : undefined,
      }}
    >
      {w.t}
    </span>
  );
};

const Line: React.FC<{words: CapWord[]; frame: number; kind: 'sans' | 'accent'; size: number}> = ({words, frame, kind, size}) => (
  <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: kind === 'accent' ? size * 0.22 : size * 0.26, maxWidth: MAX_W + 60}}>
    {words.map((w, i) => (
      <Word key={i} w={w} frame={frame} kind={kind} size={size} />
    ))}
  </div>
);

export const CaptionGroupView: React.FC<{g: CapGroup; frame: number; exitAt?: number}> = ({g, frame, exitAt}) => {
  const sans = g.sansSize ?? SANS_SIZE;
  const fadeOut = exitAt !== undefined ? 1 - prog(frame, exitAt - 4, 4) : 1;
  let body: React.ReactNode;
  if (g.layout === 'tier3') {
    const ai = g.words.findIndex((w) => w.accent);
    const lastA = g.words.length - 1 - [...g.words].reverse().findIndex((w) => w.accent);
    const pre = ai > 0 ? g.words.slice(0, ai) : [];
    const acc = ai >= 0 ? g.words.slice(ai, lastA + 1) : [];
    const post = ai >= 0 ? g.words.slice(lastA + 1) : g.words;
    const aSize = accentFontSize(acc.map((w) => w.t).join(' '), g.accentSize ?? 150);
    body = (
      <>
        {pre.length ? <Line words={pre} frame={frame} kind="sans" size={sans} /> : null}
        {acc.length ? (
          <div style={{margin: '-4px 0 2px'}}>
            <Line words={acc} frame={frame} kind="accent" size={aSize} />
          </div>
        ) : null}
        {post.length ? <Line words={post} frame={frame} kind="sans" size={sans} /> : null}
      </>
    );
  } else if (g.layout === 'stack2') {
    const half = g.split ?? Math.ceil(g.words.length / 2);
    body = (
      <>
        <Line words={g.words.slice(0, half)} frame={frame} kind="sans" size={sans} />
        <Line words={g.words.slice(half)} frame={frame} kind="sans" size={sans} />
      </>
    );
  } else {
    body = <Line words={g.words} frame={frame} kind="sans" size={sans} />;
  }
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: g.y ?? 1250,
        transform: 'translateY(-50%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        opacity: fadeOut,
        filter: fadeOut < 1 ? 'blur(' + ((1 - fadeOut) * 6).toFixed(2) + 'px)' : undefined,
      }}
    >
      {body}
    </div>
  );
};

export const Captions: React.FC<{groups: CapGroup[]; hiddenAt?: (f: number) => boolean; cutFrames?: number[]}> = ({groups, hiddenAt, cutFrames = []}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  if (hiddenAt && hiddenAt(frame)) return null;
  let gi = groups.findIndex((g) => frame >= g.from && frame < g.to);
  if (gi < 0) return null;
  // No blink between back-to-back groups: until the new group's first word starts popping, keep the previous line.
  {
    const g0 = groups[gi];
    const prev = groups[gi - 1];
    const firstPop = Math.min(...g0.words.map((w) => w.f)) - 1;
    if (prev && prev.to === g0.from && frame < firstPop && !cutFrames.some((c) => Math.abs(c - g0.from) <= 2)) gi = gi - 1;
  }
  const g = groups[gi];
  const next = groups[gi + 1];
  const isLast = !next && g.to >= durationInFrames; // the final caption holds through the last frame
  const atCut = cutFrames.some((c) => Math.abs(c - g.to) <= 2); // a full-screen scene hard-cuts in -> caption cuts with it
  const soft = !isLast && !atCut && (!next || next.from - g.to >= 4); // fade only when there's room; otherwise hard swap
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <CaptionGroupView g={g} frame={frame} exitAt={soft ? g.to : undefined} />
    </AbsoluteFill>
  );
};

/** Darkened band behind lower-third text (the blur comes from BlurBand in ARoll.tsx). */
export const LowerShade: React.FC<{strength?: number; top?: number; dark?: number}> = ({strength = 1, top = 900, dark = 1}) => (
  <AbsoluteFill style={{pointerEvents: 'none', opacity: strength}}>
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top,
        bottom: 0,
        background:
          'linear-gradient(to bottom, rgba(4,10,16,0) 0%, rgba(4,10,16,' + (0.42 * dark).toFixed(3) + ') 35%, rgba(4,10,16,' + (0.62 * dark).toFixed(3) + ') 80%, rgba(4,10,16,' + Math.min(0.92, 0.8 * dark).toFixed(3) + ') 100%)', // deep at the very bottom: hides desk LEDs in wide shots
      }}
    />
  </AbsoluteFill>
);
