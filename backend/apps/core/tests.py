import json
import re

from django.test import Client, SimpleTestCase
from django.urls import reverse

from apps.core.game_generation import (
    CS1_DEFAULT_TOPICS,
    TOPIC_LABELS,
    TOPIC_PROFILES,
    GameSettings,
    build_game_response,
)

EXPECTED_TOPIC_LABELS = {
    "variables": "Variables",
    "primitive-data-types": "Primitive data types",
    "operations": "Operations",
    "iostream": "iostream input/output",
    "if": "if statements",
    "else-if": "else if statements",
    "else": "else statements",
    "switch": "switch statements",
    "compound-boolean-expressions": "Compound boolean expressions",
    "order-of-precedence": "Order of precedence",
    "while-loops": "while loops",
    "do-while-loops": "do-while loops",
    "strings": "string methods and manipulation",
    "for-loops": "for loops",
    "for-each-loops": "for-each loops",
    "arrays": "arrays",
    "vectors": "vectors",
    "functions": "functions and function prototypes",
    "pass-by-reference": "pass-by-reference",
    "pass-by-value": "pass-by-value",
    "fstream": "fstream file input/output",
    "structs": "structs",
    "classes": "classes",
    "pointers": "pointers",
}


def game_signature(payload):
    return tuple(
        (
            task["prompt"],
            task["specifications"],
            tuple(
                (candidate["id"], candidate["code"])
                for candidate in task["candidate_solutions"]
            ),
            task["correct_solution_id"],
            task["explanation"],
        )
        for task in payload["game"]["tasks"]
    )


def normalized_specification(task):
    specification = task["specifications"].lower()
    specification = re.sub(r"`check_[^`]+`", "`check_function`", specification)
    return " ".join(specification.split())


def normalized_correct_solution(task):
    correct_id = task["correct_solution_id"]
    code = next(
        candidate["code"]
        for candidate in task["candidate_solutions"]
        if candidate["id"] == correct_id
    )
    code = re.sub(r"bool check_[^(]+\([^)]*\) \{", "bool check_function() {", code)
    code = re.sub(r"\s*// context:[^\n]+", "", code)
    return " ".join(code.split())


def task_topic(task):
    text = f"{task['prompt']} {task['specifications']}".lower()
    for topic in CS1_DEFAULT_TOPICS:
        label = re.escape(TOPIC_LABELS[topic].lower())
        if re.search(rf"(?:focused on|covers) {label}(?: while|\.)", text):
            return topic
        if re.search(rf"debug .*{label}", text):
            return topic
    raise AssertionError(f"Could not identify covered topic in task text: {text}")


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


class CaseBreakerEndpointTests(SimpleTestCase):
    def test_challenge_hides_the_oracle_and_grades_a_counterexample(self):
        response = self.client.post(
            reverse("case-breaker-challenge"),
            data=json.dumps({"learner_profile": {"if": {"attempts": 1, "passes": 0}}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        challenge = response.json()["challenge"]
        self.assertIn(challenge["topic"], TOPIC_LABELS)
        self.assertIn("code", challenge)
        self.assertIn("input_schema", challenge)
        self.assertNotIn("explanation", challenge)
        self.assertNotIn("hints", challenge)
        self.assertNotIn("expected_output", challenge)

        failed = self.client.post(
            reverse("case-breaker-grade"),
            data=json.dumps(
                {
                    "challenge_token": challenge["challenge_token"],
                    "test_case": {"value": 5, "low": 0, "high": 10},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(failed.status_code, 200)
        self.assertFalse(failed.json()["is_breaking"])
        self.assertIn("hint", failed.json())
        self.assertNotIn("explanation", failed.json())

        passed = self.client.post(
            reverse("case-breaker-grade"),
            data=json.dumps(
                {
                    "challenge_token": challenge["challenge_token"],
                    "test_case": {"value": 11, "low": 0, "high": 10},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(passed.status_code, 200)
        self.assertTrue(passed.json()["is_breaking"])
        self.assertIn("explanation", passed.json())


class GameGenerationTests(SimpleTestCase):
    def test_topic_contract_contains_exactly_twenty_four_atomic_cpp_topics(self):
        self.assertEqual(CS1_DEFAULT_TOPICS, list(EXPECTED_TOPIC_LABELS))
        self.assertEqual(TOPIC_LABELS, EXPECTED_TOPIC_LABELS)

    def assert_game_response_contract(self, payload):
        self.assertEqual(
            payload["settings"]["cover_topics"], ["for-loops", "functions"]
        )
        self.assertEqual(payload["settings"]["emphasize_topics"], ["functions"])
        self.assertNotIn("problem_types", payload["settings"])
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
            self.assertEqual(candidate_ids, {"A", "B", "C"})
            self.assertIn(task["correct_solution_id"], candidate_ids)

            for candidate in task["candidate_solutions"]:
                self.assertIn("bool check_", candidate["code"])
                self.assertNotIn("def check_", candidate["code"])

    def post_game_generation(self, client=None, payload=None):
        test_client = client or self.client
        return test_client.post(
            reverse("generate-game"),
            data=json.dumps(
                payload
                or {
                    "cover_topics": ["for-loops", "functions"],
                    "emphasize_topics": ["functions"],
                }
            ),
            content_type="application/json",
        )

    def test_generate_game_uses_student_topic_settings(self):
        response = self.post_game_generation()

        self.assertEqual(response.status_code, 200)
        self.assert_game_response_contract(response.json())

    def test_generate_game_randomizes_answers_for_variables_solution_comparison(self):
        response = self.post_game_generation(
            payload={
                "cover_topics": ["variables"],
                "emphasize_topics": ["variables"],
            }
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        correct_ids = {
            task["correct_solution_id"] for task in payload["game"]["tasks"]
        }
        self.assertGreater(len(correct_ids), 1)

    def test_generate_game_rejects_missing_mandatory_settings(self):
        response = self.post_game_generation(
            payload={
                "cover_topics": [],
                "emphasize_topics": [],
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"error": "Select at least one topic to cover."}
        )

    def test_generate_game_rejects_emphasis_outside_cover_topics(self):
        response = self.post_game_generation(
            payload={
                "cover_topics": ["variables"],
                "emphasize_topics": ["pointers"],
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": (
                    "Topics to emphasize must also be selected as topics to cover."
                )
            },
        )

    def test_generate_game_rejects_unsupported_topic_ids(self):
        response = self.post_game_generation(
            payload={"cover_topics": ["loops"], "emphasize_topics": []}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"error": "Select only supported topics to cover."}
        )

    def test_generate_game_ignores_legacy_problem_types(self):
        response = self.post_game_generation(
            payload={
                "cover_topics": ["variables"],
                "problem_types": ["debugging"],
            }
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("problem_types", payload["settings"])
        self.assertIn("best implementation", json.dumps(payload["game"]).lower())

    def test_generate_game_allows_csrf_enforced_json_post_without_token(self):
        csrf_enforced_client = Client(enforce_csrf_checks=True)

        response = self.post_game_generation(csrf_enforced_client)

        self.assertEqual(response.status_code, 200)
        self.assert_game_response_contract(response.json())

    def test_generate_game_rejects_non_post_requests(self):
        response = self.client.get(reverse("generate-game"))

        self.assertEqual(response.status_code, 405)


class GameGeneratorTests(SimpleTestCase):
    def test_every_atomic_topic_has_a_dedicated_profile(self):
        self.assertTrue(set(CS1_DEFAULT_TOPICS).issubset(TOPIC_PROFILES))
        for topic in CS1_DEFAULT_TOPICS:
            with self.subTest(topic=topic):
                self.assertNotEqual(TOPIC_PROFILES[topic].stems, ("generic_check",))

    def test_all_selected_settings_produce_semantically_distinct_tasks(self):
        payload = build_game_response(
            GameSettings(
                cover_topics=CS1_DEFAULT_TOPICS,
                emphasize_topics=CS1_DEFAULT_TOPICS,
                problem_types=["solution comparison"],
            ),
            variant="all-selected-a",
        )

        tasks = payload["game"]["tasks"]
        self.assertEqual(len(tasks), 5)
        task_text = json.dumps(tasks).lower()
        topic_signatures = {task_topic(task) for task in tasks}
        self.assertEqual(len(topic_signatures), 5)
        self.assertIn("best implementation", task_text)
        self.assertNotIn("all listed constraints", task_text)
        self.assertNotIn("debug this", task_text)
        self.assertEqual(
            len({normalized_specification(task) for task in tasks}),
            len(tasks),
        )
        self.assertEqual(
            len({normalized_correct_solution(task) for task in tasks}),
            len(tasks),
        )

    def test_same_settings_and_variant_are_deterministic(self):
        settings = GameSettings(
            cover_topics=["for-loops"],
            emphasize_topics=["for-loops"],
            problem_types=["solution comparison"],
        )

        first = build_game_response(settings, variant="variant-a")
        second = build_game_response(settings, variant="variant-a")

        self.assertEqual(game_signature(first), game_signature(second))

    def test_same_settings_with_different_variants_produce_different_games(self):
        settings = GameSettings(
            cover_topics=["for-loops"],
            emphasize_topics=["for-loops"],
            problem_types=["solution comparison"],
        )

        first = build_game_response(settings, variant="variant-a")
        second = build_game_response(settings, variant="variant-b")

        self.assertNotEqual(game_signature(first), game_signature(second))

    def test_student_topic_settings_change_visible_content(self):
        loops_game = build_game_response(
            GameSettings(
                cover_topics=["for-loops"],
                emphasize_topics=["for-loops"],
                problem_types=["solution comparison"],
            ),
            variant="variant-a",
        )
        strings_game = build_game_response(
            GameSettings(
                cover_topics=["strings"],
                emphasize_topics=["strings"],
                problem_types=["debugging"],
            ),
            variant="variant-a",
        )

        self.assertNotEqual(game_signature(loops_game), game_signature(strings_game))
        strings_text = json.dumps(strings_game["game"]["tasks"])
        self.assertIn(TOPIC_LABELS["strings"], strings_text)
        self.assertIn("best implementation", strings_text.lower())

    def test_generator_always_uses_solution_comparison_mechanics(self):
        settings = GameSettings(
            cover_topics=["arrays"],
            emphasize_topics=["arrays"],
            problem_types=[
                "solution comparison",
                "specification checking",
                "debugging",
            ],
        )

        payload = build_game_response(settings, variant="variant-c")
        prompts = " ".join(task["prompt"].lower() for task in payload["game"]["tasks"])
        explanations = " ".join(
            task["explanation"].lower() for task in payload["game"]["tasks"]
        )

        self.assertIn("best implementation", prompts)
        self.assertNotIn("all listed constraints", prompts)
        self.assertNotIn("debug", prompts)
        self.assertIn("only implementation", explanations)

    def test_unknown_topics_are_rejected_by_the_generator(self):
        settings = GameSettings(
            cover_topics=["pointers & memory!"],
            emphasize_topics=[],
            problem_types=["custom review"],
        )

        with self.assertRaisesRegex(
            ValueError, "Select only supported topics to cover."
        ):
            build_game_response(settings, variant="variant-a")

    def test_empty_direct_settings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Select at least one topic to cover."):
            build_game_response(
                GameSettings(cover_topics=[], emphasize_topics=[], problem_types=[]),
                variant="variant-a",
            )
