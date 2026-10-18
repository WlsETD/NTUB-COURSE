"""登入與登出。

流程：
1. 學生在登入頁按「使用 Google 學校帳號登入」，前端用 Firebase Auth 跳出 Google 視窗。
2. 前端拿到 Firebase 的 ID token，POST 到 /auth/session/。
3. 伺服器用 Firebase Admin SDK 驗證 token，再確認是已驗證的 @ntub.edu.tw 信箱，才寫入 session。
前端的 hd 參數只是讓 Google 優先顯示學校帳號，真正的檢查在這裡。
"""
import json

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from firebase_admin import auth as fb_auth

from courses.firebase import get_app


def login_page(request):
    if request.session.get("uid"):
        return redirect("courses:app")
    return render(request, "accounts/login.html", {
        "firebase_config": settings.FIREBASE_WEB_CONFIG,
        "school_domain": settings.SCHOOL_DOMAIN,
    })


def verify_school_token(id_token):
    """驗證 Firebase ID token，回傳 (使用者資料, 錯誤代碼)。"""
    try:
        claims = fb_auth.verify_id_token(id_token, app=get_app(), clock_skew_seconds=10)
    except Exception:
        return None, "invalid_token"
    email = str(claims.get("email") or "").lower()
    provider = (claims.get("firebase") or {}).get("sign_in_provider")
    if provider != "google.com" or not claims.get("email_verified") or not email.endswith("@" + settings.SCHOOL_DOMAIN):
        return {"email": email}, "not_school_account"
    return {"uid": claims["uid"], "email": email, "name": claims.get("name") or ""}, None


@require_POST
def create_session(request):
    try:
        token = json.loads(request.body or b"{}").get("idToken", "")
    except ValueError:
        token = ""
    if not token:
        return JsonResponse({"error": "missing_token"}, status=400)
    user, err = verify_school_token(token)
    if err == "not_school_account":
        return JsonResponse({"error": err, "email": user["email"]}, status=403)
    if err:
        return JsonResponse({"error": err}, status=401)
    request.session.flush()  # 換一個新的 session，避免沿用舊的
    request.session.update(user)
    return JsonResponse({"ok": True, "name": user["name"] or user["email"]})


@require_POST
def dev_login(request):
    """本機測試用：不經過 Google，直接用指定的學校信箱登入（可以在瀏覽器 console 呼叫）。

    只有 DJANGO_DEBUG=1 才能用；正式環境（Cloud Run 設 DJANGO_DEBUG=0）一律 404。
    """
    if not settings.DEBUG:
        raise Http404
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        body = {}
    email = str(body.get("email") or "").strip().lower()
    if not email.endswith("@" + settings.SCHOOL_DOMAIN):
        return JsonResponse({"error": "not_school_account", "email": email}, status=403)
    request.session.flush()
    request.session.update({"uid": "dev:" + email, "email": email, "name": str(body.get("name") or "")[:40]})
    return JsonResponse({"ok": True, "email": email})


@require_POST
def logout_view(request):
    request.session.flush()
    return JsonResponse({"ok": True})
