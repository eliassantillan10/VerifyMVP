from django.db import models


class Problem(models.Model):
    """A reviewed Case Breaker problem stored in the application database."""

    slug = models.SlugField(max_length=64, unique=True)
    topic = models.CharField(max_length=160)
    topic_order = models.PositiveSmallIntegerField()
    problem_order = models.PositiveSmallIntegerField()
    description = models.TextField()
    code = models.TextField()
    flaw = models.TextField()
    example = models.TextField()
    seed_version = models.CharField(max_length=32)

    class Meta:
        ordering = ("topic_order", "problem_order")
        constraints = [
            models.UniqueConstraint(
                fields=("topic_order", "problem_order"),
                name="unique_problem_source_position",
            )
        ]
