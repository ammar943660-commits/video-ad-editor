#!/usr/bin/env python3
"""sfx.py — مؤثرات صوت إجرائية (numpy) متزامنة مع جدول كل وصفة. لا مكتبات خارجية ولا كريدت.
  python3 sfx.py <project_dir>      → sfx.json (أحداث قابلة للتعديل) + sfx.wav (48kHz ستيريو)
الأحداث مشتقة من project.json: stone_text (صعود/استقرار/غرق)، land_hologram (رسم/مسح/مبنى)، building_outline (خطوط/بطاقات).
ملاحظة صدق: مؤثرات تركيبية للمعاينة والمرجع الزمني؛ للإنتاج النهائي استبدلها بمكتبة صوت حقيقية (نفس التوقيتات)."""
import sys, json, os, wave
import numpy as np
SR = 48000
rng = np.random.default_rng(7)

def env(n, a=.01, r=.3):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4)); return e
def lp(x, fc):  # one-pole lowpass
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = a * s + (1 - a) * x[i]; y[i] = s
    return y
def lpf(x, fc): return lp(x, fc) if len(x) < 400000 else x
def noise(n): return rng.standard_normal(n)
def bp(x, lo, hi): return lp(x, hi) - lp(x, lo)
def tone(f, n, ph=0): t = np.arange(n) / SR; return np.sin(2 * np.pi * (f if np.isscalar(f) else np.cumsum(f) / SR) * (t if np.isscalar(f) else 1) + ph) if np.isscalar(f) else np.sin(2 * np.pi * np.cumsum(f) / SR + ph)

def ev_rumble(dur, g=.5): n = int(dur * SR); e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5; return g * e * (lp(noise(n), 90) * 9 + .5 * bp(noise(n), 120, 600) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * np.arange(n) / SR)))
def ev_thud(g=.9): n = int(.9 * SR); t = np.arange(n) / SR; return g * (np.sin(2 * np.pi * (48 + 40 * np.exp(-t * 18)) * t) * np.exp(-t * 5) + .5 * lp(noise(n), 400) * 6 * np.exp(-t * 14))
def ev_dust(dur=1.4, g=.35): n = int(dur * SR); e = env(n, .08, .5); return g * e * bp(noise(n), 300, 3500) * 3
def ev_chips(n_hits=14, span=1.0, g=.25):
    n = int((span + .3) * SR); out = np.zeros(n)
    for _ in range(n_hits):
        t0 = int(rng.uniform(0, span) * SR); m = int(.05 * SR); h = bp(noise(m), 1800, 6500) * np.exp(-np.arange(m) / SR * 80); out[t0:t0 + m] += g * h * rng.uniform(.4, 1) * 4
    return out
def ev_zap(dur=.5, g=.3, f0=300, f1=2400):
    n = int(dur * SR); f = np.geomspace(f0, f1, n); return g * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.linspace(0, 1, n)) ** .7
def ev_hum(dur, g=.08): n = int(dur * SR); t = np.arange(n) / SR; return g * np.sin(np.pi * np.linspace(0, 1, n)) * (np.sin(2 * np.pi * 110 * t) + .5 * np.sin(2 * np.pi * 220 * t) + .2 * np.sin(2 * np.pi * 330 * t))
def ev_blip(g=.2, f=1800): n = int(.12 * SR); t = np.arange(n) / SR; return g * np.sin(2 * np.pi * f * t) * np.exp(-t * 35)
def ev_whoosh(dur, g=.35, up=True):
    n = int(dur * SR); x = noise(n); e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6; fc = np.geomspace(300, 5000, n) if up else np.geomspace(5000, 300, n)
    y = np.empty(n); s1 = s2 = 0.0
    for i in range(n): a = np.exp(-2 * np.pi * fc[i] / SR); s1 = a * s1 + (1 - a) * x[i]; s2 = a * s2 + (1 - a) * s1; y[i] = s2
    return g * e * y * 8
def ev_riser(dur, g=.25): n = int(dur * SR); t = np.arange(n) / SR; f = np.geomspace(110, 880, n); return g * np.linspace(0, 1, n) ** 2 * np.sin(2 * np.pi * np.cumsum(f) / SR)

def events_for(proj):
    r, P = proj['recipe'], proj.get('params', {}); ev = []
    if r == 'stone_text':
        for b in P.get('beats', [{'t0': .35, 'rise': 1.5, 'hold': 1.6, 'sink': .9}]):
            t0, rs, hd, sk = b.get('t0', .35), b.get('rise', 1.5), b.get('hold', 1.6), b.get('sink', .9)
            ev += [{'type': 'rumble', 'at': t0, 'dur': rs + .2, 'gain': .5}, {'type': 'chips', 'at': t0 + .1, 'span': rs, 'gain': .25}, {'type': 'thud', 'at': t0 + rs, 'gain': .9}, {'type': 'dust', 'at': t0 + rs - .1, 'dur': 1.5, 'gain': .35}, {'type': 'rumble', 'at': t0 + rs + hd, 'dur': sk, 'gain': .4}, {'type': 'dust', 'at': t0 + rs + hd, 'dur': 1.2, 'gain': .3}]
    elif r == 'land_hologram':
        T = {'outline': [.15, 1.35], 'fill': [.9, 1.8], 'area': [1.7, 2.3], 'plan': [2.4, 3.3], 'build': [3.4, 5.0], **P.get('timing', {})}
        ev += [{'type': 'zap', 'at': T['outline'][0], 'dur': T['outline'][1] - T['outline'][0], 'gain': .22}, {'type': 'hum', 'at': T['outline'][0], 'dur': proj.get('duration', 5) - T['outline'][0], 'gain': .07},
               {'type': 'blip', 'at': T['outline'][1], 'gain': .25}, {'type': 'whoosh', 'at': T['fill'][0], 'dur': T['fill'][1] - T['fill'][0], 'gain': .2}]
        if P.get('area_m2'): ev.append({'type': 'blip', 'at': T['area'][0], 'gain': .3, 'f': 2600})
        if P.get('plan'): ev.append({'type': 'zap', 'at': T['plan'][0], 'dur': .5, 'gain': .18, 'f0': 500, 'f1': 3000})
        if P.get('building'):
            nb = len(P['building']['boxes']); ev.append({'type': 'riser', 'at': T['build'][0], 'dur': T['build'][1] - T['build'][0], 'gain': .22})
            ev += [{'type': 'blip', 'at': T['build'][0] + k * (T['build'][1] - T['build'][0]) / max(1, nb), 'gain': .22, 'f': 1400 + 300 * k} for k in range(nb)]
    elif r == 'building_outline':
        T = {'outline': [.1, 1.0], 'major': [.8, 2.4], 'detail': [1.5, 3.1], **P.get('timing', {})}
        ev += [{'type': 'zap', 'at': T['outline'][0], 'dur': .9, 'gain': .22}, {'type': 'whoosh', 'at': T['major'][0], 'dur': T['major'][1] - T['major'][0], 'gain': .22}, {'type': 'hum', 'at': .1, 'dur': proj.get('duration', 4), 'gain': .06}]
        ev += [{'type': 'blip', 'at': T['detail'][0] + k * (T['detail'][1] - T['detail'][0]) / 8, 'gain': .12, 'f': 2200 + 120 * (k % 4)} for k in range(8)]
        ev += [{'type': 'blip', 'at': 2.6 + k * .35, 'gain': .3, 'f': 1500} for k in range(len(P.get('cards', [])))]
    elif r == 'camera_motion':
        d = proj.get('duration', 4); ev += [{'type': 'whoosh', 'at': .2, 'dur': d - .4, 'gain': .22, 'up': proj.get('mode') != 'tilt'}, {'type': 'riser', 'at': .3, 'dur': d - .6, 'gain': .12}]
    return ev

def render(ev, dur):
    n = int(dur * SR) + SR; L = np.zeros(n); Rr = np.zeros(n)
    for e in ev:
        t = e['type']; g = e.get('gain', .3); d = e.get('dur', 1.0)
        x = {'rumble': lambda: ev_rumble(d, g), 'thud': lambda: ev_thud(g), 'dust': lambda: ev_dust(d, g), 'chips': lambda: ev_chips(14, e.get('span', 1), g), 'zap': lambda: ev_zap(d, g, e.get('f0', 300), e.get('f1', 2400)),
             'hum': lambda: ev_hum(d, g), 'blip': lambda: ev_blip(g, e.get('f', 1800)), 'whoosh': lambda: ev_whoosh(d, g, e.get('up', True)), 'riser': lambda: ev_riser(d, g)}[t]()
        i = int(e['at'] * SR); x = x[:max(0, n - i)]; pan = e.get('pan', 0.0); L[i:i + len(x)] += x * (1 - max(0, pan)); Rr[i:i + len(x)] += x * (1 + min(0, pan))
    m = max(np.abs(L).max(), np.abs(Rr).max(), 1e-6); k = .7 / m; return np.stack([L * k, Rr * k], 1)

def main():
    proj_dir = sys.argv[1]; proj = json.load(open(os.path.join(proj_dir, 'project.json'))); sj = os.path.join(proj_dir, 'sfx.json')
    ev = json.load(open(sj)) if os.path.exists(sj) and '--regen' not in sys.argv else events_for(proj)
    json.dump(ev, open(sj, 'w'), indent=1, ensure_ascii=False)
    dur = proj.get('duration', 4); y = render(ev, dur)[:int(dur * SR)]
    w = wave.open(os.path.join(proj_dir, 'sfx.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes()); w.close()
    print(f'✓ sfx.json ({len(ev)} events) + sfx.wav ({dur}s)')
if __name__ == '__main__': main()
