"""資料存取層：課程與學生選課都存在 Firestore。

Firestore 結構
- courses/{課程 id}：課程資料（課名、老師、時間、名額…），另有 registered = 透過本系統登記的人數
- students/{Firebase uid}：email、name、major、grade、cls、sel（已選課程 id）、auto（自動帶入的必修）、updatedAt

所有讀寫都由 Django 伺服器用 Admin SDK 進行，瀏覽器不直接連 Firestore（見 firestore.rules）。
STORE=memory 時改用記憶體，給自動測試使用。
"""
import threading

from django.conf import settings
from django.core.cache import cache

from .ntub_data import FIELDS, load_rows, to_dict

COURSE_CACHE_KEY = "courses:v1"
COURSE_CACHE_SECONDS = 120
MAX_SELECTED = 60


def _slots_to_fs(slots):
    # Firestore 不能存「陣列裡的陣列」，所以把 [星期, 起, 迄] 改成 map
    return [{"d": d, "s": s, "e": e} for d, s, e in slots]


def _slots_from_fs(slots):
    return [[x["d"], x["s"], x["e"]] for x in slots or []]


def clean_selection(data, valid_ids):
    """只留下合法的欄位與課程 id。"""
    def ids(key):
        out = []
        for x in data.get(key) or []:
            x = str(x)
            if x in valid_ids and x not in out:
                out.append(x)
        return out[:MAX_SELECTED]

    sel = ids("sel")
    auto = ids("auto")
    try:
        grade = int(data.get("grade"))
    except (TypeError, ValueError):
        grade = 1
    return {
        "major": str(data.get("major") or "")[:8],
        "grade": min(max(grade, 1), 4),
        "cls": str(data.get("cls") or "")[:40],
        "sel": sel,
        "auto": auto,
    }


class FirestoreStore:
    def __init__(self):
        from .firebase import db
        self._db = db

    def list_courses(self):
        cached = cache.get(COURSE_CACHE_KEY)
        if cached is not None:
            return cached
        out = []
        for snap in self._db().collection("courses").stream():
            d = snap.to_dict()
            d["id"] = snap.id
            d["slots"] = _slots_from_fs(d.get("slots"))
            d.setdefault("registered", 0)
            out.append(d)
        out.sort(key=lambda c: int(c.get("order", 0)))
        cache.set(COURSE_CACHE_KEY, out, COURSE_CACHE_SECONDS)
        return out

    def get_student(self, uid):
        snap = self._db().collection("students").document(uid).get()
        return snap.to_dict() if snap.exists else None

    def save_selection(self, uid, email, data, name=""):
        from firebase_admin import firestore

        client = self._db()
        student_ref = client.collection("students").document(uid)
        courses = client.collection("courses")

        @firestore.transactional
        def txn(transaction):
            snap = student_ref.get(transaction=transaction)
            old = set((snap.to_dict() or {}).get("sel") or []) if snap.exists else set()
            new = set(data["sel"])
            # 登記人數：新加的 +1、退掉的 -1；在同一個 transaction 裡，不會算錯
            for cid in new - old:
                transaction.update(courses.document(cid), {"registered": firestore.Increment(1)})
            for cid in old - new:
                transaction.update(courses.document(cid), {"registered": firestore.Increment(-1)})
            transaction.set(student_ref, {**data, "email": email, "name": name, "updatedAt": firestore.SERVER_TIMESTAMP}, merge=True)

        txn(client.transaction())
        cache.delete(COURSE_CACHE_KEY)
        return data

    def students_in_courses(self, course_ids):
        """選了其中任何一門課的學生（老師端用）。array_contains_any 一次最多 30 個值，所以分批查。"""
        from google.cloud.firestore_v1.base_query import FieldFilter

        ids, out = list(course_ids), {}
        col = self._db().collection("students")
        for i in range(0, len(ids), 30):
            for snap in col.where(filter=FieldFilter("sel", "array_contains_any", ids[i:i + 30])).stream():
                out[snap.id] = {**snap.to_dict(), "uid": snap.id}
        return list(out.values())

    def seed_courses(self, rows, reset_counts=False):
        client = self._db()
        batch, n = client.batch(), 0
        for order, row in enumerate(rows):
            d = to_dict(row)
            cid = d.pop("id")
            d["slots"] = _slots_to_fs(d["slots"])
            d["order"] = order
            if reset_counts:
                d["registered"] = 0
            ref = client.collection("courses").document(cid)
            batch.set(ref, d, merge=True)
            n += 1
            if n % 400 == 0:  # 一個 batch 最多 500 筆
                batch.commit()
                batch = client.batch()
        batch.commit()
        if not reset_counts:
            # 新課程補上 registered 欄位，舊課程保留原本的人數
            for snap in client.collection("courses").stream():
                if "registered" not in (snap.to_dict() or {}):
                    snap.reference.update({"registered": 0})
        cache.delete(COURSE_CACHE_KEY)
        return n


class MemoryStore:
    """測試用：資料放在記憶體，伺服器重啟就消失。"""

    def __init__(self):
        self.lock = threading.Lock()
        self.courses = {}
        self.students = {}
        self.seed_courses(load_rows(), reset_counts=True)

    def list_courses(self):
        return [dict(c) for c in sorted(self.courses.values(), key=lambda c: c["order"])]

    def get_student(self, uid):
        s = self.students.get(uid)
        return dict(s) if s else None

    def save_selection(self, uid, email, data, name=""):
        with self.lock:
            old = set((self.students.get(uid) or {}).get("sel") or [])
            new = set(data["sel"])
            for cid in new - old:
                self.courses[cid]["registered"] += 1
            for cid in old - new:
                self.courses[cid]["registered"] -= 1
            self.students[uid] = {**data, "email": email, "name": name}
        return data

    def students_in_courses(self, course_ids):
        ids = set(course_ids)
        return [{**s, "uid": uid} for uid, s in self.students.items() if ids & set(s.get("sel") or [])]

    def seed_courses(self, rows, reset_counts=False):
        for order, row in enumerate(rows):
            d = to_dict(row)
            prev = self.courses.get(d["id"], {})
            d["order"] = order
            d["registered"] = 0 if reset_counts else prev.get("registered", 0)
            self.courses[d["id"]] = d
        return len(rows)


_store = None
_store_lock = threading.Lock()


def get_store():
    global _store
    with _store_lock:
        if _store is None:
            _store = MemoryStore() if settings.STORE == "memory" else FirestoreStore()
        return _store


def reset_store_for_tests():
    global _store
    _store = None


def course_rows_for(student_sel=()):
    """給前端的 RAW：已選人數 = 原始快照 + 本系統登記人數（扣掉這位學生自己，前端會再加回來）。"""
    mine = set(student_sel)
    rows = []
    for c in get_store().list_courses():
        enr = int(c.get("enr", 0)) + int(c.get("registered", 0)) - (1 if c["id"] in mine else 0)
        row = [c[f] for f in FIELDS]
        row[FIELDS.index("enr")] = max(enr, 0)
        rows.append(row)
    return rows
