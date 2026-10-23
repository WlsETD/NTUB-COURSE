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
from .autoreq import default_selection
from .store import MAX_SELECTED, clean_selection, course_rows_for, get_store
from .swapping import SwapError, periods
from .special_requests import KINDS, RequestError
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
    store = get_store()
    saved = store.get_student(me["uid"])
    student = student_from_email(me["email"])
    # 學號判斷出本系、年級，但還沒存過（或存的是別系／別年級）：伺服器直接帶入本班必修並存檔，老師端馬上看得到
    if student and student["dept"] and (not saved or saved.get("major") != student["dept"] or saved.get("grade") != student["grade"]):
        default = default_selection(store.list_courses(), student["dept"], student["grade"])
        if default:
            approved = [cid for cid in (saved or {}).get("sel", []) if cid in ((saved or {}).get("approved") or {})]
            if approved:
                courses = {c["id"]: c for c in store.list_courses()}
                approved = [cid for cid in approved if cid in courses]
                default["sel"] = approved + [cid for cid in default["sel"] if cid not in approved
                    and not any(periods(courses[cid]) & periods(courses[aid]) for aid in approved)]
            try:
                data = store.save_selection(me["uid"], me["email"], default, me["name"], (saved or {}).get("revision", 0))
                saved = {**(saved or {}), **data}
            except RequestError:
                saved = store.get_student(me["uid"])
    sel = (saved or {}).get("sel") or []
    boot = {
        "email": me["email"],
        # 頁首的「歡迎，{名字}」；Google 帳號沒有名字時用信箱 @ 前面的部分
        "name": me["name"] or me["email"].split("@")[0],
        # 從學號判斷的學制、科系、年級；前端用它自動帶入本系本班的必修
        "student": student,
        "saved": {k: saved[k] for k in ("major", "grade", "cls", "sel", "auto", "approved", "revision") if k in saved} if saved else None,
        "applications": store.list_applications(uid=me["uid"]),
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
            if all(r["email"] != email for r in by_course[cid]):  # 同一個信箱只列一次
                by_course[cid].append({**row, "approved": cid in (s.get("approved") or {})})
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
    applications = get_store().list_applications(course_ids=[c["id"] for c in courses])
    return render(request, "courses/teacher.html", {
        "teacher": "、".join(names),
        "courses": courses,
        "total": sum(len(c["students"]) for c in courses),
        "applications": applications,
        "pending_count": sum(app["status"] == "pending" for app in applications),
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
    store = get_store()
    return JsonResponse({"email": me["email"], "name": me["name"], "saved": store.get_student(me["uid"]),
                         "applications": store.list_applications(uid=me["uid"])}, json_dumps_params={"default": str})


@require_POST
@school_login_required
def api_selection(request):
    """儲存選課（每次加選、退選後由前端自動呼叫）。"""
    me = _me(request)
    if teacher_names(me["email"]):  # 老師帳號不選課，也不能寫入選課資料
        return JsonResponse({"error": "teacher_account"}, status=403)
    valid = {c["id"] for c in get_store().list_courses()}
    body = _json_body(request)
    revision = body.get("revision")
    if revision is not None and (type(revision) is not int or revision < 0):
        return JsonResponse({"error": "invalid_revision"}, status=400)
    data = clean_selection(body, valid)
    student = student_from_email(me["email"])
    if student and student["dept"] and (data["major"] != student["dept"] or data["grade"] != student["grade"]):
        return JsonResponse({"error": "invalid_student_profile"}, status=400)
    try:
        data = get_store().save_selection(me["uid"], me["email"], data, me["name"], revision)
    except RequestError as error:
        return JsonResponse({"error": str(error), "saved": get_store().get_student(me["uid"])}, status=409, json_dumps_params={"default": str})
    return JsonResponse({"ok": True, "saved": data})


@require_POST
@school_login_required
def api_swap(request):
    me = _me(request)
    if teacher_names(me["email"]):
        return JsonResponse({"error": "teacher_account"}, status=403)
    body = _json_body(request)
    old_id, new_id, expected = body.get("old"), body.get("new"), body.get("expected")
    if (not isinstance(old_id, str) or not isinstance(new_id, str) or not old_id or not new_id
            or len(old_id) > 40 or len(new_id) > 40 or "/" in old_id or "/" in new_id or not isinstance(expected, list)
            or len(expected) > MAX_SELECTED or any(not isinstance(cid, str) or len(cid) > 40 for cid in expected)):
        return JsonResponse({"error": "invalid_swap"}, status=400)
    try:
        data = get_store().swap_course(me["uid"], me["email"], old_id, new_id, expected, me["name"])
    except (SwapError, RequestError) as error:
        return JsonResponse({"error": str(error)}, status=409)
    return JsonResponse({"ok": True, "saved": data})


@require_POST
@school_login_required
def api_apply(request):
    me = _me(request)
    if teacher_names(me["email"]):
        return JsonResponse({"error": "teacher_account"}, status=403)
    body = _json_body(request)
    cid, kind, reason = body.get("course_id"), body.get("kind"), body.get("reason")
    if (not isinstance(cid, str) or not cid or len(cid) > 40 or "/" in cid or not isinstance(kind, str)
            or kind not in KINDS or not isinstance(reason, str) or not reason.strip() or len(reason) > 1000):
        return JsonResponse({"error": "invalid_application"}, status=400)
    try:
        application = get_store().submit_application(me["uid"], me["email"], me["name"], cid, kind, reason)
    except RequestError as error:
        return JsonResponse({"error": str(error)}, status=409)
    return JsonResponse({"ok": True, "application": application})


@require_POST
@school_login_required
def api_review(request, request_id):
    me = _me(request)
    names = teacher_names(me["email"])
    if not names:
        return JsonResponse({"error": "not_teacher"}, status=403)
    if len(request_id) > 64:
        return JsonResponse({"error": "application_not_found"}, status=404)
    body = _json_body(request)
    decision, note = body.get("decision"), body.get("note", "")
    if decision not in ("approve", "reject") or not isinstance(note, str) or len(note) > 1000:
        return JsonResponse({"error": "invalid_decision"}, status=400)
    try:
        application = get_store().review_application(request_id, names, me["email"], decision, note)
    except RequestError as error:
        code = str(error)
        return JsonResponse({"error": code}, status=403 if code == "not_course_teacher" else 404 if code == "application_not_found" else 409)
    return JsonResponse({"ok": True, "application": application})


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
                out.append({**c, "enr": int(c.get("registered", 0))})
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
