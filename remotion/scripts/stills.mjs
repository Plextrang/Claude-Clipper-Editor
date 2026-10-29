// Render many stills of a composition with a single bundle.
// usage: node scripts/stills.mjs <compositionId> <outDir> <frame> [frame...] [--scale=0.5] [--entry=src/preview/X.entry.tsx]
// (default entry src/index.ts = Main; pass --entry to render a scene's own preview composition, local frame numbers)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';
import net from 'node:net';

const args = process.argv.slice(2);
const scaleArg = args.find((a) => a.startsWith('--scale='));
const scale = scaleArg ? Number(scaleArg.split('=')[1]) : 0.5;
const entryArg = args.find((a) => a.startsWith('--entry='));
const entry = entryArg ? entryArg.split('=')[1] : 'src/index.ts';
const [id, outDir, ...rest] = args.filter((a) => !a.startsWith('--'));
const frames = rest.map(Number);
if (!id || !outDir || !frames.length || frames.some((f) => !Number.isInteger(f) || f < 0)) {
  console.error('usage: node scripts/stills.mjs <compositionId> <outDir> <frame> [frame...]  (frames separated by SPACES, e.g. 3 40 120)');
  process.exit(1);
}
fs.mkdirSync(outDir, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve(entry)});
const browser = await openBrowser('chrome');
// free ports of our own (one per worker: every render call starts its own server), so another dev server already on
// 3000/3001 can never answer Remotion's requests
const freePort = () => new Promise((res) => {
  const srv = net.createServer().listen(0, '127.0.0.1', () => { const p = srv.address().port; srv.close(() => res(p)); });
});
const composition = await selectComposition({serveUrl, id, puppeteerInstance: browser, port: await freePort()});
const conc = Number(process.env.CONC || 3);
let i = 0;
const work = async () => {
  const port = await freePort();
  while (i < frames.length) {
    const f = frames[i++];
    const out = path.join(outDir, `${id}_${String(f).padStart(4, '0')}.png`);
    if (process.env.SKIP_EXISTING && fs.existsSync(out)) continue;
    await renderStill({composition, serveUrl, frame: f, output: out, scale, imageFormat: 'png', puppeteerInstance: browser, timeoutInMilliseconds: 180000, port});
    process.stdout.write(`${f} `);
  }
};
await Promise.all(Array.from({length: conc}, work));
await browser.close({silent: true});
console.log('\ndone');
process.exit(0);
