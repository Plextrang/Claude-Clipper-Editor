"""edit-any-video router: the mechanical half of "edit this: <YouTube URL or video file>" (the skill does the judgment).
State lives in work/run_state.json, so an interrupted run continues where it stopped ("continue"). Starting another
video parks the current run in work/runs/; starting that video again later brings its run back (moments, queue, files).

  python work/scripts/eav.py start "<url or file>" [--style podcast|talking-head|clip|<yours>] [--count 3|all]
  python work/scripts/eav.py fetch            download the audio + word-level transcript (long videos; clipper)
      ... Claude reads output/<project>/transcript/transcript.txt and writes output/<project>/clips.json ...
  python work/scripts/eav.py cut              check the clip boundaries, then cut raw 9:16 reframed clips (no captions)
  python work/scripts/eav.py queue [--style S] [--count N|all] [--clips 4,5] [--rest] [--redo]
                                              choose which moments get edited, in which style; writes clips.md.
                                              --also adds to the request just queued (e.g. a second style).
                                              --redo edits clips again that are already done in that style (a new
                                              version: "... v2.mp4"; the old one stays). A new request goes ahead of
                                              clips still pending from an older request.
  python work/scripts/eav.py next [--continue]  prepare the engine for the next clip of the latest request (or render
                                              its `clip`-style clips right away) and print what to do; --continue also
                                              takes clips left pending by an older request ("continue")
  python work/scripts/eav.py done             collect the finished engine edit into deliverables/<video>/, archive the
                                              engine, mark the clip done, print what's next
  python work/scripts/eav.py fail "<why>"     give up on the current clip (archived as -failed), move on
  python work/scripts/eav.py status           where the run is; what "continue" will do
Short inputs (<= 90 s) skip fetch/cut: one reel. Deliverables: deliverables/<video title>/NN - <clip title> [style].mp4,
one subfolder per clip with its extras, clips.md (every moment found) and REPORT.md (steps, timings, things to check)."""
import venv_boot  # noqa: F401  (re-runs this script inside .venv when it exists)
import os, sys, json, glob, re, shutil, subprocess, time, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # work/
PROJ = os.path.dirname(ROOT)
STATE = os.path.join(ROOT, 'run_state.json')
OUTPUT = os.path.join(PROJ, 'output')
DELIV = os.path.join(PROJ, 'deliverables')
INPUT = os.path.join(PROJ, 'input')
VIDEO_EXT = ('.mp4', '.mov', '.mkv', '.m4v', '.webm')
SHORT_MAX = 90.0
DEFAULT_COUNT = 3
ENGINE_DEFAULT = {'long': 'podcast', 'short': 'talking-head'}
now = lambda: time.time()
stamp = lambda t: datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')


def die(msg):
    print('ERROR: ' + msg)
    sys.exit(1)


RUNS = os.path.join(ROOT, 'runs')


def run_key(src):
    return re.sub(r'[^a-z0-9]+', '-', os.path.basename(src.rstrip('/')).lower()).strip('-')[:60] or 'video'


def load():
    return json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else None


def save(st):
    json.dump(st, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def need_state():
    st = load()
    if not st:
        die('no run yet. Start one: python work/scripts/eav.py start "<url or file>"')
    return st


def opt(name, default=None):
    a = sys.argv
    for i, x in enumerate(a):
        if x == name and i + 1 < len(a):
            return a[i + 1]
        if x.startswith(name + '='):
            return x.split('=', 1)[1]
    return default


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', path],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    info = json.loads(r.stdout or '{}')
    v = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), {})
    w, h = int(v.get('width', 0) or 0), int(v.get('height', 0) or 0)
    for sd in v.get('side_data_list', []) or []:
        if abs(int(sd.get('rotation', 0) or 0)) in (90, 270):
            w, h = h, w
    return {'duration': float(info.get('format', {}).get('duration', 0) or 0), 'width': w, 'height': h}


def run_py(args, log_name=None):
    """Run a repo python command (clipper via run.py, or an engine script), streaming its output."""
    cmd = [sys.executable, *args]
    print('$ python ' + ' '.join(f'"{a}"' if ' ' in a else a for a in args), flush=True)
    r = subprocess.run(cmd, cwd=PROJ, env=dict(os.environ, EAV_ROUTER='1'))
    return r.returncode


def timing(st, step, t0):
    st.setdefault('timings', []).append({'step': step, 'start': stamp(t0), 'sec': round(now() - t0, 1)})


def safe_name(s, n=80):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', s or 'video').strip().rstrip('.')
    s = re.sub(r'\s+', ' ', s)
    return (s[:n].rstrip() or 'video')


def slug(s, n=40):
    s = re.sub(r'[^\w\s-]', '', s or '', flags=re.UNICODE).strip().lower()
    return re.sub(r'[\s_-]+', '-', s)[:n].strip('-') or 'video'


def project_dir(st):
    return os.path.join(OUTPUT, st['video']['project']) if st['video'].get('project') else None


def clips_json(st):
    pd = project_dir(st)
    p = os.path.join(pd, 'clips.json') if pd else None
    return json.load(open(p, encoding='utf-8')) if p and os.path.exists(p) else None


def video_folder(st):
    d = os.path.join(DELIV, safe_name(st['video']['title']))
    os.makedirs(d, exist_ok=True)
    return d


def fmt_ts(t):
    t = max(0.0, float(t))
    h, r = divmod(int(t), 3600)
    m, s = divmod(r, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


# ------------------------------------------------------------------------------------------------ start
def cmd_start():
    if len(sys.argv) < 3:
        die('usage: eav.py start "<url or file>" [--style S] [--count N|all]')
    src = sys.argv[2].strip().strip('"')
    is_url = src.startswith(('http://', 'https://'))
    old = load()
    style = opt('--style')
    count = opt('--count')
    if old and old['video']['source'] == src:
        # same video again (e.g. "edit this in clip style"): keep the project, download and transcript
        if style or count:
            old['request'] = {'style': style or old['request'].get('style'), 'count': count or old['request'].get('count')}
        save(old)
        print(f"same video as the current run: {old['video']['title']} (project reused: nothing is downloaded twice)")
        print(next_hint(old))
        return
    if old:  # park the current run so this video can be picked up again later
        os.makedirs(RUNS, exist_ok=True)
        json.dump(old, open(os.path.join(RUNS, run_key(old['video']['source']) + '.json'), 'w', encoding='utf-8'), indent=1,
                  ensure_ascii=False)
        if any(c['status'] in ('in_progress', 'pending') for c in old.get('queue', [])):
            print(f"note: \"{old['video'].get('title')}\" still has unfinished clips; start it again later to continue them")
    parked = os.path.join(RUNS, run_key(src if is_url else os.path.abspath(os.path.expanduser(src))) + '.json')
    if os.path.exists(parked):
        st = json.load(open(parked, encoding='utf-8'))
        if style or count:
            st['request'] = {'style': style or st['request'].get('style'), 'count': count or st['request'].get('count')}
        save(st)
        print(f"back to an earlier run of this video: {st['video'].get('title')} (its moments, cuts and finished reels are reused)")
        print(next_hint(st))
        return
    if is_url:
        kind, dur, title = 'url', None, None
    else:
        p = os.path.abspath(os.path.expanduser(src))
        if not os.path.isfile(p):
            die(f'file not found: {p}')
        info = probe(p)
        dur, title = info['duration'], os.path.splitext(os.path.basename(p))[0]
        if os.path.normcase(os.path.dirname(p)) == os.path.normcase(INPUT):
            # a file dropped into input/: keep a copy outside it (the engine's input/ is emptied between clips)
            keep = os.path.join(OUTPUT, '_sources')
            os.makedirs(keep, exist_ok=True)
            shutil.copy2(p, os.path.join(keep, os.path.basename(p)))
            p = os.path.join(keep, os.path.basename(p))
        src = p
        kind = 'file'
    st = {'video': {'source': src, 'kind': kind, 'title': title, 'duration': dur, 'project': None,
                    'length': None if dur is None else ('short' if dur <= SHORT_MAX else 'long')},
          'request': {'style': style, 'count': count}, 'queue': [], 'timings': [], 'created': stamp(now())}
    save(st)
    if kind == 'file' and dur <= SHORT_MAX:
        st['video']['length'] = 'short'
        st['video']['landscape'] = bool(info['width'] and info['width'] / max(1, info['height']) > 0.75)
        save(st)
        print(f'short video ({dur:.1f} s): one reel, default style {ENGINE_DEFAULT["short"]}'
              + (' (landscape: it is reframed to 9:16 around the speaker first)' if st['video']['landscape'] else ''))
    else:
        print(('long video' if kind == 'file' else 'YouTube/web video') + ': find the best moments first')
    print(next_hint(st))


# ------------------------------------------------------------------------------------------------ fetch
def cmd_fetch():
    st = need_state()
    t0 = now()
    args = ['run.py', 'fetch', st['video']['source']]
    if opt('--cookies-from-browser'):
        args += ['--cookies-from-browser', opt('--cookies-from-browser')]
    if run_py(args) != 0:
        die('fetch failed (read the error above: missing tool, YouTube sign-in check -> --cookies-from-browser chrome, ...)')
    # find the project the clipper made (newest project.json with this source)
    best = None
    for pj in glob.glob(os.path.join(OUTPUT, '*', 'project.json')):
        try:
            d = json.load(open(pj, encoding='utf-8'))
        except Exception:
            continue
        if d.get('source') == st['video']['source'] and (best is None or os.path.getmtime(pj) > best[0]):
            best = (os.path.getmtime(pj), os.path.basename(os.path.dirname(pj)), d)
    if not best:
        die('fetch ran but no project was found in output/')
    _, name, d = best
    st['video'].update({'project': name, 'title': d.get('title') or st['video']['title'], 'duration': d.get('duration'),
                        'channel': d.get('channel'), 'description': (d.get('description') or '')[:1200]})
    dur = float(d.get('duration') or 0)
    st['video']['length'] = 'short' if dur and dur <= SHORT_MAX else 'long'
    timing(st, 'download + transcription', t0)
    st['fetched_at'] = now()
    save(st)
    print(f"\nproject output/{name}: {st['video']['title']} ({fmt_ts(dur)})")
    print(next_hint(st))


# ------------------------------------------------------------------------------------------------ cut
def auto_clips_json(st):
    """Short video: one clip = the whole recording (only used for the clip style / landscape reframing)."""
    pd = project_dir(st)
    words = json.load(open(os.path.join(pd, 'transcript', 'words.json'), encoding='utf-8'))
    title = st['video']['title']
    end = next((i for i, w in enumerate(words[:40]) if w['w'][-1:] in '.?!'), min(len(words), 20) - 1)
    a, b = max(0.0, words[0]['s'] - 0.3), words[-1]['e'] + 0.3  # a little room: the engine refines the bounds itself
    clip = {'id': 1, 'title': title, 'hook': ' '.join(w['w'] for w in words[:end + 1]), 'ranges': [[round(a, 2), round(b, 2)]],
            'score': 0, 'emphasis': [], 'caption': ''}
    json.dump({'clips': [clip]}, open(os.path.join(pd, 'clips.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


def cmd_cut():
    st = need_state()
    pd = project_dir(st)
    if not pd:
        die('run eav.py fetch first')
    if not clips_json(st):
        if st['video']['length'] == 'short':
            auto_clips_json(st)
        else:
            die(f'no output/{st["video"]["project"]}/clips.json yet: pick the moments first (skill step 3)')
    t0 = now()
    if st.get('fetched_at') and st['video']['length'] != 'short' and not any(t['step'].startswith('picking') for t in st.get('timings', [])):
        st['timings'].append({'step': 'picking the moments (Claude reads the transcript)', 'start': stamp(st['fetched_at']),
                              'sec': round(t0 - st['fetched_at'], 1)})
    if '--force' not in sys.argv:
        r = subprocess.run([sys.executable, 'run.py', 'cut', st['video']['project'], '--check'], cwd=PROJ, capture_output=True,
                           text=True, encoding='utf-8', errors='replace')
        print(r.stdout.strip())
        if 'need a look' in r.stdout:
            print('\nfix those ranges in clips.json (python run.py find <project> "<phrase>"), then run eav.py cut again, '
                  'or `eav.py cut --force` when the cut is intentional')
            sys.exit(2)
    extra = ['--clips', opt('--clips')] if opt('--clips') else []
    if run_py(['run.py', 'cut', st['video']['project'], *extra]) != 0:
        die('cut failed (see above)')
    timing(st, 'cut + 9:16 reframe', t0)
    st['video']['picked'] = len(clips_json(st)['clips'])
    save(st)
    write_clips_md(st)
    print(next_hint(st))


# ------------------------------------------------------------------------------------------------ queue
def ranked(st):
    cj = clips_json(st)
    clips = cj['clips'] if cj else []
    return sorted(clips, key=lambda c: (-float(c.get('score', 0) or 0), int(c.get('id', 0))))


def cmd_queue():
    st = need_state()
    style = opt('--style') or st['request'].get('style') or ENGINE_DEFAULT[st['video']['length'] or 'long']
    if '--rest' in sys.argv and not opt('--style') and style == 'clip':
        # "edit the rest" means the premium edit: the last engine style used, else the default
        engine = [c['style'] for c in st['queue'] if c['style'] != 'clip']
        style = engine[-1] if engine else ENGINE_DEFAULT[st['video']['length'] or 'long']
    count = opt('--count') or st['request'].get('count')
    if st['video']['length'] == 'short':
        if style == 'clip' and not clips_json(st):
            die('clip style on a short video: run eav.py fetch and eav.py cut first')
        ids = [1]
    else:
        clips = ranked(st)
        if not clips:
            die('no clips.json yet: pick the moments first')
        done_in_style = {c['id'] for c in st['queue'] if c['style'] == style and c['status'] in ('done', 'pending', 'in_progress')}
        if opt('--clips'):
            ids = [int(x) for x in opt('--clips').split(',') if x.strip()]
        elif '--rest' in sys.argv:
            ids = [int(c['id']) for c in clips if int(c['id']) not in done_in_style]
        elif count == 'all' or (style == 'clip' and not count):
            ids = [int(c['id']) for c in clips]
        else:
            ids = [int(c['id']) for c in clips][:int(count or DEFAULT_COUNT)]
        if '--redo' in sys.argv:
            busy = {c['id'] for c in st['queue'] if c['style'] == style and c['status'] in ('pending', 'in_progress')}
            ids = [i for i in ids if i not in busy]
        else:
            ids = [i for i in ids if i not in done_in_style]
    if style != 'clip':
        sd = os.path.join(PROJ, 'styles', style)
        if '/' not in style and not os.path.isdir(sd):
            die(f'no style styles/{style} (available: ' + ', '.join(sorted(d for d in os.listdir(os.path.join(PROJ, 'styles')) if not d.startswith('_'))) + ')')
    added = 0
    batch = st.get('batch', 0) + (0 if '--also' in sys.argv else 1)  # --also: part of the same request
    for i in ids:
        if any(c['id'] == i and c['style'] == style and c['status'] in ('pending', 'in_progress') for c in st['queue']):
            continue
        if '--redo' not in sys.argv and any(c['id'] == i and c['style'] == style and c['status'] == 'done' for c in st['queue']):
            continue
        st['queue'].append({'id': i, 'style': style, 'status': 'pending', 'batch': batch, **({'redo': True} if '--redo' in sys.argv else {})})
        added += 1
    if added:
        st['batch'] = batch
    st['request']['style'] = style
    save(st)
    write_clips_md(st)
    print(f'queued {added} clip(s) in {style}: {ids}' if added else f'nothing new to queue in {style}')
    print(next_hint(st))


# ------------------------------------------------------------------------------------------------ engine housekeeping
def engine_dirty():
    if [p for p in glob.glob(os.path.join(PROJ, 'remotion', 'src', 'scenes', '*')) if not p.endswith('.gitkeep')]:
        return True
    if os.path.exists(os.path.join(ROOT, 'transcript', 'edl.json')) or os.path.exists(os.path.join(ROOT, 'audio', 'voice48k.wav')):
        return True
    if glob.glob(os.path.join(DELIV, 'FINAL - *.mp4')):
        return True
    return any(p.lower().endswith(VIDEO_EXT) for p in glob.glob(os.path.join(INPUT, '*')))


def archive_engine(name):
    """Archive every per-video file of the engine (new_video.py) + any raw left in input/, under a unique name."""
    base, k = name, 2
    while os.path.exists(os.path.join(PROJ, 'archive', name)):
        name = f'{base}-{k}'; k += 1
    if run_py(['work/scripts/new_video.py', name, '--quiet']) != 0:
        die('archiving the engine failed (new_video.py)')
    for p in glob.glob(os.path.join(INPUT, '*')):
        if p.lower().endswith(VIDEO_EXT):
            d = os.path.join(PROJ, 'archive', name, 'input')
            os.makedirs(d, exist_ok=True)
            shutil.move(p, os.path.join(d, os.path.basename(p)))
    return name


def clip_meta(st, cid):
    pd = project_dir(st)
    if not pd:
        return None, None
    cj = clips_json(st) or {'clips': []}
    pick = next((c for c in cj['clips'] if int(c.get('id', 0)) == cid), None)
    meta = None
    for m in glob.glob(os.path.join(pd, 'clips', f'{cid:02d}-*.json')):
        meta = json.load(open(m, encoding='utf-8'))
    return pick, meta


def free_base(vf, base):
    """'NN - title [style]' or, when that reel already exists (a re-edit), 'NN - title [style] v2' (v3, ...)."""
    b, k = base, 2
    while os.path.exists(os.path.join(vf, b + '.mp4')):
        b = f'{base} v{k}'
        k += 1
    return b


def conform(src, dst):
    """Any clip/recording -> 1080x1920, 30 fps CFR, the engine's input format (cover-crop if it isn't 9:16)."""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf',
                    'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,format=yuv420p',
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
                    '-movflags', '+faststart', dst], check=True)


# ------------------------------------------------------------------------------------------------ next
def render_clip_style(st, items):
    pd = project_dir(st)
    ids = ','.join(str(c['id']) for c in items)
    t0 = now()
    for c in items:
        c['status'] = 'in_progress'
    save(st)
    if run_py(['run.py', 'edit', st['video']['project'], '--clips', ids]) != 0:
        die('clip-style render failed (see above)')
    vf = video_folder(st)
    per = (now() - t0) / max(1, len(items))
    for c in items:
        pick, meta = clip_meta(st, c['id'])
        name = meta['name'] if meta else f"{c['id']:02d}"
        src = os.path.join(pd, 'edited', name + '.mp4')
        if not os.path.exists(src):
            c['status'] = 'failed'; c['note'] = 'no edited file'; continue
        title = safe_name((pick or {}).get('title') or name, 60)
        base = free_base(vf, f"{c['id']:02d} - {title} [clip]")
        out = os.path.join(vf, base + '.mp4')
        shutil.copy2(src, out)
        extras = os.path.join(vf, base)
        os.makedirs(extras, exist_ok=True)
        srt = os.path.join(pd, 'edited', name + '.srt')
        if os.path.exists(srt):
            shutil.copy2(srt, os.path.join(extras, 'captions.srt'))
        if pick and pick.get('caption'):
            open(os.path.join(extras, 'post_caption.txt'), 'w', encoding='utf-8').write(pick['caption'] + '\n')
        c.update(status='done', output=os.path.relpath(out, PROJ).replace(os.sep, '/'), sec=round(per, 1), finished=stamp(now()))
    timing(st, f'clip style: render {len(items)} clip(s)', t0)
    save(st)
    write_clips_md(st)
    write_report(st)


def cmd_next():
    st = need_state()
    cur = next((c for c in st['queue'] if c['status'] == 'in_progress'), None)
    if cur and cur['style'] != 'clip':
        # an interrupted engine edit: start that clip again from a clean engine (its partial files are archived)
        print(f"clip {cur['id']} [{cur['style']}] was interrupted: archiving its partial work and starting it again")
        if engine_dirty():
            cur['archive_partial'] = archive_engine(f"{slug(st['video']['title'], 24)}-{cur['id']:02d}-{cur['style']}-partial")
        cur['status'] = 'pending'
        cur['restarts'] = cur.get('restarts', 0) + 1
        if cur.get('t0'):  # time spent on the attempt that was interrupted (shown in REPORT.md)
            cur['lost_sec'] = round(cur.get('lost_sec', 0) + now() - cur.pop('t0'), 1)
        save(st)
    latest = st.get('batch', 0)
    serve = lambda c: '--continue' in sys.argv or c.get('batch', 0) == latest
    clip_items = [c for c in st['queue'] if c['status'] in ('pending', 'in_progress') and c['style'] == 'clip' and serve(c)]
    if clip_items:
        render_clip_style(st, clip_items)
        print(f'{len(clip_items)} clip-style reel(s) are in {os.path.relpath(video_folder(st), PROJ)}')
    item = next((c for c in st['queue'] if c['status'] == 'pending' and serve(c)), None)
    older = [c for c in st['queue'] if c['status'] == 'pending' and not serve(c)]
    if not item and older:
        write_clips_md(st); write_report(st)
        print('REQUEST DONE -> ' + os.path.relpath(video_folder(st), PROJ).replace(os.sep, '/'))
        print('Clips still pending from an earlier request: ' + ', '.join(f"{c['id']} [{c['style']}]" for c in older)
              + '. They are NOT edited now; the user can say "continue" (eav.py next --continue) to edit them.')
        return
    if not item:
        write_clips_md(st); write_report(st)
        print('ALL QUEUED CLIPS DONE -> ' + os.path.relpath(video_folder(st), PROJ).replace(os.sep, '/'))
        print(next_hint(st))
        return
    if engine_dirty():
        leftover = archive_engine('leftover-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        print(f'the engine still held another video: archived it to archive/{leftover}/ (nothing deleted)')
    # the clip's raw footage
    if st['video']['length'] == 'short' and not project_dir(st):
        src, pick, meta = st['video']['source'], None, None
        title = st['video']['title']
        info = probe(src)
        if info['width'] and info['width'] / max(1, info['height']) > 0.75:
            die('this short video is landscape: run `eav.py fetch` then `eav.py cut` first (that reframes it to 9:16 '
                'around the speaker), then `eav.py next` again')
    else:
        pick, meta = clip_meta(st, item['id'])
        if not meta:
            die(f"clip {item['id']} has not been cut yet: run eav.py cut")
        src = os.path.join(project_dir(st), 'clips', meta['file'])
        title = (pick or {}).get('title') or meta.get('title') or st['video']['title']
    os.makedirs(INPUT, exist_ok=True)
    dst = os.path.join(INPUT, f"{item['id']:02d}-{slug(title)}.mp4")
    print(f"preparing clip {item['id']} \"{title}\" for the {item['style']} style ...", flush=True)
    conform(src, dst)
    r = subprocess.run([sys.executable, 'work/scripts/use_style.py', item['style']], cwd=PROJ, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        die('could not select the style')
    write_brief(st, item, title, pick, meta)
    item.update(status='in_progress', title=title, started=stamp(now()), t0=now())
    save(st)
    print(f"""
READY: clip {item['id']} "{title}" -> style {item['style']}
  input/{os.path.basename(dst)}  (1080x1920, 30 fps)   brief: work/plan/clip_brief.md
NOW: run the short-form-edit skill on it, style `{item['style']}` (already selected: skip step 0 parts 2-4), following the
     style's STYLE_GUIDE.md (kit styles: SKILL section 4). When deliverables/FINAL - <title>.mp4 exists, run:
     python work/scripts/eav.py done""")


def write_brief(st, item, title, pick, meta):
    os.makedirs(os.path.join(ROOT, 'plan'), exist_ok=True)
    v = st['video']
    L = [f'# Clip brief (from the edit-any-video router)', '',
         f"- Video: {v.get('title')}" + (f" - channel: {v['channel']}" if v.get('channel') else ''),
         f"- Source: {v['source']}", f"- Clip {item['id']}: {title}", f"- Style: {item['style']}"]
    if pick:
        L += [f"- Hook line: {pick.get('hook', '')}"]
        if pick.get('why'):
            L += [f"- Why it works: {pick['why']}"]
        if pick.get('emphasis'):
            L += [f"- Emphasis words picked with the moment: {', '.join(pick['emphasis'])}"]
        L += [f"- Source range(s): " + ', '.join(f'{fmt_ts(a)}-{fmt_ts(b)}' for a, b in pick.get('ranges', []))]
    if meta:
        L += [f"- Raw clip: {meta['duration']:.1f} s, {len(meta.get('shots', []))} camera shot(s), splices at {meta.get('splices', [])}"]
    if v['length'] == 'short':
        L += ['- A single recording: the clip title above is just its file name. Give the reel a real 3-6 word title from what is',
              '  said (it names FINAL - <title>.mp4 and the deliverable).']
    if v.get('description'):
        L += ['', '## Video description (from the platform; real names of the host / guests are usually here)', '',
              v['description'].strip()]
    L += ['', 'Use the title for FINAL - <title>.mp4. Names for vocabulary.txt and name tags come only from the video title,',
          'channel or what is said in the clip; never invent a name.']
    open(os.path.join(ROOT, 'plan', 'clip_brief.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


# ------------------------------------------------------------------------------------------------ done / fail
def cmd_done():
    st = need_state()
    item = next((c for c in st['queue'] if c['status'] == 'in_progress' and c['style'] != 'clip'), None)
    if not item:
        die('no clip is being edited (eav.py status)')
    finals = sorted(glob.glob(os.path.join(DELIV, 'FINAL - *.mp4')), key=os.path.getmtime)
    if not finals:
        die('no deliverables/FINAL - <title>.mp4 yet: finish the edit first (or eav.py fail "<why>")')
    final = finals[-1]
    vf = video_folder(st)
    # the title the edit gave its FINAL file (the clip title), else the moment's title from clips.json
    title = safe_name(os.path.basename(final)[len('FINAL - '):-4] or item.get('title'), 60)
    base = free_base(vf, f"{item['id']:02d} - {title} [{item['style']}]")
    shutil.move(final, os.path.join(vf, base + '.mp4'))
    extras = os.path.join(vf, base)
    os.makedirs(extras, exist_ok=True)
    for p in glob.glob(os.path.join(DELIV, '*')):
        if os.path.isdir(p) and os.path.exists(os.path.join(p, 'clips.md')):
            continue  # another video's folder
        shutil.move(p, os.path.join(extras, os.path.basename(p)))
    mj = os.path.join(ROOT, 'plan', 'music.json')
    if os.path.exists(mj):
        item['music'] = json.load(open(mj, encoding='utf-8')).get('credit')
    notes = os.path.join(extras, 'EDIT_NOTES.md')
    if os.path.exists(notes):
        txt = open(notes, encoding='utf-8').read()
        m = re.search(r'(?is)not verified[^\n]*\n(.*?)(\n#|\Z)', txt)
        if m and m.group(1).strip():
            item['check'] = ' '.join(m.group(1).split())[:400]
    item['archive'] = archive_engine(f"{slug(st['video']['title'], 24)}-{item['id']:02d}-{item['style']}")
    item.update(status='done', output=os.path.relpath(os.path.join(vf, base + '.mp4'), PROJ).replace(os.sep, '/'),
                finished=stamp(now()), sec=round(now() - item.pop('t0', now()), 1))
    save(st)
    write_clips_md(st)
    write_report(st)
    print(f"DONE clip {item['id']} -> {item['output']}  ({item['sec'] / 60:.0f} min)")
    print(next_hint(st))


def cmd_fail():
    st = need_state()
    item = next((c for c in st['queue'] if c['status'] == 'in_progress'), None)
    if not item:
        die('no clip in progress')
    why = sys.argv[2] if len(sys.argv) > 2 else 'failed'
    if item['style'] != 'clip' and engine_dirty():
        item['archive'] = archive_engine(f"{slug(st['video']['title'], 24)}-{item['id']:02d}-{item['style']}-failed")
    item.update(status='failed', note=why, finished=stamp(now()))
    item.pop('t0', None)
    save(st)
    write_clips_md(st); write_report(st)
    print(f"clip {item['id']} marked failed: {why}")
    print(next_hint(st))


# ------------------------------------------------------------------------------------------------ status / docs
def next_hint(st):
    v = st['video']
    q = st.get('queue', [])
    if not v.get('project') and (v['length'] != 'short' or v.get('landscape')
                                 or (st['request'].get('style') == 'clip')):
        return 'NEXT: python work/scripts/eav.py fetch' + ('   (short landscape video: the transcript drives the 9:16 reframe)'
                                                          if v['length'] == 'short' else '')
    if v['length'] != 'short' and not clips_json(st):
        return ('NEXT: read output/%s/transcript/transcript.txt, pick the moments (clip-video skill, references/'
                'picking-moments.md) into output/%s/clips.json, then: python work/scripts/eav.py cut' % (v['project'], v['project']))
    if project_dir(st) and not glob.glob(os.path.join(project_dir(st), 'clips', '*.mp4')):
        return 'NEXT: python work/scripts/eav.py cut'
    if not q:
        return 'NEXT: python work/scripts/eav.py queue   (default: ' + (
            f'the best {DEFAULT_COUNT} in podcast)' if v['length'] != 'short' else 'one reel in talking-head)')
    if any(c['status'] == 'in_progress' for c in q if c['style'] != 'clip'):
        c = next(c for c in q if c['status'] == 'in_progress')
        return (f"IN PROGRESS: clip {c['id']} [{c['style']}]. If this session is still editing it, finish the edit and run "
                f"eav.py done. After an interruption (\"continue\"): python work/scripts/eav.py next (restarts that clip cleanly)")
    if any(c['status'] == 'pending' and c.get('batch', 0) == st.get('batch', 0) for c in q):
        return 'NEXT: python work/scripts/eav.py next'
    if any(c['status'] == 'pending' for c in q):
        return ('Clips are still pending from an earlier request: say "continue" to edit them '
                '(python work/scripts/eav.py next --continue)')
    rest = [c for c in ranked(st) if not any(q_['id'] == int(c['id']) and q_['status'] == 'done' for q_ in q)] if clips_json(st) else []
    return ('ALL DONE. ' + (f'{len(rest)} more moment(s) are listed in clips.md: say "edit the rest" (or "edit clip N in <style>").'
                            if rest and v['length'] != 'short' else ''))


def cmd_status():
    st = need_state()
    v = st['video']
    print(f"video: {v.get('title')}  [{v['kind']}, {v.get('length')}]  project: {v.get('project')}")
    for c in st['queue']:
        print(f"  clip {c['id']:>2} [{c['style']}] {c['status']}" + (f"  -> {c.get('output')}" if c.get('output') else '')
              + (f"  ({c['sec'] / 60:.0f} min)" if c.get('sec') else ''))
    print(next_hint(st))


def write_clips_md(st):
    v = st['video']
    vf = video_folder(st)
    L = [f"# {v.get('title')}", '', f"Source: {v['source']}" + (f"  (channel: {v['channel']})" if v.get('channel') else ''),
         f"Length: {fmt_ts(v['duration'] or 0)}" if v.get('duration') else '', '']
    clips = ranked(st) if clips_json(st) else []
    if v['length'] == 'short' and not clips:
        clips = [{'id': 1, 'title': v['title'], 'hook': '', 'ranges': [[0, v.get('duration') or 0]], 'score': ''}]
    L += ['## Every moment found', '', '| # | Title | Timestamps | Length | Score | Hook line | Edited |', '|---|---|---|---|---|---|---|']
    for c in clips:
        cid = int(c['id'])
        rng = ', '.join(f'{fmt_ts(a)}-{fmt_ts(b)}' for a, b in c.get('ranges', []))
        ln = sum(b - a for a, b in c.get('ranges', []))
        ed = [f"{q['style']}: {q['status']}" + (f" ({os.path.basename(q['output'])})" if q.get('output') else '')
              for q in st['queue'] if q['id'] == cid]
        hook = (c.get('hook') or '').replace('|', '/')
        L.append(f"| {cid} | {c.get('title', '')} | {rng} | {ln:.0f} s | {c.get('score', '')} | {hook} | {'; '.join(ed) or '-'} |")
    rest = [c for c in clips if not any(q['id'] == int(c['id']) and q['status'] == 'done' for q in st['queue'])]
    L += ['', '## Get the rest', '']
    if rest and v['length'] != 'short':
        L += [f"{len(rest)} moment(s) are not edited yet: " + ', '.join(str(c['id']) for c in rest) + '.', '',
              'Open Claude Code in this folder and say one of:', '',
              '- `edit the rest` (podcast style, one at a time; about 10-20 minutes each, so start big batches before bed)',
              '- `edit clip 5 in talking-head` (one moment, any style)',
              '- `edit all of them in clip style` (every moment, the fast look: minutes each)', '',
              'Interrupted? Say `continue`: it picks up at the next unfinished clip.']
    else:
        L += ['Every moment found is edited. Want another look? Say `edit clip N in <style>` (podcast, talking-head, clip).']
    open(os.path.join(vf, 'clips.md'), 'w', encoding='utf-8').write('\n'.join(x for x in L if x is not None) + '\n')


def write_report(st):
    v = st['video']
    vf = video_folder(st)
    L = [f"# Report: {v.get('title')}", '', f"Run started {st.get('created')}. Source: {v['source']}", '', '## Steps', '',
         '| Step | Started | Took |', '|---|---|---|']
    for t in st.get('timings', []):
        L.append(f"| {t['step']} | {t['start']} | {t['sec'] / 60:.1f} min |")
    L += ['', '## Clips', '', '| Clip | Style | Status | Took | File | Music |', '|---|---|---|---|---|---|']
    for c in st['queue']:
        L.append(f"| {c['id']} | {c['style']} | {c['status']}{' (restarted)' if c.get('restarts') else ''} | "
                 f"{(str(round(c['sec'] / 60)) + ' min') if c.get('sec') else '-'}"
                 + (f" (+{round(c['lost_sec'] / 60)} min before an interruption)" if c.get('lost_sec') else '')
                 + f" | {os.path.basename(c.get('output', '')) or '-'} | {c.get('music') or '-'} |")
    checks = [f"- clip {c['id']} [{c['style']}]: {c['check']}" for c in st['queue'] if c.get('check')]
    checks += [f"- clip {c['id']} [{c['style']}] FAILED: {c.get('note')}" for c in st['queue'] if c['status'] == 'failed']
    L += ['', '## Check before posting', '']
    L += checks or ['- Nothing flagged. Watch each reel once on your phone before posting.']
    L += ['', 'Each engine clip keeps its working files in archive/<name>/ (safe to delete once you are happy).',
          'Only post clips of videos you own or have permission to use.']
    open(os.path.join(vf, 'REPORT.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


CMDS = {'start': cmd_start, 'fetch': cmd_fetch, 'cut': cmd_cut, 'queue': cmd_queue, 'next': cmd_next, 'done': cmd_done,
        'fail': cmd_fail, 'status': cmd_status}
if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__); sys.exit(0 if '--help' in sys.argv or '-h' in sys.argv else 1)
    CMDS[sys.argv[1]]()
