"""換課規則；Firestore 與記憶體資料層共用。"""
from .ntub_data import required_application_kind


class SwapError(ValueError):
    pass


def periods(course):
    return {(day, period) for day, start, end in course.get("slots", []) for period in range(start, end + 1)}


def swapped_selection(student, courses, old_id, new_id, expected):
    selected = (student or {}).get("sel") or []
    if set(selected) != set(expected) or old_id not in selected or new_id in selected:
        raise SwapError("selection_changed")
    if any(cid not in courses for cid in [*selected, new_id]):
        raise SwapError("course_unavailable")
    old, new = courses[old_id], courses[new_id]
    if required_application_kind(new, student.get("major")):
        raise SwapError("special_application_required")
    times = periods(new)
    if not times or periods(old) != times:
        raise SwapError("different_time")
    grade = int(student.get("grade") or 1)
    if (new["src"] == "dept" and new["grade"] > grade) or (new["src"] != "dept" and new["grade"] not in (0, grade)):
        raise SwapError("ineligible_grade")
    if int(new.get("registered", 0)) >= int(new["cap"]):
        raise SwapError("no_seats")
    if any(times & periods(courses[cid]) for cid in selected if cid != old_id):
        raise SwapError("course_conflict")
    data = {key: student[key] for key in ("major", "grade", "cls", "auto") if key in student}
    data["sel"] = [new_id if cid == old_id else cid for cid in selected]
    return data
