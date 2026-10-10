import tempfile
import unittest
from pathlib import Path

from app import create_app
from database import connect


class LaunchpadApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = str(Path(self.temp_dir.name) / "isolated-test.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-session-key",
            "DATABASE": self.database_path,
        })
        self.client = self.app.test_client()
        self.csrf_token = self.client.get("/api/health").get_json()["csrf_token"]
        self.headers = {"X-CSRF-Token": self.csrf_token}

    def tearDown(self):
        self.temp_dir.cleanup()

    def post(self, path, payload):
        return self.client.post(path, json=payload, headers=self.headers)

    def create_profile(self, **overrides):
        profile = {
            "name": "Test Student", "branch": "Computer Science",
            "semester": 5, "cgpa": 8.2, "target_role": "Software Engineer",
            "study_hours": 1.5,
        }
        profile.update(overrides)
        return self.post("/api/profile", profile)

    def test_database_initialization_and_profile_persistence(self):
        db = connect(self.database_path)
        try:
            names = {row["name"] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            db.close()
        self.assertTrue({"students", "learning_tasks", "assessments", "interview_sessions",
                         "interview_answers", "achievements", "resumes"}.issubset(names))
        self.assertEqual(self.create_profile().status_code, 201)
        loaded = self.client.get("/api/profile").get_json()["profile"]
        self.assertEqual(loaded["name"], "Test Student")
        self.assertEqual(loaded["branch"], "Computer Science")
        self.assertEqual(len(self.client.get("/api/roadmap").get_json()["tasks"]), 24)

    def test_profile_validation_and_session_isolation(self):
        for invalid in (
            {"name": "", "branch": "CS", "semester": 1, "study_hours": 1},
            {"name": "A" * 101, "branch": "CS", "semester": 1, "study_hours": 1},
            {"name": "Student", "branch": "CS", "semester": 13, "study_hours": 1},
            {"name": "Student", "branch": "CS", "semester": True, "study_hours": 1},
            {"name": "Student", "branch": "CS", "semester": 1, "cgpa": 11, "study_hours": 1},
            {"name": "Student", "branch": "CS", "semester": 1, "study_hours": 13},
        ):
            self.assertEqual(self.post("/api/profile", invalid).status_code, 400)
        self.create_profile()
        other_client = self.app.test_client()
        self.assertIsNone(other_client.get("/api/profile").get_json()["profile"])
        self.assertEqual(other_client.get("/api/progress").status_code, 401)

    def test_csrf_and_invalid_content_type_are_rejected(self):
        self.assertEqual(self.client.post("/api/profile", json={"name": "x"}).status_code, 403)
        self.assertEqual(self.client.post("/api/profile", data="{}",
                                          headers={"X-CSRF-Token": self.csrf_token}).status_code, 400)

    def test_task_completion_is_idempotent_and_awards_achievement(self):
        self.create_profile()
        first = self.post("/api/tasks/dsa-0/complete", {})
        second = self.post("/api/tasks/dsa-0/complete", {})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        progress = self.client.get("/api/progress").get_json()
        self.assertEqual(progress["tasks"], {"completed": 1, "pending": 23})
        awards = self.client.get("/api/achievements").get_json()["achievements"]
        self.assertEqual(sum(award["id"] == "first-learning-task" for award in awards), 1)
        self.assertEqual(self.post("/api/tasks/not-a-task/complete", {}).status_code, 404)

    def test_assessment_score_is_calculated_and_persisted_on_server(self):
        self.create_profile()
        questions = self.client.get("/api/assessments").get_json()["questions"]["dsa"]
        attempt = self.post("/api/assessments", {
            "skill": "dsa",
            "score": 100,
            "answers": [
                {"question_id": questions[0]["id"], "selected_option": 1},
                {"question_id": questions[1]["id"], "selected_option": 0},
            ],
        })
        self.assertEqual(attempt.status_code, 201)
        self.assertEqual(attempt.get_json()["score"], 50)
        self.assertEqual(self.client.get("/api/assessments").get_json()["history"][0]["score"], 50)
        malformed = self.post("/api/assessments", {"skill": "dsa", "answers": [{"question_id": "unknown", "selected_option": 0}]})
        self.assertEqual(malformed.status_code, 400)
        duplicate = self.post("/api/assessments", {"skill": "dsa", "answers": [
            {"question_id": questions[0]["id"], "selected_option": 1},
            {"question_id": questions[0]["id"], "selected_option": 1},
        ]})
        self.assertEqual(duplicate.status_code, 400)
        invalid_option = self.post("/api/assessments", {"skill": "dsa", "answers": [
            {"question_id": questions[0]["id"], "selected_option": 99},
        ]})
        self.assertEqual(invalid_option.status_code, 400)

    def test_interview_evaluation_persistence_and_access_control(self):
        self.create_profile()
        created = self.post("/api/interviews", {
            "target_role": "Software Engineer", "category": "DSA",
            "difficulty": "All levels", "question_count": 2,
            "question_ids": ["dsa-arrays", "dsa-two-pointers"],
        })
        self.assertEqual(created.status_code, 201, created.get_json())
        interview_id = created.get_json()["id"]
        question = created.get_json()["questions"][0]
        answer = "I scan each item once and track the maximum, which takes O(n) time and constant space."
        submitted = self.post(f"/api/interviews/{interview_id}/answers", {
            "question_id": question["id"], "answer": answer,
        })
        self.assertEqual(submitted.status_code, 201)
        self.assertGreater(submitted.get_json()["score"], 0)
        self.assertEqual(self.post(f"/api/interviews/{interview_id}/answers", {
            "question_id": question["id"], "answer": answer,
        }).status_code, 409)
        completed = self.post(f"/api/interviews/{interview_id}/complete", {})
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.get_json()["session"]["score"], submitted.get_json()["score"])
        self.assertEqual(self.client.get(f"/api/interviews/{interview_id}").status_code, 200)
        self.assertEqual(self.post(f"/api/interviews/{interview_id}/complete", {}).status_code, 409)
        other_client = self.app.test_client()
        self.assertEqual(other_client.get(f"/api/interviews/{interview_id}").status_code, 401)

    def test_interview_input_and_answer_validation(self):
        self.create_profile()
        self.assertEqual(self.post("/api/interviews", {"target_role": "Engineer", "category": "Unknown"}).status_code, 400)
        self.assertEqual(self.post("/api/interviews", {"target_role": "Engineer", "category": "DSA", "question_count": 0}).status_code, 400)
        created = self.post("/api/interviews", {
            "target_role": "Engineer", "category": "DSA", "difficulty": "All levels",
            "question_count": 1, "question_ids": ["dsa-arrays"],
        }).get_json()
        self.assertEqual(self.post(f"/api/interviews/{created['id']}/answers", {
            "question_id": "web-html", "answer": "valid but unrelated question",
        }).status_code, 400)
        self.assertEqual(self.post(f"/api/interviews/{created['id']}/answers", {
            "question_id": "dsa-arrays", "answer": " ",
        }).status_code, 400)
        self.assertEqual(self.client.get("/api/interviews/not-a-valid-id").status_code, 404)

    def test_resume_validation_and_persistence(self):
        self.create_profile()
        payload = {
            "career_objective": "Learn and contribute.", "education": "B.Tech, Computer Science",
            "technical_skills": "Python, SQL", "projects": ["Student portal: built a portal."],
            "certifications": ["Only a student-reported certificate"],
            "achievements": [{"id": "contest", "title": "College coding contest", "issuer": "College", "date": "2026-05", "detail": "Participant"}],
        }
        self.assertEqual(self.client.put("/api/resume", json=payload, headers=self.headers).status_code, 200)
        saved = self.client.get("/api/resume").get_json()["resume"]
        self.assertEqual(saved["career_objective"], payload["career_objective"])
        self.assertEqual(saved["projects"], payload["projects"])
        self.assertEqual(saved["achievements"][0]["title"], "College coding contest")
        payload["career_objective"] = "x" * 1501
        self.assertEqual(self.client.put("/api/resume", json=payload, headers=self.headers).status_code, 400)

    def test_recommendations_use_saved_evidence_only(self):
        self.create_profile(study_hours=2)
        empty = self.client.get("/api/recommendations").get_json()["recommendations"]
        self.assertEqual(len(empty), 3)
        self.assertEqual(empty[0]["evidence_score"], 0)
        self.assertEqual(empty[0]["recommended_task"]["estimated_days"], 1)
        self.post("/api/tasks/dsa-0/complete", {})
        self.post("/api/assessments", {
            "skill": "dsa",
            "answers": [
                {"question_id": "dsa-stack", "selected_option": 1},
                {"question_id": "dsa-binary", "selected_option": 1},
            ],
        })
        dsa = next(item for item in self.client.get("/api/recommendations").get_json()["recommendations"] if item["skill"] == "dsa")
        self.assertEqual(dsa["progress_score"], 13)
        self.assertEqual(dsa["practice_score"], 100)
        self.assertEqual(dsa["recommended_task"]["id"], "dsa-1")

    def test_assessment_question_payload_does_not_leak_answer_keys(self):
        self.create_profile()
        questions = self.client.get("/api/assessments").get_json()["questions"]
        self.assertNotIn("answer", questions["dsa"][0])
        self.assertNotIn("correct", questions["dsa"][0])
        web = self.post("/api/assessments", {
            "skill": "web",
            "answers": [
                {"question_id": "web-nav", "selected_option": 1},
                {"question_id": "web-grid", "selected_option": 1},
            ],
        })
        self.assertEqual(web.status_code, 201)
        self.assertEqual(web.get_json()["score"], 100)
        malformed_id = self.post("/api/assessments", {
            "skill": "web", "answers": [{"question_id": [], "selected_option": 0}],
        })
        self.assertEqual(malformed_id.status_code, 400)


if __name__ == "__main__":
    unittest.main()
