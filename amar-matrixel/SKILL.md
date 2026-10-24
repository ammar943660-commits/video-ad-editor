---
name: amar-matrixel
description: AMAR Matrixel Visual Reconstruction — محرك مستقل لإعادة بناء مؤثرات سينمائية عقارية (نص حجري ثلاثي الأبعاد على الأرض، هولوغرام حدود أرض، مخطط نيون لواجهة مبنى، حركات كاميرا سينمائية) كطبقات RGBA وملفات مشروع قابلة للتعديل. Use when user says "نص حجري على الأرض"، "هولوغرام الأرض"، "حدود الأرض نيون"، "مخطط نيون للمبنى"، "Matrixel"، "Stone Text"، "Land Hologram"، "Building Outline"، "Camera Rise"، "Tilt Up"، "Push-In"، "Parallax". لا يستبدل مهارات AMAR Video Master ولا مؤثرات Film Impact.
---

# AMAR Matrixel — مكتبة مؤثرات عقارية سينمائية

> 🎬 **سياسة الإنتاج الدائمة (AMAR Video Master):** اقرأ `${CLAUDE_SKILL_DIR}/../video-ad-editor/references/production-policy.md` أول كل مهمة جديدة — AI خيار لا شرط، حزمة طلب توليد جاهزة، بديل محلي تلقائي إن لم يتوفر AI، لا ريندر بالساعات، لا إنفاق دون موافقة، ودقة المواد الأصلية.

**المجلد:** `${CLAUDE_SKILL_DIR}` (= `amar-matrixel/`). **مستقل تماماً** عن `video-ad-editor/` وباقي المهارات: لا يعدّل ولا يستبدل شيئاً منها (يقرأ فقط three.js والخطوط العربية من `video-ad-editor/motion/`).

> ⛔ **لا تدّعِ تطابقاً مع Matrixel ولا معرفة شفرته الداخلية.** هذه إعادة بناء مستقلة مستوحاة من مراجع مرئية. قل للمستخدم ذلك إن سأل.
> ⛔ **لا تبدأ إعلان عميل نهائياً قبل اعتماد المعاينات.** كل مؤثر يمر: Preflight ← معاينة ← QA ← اعتماد المستخدم.
> ⛔ **لا كريدت مدفوع (Magnific/Higgsfield/…) دون موافقة صريحة.** المحرك كله محلي ومجاني؛ الـAI مطلوب فقط لخريطة depth أو توليد زوايا (اسأل أولاً مع تقدير التكلفة).

## الأدوار (قاعدة المشروع)
| البرنامج | دوره | في هذه المكتبة |
|---|---|---|
| **Premiere Pro** | مركز المونتاج والتصدير | `export/premiere.xml` (V1 لقطة، V2 طبقة RGBA، A1 صوت) |
| **After Effects** | Tracking · Compositing · موشن | `export/ae_build.jsx` (كومب + Nulls تتبع + Corner Pin + نص عربي قابل للتعديل) |
| **Blender** | مجسمات · نص 3D · خامات · جزيئات | `export/blender_build.py` (كاميرا من التتبع + نص 3D + خامة حجر + Shadow Catcher) |
| **المحرك المحلي** | معاينة/إنتاج فعلي بلا برامج | Chrome+three.js+OpenCV: طبقات RGBA + ProRes 4444 + WebM α |

## الوصفات الأربع
| الوصفة | الملف | مدخلات | مخرجات |
|---|---|---|---|
| **A · STONE_TEXT_REVEAL** | `engine/recipes/stone_text.js` | نص عربي `beats[].lines`، لقطة أرض + `track.json` | نص حجري 3D حقيقي (بثق كنتور الخط) يصعد من مستوى الأرض + غبار + حطام + ظل تماس + اهتزاز استقرار |
| **B · LAND_HOLOGRAM_SEQUENCE** | `engine/recipes/land_hologram.js` | 4 نقاط حدود، `area_m2` (اختياري)، `plan`، `building` | Neon Outline + مسح + مساحة على الأرض + مخطط + Wireframe |
| **C · DIGITAL_BUILDING_OUTLINE** | `engine/recipes/building_outline.js` | لقطة واجهة + `edges.json` + `cards` | مسارات نيون متتابعة + بطاقات عربية متتبعة |
| **D · CINEMATIC_CAMERA_MOTION** | `tools/camera_motion.py` | فيديو أو صورة (+depth اختياري) | Rise / Tilt Up / Push-In / Parallax بنسب 9:16 · 4:5 · 16:9 |

## سير العمل
```bash
cd ${CLAUDE_SKILL_DIR} && npm i            # مرة واحدة (puppeteer-core)
pip install opencv-python-headless numpy   # مرة واحدة (+ tesseract-ocr-ara لفحص الوضوح)

# 1) اللقطة + تتبع (النقاط الأربع: project.json ▸ corners، بترتيب TL,TR,BR,BL على الفريم الأول)
python3 tools/track.py plate.mp4 projects/my_ad --fov 60 --plane-w 50 --plane-l 40   # الأبعاد الحقيقية من المستخدم فقط
python3 tools/detect_edges.py plate.mp4 projects/my_ad                               # للواجهات فقط → edges.json (قابل للتعديل)
# 2) فحص إخراجي مسبق
python3 tools/director.py projects/my_ad
# 3) صوت + ريندر (+preview.mp4)
python3 tools/sfx.py projects/my_ad && node engine/render.js projects/my_ad --scale 0.5
# 4) جودة (يطبّق بوابات direction/director.json)
python3 tools/qa.py projects/my_ad [--gt <plate_dir>]
# 5) تصدير ملفات قابلة للتعديل
python3 tools/export.py projects/my_ad
# كاميرا
python3 tools/camera_motion.py still.jpg out.mp4 --mode rise --aspect 9:16 [--depth depth.png]
```
المخرجات في `projects/<name>/renders/`: `frames/*.png` (RGBA) · `overlay.mov` (ProRes 4444+α) · `overlay.webm` (VP9+α) · `preview.mp4` · `frame-log.json` · `meta.json`.

## اختبار كامل وإعادة التوليد
```bash
python3 tools/amx.py matrix --scale 0.5          # لقطات تركيبية + تتبع + 3 مؤثرات × 3 نسب + QA (≈15 دقيقة على 4 أنوية)
python3 tools/qa_camera.py                        # مجموعة D كاملة
python3 tests/reuse_and_policy.py                 # إعادة الاستخدام + اختبارات رفض قواعد الصدق
python3 tools/make_report.py                      # reports/TEST_REPORT.auto.md + معاينات
python3 tools/amx.py materialize                  # بعد git clone: ينسخ plate/track إلى مشاريع الوصفات
```

## قواعد الصدق (تُفرض بالكود)
1. **المساحة**: تظهر فقط لو أدخلها المستخدم `area_m2` — لا تُحسب من الصورة أبداً. بدون `--plane-w/--plane-l` تبقى أبعاد المستوى «نسبية».
2. **المخطط المعماري**: يظهر فقط مع `plan.approved=true`.
3. **المبنى Wireframe**: `building.approved` إلزامي. `true` يتطلب `source` (مرجع النموذج المعتمد). `false` ← شارة «تصور مبدئي — غير معتمد» ثابتة طوال المشهد.
4. **الصور الثابتة**: لا زوايا مخترعة. `parallax` بلا depth **يُرفض**؛ `rise`/`push` بلا depth تُوسم «محاكاة» (دوران/Zoom رقمي). مصدر لا يكفي حركته ← **رفض** (Overscan > 1.35×).
5. **الواجهات**: مستوى واحد. المباني متعددة الأسطح تحتاج تتبع سطح لكل واجهة (غير منفذ بعد).

## قرارات الإخراج
`direction/director.json` يحدد لكل مؤثر: أفضل مشهد، المدة، الكاميرا/العدسة/المنظور، الإضاءة والظلال، الحركة والتسارع، الصوت، الدمج مع المجاور، وبوابات الجودة وشروط الرفض. `direction/DIRECTION.md` نسخة مقروءة.

## الحالة الصادقة
اقرأ `reports/TEST_REPORT.md` — يصنف كل شيء: **مختبر وناجح** / **منفذ ويحتاج تصحيحاً** / **غير منفذ**، وما لم يُختبر لغياب Premiere/AE/Blender وغياب لقطات حقيقية.
