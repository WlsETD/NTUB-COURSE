# Cloud Run 部署指南

## 方案 1：使用 gcloud CLI（推薦）

### 步驟 1：安裝 gcloud CLI
在 **PowerShell** 中執行：
```powershell
# 下載並安裝（如果尚未安裝）
choco install google-cloud-sdk -y
# 或用 scoop
scoop install gcloud
```

### 步驟 2：認證登入
```powershell
gcloud auth login
gcloud config set project ntub-90ecf
```

### 步驟 3：部署
複製以下指令到 PowerShell 執行（在 `django_app` 資料夾中）：
```powershell
gcloud run deploy ntub-course `
  --source . `
  --platform managed `
  --region asia-east1 `
  --project ntub-90ecf `
  --allow-unauthenticated `
  --max-instances 3 `
  --env-vars-file deploy_env.txt `
  --set-secrets DJANGO_SECRET_KEY=django-secret-key:latest
```

部署通常需要 **3-10 分鐘**。完成後會顯示網址。

## 方案 2：使用 Google Cloud Console（網頁）

1. 前往 https://console.cloud.google.com/run
2. 點擊「建立服務」
3. 從 GitHub 連接你的 repo：`WlsETD/NTUB-COURSE`
4. 選擇分支：`main`
5. 建置類型：Dockerfile
6. 服務名稱：`ntub-course`
7. 地區：`asia-east1`
8. 驗證：允許未驗證的呼叫
9. 點「編輯及建立」設置環境變數

## 方案 3：GitHub Actions 自動部署

1. 在 GitHub Secrets 中添加：
   - `GCP_PROJECT_ID`: `ntub-90ecf`
   - `GCP_SERVICE_ACCOUNT_KEY`: 從 Firebase 服務帳戶 JSON 複製整個內容
2. 每次 push 到 `main` 就自動部署

## 部署後設置

部署完成後，在 Firebase 主控台設置授權網域：

1. 前往 https://console.firebase.google.com/project/ntub-90ecf/authentication/providers
2. 點「設定」→「授權網域」
3. 加入 `ntub-course-xxxxx.asia-east1.run.app`（實際網址會在部署完成時顯示）

## 檢查部署狀態

```powershell
gcloud run services list --region asia-east1 --project ntub-90ecf
```

## 查看日誌

```powershell
gcloud run services logs read ntub-course --region asia-east1 --project ntub-90ecf --limit 50
```

## 常見問題

**Q: 部署失敗，說 Python 不存在**
A: gcloud SDK 需要系統 Python。安裝 Python 3.10+ 後重試。

**Q: 部署成功但登入失敗**
A: 檢查 Firebase 主控台的授權網域設定，加入 `ntub-course-xxxxx.asia-east1.run.app`

**Q: 如何更新已部署的服務**
A: 改代碼後 push 到 GitHub，如果有 Actions 會自動部署；否則重新執行部署指令

## 環境變數備註

- `DJANGO_SECRET_KEY`: 已隨機生成
- `FIREBASE_*`: 已從 Firebase 專案抓取
- `OPENAI_API_KEY`: 目前空白，AI 功能停用；要啟用請填入 OpenAI API 金鑰
- `SCHOOL_DOMAIN`: `ntub.edu.tw`（學校信箱驗證）

---

有問題可以檢查雲端日誌或聯絡我進一步協助。
