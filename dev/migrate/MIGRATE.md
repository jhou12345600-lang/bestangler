# 搬到官方 Firebase 專案與主機（做法 B）

## 事前準備（不影響玩家）

1. 官方建立新的 Firebase 專案：
   - Authentication 開啟「電子郵件/密碼」和「匿名」。
   - 建立 Realtime Database（建議 asia-southeast1）。
   - 新增一個網頁應用程式，取得設定值。
2. 發布規則：`dev/migrate/migrate.sh rules 新專案ID`
3. 執行 `dev/migrate/make_package.sh` 打包網站，上傳到官方主機，再把 `firebase-config.js` 填上新專案的設定值。主機設定見 `架設說明.txt`。
4. 用新網址註冊一個測試帳號，確認能玩、能存檔。測完到新專案把這個測試帳號和它的資料刪掉。
5. 至少提前一天在遊戲內公告搬遷時間，並提醒「訪客」先註冊帳號。訪客的登入狀態存在瀏覽器裡，換網址後無法帶過去。

## 搬遷當天

1. 舊網站換成維護頁：用 `maintenance.html`（把 `__DONE_TIME__` 換成預計完成時間）取代舊網站的 `index.html`，玩家就無法再寫入舊資料庫。
2. 舊專案擁有者執行 `dev/migrate/migrate.sh export`，並到主控台抄下密碼雜湊參數。
3. 把 `dev/migrate/out/` 和密碼雜湊參數私下交給官方。
4. 官方執行 `dev/migrate/migrate.sh import 新專案ID`。
5. 用一個舊帳號登入新網站，確認存檔、好友、排行榜都在。
6. 舊網站換成轉址頁：用 `redirect.html`（把 `__NEW_URL__` 換成新網址）取代舊網站的 `index.html`。
7. 刪除 `dev/migrate/out/` 裡的匯出檔。

匯出檔含玩家帳號和密碼雜湊，不要放進 Git，也不要公開傳送。
