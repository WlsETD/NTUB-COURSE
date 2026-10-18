# 選課系統：Google 學校帳號單一登入

這個資料夾是選課系統的可部署版本。學生用學校的 Google 帳號（@ntub.edu.tw）登入，不需要另外註冊；個人 Gmail 會被擋下。

## 使用流程

1. 開啟網站，先播放片頭動畫：色塊依序彈出、「選課系統」逐字浮現。
2. 約 2.6 秒後切換到登入頁（也可以按右下角「略過動畫」）。
3. 按「使用 Google 帳戶登入」，在 Google 視窗中選擇學校帳號。
4. 伺服器驗證通過後進入選課系統；設定選單中可以看到登入的信箱，也可以登出。

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `public/login.html` | 片頭動畫與登入頁，使用 Google Identity Services 的登入按鈕 |
| `server.js` | Express 伺服器：驗證 Google 回傳的 ID token、檢查學校網域、管理登入狀態 |
| `app/course.html` | 選課系統本體，只有登入後才能存取 |
| `package.json` | 相依套件 |

## 為什麼這樣能確保是學校帳號

前端的 `hd: "ntub.edu.tw"` 只會讓 Google 優先顯示學校帳號，使用者仍然可以換成其他帳號，所以不能只靠前端。真正的檢查在 `server.js`：

1. 用 `google-auth-library` 驗證 ID token 的簽章，並確認 `audience` 是你的 Client ID，防止偽造或拿別的網站的 token 來用。
2. 確認 `hd`（Google Workspace 網域）等於 `ntub.edu.tw`。
3. 確認 `email_verified` 為 true，且信箱結尾是 `@ntub.edu.tw`。

三項都通過才會建立登入狀態。選課系統本體放在 `app/` 而不是公開的 `public/`，未登入的人直接打 `/app` 會被導回登入頁。

## 設定步驟

### 1. 建立 Google OAuth 用戶端

1. 到 Google Cloud Console 建立專案。
2. 在「OAuth 同意畫面」設定應用程式名稱。
   - 如果學校的 Google Workspace 管理員願意協助，可以把使用者類型設為「內部」，這樣只有 @ntub.edu.tw 帳號能使用。
   - 若無法設為內部，就選「外部」，伺服器端的網域檢查仍會擋下非學校帳號。
3. 在「憑證」建立「OAuth 用戶端 ID」，類型選「網頁應用程式」。
4. 「已授權的 JavaScript 來源」加入網站網址，例如本機測試的 `http://localhost:3000`，以及正式網址 `https://你的網域`。
5. 複製產生的 Client ID。

### 2. 安裝與啟動

需要 Node.js 18 以上。

```bash
npm install
# Windows PowerShell
$env:GOOGLE_CLIENT_ID="你的 Client ID"; $env:SESSION_SECRET="一串很長的隨機字"; npm start
# macOS / Linux
GOOGLE_CLIENT_ID="你的 Client ID" SESSION_SECRET="一串很長的隨機字" npm start
```

開啟 `http://localhost:3000` 即可測試。

### 3. 正式上線

- 必須使用 HTTPS，並設定環境變數 `NODE_ENV=production`，登入 cookie 才會加上 `secure`。
- `SESSION_SECRET` 不要寫進程式碼或上傳到 GitHub。
- 預設的 session 存在記憶體，伺服器重啟後大家要重新登入；人數多時建議改用 Redis 等 session store。

## 注意事項

- `app/course.html` 是目前選課系統的版本。在這個環境下，頁面內建的預覽登入畫面會自動略過，改用伺服器提供的登入資訊。
- 頁面中的「AI 選課建議」需要在 claude.ai 上開啟才能使用；部署在自己的網站時會自動隱藏。要在自己的網站提供 AI 功能，需要另外串接 Claude API，並在伺服器端保管 API 金鑰。
- 選課資料仍是 2026 年 10 月 8 日擷取的快照，加選與退選不會寫回學校系統。
