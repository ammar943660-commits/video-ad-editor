#!/usr/bin/env python3
"""amx.py — منسّق خط إنتاج AMAR Matrixel.
  amx.py plate   <land|facade> <aspect> <dir> [--duration 4] [--scale .5]   لقطة اختبار تركيبية + Ground Truth
  amx.py track   <dir> [--plane-w M --plane-l M]                           تتبع مستوي لـ <dir>/plate.mp4 من corners في project.json
  amx.py render  <dir> [--scale .5]                                         ريندر الوصفة (+SFX + preview.mp4)
  amx.py qa      <dir> [--gt <plate_dir>]
  amx.py matrix  [--scale .5] [--duration 4] [--aspects 9:16,4:5,16:9]      مصفوفة الاختبار الكاملة (3 نسب × 3 مؤثرات)"""
import sys, os, json, subprocess, random, shutil, argparse, concurrent.futures as cf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(ROOT, 'tools'); E = os.path.join(ROOT, 'engine', 'render.js')
def run(cmd, quiet=True):
    r = subprocess.run(cmd, capture_output=quiet, text=True)
    if r.returncode: print('✗', ' '.join(cmd)[:200], '\n', (r.stdout or '')[-600:], (r.stderr or '')[-1200:]); raise SystemExit(r.returncode)
    return r.stdout
def mk_plate(kind, aspect, d, duration=4, scale=.5, seed=3):
    os.makedirs(d, exist_ok=True)
    json.dump({'recipe': f'plate_{kind}', 'aspect': aspect, 'fps': 30, 'duration': duration, 'params': {}}, open(os.path.join(d, 'project.json'), 'w'))
    run(['node', E, d, '--scale', str(scale), '--workers', '3', '--no-encode'])
    run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(d, 'renders/frames/%05d.jpg'), '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', os.path.join(d, 'plate.mp4')])
    m = json.load(open(os.path.join(d, 'renders/meta.json'))); random.seed(seed)
    c = [[x + random.uniform(-1.5, 1.5), y + random.uniform(-1.5, 1.5)] for x, y in m['frames'][0]['corners']]  # خطأ نقر المستخدم ±1.5px
    p = json.load(open(os.path.join(d, 'project.json'))); p.update({'corners': c, 'fov': m['frames'][0]['fov'], 'plate': 'plate.mp4'}); json.dump(p, open(os.path.join(d, 'project.json'), 'w'), indent=1)
    return m
def track(d, pw=None, pl=None):
    cmd = ['python3', os.path.join(T, 'track.py'), os.path.join(d, 'plate.mp4'), d]
    if pw: cmd += ['--plane-w', str(pw), '--plane-l', str(pl)]
    run(cmd)
def make_project(src_plate, dst, recipe, aspect, params, duration):
    os.makedirs(dst, exist_ok=True)
    for f in ('plate.mp4', 'track.json', 'edges.json'):
        if os.path.exists(os.path.join(src_plate, f)): shutil.copy(os.path.join(src_plate, f), dst)
    json.dump({'recipe': recipe, 'aspect': aspect, 'fps': 30, 'duration': duration, 'plate': 'plate.mp4', 'params': params}, open(os.path.join(dst, 'project.json'), 'w'), ensure_ascii=False, indent=1)
def render(d, scale=.5):
    run(['python3', os.path.join(T, 'sfx.py'), d]); run(['node', E, d, '--scale', str(scale), '--workers', '3'])
def qa(d, gt):
    out = subprocess.run(['python3', os.path.join(T, 'qa.py'), d, '--gt', gt], capture_output=True, text=True); return out.stdout + out.stderr

PARAMS = {
  'stone_text': lambda dur: {'font': 'Tajawal Black', 'material': 'stone', 'sun_dir': [-70, -50, 55], 'beats': [{'lines': ['أرض للبيع'], 't0': .3, 'rise': 1.2, 'hold': 1.2, 'sink': .7, 'size': .8, 'anchor': [0, .05]}]},
  'land_hologram': lambda dur: {'area_m2': 2000, 'area_source': 'حسب بيانات المالك', 'plan': {'approved': True, 'source': 'مخطط المالك', 'footprints': [{'poly': [[.2, .25], [.8, .25], [.8, .75], [.2, .75]]}]},
      'building': {'approved': False, 'boxes': [{'u': .35, 'v': .5, 'du': .22, 'dv': .3, 'floors': 4}, {'u': .62, 'v': .5, 'du': .2, 'dv': .3, 'floors': 6}]},
      'timing': {'outline': [.15, .9], 'fill': [.6, 1.2], 'area': [1.0, 1.5], 'plan': [1.4, 2.0], 'build': [1.9, 3.2], 'badge': [.3, .6]}},
  'building_outline': lambda dur: {'timing': {'outline': [.1, .8], 'major': [.6, 1.8], 'detail': [1.0, 2.4]}, 'cards': [
      {'text': 'فيلا للبيع', 'u': .15, 'v': .13, 'dx': 2, 'dy': -14, 'at': 2.0}, {'text': 'جدة', 'sub': 'حي الشاطئ', 'u': .85, 'v': .12, 'dx': -2, 'dy': -14, 'at': 2.3}, {'text': 'تواصل معنا', 'sub': '٠٥٥ ٠٠٠ ٠٠٠٠', 'u': .55, 'v': .78, 'dx': 0, 'dy': 20, 'at': 2.6}]},
}
def matrix(scale, duration, aspects, outdir):
    jobs = []
    def one(aspect, kind):
        tag = aspect.replace(':', ''); pd = os.path.join(outdir, f'plate_{kind}_{tag}')
        recs = ('stone_text', 'land_hologram') if kind == 'land' else ('building_outline',)
        if all(os.path.exists(os.path.join(outdir, f'{r}_{tag}', 'renders', 'preview.mp4')) for r in recs): return [(os.path.join(outdir, f'{r}_{tag}'), pd) for r in recs]  # استئناف
        m = mk_plate(kind, aspect, pd, duration, scale)
        track(pd, m['plane']['w'], m['plane']['l'])
        if kind == 'facade': run(['python3', os.path.join(T, 'detect_edges.py'), os.path.join(pd, 'plate.mp4'), pd])
        res = []
        for recipe in (('stone_text', 'land_hologram') if kind == 'land' else ('building_outline',)):
            d = os.path.join(outdir, f'{recipe}_{tag}'); make_project(pd, d, recipe, aspect, PARAMS[recipe](duration), duration); render(d, scale); res.append((d, pd))
        return res
    with cf.ThreadPoolExecutor(3) as ex:
        fut = [ex.submit(one, a, k) for a in aspects for k in ('land', 'facade')]; out = []
        for f in fut: out += f.result()
    for d, pd in out: print(qa(d, pd)); 
    return out
def materialize(outdir):
    """ينسخ plate.mp4/track.json/edges.json من مجلدات plate_* إلى مشاريع الوصفات (بعد git clone)."""
    import glob
    for d in sorted(glob.glob(os.path.join(outdir, '*'))):
        b = os.path.basename(d)
        if b.startswith('plate_') or not os.path.exists(os.path.join(d, 'project.json')): continue
        tag = b.rsplit('_', 1)[1]; kind = 'facade' if 'outline' in b else 'land'; src = os.path.join(outdir, f'plate_{kind}_{tag}')
        for f in ('plate.mp4', 'track.json', 'edges.json'):
            if os.path.exists(os.path.join(src, f)): shutil.copy(os.path.join(src, f), d)
        print('✓', b)
def rerender(outdir, scale):
    import glob
    for d in sorted(glob.glob(os.path.join(outdir, '*'))):
        b = os.path.basename(d)
        if b.startswith('plate_') or not os.path.exists(os.path.join(d, 'project.json')): continue
        tag = b.rsplit('_', 1)[1]; kind = 'facade' if b.startswith('building') else 'land'; render(d, scale); print(qa(d, os.path.join(outdir, f'plate_{kind}_{tag}')))
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('rest', nargs='*'); ap.add_argument('--scale', type=float, default=.5); ap.add_argument('--duration', type=float, default=4)
    ap.add_argument('--aspects', default='9:16,4:5,16:9'); ap.add_argument('--out', default=os.path.join(ROOT, 'projects', 'matrix')); ap.add_argument('--gt'); ap.add_argument('--plane-w'); ap.add_argument('--plane-l')
    a = ap.parse_args()
    if a.cmd == 'plate': mk_plate(a.rest[0], a.rest[1], a.rest[2], a.duration, a.scale)
    elif a.cmd == 'track': track(a.rest[0], a.plane_w, a.plane_l)
    elif a.cmd == 'render': render(a.rest[0], a.scale)
    elif a.cmd == 'qa': print(qa(a.rest[0], a.gt))
    elif a.cmd == 'materialize': materialize(a.out)
    elif a.cmd == 'rerender': rerender(a.out, a.scale)
    elif a.cmd == 'matrix': matrix(a.scale, a.duration, a.aspects.split(','), a.out)
