#!/bin/bash
# AMAR — تفعيل النسخة الجديدة بشكل قابل للرجوع. افتراضياً «عرض فقط» (dry-run). التنفيذ الفعلي بـ --apply بعد موافقة المستخدم.
# الطريقة: لكل سكل من السبعة: إن وُجد في ~/.claude/skills يُنقل (لا يُحذف) إلى ~/AMAR_BACKUPS/activate_<ts>/active_skills/،
# ثم رابط رمزي إلى النسخة الجديدة. plugin «majed-video» إن كان منصّباً يُعطَّل فقط (لا يُلغى تثبيته) لمنع تكرار السكلات.
# الرجوع: rollback.sh
set -u
APPLY=0; [ "${1:-}" = "--apply" ] && APPLY=1
NEW="$(cd "$(dirname "$0")/../.." && pwd)"; TS="$(date +%Y%m%d_%H%M%S)"; BK="$HOME/AMAR_BACKUPS/activate_$TS"; DST="$HOME/.claude/skills"
SK="video-ad-editor motion-video podcast-video montage-video thumbnail-video davinci-video amar-matrixel"
run(){ if [ $APPLY = 1 ]; then echo "+ $*"; "$@"; else echo "(عرض فقط) $*"; fi; }
EXPECT=4215ca727e5c73f05fa6d0c800a55871180855db
# النسخة المعتمدة 4215ca7 + سكربتات التثبيت فقط: نتحقق أن 4215ca7 سلف لـHEAD وأن أي فرق بعده محصور في amar-matrixel/mac/ و AMAR_MASTER_STATUS.md
verify_approved(){ local R="$1"
  git -C "$R" cat-file -e "$EXPECT^{commit}" 2>/dev/null || { echo "commit 4215ca7 غير موجود في الاستنساخ"; return 1; }
  git -C "$R" merge-base --is-ancestor "$EXPECT" HEAD || { echo "HEAD لا يحتوي 4215ca7"; return 1; }
  local extra; extra=$(git -C "$R" diff --name-only "$EXPECT" HEAD | grep -vE '^(amar-matrixel/mac/|AMAR_MASTER_STATUS\.md$)')
  [ -z "$extra" ] || { echo "فروق خارج ملفات التثبيت: $extra"; return 1; }; return 0; }
msg=$(verify_approved "$NEW") || { echo "⛔ النسخة لا تطابق 4215ca7: $msg — لا تفعيل"; exit 1; }
ls "$HOME"/AMAR_BACKUPS/2*/SHA256.txt >/dev/null 2>&1 || { echo "⛔ لا نسخة احتياطية من preflight.sh — شغّله أولاً"; exit 1; }
run mkdir -p "$DST" "$BK/active_skills"
for s in $SK; do
  if [ -e "${DST:?}/${s:?}" ] || [ -L "${DST:?}/${s:?}" ]; then run mv "${DST:?}/${s:?}" "$BK/active_skills/$s"; fi
  run ln -s "$NEW/$s" "${DST:?}/${s:?}"
done
if command -v claude >/dev/null && claude plugin list 2>/dev/null | grep -q "majed-video"; then
  echo "plugin majed-video منصّب — سيُعطَّل (يبقى مثبتاً) لمنع تكرار السكلات"
  run claude plugin disable majed-video@majed-video
  [ $APPLY = 1 ] && echo plugin_disabled > "$BK/PLUGIN_DISABLED"
fi
if [ $APPLY = 1 ]; then
  echo "$NEW" > "$BK/NEW_CLONE_PATH.txt"
  echo "✅ فُعّل. الرجوع: bash \"$NEW/amar-matrixel/mac/rollback.sh\" \"$BK\" — ثم افتح جلسة claude جديدة."
else
  echo "ℹ️ عرض فقط — لم يتغير شيء. للتنفيذ بعد الموافقة: bash $0 --apply"
fi
