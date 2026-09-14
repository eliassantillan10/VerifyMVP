# ruff: noqa: E501
from django.db import migrations, models


def add_string_password_problem(apps, _schema_editor):
    Problem = apps.get_model("core", "Problem")
    Problem.objects.update_or_create(
        slug="string-password-exclamation-check",
        defaults={
            "topic": "String methods and manipulation",
            "topic_order": 1,
            "problem_order": 1,
            "description": (
                "This program asks the user to enter a password and checks whether "
                "it is at least eight characters long and contains an exclamation mark. "
                "It then reports whether the password is strong."
            ),
            "code": """#include <iostream>\n#include <string>\n\nusing namespace std;\n\nint main() {\n    string password;\n\n    cout << \"Enter a password: \";\n    cin >> password;\n\n    if (password.length() >= 8 && password.find(\"!\"))\n        cout << \"Strong password\\n\";\n    else if (password.length() >= 8)\n        cout << \"Add an exclamation mark\\n\";\n    else\n        cout << \"Password is too short\\n\";\n\n    return 0;\n}\n""",
            "flaw": (
                "find(\"!\") does not return a boolean. It returns the index of the "
                "first exclamation mark, or string::npos when none is found. An "
                "exclamation mark at index 0 therefore evaluates as false."
            ),
            "example": "Input: !dasasdadsasd. Output: Add an exclamation mark.",
            "seed_version": "reviewed-2026-08-18",
        },
    )


def remove_string_password_problem(apps, _schema_editor):
    apps.get_model("core", "Problem").objects.filter(
        slug="string-password-exclamation-check"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0002_clear_problem_catalog")]

    operations = [
        migrations.AddField(
            model_name="problem",
            name="flaw",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="problem",
            name="example",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.RunPython(add_string_password_problem, remove_string_password_problem),
    ]
