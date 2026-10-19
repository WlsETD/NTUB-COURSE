# GitHub Actions 自動部署設置

現在每次 push 到 `main` 就會自動部署到 Cloud Run！

## 設置步驟

### 1️⃣ 添加 GitHub Secrets

前往 **GitHub → Settings → Secrets and variables → Actions** 添加以下 secrets：

#### 必需：
| Secret 名稱 | 值 | 說明 |
|---------|-----|------|
| `GCP_SA_KEY` | 服務帳戶 JSON 全內容 | 見下方 |
| `FIREBASE_API_KEY` | `AIzaSyA2Mkoy8echELPCsMGlhHuiA5iXUbftKb8` | Firebase 網頁設定 |
| `FIREBASE_AUTH_DOMAIN` | `ntub-90ecf.firebaseapp.com` | Firebase 專案 |
| `FIREBASE_PROJECT_ID` | `ntub-90ecf` | Firebase 專案 ID |
| `FIREBASE_APP_ID` | `1:352781737994:web:32ff49a34458f4cabf3ff3` | Firebase 網頁應用 |

#### 選用：
| Secret 名稱 | 說明 |
|---------|------|
| `OPENAI_MODEL` | OpenAI 模型，預設 `gpt-4.1-mini` |
| `OPENAI_MODEL_FAST` | 快速模型 |
| `TEACHER_EXTRA` | 額外老師帳號設置 |

### 2️⃣ 獲取服務帳戶金鑰 JSON

#### 方法 A：複製已有的金鑰（最快）
```bash
cat django_app/secrets/firebase-service-account.json
```
複製整個 JSON 內容，貼到 `GCP_SA_KEY` secret

#### 方法 B：從 Firebase 主控台下載（如果 A 不行）
1. https://console.firebase.google.com/project/ntub-90ecf/settings/serviceaccounts/adminsdk
2. 選「Python」標籤
3. 點「新的私密金鑰」
4. 下載的 JSON 全內容

### 3️⃣ 驗證設置

前往 GitHub → Actions，應該會看到：
- **Deploy to Cloud Run** workflow
- 最新的 run status

## 工作流程說明

```
你改代碼 → git push to main
  ↓
GitHub Actions 觸發 deploy.yml
  ↓
gcloud 用 GCP_SA_KEY 認證
  ↓
建置 Docker 映像 & 部署到 Cloud Run
  ↓
驗證部署並顯示網址
```

## 查看部署日誌

1. GitHub → Actions
2. 點最新的 **Deploy to Cloud Run** run
3. 展開各個 step 查看詳細日誌

## 常見問題

**Q: 部署失敗，認證錯誤**
A: 檢查 `GCP_SA_KEY` 是否完整（JSON 應該有 `{` 開頭、`}` 結尾）

**Q: 如何暫時禁用自動部署**
A: GitHub → Actions → 左側點 **Deploy to Cloud Run** → ⋯ → Disable workflow

**Q: 想部署到不同的 Cloud Run 服務**
A: 編輯 `.github/workflows/deploy.yml`，改 `ntub-course` 為新名稱

**Q: 想在特定分支部署**
A: 編輯 workflow：
```yaml
on:
  push:
    branches: [ main, develop ]  # 添加分支
```

## 手動觸發部署

如果只想測試 workflow（不改代碼），可以手動執行：
1. GitHub → Actions
2. **Deploy to Cloud Run** → **Run workflow** → 選分支 → **Run workflow**

## 禁用特定路徑的部署

如果只想在改 Django 代碼時部署，已設置：
```yaml
paths:
  - 'django_app/**'          # 只監視 django_app 資料夾
  - '.github/workflows/deploy.yml'
```
改 HTML 或課程資料不會觸發部署。

---

現在每次改代碼 push，自動部署✨

有問題檢查 GitHub Actions 日誌或聯絡我。
