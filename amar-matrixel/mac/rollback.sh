#!/bin/bash
# AMAR — الرجوع عن activate.sh: يزيل الروابط الرمزية التي أنشأها activate.sh ويعيد السكلات المنقولة، ويعيد تفعيل plugin إن عُطّل.
# الاستخدام: bash rollback.sh ~/AMAR_BACKUPS/activate_<ts>
set -u
BK="${1:?مسار مجلد activate_<ts>}"; DST="$HOME/.claude/skills"; NEW="$(cat "$BK/NEW_CLONE_PATH.txt")"
for s in video-ad-editor motion-video podcast-video montage-video thumbnail-video davinci-video amar-matrixel; do
  if [ -L "${DST:?}/${s:?}" ] && [ "$(readlink "${DST:?}/${s:?}")" = "$NEW/$s" ]; then
    unlink "${DST:?}/${s:?}" && echo "- أزيل الرابط $s"   # unlink يحذف الرابط فقط، لا المجلد الذي يشير إليه
  fi
  if [ -e "$BK/active_skills/$s" ]; then mv "$BK/active_skills/$s" "${DST:?}/${s:?}" && echo "+ أُعيد $s"; fi
done
if [ -f "$BK/PLUGIN_DISABLED" ] && command -v claude >/dev/null; then claude plugin enable majed-video@majed-video && echo "+ أُعيد تفعيل plugin majed-video"; fi
echo "✅ رجعنا للحالة السابقة. افتح جلسة claude جديدة."
