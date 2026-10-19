#!/usr/bin/env python3
import json
import os
import sys

# 檢查服務帳戶金鑰
sa_path = "secrets/firebase-service-account.json"
if not os.path.exists(sa_path):
    print("✗ 服務帳戶金鑰檔不存在")
    sys.exit(1)

with open(sa_path) as f:
    sa = json.load(f)

print(f"✓ 服務帳戶: {sa.get('client_email')}")
print(f"✓ 專案 ID: {sa.get('project_id')}")

# 檢查 .env
with open(".env", encoding="utf-8") as f:
    env = {}
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v

required = ["DJANGO_SECRET_KEY", "FIREBASE_PROJECT_ID", "FIREBASE_API_KEY", "FIREBASE_CREDENTIALS"]
missing = [k for k in required if not env.get(k)]

if missing:
    print(f"\n✗ 缺少設定: {', '.join(missing)}")
    sys.exit(1)

print(f"\n✓ Django Secret Key: 已設置")
print(f"✓ Firebase 金鑰: 已設置")
print(f"✓ OpenAI API Key: {'已設置' if env.get('OPENAI_API_KEY') else '未設置 (AI 功能停用)'}")

print("\n準備部署到 Cloud Run...")
print("專案: ntub-90ecf")
print("地區: asia-east1")
print("服務: ntub-course")
