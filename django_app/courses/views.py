import csv
import io
import json
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import school_login_required

from . import ai
from .store import clean_selection, course_rows_for, get_store
from .student_id import student_from_email
from .teachers import courses_taught, teacher_names


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
    if teacher_names(me["email"]):
        return redirect("courses:teacher")
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


def _teacher_courses(names):
    """老師開的課，每門課附上透過本系統選課的學生（依學號排序）。"""
    store = get_store()
    courses = courses_taught(names, store.list_courses())
    ids = {c["id"] for c in courses}
    by_course = {cid: [] for cid in ids}
    for s in store.students_in_courses(ids):
        email = s.get("email") or ""
        info = student_from_email(email)
        row = {"sid": info["sid"] if info else email.split("@")[0], "name": s.get("name") or "", "email": email, "cls": s.get("cls") or ""}
        for cid in ids & set(s.get("sel") or []):
            by_course[cid].append(row)
    for c in courses:
        c["students"] = sorted(by_course[c["id"]], key=lambda r: r["sid"])
        c["slot_text"] = ai.slot_text(c["slots"])
    return courses


@school_login_required
def teacher_page(request):
    """老師端：自己開的課，以及每門課透過本系統選課的學生。"""
    names = teacher_names(_me(request)["email"])
    if not names:
        return redirect("courses:app")
    courses = _teacher_courses(names)
    return render(request, "courses/teacher.html", {
        "teacher": "、".join(names),
        "courses": courses,
        "total": sum(len(c["students"]) for c in courses),
    })


@require_GET
@school_login_required
def teacher_export(request):
    """匯出選課學生名單 CSV；?course=課程 id 只匯出那一門，沒給就匯出全部。
    加上 UTF-8 BOM，Excel 直接打開中文才不會變亂碼。"""
    names = teacher_names(_me(request)["email"])
    if not names:
        return redirect("courses:app")
    courses = _teacher_courses(names)
    only = request.GET.get("course")
    if only:
        courses = [c for c in courses if c["id"] == only]
        if not courses:
            raise Http404  # 不是這位老師的課
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["課號", "課名", "開課班級", "上課時間", "學號", "姓名", "學生班級", "信箱"])
    for c in courses:
        for s in c["students"]:
            w.writerow([c["code"], c["name"], c["cls"], c["slot_text"], s["sid"], s["name"], s["cls"], s["email"]])
    filename = f"選課名單_{courses[0]['code']}_{courses[0]['name']}.csv" if only else "選課名單_全部課程.csv"
    resp = HttpResponse("﻿" + buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f"attachment; filename=\"students.csv\"; filename*=UTF-8''{quote(filename)}"
    return resp


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
    get_store().save_selection(me["uid"], me["email"], data, me["name"])
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
