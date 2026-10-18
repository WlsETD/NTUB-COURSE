# django_app：選課系統的 Django 版本

Django 5.2 + Firebase（Auth、Firestore）+ OpenAI。套件用 uv 管理。完整說明見 README.md。

## 指令

```bash
uv sync
uv run python manage.py runserver
uv run python manage.py test          # 全部測試都不連外：STORE=memory、Firebase 與 OpenAI 都是 mock
uv run python manage.py seed_courses  # 把 data/ntub_115-1.txt 寫進 Firestore
```

## 架構重點

- 不使用 Django 資料庫（`DATABASES = {}`），session 用 signed cookies。不要加需要資料表的 app（auth、admin、contenttypes）。
- 登入：前端 Firebase Auth（Google）→ `POST /auth/session/` 帶 ID token → `accounts/views.py` 驗證並檢查 `@ntub.edu.tw` → `request.session` 存 uid、email、name。保護頁面用 `accounts.decorators.school_login_required`。
- 資料：一律透過 `courses/store.py` 的 `get_store()`，不要在 view 裡直接呼叫 Firestore。新增功能時 `FirestoreStore` 與 `MemoryStore` 兩個都要實作，測試才跑得動。
- Firestore 不能存「陣列裡的陣列」，所以課程的 slots 存成 `[{d,s,e}]`，讀出時轉回 `[[d,s,e]]`。
- 前端：`courses/templates/courses/app.html`（HTML）、`static/courses/app.js`、`app.css`。課程資料用 `json_script` 放在 `#raw-data`，學生上次的選課與設定在 `#boot-data`。
- `app.js` 的 `render()` 最後會呼叫 `queueSave()`，選課有變動時 0.6 秒後 `POST /api/selection/`。所有 POST 用 `apiPost()`，會自動帶 CSRF token。
- AI：前端只送描述與課程 id，提示詞在 `courses/ai.py` 組。回覆的 id 一定要再對照候選清單。

## 規則

- 金鑰（Firebase 服務帳戶、OpenAI）只能放 `.env` 與 `secrets/`，不能寫進程式碼或前端。
- 介面文字要中英兩份：加到 `app.js` 的 `STR.zh` 與 `STR.en`。
- 介面設計規則同上層資料夾的 CLAUDE.md（不用 1px 邊框、顏色用 CSS 變數、彩色主題不用漸層、手機與平板版面相同）。
- 改完執行 `uv run python manage.py test`。
- 上層資料夾的 `course.html` 是 claude.ai 版本，和這裡的 `app.js`／`app.css` 是分開維護的兩份程式。

## 字體

- 俐方體 11 號（Cubic 11）的檔案在 `courses/static/courses/fonts/cubic11.woff2`，由 `app.css` 第一行的 `@font-face` 載入；登入頁 `login.html` 的標題也用同一個檔案（`{% static %}` 路徑）。
- `@font-face` 的 `src` 只能寫一次 `format("woff2")`，寫錯整個字體會被瀏覽器忽略，畫面會退回 Noto Sans TC。
- 設定裡的 C／N 切換：`html[data-font="noto"]` 會改用 Noto Sans TC。
