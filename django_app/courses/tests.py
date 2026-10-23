"""自動測試：python manage.py test（或 uv run python manage.py test）

測試不會連到真的 Firebase 或 OpenAI：資料改存在記憶體（STORE=memory），
Firebase 的 token 驗證與 OpenAI 的回覆都用假的。
"""
import json
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from courses import ai, store
from courses.swapping import SwapError

SCHOOL_CLAIMS = {"uid": "u1", "email": "s1@ntub.edu.tw", "email_verified": True, "name": "測試學生", "firebase": {"sign_in_provider": "google.com"}}


@override_settings(STORE="memory", OPENAI_API_KEY="", AI_RATE_LIMIT=3)
class Base(SimpleTestCase):
    def setUp(self):
        store.reset_store_for_tests()
        cache.clear()

    def login(self, claims=SCHOOL_CLAIMS):
        with mock.patch("accounts.views.fb_auth.verify_id_token", return_value=claims), mock.patch("accounts.views.get_app"):
            return self.client.post("/auth/session/", json.dumps({"idToken": "fake"}), content_type="application/json")

    def post(self, url, body):
        return self.client.post(url, json.dumps(body), content_type="application/json")


class LoginTests(Base):
    def test_login_page(self):
        r = self.client.get("/")
        self.assertContains(r, "使用 Google 學校帳號登入")

    def test_app_requires_login(self):
        self.assertRedirects(self.client.get("/app/"), "/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/api/me/").status_code, 401)

    def test_school_account_can_sign_in(self):
        r = self.login()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/api/me/").json()["email"], "s1@ntub.edu.tw")
        self.assertRedirects(self.client.get("/"), "/app/", fetch_redirect_response=False)

    def test_gmail_is_rejected(self):
        r = self.login({**SCHOOL_CLAIMS, "email": "someone@gmail.com"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"], "not_school_account")

    def test_unverified_or_password_account_rejected(self):
        self.assertEqual(self.login({**SCHOOL_CLAIMS, "email_verified": False}).status_code, 403)
        self.assertEqual(self.login({**SCHOOL_CLAIMS, "firebase": {"sign_in_provider": "password"}}).status_code, 403)

    def test_bad_token(self):
        with mock.patch("accounts.views.fb_auth.verify_id_token", side_effect=ValueError("bad")), mock.patch("accounts.views.get_app"):
            r = self.post("/auth/session/", {"idToken": "x"})
        self.assertEqual(r.status_code, 401)

    def test_csrf_required(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        r = c.post("/auth/session/", json.dumps({"idToken": "x"}), content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_logout(self):
        self.login()
        self.post("/auth/logout/", {})
        self.assertEqual(self.client.get("/api/me/").status_code, 401)


class SelectionTests(Base):
    def test_app_page_embeds_courses(self):
        self.login()
        r = self.client.get("/app/")
        self.assertContains(r, 'id="raw-data"')
        self.assertContains(r, "courses/app.js")
        self.assertEqual(len(r.context["courses"]), 748)
        self.assertIsNone(r.context["boot"]["saved"])
        self.assertEqual(r.context["boot"]["name"], "測試學生")

    def test_save_and_restore(self):
        self.login()
        r = self.post("/api/selection/", {"major": "402", "grade": 3, "cls": "財金三年甲班", "sel": ["s1", "s2", "nope", "s1"], "auto": ["s1"]})
        self.assertEqual(r.json()["saved"]["sel"], ["s1", "s2"])  # 不存在與重複的 id 被濾掉
        boot = self.client.get("/app/").context["boot"]
        self.assertEqual(boot["saved"]["major"], "402")
        self.assertEqual(boot["saved"]["sel"], ["s1", "s2"])

    def test_registered_counts(self):
        st = store.get_store()
        self.login()
        self.post("/api/selection/", {"major": "406", "grade": 2, "sel": ["s1", "s2"]})
        self.assertEqual(st.courses["s1"]["registered"], 1)
        # 另一位學生也選 s1
        self.post("/auth/logout/", {})
        self.login({**SCHOOL_CLAIMS, "uid": "u2", "email": "s2@ntub.edu.tw"})
        self.post("/api/selection/", {"major": "406", "grade": 2, "sel": ["s1"]})
        self.assertEqual(st.courses["s1"]["registered"], 2)
        # u2 看到的人數不含自己（前端會自己 +1），u2 退選後人數減 1
        rows = {r[0]: r for r in self.client.get("/app/").context["courses"]}
        self.assertEqual(rows["s1"][12], 1)  # 只算實際登記的學生，不含學校舊快照
        self.post("/api/selection/", {"major": "406", "grade": 2, "sel": []})
        self.assertEqual(st.courses["s1"]["registered"], 1)
        self.assertEqual(st.courses["s2"]["registered"], 1)

    def test_selection_requires_login(self):
        self.assertEqual(self.post("/api/selection/", {"sel": ["s1"]}).status_code, 401)


class AITests(Base):
    def test_ai_hidden_without_key(self):
        self.login()
        self.assertFalse(self.client.get("/app/").context["boot"]["ai"])
        self.assertEqual(self.post("/api/ai/depts/", {"text": "財務", "major": "406"}).status_code, 503)

    @override_settings(OPENAI_API_KEY="sk-test")
    def test_classify_and_suggest(self):
        self.login()
        with mock.patch("courses.ai.ask_json", return_value={"depts": ["402", "403", "999", "402"]}) as m:
            r = self.post("/api/ai/depts/", {"text": "我想修財務相關的課", "major": "406"})
        self.assertEqual(r.json()["depts"], ["402", "403"])  # 無效與重複的代碼被濾掉
        self.assertIn("財務", m.call_args[0][0])

        fake = {"summary": "建議", "picks": [{"id": "s5", "reason": "相關"}, {"id": "s999", "reason": "不在清單"}, {"id": "s5", "reason": "重複"}], "notes": ["注意"]}
        with mock.patch("courses.ai.ask_json", return_value=fake) as m:
            r = self.post("/api/ai/suggest/", {"text": "財務", "major": "406", "grade": 2, "cls": "資管二年甲班", "depts": ["402"], "sel": ["s1"], "cands": ["s5", "s6"], "lang": "zh"})
        data = r.json()
        self.assertEqual([p["id"] for p in data["picks"]], ["s5"])
        prompt = m.call_args[0][0]
        self.assertIn("s5|", prompt)
        self.assertNotIn("s1|", prompt)  # 已選課程不會出現在候選清單

    @override_settings(OPENAI_API_KEY="sk-test")
    def test_rate_limit(self):
        self.login()
        with mock.patch("courses.ai.ask_json", return_value={"depts": ["406"]}):
            codes = [self.post("/api/ai/depts/", {"text": "x", "major": "406"}).status_code for _ in range(4)]
        self.assertEqual(codes, [200, 200, 200, 429])

    @override_settings(OPENAI_API_KEY="sk-test")
    def test_openai_error_mapped(self):
        self.login()
        with mock.patch("courses.ai.ask_json", side_effect=ai.AIError("ai_unavailable")):
            r = self.post("/api/ai/suggest/", {"text": "x", "major": "406", "grade": 2, "cands": ["s5"]})
        self.assertEqual(r.json()["error"], "ai_unavailable")

    def test_slot_text(self):
        self.assertEqual(ai.slot_text([[3, 2, 4], [5, 1, 1]]), "週三 2–4節、週五 第1節")


class StudentIdTests(SimpleTestCase):
    def test_day_four_year(self):
        from courses.student_id import parse_student_id
        s = parse_student_id("11446001")
        self.assertEqual((s["dept"], s["grade"], s["programName"]), ("406", 2, "四技"))
        self.assertEqual(parse_student_id("115406012")["dept"], "406")  # 科系前多一個 0
        self.assertEqual(parse_student_id("1154A001")["dept"], "40A")
        self.assertEqual(parse_student_id("11541001")["grade"], 1)
        self.assertEqual(parse_student_id("10941001")["grade"], 4)  # 延畢算大四

    def test_unsupported(self):
        from courses.student_id import parse_student_id
        self.assertIsNone(parse_student_id("s1"))
        self.assertIsNone(parse_student_id("N1134001"))  # 進修部
        self.assertIsNone(parse_student_id("11648001"))  # 還沒入學的學年度、不存在的科系
        two = parse_student_id("11436001")  # 二技：知道學制，但課程資料沒有二技
        self.assertEqual((two["programName"], two["dept"]), ("二技", None))


class StudentBootTests(Base):
    def test_boot_has_student(self):
        self.login({**SCHOOL_CLAIMS, "email": "11446001@ntub.edu.tw"})
        self.assertEqual(self.client.get("/app/").context["boot"]["student"]["dept"], "406")

    def test_boot_without_student_id(self):
        self.login()
        self.assertIsNone(self.client.get("/app/").context["boot"]["student"])


class TeacherTests(Base):
    TEACHER = {**SCHOOL_CLAIMS, "uid": "t1", "email": "sckuai@ntub.edu.tw", "name": "蒯思齊"}

    def test_roster(self):
        from courses.teachers import teacher_names
        self.assertEqual(teacher_names("SCKuai@ntub.edu.tw"), ["蒯思齊"])
        self.assertEqual(teacher_names("shli@ntub.edu.tw"), ["李淑華", "李興漢"])  # 同一個信箱對到兩位老師
        self.assertEqual(teacher_names("s1@ntub.edu.tw"), [])

    def test_teacher_sees_students(self):
        from courses.teachers import courses_taught
        cid = courses_taught(["蒯思齊"], store.get_store().list_courses())[0]["id"]
        self.login({**SCHOOL_CLAIMS, "email": "11446001@ntub.edu.tw"})
        self.post("/api/selection/", {"major": "406", "grade": 2, "cls": "資管二年甲班", "sel": [cid]})
        self.client.post("/auth/logout/")
        self.login(self.TEACHER)
        self.assertRedirects(self.client.get("/app/"), "/teacher/", fetch_redirect_response=False)
        r = self.client.get("/teacher/")
        self.assertContains(r, "11446001")
        self.assertContains(r, "測試學生")
        course = next(c for c in r.context["courses"] if c["id"] == cid)
        self.assertEqual([s["sid"] for s in course["students"]], ["11446001"])

    def test_student_cannot_open_teacher_page(self):
        self.login()
        self.assertRedirects(self.client.get("/teacher/"), "/app/", fetch_redirect_response=False)

    @override_settings(TEACHER_EXTRA="demo@ntub.edu.tw=林俊杰")
    def test_extra_teacher(self):
        from courses.teachers import teacher_names
        self.assertEqual(teacher_names("demo@ntub.edu.tw"), ["林俊杰"])


class DevLoginTests(Base):
    def dev(self, email):
        return self.post("/dev/login/", {"email": email, "name": "測試"})

    def test_off_in_production(self):
        self.assertEqual(self.dev("sckuai@ntub.edu.tw").status_code, 404)  # 測試預設 DEBUG=False
        self.assertEqual(self.client.get("/teacher/").status_code, 302)

    @override_settings(DEBUG=True)
    def test_debug_login(self):
        self.assertEqual(self.dev("me@gmail.com").status_code, 403)
        self.assertEqual(self.dev("sckuai@ntub.edu.tw").status_code, 200)
        self.assertEqual(self.client.get("/teacher/").status_code, 200)


class TeacherExportTests(Base):
    def setUp(self):
        super().setUp()
        from courses.teachers import courses_taught
        all_courses = store.get_store().list_courses()
        self.cid = courses_taught(["蒯思齊"], all_courses)[0]["id"]
        self.other = courses_taught(["林俊杰"], all_courses)[0]["id"]
        self.login({**SCHOOL_CLAIMS, "email": "11446001@ntub.edu.tw"})
        self.post("/api/selection/", {"major": "406", "grade": 2, "cls": "資管二年甲班", "sel": [self.cid]})

    def test_student_cannot_export(self):
        self.assertEqual(self.client.get("/teacher/export.csv").status_code, 302)

    def test_export(self):
        self.client.post("/auth/logout/")
        self.login(TeacherTests.TEACHER)
        r = self.client.get("/teacher/export.csv")
        text = r.content.decode("utf-8")
        self.assertTrue(text.startswith("\ufeff課號,課名"))  # BOM：Excel 開中文不亂碼
        self.assertIn("11446001,測試學生,資管二年甲班,11446001@ntub.edu.tw", text)
        self.assertIn("attachment", r["Content-Disposition"])
        one = self.client.get("/teacher/export.csv", {"course": self.cid})
        self.assertIn("11446001", one.content.decode("utf-8"))
        self.assertEqual(self.client.get("/teacher/export.csv", {"course": self.other}).status_code, 404)  # 別的老師的課


class NoFakeDataTests(Base):
    @override_settings(DEBUG=True, STORE="firestore")
    def test_dev_login_student_blocked_on_real_store(self):
        r = self.post("/dev/login/", {"email": "11446001@ntub.edu.tw"})
        self.assertEqual(r.json()["error"], "student_needs_memory_store")

    @override_settings(DEBUG=True, STORE="firestore")
    def test_dev_login_teacher_allowed_on_real_store(self):
        self.assertEqual(self.post("/dev/login/", {"email": "sckuai@ntub.edu.tw"}).status_code, 200)

    def test_teacher_cannot_save_selection(self):
        self.login(TeacherTests.TEACHER)
        r = self.post("/api/selection/", {"major": "406", "grade": 2, "sel": []})
        self.assertEqual(r.status_code, 403)


class AutoRequiredSyncTests(Base):
    STUDENT = {**SCHOOL_CLAIMS, "uid": "u-auto", "email": "11446001@ntub.edu.tw"}

    def saved(self):
        return store.get_store().get_student("u-auto")

    def test_first_visit_saves_required_on_server(self):
        from courses.teachers import courses_taught
        self.login(self.STUDENT)
        self.client.get("/app/")  # 沒有跑任何前端 JS
        s = self.saved()
        self.assertEqual((s["major"], s["grade"], s["cls"]), ("406", 2, "資管二年甲班"))
        self.assertTrue(s["sel"] and s["sel"] == s["auto"])
        kuai = courses_taught(["蒯思齊"], store.get_store().list_courses())[0]["id"]  # 資訊網路是資管二甲必修
        self.assertIn(kuai, s["sel"])
        self.client.post("/auth/logout/")
        self.login(TeacherTests.TEACHER)
        course = next(c for c in self.client.get("/teacher/").context["courses"] if c["id"] == kuai)
        self.assertEqual([x["sid"] for x in course["students"]], ["11446001"])

    def test_other_department_save_is_replaced(self):
        self.login(self.STUDENT)
        self.post("/api/selection/", {"major": "402", "grade": 2, "cls": "財金二年甲班", "sel": ["s299"]})
        self.client.get("/app/")
        self.assertEqual(self.saved()["major"], "406")
        self.assertNotIn("s299", self.saved()["sel"])

    def test_own_choices_are_kept(self):
        self.login(self.STUDENT)
        self.client.get("/app/")
        auto = self.saved()["auto"]
        self.post("/api/selection/", {"major": "406", "grade": 2, "cls": "資管二年甲班", "sel": auto[1:], "auto": auto})  # 退掉一門必修
        self.client.get("/app/")
        self.assertEqual(self.saved()["sel"], auto[1:])


class MemoryBannerTests(Base):
    def test_banner_only_in_memory_mode(self):
        self.assertContains(self.client.get("/"), "本機記憶體模式")  # Base 用 STORE=memory
        with override_settings(STORE="firestore"):
            self.assertNotContains(self.client.get("/"), "本機記憶體模式")


class DevPanelTests(Base):
    def test_panel_hidden_in_production(self):
        self.assertNotContains(self.client.get("/"), 'id="dev"')  # 測試預設 DEBUG=False

    @override_settings(DEBUG=True)
    def test_panel_shown_locally(self):
        self.assertContains(self.client.get("/"), 'id="dev"')


class CourseSwapTests(Base):
    def setUp(self):
        super().setUp()
        self.st = store.get_store()
        template = self.st.courses["s1"]
        for cid, slots in (("swap-old", [[1, 1, 3]]), ("swap-new", [[1, 1, 3]]), ("swap-other", [[2, 4, 5]])):
            self.st.courses[cid] = {**template, "id": cid, "name": cid, "src": "dept", "grade": 2,
                                    "slots": slots, "cap": 2, "registered": 0}
        self.data = {"major": "406", "grade": 2, "cls": "資管二年甲班",
                     "sel": ["swap-old", "swap-other"], "auto": ["swap-old"]}
        self.st.save_selection("u1", "s1@ntub.edu.tw", self.data)
        self.body = {"old": "swap-old", "new": "swap-new", "expected": self.data["sel"]}

    def swap(self):
        return self.post("/api/selection/swap/", self.body)

    def test_swap_saves_both_changes_and_preserves_required_reminder(self):
        self.login()
        result = self.swap()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["saved"]["sel"], ["swap-new", "swap-other"])
        self.assertEqual(self.st.courses["swap-old"]["registered"], 0)
        self.assertEqual(self.st.courses["swap-new"]["registered"], 1)
        self.assertEqual(self.st.get_student("u1")["auto"], ["swap-old"])
        self.assertEqual(self.client.get("/api/me/").json()["saved"]["sel"], ["swap-new", "swap-other"])

    def test_rejected_swaps_leave_original_selection_and_counts_unchanged(self):
        self.login()
        changes = (
            ({"registered": 2}, "no_seats"),
            ({"grade": 3}, "ineligible_grade"),
            ({"src": "ge", "grade": 4}, "ineligible_grade"),
            ({"slots": [[1, 1, 2]]}, "different_time"),
            ({"slots": [[1, 1, 3], [3, 1, 1]]}, "different_time"),
            ({"slots": []}, "different_time"),
        )
        original = dict(self.st.courses["swap-new"])
        for fields, error in changes:
            with self.subTest(error=error, fields=fields):
                self.st.courses["swap-new"] = {**original, **fields}
                response = self.swap()
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()["error"], error)
                self.assertEqual(self.st.get_student("u1")["sel"], self.data["sel"])
                self.assertEqual(self.st.courses["swap-old"]["registered"], 1)
                self.assertEqual(self.st.courses["swap-new"]["registered"], fields.get("registered", 0))

    def test_split_period_blocks_are_the_same_time(self):
        self.login()
        self.st.courses["swap-new"]["slots"] = [[1, 2, 3], [1, 1, 1]]
        self.assertEqual(self.swap().status_code, 200)

    def test_conflict_with_another_selected_course_is_rejected(self):
        self.login()
        self.st.courses["swap-other"]["slots"] = [[1, 3, 4]]
        self.assertEqual(self.swap().json()["error"], "course_conflict")
        self.assertEqual(self.st.get_student("u1")["sel"], self.data["sel"])

    def test_stale_tab_does_not_overwrite_newer_selection(self):
        self.login()
        self.st.save_selection("u1", "s1@ntub.edu.tw", {**self.data, "sel": ["swap-old"]})
        self.assertEqual(self.swap().json()["error"], "selection_changed")
        self.assertEqual(self.st.get_student("u1")["sel"], ["swap-old"])

    def test_missing_course_or_repeated_swap_does_not_drop_the_original(self):
        self.login()
        del self.st.courses["swap-new"]
        self.assertEqual(self.swap().json()["error"], "course_unavailable")
        self.assertEqual(self.st.get_student("u1")["sel"], self.data["sel"])
        self.body["new"] = "swap-old"
        self.assertEqual(self.swap().json()["error"], "selection_changed")

    def test_auth_csrf_and_payload_validation(self):
        from django.test import Client
        self.assertEqual(self.swap().status_code, 401)
        self.login()
        for payload in ({}, {**self.body, "expected": "swap-old"}, {**self.body, "new": []},
                        {**self.body, "new": "invalid/path"}, {**self.body, "expected": [None]},
                        {**self.body, "expected": ["x"] * 61}):
            self.assertEqual(self.post("/api/selection/swap/", payload).status_code, 400)
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/selection/swap/", json.dumps(self.body), content_type="application/json").status_code, 403)
        self.login({**SCHOOL_CLAIMS, "email": "sckuai@ntub.edu.tw"})
        self.assertEqual(self.swap().status_code, 403)

    def test_two_students_competing_for_one_seat_only_one_swap_succeeds(self):
        self.st.courses["swap-new"]["cap"] = 1
        self.st.save_selection("u2", "s2@ntub.edu.tw", self.data)

        def attempt(uid):
            try:
                self.st.swap_course(uid, uid + "@ntub.edu.tw", "swap-old", "swap-new", self.data["sel"])
                return "ok"
            except SwapError as error:
                return str(error)

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, ["u1", "u2"]))
        self.assertCountEqual(outcomes, ["ok", "no_seats"])
        self.assertEqual(self.st.courses["swap-new"]["registered"], 1)
        self.assertEqual(self.st.courses["swap-old"]["registered"], 1)

    def test_firestore_reads_and_validates_before_any_transaction_write(self):
        fake = mock.Mock()
        student_ref = fake.collection.return_value.document.return_value
        student_ref.get.return_value.exists = True
        student_ref.get.return_value.to_dict.return_value = self.st.get_student("u1")
        snapshots = []
        for cid in [*self.data["sel"], "swap-new"]:
            data = dict(self.st.courses[cid])
            data["slots"] = store._slots_to_fs(data["slots"])
            snapshot = mock.Mock(id=cid, exists=True)
            snapshot.raw = data
            snapshot.to_dict.side_effect = lambda data=data: deepcopy(data)
            snapshots.append(snapshot)
        fake.get_all.return_value = snapshots
        firestore_store = store.FirestoreStore()
        firestore_store._db = lambda: fake
        with mock.patch("firebase_admin.firestore.transactional", side_effect=lambda func: func):
            saved = firestore_store.swap_course("u1", "s1@ntub.edu.tw", "swap-old", "swap-new", self.data["sel"])
            self.assertEqual(saved["sel"], ["swap-new", "swap-other"])
            self.assertEqual(fake.transaction.return_value.update.call_count, 2)
            fake.transaction.return_value.set.assert_called_once()
            fake.transaction.return_value.reset_mock()
            snapshots[-1].raw["registered"] = 2
            with self.assertRaisesRegex(SwapError, "no_seats"):
                firestore_store.swap_course("u1", "s1@ntub.edu.tw", "swap-old", "swap-new", self.data["sel"])
            fake.transaction.return_value.update.assert_not_called()
            fake.transaction.return_value.set.assert_not_called()
