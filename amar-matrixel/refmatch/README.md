# refmatch — إعادة بناء المراجع الستة (مطابقة بصرية)

كل مرجع له مجلد. المدخلات: فريمات المرجع @30fps (تُستخرج من تسجيلات المستخدم؛ لا تُرفع للمستودع) ← plate ← طبقة مؤثر ← تركيب ← مقارنة جنباً إلى جنب.
الخطوط من Google Fonts (OFL) وتُجلب بـ `./fetch_fonts.sh` إلى `fonts_tmp/` (غير مرفوعة).
Blender: ‏`bpy` 5.0.1 (PyPI) — على الماك يعمل نفس السكربت داخل Blender ‏5.x: ‏`blender -b -P scene_seq.py -- ...` أو بـ bpy.

| المرجع | المجلد | الأداة | ما هو قابل للتعديل فعلاً |
|---|---|---|---|
| R3 نص حجري | `r3/` | Blender (Cycles) + تركيب OpenCV | `scene_cfg.json`: لكل جملة مستوى النص (من نقاط في الصورة `plane_from_image.py`)، أزمنة التجمّع/الاستقرار/الانفجار، سرعة الشظايا، الغبار (أحداث: زمن، عدد، كثافة، نصف قطر)، الخامة، الشمس. أشكال الحروف: `glyphs/b{1..4}_poly.json` (مضلعات متتبَّعة من المرجع، تُحرَّر نصياً)، الأرقام `digits_skel.py`. النيون: `neon.py` (مفاتيح الظهور/الإطفاء). مشروع Blender لفريم: `blend/r3_f066_text1.blend` (يُولَّد لأي فريم بـ `AMX_SAVE=out.blend`). |
| R4 هولوغرام | `r4/` | Python/OpenCV (رسم إسقاطي من تتبع) + Blender | `r4_cfg.json`: نص المساحة وخطه، أبعاد القطعة، المباني (موضع uv، الارتفاع، الأدوار، الهوائي، زمن النمو)، الألوان، الشدة، `vert_straighten` (نمط الخطوط الرأسية). الكاميرا: `lot_track.json` (تتبع + مفاتيح يدوية `late_keys.py`). مشروع Blender: `blend/r4_hologram.blend` (كاميرا بمفاتيح لكل فريم + مبانٍ Wireframe بمفاتيح ارتفاع، منظور حقيقي بلا تقويم رأسي). |
| R1 نص ذهبي | `r1/` | Blender (نفس `r3/scene_seq.py` بإعداد `r1_cfg.json` + `r1_extras.py`) | النصوص الأربعة (تُولَّد بـ `make_text_shapes.py` بأي خط)، مستويات النص، التوقيت، الذهب (لون/خشونة)، البِرك، الأعمدة السائلة، قطرات الحدود، الدخان، حلقة الختام (`comp1.py`). مشروع Blender: `blend/r1_f075_text1.blend`. |
| R5 خطوط الواجهة | `r5/` | Python/OpenCV (كاميرا ثابتة) + **After Effects JSX** | `r5_cfg.json`: نص كل بطاقة، موضعها، ذيلها، زمن ظهورها، الألوان، الخط. مسارات النيون `neon_paths.json` (متتبَّعة من المرجع). `ae_export/r5_ae_build.jsx`: يبني كومب AE بطبقات Shape للنيون (Trim Paths) + بطاقات Shape + **طبقات نص حية**. |
| R2/R6 | — | — | ⛔ يحتاجان توليد AI (خطة `../plans/R2_R6_ai_plan.md`)؛ لا إنفاق دون موافقة. |

## أوامر المعاينة/الريندر
```bash
# R3: معاينة فريم / تسلسل كامل
cd r3 && ./q.sh <work> 66 tag 50 16          # نصف الدقة 16 عينة
./render_seq.sh <work> <out> 50 10 0 291      # تسلسل كامل (يتخطى الموجود)
# R4
cd r4 && python3 holo.py <work> <out> 0 331 && python3 comp4.py <work> <out> <final> $(seq -s ' ' 0 331)
# R1
cd r1 && ./render1.sh <work> 50 12
# R5
cd r5 && /tmp/bpyenv/bin/python render_r5.py <work> <out> 0 303 && python3 export_ae.py <work> ae_export
```
