from functools import wraps

from django.http import JsonResponse
from django.shortcuts import redirect


def school_login_required(view):
    """沒登入：網頁導回登入頁，API 回 401。"""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("uid"):
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "not_signed_in"}, status=401)
            return redirect("accounts:login")
        return view(request, *args, **kwargs)
    return wrapper
