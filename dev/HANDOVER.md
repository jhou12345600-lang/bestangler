# 交接說明（給官方開發團隊）

## 程式架構（`index.html`）

整個遊戲是一個 HTML 檔，邏輯解析度 720×1280。

- **畫面層**：
  - `#gl`：WebGL 水面著色器（折射、倒影、波浪、漣漪、陽光）。
  - `#cv`：Canvas 2D，繪製所有原作美術與 UI。
- **場景**：
  - `titleScene`：讀取與登入
  - `lobbyScene`：大廳地圖
  - `pond`：釣魚，含拋竿、等待、搏魚、水下鏡頭
  - `catchScene`：結算
- **遊戲資料**：`FISH`（魚種數值）、`PONDS`（釣池）、`RODS`、`LINES`、`FLOATS`、`BAITS` 都在檔案開頭，可以直接調整數值。
- **連線**：`NET` 是統一介面，有兩種後端：
  - `FB`：公開網站用，Firebase Auth 加 Realtime Database。
  - `claude`：Claude 頁面版。
- **存檔**：玩家狀態物件是 `S`。
  - 登入後存在 `users/{uid}/save`，內容為 JSON 字串。
  - 本機另存一份 `localStorage` 當快取。

## Realtime Database 資料結構

| 路徑 | 內容 | 權限 |
|---|---|---|
| `users/{uid}/profile` | 帳號、選填信箱 | 只有本人可讀寫 |
| `users/{uid}/save` | 完整存檔 | 只有本人可讀寫 |
| `leaderboard/{uid}` | 名稱、等級、EP、漁獲數、最佳紀錄 | 登入者可讀，只有本人可寫 |
| `online/{uid}` | 線上狀態（所在釣池） | 登入者可讀，只有本人可寫，斷線自動移除 |
| `pond/{id}/{uid}` | 同池即時狀態（浮標、搏魚、表情） | 同上 |
| `feed/{pushId}` | 漁獲通知 | 只能新增，不能修改 |

## 素材建置流程（`dev/tools/`）

1. `esrgan.py`：Real-ESRGAN x2 放大，需要 `RealESRGAN_x2plus.pth` 權重與 PyTorch。
2. `roto.py`、`girlfix.py`：從官方截圖去背，製作碼頭上的角色姿勢。官方素材包缺少 `girl-animation.txt` 列出的 124 格角色動畫。
3. `build_assets.py 原始images資料夾 工作資料夾 輸出資料夾`：輸出 WebP 圖集與 `assets.json`。
4. `make_site.py`：把 `dev/game-source.html` 包成完整網站。

## 建議官方補上或決定的事項

- **角色動畫**：補上碼頭角色 124 格動畫（待機、拋竿、拉扯、收魚），目前只有兩個靜態姿勢。
- **防作弊**：若要正式營運，建議加遊戲伺服器（例如 Cloud Functions），由伺服器結算漁獲與排行榜。
- **找回密碼**：若需要，可改成用信箱登入，再搭配 Firebase 的重設密碼信。
- **Firebase 專案**：可以換成官方自己的專案，改 `firebase-config.js` 即可。
