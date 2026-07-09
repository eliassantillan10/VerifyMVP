import json

from django.test import SimpleTestCase
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
    def test_generate_game_uses_teacher_settings(self):
        response = self.client.post(
            reverse("generate-game"),
            data=json.dumps(
                {
                    "cover_topics": ["loops", "functions"],
                    "emphasize_topics": ["arrays"],
                    "problem_types": ["solution comparison"],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

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
        self.assertEqual(first_task["correct_solution_id"], "A")
        self.assertEqual(len(first_task["candidate_solutions"]), 3)
        self.assertIn("explanation", first_task)
