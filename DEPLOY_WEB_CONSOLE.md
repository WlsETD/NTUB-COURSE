# 用 Google Cloud 網頁控制台部署（最簡單）

如果 gcloud CLI 有問題，直接用網頁部署是最快的！

## 步驟

### 1️⃣ 打開 Cloud Run 主控台
👉 https://console.cloud.google.com/run?project=ntub-90ecf

### 2️⃣ 點「建立服務」

### 3️⃣ 選擇部署來源
- **選項：** 從 GitHub Repository 部署代碼
- **認證：** 連接你的 GitHub 帳號（WlsETD）
- **Repository：** 選 `NTUB-COURSE`
- **Branch：** 選 `main`
- **Build type：** 選 `Dockerfile`

### 4️⃣ 設定部署細節
| 欄位 | 值 |
|------|-----|
| Service name | `ntub-course` |
| Region | `asia-east1` (台灣) |
| Authentication | ☑️ Allow unauthenticated invocations |
| Memory | 512 MB (預設) |
| CPU | 1 |
| Timeout | 3600 秒 |
| Max instances | 3 |

### 5️⃣ 設定環境變數
點「編輯及建立」，切到「Variables and secrets」，添加：

```
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=ntub-course-*.asia-east1.run.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://ntub-course-*.asia-east1.run.app
FIREBASE_API_KEY=AIzaSyA2Mkoy8echELPCsMGlhHuiA5iXUbftKb8
FIREBASE_AUTH_DOMAIN=ntub-90ecf.firebaseapp.com
FIREBASE_PROJECT_ID=ntub-90ecf
FIREBASE_APP_ID=1:352781737994:web:32ff49a34458f4cabf3ff3
OPENAI_MODEL=gpt-4.1-mini
AI_RATE_LIMIT=20
SCHOOL_DOMAIN=ntub.edu.tw
```

### 6️⃣ 建立服務
點「建立」按鈕，等待 **5-10 分鐘**（會看到藍色進度列）

完成後會顯示網址：
```
https://ntub-course-xxxxx.asia-east1.run.app
```

## 部署完成後

### 7️⃣ 設定 Firebase 授權網域
1. https://console.firebase.google.com/project/ntub-90ecf/authentication/providers
2. 選「Google」
3. 下滑到「授權網域」
4. 點「+ 新增網域」
5. 貼上部署完成後的網址（例 `ntub-course-xxxxx.asia-east1.run.app`）

### 8️⃣ 驗證網站
打開上面的網址，應該會看到選課系統的登入頁面！

## 之後如何更新

每次你改代碼並 push 到 `main`，有兩個選項：

**方案 A：自動部署（推薦）**
- 設置 GitHub Actions secrets（見 `GITHUB_ACTIONS_SETUP.md`）
- 之後每次 push 自動部署

**方案 B：手動重新部署**
1. Cloud Run 主控台 → `ntub-course` 服務
2. 點「編輯及部署新修訂版本」
3. 建置並部署（會自動抓最新的 GitHub `main` 分支）

## 常見錯誤

**❌ Build 失敗：「找不到 Dockerfile」**
→ 確認 repo 在 `django_app/` 資料夾有 `Dockerfile`（有的）

**❌ Deploy 失敗：「No such image」**
→ Build 可能還在進行中，等 5 分鐘再試

**❌ 登入失敗：「The origin is not authorized」**
→ Firebase 授權網域未設置（見步驟 7️⃣）

**❌ 頁面顯示 403 Forbidden**
→ Cloud Run 服務未設「Allow unauthenticated invocations」

## 檢查部署狀態

Cloud Run 主控台會實時顯示：
- 📊 Metrics：CPU、Memory、Requests
- 📋 Revisions：部署歷史
- 📝 Logs：即時日誌（點「Logs」標籤）

---

**走到這裡就完成了！** 🎉 選課系統已上線。

有問題檢查日誌或聯絡我。
