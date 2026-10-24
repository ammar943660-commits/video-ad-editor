# طلب توليد — اختبار R3 (النص الحجري) بالذكاء الاصطناعي

**لماذا R3 أولاً وليس R1:** نماذج الفيديو تولّد الحجر الرمادي والغبار والركام بشكل مقنع عادةً. أما الذهب السائل الذي يتشكّل حروفاً فأصعب بكثير. فرص نجاح R3 أعلى.

**الفكرة:** الحروف العربية لا يكتبها النموذج، بل هي موجودة جاهزة في **صورة النهاية**. النموذج يحرّك فقط: خروج الحجر من الأرض، والغبار، والركام. إن شوّه الحروف أثناء الحركة، أركّب طبقة الحروف الصحيحة فوق الفيديو. هذا تركيب ثنائي الأبعاد سريع ممكن لأن الكاميرا ثابتة، ولا يحتاج إلى ريندر طويل.

## المواد (في هذا المجلد)
| الملف | الاستخدام | المصدر |
|---|---|---|
| `01_start_frame_empty_lot_1920x1080.png` | **الإطار الأول** (Start / First frame) | ⚠️ **مأخوذ من فيديو المرجع** (الفريم 0، قبل بدء المؤثر)، كُبّر من 1146×644. للاختبار فقط. في الإعلان الحقيقي تُستبدل بلقطة العقار. |
| `02_end_frame_stone_text_1920x1080.png` | **الإطار الأخير** (End / Last frame) | الخلفية نفسها + نص «ارض للبيع» **مُعاد بناؤه** في Blender: حروف متتبَّعة يدوياً بلا غبار، وكاميرا الفريم 0. |
| `03_motion_reference_sheet.jpg` | للاسترشاد بالحركة فقط، **لا ترفعه كإطار** | لقطات من فيديو المرجع |
| `text_layer_f066_cam0.png` | طبقة الحروف الشفافة للتركيب لاحقاً (لا ترفعها) | إعادة بناء |

## المطلوب توليده: مقطع واحد
- **الأداة:** أي منصة تدعم **الإطار الأول + الإطار الأخير** (مثل Google Flow / Veo «Frames to Video»، أو Kling، أو Runway، أو Luma).
- **المدة:** 4–5 ثوانٍ (إن كانت 8 ثوانٍ هي الحد الأدنى فلا مشكلة، سأقصّها).
- **الأبعاد:** 16:9، ‏1920×1080 أو 1280×720، ‏24 أو 30 fps.
- **الكاميرا:** **ثابتة تماماً** (مهم للتركيب).
- **عدد المحاولات:** 2–3 إن أمكن، لأختار الأفضل.

### البرومبت (الصقه كما هو)
```
Static locked-off aerial drone shot, camera does not move. On the empty sandy lot, massive grey concrete stone blocks burst up out of the ground and assemble into large 3D stone letters standing upright, exactly matching the letters in the last frame. Heavy chunks of rock tumble and settle at the base. Thick bright sunlit dust clouds billow outward from the base of the letters, cauliflower-shaped, white-beige, lit by warm afternoon sun, then slowly drift and thin out. Small debris scattered on the sand. Realistic physics, cinematic, photorealistic, sharp details. Keep the surrounding city, road, cars and buildings unchanged. Do not add any other text, letters, logos or signs.
```

### برومبت سلبي (إن كانت المنصة تدعمه)
```
camera movement, zoom, pan, shaking, extra text, gibberish letters, distorted letters, changing letters, watermark, logo, cartoon, low detail, melting
```

## ما سأفعله عند استلام المقطع
1. أقارنه بالمرجع عند نفس اللحظات، صوراً ثابتة وفيديو جنباً إلى جنب.
2. إن بقيت الحروف سليمة، أستخدمه كما هو. إن تشوّهت، أركّب طبقة الحروف الصحيحة فوق آخر ثانية، وأمزجها مع الغبار المولَّد عبر قناع.
3. أضيف النيون السماوي على حدود القطعة والتعتيم بالتركيب (موجودان وسريعان).
4. إن نجح الاختبار، أجهّز طلبات الجمل الثلاث الأخرى (500 متر، الخبر - حي العقيق، تواصل معنا + الرقم) ثم R1 بالطريقة نفسها.

## ما لا يُعدّ إعادة بناء
- الخلفية في هذا الاختبار من فيديو المرجع.
- الحجر والغبار والحركة في الناتج **مولَّدة بالذكاء الاصطناعي**.
- الحروف وحدها إعادة بناء.
