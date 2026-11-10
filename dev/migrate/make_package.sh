#!/usr/bin/env bash
# 打包官方主機要上傳的網站檔案：dev/migrate/make_package.sh [輸出zip路徑]
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=${1:-bestangler-site.zip}; T=$(mktemp -d); D="$T/bestangler-site"; mkdir -p "$D"
cp -r index.html assets.json img lib sfx "$D/"
cp dev/migrate/firebase-config.template.js "$D/firebase-config.js"
cp dev/migrate/htaccess.example "$D/.htaccess"
cp dev/migrate/架設說明.txt "$D/"
(cd "$T" && zip -qr - bestangler-site) > "$OUT"; rm -rf "$T"; echo "已輸出 $OUT"
