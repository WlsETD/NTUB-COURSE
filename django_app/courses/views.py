import json

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import school_login_required

from . import ai
from .store import clean_selection, course_rows_for, get_store
from .student_id import student_from_email


def _json_body(request):
    try:
        data = json.loads(request.body or b"{}")
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def _me(request):
    return {"uid": request.session["uid"], "email": request.session.get("email", ""), "name": request.session.get("name", "")}


@school_login_required
def app_page(request):
    """選課主畫面：課程資料與學生上次存的選課一起放進頁面。"""
    me = _me(request)
    saved = get_store().get_student(me["uid"])
    sel = (saved or {}).get("sel") or []
    boot = {
        "email": me["email"],
        # 頁首的「歡迎，{名字}」；Google 帳號沒有名字時用信箱 @ 前面的部分
        "name": me["name"] or me["email"].split("@")[0],
        # 從學號判斷的學制、科系、年級；前端用它自動帶入本系本班的必修
        "student": student_from_email(me["email"]),
        "saved": {k: saved[k] for k in ("major", "grade", "cls", "sel", "auto") if k in saved} if saved else None,
        "ai": ai.enabled(),
    }
    return render(request, "courses/app.html", {"courses": course_rows_for(sel), "boot": boot})


@require_GET
@school_login_required
def api_me(request):
    me = _me(request)
    return JsonResponse({"email": me["email"], "name": me["name"], "saved": get_store().get_student(me["uid"])}, json_dumps_params={"default": str})


@require_POST
@school_login_required
def api_selection(request):
    """儲存選課（每次加選、退選後由前端自動呼叫）。"""
    me = _me(request)
    valid = {c["id"] for c in get_store().list_courses()}
    data = clean_selection(_json_body(request), valid)
    get_store().save_selection(me["uid"], me["email"], data)
    return JsonResponse({"ok": True, "saved": data})


def _rate_limited(uid):
    key = f"ai-rate:{uid}"
    n = cache.get(key, 0)
    if n >= settings.AI_RATE_LIMIT:
        return True
    if n == 0:
        cache.set(key, 1, 600)
    else:
        cache.incr(key)
    return False


def _ai_guard(request):
    if not ai.enabled():
        return JsonResponse({"error": "ai_unavailable"}, status=503)
    if _rate_limited(request.session["uid"]):
        return JsonResponse({"error": "rate_limited"}, status=429)
    return None


@require_POST
@school_login_required
def api_ai_depts(request):
    blocked = _ai_guard(request)
    if blocked:
        return blocked
    body = _json_body(request)
    text = str(body.get("text") or "").strip()
    major = str(body.get("major") or "")
    if not text:
        return JsonResponse({"error": "empty"}, status=400)
    try:
        return JsonResponse({"depts": ai.classify_depts(text, major if major in ai.DEPT_ZH else "406")})
    except ai.AIError as e:
        return JsonResponse({"error": e.code}, status=429 if e.code == "rate_limited" else 502)


@require_POST
@school_login_required
def api_ai_suggest(request):
    blocked = _ai_guard(request)
    if blocked:
        return blocked
    body = _json_body(request)
    text = str(body.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "empty"}, status=400)
    courses = {c["id"]: c for c in get_store().list_courses()}

    def pick(ids, limit):
        out = []
        for x in (ids if isinstance(ids, list) else [])[:limit]:
            c = courses.get(str(x))
            if c and c not in out:
                out.append({**c, "enr": int(c.get("enr", 0)) + int(c.get("registered", 0))})
        return out

    selected = pick(body.get("sel"), 60)
    sel_ids = {c["id"] for c in selected}
    candidates = [c for c in pick(body.get("cands"), 400) if c["id"] not in sel_ids and float(c["credits"]) > 0]
    if not candidates:
        return JsonResponse({"error": "no_candidates"}, status=400)
    student = clean_selection(body, set(courses))
    depts = [d for d in (body.get("depts") or []) if d in ai.DEPT_ZH][:3] or [student["major"] or "406"]
    try:
        result = ai.suggest(text, student, depts, candidates, selected, "en" if body.get("lang") == "en" else "zh")
    except ai.AIError as e:
        return JsonResponse({"error": e.code}, status=429 if e.code == "rate_limited" else 502)
    return JsonResponse(result)
