# خطة R2 (الساعة الذهبية) وR6 (تعاقب الليل والنهار) — للاعتماد قبل أي إنفاق

> **لا تنفيذ ولا إنفاق الآن.** هذه خطة بالخدمة والبرومبت والتكلفة المتوقعة. تبقى R2 وR6 ضمن المتابعة (`TRACKER.md`) بحالة «بانتظار اعتماد الخطة».

## 1) ما يظهر في المرجعين (من الفريمات الأصلية)
- **R6** (4.25ث، `3fe6907d`): فيلا من واجهة ثابتة تقريباً: **نهار** (سماء زرقاء) ← غيوم وإضاءة دافئة ← **غروب** (سماء برتقالية، ظلال طويلة) ← **ساعة زرقاء** ← **ليل** (نوافذ ومصابيح مضاءة) ← عودة للنهار (حلقة).
- **R2** (9.95ث، `bc7b7c26`): نفس الفكرة بإيقاع أبطأ، بزاوية ومشهد مختلفين: أكثر وضوحاً لتدرج السماء والغيوم وانعكاس الضوء على الواجهة وإضاءة النوافذ.
- الكاميرا **ثابتة**: التحويل كله في الإضاءة (اتجاه الشمس، لون السماء والغيوم، ظلال، إضاءة داخلية للنوافذ، إنارة خارجية).

## 2) ما يحدّده الفحص الحالي (قراءة فقط، بلا إنفاق)
| الخدمة | الحالة على حسابك الآن |
|---|---|
| Magnific `images_relight` (إضاءة صورة بأضواء اتجاهية/ملوّنة) | متاحة؛ التقدير `simulate_cost` = **0 رصيد** (دقة 2k، صورة واحدة) — لكنها تغيّر اتجاه/لون الإضاءة فقط، **لا تبدّل السماء ولا تضيء النوافذ** |
| Magnific `video_relight` | **غير متاحة على الخطة** (تحتاج ترقية) |
| Magnific `video_generate` (كل الموديلات: Seedance/Kling/…) | **تحتاج Premium** — محجوبة |
| Magnific نماذج الصور (Seedream 5 Pro / Flux Kontext / GPT 2.5 …) لتعديل الصورة | **تحتاج Premium** (عدا `auto`) |
| Higgsfield | رصيد 10 مجانية؛ الموصل لا يولّد |
- الرصيد الحالي في Magnific: **0**.

## 3) الخطة الموصى بها (بالذكاء الاصطناعي، بعد اعتمادك)
**الفكرة:** إنشاء 5 لقطات مفتاحية بإضاءات مختلفة لنفس الصورة بتركيب ثابت، ثم تحويلات سلسة بينها، ثم تجميع في Premiere/AE.
1. **المصدر:** صورة/لقطة الفيلا (الفريم الأول من المرجع للاختبار؛ ولاحقاً صورة العميل).
2. **مفاتيح الإضاءة (5 صور بنفس التكوين)** — موديل تعديل صور مع مرجع الصورة الأصلية (مثل Seedream 5 Pro أو Flux Kontext Pro) بالبرومبت التالي (الإنجليزية أدق للموديلات):
   - *Day:* `Same villa, same camera, same composition and architecture. Bright midday sun, clear blue sky with soft white clouds, crisp short shadows, natural colors. Do not change the building, fence, street or perspective.`
   - *Golden hour:* `Same scene, same composition. Low warm sun from the left, golden-orange light on the facade, long soft shadows, sky gradient from pale blue to warm orange with sunlit clouds. Windows still dark. Architecture unchanged.`
   - *Sunset:* `Same scene. Sun at the horizon, deep orange and magenta sky, strong warm rim light on the facade, long dramatic shadows, first interior lights starting to glow in windows. Architecture unchanged.`
   - *Blue hour:* `Same scene. After sunset, deep blue twilight sky with a thin orange glow at the horizon, facade lit softly in cool blue, all windows glowing warm yellow, exterior wall lights and garden lights on. Architecture unchanged.`
   - *Night:* `Same scene at night, dark navy sky with few stars, strongly lit warm windows, wall-wash uplights on the facade, street lamps on, subtle ground reflections. Architecture unchanged.`
3. **التحويلات (4 مقاطع):** `video_generate` بإطار بداية ونهاية (keyframes.start/end) من لقطتين متجاورتين، 4–5 ثوانٍ لكل مقطع، كاميرا ثابتة. برومبت موحّد: `Static camera. Smooth, realistic time-lapse transition of the lighting from the first frame to the last frame. The building and everything else stay perfectly still; only sun position, sky color, clouds, shadows and window lights change.`
4. **التجميع:** قص/تسريع/تدرج في Premiere أو AE؛ تثبيت الإطارات؛ حلقة نهار←نهار لـR2.
5. **R6 (4.25ث):** نفس السلسلة مضغوطة: نهار ← غروب ← ليل ← نهار (صورتا مفتاح إضافيتان فقط + 3 تحويلات قصيرة 1.4ث).

## 4) التكلفة المتوقعة
- **لا أستطيع حسابها بدقة قبل الترقية**: `simulate_cost` يرفض موديلات Premium على الخطة المجانية («الخدمة غير متاحة على خطتك»).
- **بعد الترقية** أشغّل `simulate_cost` لكل نداء (5 صور + 4 تحويلات لـR2؛ 3 صور + 3 تحويلات لـR6) وأعرض لك **الإجمالي بالأرصدة** قبل تنفيذ أي نداء، وأتوقف عند السقف الذي تحدده.
- `images_relight` وحده 0 رصيد، ويمكن استخدامه لمعاينة اتجاه الضوء دون إنفاق **لو وافقت**.

## 5) بديل بلا ذكاء اصطناعي (أضعف بوضوح — لا يُنفَّذ إلا بموافقتك)
تدريج لوني متحرك + استبدال سماء بتدرج/غيوم مُنتَجة + أقنعة يدوية لإضاءة النوافذ والإنارة + توهج. يعطي تحوّل ألوان مقنعاً بصرياً لكن **بلا ظلال ساقطة حقيقية ولا انعكاسات**، وسيبدو أبسط من المرجع.

## 6) قرارات مطلوبة منك (لاحقاً، لا الآن)
1. اعتماد الخطة (الخدمة + البرومبت) أو تعديلها. 2. ترقية الحساب وسقف الأرصدة. 3. الصورة المصدر (من المرجع للاختبار أم صورة عميل).
