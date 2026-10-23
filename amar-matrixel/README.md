# AMAR Matrixel — Visual Reconstruction

محرك مستقل لإعادة بناء مؤثرات سينمائية عقارية **مشابهة** لمراجع مرئية تم تحليلها (نص حجري على الأرض، هولوغرام حدود أرض، مخطط نيون لواجهة، حركات كاميرا) — مع **الحفاظ الكامل** على نظام AMAR Video Master: لا ملف أصلي عُدِّل، ولا مهارة حُذفت أو استُبدلت، ولا مؤثرات Film Impact مُسّت. (نسخة احتياطية: وسم git `pre-matrixel-backup` + أرشيف خارج المستودع.)

> **لا ادعاء:** هذا ليس Matrixel ولا نسخة منه ولا نعرف شفرته الداخلية. هو تنفيذ مستقل لنفس الفكرة البصرية، بقواعد صدق أشدّ (لا مساحات مخترعة، لا مباني غير موسومة، لا زوايا مخترعة).

## ماذا بُني
```
amar-matrixel/
  SKILL.md                    المهارة (مستقلة) — نقطة الدخول
  engine/
    render.js stage.html      مُرندر Chrome بلا واجهة → فريمات RGBA + ProRes 4444 + WebM α + preview.mp4
    core.js                   رياضيات الكاميرا (pose↔three) · نص عربي · كنتور→بثق 3D · نيون Glow · إلصاق منظوري
    recipes/
      stone_text.js           A · نص حجري 3D حقيقي + غبار + حطام + ظل + اهتزاز
      land_hologram.js        B · نيون الحدود + مساحة (من المستخدم فقط) + مخطط + Wireframe موسوم
      building_outline.js     C · مسارات نيون للواجهة + بطاقات عربية
      plate_land.js plate_facade.js   مواد اختبار تركيبية بحقيقة أرضية (ليست لقطات حقيقية)
  tools/
    track.py                  تتبع مستوي: SIFT+RANSAC + ECC تزايدي + تصحيح انجراف + تنعيم + حل pose
    detect_edges.py           حواف الواجهة مرة واحدة في الفضاء المعدَّل → edges.json قابل للتعديل
    camera_motion.py          D · Rise / Tilt Up / Push-In / Parallax (+ تثبيت) مع فحص Overscan ورفض
    director.py               Preflight إخراجي · qa.py / qa_camera.py فحص الجودة · sfx.py مؤثرات صوت
    export.py                 premiere.xml · ae_build.jsx · blender_build.py
    amx.py                    منسّق (plate/track/render/qa/matrix)
  direction/director.json     قرارات الإخراج + بوابات الجودة (DIRECTION.md مولَّد منه)
  projects/                   مشاريع قابلة للتعديل (project.json + track.json + edges.json)
  previews/  reports/         معاينات فعلية + تقرير الاختبار الصادق
```

## كيف يعمل (باختصار)
1. **التتبع** يحلّ كاميرا كل فريم (R,t) من 4 زوايا يحدّدها المستخدم → كل المؤثرات تُرسم عبر نفس الكاميرا، فتلتصق بالأرض/الواجهة بمنظور صحيح.
2. **النص الحجري**: خط عربي مُشكَّل من المتصفح ← كنتور (Marching Squares) ← `ExtrudeGeometry` بتشطيف ← خامة حجر إجرائية 3D ← يصعد من تحت مستوى الأرض (قطع بمستوى) مع ظل Shadow-Map حقيقي وظل تماس وغبار حجمي (Sprites) وحطام باليستي.
3. **الواجهة**: الحواف تُكتشف مرة واحدة على الواجهة المعدَّلة وتُتبَّع كإحداثيات (u,v) → لا اهتزاز ولا انزلاق.
4. **الكاميرا**: دوران كاميرا حول مركزها (تحويل منظوري دقيق للصورة الثابتة) + عمق اختياري لـparallax حقيقي؛ بلا عمق تُرفض الزوايا المخترعة.

الحالة الصادقة لكل شيء: `reports/TEST_REPORT.md`.
