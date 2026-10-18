# 北商選課系統：Django + Firebase + OpenAI

把原本單檔的選課介面搬進 Django，使用課程教材的工具（uv、Django、templates、static），並串接：

- **Firebase Authentication**：Google 學校帳號登入，只收 @ntub.edu.tw
- **Cloud Firestore**：存課程資料、每位學生的選課，以及每門課透過本系統登記的人數
- **OpenAI**：右下角 AI 機器人的選課建議（API 金鑰只放在伺服器）

## 運作方式

```
瀏覽器 ──Google 登入──▶ Firebase Auth
   │  拿到 ID token
   ▼
Django（views.py）── 驗證 token、檢查 @ntub.edu.tw ──▶ 寫入 session
   │
   ├─ GET  /app/              選課頁面（課程資料與上次的選課一起放進頁面）
   ├─ POST /api/selection/    加選／退選後自動儲存 ──▶ Firestore（transaction 更新登記人數）
   ├─ POST /api/ai/depts/     AI 判斷相關學系      ──▶ OpenAI
   └─ POST /api/ai/suggest/   AI 挑選課程          ──▶ OpenAI
```

瀏覽器不會直接連 Firestore，也拿不到 OpenAI 金鑰；所有資料存取都經過 Django 檢查。

## 專案結構

```
django_app/
├── pyproject.toml / uv.lock      套件（uv 管理）
├── manage.py
├── .env.example                  設定範本，複製成 .env 後填值
├── firestore.rules / firebase.json
├── data/ntub_115-1.txt           課程原始資料（748 筆）
├── secrets/                      放 Firebase 服務帳戶金鑰（不會進 Git）
├── config/                       settings.py、urls.py
├── accounts/                     登入、登出
│   ├── views.py                  驗證 Firebase ID token、檢查學校網域
│   ├── decorators.py             school_login_required
│   └── templates/accounts/login.html   片頭動畫＋Google 登入
└── courses/                      選課
    ├── views.py                  頁面與 API
    ├── store.py                  Firestore 讀寫（courses、students 集合）
    ├── ai.py                     組提示詞、呼叫 OpenAI
    ├── ntub_data.py              讀取課程資料檔
    ├── firebase.py               Firebase Admin SDK 初始化
    ├── management/commands/seed_courses.py   把課程寫進 Firestore
    ├── templates/courses/app.html
    ├── static/courses/app.css、app.js、fonts/cubic11.woff2
    └── tests.py
```

## 第一次設定

### 1. Firebase 主控台

你已經有 Firebase 專案，接著確認：

1. **Authentication → Sign-in method**：啟用「Google」。
2. **Authentication → 設定 → 授權網域**：加入 `127.0.0.1`（本機測試）與正式網域。`localhost` 預設已在清單中。
3. **Firestore Database**：建立資料庫（正式模式即可），位置建議選 `asia-east1`（台灣）。
4. **專案設定 → 一般 → 你的應用程式**：新增「網頁應用程式」，複製 `firebaseConfig` 裡的 `apiKey`、`authDomain`、`projectId`、`appId`。
5. **專案設定 → 服務帳戶 → 產生新的私密金鑰**：下載 JSON，改名為 `firebase-service-account.json` 放進 `secrets/`。**這個檔案等同密碼，不要傳給別人或上傳 GitHub。**
6. 部署安全規則（瀏覽器一律不能直接讀寫）：
   ```bash
   npm install -g firebase-tools
   firebase login
   firebase deploy --only firestore:rules --project 你的專案ID
   ```
   也可以直接把 `firestore.rules` 的內容貼到主控台的 Firestore → 規則。

### 2. OpenAI

到 OpenAI Platform 建立 API key，填進 `.env` 的 `OPENAI_API_KEY`。帳戶需要有額度。`OPENAI_MODEL` 可以換成你帳戶能用的任何支援 JSON 模式的模型。沒有填金鑰時，AI 機器人按鈕會自動隱藏，其他功能照常。

### 3. 安裝與啟動（Windows PowerShell）

```powershell
cd D:\競賽\選課系統\django_app
uv sync                                  # 建立 .venv 並安裝套件
copy .env.example .env                   # 用 VS Code 打開 .env 填值
uv run python manage.py seed_courses     # 第一次：把 748 門課寫進 Firestore
uv run python manage.py runserver
```

打開 <http://127.0.0.1:8000/>：片頭動畫 → Google 學校帳號登入 → 選課系統。加選、退選後會自動存到 Firestore，換電腦登入也能看到同樣的選課。

> 用 `127.0.0.1:8000` 開啟時，記得 `127.0.0.1` 要在 Firebase 的授權網域裡；或改用 `http://localhost:8000/`。

## 常用指令

| 指令 | 用途 |
|---|---|
| `uv run python manage.py runserver` | 啟動開發伺服器 |
| `uv run python manage.py test` | 自動測試（不會連 Firebase 與 OpenAI） |
| `uv run python manage.py seed_courses` | 課程資料有更新時重新寫入（保留登記人數） |
| `uv run python manage.py seed_courses --reset-counts` | 重新寫入並把登記人數歸零 |

## Firestore 資料

| 集合 | 文件 ID | 欄位 |
|---|---|---|
| `courses` | 課程 id（`s0`～`s747`） | name、teacher、dept、cls、grade、slots、credits、cap、enr（擷取時的已選人數）、registered（本系統登記人數）… |
| `students` | Firebase uid | email、major、grade、cls、sel（已選課程 id）、auto（自動帶入的必修）、updatedAt |

畫面上的「已選人數」＝ `enr` ＋ `registered`。加選、退選在同一個 transaction 裡更新 `registered`，多人同時操作也不會算錯。

## 學生與老師

- **學生**：從信箱的學號判斷學制、科系、年級（`courses/student_id.py`），自動帶入本班必修。
- **老師**：信箱在 `data/teachers.txt` 裡就是老師，登入後進 `/teacher/`，看到自己開的課（用姓名對應課程資料的授課老師）和每門課透過本系統選課的學生（學號、姓名、班級、信箱）。示範時可以用 `.env` 的 `TEACHER_EXTRA` 再加帳號。

## 安全設計

- **學校帳號檢查在伺服器**：Google 登入視窗的 `hd` 參數只是提示，學生仍可換帳號，所以 `accounts/views.py` 會用 Firebase Admin SDK 驗證 token，並確認是 Google 登入、信箱已驗證、結尾是 `@ntub.edu.tw`。
- **CSRF**：所有 POST 都要帶 Django 的 CSRF token。
- **Firestore 規則全部拒絕**：只有 Django（Admin SDK）能讀寫。
- **OpenAI 金鑰不出伺服器**，而且提示詞由伺服器組合，前端只能送「描述」與課程 id，不能拿來問別的問題；每位學生每 10 分鐘有次數上限。
- **登入狀態**存在簽章過的 cookie，8 小時後失效。

## 正式上線注意

部署到 Google Cloud Run：在 `django_app` 執行 `powershell -ExecutionPolicy Bypass -File deploy.ps1`。它會把 `.env` 裡的金鑰存進 Secret Manager，再用 `Dockerfile`（gunicorn＋WhiteNoise）建置並部署到 `ntub-90ecf` 的 `asia-east1`。部署完要把網址加進 Firebase 的授權網域。`.env` 和 `secrets/` 不會被上傳（見 `.gcloudignore`）。

- `.env` 設 `DJANGO_DEBUG=0`、很長的 `DJANGO_SECRET_KEY`、`DJANGO_ALLOWED_HOSTS`、`DJANGO_CSRF_TRUSTED_ORIGINS`。
- 必須使用 HTTPS。
- 執行 `uv run python manage.py collectstatic`，由網頁伺服器（或 WhiteNoise）提供 `staticfiles/`。
- 用 gunicorn 等正式伺服器啟動，不要用 `runserver`。
- AI 次數上限存在記憶體快取，多台伺服器時要改用 Redis。

## 與 claude.ai 版本的差異

- 課程資料從 Firestore 讀取，選課會存檔（claude.ai 版重新整理就消失）。
- AI 機器人改用 OpenAI（claude.ai 版使用 Claude）。
- 登入改用 Firebase，不再有「示範模式」。
- 「已修學分」仍是範例數字。
