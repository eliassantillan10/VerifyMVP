from apps.core.lm_studio import coach_reply
from apps.core.models import Problem


def ask_coach(problem: Problem, mode: str, learner_text: str) -> str:
    return coach_reply(
        topic=problem.topic,
        description=problem.description,
        code=problem.code,
        mode=mode,
        learner_text=learner_text,
    )
