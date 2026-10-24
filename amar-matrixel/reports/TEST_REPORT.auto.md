# تقرير الاختبار — AMAR Matrixel

> مولَّد تلقائياً بـ `tools/make_report.py` — 2026-10-23

## 1) نتائج QA الآلي لكل مؤثر × نسبة (مواد اختبار تركيبية بحقيقة أرضية)

| المؤثر | النسبة | الحكم | فحوص فاشلة | ملاحظات |
|---|---|---|---|---|
| STONE_TEXT_REVEAL | 9:16 | **pass** | — |  |
| LAND_HOLOGRAM_SEQUENCE | 9:16 | **pass** | — |  |
| DIGITAL_BUILDING_OUTLINE | 9:16 | **pass** | — |  |
| STONE_TEXT_REVEAL | 4:5 | **pass** | — |  |
| LAND_HOLOGRAM_SEQUENCE | 4:5 | **pass** | — |  |
| DIGITAL_BUILDING_OUTLINE | 4:5 | **pass** | — |  |
| STONE_TEXT_REVEAL | 16:9 | **pass** | — |  |
| LAND_HOLOGRAM_SEQUENCE | 16:9 | **pass** | — |  |
| DIGITAL_BUILDING_OUTLINE | 16:9 | **pass** | — |  |

## 2) تفاصيل القياسات


### stone_text_916 — STONE_TEXT_REVEAL 9:16 (540×960)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 540×960 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.2916 % of W | max 0.5 | pass | متوسط 1.57px — أقصى 2.51px |
| track_err_max_pct | 0.4657 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0104 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.056px |
| track_drift_px | 0.5932 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| ocr_silhouette[أرض للبيع] | 0.5333  | max None | info | OCR «رضللادة» |
| ocr_composite[أرض للبيع] | 0.3333  | max None | info | OCR «لاسي» |
| ocr_rectified[أرض للبيع] | 0.4286  | max None | info | OCR «ايضليه» (الشكل بعد إزالة المنظور) |
| ocr_similarity | 0.5333  | min 0.5 | pass | أسوأ beat: أعلى تشابه OCR بين (ظلّية، مركّب، معدّل المنظور) |
| text_height_pct | 6.98 % of H | min 3.5 | pass | ارتفاع النص على الشاشة وقت الثبات |
| stroke_rel_pct | 2.8894 % of W | min 0.45 | pass | سمك الخط التقديري |
| floating_alpha_pct | 0 % | max 1.5 | pass | أسوأ نسبة ألفا خارج الحجم المسموح (نص+غبار+حطام) |
| shadow_present | 7287 px | max None | info | بكسلات الظل شبه الشفافة الداكنة |
| perspective_err_pct | 0.2733 % of W | max 0.8 | pass | متوسط 1.48px أقصى 2.99px |
| contact_err_pct | 0.0969 % of W | max 1.5 | pass | متوسط 0.52px أقصى 0.68px |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 9:16: x 5%-95%, y 6%-82% |

### land_hologram_916 — LAND_HOLOGRAM_SEQUENCE 9:16 (540×960)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 540×960 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.2916 % of W | max 0.5 | pass | متوسط 1.57px — أقصى 2.51px |
| track_err_max_pct | 0.4657 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0104 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.056px |
| track_drift_px | 0.5932 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| policy_violations | 0  | max 0 | pass | قواعد الصدق: المساحة/المخطط/المبنى المعتمد — سليمة |
| outline_to_gt_pct | 0.4243 % of W | max 0.7 | pass | الخط المرسوم مقابل حدود الأرض الحقيقية: 2.29px |
| perspective_err_pct | 0.3288 % of W | max 0.8 | pass | متوسط 1.78px أقصى 3.50px |
| ocr_similarity | 0.8889  | min 0.5 | pass | قراءة المساحة بعد إزالة المنظور: «|2000م» (المتوقع 2000) |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 9:16: x 5%-95%, y 6%-82% |

### building_outline_916 — DIGITAL_BUILDING_OUTLINE 9:16 (540×960)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 540×960 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.3871 % of W | max 0.5 | pass | متوسط 2.09px — أقصى 8.09px |
| track_err_max_pct | 1.4985 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0246 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.133px |
| track_drift_px | 1.3888 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| line_slip_pct | 0.174 % of W | max 0.6 | pass | انزلاق الخطوط عن الواجهة الحقيقية: متوسط 0.94px أقصى 5.38px |
| edge_recall | 0.6  | max None | info | نسبة الحواف الأفقية الحقيقية المكتشفة |
| edge_precision | 0.5769  | max None | info | نسبة الحواف المكتشفة التي تطابق حافة حقيقية |
| card_jitter_px | 0.1065 px | max 0.5 | pass | اهتزاز مواضع البطاقات (فرق ثانٍ) |
| card_overlap | 0 frames×pairs | max 0 | pass | تداخل البطاقات |
| ocr[فيلا للبيع] | 0.8235  | max None | info | «غيلللبيع|» |
| ocr[جدة] | 1.0  | max None | info | «جدة» |
| ocr[تواصل معنا] | 0.9412  | max None | info | «واصلمعنا» |
| ocr_similarity | 0.9216  | min 0.6 | pass | متوسط وضوح البطاقات (OCR عربي) |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 9:16: x 5%-95%, y 6%-82% |

### stone_text_45 — STONE_TEXT_REVEAL 4:5 (540×676)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 540×676 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.3277 % of W | max 0.5 | pass | متوسط 1.77px — أقصى 3.86px |
| track_err_max_pct | 0.7145 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0169 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.091px |
| track_drift_px | 0.9975 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| ocr_silhouette[أرض للبيع] | 0.5333  | max None | info | OCR «رضللادة» |
| ocr_composite[أرض للبيع] | 0.375  | max None | info | OCR «ورخصطيعة» |
| ocr_rectified[أرض للبيع] | 0.7059  | max None | info | OCR «ايض.لليبيع» (الشكل بعد إزالة المنظور) |
| ocr_similarity | 0.7059  | min 0.5 | pass | أسوأ beat: أعلى تشابه OCR بين (ظلّية، مركّب، معدّل المنظور) |
| text_height_pct | 9.822 % of H | min 3.5 | pass | ارتفاع النص على الشاشة وقت الثبات |
| stroke_rel_pct | 2.8894 % of W | min 0.45 | pass | سمك الخط التقديري |
| floating_alpha_pct | 0 % | max 1.5 | pass | أسوأ نسبة ألفا خارج الحجم المسموح (نص+غبار+حطام) |
| shadow_present | 6955 px | max None | info | بكسلات الظل شبه الشفافة الداكنة |
| perspective_err_pct | 0.2871 % of W | max 0.8 | pass | متوسط 1.55px أقصى 3.90px |
| contact_err_pct | 0.1369 % of W | max 1.5 | pass | متوسط 0.74px أقصى 1.96px |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 4:5: x 5%-95%, y 5%-90% |

### land_hologram_45 — LAND_HOLOGRAM_SEQUENCE 4:5 (540×676)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 540×676 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.3277 % of W | max 0.5 | pass | متوسط 1.77px — أقصى 3.86px |
| track_err_max_pct | 0.7145 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0169 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.091px |
| track_drift_px | 0.9975 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| policy_violations | 0  | max 0 | pass | قواعد الصدق: المساحة/المخطط/المبنى المعتمد — سليمة |
| outline_to_gt_pct | 0.3899 % of W | max 0.7 | pass | الخط المرسوم مقابل حدود الأرض الحقيقية: 2.11px |
| perspective_err_pct | 0.3325 % of W | max 0.8 | pass | متوسط 1.80px أقصى 4.60px |
| ocr_similarity | 1.0  | min 0.5 | pass | قراءة المساحة بعد إزالة المنظور: «2000|» (المتوقع 2000) |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 4:5: x 5%-95%, y 5%-90% |

### building_outline_45 — DIGITAL_BUILDING_OUTLINE 4:5 (540×676)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 540×676 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.4145 % of W | max 0.5 | pass | متوسط 2.24px — أقصى 8.61px |
| track_err_max_pct | 1.5937 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0279 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.150px |
| track_drift_px | 1.7134 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| line_slip_pct | 0.1903 % of W | max 0.6 | pass | انزلاق الخطوط عن الواجهة الحقيقية: متوسط 1.03px أقصى 6.42px |
| edge_recall | 0.5  | max None | info | نسبة الحواف الأفقية الحقيقية المكتشفة |
| edge_precision | 0.6  | max None | info | نسبة الحواف المكتشفة التي تطابق حافة حقيقية |
| card_jitter_px | 0.0909 px | max 0.5 | pass | اهتزاز مواضع البطاقات (فرق ثانٍ) |
| card_overlap | 0 frames×pairs | max 0 | pass | تداخل البطاقات |
| ocr[فيلا للبيع] | 1.0  | max None | info | «فيلاللبيع.» |
| ocr[جدة] | 1.0  | max None | info | «جدة» |
| ocr[تواصل معنا] | 0.9412  | max None | info | «واصلمعنا» |
| ocr_similarity | 0.9804  | min 0.6 | pass | متوسط وضوح البطاقات (OCR عربي) |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 4:5: x 5%-95%, y 5%-90% |

### stone_text_169 — STONE_TEXT_REVEAL 16:9 (960×540)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 960×540 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.1893 % of W | max 0.5 | pass | متوسط 1.82px — أقصى 4.27px |
| track_err_max_pct | 0.4445 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0136 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.130px |
| track_drift_px | 1.0304 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| ocr_silhouette[أرض للبيع] | 0.5333  | max None | info | OCR «رضللادة» |
| ocr_composite[أرض للبيع] | 0.3333  | max None | info | OCR «لاسي» |
| ocr_rectified[أرض للبيع] | 0.375  | max None | info | OCR «الهش.انيع» (الشكل بعد إزالة المنظور) |
| ocr_similarity | 0.5333  | min 0.5 | pass | أسوأ beat: أعلى تشابه OCR بين (ظلّية، مركّب، معدّل المنظور) |
| text_height_pct | 12.2567 % of H | min 3.5 | pass | ارتفاع النص على الشاشة وقت الثبات |
| stroke_rel_pct | 1.6253 % of W | min 0.45 | pass | سمك الخط التقديري |
| floating_alpha_pct | 0.0306 % | max 1.5 | pass | أسوأ نسبة ألفا خارج الحجم المسموح (نص+غبار+حطام) |
| shadow_present | 7044 px | max None | info | بكسلات الظل شبه الشفافة الداكنة |
| perspective_err_pct | 0.1465 % of W | max 0.8 | pass | متوسط 1.41px أقصى 3.85px |
| contact_err_pct | 0.07 % of W | max 1.5 | pass | متوسط 0.67px أقصى 1.93px |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 16:9: x 5%-95%, y 6%-90% |

### land_hologram_169 — LAND_HOLOGRAM_SEQUENCE 16:9 (960×540)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 960×540 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.1893 % of W | max 0.5 | pass | متوسط 1.82px — أقصى 4.27px |
| track_err_max_pct | 0.4445 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0136 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.130px |
| track_drift_px | 1.0304 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| policy_violations | 0  | max 0 | pass | قواعد الصدق: المساحة/المخطط/المبنى المعتمد — سليمة |
| outline_to_gt_pct | 0.2254 % of W | max 0.7 | pass | الخط المرسوم مقابل حدود الأرض الحقيقية: 2.16px |
| perspective_err_pct | 0.1713 % of W | max 0.8 | pass | متوسط 1.64px أقصى 4.57px |
| ocr_similarity | 1.0  | min 0.5 | pass | قراءة المساحة بعد إزالة المنظور: «2000» (المتوقع 2000) |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 16:9: x 5%-95%, y 6%-90% |

### building_outline_169 — DIGITAL_BUILDING_OUTLINE 16:9 (960×540)

| الفحص | القيمة | العتبة | الحالة | ملاحظة |
|---|---|---|---|---|
| aspect_ok | 1  | max None | info | 960×540 |
| track_flagged_frames_pct | 0.0 % | max None | info |  |
| track_err_mean_pct | 0.194 % of W | max 0.5 | pass | متوسط 1.86px — أقصى 6.82px |
| track_err_max_pct | 0.7103 % of W | max None | info |  |
| track_jitter_px_rel_pct | 0.0154 % of W | max 0.05 | pass | اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) 0.148px |
| track_drift_px | 0.6065 px | max None | info | نمو الخطأ بين بداية ونهاية المقطع |
| line_slip_pct | 0.0986 % of W | max 0.6 | pass | انزلاق الخطوط عن الواجهة الحقيقية: متوسط 0.95px أقصى 6.40px |
| edge_recall | 0.8  | max None | info | نسبة الحواف الأفقية الحقيقية المكتشفة |
| edge_precision | 0.6154  | max None | info | نسبة الحواف المكتشفة التي تطابق حافة حقيقية |
| card_jitter_px | 0.0394 px | max 0.5 | pass | اهتزاز مواضع البطاقات (فرق ثانٍ) |
| card_overlap | 0 frames×pairs | max 0 | pass | تداخل البطاقات |
| ocr[فيلا للبيع] | 0.8889  | max None | info | «غيلاللبيع.» |
| ocr[جدة] | 1.0  | max None | info | «جدة» |
| ocr[تواصل معنا] | 0.9412  | max None | info | «واصلمعنا» |
| ocr_similarity | 0.9434  | min 0.6 | pass | متوسط وضوح البطاقات (OCR عربي) |
| safe_zone_violations | 0 boxes | max 0 | pass | المنطقة الآمنة 16:9: x 5%-95%, y 6%-90% |

## 3) D · CINEMATIC_CAMERA_MOTION

| الحالة | الحكم | القياسات |
|---|---|---|
| land_916_tilt | pass | aspect_ok=1.0, overscan_zoom=1.16, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=1.0 |
| land_916_rise | pass | aspect_ok=1.0, overscan_zoom=1.215, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=1.0 |
| land_916_push | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.01 |
| facade_916_push | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.01 |
| land_45_tilt | pass | aspect_ok=1.0, overscan_zoom=1.175, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=1.0 |
| land_45_rise | pass | aspect_ok=1.0, overscan_zoom=1.235, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=1.0 |
| land_45_push | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.01 |
| facade_45_push | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.01 |
| land_169_tilt | pass | aspect_ok=1.0, overscan_zoom=1.295, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=1.0 |
| land_169_rise | pass (رفض متوقع ✓) | ✗ REJECT: تغطية المصدر لا تكفي حتى بتكبير 1.35× — المصدر صغير/الحركة كبيرة. قلّل --amount أو استخدم مصدراً أعلى دقة. |
| land_169_push | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.01 |
| land_169_rise_gentle | pass | aspect_ok=1.0, overscan_zoom=1.335, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=1.0 |
| facade_169_push | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.01 |
| land_916_rise_depth | pass | aspect_ok=1.0, overscan_zoom=1.215, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=1.0 |
| land_916_push_depth | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.01 |
| land_916_parallax_depth | pass | aspect_ok=1.0, overscan_zoom=1.0, velocity_start_end_pct=0.0, jerk_ratio=0.01, measured_vs_path_corr=0.995 |
| land_916_parallax_nodepth | pass (رفض متوقع ✓) | ✗ REJECT: parallax يتطلب خريطة depth (نموذج 3D أو توليد AI معتمد). لن أخترع زوايا جديدة من صورة ثابتة. |
| small_source_big_move | pass (رفض متوقع ✓) | ✗ REJECT: تغطية المصدر لا تكفي حتى بتكبير 1.35× — المصدر صغير/الحركة كبيرة. قلّل --amount أو استخدم مصدراً أعلى دقة. |
| video_stabilized_push | pass | aspect_ok=1.0, overscan_zoom=1.005, velocity_start_end_pct=0.0, jerk_ratio=0.0, stab_improvement_x=3.98 |

## 4) ملفات التصدير (فحص ثابت فقط)
- `premiere.xml`: XML سليم (parse OK) — غير مُستورد في Premiere
- `ae_build.jsx`: خطأ صياغة: node:internal/modules/esm/get_format:219
  throw new ERR_UNKNOWN_FILE_EXTENSION(ext, filepath);
        ^

TypeError [ERR_UNKNOWN_FILE_EXTENSION]: Unknown file extension ".jsx" for /home/user/video-ad
- `blender_build.py`: صياغة Python سليمة — غير مُشغَّل في Blender
