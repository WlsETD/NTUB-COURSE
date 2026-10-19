#!/usr/bin/env python3
"""
部署 Django 應用到 Google Cloud Run。
相當於 deploy.ps1 但用 Python 實現，避開 gcloud CLI 的問題。
"""
import json
import os
import sys
import subprocess
from pathlib import Path

def load_env():
    """讀取 .env 檔案"""
    env = {}
    with open(".env", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip('"\'')
    return env

def run_cmd(cmd, description):
    """執行指令"""
    print(f"\n→ {description}")
    print(f"  {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"✗ 失敗")
        if result.stderr:
            print(f"  {result.stderr[:200]}")
        return False
    print(f"✓ 完成")
    return True

def main():
    # 載入設定
    env = load_env()

    project = "ntub-90ecf"
    region = "asia-east1"
    service = "ntub-course"

    print("=" * 50)
    print("北商選課系統 - Cloud Run 部署")
    print("=" * 50)
    print(f"專案: {project}")
    print(f"地區: {region}")
    print(f"服務: {service}")

    # 驗證服務帳戶金鑰
    cred_path = env.get("FIREBASE_CREDENTIALS", "secrets/firebase-service-account.json")
    if not Path(cred_path).exists():
        print(f"✗ 服務帳戶金鑰檔不存在: {cred_path}")
        sys.exit(1)

    # 設置 Google 認證
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(cred_path)

    # 檢查並設置 gcloud 認證
    print("\n→ 驗證 Google Cloud 認證...")
    auth_ok = subprocess.run(
        f'gcloud auth application-default print-access-token --project={project} >nul 2>&1',
        shell=True
    ).returncode == 0

    if not auth_ok:
        print("⚠ 提示: 執行以下命令以驗證認證 (首次需要)")
        print(f"  gcloud auth login --project={project}")
        print("\n或按 Ctrl+C 中止，手動設置後重新執行本腳本")
        input("確認已驗證? (按 Enter 繼續)")

    # 構建環境變數檔
    print("\n→ 準備部署環境變數...")
    env_vars = {
        "DJANGO_DEBUG": "0",
        "DJANGO_ALLOWED_HOSTS": f"{service}-{project.split('-')[1]}.{region}.run.app",
        "DJANGO_CSRF_TRUSTED_ORIGINS": f"https://{service}-*.{region}.run.app",
        "FIREBASE_API_KEY": env.get("FIREBASE_API_KEY", ""),
        "FIREBASE_AUTH_DOMAIN": env.get("FIREBASE_AUTH_DOMAIN", ""),
        "FIREBASE_PROJECT_ID": env.get("FIREBASE_PROJECT_ID", ""),
        "FIREBASE_APP_ID": env.get("FIREBASE_APP_ID", ""),
        "OPENAI_MODEL": env.get("OPENAI_MODEL", "gpt-4.1-mini"),
        "OPENAI_MODEL_FAST": env.get("OPENAI_MODEL_FAST", ""),
        "AI_RATE_LIMIT": env.get("AI_RATE_LIMIT", "20"),
        "SCHOOL_DOMAIN": env.get("SCHOOL_DOMAIN", "ntub.edu.tw"),
        "TEACHER_EXTRA": env.get("TEACHER_EXTRA", ""),
    }

    # 寫環境變數檔
    env_file = "deploy_env.txt"
    with open(env_file, "w", encoding="utf-8") as f:
        for k, v in env_vars.items():
            if v:
                f.write(f"{k}={v}\n")
    print(f"✓ 環境變數已準備")

    # 部署指令
    deploy_cmd = (
        f"gcloud run deploy {service} "
        f"--source . "
        f"--platform managed "
        f"--region {region} "
        f"--project {project} "
        f"--allow-unauthenticated "
        f"--max-instances 3 "
        f"--env-vars-file {env_file}"
    )

    # 如果有 OPENAI_API_KEY，加上密鑰設置
    if env.get("OPENAI_API_KEY"):
        deploy_cmd += (
            f" --set-secrets "
            f"OPENAI_API_KEY=openai-api-key:latest,"
            f"DJANGO_SECRET_KEY=django-secret-key:latest"
        )

    # 執行部署
    if not run_cmd(deploy_cmd, "部署到 Cloud Run (這可能需要 3-10 分鐘)"):
        sys.exit(1)

    # 清理臨時檔
    os.remove(env_file)

    print("\n" + "=" * 50)
    print("✓ 部署完成！")
    print("=" * 50)
    print(f"\n網站網址: https://{service}-*.{region}.run.app")
    print("\n⚠ 後續步驟:")
    print(f"1. 前往 Firebase 主控台: https://console.firebase.google.com/project/{project}/overview")
    print(f"2. Authentication → 設定 → 授權網域")
    print(f"3. 加入 {service}-*.{region}.run.app")

if __name__ == "__main__":
    main()
