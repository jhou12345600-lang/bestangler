# 神釣手 Best Angler — 2D 高畫質重製版（線上版）

原作《神釣手 Web 3D》美術 © 鳳翔科技，經官方同意重製。
官方接手後，內容與修改方向以官方決定為準。

**線上遊玩：** https://jhou12345600-lang.github.io/bestangler/

## 功能

- 帳號註冊／登入。帳號為 4–16 個英文、數字或底線，密碼至少 6 碼，信箱選填。
- 新手馬上玩：免註冊的訪客身分，之後可以綁定成正式帳號，進度保留。
- 雲端存檔：換裝置登入同一個帳號，就能接著玩。
- 連線：
  - 線上玩家名單
  - 同一個釣池會一起站在碼頭上，看得到彼此的浮標和搏魚
  - 表情互動
  - 全服漁獲通知
  - 全服排行榜
- 4 個釣池、13 種魚，有拋竿、咬餌、揚竿、捲線搏魚、上岸結算。另有釣具店與裝備系統。

## 檔案結構

| 路徑 | 內容 |
|---|---|
| `index.html` | 遊戲本體，單一檔案，Canvas 2D 加 WebGL 水面 |
| `assets.json`、`img/` | 素材索引與圖集（WebP） |
| `lib/` | Firebase JS SDK（compat 版） |
| `firebase-config.js` | Firebase 專案設定（公開的用戶端設定，不是密碼） |
| `database.rules.json` | Realtime Database 安全規則 |
| `dev/` | 開發用：素材建置與 AI 放大腳本、Firebase 模擬器設定。詳見 [`dev/HANDOVER.md`](dev/HANDOVER.md) |

## 架設到其他 Firebase 專案

1. 建立 Firebase 專案，新增網頁應用程式，把 `firebaseConfig` 填進 `firebase-config.js`。記得加上 `databaseURL`。
2. Authentication → 登入方式：啟用「電子郵件/密碼」和「匿名」。
3. Realtime Database：建立資料庫（建議新加坡區），把 `database.rules.json` 的內容貼到「規則」後發布。
4. 網站放在任何靜態主機都可以，例如 GitHub Pages、Firebase Hosting。

## 已知限制

- 帳號不使用真實信箱登入，所以無法線上自動重設密碼。
- 沒有遊戲伺服器，遊戲邏輯在玩家端執行，排行榜分數理論上可以被竄改。
- Firebase 免費方案最多約 100 人同時在線。
