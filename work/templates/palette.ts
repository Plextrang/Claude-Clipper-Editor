// PER-VIDEO footage palette. Written by work/scripts/palette.py (do not edit by hand; re-run it with --accent/--warm to
// steer it). null = use the client style's own colours. The engine's theme.ts merges it over the style's C tokens.
export type Palette = {
  accent: string;
  accentRgb: string;
  accentDeep: string;
  accentSoft: string;
  warm: string;
  warmDeep: string;
  ink: string;
  inkSoft: string;
  grey: string;
  paper: string;
  paperCool: string;
  grid: string;
};

export const PALETTE: Palette | null = null;
