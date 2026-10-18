"""Firebase Admin SDK 初始化：整個網站共用一個 app。

金鑰路徑從 .env 的 FIREBASE_CREDENTIALS 讀取。
若設定了 FIRESTORE_EMULATOR_HOST / FIREBASE_AUTH_EMULATOR_HOST，Admin SDK 會自動改連本機模擬器。
"""
import os
import threading

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, firestore

_lock = threading.Lock()


def get_app():
    with _lock:
        try:
            return firebase_admin.get_app()
        except ValueError:
            pass
        options = {"projectId": settings.FIREBASE_WEB_CONFIG["projectId"]} if settings.FIREBASE_WEB_CONFIG["projectId"] else None
        if settings.FIREBASE_CREDENTIALS:
            path = settings.FIREBASE_CREDENTIALS
            if not os.path.isabs(path):
                path = os.path.join(settings.BASE_DIR, path)
            cred = credentials.Certificate(path)
        elif os.getenv("FIRESTORE_EMULATOR_HOST") or os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
            cred = None  # 模擬器不需要金鑰
        else:
            cred = credentials.ApplicationDefault()
        return firebase_admin.initialize_app(cred, options)


def db():
    return firestore.client(get_app())
