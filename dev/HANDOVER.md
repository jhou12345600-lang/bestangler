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
| `chat/world`、`chat/p{池}` | 聊天訊息（最多 60 字） | 登入者可讀；只能新增，每人至少間隔 1.5 秒（`chatT/{uid}`） |
| `ids/{帳號}` | 帳號對應 uid，用來以帳號加好友 | 登入者可讀，只能由該帳號本人建立一次 |
| `requests/{對方}/{我}` | 好友邀請 | 收件人可讀可刪，寄件人可建立 |
| `friends/{uid}/{好友uid}` | 好友名單 | 只有本人可讀；接受邀請時雙方同時寫入 |
| `gifts/{收件人}/{pushId}` | 禮物 | 只能送給好友；數量有上限；每人至少間隔 3 秒（`giftT/{uid}`）。收件人領取後刪除 |

同池即時狀態另外帶有 `x`（在碼頭上的位置）、`w`（走動方向）和 `c`（角色：`g` 女主角、`b` 男主角）。

## 素材建置流程（`dev/tools/`）

1. `esrgan.py`：Real-ESRGAN x2 放大，需要 `RealESRGAN_x2plus.pth` 權重與 PyTorch。
2. `roto.py`、`girlfix.py`：從官方截圖去背，製作碼頭上的角色姿勢。官方素材包缺少 `girl-animation.txt` 列出的 124 格角色動畫。
3. `build_assets.py 原始images資料夾 工作資料夾 輸出資料夾`：輸出 WebP 圖集與 `assets.json`。
4. `make_site.py`：把 `dev/game-source.html` 包成完整網站。

## 這一版新增的程式重點

- **碼頭與鏡頭**：`pond.wx` 是自己在碼頭上的位置，`pond.camW` 是鏡頭位置，單位是在碼頭處 1 單位等於 300 像素。全域變數 `CAMX` 讓 `proj()` 依透視平移。背景用鏡像拼接，水面著色器的 `cam` uniform 也會一起平移。
- **角色**：`charInfo()` 回傳角色的圖、錨點和握竿位置，`drawChar()` 負責畫角色，`charHand()` 負責算出握竿的手的位置。
- **男主角美術**：在 `dev/tools/char3d/` 用 three.js 算繪。
  - `final.py` 輸出待機、搏魚、結算和頭像。
  - `walk.py` 輸出走路動畫的 8 格。
  - 模型是 Microsoft Rocketbox 的 Male_Adult_05，MIT 授權。
- **水下搏魚**：`pond.drawUnder()`，依 `pond.line` 和 `pond.fish` 的狀態畫出來。
- **聊天、好友、送禮**：
  - 介面在 `chatModal`、`friendsModal`、`playerCard`、`giftModal`。
  - 資料讀寫在 `FB.sendChat`、`FB.requestFriend`、`FB.acceptFriend`、`FB.sendGift`、`FB.claimGift`。
  - 禮物內容由 `applyGift` 加進存檔。
  - 不雅字清單是 `BAD_WORDS`。
- **模擬器測試**：`dev/tools/mp_test3.py` 用兩個瀏覽器測試走動、聊天、加好友和送禮。
  - 模擬器要先載入規則：`curl -X PUT -H "Authorization: Bearer owner" --data-binary @database.rules.json "http://127.0.0.1:9000/.settings/rules.json?ns=demo-bestangler"`

## 建議官方補上或決定的事項

- **男主角**：目前是暫代的 3D 算繪美術，可以換成官方畫風的男主角。換的時候保持同樣的錨點，也就是腳底在畫面 y=1266、身體中心在 x=392。
- **聊天管理**：目前只有用戶端的不雅字過濾和個人封鎖，沒有檢舉和後台。正式營運建議加 Cloud Functions 做審核，並定期清除舊訊息。

- **角色動畫**：補上碼頭角色 124 格動畫（待機、拋竿、拉扯、收魚），目前只有兩個靜態姿勢。
- **防作弊**：若要正式營運，建議加遊戲伺服器（例如 Cloud Functions），由伺服器結算漁獲與排行榜。
- **找回密碼**：若需要，可改成用信箱登入，再搭配 Firebase 的重設密碼信。
- **Firebase 專案**：可以換成官方自己的專案，改 `firebase-config.js` 即可。
