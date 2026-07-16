# ruff: noqa: E501

import json
import random
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GameSettings:
    cover_topics: list[str]
    emphasize_topics: list[str]
    problem_types: list[str]


@dataclass(frozen=True)
class TopicProfile:
    contexts: tuple[str, ...]
    stems: tuple[str, ...]
    params: str
    requirements: tuple[str, ...]
    correct_bodies: tuple[str, ...]
    constraint_distractors: tuple[str, ...]
    bug_bodies: tuple[str, ...]


@dataclass(frozen=True)
class TaskBlueprint:
    topic: str
    emphasis: str | None
    problem_type: str
    variant: int


CS1_DEFAULT_TOPICS = [
    "variables",
    "primitive-data-types",
    "operations",
    "iostream",
    "if",
    "else-if",
    "else",
    "switch",
    "compound-boolean-expressions",
    "order-of-precedence",
    "while-loops",
    "do-while-loops",
    "strings",
    "for-loops",
    "for-each-loops",
    "arrays",
    "vectors",
    "functions",
    "pass-by-reference",
    "pass-by-value",
    "fstream",
    "structs",
    "classes",
    "pointers",
]

TOPIC_LABELS = {
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

DEFAULT_EMPHASIS_TOPICS: list[str] = []
SOLUTION_COMPARISON = "solution comparison"

TASK_COUNT = 5
LABELS = ["A", "B", "C"]
MAX_DIVERSITY_ATTEMPTS = 8
SOLUTION_COMPARISON_PROMPTS = (
    "Choose the best implementation for this {problem_type} task about {topic}.",
    "Review the candidates and choose the best implementation for this {topic} task.",
    "Choose the best implementation that demonstrates {topic} in this task.",
)
SPECIFICATION_CHECKING_PROMPTS = (
    (
        "Select the solution that meets all listed constraints for this "
        "{problem_type} task."
    ),
    "Check every candidate and select the solution that meets all listed constraints.",
    "Select the candidate that satisfies all listed constraints in this {topic} task.",
)
DEBUGGING_PROMPTS = (
    "Debug this {topic} function by choosing the corrected implementation.",
    "Debug the faulty {topic} implementation and choose the corrected version.",
    "Debug this task by selecting the corrected {topic} function.",
)
SCORING = {
    "correctness_points": 100,
    "time_bonus_points": 25,
    "fast_answer_threshold_ms": 8000,
}

TOPIC_PROFILES: dict[str, TopicProfile] = {
    "variables": TopicProfile(
        contexts=("score threshold", "inventory count", "running total"),
        stems=("variables_total", "variables_threshold", "variables_balance"),
        params="int raw, int adjustment, int target",
        requirements=(
            "combine the raw value with the adjustment before comparing",
            "store the intermediate total before returning the decision",
            "avoid comparing the adjustment by itself",
        ),
        correct_bodies=(
            "    int total = raw + adjustment;\n    return total >= target;",
            "    int adjusted = raw - adjustment;\n    return adjusted <= target;",
        ),
        constraint_distractors=(
            "    int total = raw;\n    return total >= target;",
            "    return adjustment >= target;",
            "    int total = raw + target;\n    return total >= adjustment;",
        ),
        bug_bodies=(
            "    int total = raw;\n    return total >= target;",
            "    int total = adjustment - raw;\n    return total >= target;",
        ),
    ),
    "iostream": TopicProfile(
        contexts=("console score entry", "menu choice input", "numeric prompt"),
        stems=("iostream_read", "iostream_prompt", "iostream_extract"),
        params="std::istream& input, int minimum",
        requirements=(
            "read one integer from the input stream before comparing it",
            "reject failed extractions instead of trusting an old value",
            "use stream extraction instead of hard-coded input",
        ),
        correct_bodies=(
            (
                "    int value = 0;\n"
                "    input >> value;\n"
                "    return input && value >= minimum;"
            ),
            (
                "    int choice = 0;\n"
                "    if (!(input >> choice)) {\n"
                "        return false;\n"
                "    }\n"
                "    return choice == minimum;"
            ),
        ),
        constraint_distractors=(
            "    int value = minimum;\n    return value >= minimum;",
            "    int value = 0;\n    return value >= minimum;",
            (
                "    int value = 0;\n"
                "    input >> value;\n"
                "    return minimum >= 0;"
            ),
        ),
        bug_bodies=(
            "    int value = minimum;\n    return value >= minimum;",
            "    int value = 0;\n    return value >= minimum;",
        ),
    ),
    "conditionals": TopicProfile(
        contexts=("grade boundary", "access rule", "temperature alert"),
        stems=("conditionals_range", "conditionals_gate", "conditionals_alert"),
        params="int value, int low, int high",
        requirements=(
            "accept values inside the inclusive range",
            "reject values below the lower bound or above the upper bound",
            "use both sides of the condition instead of only one boundary",
        ),
        correct_bodies=(
            "    return value >= low && value <= high;",
            (
                "    if (value < low) {\n"
                "        return false;\n"
                "    }\n"
                "    return value <= high;"
            ),
        ),
        constraint_distractors=(
            "    return value > low && value < high;",
            "    return value >= low || value <= high;",
            "    return value <= low && value >= high;",
        ),
        bug_bodies=(
            "    return value >= low || value <= high;",
            "    return value > low && value < high;",
        ),
    ),
    "boolean-expressions": TopicProfile(
        contexts=("eligibility rule", "safety gate", "discount policy"),
        stems=("boolean_precedence", "boolean_gate", "boolean_policy"),
        params="bool hasPass, bool isMember, bool isBlocked",
        requirements=(
            "combine &&, ||, and ! with explicit grouping",
            "deny blocked users even when another condition is true",
            "preserve the intended operator precedence with parentheses",
        ),
        correct_bodies=(
            "    return (hasPass || isMember) && !isBlocked;",
            "    return hasPass && (!isBlocked || isMember);",
        ),
        constraint_distractors=(
            "    return hasPass || isMember && !isBlocked;",
            "    return (hasPass || isMember) && isBlocked;",
            "    return hasPass && isMember && !isBlocked;",
        ),
        bug_bodies=(
            "    return hasPass || isMember && !isBlocked;",
            "    return (hasPass || isMember) && isBlocked;",
        ),
    ),
    "while-loops": TopicProfile(
        contexts=("retry counter", "sentinel scan", "countdown"),
        stems=("while_retry", "while_sentinel", "while_countdown"),
        params="int start, int stop",
        requirements=(
            "use a while or do-while loop to advance toward the stop value",
            "update the loop variable so the loop can terminate",
            "handle the first iteration correctly when start already meets stop",
        ),
        correct_bodies=(
            (
                "    int current = start;\n"
                "    while (current < stop) {\n"
                "        ++current;\n"
                "    }\n"
                "    return current == stop;"
            ),
            (
                "    int current = start;\n"
                "    do {\n"
                "        --current;\n"
                "    } while (current > stop);\n"
                "    return current <= stop;"
            ),
        ),
        constraint_distractors=(
            (
                "    int current = start;\n"
                "    while (current < stop) {\n"
                "        return true;\n"
                "    }\n"
                "    return current == stop;"
            ),
            (
                "    int current = start;\n"
                "    while (current < stop) {\n"
                "        --current;\n"
                "    }\n"
                "    return current == stop;"
            ),
            "    return start == stop;",
        ),
        bug_bodies=(
            (
                "    int current = start;\n"
                "    while (current < stop) {\n"
                "        return true;\n"
                "    }\n"
                "    return current == stop;"
            ),
            (
                "    int current = start;\n"
                "    while (current < stop) {\n"
                "        --current;\n"
                "    }\n"
                "    return current == stop;"
            ),
        ),
    ),
    "loops": TopicProfile(
        contexts=("counter scan", "retry budget", "range check"),
        stems=("loops_count", "loops_scan", "loops_limit"),
        params="int limit",
        requirements=(
            "visit every value from zero up to but not including the limit",
            "accumulate one count for each loop iteration",
            "handle a zero limit without entering the loop",
        ),
        correct_bodies=(
            (
                "    int count = 0;\n"
                "    for (int i = 0; i < limit; ++i) {\n"
                "        count += 1;\n"
                "    }\n"
                "    return count == limit;"
            ),
            (
                "    int sum = 0;\n"
                "    for (int i = 1; i <= limit; ++i) {\n"
                "        sum += i;\n"
                "    }\n"
                "    return limit <= 0 || sum >= limit;"
            ),
        ),
        constraint_distractors=(
            (
                "    int count = 0;\n"
                "    for (int i = 0; i <= limit; ++i) {\n"
                "        count += 1;\n"
                "    }\n"
                "    return count == limit;"
            ),
            "    return limit > 0;",
            (
                "    int count = 0;\n"
                "    for (int i = 1; i < limit; ++i) {\n"
                "        count += 1;\n"
                "    }\n"
                "    return count == limit;"
            ),
        ),
        bug_bodies=(
            (
                "    int count = 0;\n"
                "    for (int i = 0; i <= limit; ++i) {\n"
                "        count += 1;\n"
                "    }\n"
                "    return count == limit;"
            ),
            (
                "    int count = 0;\n"
                "    while (count < limit) {\n"
                "        return true;\n"
                "    }\n"
                "    return false;"
            ),
        ),
    ),
    "for-loops": TopicProfile(
        contexts=("indexed scan", "range-based total", "bounded count"),
        stems=("for_index", "for_range", "for_count"),
        params="const std::vector<int>& values, int target",
        requirements=(
            "use a traditional for loop or range-based for loop over the data",
            "visit every element without skipping the first or last item",
            "return true only when a loop iteration finds the target",
        ),
        correct_bodies=(
            (
                "    for (int value : values) {\n"
                "        if (value == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            (
                "    for (std::size_t i = 0; i < values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
        ),
        constraint_distractors=(
            "    return !values.empty() && values[0] == target;",
            (
                "    for (std::size_t i = 0; i <= values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            "    return values.size() == static_cast<std::size_t>(target);",
        ),
        bug_bodies=(
            (
                "    for (std::size_t i = 0; i <= values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            "    return !values.empty() && values[0] == target;",
        ),
    ),
    "arrays-vectors": TopicProfile(
        contexts=("vector search", "array boundary", "collection lookup"),
        stems=("arrays_vectors_scan", "arrays_vectors_index", "arrays_vectors_match"),
        params="const std::vector<int>& values, int target",
        requirements=(
            "inspect the vector elements without reading past the end",
            "use the collection contents instead of only the collection size",
            "handle an empty vector by returning false",
        ),
        correct_bodies=(
            (
                "    for (std::size_t i = 0; i < values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            (
                "    for (int value : values) {\n"
                "        if (value == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
        ),
        constraint_distractors=(
            "    return !values.empty() && values[0] == target;",
            (
                "    for (std::size_t i = 0; i <= values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            "    return values.size() == static_cast<std::size_t>(target);",
        ),
        bug_bodies=(
            (
                "    for (std::size_t i = 0; i <= values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            "    return values.size() == static_cast<std::size_t>(target);",
        ),
    ),
    "functions": TopicProfile(
        contexts=("helper function", "return contract", "parameter check"),
        stems=("functions_helper", "functions_contract", "functions_return"),
        params="int first, int second",
        requirements=(
            "return the result instead of only computing it locally",
            "use both parameters when making the decision",
            "keep the helper free of hard-coded constants",
        ),
        correct_bodies=(
            (
                "    int larger = first > second ? first : second;\n"
                "    return larger == first;"
            ),
            "    return (first + second) % 2 == 0;",
        ),
        constraint_distractors=(
            "    int larger = first > second ? first : second;\n    return true;",
            "    return first > 0;",
            "    int larger = first;\n    return larger == second;",
        ),
        bug_bodies=(
            "    int larger = first > second ? first : second;\n    return true;",
            "    int larger = first + second;\n    return larger == first;",
        ),
    ),
    "reference-value-parameters": TopicProfile(
        contexts=("update helper", "swap operation", "copy check"),
        stems=("parameters_reference", "parameters_value", "parameters_update"),
        params="int value, int& output",
        requirements=(
            "modify the reference parameter when the input is valid",
            "avoid pretending a pass-by-value copy updates the caller",
            "return whether the reference output received the intended value",
        ),
        correct_bodies=(
            (
                "    output = value * 2;\n"
                "    return output == value * 2;"
            ),
            (
                "    int copy = value;\n"
                "    output = copy + 1;\n"
                "    return output > value;"
            ),
        ),
        constraint_distractors=(
            "    int outputCopy = value * 2;\n    return outputCopy == value * 2;",
            "    return output == value;",
            "    value = output;\n    return value > 0;",
        ),
        bug_bodies=(
            "    int outputCopy = value * 2;\n    return outputCopy == value * 2;",
            "    return output == value;",
        ),
    ),
    "fstream": TopicProfile(
        contexts=("file score import", "configuration file", "saved total"),
        stems=("fstream_read", "fstream_open", "fstream_extract"),
        params="const std::string& path, int minimum",
        requirements=(
            "open an input file stream before reading from the file",
            "check that file extraction succeeds before comparing the value",
            "use the file contents instead of the file path text",
        ),
        correct_bodies=(
            (
                "    std::ifstream file(path);\n"
                "    int value = 0;\n"
                "    file >> value;\n"
                "    return file && value >= minimum;"
            ),
            (
                "    std::ifstream file(path);\n"
                "    int stored = 0;\n"
                "    if (!(file >> stored)) {\n"
                "        return false;\n"
                "    }\n"
                "    return stored == minimum;"
            ),
        ),
        constraint_distractors=(
            "    return !path.empty();",
            "    int value = minimum;\n    return value >= minimum;",
            (
                "    std::ifstream file(path);\n"
                "    return file.good();"
            ),
        ),
        bug_bodies=(
            "    return !path.empty();",
            (
                "    std::ifstream file(path);\n"
                "    return file.good();"
            ),
        ),
    ),
    "structs": TopicProfile(
        contexts=("score record", "point pair", "student total"),
        stems=("structs_record", "structs_fields", "structs_total"),
        params="int earned, int possible",
        requirements=(
            "group related values in a struct before checking the result",
            "read the intended struct fields instead of swapping their meaning",
            "use the struct data to decide whether the score passes",
        ),
        correct_bodies=(
            (
                "    struct Score {\n"
                "        int earned;\n"
                "        int possible;\n"
                "    };\n"
                "    Score score{earned, possible};\n"
                "    return score.possible > 0 && score.earned * 2 >= score.possible;"
            ),
            (
                "    struct Pair {\n"
                "        int left;\n"
                "        int right;\n"
                "    };\n"
                "    Pair values{earned, possible};\n"
                "    return values.left <= values.right;"
            ),
        ),
        constraint_distractors=(
            (
                "    struct Score {\n"
                "        int earned;\n"
                "        int possible;\n"
                "    };\n"
                "    Score score{possible, earned};\n"
                "    return score.earned * 2 >= score.possible;"
            ),
            "    return earned > 0;",
            "    return possible > 0;",
        ),
        bug_bodies=(
            (
                "    struct Score {\n"
                "        int earned;\n"
                "        int possible;\n"
                "    };\n"
                "    Score score{possible, earned};\n"
                "    return score.earned * 2 >= score.possible;"
            ),
            "    return earned > 0;",
        ),
    ),
    "classes": TopicProfile(
        contexts=("account object", "score keeper", "encapsulated counter"),
        stems=("classes_encapsulation", "classes_method", "classes_private"),
        params="int initial, int delta",
        requirements=(
            "keep object state private and expose behavior through a method",
            "construct an object before asking it for the result",
            "use the class method instead of duplicating hidden state logic",
        ),
        correct_bodies=(
            (
                "    class Counter {\n"
                "    public:\n"
                "        explicit Counter(int value) : value_(value) {}\n"
                "        bool reaches(int deltaValue) const {\n"
                "            return value_ + deltaValue >= 0;\n"
                "        }\n"
                "    private:\n"
                "        int value_;\n"
                "    };\n"
                "    Counter counter(initial);\n"
                "    return counter.reaches(delta);"
            ),
            (
                "    class Score {\n"
                "    public:\n"
                "        Score(int earned, int bonus)\n"
                "            : earned_(earned), bonus_(bonus) {}\n"
                "        bool passes() const {\n"
                "            return earned_ + bonus_ >= 10;\n"
                "        }\n"
                "    private:\n"
                "        int earned_;\n"
                "        int bonus_;\n"
                "    };\n"
                "    Score score(initial, delta);\n"
                "    return score.passes();"
            ),
        ),
        constraint_distractors=(
            "    return initial >= 0;",
            (
                "    class Counter {\n"
                "    public:\n"
                "        int value;\n"
                "    };\n"
                "    Counter counter{initial};\n"
                "    return counter.value == delta;"
            ),
            "    return delta >= 0;",
        ),
        bug_bodies=(
            "    return initial >= 0;",
            (
                "    class Counter {\n"
                "    public:\n"
                "        int value;\n"
                "    };\n"
                "    Counter counter{initial};\n"
                "    return counter.value == delta;"
            ),
        ),
    ),
    "pointers": TopicProfile(
        contexts=("optional score", "nullable input", "address check"),
        stems=("pointers_null", "pointers_deref", "pointers_target"),
        params="const int* value, int target",
        requirements=(
            "check for nullptr before dereferencing the pointer",
            "compare the pointed-to value instead of the pointer address",
            "return false when no valid pointee is available",
        ),
        correct_bodies=(
            "    return value != nullptr && *value >= target;",
            (
                "    if (value == nullptr) {\n"
                "        return false;\n"
                "    }\n"
                "    return *value == target;"
            ),
        ),
        constraint_distractors=(
            "    return value != nullptr;",
            "    return *value == target;",
            "    return value == nullptr || *value >= target;",
        ),
        bug_bodies=(
            "    return *value == target;",
            "    return value != nullptr;",
        ),
    ),
    "arrays": TopicProfile(
        contexts=("array scan", "index boundary", "collection minimum"),
        stems=("arrays_scan", "arrays_index", "arrays_match"),
        params="const std::vector<int>& values, int target",
        requirements=(
            "inspect every element without reading past the vector",
            "return true only when an element matches the target",
            "handle an empty vector by returning false",
        ),
        correct_bodies=(
            (
                "    for (int value : values) {\n"
                "        if (value == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            (
                "    for (std::size_t i = 0; i < values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
        ),
        constraint_distractors=(
            "    return !values.empty() && values[0] == target;",
            (
                "    for (std::size_t i = 0; i <= values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            "    return values.size() == static_cast<std::size_t>(target);",
        ),
        bug_bodies=(
            (
                "    for (std::size_t i = 0; i <= values.size(); ++i) {\n"
                "        if (values[i] == target) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            "    return !values.empty() && values[0] == target;",
        ),
    ),
    "strings": TopicProfile(
        contexts=("string prefix", "character scan", "input validation"),
        stems=("strings_prefix", "strings_scan", "strings_validate"),
        params="const std::string& text, char expected",
        requirements=(
            "check the characters in the string without changing the input",
            "handle an empty string before reading the first character",
            "return true only when the expected character is present",
        ),
        correct_bodies=(
            (
                "    for (char letter : text) {\n"
                "        if (letter == expected) {\n"
                "            return true;\n"
                "        }\n"
                "    }\n"
                "    return false;"
            ),
            (
                "    if (text.empty()) {\n"
                "        return false;\n"
                "    }\n"
                "    return text[0] == expected;"
            ),
        ),
        constraint_distractors=(
            "    return text[0] == expected;",
            "    return !text.empty();",
            (
                "    for (char letter : text) {\n"
                "        return letter == expected;\n"
                "    }\n"
                "    return false;"
            ),
        ),
        bug_bodies=(
            "    return text[0] == expected;",
            (
                "    for (char letter : text) {\n"
                "        return letter != expected;\n"
                "    }\n"
                "    return false;"
            ),
        ),
    ),
}


def _atomic_profile(
    stem: str,
    params: str,
    requirement: str,
    correct_body: str,
    first_distractor: str,
    second_distractor: str,
) -> TopicProfile:
    """Build one isolated profile for an atomic CS1 concept."""
    return TopicProfile(
        contexts=("focused CS1 practice",),
        stems=(stem,),
        params=params,
        requirements=(requirement,),
        correct_bodies=(correct_body,),
        constraint_distractors=(first_distractor, second_distractor),
        bug_bodies=(first_distractor, second_distractor),
    )


TOPIC_PROFILES.update(
    {
        "primitive-data-types": _atomic_profile(
            "primitive_type",
            "int itemCount, double average",
            "preserve the fractional average in a double value",
            "    return average >= static_cast<double>(itemCount);",
            "    return static_cast<int>(average) >= itemCount;",
            "    return itemCount >= 0;",
        ),
        "operations": _atomic_profile(
            "operations_total",
            "int earned, int bonus, int target",
            "add the earned points and bonus before comparing with the target",
            "    return earned + bonus >= target;",
            "    return earned >= target;",
            "    return earned - bonus >= target;",
        ),
        "if": _atomic_profile(
            "if_guard",
            "int value, int minimum",
            "use an if statement to accept a value at or above the minimum",
            "    if (value >= minimum) {\n        return true;\n    }\n    return false;",
            "    return value >= minimum;",
            "    if (value < minimum) {\n        return true;\n    }\n    return false;",
        ),
        "else-if": _atomic_profile(
            "else_if_band",
            "int score",
            "use an else-if branch to identify a score in the middle band",
            "    if (score < 60) {\n        return false;\n    } else if (score < 80) {\n        return true;\n    }\n    return false;",
            "    if (score < 80) {\n        return true;\n    }\n    return false;",
            "    if (score < 60) {\n        return false;\n    } else if (score >= 80) {\n        return true;\n    }\n    return false;",
        ),
        "else": _atomic_profile(
            "else_fallback",
            "bool isComplete",
            "use an else branch to return false when the condition is not met",
            "    if (isComplete) {\n        return true;\n    } else {\n        return false;\n    }",
            "    if (isComplete) {\n        return true;\n    }\n    return true;",
            "    return isComplete;",
        ),
        "switch": _atomic_profile(
            "switch_case",
            "int menuChoice",
            "use switch cases to accept only menu choices one or two",
            "    switch (menuChoice) {\n    case 1:\n    case 2:\n        return true;\n    default:\n        return false;\n    }",
            "    return menuChoice > 0;",
            "    switch (menuChoice) {\n    case 1:\n        return true;\n    default:\n        return true;\n    }",
        ),
        "compound-boolean-expressions": _atomic_profile(
            "compound_boolean",
            "bool hasPass, bool hasPermission, bool isBlocked",
            "combine permission alternatives while rejecting blocked users",
            "    return (hasPass || hasPermission) && !isBlocked;",
            "    return hasPass || hasPermission && !isBlocked;",
            "    return (hasPass || hasPermission) && isBlocked;",
        ),
        "order-of-precedence": _atomic_profile(
            "precedence_grouping",
            "bool hasPass, bool isMember, bool isBlocked",
            "use parentheses so membership or a pass is checked before blocking",
            "    return (hasPass || isMember) && !isBlocked;",
            "    return hasPass || isMember && !isBlocked;",
            "    return hasPass || (isMember && isBlocked);",
        ),
        "while-loops": _atomic_profile(
            "while_count",
            "int start, int stop",
            "use a while loop that advances toward the stop value",
            "    while (start < stop) {\n        ++start;\n    }\n    return start == stop;",
            "    while (start < stop) {\n        --start;\n    }\n    return start == stop;",
            "    return start < stop;",
        ),
        "do-while-loops": _atomic_profile(
            "do_while_count",
            "int start, int stop",
            "use a do-while loop that executes once before checking its stop condition",
            "    do {\n        ++start;\n    } while (start < stop);\n    return start >= stop;",
            "    while (start < stop) {\n        ++start;\n    }\n    return start >= stop;",
            "    do {\n        --start;\n    } while (start < stop);\n    return start >= stop;",
        ),
        "for-loops": _atomic_profile(
            "for_count",
            "int limit",
            "use a traditional for loop to count exactly limit iterations",
            "    int count = 0;\n    for (int index = 0; index < limit; ++index) {\n        ++count;\n    }\n    return count == limit;",
            "    int count = 0;\n    for (int index = 0; index <= limit; ++index) {\n        ++count;\n    }\n    return count == limit;",
            "    return limit > 0;",
        ),
        "for-each-loops": _atomic_profile(
            "for_each_match",
            "const std::vector<int>& values, int target",
            "use a range-based for loop to find a matching value",
            "    for (int value : values) {\n        if (value == target) {\n            return true;\n        }\n    }\n    return false;",
            "    return !values.empty() && values[0] == target;",
            "    for (int value : values) {\n        return value == target;\n    }\n    return false;",
        ),
        "arrays": _atomic_profile(
            "array_index",
            "const std::array<int, 3>& values, int target",
            "inspect the fixed-size array at each valid index",
            "    for (std::size_t index = 0; index < values.size(); ++index) {\n        if (values[index] == target) {\n            return true;\n        }\n    }\n    return false;",
            "    return values[0] == target;",
            "    return values[values.size()] == target;",
        ),
        "vectors": _atomic_profile(
            "vector_size",
            "const std::vector<int>& values, int expectedSize",
            "use vector size to verify the dynamic collection length",
            "    return values.size() == static_cast<std::size_t>(expectedSize);",
            "    return values.capacity() == static_cast<std::size_t>(expectedSize);",
            "    return !values.empty();",
        ),
        "pass-by-reference": _atomic_profile(
            "reference_update",
            "int value, int& output",
            "update the caller-provided output through a reference parameter",
            "    output = value * 2;\n    return output == value * 2;",
            "    int output = value * 2;\n    return output == value * 2;",
            "    return output == value;",
        ),
        "pass-by-value": _atomic_profile(
            "value_copy",
            "int value, int original",
            "change only the local pass-by-value copy without changing the original value",
            "    value += 1;\n    return original + 1 == value;",
            "    original += 1;\n    return original == value;",
            "    return value == original;",
        ),
    }
)

GENERIC_PROFILE = TopicProfile(
    contexts=("general CS1 check", "custom classroom rule", "practice constraint"),
    stems=("generic_check", "generic_rule", "generic_review"),
    params="int value, int target",
    requirements=(
        "compare the input against the requested target",
        "return a boolean result without hard-coding the answer",
        "keep the implementation small and explicit",
    ),
    correct_bodies=(
        "    return value == target;",
        "    int difference = value - target;\n    return difference == 0;",
    ),
    constraint_distractors=(
        "    return value != target;",
        "    return target > 0;",
        "    return value > 0;",
    ),
    bug_bodies=(
        "    return value != target;",
        "    int difference = target - value;\n    return difference > 0;",
    ),
)


def normalize_settings_payload(payload: Mapping[str, object]) -> GameSettings:
    return _validate_settings(
        GameSettings(
            cover_topics=_normalize_items(payload.get("cover_topics")),
            emphasize_topics=_normalize_items(payload.get("emphasize_topics")),
            problem_types=[SOLUTION_COMPARISON],
        )
    )


def build_game_response(settings: GameSettings, variant: str | None = None) -> dict:
    settings = _normalize_settings(settings)
    variant_seed = variant or secrets.token_hex(8)
    rng = random.Random(f"{_settings_fingerprint(settings)}|{variant_seed}")
    tasks = []
    used_names: set[str] = set()
    used_specifications: dict[str, int] = {}
    used_correct_solutions: dict[str, int] = {}
    correct_label_offset = rng.randrange(len(LABELS))

    for index, blueprint in enumerate(_build_blueprints(settings, rng)):
        task = _build_task(
            blueprint=blueprint,
            index=index,
            rng=rng,
            correct_position=(index + correct_label_offset) % len(LABELS),
            used_names=used_names,
            used_specifications=used_specifications,
            used_correct_solutions=used_correct_solutions,
        )
        tasks.append(task)
        specification = _specification_signature(task["specifications"])
        correct_solution = _correct_solution_signature(task)
        used_specifications[specification] = used_specifications.get(
            specification, 0
        ) + 1
        used_correct_solutions[correct_solution] = (
            used_correct_solutions.get(correct_solution, 0) + 1
        )

    rng.shuffle(tasks)
    for index, task in enumerate(tasks, start=1):
        task["id"] = f"task-{index}"

    return {
        "settings": {
            "cover_topics": settings.cover_topics,
            "emphasize_topics": settings.emphasize_topics,
        },
        "game": {
            "title": "CS1 Solution Spotlight",
            "tasks": tasks,
            "scoring": SCORING,
        },
    }


def _normalize_items(values: object) -> list[str]:
    if not isinstance(values, list):
        return []

    items = []
    seen = set()
    for item in values:
        normalized = str(item).strip()
        if normalized and normalized not in seen:
            items.append(normalized)
            seen.add(normalized)
    return items


def _normalize_settings(settings: GameSettings) -> GameSettings:
    return _validate_settings(
        GameSettings(
            cover_topics=_normalize_items(settings.cover_topics),
            emphasize_topics=_normalize_items(settings.emphasize_topics),
            problem_types=[SOLUTION_COMPARISON],
        )
    )


def _validate_settings(settings: GameSettings) -> GameSettings:
    if not settings.cover_topics:
        raise ValueError("Select at least one topic to cover.")
    unknown_cover_topics = [
        topic for topic in settings.cover_topics if topic not in TOPIC_LABELS
    ]
    if unknown_cover_topics:
        raise ValueError("Select only supported topics to cover.")

    cover_topics = set(settings.cover_topics)
    unknown_emphasis = [
        topic for topic in settings.emphasize_topics if topic not in cover_topics
    ]
    if unknown_emphasis:
        raise ValueError(
            "Topics to emphasize must also be selected as topics to cover."
        )

    return settings


def _settings_fingerprint(settings: GameSettings) -> str:
    return json.dumps(
        {
            "cover_topics": settings.cover_topics,
            "emphasize_topics": settings.emphasize_topics,
            "problem_types": settings.problem_types,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _choice_sequence(values: list[str], rng: random.Random) -> list[str]:
    if len(values) >= TASK_COUNT:
        choices = rng.sample(values, TASK_COUNT)
    else:
        choices = list(values)
        while len(choices) < TASK_COUNT:
            choices.append(rng.choice(values))
    rng.shuffle(choices)
    return choices


def _build_blueprints(
    settings: GameSettings, rng: random.Random
) -> list[TaskBlueprint]:
    topics = _choice_sequence(settings.cover_topics, rng)
    emphases: list[str | None]
    if settings.emphasize_topics:
        emphases = _choice_sequence(settings.emphasize_topics, rng)
    else:
        emphases = [None] * TASK_COUNT
    return [
        TaskBlueprint(
            topic=topics[index],
            emphasis=emphases[index],
            problem_type=SOLUTION_COMPARISON,
            variant=index,
        )
        for index in range(TASK_COUNT)
    ]


def _build_task(
    blueprint: TaskBlueprint,
    index: int,
    rng: random.Random,
    correct_position: int,
    used_names: set[str],
    used_specifications: dict[str, int],
    used_correct_solutions: dict[str, int],
) -> dict:
    builder = _build_solution_comparison_task

    attempts = []
    for _ in range(MAX_DIVERSITY_ATTEMPTS):
        task = builder(
            blueprint.topic,
            blueprint.emphasis,
            blueprint.problem_type,
            index,
            rng,
            correct_position,
            used_names,
        )
        specification = _specification_signature(task["specifications"])
        correct_solution = _correct_solution_signature(task)
        duplicate_count = used_specifications.get(
            specification, 0
        ) + used_correct_solutions.get(correct_solution, 0)
        if duplicate_count == 0:
            return task
        attempts.append((duplicate_count, specification, correct_solution, task))

    best_attempt = min(
        attempts,
        key=lambda candidate: (
            candidate[0],
            used_specifications.get(candidate[1], 0),
            used_correct_solutions.get(candidate[2], 0),
            candidate[1],
            candidate[2],
        ),
    )
    return best_attempt[3]


def _build_solution_comparison_task(
    topic: str,
    emphasis: str | None,
    problem_type: str,
    index: int,
    rng: random.Random,
    correct_position: int,
    used_names: set[str],
) -> dict:
    profile, topic_id = _profile_for(topic)
    topic_label = _topic_label(topic)
    context = rng.choice(profile.contexts)
    requirement = rng.choice(profile.requirements)
    function_name = _unique_function_name(profile, topic_id, index, rng, used_names)
    correct_body = rng.choice(profile.correct_bodies)
    distractors = rng.sample(profile.constraint_distractors, 2)
    candidates = _label_candidates(
        function_name,
        profile.params,
        context,
        emphasis,
        [
            {"is_correct": True, "body": correct_body},
            {"is_correct": False, "body": distractors[0]},
            {"is_correct": False, "body": distractors[1]},
        ],
        correct_position,
        rng,
    )

    return _task_payload(
        index=index,
        prompt=rng.choice(SOLUTION_COMPARISON_PROMPTS).format(
            problem_type=problem_type,
            topic=topic_label,
        ),
        specifications=(
            f"`{function_name}` should {requirement} in a {context} scenario. "
            f"Keep the solution focused on {topic_label}"
            f"{_emphasis_clause(emphasis)}."
        ),
        candidates=candidates,
        explanation=(
            "Solution {correct} is the only implementation that satisfies the "
            f"{topic_label} requirement{_emphasis_explanation(emphasis)}."
        ),
    )


def _build_specification_checking_task(
    topic: str,
    emphasis: str | None,
    problem_type: str,
    index: int,
    rng: random.Random,
    correct_position: int,
    used_names: set[str],
) -> dict:
    profile, topic_id = _profile_for(topic)
    topic_label = _topic_label(topic)
    context = rng.choice(profile.contexts)
    requirements = rng.sample(profile.requirements, min(2, len(profile.requirements)))
    function_name = _unique_function_name(profile, topic_id, index, rng, used_names)
    correct_body = rng.choice(profile.correct_bodies)
    distractors = rng.sample(profile.constraint_distractors, 2)
    candidates = _label_candidates(
        function_name,
        profile.params,
        context,
        emphasis,
        [
            {"is_correct": True, "body": correct_body},
            {"is_correct": False, "body": distractors[0]},
            {"is_correct": False, "body": distractors[1]},
        ],
        correct_position,
        rng,
    )

    return _task_payload(
        index=index,
        prompt=rng.choice(SPECIFICATION_CHECKING_PROMPTS).format(
            problem_type=problem_type,
            topic=topic_label,
        ),
        specifications=(
            f"`{function_name}` has two constraints: {requirements[0]}; and "
            f"{requirements[-1]}. The task covers {topic_label}"
            f"{_emphasis_clause(emphasis)}."
        ),
        candidates=candidates,
        explanation=(
            "Solution {correct} satisfies all listed constraints. The other "
            f"solutions each violates at least one {topic_label} constraint"
            f"{_emphasis_explanation(emphasis)}."
        ),
    )


def _build_debugging_task(
    topic: str,
    emphasis: str | None,
    problem_type: str,
    index: int,
    rng: random.Random,
    correct_position: int,
    used_names: set[str],
) -> dict:
    profile, topic_id = _profile_for(topic)
    topic_label = _topic_label(topic)
    context = rng.choice(profile.contexts)
    requirement = rng.choice(profile.requirements)
    function_name = _unique_function_name(profile, topic_id, index, rng, used_names)
    correct_body = rng.choice(profile.correct_bodies)
    buggy_body = rng.choice(profile.bug_bodies)
    still_wrong_body = rng.choice(profile.constraint_distractors)
    candidates = _label_candidates(
        function_name,
        profile.params,
        context,
        emphasis,
        [
            {"is_correct": True, "body": correct_body},
            {"is_correct": False, "body": buggy_body},
            {"is_correct": False, "body": still_wrong_body},
        ],
        correct_position,
        rng,
    )

    return _task_payload(
        index=index,
        prompt=rng.choice(DEBUGGING_PROMPTS).format(topic=topic_label),
        specifications=(
            f"`{function_name}` currently has a bug in a {context} scenario. "
            f"The corrected version should {requirement}"
            f"{_emphasis_clause(emphasis)}."
        ),
        candidates=candidates,
        explanation=(
            f"Solution {{correct}} fixes the bug by handling the {topic_label} "
            f"rule{_emphasis_explanation(emphasis)}."
        ),
    )


def _label_candidates(
    function_name: str,
    params: str,
    context: str,
    emphasis: str | None,
    semantic_candidates: list[dict[str, Any]],
    correct_position: int,
    rng: random.Random,
) -> dict:
    correct = next(
        candidate for candidate in semantic_candidates if candidate["is_correct"]
    )
    distractors = [
        candidate for candidate in semantic_candidates if not candidate["is_correct"]
    ]
    rng.shuffle(distractors)
    ordered = distractors
    ordered.insert(correct_position, correct)

    candidate_solutions = []
    correct_solution_id = LABELS[correct_position]
    for label, candidate in zip(LABELS, ordered, strict=True):
        candidate_solutions.append(
            {
                "id": label,
                "label": f"Solution {label}",
                "code": _format_code(
                    function_name,
                    params,
                    str(candidate["body"]),
                    context,
                    emphasis,
                ),
            }
        )

    return {
        "candidate_solutions": candidate_solutions,
        "correct_solution_id": correct_solution_id,
    }


def _task_payload(
    index: int,
    prompt: str,
    specifications: str,
    candidates: dict,
    explanation: str,
) -> dict:
    correct = candidates["correct_solution_id"]
    return {
        "id": f"task-{index + 1}",
        "prompt": prompt,
        "specifications": specifications,
        "candidate_solutions": candidates["candidate_solutions"],
        "correct_solution_id": correct,
        "explanation": explanation.format(correct=correct),
    }


def _specification_signature(specifications: str) -> str:
    normalized = re.sub(r"`check_[^`]+`", "`check_function`", specifications.lower())
    return " ".join(normalized.split())


def _correct_solution_signature(task: dict) -> str:
    correct_id = task["correct_solution_id"]
    code = next(
        candidate["code"]
        for candidate in task["candidate_solutions"]
        if candidate["id"] == correct_id
    )
    code = re.sub(r"bool check_[^(]+\([^)]*\) \{", "bool check_function() {", code)
    code = re.sub(r"\s*// context:[^\n]+", "", code)
    return " ".join(code.split())


def _profile_for(topic: str) -> tuple[TopicProfile, str]:
    topic_id = _cpp_identifier(topic)
    return TOPIC_PROFILES.get(topic, GENERIC_PROFILE), topic_id


def _topic_label(topic: str) -> str:
    return TOPIC_LABELS.get(topic, topic)


def _emphasis_clause(emphasis: str | None) -> str:
    if not emphasis:
        return ""
    return f" while emphasizing {_topic_label(emphasis)}"


def _emphasis_explanation(emphasis: str | None) -> str:
    if not emphasis:
        return ""
    return f" and respects the emphasis on {_topic_label(emphasis)}"


def _unique_function_name(
    profile: TopicProfile,
    topic_id: str,
    index: int,
    rng: random.Random,
    used_names: set[str],
) -> str:
    stem = rng.choice(profile.stems)
    base_name = f"check_{topic_id}_{stem}_{index + 1}"
    function_name = base_name
    suffix = 2
    while function_name in used_names:
        function_name = f"{base_name}_{suffix}"
        suffix += 1
    used_names.add(function_name)
    return function_name


def _format_code(
    function_name: str,
    params: str,
    body: str,
    context: str,
    emphasis: str | None,
) -> str:
    safe_context = _comment_text(context)
    comment_parts = [f"context: {safe_context}"]
    if emphasis:
        comment_parts.append(f"emphasis: {_cpp_identifier(emphasis)}")
    return (
        f"bool {function_name}({params}) {{\n"
        f"    // {'; '.join(comment_parts)}\n"
        f"{body}\n"
        "}"
    )


def _comment_text(value: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z_ ,.:-]+", "", value.strip())
    return cleaned or "practice"


def _cpp_identifier(value: str) -> str:
    identifier = re.sub(r"[^0-9a-zA-Z_]+", "_", value.strip().lower()).strip("_")
    if not identifier:
        return "topic"
    if identifier[0].isdigit():
        return f"topic_{identifier}"
    return identifier
