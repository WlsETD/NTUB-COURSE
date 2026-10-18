"""本班必修自動帶入（伺服器版）。規則和 app.js 的 classesFor()、autoReq() 一樣，兩邊改的時候要一起改。

學生載入選課頁時由伺服器直接算好並存進 Firestore，不靠前端 JS 存檔，
這樣老師端一定看得到自動帶入的必修。
"""
import re

_CLASS_ORDER = "甲乙丙丁"
_GROUP_SECTION = re.compile(r"組\)")  # 分組專題（A組、B組…）留給學生自己選


def classes_for(courses, dept, grade):
    out = []
    for c in courses:
        if c["src"] == "dept" and c["dept"] == dept and c["grade"] == grade and c["cls"] not in out:
            out.append(c["cls"])
    return sorted(out, key=lambda x: _CLASS_ORDER.find(x[-2:-1]))


def _overlap(a, b):
    return any(x[0] == y[0] and x[1] <= y[2] and y[1] <= x[2] for x in a["slots"] for y in b["slots"])


def auto_required(courses, cls):
    """這個班級的必修課 id（同一個課號只取一班、時間衝突的跳過），順序和前端一樣。"""
    out, codes, by_id = [], set(), {}
    for c in courses:
        if c["src"] != "dept" or c["cls"] != cls or c["cat"] != "req" or _GROUP_SECTION.search(c["name"]) or c["code"] in codes:
            continue
        if any(_overlap(by_id[i], c) for i in out):
            continue
        codes.add(c["code"])
        out.append(c["id"])
        by_id[c["id"]] = c
    return out


def default_selection(courses, dept, grade):
    """學號判斷出的本系、年級 → 第一個班級的選課資料（格式同 clean_selection）。沒有班級資料回傳 None。"""
    cl = classes_for(courses, dept, grade)
    if not cl:
        return None
    sel = auto_required(courses, cl[0])
    return {"major": dept, "grade": grade, "cls": cl[0], "sel": sel, "auto": list(sel)}
