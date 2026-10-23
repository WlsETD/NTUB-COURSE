"""資料存取層：課程與學生選課都存在 Firestore。

Firestore 結構
- courses/{課程 id}：課程資料、registered（本系統登記人數），可選填 approval_kind（需教師審核的類型）
- students/{Firebase uid}：email、name、major、grade、cls、sel（已選課程 id）、auto（自動帶入的必修）、updatedAt
- special_requests/{申請 id}：特殊申請內容、審核狀態及教師回覆

所有讀寫都由 Django 伺服器用 Admin SDK 進行，瀏覽器不直接連 Firestore（見 firestore.rules）。
STORE=memory 時改用記憶體，給自動測試使用。
"""
import threading
import uuid
from copy import deepcopy

from django.conf import settings
from django.core.cache import cache

from .ntub_data import FIELDS, load_rows, to_dict
from .swapping import swapped_selection
from .special_requests import RequestError, make_application, pending_key, review_application, saved_selection

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

    def save_selection(self, uid, email, data, name="", expected_revision=None):
        from firebase_admin import firestore

        client = self._db()
        student_ref = client.collection("students").document(uid)
        courses = client.collection("courses")

        @firestore.transactional
        def txn(transaction):
            snap = student_ref.get(transaction=transaction)
            current = snap.to_dict() if snap.exists else {}
            saved = saved_selection(current, data, expected_revision)
            old = set(current.get("sel") or [])
            new = set(saved["sel"])
            added = {}
            if new - old:
                for course in client.get_all([courses.document(cid) for cid in new - old], transaction=transaction):
                    if course.exists:
                        added[course.id] = course.to_dict()
                if set(added) != new - old:
                    raise RequestError("course_unavailable")
            saved = saved_selection(current, data, expected_revision, added)
            # 登記人數：新加的 +1、退掉的 -1；在同一個 transaction 裡，不會算錯
            for cid in new - old:
                transaction.update(courses.document(cid), {"registered": firestore.Increment(1)})
            for cid in old - new:
                transaction.update(courses.document(cid), {"registered": firestore.Increment(-1)})
            payload = {**saved, "email": email, "name": name, "updatedAt": firestore.SERVER_TIMESTAMP}
            transaction.set(student_ref, payload, merge=list(payload))
            return saved

        data = txn(client.transaction())
        cache.delete(COURSE_CACHE_KEY)
        return data

    def swap_course(self, uid, email, old_id, new_id, expected, name=""):
        from firebase_admin import firestore

        client = self._db()
        student_ref = client.collection("students").document(uid)
        courses = client.collection("courses")

        @firestore.transactional
        def txn(transaction):
            snap = student_ref.get(transaction=transaction)
            student = snap.to_dict() if snap.exists else {}
            ids = set(student.get("sel") or []) | {old_id, new_id}
            snapshots = client.get_all([courses.document(cid) for cid in ids], transaction=transaction)
            current = {}
            for course in snapshots:
                if course.exists:
                    data = course.to_dict()
                    data["slots"] = _slots_from_fs(data.get("slots"))
                    current[course.id] = data
            data = swapped_selection(student, current, old_id, new_id, expected)
            data = saved_selection(student, data, student.get("revision", 0))
            # 先完成所有讀取與檢查，再在同一交易更新兩門課和學生；失敗不會退掉原課。
            transaction.update(courses.document(old_id), {"registered": max(0, int(current[old_id].get("registered", 0)) - 1)})
            transaction.update(courses.document(new_id), {"registered": int(current[new_id].get("registered", 0)) + 1})
            payload = {**data, "email": email, "name": name, "updatedAt": firestore.SERVER_TIMESTAMP}
            transaction.set(student_ref, payload, merge=list(payload))
            return data

        data = txn(client.transaction())
        cache.delete(COURSE_CACHE_KEY)
        return data

    def list_applications(self, uid=None, course_ids=None):
        from google.cloud.firestore_v1.base_query import FieldFilter

        collection = self._db().collection("special_requests")
        if uid is not None:
            snapshots = collection.where(filter=FieldFilter("uid", "==", uid)).stream()
            out = [snap.to_dict() for snap in snapshots]
        else:
            ids, out = list(course_ids or []), []
            for i in range(0, len(ids), 30):
                out.extend(snap.to_dict() for snap in collection.where(filter=FieldFilter("course_id", "in", ids[i:i + 30])).stream())
        return sorted(out, key=lambda app: (app["status"] == "pending", app["created_at"]), reverse=True)

    def submit_application(self, uid, email, name, course_id, kind, reason):
        from firebase_admin import firestore

        client = self._db()
        student_ref = client.collection("students").document(uid)
        course_ref = client.collection("courses").document(course_id)
        requests = client.collection("special_requests")
        new_ref = requests.document(uuid.uuid4().hex)

        @firestore.transactional
        def txn(transaction):
            student = student_ref.get(transaction=transaction).to_dict()
            snap = course_ref.get(transaction=transaction)
            course = {**snap.to_dict(), "id": snap.id} if snap.exists else None
            application = make_application(new_ref.id, uid, email, name, student, course, kind, reason)
            key = pending_key(course_id, kind)
            pending = dict(student.get("pending_requests") or {})
            if pending.get(key):
                existing = requests.document(pending[key]).get(transaction=transaction)
                if existing.exists and existing.to_dict()["status"] == "pending":
                    return existing.to_dict()
            pending[key] = new_ref.id
            transaction.set(new_ref, application)
            transaction.set(student_ref, {"pending_requests": pending}, merge=True)
            return application

        return txn(client.transaction())

    def review_application(self, request_id, names, reviewer, decision, note):
        from firebase_admin import firestore

        client = self._db()
        request_ref = client.collection("special_requests").document(request_id)

        @firestore.transactional
        def txn(transaction):
            application = request_ref.get(transaction=transaction).to_dict()
            if not application:
                raise RequestError("application_not_found")
            student_ref = client.collection("students").document(application["uid"])
            student = student_ref.get(transaction=transaction).to_dict()
            ids = set((student or {}).get("sel") or []) | {application["course_id"]}
            refs = [client.collection("courses").document(cid) for cid in ids]
            courses = {}
            for snap in client.get_all(refs, transaction=transaction):
                if snap.exists:
                    course = snap.to_dict()
                    course["slots"] = _slots_from_fs(course.get("slots"))
                    courses[snap.id] = course
            reviewed, updated, added = review_application(application, student, courses, names, reviewer, decision, note)
            if updated is not None:
                if added:
                    transaction.update(client.collection("courses").document(application["course_id"]), {"registered": firestore.Increment(1)})
                updated["updatedAt"] = firestore.SERVER_TIMESTAMP
                transaction.set(student_ref, updated, merge=list(updated))
                transaction.set(request_ref, reviewed)
            return reviewed

        application = txn(client.transaction())
        cache.delete(COURSE_CACHE_KEY)
        return application

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
        self.applications = {}
        self.seed_courses(load_rows(), reset_counts=True)

    def list_courses(self):
        return [dict(c) for c in sorted(self.courses.values(), key=lambda c: c["order"])]

    def get_student(self, uid):
        s = self.students.get(uid)
        return dict(s) if s else None

    def save_selection(self, uid, email, data, name="", expected_revision=None):
        with self.lock:
            return self._save_selection(uid, email, data, name, expected_revision)

    def _save_selection(self, uid, email, data, name, expected_revision=None):
        current = self.students.get(uid) or {}
        data = saved_selection(current, data, expected_revision, self.courses)
        old = set(current.get("sel") or [])
        new = set(data["sel"])
        for cid in new - old:
            self.courses[cid]["registered"] += 1
        for cid in old - new:
            self.courses[cid]["registered"] -= 1
        self.students[uid] = {**current, **data, "email": email, "name": name}
        return data

    def swap_course(self, uid, email, old_id, new_id, expected, name=""):
        with self.lock:
            data = swapped_selection(self.students.get(uid), self.courses, old_id, new_id, expected)
            data = self._save_selection(uid, email, data, name, self.students[uid].get("revision", 0))
        return data

    def list_applications(self, uid=None, course_ids=None):
        ids = set(course_ids or [])
        with self.lock:
            out = [deepcopy(app) for app in self.applications.values()
                   if (app["uid"] == uid if uid is not None else app["course_id"] in ids)]
        return sorted(out, key=lambda app: (app["status"] == "pending", app["created_at"]), reverse=True)

    def submit_application(self, uid, email, name, course_id, kind, reason):
        with self.lock:
            student = self.students.get(uid)
            application = make_application(uuid.uuid4().hex, uid, email, name, student, self.courses.get(course_id), kind, reason)
            key = pending_key(course_id, kind)
            pending = dict(student.get("pending_requests") or {})
            existing = self.applications.get(pending.get(key))
            if existing and existing["status"] == "pending":
                return deepcopy(existing)
            pending[key] = application["id"]
            student["pending_requests"] = pending
            self.applications[application["id"]] = application
            return deepcopy(application)

    def review_application(self, request_id, names, reviewer, decision, note):
        with self.lock:
            application = self.applications.get(request_id)
            student = self.students.get(application["uid"]) if application else None
            reviewed, updated, added = review_application(application, student, self.courses, names, reviewer, decision, note)
            if updated is not None:
                if added:
                    self.courses[application["course_id"]]["registered"] += 1
                self.students[application["uid"]] = updated
                self.applications[request_id] = reviewed
            return deepcopy(reviewed)

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
    """給前端的 RAW：已選人數 = 本系統實際登記人數（扣掉這位學生自己，前端會再加回來）。
    學校原始資料裡的已選人數是舊快照，不是這個系統的學生，所以不算進來。"""
    mine = set(student_sel)
    rows = []
    for c in get_store().list_courses():
        enr = int(c.get("registered", 0)) - (1 if c["id"] in mine else 0)
        row = [c[f] for f in FIELDS]
        row[FIELDS.index("enr")] = max(enr, 0)
        row.append(c.get("approval_kind", ""))
        rows.append(row)
    return rows
