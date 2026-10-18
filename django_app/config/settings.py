"""北商選課系統的 Django 設定。

所有密碼與金鑰都從 .env 讀取（參考 .env.example），不要寫進程式碼或上傳到 GitHub。
這個專案沒有使用 Django 的資料庫：登入交給 Firebase Auth，資料存在 Firestore。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or ("dev-only-insecure-key" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("請在 .env 設定 DJANGO_SECRET_KEY（開發時可改設 DJANGO_DEBUG=1）")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "accounts",
    "courses",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # 正式環境由 WhiteNoise 提供 staticfiles/（collectstatic 產生）
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# Firebase 的 signInWithPopup 需要和彈出視窗溝通；預設的 same-origin 會讓它誤判成「登入視窗已關閉」
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# 不使用 Django 資料庫；登入狀態存在簽章過的 cookie 裡
DATABASES = {}
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 8 * 60 * 60  # 8 小時
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Asia/Taipei"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# ---------- 學校 ----------
SCHOOL_DOMAIN = os.getenv("SCHOOL_DOMAIN", "ntub.edu.tw")

# ---------- Firebase ----------
# 前端登入用的設定（Firebase 主控台 → 專案設定 → 一般 → 你的應用程式）。這些值本來就會出現在網頁上，不是密碼。
FIREBASE_WEB_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
}
# 伺服器用的服務帳戶金鑰（Firebase 主控台 → 專案設定 → 服務帳戶 → 產生新的私密金鑰）。這是密碼，不能外流。
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "")
# STORE=memory 時不連 Firestore，資料存在記憶體（只給自動測試用）
STORE = os.getenv("STORE", "firestore")

# ---------- OpenAI ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# 用 or：.env 裡留空的「OPENAI_MODEL_FAST=」也要退回預設值，不能變成空字串
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4.1-mini"
OPENAI_MODEL_FAST = os.getenv("OPENAI_MODEL_FAST", "").strip() or OPENAI_MODEL
AI_RATE_LIMIT = int(os.getenv("AI_RATE_LIMIT", "20"))  # 每位學生每 10 分鐘最多幾次 AI 請求

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
