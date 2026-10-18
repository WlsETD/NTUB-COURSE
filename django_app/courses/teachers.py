"""老師帳號：學校信箱 → 授課老師姓名（data/teachers.txt）。

用老師信箱登入會進老師端（/teacher/），看到自己開的課與透過本系統選課的學生。
課程資料的授課老師欄位是姓名（多位老師用逗號分隔），所以用姓名對應。
.env 的 TEACHER_EXTRA 可以再加帳號（例如示範用），格式：信箱=姓名,信箱=姓名
"""
from functools import lru_cache

from django.conf import settings

ROSTER_PATH = settings.BASE_DIR / "data" / "teachers.txt"


@lru_cache(maxsize=1)
def _roster():
    out = {}
    with open(ROSTER_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, email = (x.strip() for x in line.split("|")[:2])
            out.setdefault(email.lower(), []).append(name)
    return out


def _extra():
    out = {}
    for pair in settings.TEACHER_EXTRA.split(","):
        email, _, name = pair.partition("=")
        if email.strip() and name.strip():
            out.setdefault(email.strip().lower(), []).append(name.strip())
    return out


def teacher_names(email):
    """這個信箱對應的老師姓名；不是老師回傳空串列。同一個信箱可能對到多位老師。"""
    email = (email or "").strip().lower()
    names = _roster().get(email, []) + _extra().get(email, [])
    return list(dict.fromkeys(names))


def courses_taught(names, courses):
    names = set(names)
    return [c for c in courses if names & {t.strip() for t in str(c.get("teacher") or "").split(",")}]
