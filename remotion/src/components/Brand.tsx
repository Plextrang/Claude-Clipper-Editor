import React, {useEffect, useState} from 'react';
import {Img, cancelRender, continueRender, delayRender, staticFile} from 'remotion';

/**
 * REAL brand assets for scenes (fetched by work/scripts/fetch_brand_assets.py into public/brand and public/ui; the
 * index is public/brand/README.md). Never draw a stand-in logo, a fake app icon or a generic play triangle.
 *
 * <BrandLogo name="premiere" width={120} />        official full-colour logo (public/brand/<name>.svg), own colours,
 *                                                   never recoloured or stretched (objectFit contain keeps proportions)
 * <Glyph name="thumb_up" size={40} color={C.ink} /> real UI glyph (Material Symbols Rounded, public/ui/<name>.svg)
 * <Glyph name="thumb_up" fill ... />                the filled variant (<name>-fill.svg)
 * <Glyph brand="instagram" size={60} />             simple-icons brand glyph (public/brand/si_<slug>.svg), painted in its
 *                                                   brand colour from brand_colors.json unless `color` is given
 * Glyphs are inlined as SVG paths and held with delayRender until loaded, so no frame renders without them.
 */
export const BrandLogo: React.FC<{name: string; width?: number; height?: number; style?: React.CSSProperties}> = ({
  name,
  width,
  height,
  style,
}) => (
  <Img
    src={staticFile('brand/' + (/\.(svg|png|webp|jpg)$/i.test(name) ? name : name + '.svg'))}
    style={{width, height, objectFit: 'contain', display: 'block', ...style}}
  />
);

type G = {vb: string; d: string[]};
const cache: Record<string, G> = {};
const pending: Record<string, Promise<G>> = {};
let colors: Record<string, {title: string; hex: string | null}> | null = null;
let colorsP: Promise<void> | null = null;

const load = (src: string): Promise<G> => {
  if (!pending[src]) {
    pending[src] = fetch(staticFile(src))
      .then((r) => {
        if (!r.ok) throw new Error('missing ' + src + ' (run python work/scripts/fetch_brand_assets.py, see its --si/--ui options)');
        return r.text();
      })
      .then((t) => {
        const vb = (t.match(/viewBox="([^"]+)"/) || [])[1] || '0 0 24 24';
        const d: string[] = [];
        const re = /<path[^>]*\sd="([^"]+)"/g;
        let m: RegExpExecArray | null;
        while ((m = re.exec(t)) !== null) d.push(m[1]);
        cache[src] = {vb, d};
        return cache[src];
      });
  }
  return pending[src];
};
const loadColors = (): Promise<void> => {
  if (!colorsP) {
    colorsP = fetch(staticFile('brand/brand_colors.json'))
      .then((r) => (r.ok ? r.json() : {}))
      .then((j) => {
        colors = j;
      });
  }
  return colorsP;
};

export const Glyph: React.FC<{
  name?: string; // Material Symbols name (public/ui)
  brand?: string; // simple-icons slug (public/brand/si_<slug>.svg)
  fill?: boolean; // Material: the filled variant
  size: number;
  color?: string; // required look for UI glyphs; brand glyphs default to their brand colour
  style?: React.CSSProperties;
}> = ({name, brand, fill, size, color, style}) => {
  const src = brand ? 'brand/si_' + brand + '.svg' : 'ui/' + name + (fill ? '-fill' : '') + '.svg';
  const ready = () => !!cache[src] && (!brand || color !== undefined || colors !== null);
  const [g, setG] = useState<G | null>(cache[src] ?? null);
  const [handle] = useState(() => (ready() ? null : delayRender('glyph ' + src)));
  useEffect(() => {
    Promise.all([load(src), brand && color === undefined ? loadColors() : Promise.resolve()])
      .then(([res]) => {
        setG(res);
        if (handle !== null) continueRender(handle);
      })
      .catch((e) => cancelRender(e));
  }, [src, brand, color, handle]);
  const paint = color ?? (brand && colors?.[brand]?.hex) ?? '#000';
  return (
    <svg width={size} height={size} viewBox={g ? g.vb : '0 0 24 24'} style={{display: 'block', overflow: 'visible', flexShrink: 0, ...style}}>
      {g ? g.d.map((d, i) => <path key={i} d={d} fill={paint} />) : null}
    </svg>
  );
};
