#!/bin/bash
# AMAR — فحص ما قبل التفعيل على الماك. آمن: قراءة + نسخة احتياطية + اختبارات داخل النسخة المنفصلة ومجلد مؤقت فقط.
# لا يغيّر أي سكل نشط، ولا إعدادات Claude، ولا أي ملف Adobe.
# الاستخدام (من أي مكان):  bash <الاستنساخ>/amar-matrixel/mac/preflight.sh
# المخرج: تقرير نصي في ~/AMAR/reports/ — أرسله لـClaude.
set -u
EXPECT=4215ca727e5c73f05fa6d0c800a55871180855db
# النسخة المعتمدة 4215ca7 + سكربتات التثبيت فقط: نتحقق أن 4215ca7 سلف لـHEAD وأن أي فرق بعده محصور في amar-matrixel/mac/ و AMAR_MASTER_STATUS.md
verify_approved(){ local R="$1"
  git -C "$R" cat-file -e "$EXPECT^{commit}" 2>/dev/null || { echo "commit 4215ca7 غير موجود في الاستنساخ"; return 1; }
  git -C "$R" merge-base --is-ancestor "$EXPECT" HEAD || { echo "HEAD لا يحتوي 4215ca7"; return 1; }
  local extra; extra=$(git -C "$R" diff --name-only "$EXPECT" HEAD | grep -vE '^(amar-matrixel/mac/|AMAR_MASTER_STATUS\.md$)')
  [ -z "$extra" ] || { echo "فروق خارج ملفات التثبيت: $extra"; return 1; }; return 0; }
NEW="$(cd "$(dirname "$0")/../.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"; BK="$HOME/AMAR_BACKUPS/$TS"; RD="$HOME/AMAR/reports"; mkdir -p "$BK" "$RD"
REP="$RD/preflight_$TS.txt"; exec > >(tee "$REP") 2>&1
PASS=0; FAIL=0; WARN=0
ok(){ echo "✅ $*"; PASS=$((PASS+1)); }; bad(){ echo "❌ $*"; FAIL=$((FAIL+1)); }; warn(){ echo "⚠️ $*"; WARN=$((WARN+1)); }
SK="video-ad-editor motion-video podcast-video montage-video thumbnail-video davinci-video amar-matrixel"
echo "AMAR preflight $TS — $(sw_vers -productVersion 2>/dev/null || uname -s)"; echo "النسخة الجديدة: $NEW"; echo

echo "== 1) أماكن السكلات الحالية (قراءة فقط) =="
FOUND=""
for d in "$HOME/.claude/skills" "$HOME/.claude/plugins"; do
  [ -d "$d" ] || { echo "  (لا يوجد $d)"; continue; }
  while IFS= read -r f; do
    sd="$(dirname "$f")"
    case "$sd" in "$NEW"*) continue;; esac
    n="$(sed -n 's/^name: *//p' "$f" | head -1)"
    link=""; [ -L "$sd" ] && link=" → $(readlink "$sd")"
    ver=""; [ -f "$sd/VERSION" ] && ver=" v$(cat "$sd/VERSION")"
    pol="سياسة AMAR: لا"; grep -q production-policy "$f" && pol="سياسة AMAR: نعم"
    echo "  • $n — $sd$link$ver — $pol"; FOUND="$FOUND $n"
  done < <(find -L "$d" -maxdepth 6 -name SKILL.md 2>/dev/null)
done
if [ -f "$HOME/.claude/settings.json" ]; then echo "  settings.json — plugins مفعّلة:"; grep -o '"[^"]*@[^"]*": *true' "$HOME/.claude/settings.json" 2>/dev/null | sed 's/^/    /'; fi
if command -v claude >/dev/null; then echo "  claude plugin list:"; claude plugin list 2>/dev/null | sed 's/^/    /' | head -20; fi
for s in $SK; do c=$(echo "$FOUND" | tr ' ' '\n' | grep -cx "$s"); [ "$c" -gt 1 ] && warn "السكل $s منصّب $c مرات (تكرار قائم مسبقاً)"; done
echo

echo "== 2) Premiere / After Effects (قراءة فقط) =="
ls -d /Applications/Adobe\ Premiere\ Pro* /Applications/Adobe\ After\ Effects* 2>/dev/null | sed 's/^/  تطبيق: /'
for d in /Applications/Adobe\ After\ Effects*/Scripts "$HOME/Library/Application Support/Adobe/CEP/extensions" "/Library/Application Support/Adobe/CEP/extensions" "$HOME/Documents/Adobe"; do
  [ -d "$d" ] || continue
  hits=$(grep -rIl -E "video-ad-editor|amar-matrixel|majed-video|\.claude/skills" "$d" 2>/dev/null | head -5)
  if [ -n "$hits" ]; then warn "مراجع لمسارات السكلات داخل: $d"; echo "$hits" | sed 's/^/     /'; else echo "  لا مراجع لمسارات السكلات في: $d"; fi
done
echo "  (لم يُفتح أي مشروع .prproj/.aep ولم يُعدَّل أي إعداد Adobe)"; echo

echo "== 3) نسخة احتياطية كاملة → $BK =="
for d in "$HOME/.claude/skills" "$HOME/.claude/plugins" "$HOME/.claude/settings.json" "$HOME/.claude/CLAUDE.md"; do
  [ -e "$d" ] || continue; b="$(basename "$d")"
  if tar -czhf "$BK/$b.tgz" -C "$(dirname "$d")" "$b" 2>/dev/null; then ok "نسخة: $d → $b.tgz ($(du -h "$BK/$b.tgz" | cut -f1))"; else bad "فشل نسخ $d"; fi
done
( cd "$BK" && shasum -a 256 ./*.tgz > SHA256.txt 2>/dev/null; true ); echo "$NEW" > "$BK/NEW_CLONE_PATH.txt"
echo "  الاستعادة اليدوية: انقل الحالي جانباً ثم: tar -xzf <ملف>.tgz -C ~/.claude"; echo

echo "== 4) مطابقة النسخة الجديدة =="
H=$(git -C "$NEW" rev-parse --short HEAD 2>/dev/null)
if msg=$(verify_approved "$NEW"); then ok "مطابق: النسخة المعتمدة 4215ca7 كاملة (HEAD=$H يضيف ملفات التثبيت فقط: $(git -C "$NEW" diff --name-only "$EXPECT" HEAD | tr '\n' ' '))"; else bad "عدم مطابقة: $msg"; fi
if [ -z "$(git -C "$NEW" status --porcelain 2>/dev/null)" ]; then ok "شجرة العمل نظيفة"; else warn "تعديلات محلية في النسخة الجديدة"; fi
for f in AMAR_MASTER_STATUS.md CLAUDE.md amar-matrixel/refmatch/USAGE.md video-ad-editor/references/production-policy.md; do
  if [ -s "$NEW/$f" ]; then ok "موجود ويُقرأ: $f ($(wc -l < "$NEW/$f" | tr -d ' ') سطر)"; else bad "ناقص: $f"; fi
done
for f in amar-matrixel/refmatch/final/R4_v2.1_hologram_final_1146x644.mp4 amar-matrixel/refmatch/final/R5_v2_facade_outline_final_1146x644.mp4 amar-matrixel/refmatch/final/R3_AI_vertical_comp_v1_1080x1920.mp4; do
  if [ -s "$NEW/$f" ]; then ok "النسخة المعتمدة موجودة: $(basename "$f")"; else bad "ناقص: $f"; fi
done; echo

echo "== 5) السكلات السبع والسياسة =="
for s in $SK; do
  f="$NEW/$s/SKILL.md"
  if [ ! -f "$f" ]; then bad "$s: SKILL.md ناقص"; continue; fi
  if ! { head -1 "$f" | grep -q '^---$' && grep -q '^name: ' "$f" && grep -q '^description: ' "$f"; }; then bad "$s: رأس السكل غير سليم"; continue; fi
  p=$(grep -o '`${CLAUDE_SKILL_DIR}[^`]*production-policy.md`' "$f" | head -1 | tr -d '`' | sed "s|\${CLAUDE_SKILL_DIR}|$NEW/$s|")
  if [ -n "$p" ] && [ -f "$p" ]; then ok "$s: رأس سليم + يحيل للسياسة (المسار موجود)"; else bad "$s: إحالة السياسة مفقودة أو لا تُحلّ"; fi
done
if grep -q production-policy "$NEW/video-ad-editor/references/start.md"; then ok "start.md يحيل للسياسة"; else bad "start.md لا يحيل"; fi
if grep -q production-policy "$NEW/CLAUDE.md" && grep -q AMAR_MASTER_STATUS "$NEW/CLAUDE.md"; then ok "CLAUDE.md يحيل للسياسة وملف الحالة"; else bad "CLAUDE.md ناقص"; fi
echo

echo "== 6) رفض AI ← البديل المحلي (مجلد مؤقت، بلا إنترنت ولا إنفاق) =="
T="$(mktemp -d)"; PY=$(command -v python3)
if [ -n "$PY" ] && command -v ffmpeg >/dev/null; then
  ffmpeg -v error -y -f lavfi -i testsrc2=s=720x1280:d=2 -pix_fmt yuv420p "$T/source.mp4"
  printf '%s' '{"assets":[{"k":"desk","kind":"video","dur":2,"ar":"9:16","prompt":"slow dolly across a desk"},{"k":"paper","kind":"image","ar":"3:4","prompt":"flat lay notebook"}],"scenes":[{"s":"w:a","e":"w:b","k":"desk","mode":"bg"},{"s":"w:c","e":"w:d","k":"paper","mode":"card"}]}' > "$T/gen.json"
  G="$NEW/video-ad-editor/scripts/17_gen_scenes.py"
  if "$PY" "$G" "$T" request >/dev/null && [ -s "$T/ai_requests/REQUEST.md" ]; then ok "request: حزمة طلب بلا إنفاق"; else bad "request فشل"; fi
  if ( cd "$T" && env -u FAL_KEY HOME="$T" "$PY" "$G" "$T" fetch >/dev/null 2>&1 ); then warn "fetch لم يتوقف بلا مفتاح"; else ok "fetch بلا مفتاح يتوقف (لا إنفاق)"; fi
  if "$PY" "$G" "$T" fallback >/dev/null && [ -f "$T/gen/desk_0001.jpg" ] && [ -f "$T/gen/paper.jpg" ]; then ok "fallback: بديل محلي فوري (فيديو + صورة)"; else bad "fallback فشل"; fi
  ffmpeg -v error -y -f lavfi -i testsrc=s=720x1280:d=1 -pix_fmt yuv420p "$T/u.mp4"
  if "$PY" "$G" "$T" import desk "$T/u.mp4" >/dev/null; then ok "import: استبدال البديل بلقطة المستخدم"; else bad "import فشل"; fi
else warn "python3 أو ffmpeg غير موجود — تخطّي اختبار البديل المحلي"; fi
rm -rf "${T:?}"; echo

echo "== 7) حماية التحديث (على النسخة المنفصلة فقط) =="
out=$(cd "$NEW/video-ad-editor" && bash scripts/00_setup.sh --update 2>&1 | tail -1)
if echo "$out" | grep -q "نسخة AMAR معدَّلة"; then ok "--update مرفوض في نسخة AMAR (الإضافات محمية)"; else bad "الحماية لم تعمل: $out"; fi
if [ -f "$NEW/video-ad-editor/references/production-policy.md" ]; then ok "production-policy.md باقٍ بعد محاولة التحديث"; else bad "السياسة حُذفت!"; fi
echo

echo "== 8) التعارض مع المهارات الحالية =="
for s in $SK; do
  if echo "$FOUND" | tr ' ' '\n' | grep -qx "$s"; then echo "  • $s منصّب حالياً — عند التفعيل يُنقل للنسخة الاحتياطية ويُربط بالجديد (قابل للرجوع)"; else echo "  • $s غير منصّب حالياً — سيُضاف"; fi
done
others=$(echo "$FOUND" | tr ' ' '\n' | grep . | grep -vxE "$(echo $SK | tr ' ' '|')" | sort -u | tr '\n' ' ')
echo "  مهارات أخرى لن تُلمس: ${others:-لا يوجد}"
echo
echo "== الخلاصة: نجاح $PASS · تحذير $WARN · فشل $FAIL =="
echo "النسخة الاحتياطية: $BK"; echo "التقرير: $REP"
if [ "$FAIL" -eq 0 ]; then echo "➡️ جاهز. التفعيل بعد موافقتك فقط: bash \"$NEW/amar-matrixel/mac/activate.sh\" (عرض) ثم --apply"; else echo "⛔ لا تفعّل قبل إصلاح ما فشل."; fi
