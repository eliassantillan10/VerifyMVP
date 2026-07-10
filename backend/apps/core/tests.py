import json

from django.test import Client, SimpleTestCase
from django.urls import reverse


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_public_contract(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "VerifyMVP API",
                "database": "postgresql",
            },
        )


class GameGenerationTests(SimpleTestCase):
    def assert_game_response_contract(self, payload):
        self.assertEqual(payload["settings"]["cover_topics"], ["loops", "functions"])
        self.assertEqual(payload["settings"]["emphasize_topics"], ["arrays"])
        self.assertEqual(payload["settings"]["problem_types"], ["solution comparison"])
        self.assertEqual(payload["game"]["title"], "CS1 Solution Spotlight")
        self.assertEqual(len(payload["game"]["tasks"]), 5)
        self.assertEqual(
            payload["game"]["scoring"],
            {
                "correctness_points": 100,
                "time_bonus_points": 25,
                "fast_answer_threshold_ms": 8000,
            },
        )

        first_task = payload["game"]["tasks"][0]
        self.assertIn("specifications", first_task)
        self.assertEqual(len(first_task["candidate_solutions"]), 3)
        self.assertIn("explanation", first_task)

        correct_ids = {
            task["correct_solution_id"] for task in payload["game"]["tasks"]
        }
        self.assertGreater(len(correct_ids), 1)

        for task in payload["game"]["tasks"]:
            candidate_ids = {
                candidate["id"] for candidate in task["candidate_solutions"]
            }
            self.assertIn(task["correct_solution_id"], candidate_ids)
            correct_candidate = next(
                candidate
                for candidate in task["candidate_solutions"]
                if candidate["id"] == task["correct_solution_id"]
            )
            self.assertIn("return true;", correct_candidate["code"])

            for candidate in task["candidate_solutions"]:
                self.assertIn("bool check_", candidate["code"])
                self.assertNotIn("def check_", candidate["code"])
                if candidate["id"] != task["correct_solution_id"]:
                    self.assertNotIn("return true;", candidate["code"])

    def post_game_generation(self, client=None, payload=None):
        test_client = client or self.client
        return test_client.post(
            reverse("generate-game"),
            data=json.dumps(
                payload
                or {
                    "cover_topics": ["loops", "functions"],
                    "emphasize_topics": ["arrays"],
                    "problem_types": ["solution comparison"],
                }
            ),
            content_type="application/json",
        )

    def test_generate_game_uses_teacher_settings(self):
        response = self.post_game_generation()

        self.assertEqual(response.status_code, 200)
        self.assert_game_response_contract(response.json())

    def test_generate_game_randomizes_answers_for_variables_solution_comparison(self):
        response = self.post_game_generation(
            payload={
                "cover_topics": ["variables"],
                "emphasize_topics": ["variables"],
                "problem_types": ["solution comparison"],
            }
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        correct_ids = {
            task["correct_solution_id"] for task in payload["game"]["tasks"]
        }
        self.assertGreater(len(correct_ids), 1)

    def test_generate_game_allows_csrf_enforced_json_post_without_token(self):
        csrf_enforced_client = Client(enforce_csrf_checks=True)

        response = self.post_game_generation(csrf_enforced_client)

        self.assertEqual(response.status_code, 200)
        self.assert_game_response_contract(response.json())

    def test_generate_game_rejects_non_post_requests(self):
        response = self.client.get(reverse("generate-game"))

        self.assertEqual(response.status_code, 405)
