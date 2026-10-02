from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Problem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(max_length=64, unique=True)),
                ("topic", models.CharField(max_length=160)),
                ("topic_order", models.PositiveSmallIntegerField()),
                ("problem_order", models.PositiveSmallIntegerField()),
                ("description", models.TextField()),
                ("code", models.TextField()),
                ("seed_version", models.CharField(max_length=32)),
            ],
            options={"ordering": ("topic_order", "problem_order")},
        ),
        migrations.AddConstraint(
            model_name="problem",
            constraint=models.UniqueConstraint(
                fields=("topic_order", "problem_order"),
                name="unique_problem_source_position",
            ),
        ),
    ]
