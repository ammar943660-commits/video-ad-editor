# AMAR Video Master — حالة المشروع (ملف الاستئناف الدائم)

**آخر تحديث:** 24 أكتوبر 2026. أُغلقت مرحلة تطوير ومطابقة مؤثرات AMAR Matrixel.
**الفرع:** `claude/matrixel-visual-reconstruction-ksc576` في `ammar943660-commits/video-ad-editor`.
- ⛔ لا دمج لـPR #1، ولا تعديل لـ`main`، إلا بموافقة المستخدم.
- **النسخة الاحتياطية النهائية:** الوسم المحلي `amar-matrixel-final-2026-10-24` + commit الإغلاق على الفرع. التفاصيل في §8.

> **ابدأ كل جلسة بقراءة هذا الملف، ثم `video-ad-editor/references/production-policy.md`.**

---

## 1) ما أُنجز واعتُمد
| المؤثر | الحالة | الأسلوب المعتمد | النسخة النهائية |
|---|---|---|---|
| **R3 النص الحجري** | ✅ معتمد | AI (Google Flow/Veo، Frames to Video) + تركيب محلي سريع (`comp_ai.py`) | `amar-matrixel/refmatch/final/R3_AI_vertical_comp_v1_1080x1920.mp4` |
| R3 (ريندر حجمي قديم) | 🗄️ أرشيف ومرجع فقط | Blender حجمي، 3–5 ساعات، **لا يُستخدم للإنتاج** | `final/ARCHIVE_R3_volumetric_render_v2_1146x644.mp4` |
| **R4 هولوغرام الأرض** | ✅ معتمد v2.1 (التحسينات متوقفة) | رسم إسقاطي من تتبع القطعة، أي عقار، حوالي دقيقة | `final/R4_v2.1_hologram_final_1146x644.mp4` + `final/R4_v2.1_hologram_LAYER_on_black_screen-blend.mp4` |
| **R5 خطوط الواجهة والبطاقات** | ✅ معتمد v2 (التحسينات متوقفة) | تركيب ثنائي الأبعاد، كاميرا ثابتة، أقل من دقيقة + JSX لـAE | `final/R5_v2_facade_outline_final_1146x644.mp4` |
| R1 النص الذهبي | 🧊 منجز، **التطوير مجمّد** | Blender | `final/FROZEN_R1_gold_text_v1_1146x644.mp4` |
| R2/R6 ليل↔نهار | ⏸️ مؤجَّل، لا عمل دون طلب جديد | (خطة AI) | `amar-matrixel/plans/R2_R6_ai_plan.md` |

⛔ **لا جولات مطابقة جديدة مع الفيديوهات المرجعية.**

## 2) أماكن الملفات
| الغرض | المسار |
|---|---|
| النسخ النهائية المعتمدة | `amar-matrixel/refmatch/final/` |
| دليل الاستخدام لكل مؤثر | `amar-matrixel/refmatch/USAGE.md` |
| فيديوهات المقارنة مع المرجع وصورها | `amar-matrixel/refmatch/previews/` (v1، v2، واختبارات العقار الجديد) |
| مواد اختبار AI لـR3 (صور البداية والنهاية، البرومبت، النتائج) | `amar-matrixel/refmatch/ai_test_r3/` (`REQUEST.md`، `v_01/v_02` للطول، `01/02` للعرض، `results/`) |
| السكربتات والإعدادات | `amar-matrixel/refmatch/r3` · `r4` · `r5` · `r1` (+ `bl_common.py`، `glyphs.py`) |
| بيانات العمل (تتبّع، أشكال الحروف، النيون) | `amar-matrixel/refmatch/workdata/` |
| مشاريع Blender | `r3/blend/r3_f066_text1.blend` · `r4/blend/r4_hologram.blend` · `r1/blend/r1_f075_text1.blend` |
| After Effects | `r5/ae_export/r5_ae_build.jsx`. صياغته سليمة، **لم يُشغَّل داخل AE**. الصور: `python3 r5/export_ae.py` |
| Premiere | **لا يوجد ملف مشروع Premiere مُختبر.** خطوات التركيب في `USAGE.md`، و`amar-matrixel/tools/export.py` من v1 يولّد `premiere.xml` و`ae_build.jsx` و`blender_build.py` لمشاريع الوصفات (غير مختبر داخل البرامج) |
| سجل المتابعة التفصيلي | `amar-matrixel/TRACKER.md` |
| النسخ الاحتياطية السابقة | `_backup/` (bundles و ZIP لـv1) + الوسوم المحلية `pre-matrixel-backup`، `pre-visual-match-phase`، `pre-fix-round2` |

ملاحظات:
- الخطوط تُجلب بـ`amar-matrixel/refmatch/fetch_fonts.sh` (OFL، غير مرفوعة).
- فريمات المرجع والـplates الكبيرة مشتقة من تسجيلات المستخدم، فلا تُرفع. تُعاد بالأوامر في `refmatch/README.md`.
- في `r3/scene_cfg.json` و`r1/r1_cfg.json` حقول `shapes`/`pieces` مسارات مطلقة لمجلد عمل مؤقت. النسخ الدائمة في `workdata/`، فعدّل المسار عند إعادة الاستخدام.

## 3) حالة السكلات السبع
| السكل | المجلد | يحيل لسياسة الإنتاج |
|---|---|---|
| ريل الكلام | `video-ad-editor/` | ✅ (السطر 8) |
| الموشن | `motion-video/` | ✅ |
| البودكاست | `podcast-video/` | ✅ |
| المونتاج | `montage-video/` | ✅ |
| الكفر والثمبنيل | `thumbnail-video/` | ✅ |
| دافنشي | `davinci-video/` | ✅ |
| AMAR Matrixel | `amar-matrixel/` | ✅ |

- `video-ad-editor/references/start.md` و`CLAUDE.md` يحيلان للسياسة.
- لم يُحذف ولم يُعطَّل أي سكل. كل الإضافات سطور إحالة.

## 4) سياسة AI والبديل المحلي (ملخص — المصدر: `video-ad-editor/references/production-policy.md`)
- **AI خيار إضافي وليس شرطاً.** لأي لقطة: حزمة طلب كاملة (صور كمرفقات، برومبت وقيود، منصة ومدة وأبعاد، موضع في الـTimeline). **المستخدم يولّد يدوياً.** لا إنفاق ولا كريدت من طرف Claude.
- **رفض أو تعذّر ← بديل محلي تلقائياً دون توقف.** مختبر في `video-ad-editor/scripts/17_gen_scenes.py`:
  - `request`: حزمة طلب.
  - `import`: إدخال لقطة المستخدم.
  - `fallback`: بديل محلي بلا إنترنت.
- لا ريندر بالساعات. مراعاة الإنترنت الضعيف (سوريا). لا تغيير للمنتج أو المبنى. المولّد الذي يغيّر الواقع = «تصوّري».
- **حماية التحديث:** `video-ad-editor/scripts/00_setup.sh --update` يرفض التحديث من المستودع الأصلي (majedphotos)، لأنه يحذف الإضافات بـ`rsync --delete`. التحديث فقط بـ`--force-upstream` بعد نسخة احتياطية.

## 5) تشغيل المؤثرات (التفاصيل في `amar-matrixel/refmatch/USAGE.md`)
```bash
# R3 (AI): صورة بداية + صورة نهاية بالحروف ← Google Flow ← ثم:
python3 amar-matrixel/refmatch/ai_test_r3/comp_ai.py <ai_clip.mp4> <out.mp4> [cfg.json]
# R4: عقار جديد
python3 amar-matrixel/refmatch/r4/reuse_new_property.py plate.mp4 <work> '<quad>' [track.json]
R4CFG=<work>/cfg.json /tmp/bpyenv/bin/python amar-matrixel/refmatch/r4/holo.py <work> <work>/holo 0 <n-1>
# R5: واجهة جديدة
python3 amar-matrixel/refmatch/r5/reuse_new_property.py facade.png edges.json '<quad>' <work> --texts "..."
R5CFG=<work>/r5_cfg_newprop.json /tmp/bpyenv/bin/python amar-matrixel/refmatch/r5/render_r5.py <work> <work>/final 0 303
```
- **المتطلبات:** Python 3 + OpenCV + numpy + scipy + scikit-image + ffmpeg.
- **bpy (Blender 5.x):** لـuharfbuzz وshapely، وهما مثبتان داخل bpyenv. على الماك يُستخدم Blender أو بيئة Python مماثلة.

## 6) المؤجَّل
- R2/R6، وتطوير R1، وأي مطابقة جديدة مع المراجع.
- جمل R3 الثلاث الباقية بأسلوب AI («500 متر»، «الخبر - حي العقيق»، «تواصل معنا» + الرقم). تُجهَّز عند مشروع حقيقي.

## 7) مشاكل وقيود معروفة
- **R3 (AI):**
  - الغبار قد يرتفع أكثر من المطلوب.
  - النيون فوق الغبار.
  - صورة الاختبار من المرجع، والسماء ممدودة.
- **R4:**
  - المباني أبسط من المرجع.
  - الكاميرا المحجوبة طويلاً تحتاج مفاتيح يدوية.
  - زاوية الرؤية (FOV) يجب أن تكون أفقية في الإعداد.
- **R5:**
  - كاميرا ثابتة فقط.
  - الخطوط الآلية تحتاج تنظيفاً.
  - الليل بدون صورة حقيقية = تقريب محلي.
- **مأخوذ من المرجع (للمطابقة فقط، لا يدخل إعلان عميل):**
  - خلفية R4 المرجعية.
  - صورتا نهار/ليل R5 المرجعية.
  - صورة بداية اختبار R3.
- **الوسوم:** دفعها إلى GitHub يُرفض من الحاوية. الوسوم محلية فقط، والفرع هو النسخة الدائمة.
- **Premiere وAfter Effects:** لا تكامل مُختبر داخل البرنامج.

## 8) النسخ الاحتياطية
- **commit الإغلاق** على الفرع (اسمه يبدأ بـ «AMAR Matrixel FINAL»).
- **الوسم المحلي:** `amar-matrixel-final-2026-10-24`.
- **السابقة:** `pre-fix-round2`، `pre-visual-match-phase`، `pre-matrixel-backup`، و`_backup/*.bundle`.

## 9) التثبيت على الماك (سكربتات جاهزة في `amar-matrixel/mac/` — لم تُشغَّل على الماك بعد)
1. **استنساخ منفصل** لا يلمس أي شيء منصّب:
   `git clone -b claude/matrixel-visual-reconstruction-ksc576 https://github.com/ammar943660-commits/video-ad-editor ~/AMAR/video-ad-editor_4215ca7`
2. **الفحص + النسخة الاحتياطية + الاختبارات** (قراءة فقط):
   `bash ~/AMAR/video-ad-editor_4215ca7/amar-matrixel/mac/preflight.sh`
   - يكتب تقريراً في `~/AMAR/reports/`، ونسخة احتياطية في `~/AMAR_BACKUPS/<ts>/`.
   - يتحقق أن المحتوى هو النسخة المعتمدة 4215ca7. أي فرق بعدها محصور في ملفات التثبيت.
3. **عرض التفعيل بلا تنفيذ:** `bash …/amar-matrixel/mac/activate.sh`.
4. **التفعيل بعد موافقة المستخدم فقط:** `bash …/amar-matrixel/mac/activate.sh --apply`.
   - السكلات الحالية تُنقل ولا تُحذف، ثم تُربط بالنسخة الجديدة برابط رمزي.
   - plugin `majed-video` يُعطَّل فقط ولا يُلغى تثبيته.
5. **الرجوع:** `bash …/amar-matrixel/mac/rollback.sh ~/AMAR_BACKUPS/activate_<ts>`.
6. **ممنوع:** لا `00_setup.sh --update`، ولا تحديث plugin من `majedphotos`.

## 10) الخطوة التالية عند بدء مشروع جديد
1. اقرأ هذا الملف + `production-policy.md` + `USAGE.md` للمؤثر المطلوب.
2. حلّل مواد العميل، وحدّد اللقطات الناقصة، واختر المؤثرات (R3/R4/R5 أو سكلات المونتاج الأخرى).
3. لأي لقطة AI: جهّز حزمة الطلب، وكمّل باقي المونتاج بالتوازي. عند الرفض انتقل للبديل المحلي.
4. أخرج معاينة للاعتماد قبل النسخة النهائية للعميل.
