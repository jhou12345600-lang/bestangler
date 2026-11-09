#!/usr/bin/env bash
# 神釣手：把帳號和資料從舊 Firebase 專案搬到官方的新專案（做法 B）
# 在倉庫根目錄執行，需要 Node.js 和 Firebase CLI（npm install -g firebase-tools）。
#
#   dev/migrate/migrate.sh export                 舊專案擁有者登入後執行：匯出帳號和資料到 dev/migrate/out/
#   dev/migrate/migrate.sh rules   新專案ID        新專案擁有者登入後執行：發布資料庫安全規則
#   dev/migrate/migrate.sh import  新專案ID        新專案擁有者登入後執行：匯入帳號（保留密碼）和資料
#
# 匯出的檔案含玩家帳號和密碼雜湊，只能私下交給官方，用完刪除，不要放進 Git。
set -euo pipefail
OLD=bestangler-83bed
OUT="$(dirname "$0")/out"
mkdir -p "$OUT"
cmd=${1:-}; NEW=${2:-}

case "$cmd" in
  export)
    firebase auth:export "$OUT/users.json" --format=json --project "$OLD"
    firebase database:get / --project "$OLD" --instance "$OLD-default-rtdb" -o "$OUT/db.json"
    echo
    echo "已匯出：$OUT/users.json（帳號）和 $OUT/db.json（資料）"
    echo "另外到 Firebase 主控台 > Authentication > 使用者 > 右上角選單 > 密碼雜湊參數，"
    echo "把 base64_signer_key、base64_salt_separator、rounds、mem_cost 四個值一起交給官方。"
    ;;
  rules)
    [ -n "$NEW" ] || { echo "用法：$0 rules 新專案ID"; exit 1; }
    tmp=$(mktemp -d); cp database.rules.json "$tmp/"
    printf '{ "database": { "rules": "database.rules.json" } }\n' > "$tmp/firebase.json"
    (cd "$tmp" && firebase deploy --only database --project "$NEW")
    rm -rf "$tmp"
    ;;
  import)
    [ -n "$NEW" ] || { echo "用法：$0 import 新專案ID"; exit 1; }
    read -r -p "base64_signer_key：" KEY
    read -r -p "base64_salt_separator：" SEP
    read -r -p "rounds：" ROUNDS
    read -r -p "mem_cost：" MEM
    firebase auth:import "$OUT/users.json" --project "$NEW" --hash-algo=SCRYPT \
      --hash-key="$KEY" --salt-separator="$SEP" --rounds="$ROUNDS" --mem-cost="$MEM"
    # 線上狀態和同池即時位置是暫存資料，不搬
    node -e '
      const fs = require("fs"); const p = process.argv[1];
      const d = JSON.parse(fs.readFileSync(p, "utf8")) || {};
      delete d.online; delete d.pond;
      fs.writeFileSync(p.replace(/db\.json$/, "db-import.json"), JSON.stringify(d));
    ' "$OUT/db.json"
    firebase database:set / "$OUT/db-import.json" --project "$NEW" --instance "$NEW-default-rtdb" -f
    echo "完成。請用一個舊帳號登入新網站，確認存檔、好友、排行榜都在。"
    ;;
  *)
    sed -n '2,10p' "$0"; exit 1 ;;
esac
