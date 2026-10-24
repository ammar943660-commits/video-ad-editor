#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🖼️ 17_gen_scenes.py — مشاهد مولّدة (v3.2): صور ومقاطع قصيرة يولّدها الذكاء الاصطناعي وتدخل الفيديو كمشاهد، والمحرّك يرسم فوقها.

الاستخدام:
  python3 scripts/17_gen_scenes.py <work> cost      # كم بتكلّف الأصول المطلوبة (بلا توليد)
  python3 scripts/17_gen_scenes.py <work> fetch     # يولّد الناقص فقط → <work>/gen/ ويكتب genFrames بـstudio.json
  python3 scripts/17_gen_scenes.py <work> status    # شنو جاهز وشنو ناقص
  python3 scripts/17_gen_scenes.py <work> request   # (سياسة AMAR) حزمة طلب للتوليد اليدوي بلا أي إنفاق → <work>/ai_requests/REQUEST.md
  python3 scripts/17_gen_scenes.py <work> import <k> <file>   # يدخّل لقطة ولّدها المستخدم يدوياً (صورة أو mp4)
  python3 scripts/17_gen_scenes.py <work> fallback  # رفض/تعذّر التوليد: بديل محلي فوري لكل أصل ناقص (خلفية من المصدر أو تدرّج + حركة كاميرا) — بلا إنترنت

الملف: <work>/gen.json
{
  "assets": [
    {"k":"desk",  "kind":"video", "prompt":"...", "dur":5, "ar":"9:16"},
    {"k":"paper", "kind":"image", "prompt":"...", "ar":"3:4"}
  ],
  "scenes": [ {"s":"w:منو","e":"w:الجواب+","k":"paper","mode":"card","draw":[{"op":"vs","at":"w:ولا","l":"ورقة","r":"الجوال"}]} ]
}
المزوّد: fal.ai — المفتاح من FAL_KEY بالبيئة أو بملف .env (بمجلد الشغل أو المشروع أو البيت).
الموديلات: صورة = fal-ai/nano-banana (≈0.04$) · مقطع = fal-ai/wan-25-preview/text-to-video 720p (≈0.05$/ث).
⛔ يولّد فقط اللي ما هو موجود بمجلد gen/ (ما يعيد ولا يدفع مرتين). لو فشل طلب مرة، يوقف ويقول السبب — ما يكرّر.
"""
import sys, os, json, time, subprocess, urllib.request, urllib.error

IMG_MODEL = "fal-ai/nano-banana"
VID_MODEL = "fal-ai/wan-25-preview/text-to-video"
IMG_COST, VID_COST_PER_S = 0.04, 0.05
NEG = "no women, no people, no readable text, no logos, no watermark"   # قواعد المستخدم: بلا نساء وبلا شعارات مرسومة

def _key(work):
    k = os.environ.get("FAL_KEY")
    for d in (work, os.getcwd(), os.path.expanduser("~")):
        if k: break
        p = os.path.join(d, ".env")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                if line.startswith("FAL_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'"); break
    return k

def _post(url, key, body, timeout=120):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Authorization": "Key " + key, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=timeout))

def _get(url, key, timeout=60):
    r = urllib.request.Request(url, headers={"Authorization": "Key " + key})
    return json.load(urllib.request.urlopen(r, timeout=timeout))

def _dl(url, path):
    urllib.request.urlretrieve(url, path)

def load(work):
    p = os.path.join(work, "gen.json")
    if not os.path.exists(p):
        sys.exit("❌ ما فيه gen.json بمجلد الشغل — اكتبه أولاً (الصيغة بأعلى هذا الملف)")
    return json.load(open(p, encoding="utf-8"))

def _fb(work):
    p = os.path.join(work, "gen", "fallback.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def have(work, a, real=False):
    g = os.path.join(work, "gen")
    if real and a["k"] in _fb(work): return False   # البديل المحلي لا يُعدّ أصلاً مولَّداً

    if a.get("kind") == "video":
        return os.path.exists(os.path.join(g, a["k"] + "_0001.jpg"))
    return os.path.exists(os.path.join(g, a["k"] + ".jpg"))

def cost(assets):
    return sum((VID_COST_PER_S * float(a.get("dur", 5))) if a.get("kind") == "video" else IMG_COST for a in assets)

def frames_of(work, k):
    g = os.path.join(work, "gen"); n = 0
    while os.path.exists(os.path.join(g, "%s_%04d.jpg" % (k, n + 1))): n += 1
    return n

def write_studio(work, cfg):
    """يكتب scenes/genFrames بـstudio.json (يدمج بلا ما يمسح باقي الإعدادات)"""
    sp = os.path.join(work, "studio.json")
    st = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    st["gen"] = cfg.get("scenes", [])
    st["genFrames"] = {a["k"]: frames_of(work, a["k"]) for a in cfg.get("assets", []) if a.get("kind") == "video"}
    json.dump(st, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return st

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    work, cmd = sys.argv[1], sys.argv[2]
    cfg = load(work); assets = cfg.get("assets", [])
    missing = [a for a in assets if not have(work, a, real=(cmd in ("cost", "fetch", "request")))]
    if cmd == "request": return request(work, cfg, missing)
    if cmd == "import": return import_asset(work, cfg, sys.argv[3], sys.argv[4])
    if cmd == "fallback": return fallback(work, cfg, missing)
    if cmd == "cost":
        print("الأصول: %d (ناقص %d) — التكلفة التقديرية للناقص ≈ %.2f دولار" % (len(assets), len(missing), cost(missing)))
        for a in missing: print("  •", a["k"], a.get("kind", "image"), ("%ss" % a.get("dur", 5)) if a.get("kind") == "video" else "", "≈ %.2f$" % (VID_COST_PER_S * float(a.get("dur", 5)) if a.get("kind") == "video" else IMG_COST))
        return
    if cmd == "status":
        for a in assets: print(("🔁 بديل محلي" if a["k"] in _fb(work) else "✅" if have(work, a) else "⏳"), a["k"], a.get("kind", "image"), (("%d فريم" % frames_of(work, a["k"])) if a.get("kind") == "video" and have(work, a) else ""))
        write_studio(work, cfg); print("studio.json ← gen:", len(cfg.get("scenes", [])), "مشهد"); return
    if cmd != "fetch": sys.exit(__doc__)
    key = _key(work)
    if not key: sys.exit("❌ ما فيه مفتاح فال — حط FAL_KEY بالبيئة أو بملف .env")
    g = os.path.join(work, "gen"); os.makedirs(g, exist_ok=True)
    print("🎨 أولّد %d أصل (≈ %.2f دولار)" % (len(missing), cost(missing)))
    for a in missing:
        k, kind, prompt = a["k"], a.get("kind", "image"), a["prompt"].strip() + ", " + NEG
        t0 = time.time()
        fb = _fb(work)
        if k in fb:   # كان بديلاً محلياً: امسح فريماته قبل التوليد الحقيقي
            for old in [x for x in os.listdir(g) if x.startswith(k + "_") or x == k + ".jpg"]: os.remove(os.path.join(g, old))
            fb.pop(k); json.dump(fb, open(os.path.join(g, "fallback.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        try:
            if kind == "video":
                dur = str(int(float(a.get("dur", 5))))
                q = _post("https://queue.fal.run/" + VID_MODEL, key, {"prompt": prompt, "aspect_ratio": a.get("ar", "9:16"), "duration": dur, "resolution": a.get("res", "720p"), "enable_prompt_expansion": False}, 60)
                su, ru = q["status_url"], q["response_url"]
                for _ in range(120):
                    st = _get(su, key).get("status")
                    if st == "COMPLETED": break
                    if st == "FAILED": raise RuntimeError("فشل توليد المقطع " + k)
                    time.sleep(5)
                res = _get(ru, key); url = res["video"]["url"]
                mp4 = os.path.join(g, k + ".mp4"); _dl(url, mp4)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=30", "-q:v", "3", os.path.join(g, k + "_%04d.jpg")], check=True)
                print("  ✅ %s مقطع %s ث → %d فريم (%.0f ث)" % (k, dur, frames_of(work, k), time.time() - t0))
            else:
                res = _post("https://fal.run/" + IMG_MODEL, key, {"prompt": prompt, "num_images": 1, "aspect_ratio": a.get("ar", "3:4"), "output_format": "jpeg"}, 120)
                _dl(res["images"][0]["url"], os.path.join(g, k + ".jpg"))
                print("  ✅ %s صورة (%.0f ث)" % (k, time.time() - t0))
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode("utf-8", "ignore")
            sys.exit("❌ فال رفض طلب «%s»: %s %s\n   (ما أعدت الطلب — شخّص السبب: المفتاح؟ الرصيد؟ المحتوى؟)" % (k, e.code, body))
        except Exception as e:
            sys.exit("❌ توقفت عند «%s»: %s" % (k, str(e)[:200]))
    st = write_studio(work, cfg)
    print("📝 studio.json ← gen: %d مشهد · genFrames: %s" % (len(st["gen"]), st["genFrames"]))

def _scene_of(cfg, k):
    return [x for x in cfg.get("scenes", []) if x.get("k") == k]

def request(work, cfg, missing):
    """حزمة توليد يدوي (سياسة AMAR §2): برومبت + قيود + إعدادات + موضع بالـTimeline + البديل المحلي. لا اتصال ولا إنفاق."""
    d = os.path.join(work, "ai_requests"); os.makedirs(d, exist_ok=True)
    if not missing: print("✅ كل الأصول موجودة — ما فيه طلب"); return
    L = ["# طلب توليد يدوي — %d لقطة" % len(missing), "", "ولّدها بالمنصة اللي تناسبك (Google Flow/Veo، Higgsfield، Kling، Runway…) ثم:",
         "`python3 scripts/17_gen_scenes.py <work> import <k> <الملف>` — وإن ما تيسّر: `... fallback` (بديل محلي فوري).", ""]
    for a in missing:
        v = a.get("kind") == "video"; sc = _scene_of(cfg, a["k"])
        L += ["## %s — %s" % (a["k"], "مقطع فيديو" if v else "صورة"),
              "- **المنصة/الوضع:** %s" % ("Google Flow (Veo) Text/Frames to Video · أو Kling/Higgsfield" if v else "Google Flow (Imagen) · أو Higgsfield/أي مولّد صور"),
              "- **النسبة:** %s%s" % (a.get("ar", "9:16" if v else "3:4"), (" · **المدة:** %s ث (يُقص للحاجة)" % a.get("dur", 5)) if v else ""),
              "- **البرومبت:**", "```", a["prompt"].strip(), "```", "- **القيود السلبية:**", "```", NEG + ", watermark, distorted, extra text", "```",
              "- **موضع بالـTimeline:** " + ("; ".join("من «%s» إلى «%s» (%s)" % (x.get("s"), x.get("e"), x.get("mode", "bg")) for x in sc) or "—"),
              "- **البديل المحلي إن تعذّر:** %s" % ("خلفية من فريم المصدر مضبّبة + حركة كاميرا بطيئة، والرسم فوقها كما هو" if v else "خلفية من فريم المصدر أو تدرّج بألوان الهوية، والرسم فوقها كما هو"), ""]
    p = os.path.join(d, "REQUEST.md"); open(p, "w", encoding="utf-8").write("\n".join(L)); print("📝 حزمة الطلب:", p, "(%d لقطة، بلا أي إنفاق)" % len(missing))

def import_asset(work, cfg, k, f):
    a = next((x for x in cfg.get("assets", []) if x["k"] == k), None)
    if not a: sys.exit("❌ ما فيه أصل باسم " + k)
    g = os.path.join(work, "gen"); os.makedirs(g, exist_ok=True)
    for old in [x for x in os.listdir(g) if x.startswith(k + "_") or x == k + ".jpg"]: os.remove(os.path.join(g, old))
    if a.get("kind") == "video":
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", "fps=30", "-q:v", "3", os.path.join(g, k + "_%04d.jpg")], check=True)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-frames:v", "1", "-q:v", "2", os.path.join(g, k + ".jpg")], check=True)
    fb = _fb(work); fb.pop(k, None); json.dump(fb, open(os.path.join(g, "fallback.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_studio(work, cfg); print("✅ دخلت لقطتك «%s» (%s)" % (k, "%d فريم" % frames_of(work, k) if a.get("kind") == "video" else "صورة"))

def _src_frame(work, out, ar):
    """أفضل خلفية محلية: فريم من فيديو المصدر بمجلد الشغل (مضبّب قليلاً ومقصوص للنسبة)، وإلا تدرّج داكن."""
    w, h = (1080, 1920) if ar == "9:16" else (1080, 1440) if ar == "3:4" else (1920, 1080) if ar == "16:9" else (1080, 1080)
    vids = [os.path.join(work, x) for x in sorted(os.listdir(work)) if x.lower().endswith((".mp4", ".mov", ".m4v"))]
    vf = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,gblur=sigma=6,eq=brightness=-0.08:saturation=0.85" % (w, h, w, h)
    if vids and subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", vids[0], "-frames:v", "1", "-vf", vf, "-q:v", "2", out]).returncode == 0 and os.path.exists(out):
        return "فريم المصدر"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x12161c:s=%dx%d" % (w, h), "-vf", "vignette=PI/4", "-frames:v", "1", "-q:v", "2", out], check=True)
    return "تدرّج داكن"

def fallback(work, cfg, missing):
    """سياسة AMAR §3: رفض/تعذّر التوليد ← بديل محلي فوري بلا إنترنت. الصور: خلفية محلية. المقاطع: نفس الخلفية + حركة زوم/بان بطيئة (فريمات)."""
    if not missing: print("✅ لا أصول ناقصة"); write_studio(work, cfg); return
    g = os.path.join(work, "gen"); os.makedirs(g, exist_ok=True); fb = _fb(work)
    for a in missing:
        k = a["k"]; v = a.get("kind") == "video"; ar = a.get("ar", "9:16" if v else "3:4"); still = os.path.join(g, k + ".jpg" if not v else k + "_still.jpg")
        how = _src_frame(work, still, ar)
        if v:
            n = int(float(a.get("dur", 5)) * 30)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", still, "-vf", "zoompan=z='1+0.08*on/%d':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:fps=30" % (n, n), "-frames:v", str(n), "-q:v", "3", os.path.join(g, k + "_%04d.jpg")], check=True)
        fb[k] = {"source": how, "kind": "video" if v else "image", "note": "بديل محلي — ليس لقطة مولّدة؛ استبدله بـ import متى توفرت اللقطة"}
        print("🔁 %s ← بديل محلي (%s%s)" % (k, how, " + زوم بطيء %d فريم" % frames_of(work, k) if v else ""))
    json.dump(fb, open(os.path.join(g, "fallback.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_studio(work, cfg); print("✅ المشروع يكمل بلا توليد — studio.json محدّث")

if __name__ == "__main__":
    main()
