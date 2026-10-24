#!/bin/bash
# fetch_fonts.sh — يجلب الخطوط المستخدمة في refmatch (Google Fonts، رخصة OFL) إلى fonts_tmp/ (غير مرفوعة للمستودع).
cd "$(dirname "$0")"; mkdir -p fonts_tmp
get(){ u=$(curl -sS -A "Mozilla/4.0" "https://fonts.googleapis.com/css2?family=$1" | grep -o "https://[^)]*" | head -1); curl -sS -o "fonts_tmp/$2" "$u" && echo "$2"; }
get "Baloo+Bhaijaan+2:wght@800" baloobhaijaan2-800-full.ttf
get "Baloo+2:wght@800" baloo2-800.ttf
get "Cairo:wght@700" cairo-full.ttf
get "Tajawal:wght@800" tajawal-full.ttf
