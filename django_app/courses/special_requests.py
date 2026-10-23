"""特殊申請的共用規則；審核與自動加選由資料層在同一交易完成。"""
from datetime import datetime, timezone

from .swapping import periods
from .ntub_data import required_application_kind

KINDS = {"add": "加簽", "cross_dept": "跨系選修", "prerequisite": "豁免先修"}


class RequestError(ValueError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def pending_key(course_id, kind):
    return course_id + ":" + kind


def saved_selection(current, data, expected_revision=None, courses=None):
    current = current or {}
    revision = int(current.get("revision", 0))
    approved = current.get("approved") or {}
    if expected_revision is not None and expected_revision != revision:
        raise RequestError("selection_changed")
    # 尚未重新整理的舊版頁面沒有版本號，不可把教師剛加進來的課刪掉。
    if expected_revision is None and set(approved) - set(data["sel"]):
        raise RequestError("selection_changed")
    for cid in set(data["sel"]) - set(current.get("sel") or []):
        if courses is not None and required_application_kind(courses[cid], data.get("major")):
            raise RequestError("special_application_required")
    return {**data, "revision": revision + 1,
            "approved": {cid: info for cid, info in approved.items() if cid in data["sel"]}}


def make_application(request_id, uid, email, name, student, course, kind, reason):
    if not student:
        raise RequestError("selection_not_saved")
    if not course:
        raise RequestError("course_unavailable")
    if not course.get("teacher") or course["teacher"] == "待聘":
        raise RequestError("no_teacher")
    if course["id"] in (student.get("sel") or []):
        raise RequestError("already_selected")
    if kind not in KINDS or not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
        raise RequestError("invalid_application")
    if kind == "cross_dept" and (course["src"] != "dept" or course["dept"] == student.get("major")):
        raise RequestError("not_cross_dept")
    required = required_application_kind(course, student.get("major"))
    if required and kind != required:
        raise RequestError("invalid_application")
    return {"id": request_id, "uid": uid, "email": email, "name": name, "cls": student.get("cls", ""),
            "course_id": course["id"], "course_name": course["name"], "teacher": course["teacher"],
            "kind": kind, "reason": reason.strip(), "status": "pending", "created_at": timestamp(),
            "reviewed_at": "", "reviewer": "", "reviewer_name": "", "note": ""}


def review_application(application, student, courses, names, reviewer, decision, note):
    if not application:
        raise RequestError("application_not_found")
    cid = application["course_id"]
    course = courses.get(cid)
    if not course:
        raise RequestError("course_unavailable")
    if not set(names) & {name.strip() for name in course.get("teacher", "").split(",")}:
        raise RequestError("not_course_teacher")
    if decision not in ("approve", "reject") or not isinstance(note, str) or len(note) > 1000:
        raise RequestError("invalid_decision")
    status = "approved" if decision == "approve" else "rejected"
    if application["status"] != "pending":
        if application["status"] == status:
            return application, None, False
        raise RequestError("already_reviewed")
    if not student:
        raise RequestError("student_unavailable")
    selected = list(student.get("sel") or [])
    added = False
    updated = dict(student)
    if decision == "approve":
        if cid not in selected:
            if len(selected) >= 60:
                raise RequestError("selection_limit")
            if any(course_id not in courses for course_id in selected):
                raise RequestError("course_unavailable")
            if any(periods(course) & periods(courses[course_id]) for course_id in selected):
                raise RequestError("course_conflict")
            if application["kind"] != "add" and int(course.get("registered", 0)) >= int(course["cap"]):
                raise RequestError("no_seats")
            selected.append(cid)
            added = True
        updated["sel"] = selected
        updated["approved"] = {**(student.get("approved") or {}), cid: {
            "request_id": application["id"], "kind": application["kind"]}}
        updated["revision"] = int(student.get("revision", 0)) + 1
    pending = dict(student.get("pending_requests") or {})
    key = pending_key(cid, application["kind"])
    if pending.get(key) == application["id"]:
        del pending[key]
    updated["pending_requests"] = pending
    reviewed = {**application, "status": status, "reviewed_at": timestamp(), "reviewer": reviewer,
                "reviewer_name": "、".join(names), "note": note.strip()}
    return reviewed, updated, added
