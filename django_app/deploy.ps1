# 部署到 Google Cloud Run。在 django_app 資料夾執行：powershell -ExecutionPolicy Bypass -File deploy.ps1
# 金鑰從 .env 讀取後存進 Secret Manager，不會打包進映像；其他設定以環境變數傳給 Cloud Run。
# 金鑰只在第一次建立；之後換了 .env 的 OPENAI_API_KEY 要加 -UpdateSecrets 才會更新。
param([switch]$UpdateSecrets)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8  # 中文訊息不要變亂碼
Set-Location $PSScriptRoot

$Project = "ntub-90ecf"
$Region  = "asia-east1"
$Service = "ntub-course"
$Number  = (gcloud projects describe $Project --format="value(projectNumber)")
$Url     = "https://$Service-$Number.$Region.run.app"
$RunSA   = "$Number-compute@developer.gserviceaccount.com"

# 讀 .env
$envs = @{}
Get-Content .env -Encoding UTF8 | Where-Object { $_ -match '^\s*([A-Z_]+)\s*=(.*)$' } | ForEach-Object {
    $envs[$Matches[1]] = $Matches[2].Trim()
}

function Set-Secret($name, $value) {
    if (-not $value) { throw "$name 沒有值" }
    $tmp = [IO.Path]::GetTempFileName()
    try {
        [IO.File]::WriteAllText($tmp, $value)  # 不加換行
        $exists = $true
        try { gcloud secrets describe $name --project $Project *> $null; if ($LASTEXITCODE) { $exists = $false } } catch { $exists = $false }
        if ($exists) {
            gcloud secrets versions add $name --data-file=$tmp --project $Project
        } else {
            gcloud secrets create $name --data-file=$tmp --replication-policy=automatic --project $Project
        }
    } finally { Remove-Item $tmp -Force }
    gcloud secrets add-iam-policy-binding $name --member="serviceAccount:$RunSA" `
        --role=roles/secretmanager.secretAccessor --project $Project --condition=None | Out-Null
}

Write-Host "== 1/2 Secret Manager =="
$secrets = "DJANGO_SECRET_KEY=django-secret-key:latest"
$exists = $true
try { gcloud secrets describe django-secret-key --project $Project *> $null; if ($LASTEXITCODE) { $exists = $false } } catch { $exists = $false }
if (-not $exists) {
    # 第一次部署才產生，之後沿用（換掉會讓所有人的登入失效）
    Set-Secret "django-secret-key" (-join ((48..57 + 65..90 + 97..122) | Get-Random -Count 60 | ForEach-Object { [char]$_ }))
}
$aiExists = $true
try { gcloud secrets describe openai-api-key --project $Project *> $null; if ($LASTEXITCODE) { $aiExists = $false } } catch { $aiExists = $false }
if ($envs["OPENAI_API_KEY"] -and ($UpdateSecrets -or -not $aiExists)) {
    Set-Secret "openai-api-key" $envs["OPENAI_API_KEY"]
    $aiExists = $true
}
if ($aiExists) { $secrets += ",OPENAI_API_KEY=openai-api-key:latest" }

Write-Host "== 2/2 Cloud Run =="
$vars = [ordered]@{
    DJANGO_DEBUG                = "0"
    DJANGO_ALLOWED_HOSTS        = "$Service-$Number.$Region.run.app"
    DJANGO_CSRF_TRUSTED_ORIGINS = $Url
    FIREBASE_API_KEY            = $envs["FIREBASE_API_KEY"]
    FIREBASE_AUTH_DOMAIN        = $envs["FIREBASE_AUTH_DOMAIN"]
    FIREBASE_PROJECT_ID         = $envs["FIREBASE_PROJECT_ID"]
    FIREBASE_APP_ID             = $envs["FIREBASE_APP_ID"]
    OPENAI_MODEL                = $envs["OPENAI_MODEL"]
    OPENAI_MODEL_FAST           = $envs["OPENAI_MODEL_FAST"]
    AI_RATE_LIMIT               = $envs["AI_RATE_LIMIT"]
    SCHOOL_DOMAIN               = $envs["SCHOOL_DOMAIN"]
}
$yaml = [IO.Path]::GetTempFileName()
try {
    $lines = $vars.GetEnumerator() | Where-Object { $_.Value } | ForEach-Object { "$($_.Key): '$($_.Value -replace "'", "''")'" }
    [IO.File]::WriteAllLines($yaml, $lines)
    # max-instances 3：AI 次數上限存在各台的記憶體裡，台數少一點比較準
    gcloud run deploy $Service --source . --region $Region --project $Project `
        --allow-unauthenticated --max-instances 3 `
        --env-vars-file $yaml --set-secrets $secrets
} finally { Remove-Item $yaml -Force }

Write-Host ""
Write-Host "完成：$Url"
Write-Host "記得到 Firebase 主控台 → Authentication → 設定 → 授權網域，加入 $Service-$Number.$Region.run.app"
