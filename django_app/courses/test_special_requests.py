from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from types import SimpleNamespace
from unittest import mock

from django.test import Client

from . import store
from .special_requests import RequestError
from .tests import Base, SCHOOL_CLAIMS

STUDENT = {**SCHOOL_CLAIMS, "email": "11446001@ntub.edu.tw"}
TEACHER = {**SCHOOL_CLAIMS, "uid": "teacher", "email": "sckuai@ntub.edu.tw", "name": "蒯思齊"}


class SpecialRequestTests(Base):
    def setUp(self):
        super().setUp()
        self.st = store.get_store()
        template = self.st.courses["s1"]
        for cid, slots, teacher in (("selected", [[1, 1, 2]], "別的老師"),
                                    ("request-course", [[2, 3, 4]], "蒯思齊"),
                                    ("other-course", [[3, 1, 2]], "別的老師"),
                                    ("replacement", [[2, 3, 4]], "蒯思齊")):
            self.st.courses[cid] = {**template, "id": cid, "name": cid, "teacher": teacher,
                                    "src": "dept", "dept": "406", "grade": 2, "cap": 1,
                                    "slots": slots, "registered": 0}
        self.data = {"major": "406", "grade": 2, "cls": "資管二年甲班", "sel": ["selected"], "auto": []}
        self.st.save_selection("u1", STUDENT["email"], self.data, "測試學生")

    def submit(self, kind="add", course_id="request-course", reason="申請修課理由"):
        self.login(STUDENT)
        return self.post("/api/applications/", {"course_id": course_id, "kind": kind, "reason": reason})

    def decide(self, request_id, decision="approve", note="同意修課"):
        self.login(TEACHER)
        return self.post(f"/api/applications/{request_id}/review/", {"decision": decision, "note": note})

    def test_submit_is_pending_and_does_not_enroll(self):
        response = self.submit()
        self.assertEqual(response.status_code, 200)
        app = response.json()["application"]
        self.assertEqual(app["status"], "pending")
        self.assertEqual(self.st.get_student("u1")["sel"], ["selected"])
        self.assertEqual(self.st.courses["request-course"]["registered"], 0)
        self.assertEqual(self.client.get("/api/me/").json()["applications"][0]["id"], app["id"])

    def test_course_restrictions_require_the_matching_review_before_enrollment(self):
        for kind in ("add", "cross_dept", "prerequisite"):
            with self.subTest(kind=kind):
                self.setUp()
                self.st.courses["request-course"]["approval_kind"] = kind
                if kind == "cross_dept":
                    self.st.courses["request-course"]["dept"] = "401"
                self.login(STUDENT)
                payload = {**self.data, "sel": ["selected", "request-course"]}
                blocked = self.post("/api/selection/", payload)
                self.assertEqual(blocked.status_code, 409)
                self.assertEqual(blocked.json()["error"], "special_application_required")
                self.assertEqual(self.st.get_student("u1")["sel"], ["selected"])
                self.assertEqual(self.st.courses["request-course"]["registered"], 0)
                page = self.client.get("/app/")
                row = next(row for row in page.context["courses"] if row[0] == "request-course")
                self.assertEqual(row[16], kind)
                wrong = "prerequisite" if kind == "add" else "add"
                self.assertEqual(self.submit(wrong).json()["error"], "invalid_application")
                app = self.submit(kind).json()["application"]
                self.assertEqual(self.decide(app["id"]).status_code, 200)
                self.login(STUDENT)
                current = self.st.get_student("u1")
                self.assertEqual(self.post("/api/selection/", {**payload, "revision": current["revision"]}).status_code, 200)
                self.assertIn("request-course", self.st.get_student("u1")["approved"])

    def test_cross_department_restriction_does_not_block_own_department(self):
        self.st.courses["request-course"]["approval_kind"] = "cross_dept"
        self.login(STUDENT)
        self.assertEqual(self.post("/api/selection/", {**self.data, "sel": ["selected", "request-course"]}).status_code, 200)

    def test_known_student_cannot_claim_another_department_to_skip_review(self):
        self.st.courses["request-course"].update(approval_kind="cross_dept", dept="401")
        self.login(STUDENT)
        response = self.post("/api/selection/", {**self.data, "major": "401", "sel": ["selected", "request-course"]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_student_profile")
        self.assertEqual(self.st.get_student("u1")["sel"], ["selected"])

    def test_safe_swap_cannot_bypass_required_approval(self):
        self.st.courses["selected"]["slots"] = [[2, 3, 4]]
        self.st.courses["request-course"]["approval_kind"] = "add"
        self.login(STUDENT)
        response = self.post("/api/selection/swap/", {"old": "selected", "new": "request-course", "expected": ["selected"]})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "special_application_required")
        self.assertEqual(self.st.get_student("u1")["sel"], ["selected"])

    def test_all_three_kinds_auto_enroll_and_mark_on_approval(self):
        for kind in ("add", "cross_dept", "prerequisite"):
            with self.subTest(kind=kind):
                self.setUp()
                if kind == "cross_dept":
                    self.st.courses["request-course"]["dept"] = "401"
                app = self.submit(kind).json()["application"]
                self.assertEqual(self.decide(app["id"]).status_code, 200)
                saved = self.st.get_student("u1")
                self.assertEqual(saved["sel"], ["selected", "request-course"])
                self.assertEqual(saved["approved"]["request-course"], {"request_id": app["id"], "kind": kind})
                self.assertEqual(self.st.courses["request-course"]["registered"], 1)
                self.login(STUDENT)
                page = self.client.get("/app/")
                self.assertIn("request-course", page.context["boot"]["saved"]["sel"])
                self.assertIn("request-course", page.context["boot"]["saved"]["approved"])

    def test_rejection_keeps_timetable_unchanged_and_exposes_reply(self):
        app = self.submit().json()["application"]
        self.assertEqual(self.decide(app["id"], "reject", "請先補充學習經歷").status_code, 200)
        self.assertEqual(self.st.get_student("u1")["sel"], ["selected"])
        self.assertEqual(self.st.courses["request-course"]["registered"], 0)
        self.login(STUDENT)
        record = self.client.get("/api/me/").json()["applications"][0]
        self.assertEqual(record["status"], "rejected")
        self.assertEqual(record["note"], "請先補充學習經歷")

    def test_duplicate_submission_and_repeated_approval_are_idempotent(self):
        app = self.submit().json()["application"]
        self.assertEqual(self.submit().json()["application"]["id"], app["id"])
        for _ in range(2):
            self.assertEqual(self.decide(app["id"]).status_code, 200)
        self.assertEqual(self.st.courses["request-course"]["registered"], 1)
        self.assertEqual(len(self.st.applications), 1)

        self.assertEqual(self.decide(app["id"], "reject").json()["error"], "already_reviewed")

    def test_resubmit_after_rejection_keeps_history(self):
        first = self.submit().json()["application"]
        self.decide(first["id"], "reject")
        second = self.submit().json()["application"]
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(len(self.st.list_applications(uid="u1")), 2)

    def test_conflict_does_not_approve_or_mutate_enrollment(self):
        self.st.courses["request-course"]["slots"] = [[1, 2, 3]]
        app = self.submit().json()["application"]
        self.assertEqual(self.decide(app["id"]).json()["error"], "course_conflict")
        self.assertEqual(self.st.applications[app["id"]]["status"], "pending")
        self.assertEqual(self.st.get_student("u1")["sel"], ["selected"])
        self.assertEqual(self.st.courses["request-course"]["registered"], 0)

    def test_add_permission_can_exceed_capacity_but_waiver_cannot(self):
        self.st.courses["request-course"]["cap"] = 0
        waiver = self.submit("prerequisite").json()["application"]
        self.assertEqual(self.decide(waiver["id"]).json()["error"], "no_seats")
        signature = self.submit("add").json()["application"]
        self.assertEqual(self.decide(signature["id"]).status_code, 200)
        self.assertEqual(self.st.courses["request-course"]["registered"], 1)

    def test_second_type_for_already_enrolled_course_does_not_double_count(self):
        one = self.submit("add").json()["application"]
        two = self.submit("prerequisite").json()["application"]
        self.decide(one["id"])
        self.assertEqual(self.decide(two["id"]).status_code, 200)
        self.assertEqual(self.st.courses["request-course"]["registered"], 1)

    def test_teacher_can_only_see_and_review_own_courses(self):
        own = self.submit().json()["application"]
        other = self.submit(course_id="other-course").json()["application"]
        self.login(TEACHER)
        page = self.client.get("/teacher/")
        self.assertIn(own["id"], [app["id"] for app in page.context["applications"]])
        self.assertNotIn(other["id"], [app["id"] for app in page.context["applications"]])
        self.assertEqual(self.post(f'/api/applications/{other["id"]}/review/', {"decision": "approve"}).status_code, 403)
        self.assertEqual(self.st.applications[other["id"]]["status"], "pending")

    def test_student_cannot_review_or_view_another_students_requests(self):
        app = self.submit().json()["application"]
        self.assertEqual(self.post(f'/api/applications/{app["id"]}/review/', {"decision": "approve"}).status_code, 403)
        self.login({**STUDENT, "uid": "u2", "email": "11446002@ntub.edu.tw"})
        self.assertEqual(self.client.get("/api/me/").json()["applications"], [])
        self.login(TEACHER)
        self.assertEqual(self.post("/api/applications/", {"course_id": "request-course", "kind": "add", "reason": "理由"}).status_code, 403)

    def test_old_tab_cannot_erase_teacher_enrollment(self):
        revision = self.st.get_student("u1")["revision"]
        app = self.submit().json()["application"]
        self.decide(app["id"])
        self.login(STUDENT)
        for payload in ({**self.data, "revision": revision}, self.data):
            response = self.post("/api/selection/", payload)
            self.assertEqual(response.status_code, 409)
            self.assertIn("request-course", response.json()["saved"]["sel"])
        self.assertEqual(self.st.courses["request-course"]["registered"], 1)

    def test_legitimate_drop_removes_marker_and_does_not_reenroll_on_refresh(self):
        app = self.submit().json()["application"]
        self.decide(app["id"])
        self.login(STUDENT)
        revision = self.st.get_student("u1")["revision"]
        self.assertEqual(self.post("/api/selection/", {**self.data, "revision": revision}).status_code, 200)
        self.assertEqual(self.st.get_student("u1")["approved"], {})
        self.assertEqual(self.st.courses["request-course"]["registered"], 0)
        self.client.get("/app/")
        self.assertNotIn("request-course", self.st.get_student("u1")["sel"])

    def test_swapping_approved_course_removes_only_its_grant(self):
        app = self.submit().json()["application"]
        self.decide(app["id"])
        self.login(STUDENT)
        response = self.post("/api/selection/swap/", {"old": "request-course", "new": "replacement", "expected": ["selected", "request-course"]})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("request-course", response.json()["saved"]["approved"])
        self.assertNotIn("replacement", response.json()["saved"]["approved"])

    def test_students_cannot_forge_approval_markers(self):
        self.login(STUDENT)
        response = self.post("/api/selection/", {**self.data, "approved": {"selected": {"kind": "add"}}})
        self.assertEqual(response.json()["saved"]["approved"], {})

    def test_input_validation_and_csrf(self):
        self.login(STUDENT)
        for changes in ({"course_id": "a/b"}, {"kind": []}, {"kind": "other"}, {"reason": " "}, {"reason": "x" * 1001}):
            payload = {"course_id": "request-course", "kind": "add", "reason": "理由", **changes}
            self.assertEqual(self.post("/api/applications/", payload).status_code, 400)
        self.assertEqual(self.submit("cross_dept").json()["error"], "not_cross_dept")
        self.assertEqual(self.submit(course_id="selected").json()["error"], "already_selected")
        self.assertEqual(self.submit(course_id="missing").json()["error"], "course_unavailable")
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/applications/", "{}", content_type="application/json").status_code, 403)
        self.assertEqual(client.post("/api/applications/id/review/", "{}", content_type="application/json").status_code, 403)

    def test_teacher_html_escapes_user_text_and_marks_approved_roster(self):
        app = self.submit(reason='<script>alert("x")</script>').json()["application"]
        self.login(TEACHER)
        self.assertContains(self.client.get("/teacher/"), '&lt;script&gt;')
        self.assertNotContains(self.client.get("/teacher/"), '<script>alert("x")</script>')
        self.decide(app["id"])
        page = self.client.get("/teacher/")
        course = next(c for c in page.context["courses"] if c["id"] == "request-course")
        self.assertTrue(course["students"][0]["approved"])

    def test_concurrent_approvals_only_consume_one_remaining_seat(self):
        first = self.submit("prerequisite").json()["application"]
        self.st.save_selection("u2", "11446002@ntub.edu.tw", self.data)
        second = self.st.submit_application("u2", "11446002@ntub.edu.tw", "學生二", "request-course", "prerequisite", "理由")

        def approve(request_id):
            try:
                self.st.review_application(request_id, ["蒯思齊"], TEACHER["email"], "approve", "")
                return "approved"
            except RequestError as error:
                return str(error)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(approve, [first["id"], second["id"]]))
        self.assertCountEqual(results, ["approved", "no_seats"])
        self.assertEqual(self.st.courses["request-course"]["registered"], 1)

    def test_concurrent_duplicate_submissions_create_one_pending_request(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self.st.submit_application("u1", STUDENT["email"], "學生", "request-course", "add", "理由"), range(2)))
        self.assertEqual(results[0]["id"], results[1]["id"])
        self.assertEqual(len(self.st.applications), 1)



class FirestoreRequestTests(Base):
    def setUp(self):
        super().setUp()
        template = store.get_store().courses["s1"]
        self.student = {"major": "406", "grade": 2, "cls": "資管二年甲班", "sel": ["selected"], "auto": [], "revision": 1}
        self.records = {("students", "u1"): deepcopy(self.student)}
        for cid, slots in (("selected", [[1, 1, 2]]), ("requested", [[2, 3, 4]])):
            self.records["courses", cid] = {**template, "id": cid, "name": cid, "teacher": "蒯思齊", "src": "dept",
                                            "dept": "406", "cap": 1, "registered": int(cid == "selected"),
                                            "slots": store._slots_to_fs(slots)}
        self.client_db, self.transaction = mock.Mock(), mock.Mock()
        self.references = {}

        def reference(collection, doc_id):
            key = collection, doc_id
            if key not in self.references:
                ref = mock.Mock(id=doc_id)

                def read(transaction):
                    # Firestore does not allow any read after the first transaction write.
                    self.assertFalse(transaction.set.called or transaction.update.called)
                    return SimpleNamespace(id=doc_id, exists=key in self.records, to_dict=lambda: deepcopy(self.records.get(key)))

                ref.get.side_effect = read
                self.references[key] = ref
            return self.references[key]

        self.client_db.collection.side_effect = lambda name: SimpleNamespace(document=lambda doc_id: reference(name, doc_id))
        self.client_db.get_all.side_effect = lambda refs, transaction: (ref.get(transaction=transaction) for ref in refs)
        self.client_db.transaction.return_value = self.transaction
        self.fs = store.FirestoreStore()
        self.fs._db = lambda: self.client_db
        self.decorator = mock.patch("firebase_admin.firestore.transactional", side_effect=lambda function: function)
        self.decorator.start()
        self.addCleanup(self.decorator.stop)

    def application(self, kind="add"):
        app = self.fs.submit_application("u1", STUDENT["email"], "學生", "requested", kind, "理由")
        self.records["special_requests", app["id"]] = deepcopy(app)
        self.records["students", "u1"]["pending_requests"] = {"requested:" + kind: app["id"]}
        self.transaction.reset_mock()
        return app

    def test_approval_writes_request_enrollment_and_marker_in_one_transaction(self):
        app = self.application()
        result = self.fs.review_application(app["id"], ["蒯思齊"], TEACHER["email"], "approve", "同意")
        self.assertEqual(result["status"], "approved")
        self.transaction.update.assert_called_once()
        writes = {id(call.args[0]): call for call in self.transaction.set.call_args_list}
        student_ref = self.references["students", "u1"]
        student_write = writes[id(student_ref)]
        saved = student_write.args[1]
        self.assertIn("requested", saved["sel"])
        self.assertEqual(saved["approved"]["requested"]["request_id"], app["id"])
        self.assertEqual(saved["pending_requests"], {})
        self.assertIn("approved", student_write.kwargs["merge"])
        self.assertIn("pending_requests", student_write.kwargs["merge"])
        self.assertEqual(self.transaction.set.call_count, 2)

        # The next call sees the committed documents; a retry must not add a second seat.
        self.records["students", "u1"] = deepcopy(saved)
        self.records["special_requests", app["id"]] = deepcopy(result)
        self.transaction.reset_mock()
        self.fs.review_application(app["id"], ["蒯思齊"], TEACHER["email"], "approve", "同意")
        self.transaction.update.assert_not_called()
        self.transaction.set.assert_not_called()

        with self.assertRaisesRegex(RequestError, "selection_changed"):
            self.fs.save_selection("u1", STUDENT["email"], self.student, expected_revision=1)
        self.transaction.set.assert_not_called()
        revision = saved["revision"]
        clean = self.fs.save_selection("u1", STUDENT["email"], self.student, expected_revision=revision)
        self.assertEqual(clean["approved"], {})
        self.assertIn("approved", self.transaction.set.call_args.kwargs["merge"])

    def test_failed_firestore_review_does_not_write_any_document(self):
        app = self.application("prerequisite")
        with self.assertRaisesRegex(RequestError, "not_course_teacher"):
            self.fs.review_application(app["id"], ["其他老師"], "other@ntub.edu.tw", "approve", "")
        self.transaction.set.assert_not_called()
        self.transaction.update.assert_not_called()
        self.records["courses", "requested"]["registered"] = 1
        with self.assertRaisesRegex(RequestError, "no_seats"):
            self.fs.review_application(app["id"], ["蒯思齊"], TEACHER["email"], "approve", "")
        self.transaction.set.assert_not_called()
        self.transaction.update.assert_not_called()

    def test_direct_firestore_save_checks_course_policy_before_writing(self):
        self.records["courses", "requested"]["approval_kind"] = "add"
        with self.assertRaisesRegex(RequestError, "special_application_required"):
            self.fs.save_selection("u1", STUDENT["email"], {**self.student, "sel": ["selected", "requested"]}, expected_revision=1)
        self.transaction.set.assert_not_called()
        self.transaction.update.assert_not_called()
